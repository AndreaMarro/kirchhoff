"""Potenza servita con oracoli da |I|²R, |V|²Y e bilancio dei rami."""
from fractions import Fraction as F
import asyncio
import http.client
import importlib.util
import json
from pathlib import Path
from threading import Thread

import pytest

from kirchhoff.domain.exact import Cyc12, J, ZERO
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline import lesson_ac_power
from kirchhoff.pipeline.lesson_pdf import export_pdf


SERIES = ('@ac 100 rad/s\n@amplitude rms\nV1 a 0 10 volt 30deg\n'
          'R1 a b 3 ohm\nL1 b c 1/25 henry\nC1 c 0 1/100 farad\n? power R1')


def power_amount(lesson):
    return Cyc12(tuple(F(value) for value in lesson['answer']['complex_power']['coefficients']))


@pytest.mark.parametrize('amplitude,scale', [('rms', F(1)), ('peak', F(1, 2))])
@pytest.mark.parametrize('phase', [-60, 30, 90])
def test_series_powers_match_manual_squared_current_laws_and_balance(amplitude, scale, phase):
    # Z=3+j3, quindi |I|²=100/(9+9)=50/9. L=+j4,C=-j1.
    # L'oracolo usa le leggi dei componenti senza chiamare un solver.
    expected = {'R1': Cyc12.of(F(50, 3)), 'L1': J * F(200, 9),
                'C1': -J * F(50, 9), 'V1': -F(50, 3) - J * F(50, 3)}
    actual = {}
    for target, value in expected.items():
        text = SERIES.replace('rms', amplitude).replace('30deg', f'{phase}deg').replace('? power R1', f'? power {target}')
        assert leggi(text).requests[0].quantity == 'power'
        lesson = create_lesson(text)
        assert power_amount(lesson) == value * scale
        answer = lesson['answer']
        assert answer['quantity'] == 'power' and answer['unit'] == 'VA'
        assert 'phasor' not in answer
        assert answer['complex_power']['active']['unit'] == 'W'
        assert answer['complex_power']['reactive']['unit'] == 'var'
        assert lesson['conventions']['power_calculated'] is True
        assert lesson['conventions']['power_factor'] == str(scale)
        assert lesson['conventions']['power_sign'] == 'passive'
        assert lesson['verification']['electrical_claim'] == 'PHASOR_POWER_CROSSCHECKED'
        assert lesson['verification']['product_verified'] is False
        assert lesson['algebra']['canonical_proof'] is False
        assert {step['algebra']['operation'] for step in lesson['steps'] if 'algebra' in step} == {'substitute', 'eliminate', 'solution', 'recover'}
        assert [step['title'] for step in lesson['steps'][-3:]] == [
            'Dichiariamo la potenza e i segni', 'Controlliamo il bilancio delle potenze', 'Torniamo alla potenza richiesta']
        assert 'Somma P = 0 W' in lesson['steps'][-2]['equations']
        actual[target] = power_amount(lesson)
    assert sum(actual.values(), ZERO) == ZERO


@pytest.mark.parametrize('amplitude,scale', [('rms', F(1)), ('peak', F(1, 2))])
def test_parallel_powers_use_independent_voltage_squared_admittance_and_reversed_reference(amplitude, scale):
    # Y=(4+j15)/20; |V|²=4/|Y|²=1600/241. S=|V|²*conj(Y).
    text = (f'@ac 100 rad/s\n@amplitude {amplitude}\nI1 0 a 2 ampere -60deg\n'
            'R1 a 0 5 ohm\nL1 a 0 1/25 henry\nC1 a 0 1/100 farad\n? power R1')
    expected = {'R1': Cyc12.of(F(320, 241)), 'L1': J * F(400, 241),
                'C1': -J * F(1600, 241), 'I1': -F(320, 241) + J * F(1200, 241)}
    for target, value in expected.items():
        assert power_amount(create_lesson(text.replace('? power R1', f'? power {target}'))) == value * scale
    assert power_amount(create_lesson(text.replace('R1 a 0', 'R1 0 a'))) == expected['R1'] * scale


@pytest.mark.parametrize('amplitude', ['rms', 'peak'])
def test_power_pdf_states_factor_signs_and_separate_units(amplitude):
    pdf = export_pdf(create_lesson(SERIES.replace('rms', amplitude).replace('? power R1', '? power V1')))
    plain = pdf.replace(b'\\(', b'(').replace(b'\\)', b')')
    assert b'S = V * conj(I)' in plain
    assert b'P = Re(S) [W]' in plain and b'Q = Im(S) [var]' in plain
    assert b'convenzione passiva' in plain and b'erogata' in plain
    assert b'Somma P = 0 W' in plain and b'Somma Q = 0 var' in plain
    if amplitude == 'peak':
        assert b'S = V * conj(I) / 2' in plain


