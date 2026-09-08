"""Il contratto di presentazione: tipizzato, esatto, senza doppioni elettrici.

`StudentSessionView` e' l'unico tipo fra Python e browser. Questi test
inchiodano le chiavi (ancora di parita' per TypeScript), l'esattezza prima
del decimale, il vocabolario di verita' (mai Product Verified) e il fatto
che la proiezione non risolve niente da sola.
"""
from __future__ import annotations

import ast
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import EntityRef
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
from kirchhoff.pipeline.risolvi import layout_a_maglia
from kirchhoff.render.layout import LayoutIR, Placement

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

D1_100 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

D1_200 = """\
V1 b 0 12 volt
R1 b a 200 ohm
R2 a 0 220 ohm
? current R1
"""

PONTE_12 = """\
V1 c 0 12 volt
R1 c a 10 ohm
R2 c b 20 ohm
R3 a 0 30 ohm
R4 b 0 40 ohm
Rg a b 50 ohm
? current R4
"""

PONTE_M12 = """\
V1 c 0 -12 volt
R1 c a 10 ohm
R2 c b 20 ohm
R3 a 0 30 ohm
R4 b 0 40 ohm
Rg a b 50 ohm
? current R4
"""

PIAZZAMENTI_PONTE = (
    Placement(EntityRef("node", "0"), Fraction(200), Fraction(20)),
    Placement(EntityRef("node", "a"), Fraction(20), Fraction(220)),
    Placement(EntityRef("node", "b"), Fraction(380), Fraction(220)),
    Placement(EntityRef("node", "c"), Fraction(200), Fraction(160)),
    Placement(EntityRef("component", "V1"), Fraction(200), Fraction(90)),
    Placement(EntityRef("component", "R1"), Fraction(110), Fraction(190)),
    Placement(EntityRef("component", "R2"), Fraction(290), Fraction(190)),
    Placement(EntityRef("component", "R3"), Fraction(110), Fraction(120)),
    Placement(EntityRef("component", "R4"), Fraction(290), Fraction(120)),
    Placement(EntityRef("component", "Rg"), Fraction(200), Fraction(220)),
)


