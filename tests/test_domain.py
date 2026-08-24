from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.mna import kcl_residuals, power_balance, solve_dc


def divider() -> IR:
    """E=12V su R1=10 in serie a R2=20. V(R2) deve fare esattamente 8."""
    return IR("1.0.0", "dc_resistive", "generated", ("0", "A", "B"),
              (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(12), "E_1"),
               Component.of("R1", "resistor", ("A", "B"), Fraction(10), "R_1"),
               Component.of("R2", "resistor", ("B", "0"), Fraction(20), "R_2")),
              (Request("q1", "voltage", "R2"),))


def test_partitore_esatto():
    sol = solve_dc(divider())
    assert sol["R2"]["voltage"] == Fraction(8)
    assert sol["R1"]["current"] == Fraction(12, 30)


def test_kcl_e_potenza_esattamente_nulli():
    ir = divider()
    sol = solve_dc(ir)
    assert all(r == 0 for r in kcl_residuals(ir, sol).values())
    assert power_balance(ir, sol) == 0


def test_parallelo():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1"),
             Component.of("R2", "resistor", ("A", "0"), Fraction(40), "R_2")),
            (Request("q1", "current", "R1"),))
    sol = solve_dc(ir)
    assert sol["R1"]["current"] == Fraction(1)
    assert sol["R2"]["current"] == Fraction(1, 4)
    assert sol["E1"]["current"] == Fraction(-5, 4)


def test_resistenza_non_positiva_rifiutata():
    with pytest.raises(ValueError):
        Component.of("R1", "resistor", ("A", "0"), Fraction(0), "R_1")


def test_grandezza_richiesta_su_componente_inesistente():
    with pytest.raises(ValueError):
        IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
           (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(5), "E_1"),),
           (Request("q1", "voltage", "R9"),))