@pytest.mark.parametrize('amplitude', ['', '@amplitude unspecified\n'])
def test_power_refuses_unspecified_amplitude(amplitude):
    refusal = create_lesson(SERIES.replace('@amplitude rms\n', amplitude))
    assert refusal['cause'] == 'claim_unsupported'
    assert 'answer' not in refusal and 'rms' in refusal['message']


def test_power_is_not_silently_served_in_dc():
    assert create_lesson('V1 a 0 10 volt\nR1 a 0 5 ohm\n? power R1')['cause'] == 'unsupported_domain'
    with pytest.raises(ValueError, match='inesistente'):
        create_lesson(SERIES.replace('? power R1', '? power unknown'))


@pytest.mark.parametrize('mutation', ['negated', 'double', 'conjugate', 'missing', 'extra', 'float'])
def test_corrupted_power_kernel_fails_even_if_requested_branch_was_not_corrupted(monkeypatch, mutation):
    kernel = lesson_ac_power.phasor_complex_powers
    def corrupt(ir, solution, *, amplitude):
        values = kernel(ir, solution, amplitude=amplitude)
        if mutation == 'negated': values['L1'] = -values['L1']
        elif mutation == 'double': values = {cid: value * 2 for cid, value in values.items()}
        elif mutation == 'conjugate': values['L1'] = values['L1'].conjugate()
        elif mutation == 'missing': values.pop('L1')
        elif mutation == 'extra': values['unknown'] = ZERO
        else: values['L1'] = 1.0
        return values
    monkeypatch.setattr(lesson_ac_power, 'phasor_complex_powers', corrupt)
    refusal = create_lesson(SERIES.replace('rms', 'peak'))
    assert refusal['cause'] == 'path_disagreement'
    assert 'answer' not in refusal


def test_complex_power_balance_is_an_independent_final_gate(monkeypatch):
    monkeypatch.setattr(lesson_ac_power, 'phasor_complex_powers',
                        lambda ir, *_args, **_kwargs: {c.id: Cyc12.of(1) for c in ir.components})
    monkeypatch.setattr(lesson_ac_power, '_rectangular_power', lambda *_: Cyc12.of(1))
    refusal = create_lesson(SERIES)
    assert refusal['cause'] == 'residual' and 'bilancio' in refusal['message']


def test_power_checker_requires_explicit_convention_before_kernel():
    result = lesson_ac_power.checked_complex_powers(leggi(SERIES), {}, {}, 'unspecified')
    assert isinstance(result, Refusal) and result.cause == 'claim_unsupported'


@pytest.mark.parametrize('amplitude', ['rms', 'peak'])
def test_power_http_contract_pdf_and_refusal_share_canonical_service(amplitude):
    path = Path(__file__).resolve().parents[1] / 'scripts/serve_student.py'
    spec = importlib.util.spec_from_file_location('power_http_student_server', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
    text = SERIES.replace('rms', amplitude).replace('? power R1', '? power V1')
    try:
        client.request('POST', '/api/solve', json.dumps({'netlist': text}), {'Content-Type': 'application/json'})
        result = client.getresponse()
        assert result.status == 200
        lesson = json.loads(result.read())
        expected = create_lesson(text)
        assert lesson == expected
        client.request('POST', '/api/pdf', json.dumps({'netlist': text}), {'Content-Type': 'application/json'})
        result = client.getresponse()
        assert result.status == 200 and result.read() == export_pdf(expected)
        client.request('POST', '/api/solve', json.dumps({'netlist': text.replace(amplitude, 'unspecified')}), {'Content-Type': 'application/json'})
        result = client.getresponse()
        refused = json.loads(result.read())
        assert refused['outcome'] == 'refusal' and 'answer' not in refused
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize('amplitude', ['rms', 'peak'])
def test_power_mcp_contract_and_refusal_are_not_promoted(amplitude):
    pytest.importorskip('mcp')
    from mcp import Client
    from kirchhoff.api.mcp_server import build_server
    text = SERIES.replace('rms', amplitude).replace('? power R1', '? power V1')
    async def run():
        async with Client(build_server()) as client:
            result = await client.call_tool('solve_circuit', {'netlist': text})
            assert not result.is_error
            assert result.structured_content == create_lesson(text)
            capabilities = (await client.call_tool('circuit_capabilities', {'netlist': text})).structured_content
            assert capabilities['ac_scope']['powers'] is True
            assert capabilities['ac_scope']['power_amplitude_conventions'] == ['rms', 'peak']
            assert capabilities['circuit']['outcome'] == 'solved'
            result = await client.call_tool('solve_circuit', {'netlist': text.replace(amplitude, 'unspecified')})
            assert result.structured_content['outcome'] == 'refusal'
            assert 'answer' not in result.structured_content
    asyncio.run(run())
