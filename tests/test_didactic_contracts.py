"""Contratti del piccolo IR didattico: derivation + passi analitici."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    AnalyticalStep,
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    VariableRef,
    applica_passo,
    il_grafo_resta_fermo,
    nodo_della_prima_kcl,
    stato_iniziale,
)
from kirchhoff.domain.didactic.analytical import (
    _generatori_verso_riferimento,
    _kcl_al_nodo,
    _prossimo_id,
)
from kirchhoff.domain.didactic.derivation import nome_tensione, tensione_nodo
from kirchhoff.domain.ir import IR, REFERENCE_NODE, Component
from kirchhoff.domain.proof import ProofEdge, ProofGraph, ProofNode
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PONTE
from test_proof import _ir as _proof_ir, _lay, _patch

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps, domain="dc") -> IR:
    return IR("1.0.0", domain, "netlist", tuple(nodes), tuple(comps), ())


def test_nodal_variable_guardie():
    with pytest.raises(ValueError, match="senza nome"):
        NodalVariable("", "a", "unknown")
    with pytest.raises(ValueError, match="senza nodo"):
        NodalVariable("v_a", "", "unknown")
    with pytest.raises(ValueError, match="fuori da"):
        NodalVariable("v_a", "a", "mesh")
    with pytest.raises(ValueError, match="senza source_id"):
        NodalVariable("v_a", "a", "known_from_source")
    with pytest.raises(ValueError, match="source_id su un ruolo"):
        NodalVariable("v_a", "a", "unknown", "V1")
    with pytest.raises(ValueError, match="senza known_value"):
        NodalVariable("v_a", "a", "known_from_source", "V1")
    with pytest.raises(ValueError, match="riferimento senza known_value"):
        NodalVariable("v_0", "0", "reference")
    with pytest.raises(ValueError, match="riferimento con known_value"):
        NodalVariable("v_0", "0", "reference", known_value=F(1))
    with pytest.raises(ValueError, match="source_id su un ruolo"):
        NodalVariable("v_0", "0", "reference", "V1", F(0))
    with pytest.raises(ValueError, match="known_value su un ruolo"):
        NodalVariable("v_a", "a", "unknown", known_value=F(5))
    with pytest.raises(TypeError, match="Fraction"):
        NodalVariable("v_a", "a", "known_from_source", "V1", 5.0)  # type: ignore[arg-type]
    nota = NodalVariable("v_a", "a", "known_from_source", "V1", F(5))
    assert nota.source_id == "V1"
    assert nota.known_value == F(5)
    assert nota.ref() == VariableRef("node_voltage", "a")
    zero = NodalVariable("v_a", "a", "known_from_source", "V1", F(0))
    assert zero.known_value == F(0)
    assert zero.known_value is not None


def test_nodal_term_e_exact_equation_guardie():
    va, vb = tensione_nodo("a"), tensione_nodo("b")
    with pytest.raises(TypeError, match="Fraction"):
        LinearTerm(0.5, va)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="nullo"):
        LinearTerm(F(0), va)
    with pytest.raises(TypeError, match="VariableRef"):
        LinearTerm(F(1, 2), "v_a")  # type: ignore[arg-type]
    t1 = LinearTerm(F(1, 3), va)
    t2 = LinearTerm(F(1, 2), vb)
    with pytest.raises(ValueError, match="fuori da"):
        ExactEquation("kvl", (t1,), F(0), "a")
    with pytest.raises(ValueError, match="senza nodo"):
        ExactEquation("kcl", (t1,), F(0), "")
    with pytest.raises(ValueError, match="senza variabili"):
        ExactEquation("kcl", (), F(0), "a")
    with pytest.raises(TypeError, match="rhs"):
        ExactEquation("kcl", (t1,), 0.0, "a")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="LinearTerm"):
        ExactEquation("kcl", ("x",), F(0), "a")  # type: ignore[arg-type]
    eq = ExactEquation("kcl", (t2, t1), F(0), "a")
    assert eq.terms == (t1, t2)
    assert eq.focus == "a"


def test_derivation_state_guardie_e_lookup():
    with pytest.raises(ValueError, match="senza identificatore"):
        DerivationState("", NODO)
    with pytest.raises(ValueError, match="ProofNode"):
        DerivationState("D0", "")
    with pytest.raises(TypeError, match="invece di ExactEquation"):
        DerivationState("D0", NODO, equations=("x",))  # type: ignore[arg-type]
    t = LinearTerm(F(1, 2), tensione_nodo("a"))
    eq = ExactEquation("kcl", (t,), F(0), "a")
    with pytest.raises(ValueError, match="duplicate"):
        DerivationState("D0", NODO, equations=(eq, eq))
    with pytest.raises(ValueError, match="variabili ripetute"):
        DerivationState("D0", NODO, variables=(
            NodalVariable("v_a", "a", "unknown"),
            NodalVariable("v_a", "b", "unknown"),
        ))
    with pytest.raises(ValueError, match="stesso nodo"):
        DerivationState("D0", NODO, variables=(
            NodalVariable("v_a", "a", "unknown"),
            NodalVariable("v_a2", "a", "unknown"),
        ))
    with pytest.raises(ValueError, match="reference_node vuoto"):
        DerivationState("D0", NODO, reference_node="")
    s = DerivationState(
        "D1", NODO, reference_node="0",
        variables=(NodalVariable("v_0", "0", "reference", known_value=F(0)),),
        assumptions=("verso_dai_terminali",),
    )
    assert s.variabile_del_nodo("0").role == "reference"
    with pytest.raises(KeyError):
        s.variabile_del_nodo("z")
    assert nome_tensione(REFERENCE_NODE) == "v_0"
    assert nome_tensione("a") == "v_a"


def test_stato_iniziale_e_prossimo_id():
    d0 = stato_iniziale(NODO)
    assert d0.identifier == "D0"
    assert d0.equations == ()
    assert _prossimo_id(d0) == "D1"
    with pytest.raises(ValueError, match="non sequenziale"):
        _prossimo_id(replace(d0, identifier="Dx"))


def test_generatori_verso_riferimento_polarita_e_flottante():
    verso_p = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("0", "a"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    verso_q = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert _generatori_verso_riferimento(verso_p) == {"a": ("V1", -F(5))}
    assert _generatori_verso_riferimento(verso_q) == {"a": ("V1", F(5))}
    assert _generatori_verso_riferimento(flottante) == {}
    assert _generatori_verso_riferimento(leggi(PONTE)) == {"c": ("V1", F(12))}


def test_nodo_della_prima_kcl_deterministico():
    ir = leggi(PONTE)
    assert nodo_della_prima_kcl(ir) == "a"
    solo_massa = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    assert nodo_della_prima_kcl(solo_massa) is None
    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert nodo_della_prima_kcl(flottante) is None
    senza_r = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("I1", "current_source_dc", ("b", "0"), F(1), "I1"),
    ))
    assert nodo_della_prima_kcl(senza_r) is None


def test_kcl_al_nodo_termini_esatti_e_canoni():
    ir = leggi(PONTE)
    eq = _kcl_al_nodo(ir, "a")
    assert eq.kind == "kcl" and eq.focus == "a" and eq.rhs == F(0)
    nodi = {t.variable.node for t in eq.terms}
    assert nodi == {"a", "c", "0", "b"}
    coeff = {t.variable.node: t.coefficient for t in eq.terms}
    assert coeff["a"] == F(1, 10) + F(1, 30) + F(1, 50)
    assert coeff["c"] == -F(1, 10)
    assert coeff["0"] == -F(1, 30)
    assert coeff["b"] == -F(1, 50)
    assert all(isinstance(t.coefficient, Fraction) for t in eq.terms)
    assert all(t.variable.kind == "node_voltage" for t in eq.terms)
    assert eq.terms == tuple(sorted(eq.terms, key=lambda t: t.variable))
    verso = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(2), "R1"),
        Component.of("R2", "resistor", ("0", "a"), F(4), "R2"),
    ))
    nodi_presenti = {t.variable.node for t in _kcl_al_nodo(verso, "a").terms}
    assert nodi_presenti == {"0", "a", "b"}


def test_passi_analitici_precondizioni_e_successo():
    ir = leggi(PONTE)
    d0 = stato_iniziale(NODO)
    with pytest.raises(ValueError, match="prima del riferimento"):
        applica_passo("define_nodal_unknowns", ir, d0, operands=())
    with pytest.raises(ValueError, match="senza incognite"):
        applica_passo("write_kcl", ir, d0, operands=("a",))
    p1, d1 = applica_passo("choose_reference", ir, d0, operands=())
    assert p1.kind == "choose_reference"
    assert d1.reference_node == REFERENCE_NODE
    with pytest.raises(ValueError, match="già"):
        applica_passo("choose_reference", ir, d1, operands=())
    p2, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    assert p2.kind == "define_nodal_unknowns"
    ruoli = {v.node: v.role for v in d2.variables}
    assert ruoli["0"] == "reference"
    assert ruoli["c"] == "known_from_source"
    assert ruoli["a"] == ruoli["b"] == "unknown"
    with pytest.raises(ValueError, match="già definite"):
        applica_passo("define_nodal_unknowns", ir, d2, operands=())
    p3, d3 = applica_passo("write_kcl", ir, d2, operands=("a",))
    assert p3.kind == "write_kcl"
    assert d3.equations == p3.equations
    with pytest.raises(ValueError, match="fuori da"):
        applica_passo("mesh_analysis", ir, d2, operands=())


def test_define_senza_incognite_e_write_kcl_senza_fuoco():
    massa = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    _, d1 = applica_passo("choose_reference", massa, stato_iniziale(NODO), operands=())
    with pytest.raises(ValueError, match="nessuna tensione nodale incognita"):
        applica_passo("define_nodal_unknowns", massa, d1, operands=())

    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    _, f1 = applica_passo("choose_reference", flottante, stato_iniziale(NODO), operands=())
    _, f2 = applica_passo("define_nodal_unknowns", flottante, f1, operands=())
    with pytest.raises(TypeError):
        applica_passo("write_kcl", flottante, f2)
    with pytest.raises(ValueError, match="KCL ordinaria incompleta"):
        applica_passo("write_kcl", flottante, f2, operands=("a",))
    passo_v, dopo_v = applica_passo(
        "write_voltage_constraint", flottante, f2, operands=("V1",),
    )
    assert passo_v.kind == "write_voltage_constraint"
    assert dopo_v.equations[0].kind == "voltage_constraint"


def test_write_kcl_nodo_senza_variabile():
    ir = leggi(PONTE)
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO), operands=())
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    amputato = replace(
        d2,
        variables=tuple(v for v in d2.variables if v.node != "a"),
    )
    assert nodo_della_prima_kcl(ir) == "a"
    with pytest.raises(ValueError, match="non ha una variabile"):
        applica_passo("write_kcl", ir, amputato, operands=("a",))


def test_analytical_step_guardie_e_grafo_fermo():
    with pytest.raises(ValueError, match="fuori da"):
        AnalyticalStep("thevenin", NODO, "D0", "D1", (), (), "e")
    with pytest.raises(ValueError, match="senza ProofNode"):
        AnalyticalStep("write_kcl", "", "D0", "D1", (), (), "e")
    with pytest.raises(ValueError, match="coincidono"):
        AnalyticalStep("write_kcl", NODO, "D0", "D0", (), (), "e")
    with pytest.raises(ValueError, match="evidence vuota"):
        AnalyticalStep("write_kcl", NODO, "D0", "D1", (), (), "")
    g1 = ProofGraph().con_stato_iniziale(ProofNode(_proof_ir(0), _lay(0)))
    g2 = ProofGraph().con_stato_iniziale(ProofNode(_proof_ir(0), _lay(0)))
    assert il_grafo_resta_fermo(g1, g2)
    g3 = g1.con_passo(
        ProofNode(_proof_ir(1), _lay(1)),
        ProofEdge(_proof_ir(0), _proof_ir(1), "serie", _patch("p1")),
    )
    assert not il_grafo_resta_fermo(g1, g3)
