"""Contratti del piccolo IR didattico: derivation + passi analitici."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    AnalyticalStep,
    DerivationState,
    ExactEquation,
    NodalTerm,
    NodalVariable,
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
from kirchhoff.domain.didactic.derivation import nome_tensione
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
    assert NodalVariable("v_a", "a", "known_from_source", "V1").source_id == "V1"


def test_nodal_term_e_exact_equation_guardie():
    with pytest.raises(TypeError, match="Fraction"):
        NodalTerm("R1", 0.5, "a", "0")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non positiva"):
        NodalTerm("R1", F(0), "a", "0")
    with pytest.raises(ValueError, match="non positiva"):
        NodalTerm("R1", F(-1, 2), "a", "0")
    with pytest.raises(ValueError, match="stesso nodo"):
        NodalTerm("R1", F(1, 2), "a", "a")
    t1 = NodalTerm("R2", F(1, 3), "a", "0")
    t2 = NodalTerm("R1", F(1, 2), "a", "b")
    with pytest.raises(ValueError, match="solo kind"):
        ExactEquation("kvl", "a", (t1,))
    with pytest.raises(ValueError, match="senza nodo"):
        ExactEquation("kcl", "", (t1,))
    with pytest.raises(ValueError, match="senza termini"):
        ExactEquation("kcl", "a", ())
    eq = ExactEquation("kcl", "a", (t1, t2))
    assert eq.terms == tuple(sorted((t1, t2)))


def test_derivation_state_guardie_e_lookup():
    with pytest.raises(ValueError, match="senza identificatore"):
        DerivationState("", NODO)
    with pytest.raises(ValueError, match="ProofNode"):
        DerivationState("D0", "")
    with pytest.raises(TypeError, match="invece di ExactEquation"):
        DerivationState("D0", NODO, equations=("x",))  # type: ignore[arg-type]
    t = NodalTerm("R1", F(1, 2), "a", "0")
    eq = ExactEquation("kcl", "a", (t,))
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
        variables=(NodalVariable("v_0", "0", "reference"),),
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
    assert _generatori_verso_riferimento(verso_p) == {"a": "V1"}
    assert _generatori_verso_riferimento(verso_q) == {"a": "V1"}
    assert _generatori_verso_riferimento(flottante) == {}
    assert _generatori_verso_riferimento(leggi(PONTE)) == {"c": "V1"}


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
    assert eq.kind == "kcl" and eq.node == "a"
    assert eq.terms == tuple(sorted(eq.terms))
    assert {t.component for t in eq.terms} == {"R1", "R3", "Rg"}
    assert all(isinstance(t.conductance, Fraction) for t in eq.terms)
    assert all(t.plus_node == "a" for t in eq.terms)
    verso = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(2), "R1"),
        Component.of("R2", "resistor", ("0", "a"), F(4), "R2"),
    ))
    termini = _kcl_al_nodo(verso, "a").terms
    nodi_lontani = {t.minus_node for t in termini}
    assert nodi_lontani == {"0", "b"}


def test_passi_analitici_precondizioni_e_successo():
    ir = leggi(PONTE)
    d0 = stato_iniziale(NODO)
    with pytest.raises(ValueError, match="prima del riferimento"):
        applica_passo("define_nodal_unknowns", ir, d0)
    with pytest.raises(ValueError, match="senza incognite"):
        applica_passo("write_kcl", ir, d0)
    p1, d1 = applica_passo("choose_reference", ir, d0)
    assert p1.kind == "choose_reference"
    assert d1.reference_node == REFERENCE_NODE
    with pytest.raises(ValueError, match="già"):
        applica_passo("choose_reference", ir, d1)
    p2, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    assert p2.kind == "define_nodal_unknowns"
    ruoli = {v.node: v.role for v in d2.variables}
    assert ruoli["0"] == "reference"
    assert ruoli["c"] == "known_from_source"
    assert ruoli["a"] == ruoli["b"] == "unknown"
    with pytest.raises(ValueError, match="già definite"):
        applica_passo("define_nodal_unknowns", ir, d2)
    p3, d3 = applica_passo("write_kcl", ir, d2)
    assert p3.kind == "write_kcl"
    assert d3.equations == p3.equations
    with pytest.raises(ValueError, match="fuori da"):
        applica_passo("mesh_analysis", ir, d2)


def test_define_senza_incognite_e_write_kcl_senza_fuoco():
    massa = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    _, d1 = applica_passo("choose_reference", massa, stato_iniziale(NODO))
    with pytest.raises(ValueError, match="nessuna tensione nodale incognita"):
        applica_passo("define_nodal_unknowns", massa, d1)

    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    _, f1 = applica_passo("choose_reference", flottante, stato_iniziale(NODO))
    _, f2 = applica_passo("define_nodal_unknowns", flottante, f1)
    with pytest.raises(ValueError, match="senza supernodo"):
        applica_passo("write_kcl", flottante, f2)


def test_write_kcl_nodo_senza_variabile():
    ir = leggi(PONTE)
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO))
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    amputato = replace(
        d2,
        variables=tuple(v for v in d2.variables if v.node != "a"),
    )
    assert nodo_della_prima_kcl(ir) == "a"
    with pytest.raises(ValueError, match="non ha una variabile"):
        applica_passo("write_kcl", ir, amputato)


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
