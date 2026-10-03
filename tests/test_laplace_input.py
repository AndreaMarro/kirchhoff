"""Waveform e condizioni iniziali esplicite, senza carrier ingannevoli."""
from dataclasses import replace
from fractions import Fraction as F
import json

import pytest

from kirchhoff.domain.ir import canonicalize
from kirchhoff.domain.laplace import solve_laplace
from kirchhoff.pipeline.laplace_input import parse_laplace, LaplaceSource
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.lesson_svg import schematic
from kirchhoff.pipeline.lesson_pdf import _drawing


RC='@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 1/3 farad\n@initial C1 voltage 4 volt\n? voltage C1'


def test_typed_input_preserves_explicit_sources_initials_and_exact_serialization():
    parsed=parse_laplace(RC)
    assert parsed.ir==leggi(RC) and parsed.ir.domain=='laplace'
    assert parsed.ir.component('V1').value.amount==0
    assert parsed.sources[0].amplitude==10
    assert parsed.capacitor_voltages==( ('C1',F(4)), )
    assert parsed.inductor_currents==()
    wire=json.loads(json.dumps(parsed.to_json()))
    assert wire['sources'][0]['amplitude']==dict(exact='10',unit='V')
    assert wire['sources'][0]['transform']==dict(numerator=['10'],denominator=['0','1'])
    assert wire['capacitor_voltages']==[dict(component='C1',exact='4',unit='V')]


def test_component_and_initial_order_changes_preserve_electrical_problem():
    shuffled='@laplace\n@initial C1 voltage 4 volt\nC1 a 0 1/3 farad\nR1 e a 2 ohm\nV1 e 0 10 volt step\n? voltage C1'
    first,second=parse_laplace(RC),parse_laplace(shuffled)
    assert canonicalize(first.ir)==canonicalize(second.ir)
    assert solve_laplace(first.ir,**first.solver_inputs).solution==solve_laplace(second.ir,**second.solver_inputs).solution


def test_impulse_area_and_delta_label_survive_svg_and_pdf_projection():
    text=RC.replace('10 volt step','3/2 volt*s impulse')
    parsed=parse_laplace(text)
    assert parsed.sources[0].unit=='V*s' and parsed.sources[0].transform==F(3,2)
    svg=schematic(parsed.ir,source_labels=parsed.source_labels)
    assert '3/2 V*s · δ(t)' in svg and '0 V</text>' not in svg
    assert '3/2 V*s' in _drawing(svg)[0] and 'delta' in _drawing(svg)[0]
    carrier=replace(parsed.ir,components=tuple(replace(c,value=replace(c.value,amount=F(999))) if c.id=='V1' else c for c in parsed.ir.components))
    assert schematic(carrier,source_labels=parsed.source_labels)==svg
    assert solve_laplace(carrier,**parsed.solver_inputs)==solve_laplace(parsed.ir,**parsed.solver_inputs)
    with pytest.raises(ValueError,match='autorevoli'):schematic(parsed.ir)
    with pytest.raises(ValueError):schematic(parsed.ir,source_labels={'V1':''})
    with pytest.raises(ValueError):schematic(leggi('V1 a 0 1 volt\nR1 a 0 1 ohm\n? current R1'),source_labels={'V1':'fake'})


def test_current_impulse_and_inductor_initial_current_keep_passive_orientation():
    text='@laplace\nI1 0 a -2 ampere*s impulse\nR1 a 0 3 ohm\nL1 a 0 2 henry\n@initial L1 current -4 ampere\n? current L1'
    parsed=parse_laplace(text)
    assert parsed.sources[0].label=='-2 A*s · δ(t)'
    assert parsed.inductor_currents==( ('L1',F(-4)), )
    assert parsed.to_json()['inductor_currents'][0]['unit']=='A'


@pytest.mark.parametrize('text',[
    RC.replace('@laplace','@laplace extra'),RC.replace('@laplace','@laplace\n@laplace'),
    RC.replace('@laplace','R0 b 0 2 ohm\n@laplace'),RC.replace('@laplace','@laplace\n@ac 2 rad/s'),
    RC.replace('@laplace','@laplace\n@amplitude rms'),RC.replace(' volt step',' volt'),
    RC.replace(' volt step',' volt*s step'),RC.replace(' volt step',' volt impulse'),
    RC.replace('10 volt','1/0 volt'),RC.replace('10 volt','nope volt'),
    RC.replace('@initial C1 voltage 4 volt',''),RC.replace('@initial C1 voltage 4 volt','@initial C1 voltage 4 volt\n@initial C1 voltage 0 volt'),
    RC.replace('@initial C1 voltage 4 volt','@initial C1 current 4 ampere'),
    RC.replace('@initial C1 voltage 4 volt','@initial R1 voltage 4 volt'),
    RC.replace('@initial C1 voltage 4 volt','@initial C1 voltage 4 ampere'),
    RC.replace('@initial C1 voltage 4 volt','@initial C1 voltage nope volt'),
    RC.replace('? voltage C1','? power C1'),RC.replace('? voltage C1','? impedance a 0'),
    RC.replace('? voltage C1','? voltage C1\n? current C1'),RC.replace('? voltage C1',''),
    RC+'\nR2 a 0 3 ohm',RC+'\n@initial C1 voltage 0 volt',RC.replace('R1 e a 2 ohm','G1 e a e 0 2 siemens'),
])
def test_ambiguous_mixed_or_incomplete_laplace_input_is_rejected(text):
    with pytest.raises(ValueError):parse_laplace(text)


def test_metadata_constructor_refuses_implicit_waveforms_and_inexact_amplitude():
    with pytest.raises(ValueError):LaplaceSource('V1','voltage','guess',F(3))
    with pytest.raises(TypeError):LaplaceSource('V1','voltage','step',3.0)
