"""La lezione espone l'algebra; un'altra aritmetica controlla ogni passaggio."""
from copy import deepcopy
from fractions import Fraction as F
import json

import pytest

from kirchhoff.domain.independent_phasor import solve_phasor_tableau
from kirchhoff.pipeline import lesson_ac
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_ac_algebra import build_algebra
from kirchhoff.pipeline.lesson_ac_algebra_check import verify_algebra
from kirchhoff.pipeline.lesson_math import equation_text, expression_text, number
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.pipeline.netlist import leggi


BRIDGE = ('@ac 100 rad/s\n@amplitude rms\nV1 s 0 10 volt 0deg\nR1 s x 2 ohm\n'
          'R2 s y 3 ohm\nL1 x 0 1/25 henry\nC1 y 0 1/100 farad\n'
          'R3 x y 5 ohm\nI1 0 y 2 ampere -90deg\n? current R3')
FLOATING = ('@ac 100 rad/s\n@amplitude peak\nV1 a b 12 volt 30deg\nI1 0 a 3 ampere -90deg\n'
            'R1 a 0 2 ohm\nC1 b c 1/50 farad\nL1 c 0 1/20 henry\nR2 b 0 4 ohm\n? power V1')


def numeric(expr):
    # Proiezione numerica indipendente solo per i confronti Cramer di sviluppo.
    a,b,c,d = map(F, expr['coefficients'])
    return complex(float(a+c/2)+float(b/2)*3**.5, float(d+b/2)+float(c/2)*3**.5)


@pytest.mark.parametrize('source', [BRIDGE, FLOATING, BRIDGE.replace('10 volt 0deg', '10 volt 150deg'),
    '@ac 2 rad/s\nI1 0 a 0 ampere 0deg\nR1 a 0 3 ohm\n? voltage R1',
    '@ac 2 rad/s\nV1 a 0 4 volt 90deg\nR1 a 0 2 ohm\n? current V1'])
def test_complete_algebra_is_json_portable_and_keeps_limited_claim(source):
    lesson = json.loads(json.dumps(create_lesson(source)))
    assert lesson['outcome'] == 'solved'
    assert lesson['algebra']['status'] == 'EXACT_OPERATIONS_CHECKED'
    assert lesson['algebra']['canonical_proof'] is False
    assert lesson['verification']['product_verified'] is False
    ir = leggi(source)
    verify_algebra(ir, lesson['algebra'], solve_phasor_tableau(ir))
    phases = {step['algebra']['operation'] for step in lesson['steps'] if 'algebra' in step}
    assert phases == {'substitute', 'eliminate', 'solution', 'recover'}
    for step in lesson['steps']:
        if 'math' in step:
            assert step['equations'] == [equation_text(expr) for expr in step['math']]
        assert 'j*(0)' not in '\n'.join(step['equations'])
    assert lesson['answer']['display_exact'] == expression_text(lesson['answer']['math'])
    assert export_pdf(lesson).startswith(b'%PDF-1.4')


@pytest.mark.parametrize('phase', [0,30,90,150,240])
def test_bridge_unknowns_match_manually_written_two_node_cramer(phase):
    # Nessun assemblatore o solver nell'oracolo: KCL x e y con sorgente s nota.
    import cmath
    text = BRIDGE.replace('10 volt 0deg', f'10 volt {phase}deg')
    proof = create_lesson(text)['algebra']
    source = 10*cmath.exp(1j*phase*cmath.pi/180)
    a, b, d = .7-.25j, -.2, 8/15+1j
    u, v = source/2, source/3-2j
    x, y = (u*d-b*v)/(a*d-b*b), (a*v-b*u)/(a*d-b*b)
    assert numeric(proof['solution']['V(x)']) == pytest.approx(x, rel=1e-13, abs=1e-13)
    assert numeric(proof['solution']['V(y)']) == pytest.approx(y, rel=1e-13, abs=1e-13)
    source_current = -((source-x)/2+(source-y)/3)
    assert numeric(proof['solution']['I(V1)']) == pytest.approx(source_current, rel=1e-13, abs=1e-13)


