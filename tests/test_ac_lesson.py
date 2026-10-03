"""La lezione AC attraversa il servizio canonico e fallisce prima di esporre falsi."""
import asyncio
from decimal import Decimal, localcontext, ROUND_DOWN
from fractions import Fraction as F
import http.client
import importlib.util
import json
from pathlib import Path
from threading import Thread

import pytest

from kirchhoff.domain.exact import Cyc12, J, zeta_pow
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_ac import phasor_view
from kirchhoff.pipeline import lesson_ac
from kirchhoff.pipeline.lesson_pdf import export_pdf


SERIES = ('@ac 100 rad/s\nV1 a 0 10 volt 30deg\nR1 a b 3 ohm\n'
          'L1 b c 1/25 henry\nC1 c 0 1/100 farad\n? current R1')


def amount(lesson):
    return Cyc12(tuple(F(value) for value in lesson['answer']['phasor']['coefficients']))


@pytest.mark.parametrize('amplitude,label', [('rms', 'valori efficaci'), ('peak', 'valori di picco'), ('unspecified', 'non distingue RMS e picco')])
def test_amplitude_declaration_survives_lesson_pdf_and_json_without_conversion(amplitude, label):
    text = SERIES.replace('@ac 100 rad/s', f'@ac 100 rad/s\n@amplitude {amplitude}')
    lesson = json.loads(json.dumps(create_lesson(text)))
    assert lesson['netlist'] == text
    assert lesson['conventions']['amplitude'] == amplitude
    assert lesson['conventions']['power_calculated'] is False
    assert lesson['verification']['product_verified'] is False
    assert lesson['answer'] == create_lesson(SERIES)['answer']
    assert lesson['fingerprint'] != create_lesson(SERIES)['fingerprint']
    assert label in lesson['steps'][0]['explanation']
    assert label in lesson['steps'][-1]['explanation']
    assert label.encode('latin1') in export_pdf(lesson)


def test_internal_phasor_presenter_rejects_unknown_convention():
    from kirchhoff.pipeline.netlist import leggi
    ir = leggi(SERIES)
    with pytest.raises(ValueError, match='ampiezza'):
        lesson_ac.create_phasor_lesson(SERIES, ir, ir.requests[0], 'phasor', '0' * 40, 'average')


