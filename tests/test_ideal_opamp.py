"""L'operazionale ideale impone V+ = V- senza approssimare il guadagno."""

from fractions import Fraction as F

import pytest

from kirchhoff.domain.exact import Cyc12, J
from kirchhoff.domain.independent_dc import solve_dc_tableau
from kirchhoff.domain.independent_phasor import solve_phasor_tableau
from kirchhoff.domain.ir import Component
from kirchhoff.domain.mna import solve_dc, solve_phasor
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transient import is_natural_frequency
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import constitutive_residuals, verify
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.netlist import leggi


DC = ("V1 vin 0 6 volt\nO1 out 0 vin vm\nRf out vm 10 ohm\n"
      "Rg vm 0 5 ohm\nRL out 0 4 ohm\n? voltage RL")
AC = DC.replace("V1 vin 0 6 volt", "@ac 5 rad/s\nV1 vin 0 6 volt 90deg")


def test_ideal_opamp_dc_is_an_exact_constraint_in_two_independent_solves():
    ir = leggi(DC)
    amp = ir.component("O1")
    assert amp.type == "ideal_opamp"
    assert amp.control_nodes == ("vin", "vm")
    assert isinstance(validate(ir), Validated)
    solution = solve_dc(ir)
    assert solution == solve_dc_tableau(ir)
    assert solution["RL"]["voltage"] == F(18)
    assert solution["O1"]["current"] == -F(57, 10)
    assert constitutive_residuals(ir, solution)["O1"] == 0
    assert verify(ir, solution) is None
    assert create_lesson(DC)["outcome"] == "refusal"


def test_grounded_positive_output_terminal_keeps_kcl_orientation_exact():
    ir = leggi(DC.replace("O1 out 0 vin vm", "O1 0 out vin vm"))
    solution = solve_dc(ir)
    assert solution == solve_dc_tableau(ir)
    assert solution["RL"]["voltage"] == F(18)
    assert solution["O1"]["current"] == F(57, 10)
    assert verify(ir, solution) is None


def test_grounded_negative_control_terminal_has_exact_constraint_stamp():
    ir = leggi("V1 vin 0 6 volt\nO1 out 0 vm 0\nRf out vm 10 ohm\n"
              "Rg vm vin 5 ohm\nRL out 0 4 ohm\n? voltage RL")
    solution = solve_dc(ir)
    assert solution == solve_dc_tableau(ir)
    assert solution["RL"]["voltage"] == -F(12)
    assert constitutive_residuals(ir, solution)["O1"] == 0


def test_ideal_opamp_ac_preserves_phase_without_infinite_gain_approximation():
    ir = leggi(AC)
    solution = solve_phasor(ir)
    assert solution == solve_phasor_tableau(ir)
    assert solution["RL"]["voltage"] == J * Cyc12.of(18)
    assert solution["O1"]["current"] == -J * Cyc12.of(F(57, 10))
    assert constitutive_residuals(ir, solution)["O1"] == 0
    assert verify(ir, solution) is None
    assert create_lesson(AC)["outcome"] == "refusal"


def test_reactive_feedback_remains_exact_in_both_ac_assemblies():
    ir = leggi(AC.replace("Rg vm 0 5 ohm", "C1 vm 0 1/5 farad"))
    solution = solve_phasor(ir)
    assert solution == solve_phasor_tableau(ir)
    assert solution["RL"]["voltage"] == Cyc12.of(-60) + J * Cyc12.of(6)
    assert verify(ir, solution) is None


def test_inverting_integrator_has_exact_natural_frequency_at_zero():
    ir = leggi("V1 vin 0 6 volt\nO1 out 0 0 vm\nR1 vin vm 5 ohm\n"
              "C1 out vm 1/5 farad\nRL out 0 4 ohm\n? voltage RL")
    assert is_natural_frequency(ir, F(0))
    assert not is_natural_frequency(ir, F(1))


def test_voltage_sensing_does_not_hide_an_inconsistent_current_only_cut():
    ir = leggi(DC.replace("V1 vin 0 6 volt", "I1 0 vin 1 ampere"))
    refusal = validate(ir)
    assert isinstance(refusal, Refusal)
    assert (refusal.cause, refusal.subject) == ("topology", "vin")


def test_opamp_constraint_is_verified_from_published_branch_voltages():
    ir = leggi(DC)
    solution = solve_dc(ir)
    corrupted = {cid: branch.copy() for cid, branch in solution.items()}
    corrupted["Rg"]["voltage"] += F(1)
    assert constitutive_residuals(ir, corrupted)["O1"] != 0


def test_parameterless_opamp_requires_zero_dimensionless_marker_and_control_nodes():
    with pytest.raises(ValueError, match="zero"):
        Component.of("O1", "ideal_opamp", ("out", "0"), F(1), "O1",
                     control_nodes=("vin", "vm"))
    with pytest.raises(ValueError, match="nodi di controllo"):
        Component.of("O1", "ideal_opamp", ("out", "0"), F(0), "O1")
