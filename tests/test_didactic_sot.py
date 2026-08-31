"""P0-A / P1-A: una sola source of truth per l'IR lineare didattico."""
from __future__ import annotations

import ast
from pathlib import Path

import kirchhoff.domain.didactic.analytical as analytical_mod
import kirchhoff.domain.didactic.derivation as derivation_mod
from kirchhoff.domain.didactic import ExactEquation, LinearTerm, VariableRef


def test_sot_unica_per_equazione_e_termine():
    assert ExactEquation is derivation_mod.ExactEquation
    assert LinearTerm is derivation_mod.LinearTerm
    assert VariableRef is derivation_mod.VariableRef
    assert analytical_mod.ExactEquation is derivation_mod.ExactEquation
    assert analytical_mod.LinearTerm is derivation_mod.LinearTerm


def test_classi_definite_solo_in_derivation():
    radice = Path(__file__).resolve().parents[1] / "src" / "kirchhoff" / "domain" / "didactic"
    attese = {"ExactEquation", "LinearTerm", "VariableRef"}
    definite = []
    residue = []
    for percorso in sorted(radice.glob("*.py")):
        albero = ast.parse(percorso.read_text(), filename=str(percorso))
        for nodo in ast.walk(albero):
            if not isinstance(nodo, ast.ClassDef):
                continue
            if nodo.name in attese:
                definite.append((percorso.name, nodo.name))
            if nodo.name == "NodalTerm":
                residue.append(percorso.name)
    assert residue == []
    assert sorted(definite) == [
        ("derivation.py", "ExactEquation"),
        ("derivation.py", "LinearTerm"),
        ("derivation.py", "VariableRef"),
    ]
