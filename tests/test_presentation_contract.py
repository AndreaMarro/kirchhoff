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
    "preserved", "derivation_ref", "justification",
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


SCALA_3R = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a c 220 ohm
R3 c 0 330 ohm
? current R1
"""

REATTIVO_C = """\
V1 b 0 12 volt
R1 b a 100 ohm
C1 a 0 1/1000 farad
? voltage R1
"""

PIAZZAMENTI_SCALA = (
    Placement(EntityRef("node", "b"), Fraction(0), Fraction(0)),
    Placement(EntityRef("node", "a"), Fraction(200), Fraction(0)),
    Placement(EntityRef("node", "c"), Fraction(400), Fraction(0)),
    Placement(EntityRef("node", "0"), Fraction(200), Fraction(240)),
    Placement(EntityRef("component", "V1"), Fraction(0), Fraction(120)),
    Placement(EntityRef("component", "R1"), Fraction(100), Fraction(0)),
    Placement(EntityRef("component", "R2"), Fraction(300), Fraction(0)),
    Placement(EntityRef("component", "R3"), Fraction(400), Fraction(120)),
)


def _layout_scala(istante: int = 3, casualita: bytes | None = None) -> LayoutIR:
    return LayoutIR.nuovo(
        PIAZZAMENTI_SCALA,
        istante=istante,
        casualita=casualita or bytes(range(20, 30)),
    )


def _vista_chiusa_legale():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(D1_100)
    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout_a_maglia(leggi(D1_100)),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"
    return esito


def _ricostruisci(vista):
    return StudentSessionView(
        schema_version=vista.schema_version, session_id=vista.session_id,
        outcome=vista.outcome, question=vista.question, answer=vista.answer,
        truth=vista.truth, states=vista.states, steps=vista.steps,
        verification=vista.verification, provenance=vista.provenance,
        refusal=vista.refusal, failure=vista.failure)


def test_p1a_product_verified_true_respinto():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, truth=dataclasses.replace(
                vista.truth, product_verified=True)))


def test_p1a_chiusura_backend_verificata_respinta():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, truth=dataclasses.replace(
                vista.truth, backend_closure_status="VERIFIED")))


def test_p1a_claim_contraddittorio_respinto():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, verification=dataclasses.replace(
                vista.verification, claim_status="UNVERIFIED")))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, verification=dataclasses.replace(
                vista.verification, session_status="VERIFIED")))


def test_p1a_domanda_assente_respinta():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(vista, question=None))


def test_p1a_risposta_non_coerente_con_domanda_respinta():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, answer=dataclasses.replace(vista.answer, target="R999")))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, answer=dataclasses.replace(
                vista.answer, quantity="voltage")))


def test_p1a_unita_incompatibile_respinta():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, answer=dataclasses.replace(vista.answer, unit="volt")))


@pytest.mark.parametrize("esatto", [
    "1/0", "5/0", "1/00", "abc", "", " ", "3.14", "1e3", "1E-3",
    "1/2/3", "3/", "/4", "tre/80", "3 /80", "3/ 80", "50%", "0x10",
    "NaN", "Infinity",
])
def test_p1a_exact_illecito_respinto(esatto):
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, answer=dataclasses.replace(vista.answer, exact=esatto)))


@pytest.mark.parametrize("esatto", [
    "3/80", "0", "5", "-3/80", "-7", "10/4", " 3/80 ",
])
def test_p1a_exact_lecito_accettato(esatto):
    import dataclasses
    vista = _vista_chiusa_legale()
    mutata = dataclasses.replace(
        vista, answer=dataclasses.replace(vista.answer, exact=esatto))
    assert _ricostruisci(mutata).answer.exact == esatto


def test_p1a_stati_vuoti_duplicati_o_pendenti_respinti():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(vista, states=()))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, states=vista.states + (vista.states[0],)))
    passo = dataclasses.replace(vista.steps[0], before_ref="ir_pendente")
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, steps=(passo,) + vista.steps[1:]))


def test_p1a_indici_illeciti_respinti():
    import dataclasses
    vista = _vista_chiusa_legale()
    for indice in (True, False, 1.5, -1, float("inf"), float("nan"), "0"):
        passo = dataclasses.replace(vista.steps[0], index=indice)
        with pytest.raises(ValueError):
            _ricostruisci(dataclasses.replace(
                vista, steps=(passo,) + vista.steps[1:]))
    duplicato = dataclasses.replace(vista.steps[1], index=vista.steps[0].index)
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, steps=(vista.steps[0], duplicato) + vista.steps[2:]))
    spostato = dataclasses.replace(vista.steps[-1], index=99)
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, steps=vista.steps[:-1] + (spostato,)))


def test_p1a_chiusa_con_rifiuto_o_guasto_respinta():
    import dataclasses
    vista = _vista_chiusa_legale()
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, refusal=project_refusal(
                Refusal("unsolvable", "q1", "request", "x"),
                QuestionView("q1", "current", "R1"),
                source_sha="0" * 40, detail="prova").refusal))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, failure=project_failure(
                Failure("render", "x"), QuestionView("q1", "current", "R1"),
                source_sha="0" * 40, detail="prova").failure))


@pytest.mark.parametrize("outcome", ["refusal", "failure"])
def test_p1a_esiti_negativi_con_attestazioni_positive_respinti(outcome):
    import dataclasses
    vista = _vista_chiusa_legale()
    if outcome == "refusal":
        negativa = project_refusal(
            Refusal("unsolvable", "q1", "request", "nessuna tecnica"),
            QuestionView("q1", "voltage", "R1"),
            source_sha="0" * 40, detail="prova")
    else:
        negativa = project_failure(
            Failure("render", "filo rotto"), QuestionView("q1", "current", "R1"),
            source_sha="0" * 40, detail="prova")
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(negativa, verification=vista.verification))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            negativa,
            truth=dataclasses.replace(
                negativa.truth, electrical_claim_status="VERIFIED")))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            negativa, answer=vista.answer))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            negativa, states=vista.states, steps=vista.steps))


def test_p1a_passo_analitico_con_ref_diversi_respinto():
    import dataclasses
    vista = _vista_chiusa_legale()
    analitici = [p for p in vista.steps if p.kind == "analytical"]
    assert analitici
    refs = [s.ref for s in vista.states]
    altro = next(r for r in refs if r != analitici[0].before_ref)
    mutato = dataclasses.replace(analitici[0], after_ref=altro)
    passi = tuple(mutato if p == analitici[0] else p for p in vista.steps)
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(vista, steps=passi))


def test_p1a_evidence_ids_vuote_respinte_con_controllo_lecito_adiacente():
    import dataclasses
    vista = _vista_chiusa_legale()
    assert vista.verification.evidence_ids
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, verification=dataclasses.replace(
                vista.verification, evidence_ids=())))
    assert _ricostruisci(vista).verification.evidence_ids


def test_p1a_kind_passo_fuori_vocabolo_respinto():
    import dataclasses
    vista = _vista_chiusa_legale()
    mutato = dataclasses.replace(vista.steps[0], kind="misterioso")
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            vista, steps=(mutato,) + vista.steps[1:]))


def test_p1a_scala_due_riduzioni_proiettata():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(SCALA_3R)
    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=_layout_scala(), istante=1,
        casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.outcome == "closed"
    assert esito.answer.target == "R1" == esito.question.target
    assert _ricostruisci(esito).outcome == "closed"


def test_p1a_ponte_negativo_proiettato():
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(PONTE_M12)
    esito = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=_layout_ponte(), istante=1,
        casualita=bytes(range(10)))
    assert not isinstance(esito, Failure)
    assert esito.answer.exact == "-87/425"
    assert _ricostruisci(esito).outcome == "closed"


def test_p1a_rifiuto_reattivo_legale():
    import itertools
    from datetime import datetime, timezone
    from kirchhoff.domain.proof.session import DOCUMENT_PROFILE
    from kirchhoff.pipeline.proof_run import run_proof_session_con_run

    class Fermo:
        def now(self):
            return datetime(2026, 9, 7, 12, tzinfo=timezone.utc)

    conto = itertools.count(300)

    def entropia():
        return bytes(((next(conto) + j) % 256 for j in range(10)))

    ir = leggi(REATTIVO_C)
    esito = run_proof_session_con_run(
        ir, next(iter(ir.requests)), clock=Fermo(), entropy=entropia,
        document_profile=DOCUMENT_PROFILE, source_sha="0" * 40, detail="prova")
    assert isinstance(esito, Refusal)
    vista = project_refusal(
        esito, QuestionView("q1", "voltage", "R1"),
        source_sha="0" * 40, detail="prova")
    assert _ricostruisci(vista).outcome == "refusal"


def test_p1a_guasto_senza_domanda_legale():
    vista = project_failure(
        Failure("render", "filo rotto"), None,
        source_sha="0" * 40, detail="prova")
    assert vista.outcome == "failure"
    assert _ricostruisci(vista).outcome == "failure"


@pytest.mark.parametrize("outcome", ["refusal", "failure"])
def test_p1a_status_non_positivo_in_esito_negativo_accettato(outcome):
    import dataclasses
    if outcome == "refusal":
        negativa = project_refusal(
            Refusal("unsolvable", "q1", "request", "nessuna tecnica"),
            QuestionView("q1", "voltage", "R1"),
            source_sha="0" * 40, detail="prova")
    else:
        negativa = project_failure(
            Failure("render", "filo rotto"), QuestionView("q1", "current", "R1"),
            source_sha="0" * 40, detail="prova")
    tollerata = dataclasses.replace(
        negativa, truth=dataclasses.replace(
            negativa.truth, backend_closure_status="FAILURE"))
    assert _ricostruisci(tollerata).outcome == outcome
    for chiusura in ("CLOSED", "VERIFIED"):
        with pytest.raises(ValueError):
            _ricostruisci(dataclasses.replace(
                negativa, truth=dataclasses.replace(
                    negativa.truth, backend_closure_status=chiusura)))
    with pytest.raises(ValueError):
        _ricostruisci(dataclasses.replace(
            negativa, truth=dataclasses.replace(
                negativa.truth, electrical_claim_status="VERIFIED")))


@pytest.mark.parametrize("volt", [12, 24])
def test_la_run_di_un_altra_chiusura_non_presta_i_suoi_disegni(volt):
    from kirchhoff.pipeline.presentation import project_closed_session
    from kirchhoff.pipeline.risolvi import layout_a_maglia
    netlist = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? current R1\n"
    chiusura, _ = _chiusura_con_run(netlist)
    _, altra_run = _chiusura_con_run(netlist.replace("12 volt", f"{volt} volt"))
    esito = project_closed_session(
        chiusura.session, chiusura.registry, altra_run,
        layout_iniziale=layout_a_maglia(leggi(netlist)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "publication"
    if volt == 12:
        assert esito.messaggio == "l'effetto del passo 0 non e' l'oggetto certificato della run"
    else:
        assert esito.messaggio == (
            "gli stati del registro non coincidono con gli stati operativi della run")


def test_il_registro_di_un_altro_circuito_non_presta_i_suoi_stati():
    from kirchhoff.pipeline.presentation import project_closed_session
    from kirchhoff.pipeline.risolvi import layout_a_maglia
    netlist = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? current R1\n"
    chiusura, run = _chiusura_con_run(netlist)
    altra_chiusura, _ = _chiusura_con_run(netlist.replace("12 volt", "24 volt"))
    esito = project_closed_session(
        chiusura.session, altra_chiusura.registry, run,
        layout_iniziale=layout_a_maglia(leggi(netlist)),
        istante=1, casualita=bytes(range(10)))
    assert isinstance(esito, Failure)
    assert esito.dove == "publication"
    assert esito.messaggio == (
        "gli stati del registro non coincidono con gli stati operativi della run")


@pytest.mark.parametrize("netlist,layout", [(D1_100, None), (SCALA_3R, _layout_scala)])
def test_h5_la_proiezione_conserva_il_legame_autorevole_della_derivazione(netlist, layout):
    from kirchhoff.domain.proof.session import AnalyticalProofStep
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(netlist)
    vista = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout() if layout else layout_a_maglia(leggi(netlist)),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(vista, Failure)
    attesi = {p.index: p.derivation_after for p in chiusura.session.steps
              if isinstance(p, AnalyticalProofStep)}
    assert attesi
    assert [getattr(p, "derivation_ref", None) for p in vista.steps
            if p.kind == "analytical"] == list(chiusura.session.final_claim.evidence_ids)
    for passo in vista.steps:
        assert getattr(passo, "derivation_ref", None) == attesi.get(passo.index)
    assert all(p.evidence_refs for p in vista.steps)


@pytest.mark.parametrize("caso", [
    "analitico-null", "analitico-blank", "analitico-numero", "analitico-bool",
    "trasformazione-ref", "duplicati-anche-nel-claim", "estraneo", "tutti-null",
    "ref-scambiati", "claim-riordinato", "claim-extra", "claim-incompleto",
    "spazi-id", "passi-riordinati",
])
def test_h5_il_confine_respinge_il_legame_incoerente(caso):
    from dataclasses import replace
    vista = _vista_chiusa_legale()
    # Il costruttore della sessione deve prima accettare il controllo sano.
    assert _ricostruisci(vista).outcome == "closed"
    passi = list(vista.steps)
    analitici = [i for i, p in enumerate(passi) if p.kind == "analytical"]
    primo, secondo = analitici[:2]
    verifica = vista.verification
    if caso == "analitico-null": passi[primo] = replace(passi[primo], derivation_ref=None)
    if caso == "analitico-blank": passi[primo] = replace(passi[primo], derivation_ref=" \n ")
    if caso == "analitico-numero": passi[primo] = replace(passi[primo], derivation_ref=3)
    if caso == "analitico-bool": passi[primo] = replace(passi[primo], derivation_ref=False)
    if caso == "trasformazione-ref": passi[0] = replace(passi[0], derivation_ref=passi[primo].derivation_ref)
    if caso == "duplicati-anche-nel-claim":
        passi[secondo] = replace(passi[secondo], derivation_ref=passi[primo].derivation_ref)
        verifica = replace(verifica, evidence_ids=(passi[primo].derivation_ref,) * 2)
    if caso == "estraneo": passi[primo] = replace(passi[primo], derivation_ref="D0")
    if caso == "tutti-null": passi = [replace(p, derivation_ref=None) for p in passi]
    if caso == "ref-scambiati":
        a, b = passi[primo].derivation_ref, passi[secondo].derivation_ref
        passi[primo] = replace(passi[primo], derivation_ref=b)
        passi[secondo] = replace(passi[secondo], derivation_ref=a)
    if caso == "claim-riordinato": verifica = replace(verifica, evidence_ids=tuple(reversed(verifica.evidence_ids)))
    if caso == "claim-extra": verifica = replace(verifica, evidence_ids=(*verifica.evidence_ids, "extra"))
    if caso == "claim-incompleto": verifica = replace(verifica, evidence_ids=verifica.evidence_ids[:-1])
    if caso == "spazi-id": passi[primo] = replace(passi[primo], derivation_ref=" " + passi[primo].derivation_ref + " ")
    if caso == "passi-riordinati": passi.reverse()
    with pytest.raises(ValueError):
        replace(vista, steps=tuple(passi), verification=verifica)


def test_h5_gli_identificatori_restano_opachi_senza_normalizzazione():
    from dataclasses import replace
    vista = _vista_chiusa_legale()
    nomi = ("origine-alfa", "derivazione-omega")
    mappa = dict(zip(vista.verification.evidence_ids, nomi))
    passi = tuple(replace(p, derivation_ref=mappa.get(p.derivation_ref)) for p in vista.steps)
    nuova = replace(vista, steps=passi, verification=replace(vista.verification, evidence_ids=nomi))
    assert nuova.verification.evidence_ids == nomi
    assert tuple(p.derivation_ref for p in nuova.steps if p.kind == "analytical") == nomi


def test_h5_due_trasformazioni_scambiate_non_cambiano_la_sequenza_analitica():
    from dataclasses import replace
    from kirchhoff.pipeline.presentation import project_closed_session
    chiusura, run = _chiusura_con_run(SCALA_3R)
    vista = project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=_layout_scala(), istante=1,
        casualita=bytes(range(10)))
    assert not isinstance(vista, Failure)
    assert _ricostruisci(vista).outcome == "closed"
    passi = list(vista.steps)
    assert passi[0].kind == passi[1].kind == "transform"
    passi[0], passi[1] = passi[1], passi[0]
    assert tuple(p.derivation_ref for p in passi if p.kind == "analytical") == vista.verification.evidence_ids
    with pytest.raises(ValueError, match="fuori ordine"):
        replace(vista, steps=tuple(passi))


@pytest.mark.parametrize("netlist,layout", [
    (D1_100, None), (SCALA_3R, _layout_scala), (PONTE_12, _layout_ponte),
])
def test_k4_la_giustificazione_esposta_proviene_dal_passo_canonico(netlist, layout, monkeypatch):
    """UX-DR23: quattro campi del passo, senza ricomporre o inventare fatti."""
    from dataclasses import asdict
    import kirchhoff.pipeline.presentation as proiezione

    chiusura, run = _chiusura_con_run(netlist)
    componi_reale = proiezione.componi
    giustificazioni = []

    def cattura(*args, **kwargs):
        passo_visuale = componi_reale(*args, **kwargs)
        assert not isinstance(passo_visuale, Failure)
        giustificazioni.append(passo_visuale.giustificazione)
        return passo_visuale

    monkeypatch.setattr(proiezione, "componi", cattura)
    vista = proiezione.project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=layout() if layout else layout_a_maglia(leggi(netlist)),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(vista, Failure)
    assert vista.outcome == "closed"
    assert len(giustificazioni) == len(run.transform_executions)
    corpo = json.loads(to_json(vista))
    trasformazioni = 0
    for passo in corpo["steps"]:
        assert "justification" in passo, "la vista non espone il profilo di giustificazione"
        if passo["kind"] == "analytical":
            assert passo["justification"] is None
            continue
        g = giustificazioni[trasformazioni]
        trasformazioni += 1
        attesa = {
            "terminals": [asdict(e) for e in g.terminali],
            "preconditions": list(g.precondizioni),
            "formula": str(g.formula),
            "certificate": json.loads(json.dumps(asdict(g.certificato))),
        }
        assert passo["justification"] == attesa
        assert set(passo["justification"]) == {
            "terminals", "preconditions", "formula", "certificate",
        }
        assert attesa["formula"] == passo["equation"]
        assert attesa["certificate"]["operation"] == passo["action"]
        assert "attestations" in attesa["certificate"]
    assert trasformazioni == len(giustificazioni)
    if netlist == D1_100:
        # Attesi indipendenti dal DTO: a e' interno eliminato, V1 solo preservato.
        prima = corpo["steps"][0]
        assert prima["justification"]["terminals"] == [
            {"kind": "node", "id": "0"}, {"kind": "node", "id": "b"},
        ]
        assert {"kind": "component", "id": "V1"} in prima["preserved"]
        assert prima["justification"]["formula"] == "R1R2eq = R1 + R2"
        assert prima["justification"]["certificate"]["attestations"] == []
    assert corpo["truth"]["product_verified"] is False


@pytest.fixture(scope="module")
def k4_vista_legale():
    """Fonte canonica condivisa, immutabile; ogni controesempio usa replace."""
    return _vista_chiusa_legale()


def _k4_giustificazione_mutata(g, caso):
    from dataclasses import replace
    from kirchhoff.pipeline.presentation import (
        EntityView, StepCertificateView, StepIdentityAttestationView,
    )

    def attestazione(**kwargs):
        return StepIdentityAttestationView(**{
            "entity": EntityView("component", "V1"), "changed": ("value",),
            **kwargs,
        })

    modifiche = {
        "assente": lambda: None,
        "oggetto_estraneo": lambda: {},
        "terminali_vuoti": lambda: replace(g, terminals=()),
        "terminali_non_tuple": lambda: replace(g, terminals=list(g.terminals)),
        "terminali_duplicati": lambda: replace(g, terminals=g.terminals * 2),
        "terminale_non_entita": lambda: replace(g, terminals=("0",)),
        "terminale_componente": lambda: replace(g, terminals=(EntityView("component", "V1"),)),
        "terminale_genere_ignoto": lambda: replace(g, terminals=(EntityView("altro", "0"),)),
        "terminale_id_vuoto": lambda: replace(g, terminals=(EntityView("node", " "),)),
        "terminale_id_non_testo": lambda: replace(g, terminals=(EntityView("node", 0),)),
        "terminale_interno": lambda: replace(g, terminals=(EntityView("node", "a"),)),
        "precondizioni_vuote": lambda: replace(g, preconditions=()),
        "precondizioni_scalare": lambda: replace(g, preconditions="condizione"),
        "precondizione_duplicata": lambda: replace(g, preconditions=("a", "a")),
        "precondizione_vuota": lambda: replace(g, preconditions=(" ",)),
        "precondizione_non_testo": lambda: replace(g, preconditions=(1,)),
        "formula_diversa": lambda: replace(g, formula="R = R1 * R2"),
        "formula_non_testo": lambda: replace(g, formula=1),
        "certificato_estraneo": lambda: replace(g, certificate={}),
        "operazione_diversa": lambda: replace(g, certificate=replace(g.certificate, operation="parallelo")),
        "operazione_vuota": lambda: replace(g, certificate=replace(g.certificate, operation=" ")),
        "operazione_non_testo": lambda: replace(g, certificate=replace(g.certificate, operation=1)),
        "controlli_vuoti": lambda: replace(g, certificate=replace(g.certificate, checks=())),
        "controlli_scalare": lambda: replace(g, certificate=replace(g.certificate, checks="check")),
        "controlli_duplicati": lambda: replace(g, certificate=replace(g.certificate, checks=("a", "a"))),
        "controllo_vuoto": lambda: replace(g, certificate=replace(g.certificate, checks=(" ",))),
        "controllo_non_testo": lambda: replace(g, certificate=replace(g.certificate, checks=(1,))),
        "attestazioni_non_tuple": lambda: replace(g, certificate=replace(g.certificate, attestations=[])),
        "attestazione_estranea": lambda: replace(g, certificate=replace(g.certificate, attestations=({},))),
        "attestazioni_soggetto_duplicato": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(), attestazione(changed=("type",))))),
        "attestazione_entita_estranea": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(entity="V1"),))),
        "attestazione_nodo": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(entity=EntityView("node", "0")),))),
        "attestazione_id_vuoto": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(entity=EntityView("component", " ")),))),
        "attestazione_non_preservata": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(entity=EntityView("component", "R1")),))),
        "attributi_vuoti": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(changed=()),))),
        "attributi_scalare": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(changed="value"),))),
        "attributi_duplicati": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(changed=("value", "value")),))),
        "attributo_non_testo": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(changed=(1,)),))),
        "attributo_ignoto": lambda: replace(g, certificate=replace(g.certificate, attestations=(attestazione(changed=("provenance",)),))),
    }
    return modifiche[caso]()


@pytest.mark.parametrize("caso", [
    "assente", "oggetto_estraneo", "terminali_vuoti", "terminali_non_tuple",
    "terminali_duplicati", "terminale_non_entita", "terminale_componente",
    "terminale_genere_ignoto", "terminale_id_vuoto", "terminale_id_non_testo",
    "terminale_interno", "precondizioni_vuote", "precondizioni_scalare",
    "precondizione_duplicata", "precondizione_vuota", "precondizione_non_testo",
    "formula_diversa", "formula_non_testo", "certificato_estraneo",
    "operazione_diversa", "operazione_vuota", "operazione_non_testo",
    "controlli_vuoti", "controlli_scalare", "controlli_duplicati", "controllo_vuoto",
    "controllo_non_testo", "attestazioni_non_tuple", "attestazione_estranea",
    "attestazioni_soggetto_duplicato", "attestazione_entita_estranea",
    "attestazione_nodo", "attestazione_id_vuoto", "attestazione_non_preservata",
    "attributi_vuoti", "attributi_scalare", "attributi_duplicati",
    "attributo_non_testo", "attributo_ignoto",
])
def test_k4_giustificazione_incoerente_respinta(k4_vista_legale, caso):
    from dataclasses import replace
    vista = k4_vista_legale
    assert _ricostruisci(vista) == vista
    primo = vista.steps[0]
    assert primo.kind == "transform" and primo.justification is not None
    with pytest.raises(ValueError, match="giustificazione|certificato|attestazione"):
        mutata = _k4_giustificazione_mutata(primo.justification, caso)
        _ricostruisci(replace(vista, steps=(replace(primo, justification=mutata),) + vista.steps[1:]))


def test_k4_analitico_non_accetta_giustificazione_topologica(k4_vista_legale):
    from dataclasses import replace
    vista = k4_vista_legale
    assert _ricostruisci(vista) == vista
    indice = next(i for i, p in enumerate(vista.steps) if p.kind == "analytical")
    passi = list(vista.steps)
    passi[indice] = replace(passi[indice], justification=passi[0].justification)
    with pytest.raises(ValueError, match="giustificazione"):
        _ricostruisci(replace(vista, steps=tuple(passi)))


def test_k4_trasporto_conserva_ordine_byte_e_attestazioni_senza_verificare_licenze(k4_vista_legale):
    """Attestazione sintetica di solo DTO: non e' una licenza del Catalogo."""
    from dataclasses import replace
    from kirchhoff.pipeline.presentation import EntityView, StepIdentityAttestationView
    vista = k4_vista_legale
    primo = vista.steps[0]
    g = primo.justification
    attestazione = StepIdentityAttestationView(EntityView("component", "V1"), ("value", "type"))
    nuova = replace(g, terminals=g.terminals[:1], preconditions=(" z ", "a"),
                    certificate=replace(g.certificate, checks=(" z ", "a"), attestations=(attestazione,)))
    corpo = json.loads(to_json(replace(vista, steps=(replace(primo, justification=nuova),) + vista.steps[1:])))
    esposta = corpo["steps"][0]["justification"]
    assert esposta["terminals"] == [{"kind": "node", "id": "0"}]
    assert esposta["preconditions"] == [" z ", "a"]
    assert esposta["certificate"]["checks"] == [" z ", "a"]
    assert esposta["certificate"]["attestations"] == [{"entity": {"kind": "component", "id": "V1"}, "changed": ["value", "type"]}]
    assert corpo["truth"]["product_verified"] is False


