"""The lesson diagram must not turn supported reactive parts into unknown symbols."""

import xml.etree.ElementTree as ET
from fractions import Fraction as F
import re

import pytest

from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.pipeline.lesson_svg import schematic
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_pdf import _drawing, export_pdf


SVG = "{http://www.w3.org/2000/svg}"


def test_phasor_diagram_names_and_draws_each_supported_element():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a", "b"), (
        Component.of("V1", "voltage_source_ac", ("a", "0"), F(10), "V1", phase_steps=1),
        Component.of("R1", "resistor", ("a", "b"), F(3), "R1"),
        Component.of("L1", "inductor", ("b", "0"), F(2), "L1"),
        Component.of("C1", "capacitor", ("b", "0"), F(1, 100), "C1"),
        Component.of("I1", "current_source_ac", ("0", "a"), F(2), "I1", phase_steps=-2),
    ), (Request("q1", "voltage", "C1"),), omega=F(100))
    first = schematic(ir)
    assert first == schematic(ir)
    root = ET.fromstring(first)
    symbols = [e.get("data-symbol") for e in root.iter() if e.get("data-symbol")]
    assert sorted(symbols) == ["capacitor", "current_source_ac", "inductor", "voltage_source_ac"]
    labels = [e.text for e in root.iter(f"{SVG}text")]
    assert "10 V ∠ 30°" in labels
    assert "2 A ∠ -60°" in labels
    assert "2 H" in labels
    assert "0.01 F" in labels
    assert "?" not in labels


def test_pdf_preserves_inductor_cubic_control_points():
    svg = '<svg viewBox="0 0 100 100"><path d="M10 20 C11 21 12 22 13 23 L14 24"/></svg>'
    drawing, _ = _drawing(svg, ytop=400, max_height=100)
    assert '257.500 380.000 m' in drawing
    assert '258.500 379.000 259.500 378.000 260.500 377.000 c' in drawing
    assert '261.500 376.000 l' in drawing


@pytest.mark.parametrize('path,reason', [('M10 20 Q11 21 12 22', 'Comando'), ('M10 20 C11 21', 'incomplete')])
def test_pdf_refuses_unsupported_or_incomplete_curves(path, reason):
    with pytest.raises(ValueError, match=reason):
        _drawing(f'<svg viewBox="0 0 100 100"><path d="{path}"/></svg>')


def test_complete_ac_lesson_pdf_keeps_phase_equations_and_actual_coils():
    lesson = create_lesson('@ac 100 rad/s\nV1 a 0 10 volt 30deg\nR1 a b 3 ohm\n'
                           'L1 b c 1/25 henry\nC1 c 0 1/100 farad\n? current R1')
    pdf = export_pdf(lesson)
    assert pdf.startswith(b'%PDF-1.4') and pdf.endswith(b'%%EOF\n')
    readable = pdf.replace(b'\\(', b'(').replace(b'\\)', b')')
    assert b'10 V angolo 30' in readable
    formulas = '\n'.join(bytes.fromhex(value.decode()).decode('utf-16-be')
                         for value in re.findall(rb'/ActualText <FEFF([A-F0-9]+)>',pdf))
    assert 'Z(L1) = j4 Ω' in formulas
    assert 'Z(C1) = −j Ω' in formulas
    assert 'sqrt(3)' in formulas
    assert 'j*(0)' not in formulas
    # Si conservano tutte le cubiche degli snapshot: bobine e ponticelli
    # del routing generale sono entrambi geometria reale della lezione.
    curves = re.findall(rb'^[-.\d]+ [-.\d]+ [-.\d]+ [-.\d]+ [-.\d]+ [-.\d]+ c$', pdf, re.M)
    source_curves = sum(path.get('d', '').count('C') for svg in [lesson['original'], *[step['svg'] for step in lesson['steps']]]
                        for path in ET.fromstring(svg).iter(f'{SVG}path'))
    assert source_curves >= 4 * (len(lesson['steps']) + 1)
    assert len(curves) == source_curves
