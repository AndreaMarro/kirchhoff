"""P0-A: ExactEquation e NodalTerm hanno una sola definizione autoritativa."""
from __future__ import annotations

import ast
from pathlib import Path

import kirchhoff.domain.didactic.analytical as analytical_mod
import kirchhoff.domain.didactic.derivation as derivation_mod
from kirchhoff.domain.didactic import ExactEquation, NodalTerm


def test_sot_unica_per_equazione_e_termine():
    assert ExactEquation is derivation_mod.ExactEquation
    assert NodalTerm is derivation_mod.NodalTerm
    assert analytical_mod.ExactEquation is derivation_mod.ExactEquation
    assert analytical_mod.NodalTerm is derivation_mod.NodalTerm


def test_classi_definite_solo_in_derivation():
    radice = Path(__file__).resolve().parents[1] / "src" / "kirchhoff" / "domain" / "didactic"
    definite = []
    for percorso in sorted(radice.glob("*.py")):
        albero = ast.parse(percorso.read_text(), filename=str(percorso))
        for nodo in ast.walk(albero):
            if isinstance(nodo, ast.ClassDef) and nodo.name in {"ExactEquation", "NodalTerm"}:
                definite.append((percorso.name, nodo.name))
    assert definite == [("derivation.py", "NodalTerm"), ("derivation.py", "ExactEquation")]
