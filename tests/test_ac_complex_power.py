"""Potenza fasoriale: convenzione esplicita e coniugato della corrente."""

from fractions import Fraction as F
from dataclasses import replace

import pytest

from kirchhoff.domain.exact import J, Cyc12, ZERO
from kirchhoff.domain.ir import Component, IR
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.domain.verify import phasor_complex_powers


def _rl() -> IR:
    return IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a", "b"), (
        Component.of("E1", "voltage_source_ac", ("a", "0"), F(10), "E1"),
        Component.of("R1", "resistor", ("a", "b"), F(30), "R1"),
        Component.of("L1", "inductor", ("b", "0"), F(4, 100), "L1"),
    ), (), omega=F(1000))


def test_rms_power_uses_conjugated_current_and_source_sign():
    ir = _rl()
    powers = phasor_complex_powers(ir, solve_phasor(ir), amplitude="rms")
    assert powers["R1"] == Cyc12.of(F(6, 5))
    assert powers["L1"] == J * Cyc12.of(F(8, 5))
    assert powers["E1"] == -powers["R1"] - powers["L1"]
    assert sum(powers.values(), ZERO) == ZERO


def test_peak_power_requires_one_half_and_differs_from_tellegen_product():
    ir = _rl()
    solution = solve_phasor(ir)
    rms = phasor_complex_powers(ir, solution, amplitude="rms")
    peak = phasor_complex_powers(ir, solution, amplitude="peak")
    assert peak["R1"] == Cyc12.of(F(3, 5))
    assert peak["L1"] == J * Cyc12.of(F(4, 5))
    assert all(peak[cid] * 2 == rms[cid] for cid in rms)
    assert solution["R1"]["voltage"] * solution["R1"]["current"] != rms["R1"]


def test_capacitor_absorbs_negative_reactive_power():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (
        Component.of("E1", "voltage_source_ac", ("a", "0"), F(10), "E1"),
        Component.of("C1", "capacitor", ("a", "0"), F(1, 1000), "C1"),
    ), (), omega=F(100))
    powers = phasor_complex_powers(ir, solve_phasor(ir), amplitude="rms")
    assert powers["C1"] == -J * Cyc12.of(10)
    assert sum(powers.values(), ZERO) == ZERO


def test_without_amplitude_convention_or_phasor_domain_no_power_claim():
    ir = _rl()
    solution = solve_phasor(ir)
    with pytest.raises(TypeError):
        phasor_complex_powers(ir, solution)
    with pytest.raises(ValueError, match="picco|RMS"):
        phasor_complex_powers(ir, solution, amplitude="unknown")
    dc = replace(ir, domain="dc")
    with pytest.raises(ValueError, match="sinusoidale"):
        phasor_complex_powers(dc, solution, amplitude="rms")
    mixed = {cid: dict(values) for cid, values in solution.items()}
    mixed["R1"]["current"] = F(1)
    with pytest.raises(TypeError, match="Cyc12"):
        phasor_complex_powers(ir, mixed, amplitude="rms")
