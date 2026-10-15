"""E/G reali producono fasori controllati esatti, senza lezione AC servita."""

from fractions import Fraction as F

from kirchhoff.domain.exact import Cyc12, J
from kirchhoff.domain.independent_phasor import solve_phasor_tableau
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.domain.verify import constitutive_residuals, verify
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.netlist import leggi


VCVS = ("@ac 2 rad/s\nV1 a 0 6 volt 90deg\nR1 a 0 3 ohm\n"
        "E1 b 0 a 0 2 dimensionless\nR2 b 0 4 ohm\n? voltage R2")
VCCS = ("@ac 2 rad/s\nV1 a 0 6 volt 90deg\nR1 a 0 3 ohm\n"
        "G1 0 b a 0 1/2 siemens\nC1 b 0 1/2 farad\n? voltage C1")


def test_ac_vcvs_scales_a_quadrature_control_without_rounded_gain():
    ir = leggi(VCVS)
    mna = solve_phasor(ir)
    assert mna == solve_phasor_tableau(ir)
    assert mna["R2"]["voltage"] == J * Cyc12.of(12)
    assert mna["E1"]["current"] == -J * Cyc12.of(3)
    assert constitutive_residuals(ir, mna)["E1"] == 0
    assert verify(ir, mna) is None
    assert create_lesson(VCVS)["outcome"] == "refusal"


def test_ac_vccs_drives_reactive_load_with_exact_phase():
    ir = leggi(VCCS)
    mna = solve_phasor(ir)
    assert mna == solve_phasor_tableau(ir)
    assert mna["G1"]["current"] == J * Cyc12.of(3)
    assert mna["C1"]["voltage"] == Cyc12.of(3)
    assert mna["C1"]["current"] == J * Cyc12.of(3)
    assert constitutive_residuals(ir, mna)["G1"] == 0
    assert verify(ir, mna) is None
    assert create_lesson(VCCS)["outcome"] == "refusal"


def test_reversing_vccs_control_reverses_observed_phasor():
    baseline = solve_phasor(leggi(VCCS))["C1"]["voltage"]
    ir = leggi(VCCS.replace("G1 0 b a 0", "G1 0 b 0 a"))
    mna = solve_phasor(ir)
    assert mna == solve_phasor_tableau(ir)
    assert mna["C1"]["voltage"] == -baseline


def test_ac_gain_is_a_real_exact_parameter_with_physical_units():
    ir = leggi(VCVS.replace("2 dimensionless", "3/2 dimensionless"))
    assert ir.component("E1").value.amount == F(3, 2)
    assert solve_phasor(ir) == solve_phasor_tableau(ir)
