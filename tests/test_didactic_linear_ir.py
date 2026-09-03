"""P1-A: IR lineare generale della derivazione."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    VariableRef,
)
from kirchhoff.domain.didactic.analytical import _kcl_al_nodo
from kirchhoff.domain.didactic.derivation import tensione_nodo
from kirchhoff.domain.ir import Component, IR, REFERENCE_NODE


F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def test_variable_ref_guardie_uguaglianza_ordine():
    va = VariableRef("node_voltage", "a")
    altra = VariableRef("node_voltage", "a")
    vb = VariableRef("node_voltage", "b")
    v0 = VariableRef("node_voltage", REFERENCE_NODE)
    assert va == altra
    assert va != vb
    assert va.node == "a" and va.kind == "node_voltage"
    assert va != "v_a" and va != "V_a"
    assert sorted((vb, v0, va)) == [v0, va, vb]
    with pytest.raises(ValueError, match="senza nodo"):
        VariableRef("node_voltage", "")
    with pytest.raises(ValueError, match="fuori da"):
        VariableRef("mesh_current", "a")
    assert tensione_nodo("a") == va


def test_linear_term_guardie_segno_e_ordine():
    va, vb = tensione_nodo("a"), tensione_nodo("b")
    pos = LinearTerm(F(2, 3), va)
    neg = LinearTerm(F(-1, 4), vb)
    assert pos.coefficient > 0
    assert neg.coefficient < 0
    with pytest.raises(TypeError, match="Fraction"):
        LinearTerm(2, va)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Fraction"):
        LinearTerm(0.5, va)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="nullo"):
        LinearTerm(F(0), va)
    with pytest.raises(TypeError, match="VariableRef"):
        LinearTerm(F(1), "a")  # type: ignore[arg-type]
    t1 = LinearTerm(F(1), va)
    t2 = LinearTerm(F(1), vb)
    assert sorted((t2, t1), key=lambda t: t.variable) == [t1, t2]


def test_exact_equation_kind_rhs_e_canonicalizzazione():
    va, vb, vc = tensione_nodo("a"), tensione_nodo("b"), tensione_nodo("c")
    eq = ExactEquation(
        "kcl",
        (LinearTerm(F(3), vb), LinearTerm(F(2), va)),
        F(5),
        "a",
    )
    stessa = ExactEquation(
        "voltage_constraint",
        (LinearTerm(F(2), va), LinearTerm(F(3), vb)),
        F(5),
    )
    assert eq.kind == "kcl"
    assert stessa.kind == "voltage_constraint"
    assert eq.terms == (
        LinearTerm(F(2), va),
        LinearTerm(F(3), vb),
    )
    assert eq.terms == stessa.terms
    assert eq != stessa
    aggregata = ExactEquation(
        "kcl",
        (LinearTerm(F(1), va), LinearTerm(F(2), va), LinearTerm(F(3), vb)),
        F(5),
        "n",
    )
    assert aggregata.terms == (LinearTerm(F(3), va), LinearTerm(F(3), vb))
    with pytest.raises(ValueError, match="fuori da"):
        ExactEquation("millman", (LinearTerm(F(1), va),), F(0), "a")
    with pytest.raises(ValueError, match="senza variabili"):
        ExactEquation(
            "kcl",
            (LinearTerm(F(1), va), LinearTerm(F(-1), va)),
            F(0),
            "a",
        )
    with pytest.raises(ValueError, match="senza variabili"):
        ExactEquation("voltage_constraint", (), F(5))


def test_permutation_invariance_e_non_equivalenza_per_scala():
    va, vb = tensione_nodo("a"), tensione_nodo("b")
    a = ExactEquation(
        "kcl",
        (LinearTerm(F(2), va), LinearTerm(F(3), vb)),
        F(5),
        "x",
    )
    b = ExactEquation(
        "kcl",
        (LinearTerm(F(3), vb), LinearTerm(F(2), va)),
        F(5),
        "x",
    )
    assert a == b
    assert hash(a) == hash(b)
    scala = ExactEquation(
        "kcl",
        (LinearTerm(F(4), va), LinearTerm(F(6), vb)),
        F(10),
        "x",
    )
    assert a != scala


def test_derivation_state_accetta_ir_nuovo_e_rifiuta_duplicati_canonici():
    va, vb = tensione_nodo("a"), tensione_nodo("b")
    eq = ExactEquation(
        "kcl",
        (LinearTerm(F(2), va), LinearTerm(F(3), vb)),
        F(5),
        "a",
    )
    permutata = ExactEquation(
        "kcl",
        (LinearTerm(F(3), vb), LinearTerm(F(2), va)),
        F(5),
        "a",
    )
    assert eq == permutata
    stato = DerivationState(
        "D1", NODO, reference_node="0",
        variables=(NodalVariable("v_0", "0", "reference", known_value=F(0)),),
        equations=(eq,),
    )
    assert stato.equations == (eq,)
    with pytest.raises(ValueError, match="duplicate"):
        DerivationState(
            "D1", NODO,
            equations=(eq, permutata),
        )
    vincolo = ExactEquation(
        "voltage_constraint",
        (LinearTerm(F(1), va), LinearTerm(F(-1), vb)),
        F(5),
    )
    with pytest.raises(ValueError, match="duplicate"):
        DerivationState("D1", NODO, equations=(vincolo, vincolo))


def test_kcl_migrazione_entrambi_orientamenti_del_resistore():
    verso_ab = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(5), "R1"),
    ))
    verso_ba = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("b", "a"), F(5), "R1"),
    ))
    attesa = ExactEquation(
        "kcl",
        (
            LinearTerm(F(1, 5), tensione_nodo("a")),
            LinearTerm(F(-1, 5), tensione_nodo("b")),
        ),
        F(0),
        "a",
    )
    assert _kcl_al_nodo(verso_ab, "a") == attesa
    assert _kcl_al_nodo(verso_ba, "a") == attesa
    verso_massa = _ir(("0", "a"), (
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
    ))
    kcl_massa = _kcl_al_nodo(verso_massa, "a")
    coeff = {t.variable.node: t.coefficient for t in kcl_massa.terms}
    assert coeff[REFERENCE_NODE] == F(-1, 2)
    assert coeff["a"] == F(1, 2)
    assert kcl_massa.rhs == F(0)


def test_voltage_constraint_rappresentabile_senza_stringhe_autoritative():
    va, vb = tensione_nodo("a"), tensione_nodo("b")
    diretta = ExactEquation(
        "voltage_constraint",
        (LinearTerm(F(1), va), LinearTerm(F(-1), vb)),
        F(5),
    )
    opposta = ExactEquation(
        "voltage_constraint",
        (LinearTerm(F(1), vb), LinearTerm(F(-1), va)),
        F(-5),
    )
    assert diretta.rhs == F(5)
    assert opposta.rhs == F(-5)
    assert {t.variable for t in diretta.terms} == {va, vb}
    assert diretta != "Va - Vb = 5"
    assert diretta.terms[0].variable != "V_a"
    assert diretta.kind == "voltage_constraint"
    assert diretta.focus == ""
