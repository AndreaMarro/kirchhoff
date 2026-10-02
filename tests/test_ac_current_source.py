"""Una sorgente AC di corrente è un fasore orientato, non una sorgente DC."""

from fractions import Fraction as F

import pytest

from kirchhoff.domain.exact import Cyc12, J, ZERO
from kirchhoff.domain.ir import Component, IR
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.domain.independent_phasor import solve_phasor_tableau
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import phasor_complex_powers, verify


def test_current_phasor_orients_injection_and_two_assemblies_agree():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (
        Component.of("I1", "current_source_ac", ("0", "a"), F(2), "I1", phase_steps=3),
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
    ), (), omega=F(100))
    mna = solve_phasor(ir)
    assert mna == solve_phasor_tableau(ir)
    assert mna["I1"]["current"] == J * Cyc12.of(2)
    assert mna["R1"]["current"] == J * Cyc12.of(2)
    assert mna["R1"]["voltage"] == J * Cyc12.of(10)
    assert verify(ir, mna) is None
    powers = phasor_complex_powers(ir, mna, amplitude="rms")
    assert powers["R1"] == Cyc12.of(20)
    assert sum(powers.values(), ZERO) == ZERO


def test_only_current_ac_source_requires_frequency_and_dc_source_cannot_have_phase():
    source = Component.of("I1", "current_source_ac", ("0", "a"), F(1), "I1", phase_steps=1)
    assert source.value.unit == "ampere"
    with pytest.raises(ValueError, match="pulsazione positiva"):
        IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (source,), ())
    with pytest.raises(ValueError, match="sfasamento"):
        Component.of("I1", "current_source_dc", ("0", "a"), F(1), "I1", phase_steps=1)


def test_ac_current_only_cut_detects_nonzero_kcl_but_accepts_balanced_pair():
    def network(second):
        return IR("1.0.0", "ac_sinusoidal", "generated", ("0", "x", "b"), (
            Component.of("I1", "current_source_ac", ("0", "x"), F(2), "I1", phase_steps=3),
            Component.of("I2", "current_source_ac", ("x", "0"), F(second), "I2", phase_steps=3),
            Component.of("R1", "resistor", ("b", "0"), F(5), "R1"),
            Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
        ), (), omega=F(100))
    bad = validate(network(1))
    assert isinstance(bad, Refusal) and bad.subject == "x" and bad.cause == "topology"
    assert isinstance(validate(network(2)), Validated)


def test_ac_current_cut_compares_full_phasors_instead_of_scalar_amplitudes():
    def network(second_phase):
        return IR("1.0.0", "ac_sinusoidal", "generated", ("0", "x", "b"), (
            Component.of("I1", "current_source_ac", ("0", "x"), F(2), "I1", phase_steps=3),
            Component.of("I2", "current_source_ac", ("0", "x"), F(2), "I2", phase_steps=second_phase),
            Component.of("R1", "resistor", ("b", "0"), F(5), "R1"),
            Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
        ), (), omega=F(100))

    assert isinstance(validate(network(9)), Validated)  # +j2 - j2 = 0
    bad = validate(network(3))                         # +j2 + j2 != 0
    assert isinstance(bad, Refusal) and bad.subject == "x"
