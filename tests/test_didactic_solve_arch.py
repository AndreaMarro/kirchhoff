"""P1-G: determinismo, esattezza e confine architetturale."""
from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from kirchhoff.domain.didactic import (
    DerivationSolution,
    ExactLinearSystem,
    SolvedVariable,
    build_linear_system,
    solve_derivation,
)

from test_didactic_solve import F, V, kcl, nv, stato


def test_d1_ordine_dichiarazione_irrilevante():
    eq = kcl((F(3, 20), "a"), (F(-1, 10), "b"), (F(-1, 20), "0"), rhs=0, focus="a")
    s1 = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "known_from_source", 5, "Vb")),
        equations=(eq,),
    )
    s2 = stato(
        variables=(nv("b", "known_from_source", 5, "Vb"), nv("a", "unknown"), nv("0", "reference")),
        equations=(eq,),
    )
    a, b = build_linear_system(s1), build_linear_system(s2)
    assert a.variables == b.variables == (V("a"),)
    assert a.matrix == b.matrix and a.rhs == b.rhs


def test_d2_ordine_equazioni_cambia_righe_non_la_soluzione():
    e1 = kcl((2, "a"), (-1, "b"), rhs=-1, focus="a")
    e2 = kcl((-1, "a"), (2, "b"), rhs=0, focus="b")
    s1 = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(e1, e2),
    )
    s2 = replace(s1, identifier="D5", equations=(e2, e1))
    assert build_linear_system(s1).matrix != build_linear_system(s2).matrix
    sol1, sol2 = solve_derivation(s1), solve_derivation(s2)
    assert sol1.value_of(V("a")) == sol2.value_of(V("a")) == F(-2, 3)
    assert sol1.value_of(V("b")) == sol2.value_of(V("b")) == F(-1, 3)


def test_d3_ordine_canonico_della_soluzione():
    s = stato(
        variables=(nv("b", "unknown"), nv("a", "unknown"), nv("0", "reference")),
        equations=(
            kcl((2, "a"), (-1, "b"), rhs=-1, focus="a"),
            kcl((-1, "a"), (2, "b"), rhs=0, focus="b"),
        ),
    )
    sol = solve_derivation(s)
    assert tuple(item.variable for item in sol.values) == (V("0"), V("a"), V("b"))


def test_e1_solo_fraction():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "known_from_source", 5, "Vb")),
        equations=(kcl((F(3, 20), "a"), (F(-1, 10), "b"), (F(-1, 20), "0"), rhs=0, focus="a"),),
    )
    sistema = build_linear_system(s)
    assert all(type(c) is Fraction for r in sistema.matrix for c in r)
    assert all(type(v) is Fraction for v in sistema.rhs)
    assert all(type(item.value) is Fraction for item in solve_derivation(s).values)


def test_e2_nessun_letterale_float_in_solve():
    percorso = Path(__file__).resolve().parents[1] / "src/kirchhoff/domain/didactic/solve.py"
    albero = ast.parse(percorso.read_text(encoding="utf-8"), filename=str(percorso))
    assert [
        n.value for n in ast.walk(albero)
        if isinstance(n, ast.Constant) and isinstance(n.value, float)
    ] == []


def test_a3_firma_solo_state():
    assert list(inspect.signature(solve_derivation).parameters) == ["state"]
    assert list(inspect.signature(build_linear_system).parameters) == ["state"]


def test_a4_stato_immutabile():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(kcl((F(1, 10), "a"), rhs=F(-2), focus="a"),),
    )
    originale, variabili, equazioni = s, s.variables, s.equations
    sol = solve_derivation(s)
    assert s == originale and s.variables is variabili and s.equations is equazioni
    assert sol.derivation_id == s.identifier
