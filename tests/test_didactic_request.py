"""P1-H: Request + DerivationSolution → ResolvedQuantity, senza risolverlo di nuovo."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DerivationSolution,
    ResolvedQuantity,
    SolvedVariable,
    VariableRef,
    resolve_request,
)
from kirchhoff.domain.ir import Component, IR, Magnitude, Request

F = Fraction


def V(nodo: str) -> VariableRef:
    return VariableRef("node_voltage", nodo)


def soluzione(derivation_id: str, **nodi: Fraction | int) -> DerivationSolution:
    valori = tuple(
        SolvedVariable(V(nodo), F(valore) if not isinstance(valore, Fraction) else valore)
        for nodo, valore in nodi.items()
    )
    return DerivationSolution(derivation_id, valori)


def circuito(nodes, comps, domain="dc") -> IR:
    return IR("1.0.0", domain, "netlist", tuple(nodes), tuple(comps), ())


def req(target: str, quantity: str = "voltage", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _risolvi(ir: IR, target: str, quantity: str, sol: DerivationSolution):
    return resolve_request(ir, req(target, quantity), sol)


# ---------------------------------------------------------------------------
# R1–R4 resistore
# ---------------------------------------------------------------------------


def _resistore(va, vb, r=F(6)):
    ir = circuito(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), r, "R1"),
        Component.of("G", "voltage_source_dc", ("0", "b"), F(1), "G"),
    ))
    # Il secondo componente esiste solo per avere un IR DC non degenere
    # nella chiusura nodale; la soluzione è imposta a mano.
    sol = soluzione("D1", **{"0": 0, "a": va, "b": vb})
    return ir, sol


def test_r1_resistor_voltage():
    ir, sol = _resistore(5, 2)
    out = _risolvi(ir, "R1", "voltage", sol)
    assert out.value.amount == F(3)
    assert out.value.unit == "volt"
    assert out.orientation == ("a", "b")


def test_r2_resistor_reversed_voltage():
    ir, sol = _resistore(2, 5)
    out = _risolvi(ir, "R1", "voltage", sol)
    assert out.value.amount == F(-3)
    assert out.orientation == ("a", "b")


def test_r3_resistor_current():
    ir, sol = _resistore(5, 2, F(6))
    out = _risolvi(ir, "R1", "current", sol)
    assert out.value.amount == F(1, 2)
    assert out.value.unit == "ampere"


def test_r4_resistor_negative_current():
    ir, sol = _resistore(2, 5, F(6))
    out = _risolvi(ir, "R1", "current", sol)
    assert out.value.amount == F(-1, 2)


def test_mutation_resistor_voltage_not_abs():
    ir, sol = _resistore(2, 5)
    assert _risolvi(ir, "R1", "voltage", sol).value.amount != abs(F(2) - F(5))


def test_mutation_resistor_current_not_reversed_ohm():
    ir, sol = _resistore(5, 2, F(6))
    assert _risolvi(ir, "R1", "current", sol).value.amount != (F(2) - F(5)) / F(6)


# ---------------------------------------------------------------------------
# I1–I3 current source
# ---------------------------------------------------------------------------


def _corrente(amount, va=F(4), vb=F(1)):
    ir = circuito(("0", "a", "b"), (
        Component.of("I1", "current_source_dc", ("a", "b"), amount, "I1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    sol = soluzione("D2", **{"0": 0, "a": va, "b": vb})
    return ir, sol


def test_i1_current_source_current():
    ir, sol = _corrente(F(7, 3))
    out = _risolvi(ir, "I1", "current", sol)
    assert out.value.amount == F(7, 3)
    assert out.orientation == ("a", "b")


def test_i2_negative_current_source_no_abs():
    ir, sol = _corrente(F(-7, 3))
    out = _risolvi(ir, "I1", "current", sol)
    assert out.value.amount == F(-7, 3)
    assert out.value.amount != abs(F(-7, 3))


def test_i3_current_source_voltage_from_solution():
    ir, sol = _corrente(F(1), va=F(9), vb=F(4))
    out = _risolvi(ir, "I1", "voltage", sol)
    assert out.value.amount == F(5)
    assert out.value.unit == "volt"


# ---------------------------------------------------------------------------
# V1–V3 voltage of voltage source
# ---------------------------------------------------------------------------


def test_v1_grounded_voltage_source_voltage():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(5), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    sol = soluzione("D3", **{"0": 0, "a": 5})
    out = _risolvi(ir, "E1", "voltage", sol)
    assert out.value.amount == F(5)
    assert out.orientation == ("a", "0")


def test_v2_reversed_grounded_source_voltage():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("0", "a"), F(5), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    sol = soluzione("D3", **{"0": 0, "a": -5})
    out = _risolvi(ir, "E1", "voltage", sol)
    assert out.value.amount == F(5)
    assert out.orientation == ("0", "a")


def test_v3_inconsistent_voltage_source_solution():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(5), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    sol = soluzione("D3", **{"0": 0, "a": 4})
    with pytest.raises(ValueError, match="tensione derivata"):
        _risolvi(ir, "E1", "voltage", sol)


# ---------------------------------------------------------------------------
# V4–V8 voltage-source current
# ---------------------------------------------------------------------------


def test_v4_grounded_source_current_q_reference():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    sol = soluzione("D4", **{"0": 0, "a": 12})
    # S_a = I_R = 12/4 = 3; I_E = -S_a = -3
    out = _risolvi(ir, "E1", "current", sol)
    assert out.value.amount == F(-3)
    assert out.orientation == ("a", "0")


def test_v5_grounded_source_current_p_reference():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("0", "a"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    sol = soluzione("D5", **{"0": 0, "a": -12})
    # S_a = I_R = (-12-0)/4 = -3; I_E = S_a = -3
    out = _risolvi(ir, "E1", "current", sol)
    assert out.value.amount == F(-3)
    assert out.orientation == ("0", "a")


def test_v6_floating_source_current_agreement():
    ir = circuito(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    sol = soluzione("D6", **{"0": 0, "a": 2, "b": -4})
    out = _risolvi(ir, "E1", "current", sol)
    assert out.value.amount == F(-1, 5)


def test_v7_floating_source_internal_resistor():
    ir = circuito(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("Rint", "resistor", ("a", "b"), F(3), "Rint"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    # Vincolo E: Va-Vb=6. Rete esterna come V6 più Rint.
    # I_R1=(Va)/10, I_R2=(Vb)/20, I_Rint=(Va-Vb)/3=2
    # S_a = I_R1 + I_Rint ; I_E = -S_a
    va, vb = F(2), F(-4)
    sol = soluzione("D7", **{"0": 0, "a": va, "b": vb})
    i_r1 = va / F(10)
    i_rint = (va - vb) / F(3)
    atteso = -(i_r1 + i_rint)
    out = _risolvi(ir, "E1", "current", sol)
    assert out.value.amount == atteso
    assert atteso != -i_r1  # mutation: internal resistor ignored


def test_v8_floating_source_internal_current_source():
    ir = circuito(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("Iint", "current_source_dc", ("a", "b"), F(1, 5), "Iint"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    va, vb = F(2), F(-4)
    sol = soluzione("D8", **{"0": 0, "a": va, "b": vb})
    i_r1 = va / F(10)
    i_int = F(1, 5)
    atteso = -(i_r1 + i_int)
    out = _risolvi(ir, "E1", "current", sol)
    assert out.value.amount == atteso
    assert atteso != -i_r1  # mutation: internal current source ignored


def test_v9_terminal_kcl_disagreement():
    ir = circuito(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(5), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    sol = soluzione("D9", **{"0": 0, "a": 5, "b": 0})
    with pytest.raises(ValueError, match="terminal KCL agreement"):
        _risolvi(ir, "E1", "current", sol)


def test_mutation_grounded_q0_uses_minus_sp():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    sol = soluzione("D4", **{"0": 0, "a": 12})
    assert _risolvi(ir, "E1", "current", sol).value.amount != F(3)


def test_mutation_grounded_p0_uses_plus_sq():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("0", "a"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    sol = soluzione("D5", **{"0": 0, "a": -12})
    assert _risolvi(ir, "E1", "current", sol).value.amount != F(3)


# ---------------------------------------------------------------------------
# S1–S6 guards
# ---------------------------------------------------------------------------


def test_s1_solution_missing_node():
    ir = circuito(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(6), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(3), "R2"),
    ))
    sol = soluzione("Ds", **{"0": 0, "a": 1})
    with pytest.raises(ValueError, match="manca"):
        _risolvi(ir, "R1", "voltage", sol)


def test_s2_solution_extra_node():
    ir = circuito(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(6), "R1"),
    ))
    sol = soluzione("Ds", **{"0": 0, "a": 1, "z": 2})
    with pytest.raises(ValueError, match="extra"):
        _risolvi(ir, "R1", "voltage", sol)


def test_s3_target_missing():
    ir = circuito(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(6), "R1"),
    ))
    sol = soluzione("Ds", **{"0": 0, "a": 1})
    with pytest.raises(ValueError, match="assente"):
        resolve_request(ir, req("RX", "voltage"), sol)


def test_s4_unsupported_quantity():
    ir = circuito(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(6), "R1"),
    ))
    sol = soluzione("Ds", **{"0": 0, "a": 1})
    with pytest.raises(ValueError, match="non risolvibile"):
        resolve_request(ir, req("R1", "time_constant"), sol)


def test_s5_unsupported_component_type():
    ir = circuito(("0", "a"), (
        Component.of("C1", "capacitor", ("a", "0"), F(1, 1000), "C1"),
    ))
    sol = soluzione("Ds", **{"0": 0, "a": 1})
    with pytest.raises(ValueError, match="non è un tipo risolvibile"):
        _risolvi(ir, "C1", "voltage", sol)


def test_s6_non_dc_domain():
    ir = circuito(
        ("0", "a"),
        (Component.of("R1", "resistor", ("a", "0"), F(6), "R1"),),
        domain="transient",
    )
    sol = soluzione("Ds", **{"0": 0, "a": 1})
    with pytest.raises(ValueError, match="solo in continua"):
        _risolvi(ir, "R1", "voltage", sol)


def test_incident_voltage_source_unsupported():
    ir = circuito(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(5), "E1"),
        Component.of("E2", "voltage_source_dc", ("a", "0"), F(1), "E2"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    sol = soluzione("Dx", **{"0": 0, "a": 1, "b": -4})
    with pytest.raises(ValueError, match="unsupported topology"):
        _risolvi(ir, "E1", "current", sol)


def test_incident_unsupported_branch_type():
    ir = circuito(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(5), "E1"),
        Component.of("C1", "capacitor", ("a", "0"), F(1, 2), "C1"),
    ))
    sol = soluzione("Dx", **{"0": 0, "a": 5})
    with pytest.raises(ValueError, match="unsupported branch type"):
        _risolvi(ir, "E1", "current", sol)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


def test_t1_t8_result_contract():
    ir, sol = _resistore(5, 2)
    out = _risolvi(ir, "R1", "voltage", sol)
    assert out.value.unit == "volt"
    assert out.orientation == ("a", "b")
    assert out.derivation_id == "D1"
    assert out.request_id == "q1"
    assert out.target == "R1"
    assert type(out.value.amount) is Fraction
    cur = _risolvi(ir, "R1", "current", sol)
    assert cur.value.unit == "ampere"
    assert type(cur.value.amount) is Fraction


def test_t7_invalid_quantity_unit_pairing():
    with pytest.raises(ValueError, match="serve volt"):
        ResolvedQuantity("D1", "q1", "R1", "voltage", ("a", "b"), Magnitude(F(1), "ampere"))
    with pytest.raises(ValueError, match="serve ampere"):
        ResolvedQuantity("D1", "q1", "R1", "current", ("a", "b"), Magnitude(F(1), "volt"))


def test_resolved_quantity_guardie():
    mag = Magnitude(F(1), "volt")
    with pytest.raises(ValueError, match="derivation_id"):
        ResolvedQuantity("", "q1", "R1", "voltage", ("a", "b"), mag)
    with pytest.raises(ValueError, match="request_id"):
        ResolvedQuantity("D1", "", "R1", "voltage", ("a", "b"), mag)
    with pytest.raises(ValueError, match="target"):
        ResolvedQuantity("D1", "q1", "", "voltage", ("a", "b"), mag)
    with pytest.raises(ValueError, match="fuori da"):
        ResolvedQuantity("D1", "q1", "R1", "power", ("a", "b"), mag)
    with pytest.raises(ValueError, match="due nodi distinti"):
        ResolvedQuantity("D1", "q1", "R1", "voltage", ("a", "a"), mag)
    with pytest.raises(ValueError, match="due nodi distinti"):
        ResolvedQuantity("D1", "q1", "R1", "voltage", ("a",), mag)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Magnitude"):
        ResolvedQuantity("D1", "q1", "R1", "voltage", ("a", "b"), F(1))  # type: ignore[arg-type]


def test_orientation_is_component_terminal_order():
    ir = circuito(("0", "b", "a"), (
        Component.of("R1", "resistor", ("b", "a"), F(2), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(2), "R2"),
    ))
    sol = soluzione("Do", **{"0": 0, "a": 1, "b": 3})
    out = _risolvi(ir, "R1", "voltage", sol)
    assert out.orientation == ("b", "a")
    assert out.orientation != tuple(sorted(("b", "a")))
    assert out.value.amount == F(2)


def test_immutability():
    ir, sol = _resistore(5, 2)
    request = req("R1", "voltage")
    ir_id, req_id, sol_id = id(ir), id(request), id(sol)
    comps, reqs, vals = ir.components, ir.requests, sol.values
    resolve_request(ir, request, sol)
    assert id(ir) == ir_id and id(request) == req_id and id(sol) == sol_id
    assert ir.components is comps and ir.requests is reqs and sol.values is vals
    assert replace(ir, domain=ir.domain) == ir
