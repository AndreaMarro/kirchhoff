"""Il controllo fasoriale monta un tableau di ramo, separato dalla MNA."""

from fractions import Fraction as F

import pytest

from kirchhoff.domain.exact import J, Cyc12, ZERO
from kirchhoff.domain.ir import Component, IR
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.domain.independent_phasor import solve_phasor_tableau


def _rl() -> IR:
    return IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a", "b"), (
        Component.of("E1", "voltage_source_ac", ("a", "0"), F(10), "E1"),
        Component.of("R1", "resistor", ("a", "b"), F(30), "R1"),
        Component.of("L1", "inductor", ("b", "0"), F(4, 100), "L1"),
    ), (), omega=F(1000))


def test_rl_branch_tableau_agrees_with_mna_and_exact_series_relation():
    ir = _rl()
    actual = solve_phasor_tableau(ir)
    assert actual == solve_phasor(ir)
    assert actual["R1"]["current"] == Cyc12.of(F(3, 25)) - J * Cyc12.of(F(4, 25))
    assert actual["L1"]["voltage"] == J * Cyc12.of(40) * actual["L1"]["current"]


def test_parallel_capacitor_and_phase_shift_use_independent_branch_equations():
    ir = IR("1.0.0", "three_phase", "generated", ("0", "a"), (
        Component.of("E1", "voltage_source_ac", ("a", "0"), F(10), "E1", phase_steps=4),
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
        Component.of("C1", "capacitor", ("a", "0"), F(1, 1000), "C1"),
    ), (), omega=F(100))
    actual = solve_phasor_tableau(ir)
    assert actual == solve_phasor(ir)
    assert actual["C1"]["current"] == J * Cyc12.of(F(1, 10)) * actual["C1"]["voltage"]
    assert sum((value["voltage"] * value["current"] for value in actual.values()), ZERO) == ZERO


def test_rejects_dc_and_elements_outside_both_phasor_solvers():
    from dataclasses import replace

    ir = _rl()
    with pytest.raises(ValueError, match="fasoriale"):
        solve_phasor_tableau(replace(ir, domain="dc"))
    ir = replace(ir, components=ir.components + (
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
    ))
    with pytest.raises(ValueError, match="I1"):
        solve_phasor_tableau(ir)


def test_conflicting_ideal_sources_are_singular():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (
        Component.of("E1", "voltage_source_ac", ("a", "0"), F(10), "E1"),
        Component.of("E2", "voltage_source_ac", ("a", "0"), F(11), "E2"),
    ), (), omega=F(100))
    with pytest.raises(ValueError, match="singolare"):
        solve_phasor_tableau(ir)


def test_requires_positive_frequency_and_an_actual_network():
    no_source = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
    ), (), omega=F(0))
    with pytest.raises(ValueError, match="pulsazione positiva"):
        solve_phasor_tableau(no_source)
    empty = IR("1.0.0", "ac_sinusoidal", "generated", ("0",), (), (), omega=F(100))
    with pytest.raises(ValueError, match="senza rami"):
        solve_phasor_tableau(empty)


def test_rejects_a_broken_spanning_tree_contract(monkeypatch):
    from kirchhoff.domain import independent_phasor

    ir = _rl()
    monkeypatch.setattr(independent_phasor, "_albero_ricoprente",
                        lambda _: ({"0": None, "a": ("0", "E1"), "b": ("a", "R1")}, frozenset()))
    with pytest.raises(ValueError, match="non quadrato"):
        solve_phasor_tableau(ir)


@pytest.mark.parametrize("seed", [2, 8, 19, 31])
def test_generated_ac_topologies_agree_with_constructive_oracle(seed):
    from kirchhoff.eval.generator_ac import generate_case

    ir, expected, _ = generate_case(seed, depth=2)
    assert solve_phasor_tableau(ir) == expected == solve_phasor(ir)


@pytest.mark.parametrize("seed", [0, 1])
def test_three_phase_star_and_delta_agree_with_constructive_oracle(seed):
    from kirchhoff.eval.generator_three_phase import generate_case

    ir, expected, _ = generate_case(seed)
    assert solve_phasor_tableau(ir) == expected == solve_phasor(ir)
