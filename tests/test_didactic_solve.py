"""P1-G: soluzione esatta chiusa su DerivationState, senza rileggere il circuito."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DerivationSolution,
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    SolvedVariable,
    VariableRef,
    build_linear_system,
    solve_derivation,
)
from kirchhoff.domain.exact import SingularSystemError
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR
from kirchhoff.domain.mna import solve_dc

F = Fraction
NODO = "nodo-prova"


def V(nodo: str) -> VariableRef:
    return VariableRef("node_voltage", nodo)


def term(coeff, nodo: str) -> LinearTerm:
    return LinearTerm(F(coeff) if not isinstance(coeff, Fraction) else coeff, V(nodo))


def kcl(*parti, rhs=0, focus="a") -> ExactEquation:
    termini = tuple(term(c, n) for c, n in parti)
    return ExactEquation("kcl", termini, F(rhs) if not isinstance(rhs, Fraction) else rhs, focus)


def vincolo(*parti, rhs, focus="V1") -> ExactEquation:
    termini = tuple(term(c, n) for c, n in parti)
    return ExactEquation(
        "voltage_constraint",
        termini,
        F(rhs) if not isinstance(rhs, Fraction) else rhs,
        focus,
    )


def nv(nodo: str, role: str, value=None, source=None) -> NodalVariable:
    if role == "reference":
        return NodalVariable(f"v_{nodo}", nodo, "reference", known_value=F(0))
    if role == "known_from_source":
        return NodalVariable(
            f"v_{nodo}", nodo, "known_from_source", source or "Vs",
            F(value) if not isinstance(value, Fraction) else value,
        )
    return NodalVariable(f"v_{nodo}", nodo, "unknown")


def stato(*, variables, equations, identifier="D4", reference="0") -> DerivationState:
    return DerivationState(
        identifier, NODO, reference_node=reference,
        variables=tuple(variables),
        equations=tuple(equations),
    )


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def nodi_da_kernel(ir: IR) -> dict[str, Fraction]:
    sol = solve_dc(ir)
    v: dict[str, Fraction] = {REFERENCE_NODE: F(0)}
    avanzato = True
    while avanzato:
        avanzato = False
        for c in ir.components:
            p, q = c.terminals
            vd = sol[c.id]["voltage"]
            if p in v and q not in v:
                v[q] = v[p] - vd
                avanzato = True
            elif q in v and p not in v:
                v[p] = v[q] + vd
                avanzato = True
    return v


def test_t1_singola_incognita_con_generatore_di_corrente():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(kcl((F(1, 10), "a"), (F(-1, 10), "0"), rhs=F(-2), focus="a"),),
    )
    sistema = build_linear_system(s)
    assert sistema.variables == (V("a"),)
    assert sistema.matrix == ((F(1, 10),),)
    assert sistema.rhs == (F(-2),)
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-20)
    assert sol.value_of(V("0")) == F(0)


def test_t2_sostituzione_tensione_nota():
    s = stato(
        variables=(
            nv("0", "reference"),
            nv("a", "unknown"),
            nv("b", "known_from_source", 5, "Vb"),
        ),
        equations=(
            kcl((F(3, 20), "a"), (F(-1, 10), "b"), (F(-1, 20), "0"), rhs=0, focus="a"),
        ),
    )
    sistema = build_linear_system(s)
    assert sistema.variables == (V("a"),)
    assert sistema.matrix == ((F(3, 20),),)
    assert sistema.rhs == (F(1, 2),)
    assert sistema.rhs != (F(-1, 2),)
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(10, 3)


def test_t3_due_incognite_ordinarie():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((2, "a"), (-1, "b"), rhs=-1, focus="a"),
            kcl((-1, "a"), (2, "b"), rhs=0, focus="b"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-2, 3)
    assert sol.value_of(V("b")) == F(-1, 3)


def test_t4_supernodo_canonico():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), (F(-3, 20), "0"), rhs=0, focus="V1"),
            vincolo((1, "a"), (-1, "b"), rhs=6, focus="V1"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(2)
    assert sol.value_of(V("b")) == F(-4)


def test_t5_sorgente_invertita():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), rhs=0, focus="V1"),
            vincolo((1, "b"), (-1, "a"), rhs=6, focus="V1"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-2)
    assert sol.value_of(V("b")) == F(4)


def test_t6_vincolo_negativo_frazionario():
    rhs = F(-7, 3)
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), rhs=0, focus="V1"),
            vincolo((1, "a"), (-1, "b"), rhs=rhs, focus="V1"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-7, 9)
    assert sol.value_of(V("b")) == F(14, 9)
    assert all(isinstance(item.value, Fraction) for item in sol.values)
    assert sol.value_of(V("a")) != abs(sol.value_of(V("a")))
