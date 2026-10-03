"""Impedenza AC: oracoli manuali, algebra, riferimenti e rifiuti fail-closed."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import json

import pytest

from kirchhoff.domain.ir import PortRequest, canonicalize
from kirchhoff.pipeline import lesson_ac, lesson_ac_port
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_math import equation_text, number
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.pipeline.netlist import leggi


BRIDGE = ('@ac 2 rad/s\nR1 p a 2 ohm\nR2 p b 3 ohm\nL1 a 0 2 henry\n'
          'C1 b 0 1/2 farad\nR3 a b 5 ohm')
FLOATING = ('@ac 2 rad/s\nV1 a b 12 volt 30deg\nI1 0 p 7 ampere -90deg\n'
            'R1 p a 2 ohm\nL1 a 0 2 henry\nR2 p b 3 ohm\nC1 b 0 1/2 farad\nR3 p 0 5 ohm')


def plus(x, y):
    return x[0]+y[0], x[1]+y[1]


def times(x, y):
    return x[0]*y[0]-x[1]*y[1], x[0]*y[1]+x[1]*y[0]


def ratio(x, y):
    norm = y[0]*y[0]+y[1]*y[1]
    return (x[0]*y[0]+x[1]*y[1])/norm, (x[1]*y[0]-x[0]*y[1])/norm


def bridge_oracle(r1, r2, r3, xl, xc):
    # Prova in tensione a 1 V (il prodotto usa 1 A). KCL a,b scritte a mano:
    # A*Va+B*Vb=g1; B*Va+D*Vb=g2. Cramer, poi I=(1-Va)g1+(1-Vb)g2.
    g1, g2, g3 = 1/r1, 1/r2, 1/r3
    a, b, d = (g1+g3, -1/xl), (-g3,F(0)), (g2+g3, -1/xc)
    determinant = plus(times(a,d), times((-1,F(0)),times(b,b)))
    va = ratio(plus(times((g1,F(0)),d),times((-g2,F(0)),b)),determinant)
    vb = ratio(plus(times((g2,F(0)),a),times((-g1,F(0)),b)),determinant)
    current = plus(times((g1,F(0)),(1-va[0],-va[1])),times((g2,F(0)),(1-vb[0],-vb[1])))
    return ratio((F(1),F(0)),current)


def rectangular(lesson):
    a,b,c,d = map(F,lesson['answer']['complex_impedance']['coefficients'])
    # Tutte le fonti sono spente: RLC a valori razionali dà coordinate razionali.
    assert b==c==0
    return a,d


def test_port_request_is_typed_and_requires_ac_even_without_sources():
    ir=leggi(BRIDGE+'\n? impedance p 0')
    assert ir.requests==(PortRequest('q1','equivalent_impedance',('p','0')),)
    assert canonicalize(ir).requests==ir.requests
    with pytest.raises(ValueError,match='regime AC'):
        replace(ir,domain='dc')
    with pytest.raises(ValueError,match='richiede prima @ac'):
        leggi('R1 p 0 2 ohm\n? impedance p 0')


@pytest.mark.parametrize('question', ['? impedance p','? impedance p 0 extra','? impedance p p','? impedance missing 0'])
def test_invalid_port_does_not_become_component_question(question):
    with pytest.raises(ValueError):create_lesson(BRIDGE+'\n'+question)


@pytest.mark.parametrize('r1,r2,r3,l,c,omega',[(2,3,5,2,F(1,2),2),(7,11,13,F(3,5),F(2,7),3),
                                             (F(2,3),F(4,5),F(7,3),F(5,2),F(3,7),F(7,5))])
def test_nonseries_bridge_matches_exact_manual_voltage_probe(r1,r2,r3,l,c,omega):
    r1,r2,r3,l,c,omega=map(F,(r1,r2,r3,l,c,omega))
    text=(f'@ac {omega} rad/s\nR1 p a {r1} ohm\nR2 p b {r2} ohm\nL1 a 0 {l} henry\n'
          f'C1 b 0 {c} farad\nR3 a b {r3} ohm\n? impedance p 0')
    lesson=create_lesson(text,method='test_current')
    assert lesson['outcome']=='solved'
    assert rectangular(lesson)==bridge_oracle(r1,r2,r3,omega*l,-1/(omega*c))
    assert lesson['method']=='test_current' and lesson['available']==['auto','test_current']
    assert lesson['verification']['product_verified'] is False


@pytest.mark.parametrize('amplitude',['rms','peak','unspecified'])
@pytest.mark.parametrize('port',[('p','0'),('0','p')])
def test_floating_source_short_and_amplitude_preserve_impedance(amplitude,port):
    text=FLOATING.replace('@ac 2 rad/s',f'@ac 2 rad/s\n@amplitude {amplitude}')+f'\n? impedance {port[0]} {port[1]}'
    lesson=create_lesson(text)
    # V1 spenta unisce a,b; (2||3) è in serie a (j4||-j), tutto in parallelo a5Ω.
    series=plus((F(6,5),F(0)),ratio((F(1),F(0)),(F(0),F(3,4))))
    expected=ratio(times((F(5),F(0)),series),plus((F(5),F(0)),series))
    assert rectangular(lesson)==expected
    assert lesson['answer']['reference']==f'{port[0]} → {port[1]}'
    assert lesson['conventions']['amplitude']==amplitude
    assert lesson['conventions']['power_calculated'] is False
    assert lesson['conventions']['impedance_amplitude_invariant'] is True
    assert 'phasor' not in lesson['answer'] and 'complex_power' not in lesson['answer']
    assert lesson['port_analysis']['test_source']['terminals']==list(reversed(port))
    assert lesson['port_analysis']['deactivated_sources']==['V1','I1']


def test_different_source_values_and_phases_are_deactivated_and_probe_id_is_unique():
    base=create_lesson(BRIDGE+'\n? impedance p 0')
    for current in ['I_port_probe a b 13 ampere 30deg','I_port_probe a b 2/3 ampere 240deg']:
        lesson=create_lesson(BRIDGE+'\n'+current+'\n? impedance p 0')
        assert rectangular(lesson)==rectangular(base)
        assert lesson['port_analysis']['test_source']['id']=='I_port_probe_'
        assert lesson['port_analysis']['deactivated_sources']==['I_port_probe']


@pytest.mark.parametrize('circuit',[
    '@ac 1 rad/s\nV1 p 0 4 volt 90deg\nR1 p 0 2 ohm',
    '@ac 1 rad/s\nL1 p a 1 henry\nC1 a 0 1 farad'])
def test_finite_short_or_series_resonance_is_exact_zero(circuit):
    lesson=create_lesson(circuit+'\n? impedance p 0')
    assert lesson['outcome']=='solved' and rectangular(lesson)==(F(0),F(0))


@pytest.mark.parametrize('circuit',[
    '@ac 1 rad/s\nL1 p 0 1 henry\nC1 p 0 1 farad',
    '@ac 1 rad/s\nI1 p 0 0 ampere 0deg',
    '@ac 1 rad/s\nR1 p a 2 ohm\nR2 b 0 3 ohm',
    '@ac 1 rad/s\nV1 p 0 1 volt 0deg\nV2 p 0 2 volt 0deg'])
def test_open_resonance_island_and_inconsistent_source_refuse_without_infinite_answer(circuit):
    lesson=create_lesson(circuit+'\n? impedance p 0')
    assert lesson['outcome']=='refusal'
    assert 'answer' not in lesson and 'verification' not in lesson


def test_unsupported_methods_types_and_ac_resistance_keep_their_scope():
    with pytest.raises(ValueError,match='Corrente di prova'):
        create_lesson(BRIDGE+'\n? impedance p 0',method='phasor')
    unsupported=create_lesson('@ac 2 rad/s\nR1 p 0 2 ohm\nE1 p 0 p 0 2\n? impedance p 0')
    assert unsupported['outcome']=='refusal' and unsupported['cause']=='unsupported_domain'
    resistance=create_lesson(BRIDGE+'\n? resistance p 0')
    assert resistance['outcome']=='refusal' and resistance['cause']=='unsupported_domain'


@pytest.mark.parametrize('change',['source_on','source_phase','passive','probe_value','probe_phase','probe_direction','omega'])
def test_wrong_transformation_cannot_hide_behind_agreeing_solvers(monkeypatch,change):
    real=lesson_ac_port._ac_probe
    def corrupt(ir,port,amperes,*,off):
        measured,probe=real(ir,port,amperes,off=off)
        cs=list(measured.components)
        if change=='source_on':cs[0]=replace(cs[0],value=replace(cs[0].value,amount=F(7)))
        elif change=='source_phase':cs[0]=replace(cs[0],phase_steps=1)
        elif change=='passive':cs[2]=replace(cs[2],value=replace(cs[2].value,amount=F(9)))
        elif change=='probe_value':cs[-1]=replace(cs[-1],value=replace(cs[-1].value,amount=F(2)))
        elif change=='probe_phase':cs[-1]=replace(cs[-1],phase_steps=6)
        elif change=='probe_direction':cs[-1]=replace(cs[-1],terminals=tuple(reversed(cs[-1].terminals)))
        else:measured=replace(measured,omega=measured.omega*2)
        return replace(measured,components=tuple(cs)),probe
    monkeypatch.setattr(lesson_ac_port,'_ac_probe',corrupt)
    lesson=create_lesson(FLOATING+'\n? impedance p 0')
    assert lesson['outcome']=='refusal' and lesson['cause']=='path_disagreement'
    assert 'answer' not in lesson


def test_probe_algebra_corruption_is_rejected_before_port_answer(monkeypatch):
    real=lesson_ac.build_algebra
    def corrupt(ir):
        proof=deepcopy(real(ir));proof['initial'][0]['row'][0][0]='999';return proof
    monkeypatch.setattr(lesson_ac,'build_algebra',corrupt)
    lesson=create_lesson(BRIDGE+'\n? impedance p 0')
    assert lesson['outcome']=='refusal' and lesson['cause']=='path_disagreement'
    assert 'answer' not in lesson


def test_wrong_port_sign_from_kernel_is_rejected(monkeypatch):
    real=lesson_ac_port.analyze_ac_port
    def corrupt(ir,port):
        fact=real(ir,port)
        return replace(fact,impedance=replace(fact.impedance,amount=-fact.impedance.amount))
    monkeypatch.setattr(lesson_ac_port,'analyze_ac_port',corrupt)
    lesson=create_lesson(BRIDGE+'\n? impedance p 0')
    assert lesson['outcome']=='refusal' and lesson['cause']=='path_disagreement'


def test_port_math_and_full_probe_algebra_survive_json_and_pdf_without_fake_original_component():
    lesson=json.loads(json.dumps(create_lesson(BRIDGE+'\n? impedance p 0')))
    assert lesson['algebra']['canonical_proof'] is False
    assert lesson['algebra']['status']=='EXACT_OPERATIONS_CHECKED'
    operations={s['algebra']['operation'] for s in lesson['steps'] if 'algebra' in s}
    assert operations=={'substitute','eliminate','solution','recover'}
    for step in lesson['steps']:
        if 'math' in step:assert step['equations']==[equation_text(e) for e in step['math']]
        assert 'j*(0)' not in '\n'.join(step['equations'])
    probe=lesson['port_analysis']['test_source']['id']
    assert probe not in lesson['original']
    assert any(probe in s['svg'] for s in lesson['steps'])
    assert lesson['steps'][-1]['svg']==lesson['original']
    assert lesson['answer']['math']==number(lesson_ac_port.Cyc12(tuple(map(F,lesson['answer']['complex_impedance']['coefficients']))))
    assert export_pdf(lesson).startswith(b'%PDF-1.4')


def test_mcp_stdio_serves_the_same_port_impedance_and_probe_algebra():
    import asyncio
    import sys
    pytest.importorskip('mcp')
    from mcp import Client, StdioServerParameters
    text=BRIDGE+'\n? impedance p 0'
    expected=create_lesson(text)
    async def run():
        params=StdioServerParameters(command=sys.executable,args=['-m','kirchhoff.api.mcp_server'])
        async with Client(params) as client:
            result=await client.call_tool('solve_circuit',{'netlist':text,'method':'test_current'})
            assert not result.is_error
            actual=result.structured_content
            for key in ('answer','algebra','port_analysis','conventions','verification','steps'):
                assert actual[key]==expected[key]
            rejected=await client.call_tool('solve_circuit',{'netlist':text,'method':'phasor'})
            assert rejected.is_error and rejected.structured_content is None
    asyncio.run(run())


def test_http_serves_port_impedance_and_the_same_pdf():
    import http.client
    import importlib.util
    from pathlib import Path
    from threading import Thread
    path=Path(__file__).resolve().parents[1]/'scripts'/'serve_student.py'
    spec=importlib.util.spec_from_file_location('ac_port_http_server',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    server=module.ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        text=BRIDGE+'\n? impedance p 0'
        connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=20)
        payload=json.dumps({'netlist':text,'method':'test_current'})
        connection.request('POST','/api/solve',payload,{'Content-Type':'application/json'})
        response=connection.getresponse();actual=json.loads(response.read())
        assert response.status==200
        expected=create_lesson(text)
        for key in ('answer','algebra','port_analysis','conventions','verification','steps'):
            assert actual[key]==expected[key]
        connection.request('POST','/api/pdf',payload,{'Content-Type':'application/json'})
        response=connection.getresponse();pdf=response.read()
        assert response.status==200 and response.getheader('Content-Type')=='application/pdf'
        assert pdf==export_pdf(actual)
        connection.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
