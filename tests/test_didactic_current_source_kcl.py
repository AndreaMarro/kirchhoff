"""P1-D: generatori di corrente indipendenti nella KCL ordinaria."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DidacticPlan,
    ExactEquation,
    LinearTerm,
    applica_passo,
    nodi_kcl_ordinarie,
    pianifica,
    scrivi_kcl_al_nodo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.analytical import _kcl_al_nodo
from kirchhoff.domain.didactic.capabilities import (
    DIDACTIC_NODAL_COMPONENT_TYPES,
    nodale_disponibile,
)
from kirchhoff.domain.didactic.kinds import ANALYTICAL_KINDS
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import REFERENCE_NODE, POSITIVE_VALUED, Component, IR, Request
from kirchhoff.domain.mna import solve_dc
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve

from test_percorso_b import CORRENTE

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str, quantity: str = "voltage", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _fino_alle_incognite(ir: IR):
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO), operands=())
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    return d2


def _coeff(eq: ExactEquation) -> dict[str, Fraction]:
    return {t.variable.node: t.coefficient for t in eq.terms}


def _r_a0_i(terminals: tuple[str, str], amount: Fraction, r: Fraction = F(10)):
    return _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), r, "R1"),
        Component.of("I1", "current_source_dc", terminals, amount, "I1"),
    ))


def _due_unknown_con_i(amount: Fraction = F(3)):
    return _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("R3", "resistor", ("a", "b"), F(5), "R3"),
        Component.of("I1", "current_source_dc", ("a", "b"), amount, "I1"),
    ))


def test_source_p_nodo_q_riferimento_rhs_negativo():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(2)), "a")
    assert eq.rhs == -F(2)
    assert _coeff(eq)["a"] == F(1, 10)
    assert _coeff(eq)["0"] == -F(1, 10)


def test_source_p_riferimento_q_nodo_rhs_positivo():
    eq = _kcl_al_nodo(_r_a0_i(("0", "a"), F(2)), "a")
    assert eq.rhs == F(2)


def test_inversione_terminali_inverte_il_rhs():
    diretta = _kcl_al_nodo(_r_a0_i(("a", "0"), F(2)), "a")
    inversa = _kcl_al_nodo(_r_a0_i(("0", "a"), F(2)), "a")
    assert diretta.rhs == -inversa.rhs
    assert diretta.rhs == -F(2)
    assert inversa.rhs == F(2)
    assert diretta.terms == inversa.terms


def test_amount_negativo_senza_normalizzare_i_terminali():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(-2)), "a")
    assert eq.rhs == F(2)
    assert "current_source_dc" not in POSITIVE_VALUED
    negativo = Component.of("I1", "current_source_dc", ("a", "0"), F(-2), "I1")
    assert negativo.terminals == ("a", "0")
    assert negativo.value.amount == F(-2)


def test_sorgente_fra_due_unknown_segni_opposti():
    ir = _due_unknown_con_i(F(3))
    a = _kcl_al_nodo(ir, "a")
    b = _kcl_al_nodo(ir, "b")
    assert a.rhs == -F(3)
    assert b.rhs == F(3)


def test_piu_sorgenti_sommano_in_fraction():
    ir = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(4), "R2"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
        Component.of("I2", "current_source_dc", ("0", "a"), F(5), "I2"),
        Component.of("I3", "current_source_dc", ("a", "b"), F(1), "I3"),
    ))
    assert _kcl_al_nodo(ir, "a").rhs == F(2)
    assert _kcl_al_nodo(ir, "b").rhs == F(1)


def test_sorgente_frazionaria_resta_esatta():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(2, 3)), "a")
    assert eq.rhs == -F(2, 3)
    assert isinstance(eq.rhs, Fraction)
    assert eq.rhs != float(eq.rhs)


def test_cancellazione_rhs_termini_intatti():
    solo_r = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    con_i = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
        Component.of("I2", "current_source_dc", ("0", "a"), F(2), "I2"),
    ))
    senza = _kcl_al_nodo(solo_r, "a")
    con = _kcl_al_nodo(con_i, "a")
    assert con.rhs == F(0)
    assert con.terms == senza.terms


def test_termini_resistivi_invariati_aggiungendo_una_source():
    solo_r = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(5), "R2"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(3), "V1"),
    ))
    con_i = _ir(("0", "a", "b"), (
        *solo_r.components,
        Component.of("I1", "current_source_dc", ("a", "0"), F(7), "I1"),
    ))
    senza = _kcl_al_nodo(solo_r, "a")
    con = _kcl_al_nodo(con_i, "a")
    assert con.terms == senza.terms
    assert senza.rhs == F(0)
    assert con.rhs == -F(7)


def test_source_non_crea_variabile_di_corrente():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(2)), "a")
    assert all(t.variable.kind == "node_voltage" for t in eq.terms)
    assert {t.variable.node for t in eq.terms} == {"a", "0"}
    assert all(isinstance(t, LinearTerm) for t in eq.terms)


def test_source_fra_known_e_unknown():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "b"), F(3), "I1"),
    ))
    d2 = _fino_alle_incognite(ir)
    assert d2.variabile_del_nodo("a").role == "unknown"
    assert d2.variabile_del_nodo("b").role == "known_from_source"
    assert nodi_kcl_ordinarie(ir) == ("a",)
    eq = _kcl_al_nodo(ir, "a")
    assert eq.rhs == -F(3)
    assert "b" in _coeff(eq)


def test_riferimento_resta_nei_termini_resistivi():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(2)), "a")
    assert any(t.variable.node == REFERENCE_NODE for t in eq.terms)
    assert _coeff(eq)[REFERENCE_NODE] == -F(1, 10)


def test_una_equazione_per_unknown_e_replay():
    ir = _due_unknown_con_i(F(3))
    assert nodale_disponibile(ir, "voltage")
    piano = pianifica(ir, _req("R1"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "nodal_analysis"
    kcl = tuple(a.operands[0] for a in piano.actions if a.kind == "write_kcl")
    assert kcl == ("a", "b")
    stato = _fino_alle_incognite(ir)
    assert stato.identifier == "D2"
    passi = []
    for nodo in kcl:
        passo, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
        passi.append(passo)
    assert [p.equations[0].rhs for p in passi] == [-F(3), F(3)]
    assert [p.derivation_before for p in passi] == ["D2", "D3"]
    assert [eq.focus for eq in stato.equations] == ["a", "b"]
    assert all(p.evidence == "kcl_leaving_currents_dc" for p in passi)


def test_corrente_semplice_ora_nodale():
    ir = leggi(CORRENTE)
    assert "current_source_dc" in DIDACTIC_NODAL_COMPONENT_TYPES
    assert nodale_disponibile(ir, "voltage")
    assert nodale_disponibile(ir, "current")
    piano = pianifica(ir, _req("R1"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "nodal_analysis"
    assert nodi_kcl_ordinarie(ir) == ("a",)


def test_nodo_solo_correnti_fail_closed():
    ir = _ir(("0", "a"), (
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
        Component.of("I2", "current_source_dc", ("0", "a"), F(1), "I2"),
    ))
    assert "a" not in nodi_kcl_ordinarie(ir)
    assert not nodale_disponibile(ir, "voltage")
    with pytest.raises(ValueError, match="senza contributo resistivo"):
        _kcl_al_nodo(ir, "a")
    with pytest.raises(ValueError):
        ExactEquation("kcl", (), F(1), "a")


def test_tensione_flottante_semplice_entra_nello_slice():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert nodale_disponibile(ir, "voltage")
    assert nodi_kcl_ordinarie(ir) == ()
    piano = pianifica(ir, _req("R1"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "nodal_analysis"


def test_vcvs_e_vccs_restano_fuori():
    vcvs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "E1", "voltage_controlled_voltage_source", ("C", "0"),
            F(2), "E1", control_nodes=("A", "0"),
        ),
        Component.of("I1", "current_source_dc", ("C", "0"), F(1), "I1"),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    vccs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "G1", "voltage_controlled_current_source", ("C", "0"),
            F(1), "G1", control_nodes=("A", "0"),
        ),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    assert not nodale_disponibile(vcvs, "voltage")
    assert not nodale_disponibile(vccs, "voltage")
    assert isinstance(pianifica(vcvs, _req("R3")), Refusal)
    assert isinstance(pianifica(vccs, _req("R3")), Refusal)
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(vcvs, "C")
    with pytest.raises(ValueError, match="non rappresentabili"):
        _kcl_al_nodo(vccs, "C")


def test_ac_e_transitorio_restano_fuori():
    dc = _r_a0_i(("a", "0"), F(2))
    assert nodale_disponibile(dc, "voltage")
    ac = IR("1.0.0", "ac", "netlist", dc.nodes, dc.components, (), omega=F(1))
    assert not nodale_disponibile(ac, "voltage")
    tr = IR("1.0.0", "transient", "netlist", dc.nodes, dc.components, ())
    assert not nodale_disponibile(tr, "voltage")
    cap = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("C1", "capacitor", ("a", "0"), F(1, 1000), "C1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
    ))
    assert not nodale_disponibile(cap, "voltage")


def test_planner_non_ha_logica_sulla_sorgente():
    import inspect

    assert "current_source" not in inspect.getsource(_azioni_nodali)
    piano = pianifica(_r_a0_i(("a", "0"), F(2)), _req("R1"))
    assert [a.kind for a in piano.actions] == [
        "choose_reference", "define_nodal_unknowns", "write_kcl",
    ]


def test_vocabolario_analitico_invariato():
    assert ANALYTICAL_KINDS == frozenset({
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_voltage_constraint",
    })
    assert "supernode_kcl" not in ANALYTICAL_KINDS


def test_cross_check_segno_con_mna():
    diretta = _r_a0_i(("a", "0"), F(2), F(10))
    eq = _kcl_al_nodo(diretta, "a")
    assert eq.rhs == -F(2)
    assert solve_dc(diretta)["R1"]["voltage"] == F(-20)
    inversa = _r_a0_i(("0", "a"), F(2), F(10))
    assert _kcl_al_nodo(inversa, "a").rhs == F(2)
    assert solve_dc(inversa)["R1"]["voltage"] == F(20)


def test_mutante_stesso_segno_sui_due_nodi_fallirebbe():
    ir = _due_unknown_con_i(F(3))
    assert _kcl_al_nodo(ir, "a").rhs != _kcl_al_nodo(ir, "b").rhs


def test_amount_non_viene_reso_assoluto():
    eq = _kcl_al_nodo(_r_a0_i(("a", "0"), F(-2)), "a")
    assert eq.rhs != -abs(F(-2))
    assert eq.rhs == -F(-2)


def test_kernel_risolve_ancora_la_rete_r_piu_i():
    ir = leggi(CORRENTE)
    assert isinstance(resolve(IR(
        "1.0.0", "dc", "netlist", ir.nodes, ir.components, (_req("R1"),),
    )), Solved)
