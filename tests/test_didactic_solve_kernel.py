"""P1-G: confronto test-only con il kernel MNA certificato."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.didactic import applica_passo, solve_derivation, stato_iniziale
from kirchhoff.domain.ir import Component

from test_didactic_solve import F, NODO, V, _ir, kcl, nodi_da_kernel, nv, stato


def _deriva(ir):
    _, d = applica_passo("choose_reference", ir, stato_iniziale(NODO), operands=())
    _, d = applica_passo("define_nodal_unknowns", ir, d, operands=())
    from kirchhoff.domain.didactic import nodi_kcl_ordinarie, supernodi_semplici
    for nodo in nodi_kcl_ordinarie(ir):
        _, d = applica_passo("write_kcl", ir, d, operands=(nodo,))
    for sn in supernodi_semplici(ir):
        _, d = applica_passo("write_kcl", ir, d, operands=(sn.source_id, sn.p, sn.q))
        _, d = applica_passo("write_voltage_constraint", ir, d, operands=(sn.source_id,))
    return d


def _incrocia(ir):
    sol = solve_derivation(_deriva(ir))
    for nodo, valore in nodi_da_kernel(ir).items():
        assert sol.value_of(V(nodo)) == valore


def test_kernel_ordinary_nodal_e_corrente():
    _incrocia(_ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
    )))


def test_kernel_supernodo():
    _incrocia(_ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(6), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    )))


def test_kernel_sorgente_invertita():
    _incrocia(_ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "a"), F(6), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    )))


def test_kernel_supernodi_disgiunti():
    _incrocia(_ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(6), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("V2", "voltage_source_dc", ("c", "d"), F(3), "V2"),
        Component.of("R3", "resistor", ("c", "0"), F(2), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(2), "R4"),
    )))


def test_kernel_noto_verso_massa():
    _incrocia(_ir(("0", "a", "k"), (
        Component.of("Vk", "voltage_source_dc", ("k", "0"), F(-5), "Vk"),
        Component.of("R1", "resistor", ("a", "k"), F(5), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(10), "R2"),
    )))


def test_e3_razionali_scomodi():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((F(17, 19), "a"), (F(-23, 31), "b"), rhs=F(7, 13), focus="a"),
            kcl((F(-23, 31), "a"), (F(17, 19), "b"), rhs=F(-7, 13), focus="b"),
        ),
    )
    sol = solve_derivation(s)
    va, vb = sol.value_of(V("a")), sol.value_of(V("b"))
    assert F(17, 19) * va + F(-23, 31) * vb == F(7, 13)
    assert type(va) is Fraction
