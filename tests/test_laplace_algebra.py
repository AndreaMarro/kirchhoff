from copy import deepcopy
from fractions import Fraction as F

import pytest

from kirchhoff.domain.laplace import solve_laplace
from kirchhoff.domain.laplace_rational import RationalFunction as RF
from kirchhoff.pipeline.laplace_input import parse_laplace
from kirchhoff.pipeline.lesson_laplace_algebra import build_laplace_algebra, rational_math
from kirchhoff.pipeline.lesson_laplace_check import verify_laplace_algebra, verify_laplace_presentation, Q, decode, expression, scalar
from kirchhoff.pipeline.lesson_math import equation, equation_text, symbol

CASES = [
    '@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 1/3 farad\n@initial C1 voltage 4 volt\n? voltage C1',
    '@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nL1 a 0 3 henry\n@initial L1 current -2 ampere\n? current L1',
    '@laplace\nV1 e 0 10 volt*s impulse\nR1 e a 2 ohm\nL1 a b 3 henry\nC1 b 0 1/3 farad\n@initial L1 current 2 ampere\n@initial C1 voltage -4 volt\n? voltage L1',
    '@laplace\nV1 a b 5 volt step\nR1 a 0 2 ohm\nR2 b 0 3 ohm\nI1 0 b 2 ampere*s impulse\nC1 a 0 1/2 farad\nL1 b 0 4 henry\n@initial C1 voltage 3 volt\n@initial L1 current -1 ampere\n? current V1',
    '@laplace\nV1 a 0 5 volt step\nC1 a 0 2 farad\n@initial C1 voltage 3 volt\n? current C1',
    '@laplace\nL1 a 0 3 henry\n@initial L1 current 2 ampere\n? voltage L1',
]


def fixture(text=CASES[2]):
    parsed = parse_laplace(text)
    solved = solve_laplace(parsed.ir, **parsed.solver_inputs)
    proof = build_laplace_algebra(parsed, solved)
    return parsed, solved, proof


@pytest.mark.parametrize('text', CASES)
def test_exact_substitution_elimination_and_all_branches(text):
    parsed, solved, proof = fixture(text)
    verify_laplace_algebra(parsed, proof, solved)
    assert proof['canonical_proof'] is False
    assert proof['groups'] and proof['branches']
    assert all('j*(0)' not in equation_text(eq) for eq in proof['laws'])


def test_rc_exact_oracle_with_initial_voltage():
    parsed, solved, proof = fixture(CASES[0])
    verify_laplace_algebra(parsed, proof, solved)
    # C dv/dt + (v-10)/R = 0: (s+3/2)V = 4+15/s.
    assert solved.branch('C1').voltage == RF((F(15),F(4)), (F(0),F(3,2),F(1)))
    assert solved.branch('C1').current == RF((F(3),), (F(3,2),F(1)))


@pytest.mark.parametrize('mutation', ['coefficient','rhs','substituted','collected','factor','after','donor','remove','group','solution','branch','reference','unit','law','source','ic','zero_scale'])
def test_mutations_fail_closed(mutation):
    parsed, solved, proof = fixture()
    altered = deepcopy(proof)
    rf = RF.of(987).to_json()
    if mutation == 'coefficient': altered['initial'][0]['row'][0] = rf
    elif mutation == 'rhs': altered['initial'][0]['row'][-1] = rf
    elif mutation in {'substituted','collected'}: altered['initial'][0][mutation]['right'] = rational_math(RF.of(987))
    elif mutation == 'factor': altered['operations'][0 if altered['operations'][0]['kind']=='scale' else 1]['factor'] = rf
    elif mutation == 'zero_scale': next(op for op in altered['operations'] if op['kind']=='scale')['factor'] = RF.of(0).to_json()
    elif mutation == 'after': next(op for op in altered['operations'] if op['kind']=='scale')['after'][0] = rf
    elif mutation == 'donor': next(op for op in altered['operations'] if op['kind']=='eliminate')['donor'][0] = rf
    elif mutation == 'remove': altered['operations'].pop()
    elif mutation == 'group': altered['groups'][0]['operations'] = []
    elif mutation == 'solution': altered['solution'][next(iter(altered['solution']))] = rf
    elif mutation == 'branch': altered['branches'][0]['voltage_value'] = rf
    elif mutation == 'reference': altered['branches'][0]['reference'].reverse()
    elif mutation == 'unit': altered['initial'][0]['collected']['unit'] = 'V'
    elif mutation == 'law': altered['laws'][0]['right'] = rational_math(RF.of(987))
    elif mutation in {'source','ic'}: altered['declarations'][0 if mutation=='source' else -1]['right'] = rational_math(RF.of(987))
    with pytest.raises((ValueError, IndexError)):
        verify_laplace_algebra(parsed, altered, solved)


def test_independent_arithmetic_does_not_use_primary_multiply(monkeypatch):
    parsed, solved, proof = fixture()
    monkeypatch.setattr(RF, '__mul__', lambda *args: (_ for _ in ()).throw(AssertionError('primary field called')))
    verify_laplace_algebra(parsed, proof, solved)


def test_presented_equation_and_answer_must_match_checked_solution():
    parsed, solved, proof = fixture()
    value = solved.branch('L1').voltage
    answer = dict(quantity='voltage',unit='V*s',reference='a → b',math=rational_math(value),
                  laplace_transform=dict(variable='s',coefficient_order='ascending',**value.to_json()))
    from kirchhoff.pipeline.lesson import create_lesson
    lesson = create_lesson(CASES[2])
    steps = lesson['steps']
    verify_laplace_presentation(parsed,proof,solved,steps,answer)
    steps[-3]['math'][0]['right'] = rational_math(RF.of(999))
    steps[-3]['equations'] = [equation_text(eq) for eq in steps[-3]['math']]
    with pytest.raises(ValueError,match='passaggio'):
        verify_laplace_presentation(parsed,proof,solved,steps,answer)
    steps = lesson['steps'] = create_lesson(CASES[2])['steps']
    for field, bad in [('unit','V'),('reference','b → a'),('quantity','current')]:
        changed = dict(answer,**{field:bad})
        with pytest.raises(ValueError): verify_laplace_presentation(parsed,proof,solved,steps,changed)
    changed = deepcopy(answer)
    changed['laplace_transform']['numerator'] = ['99']
    with pytest.raises(ValueError): verify_laplace_presentation(parsed,proof,solved,steps,changed)


@pytest.mark.parametrize('raw', [None,{}, {'numerator':[],'denominator':['1']}, {'numerator':['0','0'],'denominator':['1']},
                                {'numerator':['01'],'denominator':['1']}, {'numerator':['1'],'denominator':['2']},
                                {'numerator':['1'],'denominator':['0']}])
def test_independent_decoder_rejects_invalid(raw):
    with pytest.raises((ValueError,TypeError)): decode(raw)


def test_checker_rejects_nonlinear_unknown_expressions():
    context = {'x':[scalar(1),scalar(0)],'s':[scalar(0),scalar(2)]}
    for expr in [{'kind':'multiply','args':[symbol('x'),symbol('x')]},
                 {'kind':'divide','numerator':symbol('s'),'denominator':symbol('x')}, {'kind':'evil'}]:
        with pytest.raises(ValueError): expression(expr,context)
