"""Il contratto di presentazione: tipizzato, esatto, senza doppioni elettrici.

`StudentSessionView` e' l'unico tipo fra Python e browser. Questi test
inchiodano le chiavi (ancora di parita' per TypeScript), l'esattezza prima
del decimale, il vocabolario di verita' (mai Product Verified) e il fatto
che la proiezione non risolve niente da sola.
"""
from __future__ import annotations

import ast
import json
from fractions import Fraction
from pathlib import Path

import pytest

from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.presentation import (
    SCHEMA_VERSION,
    QuestionView,
    StudentSessionView,
    decimale,
    project_failure,
    project_refusal,
    to_json,
)

RADICE = Path(__file__).resolve().parent.parent

CHIAVI_VISTA = frozenset({
    "answer", "failure", "outcome", "provenance", "question", "refusal",
    "schema_version", "session_id", "states", "steps", "truth", "verification",
})

CHIAVI_PASSO = frozenset({
    "action", "affected", "after_ref", "after_svg", "before_ref",
    "before_svg", "equation", "equations", "evidence_refs", "index", "kind",
    "preserved",
})


def _chiusa():
    import sys
    import tempfile
    sys.path.insert(0, str(RADICE / "scripts"))
    import generate_workbench as gen
    with tempfile.TemporaryDirectory() as tmp:
        gen.genera(Path(tmp), "0" * 40)
        vista = json.loads((Path(tmp) / "partitore-d1.json").read_text(encoding="utf-8"))
    return vista


def test_le_chiavi_della_vista_sono_il_contratto():
    assert set(_chiusa().keys()) == CHIAVI_VISTA


def test_le_chiavi_del_passo_sono_il_contratto():
    for passo in _chiusa()["steps"]:
        assert set(passo.keys()) == CHIAVI_PASSO


def test_l_esatto_comanda_e_il_decimale_accompagna():
    vista = _chiusa()
    assert vista["answer"]["exact"] == "3/80"
    assert vista["answer"]["decimal"] == "0.0375"
    assert vista["answer"]["unit"] == "ampere"
    assert vista["answer"]["target"] == "R1"
    assert Fraction(vista["answer"]["exact"]) == Fraction(3, 80)
    assert decimale(Fraction(33, 4)) == "8.25"


def test_il_vocabolo_di_verita_non_crolla():
    vista = _chiusa()
    assert vista["truth"]["electrical_claim_status"] == "VERIFIED"
    assert vista["truth"]["backend_closure_status"] == "CLOSED"
    assert vista["truth"]["product_verified"] is False
    assert vista["verification"]["claim_status"] == "VERIFIED"
    assert "Product Verified" not in json.dumps(vista)


def test_il_rifiuto_e_una_superficie_senza_risposta():
    vista = project_refusal(
        Refusal("unsolvable", "q1", "request", "nessuna tecnica"),
        QuestionView("q1", "voltage", "R1"),
        source_sha="0" * 40, detail="prova")
    assert vista.outcome == "refusal"
    assert vista.answer is None
    assert vista.truth.electrical_claim_status is None
    assert vista.truth.backend_closure_status is None
    assert vista.truth.product_verified is False
    assert vista.states == () and vista.steps == ()
    assert vista.refusal.diagnosis == "nessuna tecnica"
    corpo = json.loads(to_json(vista))
    assert set(corpo.keys()) == CHIAVI_VISTA
    assert "Product Verified" not in to_json(vista)


def test_il_guasto_e_distinto_dal_rifiuto():
    vista = project_failure(
        Failure("render", "filo rotto"), QuestionView("q1", "current", "R1"),
        source_sha="0" * 40, detail="prova")
    assert vista.outcome == "failure"
    assert vista.answer is None
    assert vista.failure.dove == "render"
    assert vista.refusal is None


def test_gli_esiti_incoerenti_non_si_costruiscono():
    with pytest.raises(ValueError):
        StudentSessionView(
            schema_version=SCHEMA_VERSION, session_id="x", outcome="closed",
            question=None, answer=None, truth=None, states=(), steps=(),
            verification=None, provenance=None, refusal=None, failure=None)


def test_la_proiezione_non_importa_solutori():
    albero = ast.parse(
        (RADICE / "src" / "kirchhoff" / "pipeline" / "presentation.py")
        .read_text(encoding="utf-8"))
    importati = set()
    for stmt in albero.body:
        if isinstance(stmt, ast.If):
            test = stmt.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        for nodo in ast.walk(stmt):
            if isinstance(nodo, ast.Import):
                importati.update(a.name for a in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                importati.add(nodo.module)
    vietati = {
        "kirchhoff.domain.mna", "kirchhoff.domain.independent_dc",
        "kirchhoff.domain.truthfulness", "kirchhoff.domain.verify",
        "kirchhoff.domain.didactic.planner", "kirchhoff.domain.didactic.orchestrate",
        "kirchhoff.domain.didactic.solve", "kirchhoff.domain.transform.engine",
    }
    assert importati & vietati == set()
    chiamate = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Call):
            if isinstance(nodo.func, ast.Name):
                chiamate.add(nodo.func.id)
            elif isinstance(nodo.func, ast.Attribute):
                chiamate.add(nodo.func.attr)
    vietate = {
        "transform", "orchestrate_didactic_run", "pianifica", "execute_plan",
        "solve_dc", "solve_phasor", "solve_dc_tableau", "truthfulness_gate",
        "certify_execution", "run_proof_session", "run_proof_session_con_run",
    }
    assert chiamate & vietate == set()


def test_il_decimale_non_sostituisce_mai_l_esatto():
    assert decimale(Fraction(1, 3)) == "0.3333"
    assert decimale(Fraction(3, 80)) == "0.0375"