@pytest.mark.parametrize('phase', [-390, -90, 0, 30, 120, 330, 720])
@pytest.mark.parametrize('resistance,inductance,capacitance', [(3, '1/25', '1/100'), (7, '1/50', '1/300')])
def test_series_answer_matches_independent_closed_form_and_shows_laws(phase, resistance, inductance, capacitance):
    text = SERIES.replace('30deg', f'{phase}deg').replace('3 ohm', f'{resistance} ohm')
    text = text.replace('1/25 henry', f'{inductance} henry').replace('1/100 farad', f'{capacitance} farad')
    lesson = create_lesson(text)
    expected = 10 * zeta_pow(phase // 30) / (resistance + J * (100 * F(inductance) - 1 / (100 * F(capacitance))))
    assert amount(lesson) == expected
    assert lesson['schema'] == 'circuit-lesson.v1' and lesson['method'] == 'phasor'
    assert lesson['available'] == ['auto', 'phasor']
    assert lesson['answer']['reference'] == 'a → b' and lesson['answer']['unit'] == 'A'
    assert lesson['verification']['electrical_claim'] == 'PHASOR_PATHS_CROSSCHECKED'
    assert lesson['verification']['backend'] == 'PHASOR_RESIDUALS_CHECKED'
    assert lesson['verification']['lesson'] == 'phasor-all-branches-crosscheck'
    assert lesson['verification']['product_verified'] is False
    assert lesson['conventions']['amplitude'] == 'unspecified'
    assert lesson['conventions']['power_calculated'] is False
    assert lesson['conventions']['time_dependence'] == 'exp(+jωt)'
    equations = '\n'.join(e for step in lesson['steps'] for e in step['equations'])
    from kirchhoff.pipeline.lesson_math import number
    impedance_math = lesson['steps'][1]['math']
    assert any(eq['left'] == {'kind':'symbol','name':'Z(L1)'} and eq['right'] == number(J*100*F(inductance)) for eq in impedance_math)
    assert any(eq['left'] == {'kind':'symbol','name':'Z(C1)'} and eq['right'] == number(-J/(100*F(capacitance))) for eq in impedance_math)
    assert any(eq['right']['kind'] == 'divide' for eq in impedance_math), 'La sostituzione del condensatore resta esplicita.'
    assert 'Nodo b: −I(R1) + I(L1) = 0 A' in equations
    assert lesson['steps'][-1]['focus'] == ['R1']
    json.dumps(lesson)  # nessun oggetto Fraction/Cyc12 attraversa HTTP/MCP


def test_parallel_current_source_uses_admittances_and_reversed_terminal_sign():
    text = ('@ac 100 rad/s\nI1 0 a 2 ampere -60deg\nR1 a 0 5 ohm\n'
            'L1 a 0 1/25 henry\nC1 a 0 1/100 farad\n? voltage R1')
    expected = 2 * zeta_pow(-2) / (F(1, 5) + J * F(3, 4))
    assert amount(create_lesson(text)) == expected
    reversed_lesson = create_lesson(text.replace('R1 a 0', 'R1 0 a'), method='phasor')
    assert amount(reversed_lesson) == -expected
    assert reversed_lesson['answer']['reference'] == '0 → a'
    assert reversed_lesson['answer']['unit'] == 'V'


@pytest.mark.parametrize('phase', [-60, 0, 30, 120])
def test_bridged_network_matches_manual_two_node_kcl_determinant(phase):
    # Rete a ponte non riducibile in serie/parallelo. Due incognite x,y:
    # (1/2+1/5-j/4)*x - y/5 = Vs/2
    # -x/5 + (1/3+1/5+j)*y = Vs/3 + Is.
    # L'oracolo usa Cramer su queste due equazioni scritte qui, senza MNA,
    # tableau, riconoscitori topologici o generatore del prodotto.
    text = (f'@ac 100 rad/s\nV1 s 0 10 volt {phase}deg\nR1 s x 2 ohm\n'
            'R2 s y 3 ohm\nL1 x 0 1/25 henry\nC1 y 0 1/100 farad\n'
            'R3 x y 5 ohm\nI1 0 y 2 ampere -90deg\n? current R3')
    a, b, d = Cyc12.of(F(7, 10)) - J / 4, Cyc12.of(F(-1, 5)), Cyc12.of(F(8, 15)) + J
    source = 10 * zeta_pow(phase // 30)
    u, v = source / 2, source / 3 - 2 * J
    determinant = a * d - b * b
    x, y = (u * d - b * v) / determinant, (a * v - b * u) / determinant
    assert amount(create_lesson(text)) == (x - y) / 5
    assert amount(create_lesson(text.replace('? current R3', '? voltage L1'))) == x
    assert amount(create_lesson(text.replace('? current R3', '? voltage C1'))) == y
    assert amount(create_lesson(text.replace('R3 x y', 'R3 y x'))) == (y - x) / 5


@pytest.mark.parametrize('quantity,target', [('voltage', 'V1'), ('current', 'V1'), ('voltage', 'C1'), ('current', 'L1')])
def test_every_branch_observable_is_available(quantity, target):
    solved = create_lesson(SERIES.replace('? current R1', f'? {quantity} {target}'))
    current = 10 * zeta_pow(1) / (3 + J * 3)
    expected = {'V1': {'voltage': 10 * zeta_pow(1), 'current': -current},
                'C1': {'voltage': -J * current}, 'L1': {'current': current}}[target][quantity]
    assert amount(solved) == expected


@pytest.mark.parametrize('value,real,imaginary', [
    (Cyc12.of(0), '0', '0'), (J * -3, '0', '-3'),
    (zeta_pow(1), '1/2*sqrt(3)', '1/2'),
    (zeta_pow(2), '1/2', '1/2*sqrt(3)'),
    (1 - 2 * zeta_pow(1), '1 - sqrt(3)', '-1'),
    (-2 * zeta_pow(1), '-sqrt(3)', '-1'),
    (1 + 2 * zeta_pow(1), '1 + sqrt(3)', '1'),
])
def test_rectangular_projection_preserves_exact_radicals(value, real, imaginary):
    view = phasor_view(value)
    assert view['phasor']['real_exact'] == real
    assert view['phasor']['imaginary_exact'] == imaginary
    assert Cyc12(tuple(F(x) for x in view['phasor']['coefficients'])) == value


def test_projection_rejects_nonexact_values():
    with pytest.raises(ValueError, match='Cyc12'):
        phasor_view(1.0)


@pytest.mark.parametrize('digits', [30, 90, 210])
def test_near_cancellation_is_nonzero_in_served_decimal_with_adaptive_precision(digits):
    # Tre sorgenti e quattro resistori: KCL manuale al nodo x dà
    # Vx = (q + exp(j150°) + exp(j210°))/4 = (q-sqrt(3))/4.
    # q tronca sqrt(3); il valore vero è negativo, piccolo e non nullo.
    with localcontext() as ctx:
        ctx.prec = digits + 80
        root = Decimal(3).sqrt()
        q = root.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_DOWN)
        expected = format((q - root) / 4, '.8g')
    text = (f'@ac 100 rad/s\nV1 a 0 {q} volt 0deg\nV2 b 0 1 volt 150deg\n'
            'V3 c 0 1 volt 210deg\nR1 a x 1 ohm\nR2 b x 1 ohm\n'
            'R3 c x 1 ohm\nR4 x 0 1 ohm\n? voltage R4')
    lesson = create_lesson(text)
    view = lesson['answer']['phasor']
    assert Decimal(view['real_decimal']) < 0
    assert view['real_decimal'] == expected
    assert view['imaginary_decimal'] == '0'
    assert amount(lesson) == Cyc12((F(q) / 4, F(-1, 2), F(0), F(1, 4)))
    assert view['decimal_precision']['real'] > digits
    assert view['decimal_precision']['method'] == 'exact-rational-sqrt3-bounds'


@pytest.mark.parametrize('solver', ['solve_phasor', 'solve_phasor_tableau'])
@pytest.mark.parametrize('corruption', ['extra', 'missing', 'quantity', 'wrong', 'float'])
def test_any_branch_disagreement_blocks_correct_target(monkeypatch, solver, corruption):
    real_solver = getattr(lesson_ac, solver)
    def corrupt(ir):
        result = real_solver(ir)
        if corruption == 'extra':
            result['invented'] = result['L1'].copy()
        elif corruption == 'missing':
            result.pop('L1')
        elif corruption == 'quantity':
            result['L1'].pop('voltage')
        elif corruption == 'wrong':
            result['L1']['voltage'] += 1
        else:
            result['L1']['voltage'] = 0.0
        return result
    monkeypatch.setattr(lesson_ac, solver, corrupt)
    refused = create_lesson(SERIES)
    assert refused['outcome'] == 'refusal' and refused['cause'] == 'path_disagreement'
    assert 'answer' not in refused and 'verification' not in refused


def test_two_wrong_paths_cannot_hide_violated_source_constitutive_law(monkeypatch):
    def zero_solution(ir):
        return {c.id: {'voltage': Cyc12.of(0), 'current': Cyc12.of(0)} for c in ir.components}
    monkeypatch.setattr(lesson_ac, 'solve_phasor', zero_solution)
    monkeypatch.setattr(lesson_ac, 'solve_phasor_tableau', zero_solution)
    refused = create_lesson(SERIES)
    assert refused['cause'] == 'residual' and 'V1' in refused['message']


def test_residual_gate_failure_is_not_exposed(monkeypatch):
    monkeypatch.setattr(lesson_ac, 'verify', lambda *_: Refusal('residual', 'R1', 'component', 'Residuo non nullo.'))
    assert create_lesson(SERIES) == {'outcome': 'refusal', 'cause': 'residual', 'message': 'Residuo non nullo.'}


@pytest.mark.parametrize('text,cause', [
    (SERIES.replace('? current R1', '? resistance a 0'), 'unsupported_domain'),
    (SERIES.replace('? current R1', '? time_constant R1'), 'unsupported_domain'),
    (SERIES.replace('R1 a b 3 ohm', 'E1 a b c 0 2').replace('? current R1', '? current E1'), 'unsupported_domain'),
    (SERIES.replace('R1 a b 3 ohm', 'R1 z b 3 ohm'), 'topology'),
    ('@ac 1 rad/s\nI1 0 a 1 ampere 0deg\nC1 a 0 1 farad\nL1 a 0 1 henry\n? voltage C1', 'unsolvable'),
])
def test_unsupported_or_singular_ac_fails_closed(text, cause):
    lesson = create_lesson(text)
    assert lesson['outcome'] == 'refusal' and lesson['cause'] == cause
    assert 'answer' not in lesson


def test_methods_do_not_silently_cross_domains():
    with pytest.raises(ValueError, match='Fasori'):
        create_lesson(SERIES, 'millman')
    with pytest.raises(ValueError, match='@ac'):
        create_lesson('V1 a 0 10 volt\nR1 a 0 5 ohm\n? current R1', 'phasor')
    with pytest.raises(ValueError, match='inesistente'):
        create_lesson(SERIES.replace('? current R1', '? current Rmissing'))


@pytest.mark.parametrize('seed', range(20))
def test_generated_ac_tree_reaches_service_with_construction_oracle(seed):
    from kirchhoff.eval.generator_ac import generate_case
    ir, expected, _ = generate_case(seed)
    rows = [f'@ac {ir.omega} rad/s']
    for component in ir.components:
        name = 'V1' if component.id == 'E1' else component.id
        row = f'{name} {component.terminals[0]} {component.terminals[1]} {component.value.amount} {component.value.unit}'
        rows.append(row + (' 0deg' if component.id == 'E1' else ''))
    for request in ir.requests:
        text = '\n'.join(rows + [f'? {request.quantity} {request.target}'])
        assert amount(create_lesson(text)) == expected[request.target][request.quantity]


@pytest.mark.parametrize('amplitude', ['rms', 'peak', 'unspecified'])
def test_http_serves_the_same_full_ac_lesson(amplitude):
    text = SERIES.replace('@ac 100 rad/s', f'@ac 100 rad/s\n@amplitude {amplitude}')
    path = Path(__file__).resolve().parents[1] / 'scripts/serve_student.py'
    spec = importlib.util.spec_from_file_location('ac_http_student_server', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
        client.request('POST', '/api/solve', json.dumps(dict(netlist=text)), {'Content-Type': 'application/json'})
        response = client.getresponse()
        assert response.status == 200
        lesson = json.loads(response.read())
        expected = create_lesson(text)
        assert lesson['conventions']['amplitude'] == amplitude
        assert lesson['answer'] == expected['answer']
        assert lesson['steps'] == expected['steps']
        assert lesson['verification'] == expected['verification']
        client.request('POST', '/api/solve', json.dumps(dict(netlist=text.replace(f'@amplitude {amplitude}', '@amplitude average'))), {'Content-Type': 'application/json'})
        invalid = client.getresponse()
        assert invalid.status == 422
        assert '@amplitude' in json.loads(invalid.read())['message']
        client.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize('amplitude', ['rms', 'peak', 'unspecified'])
def test_mcp_serves_exact_ac_and_its_actual_capability(amplitude):
    text = SERIES.replace('@ac 100 rad/s', f'@ac 100 rad/s\n@amplitude {amplitude}')
    pytest.importorskip('mcp')
    from mcp import Client
    from kirchhoff.api.mcp_server import build_server
    async def run():
        async with Client(build_server()) as client:
            result = await client.call_tool('solve_circuit', {'netlist': text, 'method': 'phasor'})
            assert not result.is_error
            lesson = result.structured_content
            assert lesson['conventions']['amplitude'] == amplitude
            assert lesson['answer'] == create_lesson(SERIES)['answer']
            assert lesson['verification']['electrical_claim'] == 'PHASOR_PATHS_CROSSCHECKED'
            capabilities = (await client.call_tool('circuit_capabilities', {'netlist': SERIES})).structured_content
            assert capabilities['ac'] is True
            assert capabilities['ac_scope']['certified_lesson'] is False
            assert capabilities['ac_scope']['amplitude'] == capabilities['ac_scope']['amplitude_default'] == 'unspecified'
            assert set(capabilities['ac_scope']['amplitude_conventions']) == {'rms', 'peak', 'unspecified'}
            assert capabilities['circuit']['available_methods'] == ['auto', 'phasor']
            invalid = await client.call_tool('solve_circuit', {'netlist': text.replace(f'@amplitude {amplitude}', '@amplitude average')})
            assert invalid.is_error
            assert invalid.structured_content is None
    asyncio.run(run())
