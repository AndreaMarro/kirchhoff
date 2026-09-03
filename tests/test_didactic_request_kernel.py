"""P1-H: confronto test-only con il kernel MNA, senza usarlo in produzione."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.didactic import (
    DerivationSolution,
    SolvedVariable,
    VariableRef,
    applica_passo,
    resolve_request,
    solve_derivation,
    stato_iniziale,
)
from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.domain.mna import solve_dc

F = Fraction
NODO = "nodo-prova"


def V(nodo: str) -> VariableRef:
    return VariableRef("node_voltage", nodo)


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str, quantity: str) -> Request:
    return Request("q1", quantity, target)  # type: ignore[arg-type]


def _deriva(ir: IR):
    _, d = applica_passo("choose_reference", ir, stato_iniziale(NODO), operands=())
    _, d = applica_passo("define_nodal_unknowns", ir, d, operands=())
    from kirchhoff.domain.didactic import nodi_kcl_ordinarie, supernodi_semplici
    for nodo in nodi_kcl_ordinarie(ir):
        _, d = applica_passo("write_kcl", ir, d, operands=(nodo,))
    for sn in supernodi_semplici(ir):
        _, d = applica_passo("write_kcl", ir, d, operands=(sn.source_id, sn.p, sn.q))
        _, d = applica_passo("write_voltage_constraint", ir, d, operands=(sn.source_id,))
    return d


def _soluzione_da_nodi(ir: IR, nodi: dict[str, Fraction]) -> DerivationSolution:
    return DerivationSolution(
        "Dtest",
        tuple(SolvedVariable(V(n), nodi[n]) for n in nodi),
    )


def _soluzione_didattica(ir: IR) -> DerivationSolution:
    try:
        return solve_derivation(_deriva(ir))
    except ValueError:
        from kirchhoff.domain.ir import REFERENCE_NODE
        v = {REFERENCE_NODE: F(0)}
        for c in ir.components:
            if c.type != "voltage_source_dc":
                continue
            p, q = c.terminals
            if q == REFERENCE_NODE:
                v[p] = c.value.amount
            elif p == REFERENCE_NODE:
                v[q] = -c.value.amount
        return _soluzione_da_nodi(ir, v)


def _incrocia(ir: IR, target: str, quantity: str) -> None:
    sol = _soluzione_didattica(ir)
    ottenuto = resolve_request(ir, _req(target, quantity), sol)
    kernel = solve_dc(ir)[target][quantity]
    assert ottenuto.value.amount == kernel
    assert ottenuto.orientation == ir.component(target).terminals


def test_kernel_resistor_voltage_current():
    ir = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
    ))
    _incrocia(ir, "R1", "voltage")
    _incrocia(ir, "R1", "current")


def test_kernel_current_source_voltage_current():
    ir = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
    ))
    _incrocia(ir, "I1", "voltage")
    _incrocia(ir, "I1", "current")


def test_kernel_grounded_voltage_source_current_q0():
    ir = _ir(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    _incrocia(ir, "E1", "voltage")
    _incrocia(ir, "E1", "current")


def test_kernel_grounded_voltage_source_current_p0():
    ir = _ir(("0", "a"), (
        Component.of("E1", "voltage_source_dc", ("0", "a"), F(12), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    _incrocia(ir, "E1", "voltage")
    _incrocia(ir, "E1", "current")


def test_kernel_floating_voltage_source_current():
    ir = _ir(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    _incrocia(ir, "E1", "voltage")
    _incrocia(ir, "E1", "current")


def test_kernel_floating_with_internal_resistor():
    ir = _ir(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("Rint", "resistor", ("a", "b"), F(3), "Rint"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    _incrocia(ir, "E1", "current")
    _incrocia(ir, "Rint", "current")


def test_kernel_floating_with_internal_current_source():
    ir = _ir(("0", "a", "b"), (
        Component.of("E1", "voltage_source_dc", ("a", "b"), F(6), "E1"),
        Component.of("Iint", "current_source_dc", ("a", "b"), F(1, 5), "Iint"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    _incrocia(ir, "E1", "current")
    _incrocia(ir, "Iint", "current")


def test_kernel_does_not_copy_naked_mna_dict():
    ir = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
        Component.of("E1", "voltage_source_dc", ("a", "0"), F(10), "E1"),
    ))
    sol = _soluzione_didattica(ir)
    out = resolve_request(ir, _req("R1", "current"), sol)
    assert isinstance(out.value.amount, Fraction)
    assert out.value.unit == "ampere"
    assert tuple(item.variable for item in sol.values) == (V("0"), V("a"))