@pytest.mark.parametrize("id_esercizio", [
    "partitore-d1", "scala-due-riduzioni", "due-rami-parallelo", "ponte-nodale",
])
def test_k4_binding_per_identita_ordine_e_formula_della_run(id_esercizio, monkeypatch):
    """Completa l'oracolo iniziale con una fonte indipendente dalla cattura."""
    from dataclasses import asdict, replace
    from kirchhoff.domain.transform.catalog import preconditions_of
    import kirchhoff.pipeline.presentation as proiezione

    monkeypatch.syspath_prepend(str(RADICE / "scripts"))
    import generate_workbench as gen
    ex = next(e for e in gen.ESERCIZI if e.id == id_esercizio)
    chiusura, run = _chiusura_con_run(ex.netlist)
    attese = tuple(run.transform_executions)
    osservate = []
    componi_reale = proiezione.componi

    def cattura(esecuzione, *args, **kwargs):
        indice = len(osservate)
        osservate.append(esecuzione)
        assert indice < len(attese)
        assert esecuzione is attese[indice]
        visuale = componi_reale(esecuzione, *args, **kwargs)
        assert not isinstance(visuale, Failure)
        risultato = attese[indice].results[0]
        assert visuale.risultato is risultato
        g = visuale.giustificazione
        assert g.terminali is risultato.boundary.entities
        assert g.formula is risultato.equation
        assert g.certificato is risultato.certificate
        assert g.precondizioni is preconditions_of(risultato.certificate.operation)
        return visuale

    monkeypatch.setattr(proiezione, "componi", cattura)
    vista = proiezione.project_closed_session(
        chiusura.session, chiusura.registry, run,
        layout_iniziale=gen._disposizione(ex.disposizione, leggi(ex.netlist), 3, bytes(range(10, 20))),
        istante=1, casualita=bytes(range(10)))
    assert not isinstance(vista, Failure)
    assert len(osservate) == len(attese)
    assert all(osservate[i] is attese[i] for i in range(len(attese)))
    trasformazioni = [p for p in json.loads(to_json(vista))["steps"] if p["kind"] == "transform"]
    assert len(trasformazioni) == len(attese)
    for i, passo in enumerate(trasformazioni):
        r = attese[i].results[0]
        assert passo["justification"] == {
            "terminals": [asdict(e) for e in r.boundary.entities],
            "preconditions": list(preconditions_of(r.certificate.operation)),
            "formula": str(r.equation),
            "certificate": json.loads(json.dumps(asdict(r.certificate))),
        }
    if id_esercizio == "due-rami-parallelo":
        assert len(trasformazioni) == 1
        assert trasformazioni[0]["action"] == "parallelo"
        assert trasformazioni[0]["justification"]["terminals"] == [
            {"kind": "node", "id": "0"}, {"kind": "node", "id": "a"},
        ]
        assert trasformazioni[0]["justification"]["formula"] == "R1R2eq = R1·R2 / (R1 + R2)"
        assert vista.answer.exact == "12" and vista.answer.unit == "volt"
    if id_esercizio == "scala-due-riduzioni":
        # Controprova del binding gia' osservato RED per formula diversa:
        # scambiare due serie deve fallire anche con la medesima operazione.
        assert _ricostruisci(vista) == vista
        primi = [p for p in vista.steps if p.kind == "transform"]
        assert len(primi) == 2 and all(p.action == "serie" for p in primi)
        assert primi[0].justification.formula != primi[1].justification.formula
        assert primi[0].justification.terminals != primi[1].justification.terminals
        passi = list(vista.steps)
        passi[0] = replace(primi[0], justification=primi[1].justification)
        passi[1] = replace(primi[1], justification=primi[0].justification)
        with pytest.raises(ValueError, match="giustificazione: formula"):
            replace(vista, steps=tuple(passi))