def _layout_ponte(istante: int = 2, casualita: bytes | None = None) -> LayoutIR:
    return LayoutIR.nuovo(
        PIAZZAMENTI_PONTE,
        istante=istante,
        casualita=casualita or bytes(range(10, 20)),
    )


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
    with pytest.raises(ValueError):
        StudentSessionView(
            schema_version="altro", session_id="x", outcome="failure",
            question=None, answer=None, truth=None, states=(), steps=(),
            verification=None, provenance=None, refusal=None,
            failure=None)
    with pytest.raises(ValueError):
        StudentSessionView(
            schema_version=SCHEMA_VERSION, session_id="x", outcome="refusal",
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


def _chiusura_con_run(netlist):
    import itertools
    from datetime import datetime, timezone
    from kirchhoff.domain.proof.session import DOCUMENT_PROFILE
    from kirchhoff.pipeline.proof_run import run_proof_session_con_run

    class Fermo:
        def now(self):
            return datetime(2026, 9, 7, 12, tzinfo=timezone.utc)

    conto = itertools.count(7)

    def entropia():
        return bytes(((next(conto) + j) % 256 for j in range(10)))

    ir = leggi(netlist)
    richiesta = next(iter(ir.requests))
    esito = run_proof_session_con_run(
        ir, richiesta, clock=Fermo(), entropy=entropia,
        document_profile=DOCUMENT_PROFILE, source_sha="0" * 40, detail="prova")
    assert not isinstance(esito, (Failure, Refusal))
    return esito


def test_disposizione_incoerente_e_failure_di_render():
    from kirchhoff.pipeline.failure import Failure
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura_b, run_b = _chiusura_con_run(PONTE_12)
    esito = project_closed_session(
        chiusura_b.session, chiusura_b.registry, run_b,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "render"


def test_sessione_scambiata_con_altra_run_e_failure_di_proiezione():
    from kirchhoff.pipeline.failure import Failure
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura_a, run_a = _chiusura_con_run(D1_100)
    chiusura_b, _ = _chiusura_con_run(PONTE_12)
    esito = project_closed_session(
        chiusura_b.session, chiusura_b.registry, run_a,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "publication"


def test_difetto_del_render_nella_proiezione_e_failure(monkeypatch):
    import kirchhoff.pipeline.presentation as proiezione
    from kirchhoff.pipeline.failure import Failure
    chiusura, run = _chiusura_con_run(D1_100)

    def rotto(*a, **k):
        raise ValueError("pennello rotto")

    monkeypatch.setattr(proiezione, "render", rotto)
    esito = proiezione.project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "render"


def test_matrice_mix_serie_rigettata_prima_del_render():
    from kirchhoff.pipeline.presentation import project_closed_session
    ch_a, run_a = _chiusura_con_run(D1_100)
    ch_b, run_b = _chiusura_con_run(D1_200)

    assert ch_a.session.state_refs == ch_b.session.state_refs
    assert run_a.state_ids == run_b.state_ids
    assert ch_a.session.final_solution != ch_b.session.final_solution
    assert Fraction(ch_a.session.final_solution.value.amount) == Fraction(3, 80)
    assert Fraction(ch_b.session.final_solution.value.amount) == Fraction(1, 35)

    layout = layout_a_maglia(leggi(D1_100))
    esito_ok = project_closed_session(
        ch_a.session, ch_a.registry, run_a,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito_ok, Failure)
    assert esito_ok.outcome == "closed"
    assert esito_ok.answer.exact == "3/80"

    mix = [
        ("A/B/A", ch_a.session, run_b, ch_a.registry),
        ("A/A/B", ch_a.session, run_a, ch_b.registry),
        ("A/B/B", ch_a.session, run_b, ch_b.registry),
    ]
    for etichetta, sessione, run, registro in mix:
        esito = project_closed_session(
            sessione, registro, run,
            layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
        assert isinstance(esito, Failure), etichetta
        assert esito.dove == "publication", etichetta


def test_matrice_mix_ponte_rigettata_prima_del_render():
    from kirchhoff.pipeline.presentation import project_closed_session
    ch_a, run_a = _chiusura_con_run(PONTE_12)
    ch_b, run_b = _chiusura_con_run(PONTE_M12)

    assert ch_a.session.state_refs == ch_b.session.state_refs
    assert run_a.state_ids == run_b.state_ids
    assert ch_a.session.final_solution != ch_b.session.final_solution
    assert Fraction(ch_a.session.final_solution.value.amount) == Fraction(87, 425)
    assert Fraction(ch_b.session.final_solution.value.amount) == Fraction(-87, 425)

    layout = _layout_ponte()
    esito_ok = project_closed_session(
        ch_a.session, ch_a.registry, run_a,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito_ok, Failure)
    assert esito_ok.outcome == "closed"
    assert esito_ok.answer.exact == "87/425"

    mix = [
        ("A/B/A", ch_a.session, run_b, ch_a.registry),
        ("A/A/B", ch_a.session, run_a, ch_b.registry),
        ("A/B/B", ch_a.session, run_b, ch_b.registry),
    ]
    for etichetta, sessione, run, registro in mix:
        esito = project_closed_session(
            sessione, registro, run,
            layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
        assert isinstance(esito, Failure), etichetta
        assert esito.dove == "publication", etichetta


def test_d1_proiettata_domanda_originale_retARGET_e_svg():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    layout = layout_a_maglia(leggi(D1_100))
    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"
    assert esito.question.target == "R1"
    assert esito.answer.target == "R1"
    assert esito.answer.exact == "3/80"
    assert esito.answer.unit == "ampere"
    assert len(esito.states) == 2
    assert all("<svg" in s.svg for s in esito.states)
    assert any(s.ref == chiusura.session.initial_state_ref for s in esito.states)
    assert esito.steps[0].kind == "transform"
    assert esito.steps[-1].kind == "analytical"


def test_ponte_zero_trasformazioni_proiettato():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(PONTE_12)
    assert run.transform_executions == ()
    layout = _layout_ponte()
    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"
    assert esito.answer.exact == "87/425"
    assert all(p.kind == "analytical" for p in esito.steps)


def test_deepcopy_del_solo_registro_ammesso_live():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    registro_copia = deepcopy(chiusura.registry)
    esito = project_closed_session(
        chiusura.session, registro_copia, run,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"


def test_deepcopy_congiunto_ammesso_live():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    sessione_copia, run_copia, registro_copia = deepcopy(
        (chiusura.session, run, chiusura.registry))
    esito = project_closed_session(
        sessione_copia, registro_copia, run_copia,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"


def test_deepcopy_della_sola_sessione_rifiutata_live():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    sessione_copia = deepcopy(chiusura.session)
    esito = project_closed_session(
        sessione_copia, chiusura.registry, run,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "publication"


def test_mix_serie_non_chiama_render(monkeypatch):
    import kirchhoff.pipeline.presentation as proiezione
    from kirchhoff.pipeline.failure import Failure
    ch_a, run_a = _chiusura_con_run(D1_100)
    _, run_b = _chiusura_con_run(D1_200)
    layout = layout_a_maglia(leggi(D1_100))
    chiamate: list[str] = []

    def render_cattivo(*a, **k):
        chiamate.append("render")
        raise AssertionError("render chiamato su mix")

    monkeypatch.setattr(proiezione, "render", render_cattivo)
    esito = proiezione.project_closed_session(
        ch_a.session, ch_a.registry, run_b,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "publication"
    assert chiamate == []


def test_proiezione_valida_non_ricalcola_semantica(monkeypatch):
    import kirchhoff.domain.didactic.execute as execute
    import kirchhoff.domain.didactic.orchestrate as orchestrate
    import kirchhoff.domain.didactic.planner as planner
    import kirchhoff.domain.didactic.solve as solve
    import kirchhoff.domain.independent_dc as independent_dc
    import kirchhoff.domain.mna as mna
    import kirchhoff.domain.transform.engine as transform_engine
    import kirchhoff.domain.truthfulness as truthfulness
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    layout = layout_a_maglia(leggi(D1_100))

    def boom(*a, **k):
        raise AssertionError("chiamata semantica durante la proiezione")

    monkeypatch.setattr(planner, "pianifica", boom)
    monkeypatch.setattr(execute, "execute_plan", boom)
    monkeypatch.setattr(transform_engine, "transform", boom)
    monkeypatch.setattr(solve, "solve_derivation", boom)
    monkeypatch.setattr(mna, "solve_dc", boom)
    monkeypatch.setattr(mna, "solve_phasor", boom)
    monkeypatch.setattr(independent_dc, "solve_dc_tableau", boom)
    monkeypatch.setattr(truthfulness, "truthfulness_gate", boom)
    monkeypatch.setattr(truthfulness, "certify_execution", boom)
    monkeypatch.setattr(orchestrate, "orchestrate_didactic_run", boom)

    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout, istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"
