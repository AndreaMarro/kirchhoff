"""Percorso servito Laplace, PDF e metadati portabili, nessuna prova canonica inventata."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import json

import pytest

from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.pipeline import lesson_laplace as module
from kirchhoff.pipeline.lesson_math import equation_text
from kirchhoff.domain.laplace_rational import RationalFunction as RF

RC='@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 1/3 farad\n@initial C1 voltage 4 volt\n? voltage C1'


def test_single_served_entry_returns_exact_initial_condition_lesson():
    lesson=create_lesson(RC)
    assert lesson['outcome']=='solved'
    assert lesson['answer']['laplace_transform']==dict(variable='s',coefficient_order='ascending',numerator=['15','4'],denominator=['0','3/2','1'])
    assert lesson['answer']['unit']=='V*s' and lesson['answer']['reference']=='a → 0'
    assert lesson['method']=='laplace' and lesson['available']==['auto','laplace']
    assert lesson['verification']['product_verified'] is False and lesson['algebra']['canonical_proof'] is False
    assert lesson['verification']['checks']==module.CHECKS
    assert lesson['laplace_output']==dict(time_domain_evaluated=False,contains_impulse_terms=False,polynomial_part_degree=None)
    for step in lesson['steps']:
        assert step['equations']==[equation_text(eq) for eq in step['math']]
        assert 'j*(0)' not in '\n'.join(step['equations'])
        assert '0 V</text>' not in step['svg']
    assert any('4' in text and 'v0(C1)' in text for text in lesson['steps'][0]['equations'])
    assert len(lesson['steps'])>=10


def test_json_roundtrip_and_pdf_share_ast_and_revision():
    lesson=create_lesson(RC,'laplace')
    restored=json.loads(json.dumps(lesson,ensure_ascii=False))
    assert restored==lesson
    pdf=export_pdf(restored)
    assert pdf.startswith(b'%PDF-1.4') and b'/ActualText' in pdf
    assert lesson['lesson_build'].encode('utf-16-be').hex().upper().encode() in pdf
    assert export_pdf(lesson)==pdf


@pytest.mark.parametrize('source', ['0 volt step','3/2 volt*s impulse','-2 volt step'])
def test_explicit_source_waveform_is_preserved(source):
    lesson=create_lesson(RC.replace('10 volt step',source))
    assert lesson['outcome']=='solved'
    metadata=lesson['laplace_inputs']['sources'][0]
    assert metadata['waveform']==source.split()[-1]
    assert metadata['amplitude']['exact']==source.split()[0]
    assert ('δ(t)' if 'impulse' in source else 'u(t)') in lesson['original']
    if source.startswith('0 '): assert metadata['transform']==dict(numerator=['0'],denominator=['1'])


def test_rl_free_response_passive_sign_and_capacitor_impulse():
    rl=create_lesson('@laplace\nR1 a 0 2 ohm\nL1 a 0 3 henry\n@initial L1 current -2 ampere\n? current L1')
    assert rl['answer']['laplace_transform']==dict(variable='s',coefficient_order='ascending',numerator=['-2'],denominator=['2/3','1'])
    impulse=create_lesson('@laplace\nV1 a 0 5 volt step\nC1 a 0 2 farad\n@initial C1 voltage 3 volt\n? current C1')
    assert impulse['answer']['laplace_transform']==dict(variable='s',coefficient_order='ascending',numerator=['4'],denominator=['1'])
    assert impulse['laplace_output']['contains_impulse_terms'] is True
    assert impulse['laplace_output']['polynomial_part_degree']==0


def test_reordered_netlist_preserves_answer_and_initial_metadata():
    lines=RC.splitlines()
    shuffled='\n'.join([lines[0],lines[4],lines[3],lines[2],lines[1],lines[5]])
    first,second=create_lesson(RC),create_lesson(shuffled)
    assert first['answer']==second['answer']
    assert first['laplace_inputs']==second['laplace_inputs']
    assert first['fingerprint']!=second['fingerprint']


@pytest.mark.parametrize('method',['nodal','test_current','phasor'])
def test_incompatible_method_rejected(method):
    with pytest.raises(ValueError,match='Laplace'):create_lesson(RC,method)
    with pytest.raises(ValueError,match='@laplace'):create_lesson('V1 a 0 2 volt\nR1 a 0 3 ohm\n? current R1','laplace')


def test_singular_and_missing_initials_fail_closed():
    lesson=create_lesson('@laplace\nI1 0 a 1 ampere step\n? voltage I1')
    assert lesson['outcome']=='refusal' and lesson['cause']=='unsolvable'
    with pytest.raises(ValueError):create_lesson(RC.replace('@initial C1 voltage 4 volt\n',''))


@pytest.mark.parametrize('corrupt',['factor','projection','answer'])
def test_mutations_in_served_path_are_refused(monkeypatch,corrupt):
    if corrupt=='factor':
        original=module.build_laplace_algebra
        def bad(*args):
            proof=original(*args)
            next(op for op in proof['operations'] if op['kind']=='scale')['factor']=RF.of(2).to_json()
            return proof
        monkeypatch.setattr(module,'build_laplace_algebra',bad)
    elif corrupt=='projection':
        import kirchhoff.pipeline.lesson as base
        original=base._checked_step
        def bad(*args,**kwargs):
            result=original(*args,**kwargs)
            result['equations']=['fake = 1']
            return result
        monkeypatch.setattr(base,'_checked_step',bad)
        # Text projection comparison belongs to presentation checker.
    else:
        original=module.rational_math
        monkeypatch.setattr(module,'rational_math',lambda v:original(v+1))
    result=create_lesson(RC)
    assert result['outcome']=='refusal' and result['cause']=='path_disagreement'


def test_capability_advertises_only_transformed_response_and_real_method():
    from kirchhoff.pipeline.capabilities import product_capabilities
    capability=product_capabilities(RC)
    assert capability['transients'] is True
    assert capability['laplace_scope']['source_waveforms']==['step','impulse']
    assert capability['laplace_scope']['inverse_transform'] is False
    assert capability['laplace_scope']['topology_switching'] is False
    assert capability['laplace_scope']['certified_lesson'] is False
    assert capability['circuit']['available_methods']==['auto','laplace']
    missing=product_capabilities(RC.replace('@initial C1 voltage 4 volt\n',''))
    assert missing['circuit']['outcome']=='invalid'


@pytest.mark.parametrize('mutation',['remove','swap','unit','initial','solution','final'])
def test_presentation_cannot_omit_or_exchange_steps(mutation):
    from kirchhoff.pipeline.laplace_input import parse_laplace
    from kirchhoff.domain.laplace import solve_laplace
    from kirchhoff.pipeline.lesson_laplace_check import verify_laplace_presentation
    parsed= parse_laplace(RC)
    result=solve_laplace(parsed.ir,**parsed.solver_inputs)
    lesson=create_lesson(RC)
    steps=deepcopy(lesson['steps'])
    if mutation=='remove': steps.pop(2)
    elif mutation=='swap': steps[2],steps[3]=steps[3],steps[2]
    elif mutation=='unit': steps[-2]['math'][0]['unit']='V'
    elif mutation=='initial': steps[0]['math']=[]
    elif mutation=='solution': steps[-3]['math']=[]
    elif mutation=='final': steps[-1]['math']=[]
    with pytest.raises(ValueError): verify_laplace_presentation(parsed,lesson['algebra'],result,steps,lesson['answer'])


def test_two_capacitors_two_inductors_with_floating_source_and_mixed_waveforms():
    text='''@laplace
V1 a b 3 volt step
I1 0 c 2 ampere*s impulse
R1 a 0 2 ohm
R2 b c 3 ohm
R3 a d 5 ohm
C1 c 0 1/2 farad
C2 b d 1/3 farad
L1 d 0 2 henry
L2 c d 3 henry
@initial C1 voltage 2 volt
@initial C2 voltage -1 volt
@initial L1 current 3 ampere
@initial L2 current -2 ampere
? current L2'''
    lesson=create_lesson(text)
    assert lesson['outcome']=='solved'
    assert len(lesson['algebra']['variables'])==7
    assert len(lesson['algebra']['branches'])==9
    assert lesson['laplace_inputs']['sources'][1]['amplitude']['unit']=='A*s'
    assert lesson['verification']['product_verified'] is False
