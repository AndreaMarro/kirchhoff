"""P1-G: contratti dei tipi derivati e confine di import."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from kirchhoff.domain.didactic import (
    DerivationSolution,
    ExactLinearSystem,
    SolvedVariable,
    build_linear_system,
    solve_derivation,
)

from test_didactic_solve import F, V, kcl, nv, stato, vincolo


def test_exact_linear_system_guardie():
    with pytest.raises(ValueError, match="senza variabili"):
        ExactLinearSystem((), (), ())
    with pytest.raises(ValueError, match="lunghezze diverse"):
        ExactLinearSystem((V("a"),), ((F(1),),), ())
    with pytest.raises(ValueError, match="non è quadrato"):
        ExactLinearSystem((V("a"), V("b")), ((F(1), F(0)),), (F(1),))
    with pytest.raises(TypeError, match="VariableRef"):
        ExactLinearSystem(("a",), ((F(1),),), (F(1),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicata"):
        ExactLinearSystem((V("a"), V("a")), ((F(1), F(0)), (F(0), F(1))), (F(1), F(0)))
    with pytest.raises(ValueError, match="ordine canonico"):
        ExactLinearSystem((V("b"), V("a")), ((F(1), F(0)), (F(0), F(1))), (F(1), F(0)))
    with pytest.raises(ValueError, match="lunghezza errata"):
        ExactLinearSystem((V("a"),), ((F(1), F(0)),), (F(1),))
    with pytest.raises(TypeError, match="coefficiente"):
        ExactLinearSystem((V("a"),), ((1,),), (F(1),))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="rhs"):
        ExactLinearSystem((V("a"),), ((F(1),),), (1,))  # type: ignore[arg-type]


def test_solved_variable_e_solution_guardie():
    with pytest.raises(TypeError, match="VariableRef"):
        SolvedVariable("a", F(1))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Fraction"):
        SolvedVariable(V("a"), 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="senza identificatore"):
        DerivationSolution("", (SolvedVariable(V("a"), F(1)),))
    with pytest.raises(ValueError, match="senza valori"):
        DerivationSolution("D1", ())
    with pytest.raises(TypeError, match="SolvedVariable"):
        DerivationSolution("D1", ("x",))  # type: ignore[arg-type]


def test_kind_non_speciale_algebraicamente():
    variabili = (nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown"))
    termini = ((1, "a"), (-1, "b"))
    come_kcl = stato(
        identifier="Dk", variables=variabili,
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), rhs=0, focus="a"),
            kcl(*termini, rhs=6, focus="b"),
        ),
    )
    come_vincolo = stato(
        identifier="Dv", variables=variabili,
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), rhs=0, focus="V1"),
            vincolo(*termini, rhs=6, focus="V1"),
        ),
    )
    assert build_linear_system(come_kcl).rhs == build_linear_system(come_vincolo).rhs
    assert solve_derivation(come_kcl).value_of(V("a")) == solve_derivation(come_vincolo).value_of(V("a"))


def test_a1_a2_confine_import():
    percorso = Path(__file__).resolve().parents[1] / "src/kirchhoff/domain/didactic/solve.py"
    testo = percorso.read_text(encoding="utf-8")
    albero = ast.parse(testo, filename=str(percorso))
    moduli = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            moduli.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            moduli.add(nodo.module.split(".")[0])
    assert moduli.isdisjoint({"sympy", "lcapy", "numpy", "scipy", "egglog", "ir", "mna"})
    for vietato in ("from ..ir", "from ..mna", "solve_dc", "CircuitIR"):
        assert vietato not in testo