def test_floating_voltage_constraint_and_current_unknown_survive_substitution():
    lesson = create_lesson(FLOATING)
    proof = lesson['algebra']
    source = next(entry for entry in proof['initial'] if entry['origin'] == 'source')
    assert source['component'] == 'V1'
    text = equation_text(source['substituted'])
    assert 'V(a) − V(b)' in text
    assert 'I(V1)' in proof['solution']
    assert numeric(proof['solution']['V(a)'])-numeric(proof['solution']['V(b)']) == pytest.approx(complex(6*3**.5,6))
    assert lesson['answer']['complex_power']['active']['unit'] == 'W'


def _corrupt(proof, kind):
    if kind == 'coefficient':
        proof['initial'][0]['row'][0][0] = '99'
    elif kind == 'substitution_sign':
        proof['initial'][0]['substituted']['left']['args'][0] = number(123)
    elif kind == 'collected_equation':
        proof['initial'][0]['collected']['right'] = number(123)
    elif kind == 'missing_equation':
        proof['initial'].pop()
    elif kind == 'origin':
        proof['initial'][0]['node'] = 'invented'
    elif kind == 'unit':
        proof['initial'][0]['substituted']['unit'] = 'V'
    elif kind == 'group_variable':
        proof['groups'][0]['variable'] = 'I(invented)'
    elif kind == 'missing_step':
        proof['operations'].pop(0)
    elif kind == 'factor':
        next(op for op in proof['operations'] if op['kind'] == 'eliminate')['factor'] = number(123)
    elif kind == 'zero_scale':
        next(op for op in proof['operations'] if op['kind'] == 'scale')['factor'] = number(0)
    elif kind == 'before':
        next(op for op in proof['operations'] if op['kind'] == 'scale')['before'][0][0] = '123'
    elif kind == 'after':
        next(op for op in proof['operations'] if op['kind'] == 'eliminate')['after'][-1][0] = '123'
    elif kind == 'step_equation':
        next(op for op in proof['operations'] if op['kind'] == 'eliminate')['equation']['right'] = number(123)
    elif kind == 'rationalization':
        next(op for op in proof['operations'] if op['kind'] == 'scale')['normalization'][0]['right'] = number(123)
    elif kind == 'solution':
        proof['solution']['V(x)'] = number(123)
    elif kind == 'recover':
        proof['branches'][1]['current'] = number(123)
    elif kind == 'reference':
        proof['branches'][1]['reference'].reverse()
    elif kind == 'canonical':
        proof['canonical_proof'] = True
    return proof


@pytest.mark.parametrize('kind', ['coefficient','substitution_sign','collected_equation','missing_equation',
    'origin','unit','group_variable','missing_step','factor','zero_scale','before','after','step_equation',
    'rationalization','solution','recover','reference','canonical'])
def test_corrupted_algebra_fails_independent_checker_and_service_before_answer(monkeypatch, kind):
    ir = leggi(BRIDGE)
    bad = _corrupt(deepcopy(build_algebra(ir)), kind)
    with pytest.raises(ValueError, match='Derivazione algebrica non verificata'):
        verify_algebra(ir, bad, solve_phasor_tableau(ir))
    monkeypatch.setattr(lesson_ac, 'build_algebra', lambda _: bad)
    refused = create_lesson(BRIDGE)
    assert refused['outcome'] == 'refusal' and refused['cause'] == 'path_disagreement'
    assert 'answer' not in refused and 'verification' not in refused


def test_complex_subtraction_preserves_parentheses_and_zero_is_not_a_phasor_dump():
    from kirchhoff.domain.exact import J
    from kirchhoff.pipeline.lesson_math import add, multiply
    assert expression_text(number(0)) == '0'
    assert expression_text(number(3)) == '3'
    assert expression_text(number(-J)) == '−j'
    expr = add(number(3+J), multiply(number(-1), number(2-5*J)))
    assert expression_text(expr) == '3 + j − (2 − j5)'
    assert expression_text(add(number(3),number(-10))) == '3 − 10'
    assert expression_text(add(number(3),multiply(number(F(-1,3)),number(9)))) == '3 − (1/3) · (9)'
    from kirchhoff.pipeline.lesson_math import symbol
    assert expression_text(add(symbol('V(a)'),multiply(number(-2),symbol('V(b)')))) == 'V(a) − (2) · V(b)'
    assert expression_text(add(number(3),multiply(number(1),number(-10)))) == '3 − 10'
