"""The lesson diagram must not turn supported reactive parts into unknown symbols."""

import xml.etree.ElementTree as ET
from fractions import Fraction as F

from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.pipeline.lesson_svg import schematic


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
