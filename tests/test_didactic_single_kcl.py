"""P1-B: una KCL ordinaria, esplicita sul nodo, completa e fail-closed."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    ExactEquation,
    LinearTerm,
    applica_passo,
    nodo_della_prima_kcl,
    nodi_kcl_ordinarie,
    pianifica,
    scrivi_kcl_al_nodo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.analytical import _kcl_al_nodo
from kirchhoff.domain.didactic.derivation import tensione_nodo
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR, Request
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PONTE

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _fino_alle_incognite(ir: IR):
    d0 = stato_iniziale(NODO)
    _, d1 = applica_passo("choose_reference", ir, d0, operands=())
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    return d2


def _due_nodi_ordinari():
    """Rete con due nodi ordinari a,b: V1 fissa c, R su a e b."""
    return _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "c"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("b", "0"), F(5), "R3"),
        Component.of("R4", "resistor", ("a", "0"), F(4), "R4"),
    ))


def test_kcl_esplicita_scrive_il_nodo_chiesto_non_il_primo():
    ir = _due_nodi_ordinari()
    assert nodo_della_prima_kcl(ir) == "a"
    assert nodi_kcl_ordinarie(ir) == ("a", "b")
    prima = _fino_alle_incognite(ir)
    passo, dopo = scrivi_kcl_al_nodo(ir, prima, "b")
    assert passo.kind == "write_kcl"
    assert passo.focused_entities == ("b",)
    assert passo.equations[0].focus == "b"
    assert dopo.equations[0].focus == "b"
    assert passo.equations[0].focus != "a"


def test_planner_e_formulator_sono_consistenti_sul_nodo():
    ir = leggi(PONTE)
    piano = pianifica(ir, Request("q1", "current", "R4"))
    kcl = next(a for a in piano.actions if a.kind == "write_kcl")
    assert kcl.operands == ("a",)
    prima = _fino_alle_incognite(ir)
    passo, _ = scrivi_kcl_al_nodo(ir, prima, kcl.operands[0])
    assert passo.focused_entities == ("a",)
    assert passo.equations[0].focus == "a"
    assert passo.equations[0] == _kcl_al_nodo(ir, "a")


def test_nodo_assente_dal_circuit_ir():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match="assente dal CircuitIR"):
        scrivi_kcl_al_nodo(ir, prima, "z")
    with pytest.raises(ValueError, match="assente dal CircuitIR"):
        _kcl_al_nodo(ir, "z")


def test_kcl_al_riferimento_rifiutata():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match="riferimento"):
        scrivi_kcl_al_nodo(ir, prima, REFERENCE_NODE)
    with pytest.raises(ValueError, match="riferimento"):
        _kcl_al_nodo(ir, REFERENCE_NODE)


def test_nodo_senza_variabile_dichiarata():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    amputato = replace(
        prima,
        variables=tuple(v for v in prima.variables if v.node != "b"),
    )
    with pytest.raises(ValueError, match="non ha una variabile"):
        scrivi_kcl_al_nodo(ir, amputato, "b")


def test_vicino_non_dichiarato_nello_stato():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    senza_c = replace(
        prima,
        variables=tuple(v for v in prima.variables if v.node != "c"),
    )
    with pytest.raises(ValueError, match="non dichiarato"):
        scrivi_kcl_al_nodo(ir, senza_c, "a")


def test_kcl_resistiva_ordinaria_coefficienti_esatti():
    ir = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(5), "R2"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(3), "V1"),
    ))
    prima = _fino_alle_incognite(ir)
    passo, dopo = scrivi_kcl_al_nodo(ir, prima, "a")
    attesa = ExactEquation(
        "kcl",
        (
            LinearTerm(F(1, 10) + F(1, 5), tensione_nodo("a")),
            LinearTerm(-F(1, 10), tensione_nodo("b")),
            LinearTerm(-F(1, 5), tensione_nodo(REFERENCE_NODE)),
        ),
        F(0),
        "a",
    )
    assert passo.equations[0] == attesa
    assert dopo.equations == (attesa,)
    coeff = {t.variable.node: t.coefficient for t in attesa.terms}
    assert coeff["a"] == F(3, 10)
    assert coeff["b"] == -F(1, 10)
    assert coeff["0"] == -F(1, 5)


def test_inversione_terminali_del_resistore_non_cambia_la_kcl():
    verso_ab = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(8), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(2), "R2"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
    ))
    verso_ba = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("b", "a"), F(8), "R1"),
        Component.of("R2", "resistor", ("0", "a"), F(2), "R2"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
    ))
    assert _kcl_al_nodo(verso_ab, "a") == _kcl_al_nodo(verso_ba, "a")
    d_ab = _fino_alle_incognite(verso_ab)
    d_ba = _fino_alle_incognite(verso_ba)
    p_ab, _ = scrivi_kcl_al_nodo(verso_ab, d_ab, "a")
    p_ba, _ = scrivi_kcl_al_nodo(verso_ba, d_ba, "a")
    assert p_ab.equations[0] == p_ba.equations[0]


def test_resistori_multipli_sulla_stessa_coppia_si_aggregato():
    ir = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(4), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(4), "R2"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
    ))
    eq = _kcl_al_nodo(ir, "a")
    assert eq.terms == (
        LinearTerm(F(1, 2), tensione_nodo("a")),
        LinearTerm(-F(1, 2), tensione_nodo("b")),
    )
    nodi = [t.variable.node for t in eq.terms]
    assert nodi == sorted(nodi)
    assert len(eq.terms) == 2


def test_vicino_a_tensione_nota_resta_variable_ref():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(7), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(3), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(6), "R2"),
    ))
    prima = _fino_alle_incognite(ir)
    ruoli = {v.node: v.role for v in prima.variables}
    assert ruoli["b"] == "known_from_source"
    assert ruoli["0"] == "reference"
    assert ruoli["a"] == "unknown"
    passo, _ = scrivi_kcl_al_nodo(ir, prima, "a")
    nodi = {t.variable.node for t in passo.equations[0].terms}
    assert nodi == {"a", "b", "0"}
    assert prima.variabile_del_nodo("b").source_id == "V1"


def test_riferimento_compare_come_variable_ref():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
    ))
    prima = _fino_alle_incognite(ir)
    assert prima.variabile_del_nodo(REFERENCE_NODE).role == "reference"
    eq = scrivi_kcl_al_nodo(ir, prima, "a")[0].equations[0]
    coeff = {t.variable.node: t.coefficient for t in eq.terms}
    assert coeff["a"] == F(1, 2)
    assert coeff["0"] == -F(1, 2)
    assert REFERENCE_NODE in coeff


def test_kcl_duplicata_rifiutata_sullo_stato_evoluto():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    _, dopo = scrivi_kcl_al_nodo(ir, prima, "a")
    with pytest.raises(ValueError, match="duplicate"):
        scrivi_kcl_al_nodo(ir, dopo, "a")


def test_immutabilita_dello_stato_precedente():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    snap_eq = prima.equations
    snap_id = prima.identifier
    passo, dopo = scrivi_kcl_al_nodo(ir, prima, "b")
    assert prima.equations == snap_eq == ()
    assert prima.identifier == snap_id
    assert dopo.equations == (*snap_eq, passo.equations[0])
    assert dopo.identifier != prima.identifier
    assert dopo.variables == prima.variables


def test_determinismo_stessi_ir_stato_nodo():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    p1, s1 = scrivi_kcl_al_nodo(ir, prima, "b")
    p2, s2 = scrivi_kcl_al_nodo(ir, prima, "b")
    assert p1 == p2
    assert s1 == s2
    assert s1.equations[0] == s2.equations[0]


def test_corrente_incidente_entra_nella_kcl_ordinaria():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
    ))
    assert "a" in nodi_kcl_ordinarie(ir)
    eq = _kcl_al_nodo(ir, "a")
    assert eq.rhs == -F(1)
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO), operands=())
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    passo, _ = scrivi_kcl_al_nodo(ir, d2, "a")
    assert passo.equations[0].rhs == -F(1)
    assert passo.evidence == "kcl_leaving_currents_dc"


def test_sorgente_controllata_incidente_rifiutata():
    vcvs = _ir(("0", "a", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
        Component.of(
            "E1", "voltage_controlled_voltage_source", ("a", "0"),
            F(2), "E1", control_nodes=("c", "0"),
        ),
    ))
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(vcvs, "a")
    vccs = _ir(("0", "a", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
        Component.of(
            "G1", "voltage_controlled_current_source", ("a", "0"),
            F(1), "G1", control_nodes=("c", "0"),
        ),
    ))
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(vccs, "a")


def test_generatore_di_tensione_incidente_non_e_kcl_ordinaria():
    ir = leggi(PONTE)
    prima = _fino_alle_incognite(ir)
    assert prima.variabile_del_nodo("c").role == "known_from_source"
    with pytest.raises(ValueError, match="ruolo known_from_source"):
        scrivi_kcl_al_nodo(ir, prima, "c")
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(ir, "c")
    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert nodi_kcl_ordinarie(flottante) == ()
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(flottante, "a")


def test_nodo_isolato_senza_rami():
    ir = _ir(("0", "a", "z"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
    ))
    assert "z" not in nodi_kcl_ordinarie(ir)
    with pytest.raises(ValueError, match="nessun ramo incidente"):
        _kcl_al_nodo(ir, "z")


def test_wrapper_legacy_delega_al_primo_nodo_ordinario():
    ir = _due_nodi_ordinari()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(TypeError):
        applica_passo("write_kcl", ir, prima)
    via_dispatch = applica_passo("write_kcl", ir, prima, operands=("a",))
    via_esplicita = scrivi_kcl_al_nodo(ir, prima, "a")
    assert via_dispatch == via_esplicita
    assert via_dispatch[0].focused_entities == ("a",)
    via_b = applica_passo("write_kcl", ir, prima, operands=("b",))
    assert via_b[0].focused_entities == ("b",)
    assert via_b[0].focused_entities != via_dispatch[0].focused_entities
