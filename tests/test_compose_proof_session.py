"""H2 — `compose_proof_session` e' una proiezione, non un secondo solutore.

Il compositore proietta run certificata + registro autorevole in sessione e
la pubblica tramite il validatore H1.5. Non pianifica, non esegue, non
trasforma, non certifica, non renderizza: la prova e' anche bianca
(`test_compositore_non_ricalcola_semantica`).

H2.5: il compositore e' l'unico writer che conia `sess_` da istante ed
entropia iniettati; il chiamante non fornisce mai un id gia' coniato.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.proof.session import ProofSession
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline import proof_session as compositore
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.proof_session import COMPOSER_ID, compose_proof_session
from kirchhoff.pipeline.state_registry import StateRef, componi_registro

D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

PONTE = """\
V1 b 0 12 volt
R1 b x 100 ohm
R2 x 0 200 ohm
R3 b y 300 ohm
R4 y 0 400 ohm
R5 x y 500 ohm
? current R5
"""

FUORI_CAPABILITY = """\
V1 b 0 12 volt
R1 b a 100 ohm
C1 a 0 1 farad
? current R1
"""

SHA_FIXTURE = "0123456789abcdef0123456789abcdef01234567"


def _stato(n: int) -> str:
    return conia("ir", 1700000000000 + n, bytes((n + 1,)) * 10)


def _istante(n: int) -> int:
    return 1700000000000 + n


def _entropia(n: int) -> bytes:
    return bytes((n + 101,)) * 10


def _run(netlist: str, offset: int = 0):
    ir = leggi(netlist)
    richiesta = next(iter(ir.requests))
    return orchestrate_didactic_run(
        ir, richiesta,
        state_ids=tuple(_stato(offset + i) for i in range(6)))


def _run_d1() -> CertifiedDidacticRun:
    esito = _run(D1)
    assert isinstance(esito, CertifiedDidacticRun)
    return esito


def _componi(run, n: int = 0):
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    return compose_proof_session(
        run, registro, session_instant_ms=_istante(n),
        session_entropy=_entropia(n), document_profile="student-pdf.v0.1",
        source_sha=SHA_FIXTURE, detail="fixture H2"), registro


# --- verde: D1 end-to-end (punto 30) --------------------------------------------------


def test_d1_composta_e_pubblicata():
    run = _run_d1()
    esito, _ = _componi(run, 0)
    assert isinstance(esito, ProofSession)
    assert esito.publication_status == "CLOSED"
    assert esito.final_claim is run.final_execution.claim
    assert esito.final_solution is run.final_execution.execution.resolved
    assert esito.session_id == conia("sess", _istante(0), _entropia(0))


def test_d1_e2e_riferimenti_risolti():
    run = _run_d1()
    esito, registro = _componi(run, 0)
    assert isinstance(esito, ProofSession)
    assert registro.resolve(StateRef(esito.initial_state_ref)) == run.initial_ir
    assert registro.resolve(StateRef(esito.final_state_ref)) == run.final_ir
    esecuzione = run.transform_executions[0]
    assert registro.resolve(StateRef(esito.steps[0].before_state_ref)) == esecuzione.before
    assert esito.steps[0].operation == "serie"
    assert esito.steps[0].effect.kind == "retarget"
    assert esito.steps[0].lineage.target_before == "R1"
    assert esito.steps[0].lineage.target_after == "R1R2eq"
    assert esito.final_request.target == "R1R2eq"
    nodale = run.final_execution.execution
    assert [(p.kind, p.derivation_before, p.derivation_after)
            for p in nodale.steps] == [
        ("choose_reference", "D0", "D1"),
        ("define_nodal_unknowns", "D1", "D2")]
    assert esito.final_derivation_id == nodale.derivation.identifier == "D2"
    assert nodale.resolved.value.amount == Fraction(3, 80)
    assert nodale.resolved.value.unit == "ampere"


def test_d1_evidenza_after_letterale_conservata():
    run = _run_d1()
    esito, registro = _componi(run, 0)
    assert isinstance(esito, ProofSession)
    esecuzione = run.transform_executions[0]
    assert registro.ref_for(esecuzione.after) is not None
    assert registro.resolve(registro.ref_for(esecuzione.after)) == esecuzione.after


def test_ponte_senza_trasformazioni_composto():
    esito_run = _run(PONTE)
    assert isinstance(esito_run, CertifiedDidacticRun)
    assert esito_run.transform_executions == ()
    esito, registro = _componi(esito_run, 5)
    assert isinstance(esito, ProofSession)
    assert len(esito.state_refs) == 1
    assert registro.resolve(StateRef(esito.final_state_ref)) == esito_run.final_ir


# --- il compositore non ricalcola semantica -------------------------------------------------


def test_compositore_non_ricalcola_semantica():
    sorgente = Path(compositore.__file__).read_text(encoding="utf-8")
    for chiamata in ("pianifica(", "transform(", "execute_plan(",
                     "certify_execution(", "truthfulness_gate(",
                     "solve_dc(", "solve_dc_tableau(", "verify(",
                     "orchestrate_didactic_run(", "render(", "deposita("):
        assert chiamata not in sorgente, chiamata


# --- matrice Failure (punto 29) ------------------------------------------------------------------


def test_refusal_all_ingresso_e_corruzione_del_chiamante():
    # Il compositore stretto non propaga Refusal: lo respinge come Failure.
    # La propagazione "rifiuto resta rifiuto" vive al confine di prodotto
    # (orchestrare -> se Refusal restituirlo senza comporre), provata in
    # test_proof_durable_authority.py::test_j_confine_prodotto_rifiuto_resta_rifiuto.
    esito_run = _run(FUORI_CAPABILITY)
    assert isinstance(esito_run, Refusal)
    registro = componi_registro(_run_d1(), refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        esito_run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="refusal in ingresso")
    assert type(esito) is Failure
    assert not isinstance(esito, (Refusal, ProofSession))


def test_run_di_tipo_sbagliato_fallisce():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        "non-una-run", registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="run sbagliata")
    assert type(esito) is Failure


def test_registro_di_tipo_sbagliato_fallisce():
    esito = compose_proof_session(
        _run_d1(), "non-un-registro", session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="registro sbagliato")
    assert type(esito) is Failure


def test_registro_vuoto_fallisce():
    from kirchhoff.pipeline.state_registry import CircuitStateRegistry

    esito = compose_proof_session(
        _run_d1(), CircuitStateRegistry(), session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="registro vuoto")
    assert isinstance(esito, Failure)
    assert "senza legame" in esito.messaggio


def test_registro_senza_evidenza_fallisce():
    from kirchhoff.pipeline.state_registry import (
        CircuitStateRegistry,
        StateBinding,
    )

    run = _run_d1()
    senza_evidenza = CircuitStateRegistry(tuple(
        StateBinding(StateRef(sid), stato)
        for sid, stato in zip(run.state_ids,
                              (run.initial_ir, run.final_ir), strict=True)))
    esito = compose_proof_session(
        run, senza_evidenza, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="senza evidenza")
    assert isinstance(esito, Failure)
    assert "evidenza" in esito.messaggio


def test_registro_con_valori_diversi_fallisce():
    from kirchhoff.pipeline.state_registry import (
        CircuitStateRegistry,
        StateBinding,
    )

    run = _run_d1()
    altra_ir = leggi(D1.replace("R2 a 0 220 ohm", "R2 a 0 221 ohm"))
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    evidenze = tuple(
        b for b in registro.bindings if b.ref.identifier not in run.state_ids)
    registrone = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[0]), altra_ir),
        StateBinding(StateRef(run.state_ids[1]), run.final_ir),
        *evidenze,
    ))
    esito = compose_proof_session(
        run, registrone, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="valori diversi")
    assert isinstance(esito, Failure)
    assert "non coincidono" in esito.messaggio


def test_registro_di_un_altra_run_fallisce():
    run = _run_d1()
    altra = _run(D1, offset=20)
    assert isinstance(altra, CertifiedDidacticRun)
    registro_altra = componi_registro(
        altra, refs_evidenza=(StateRef(_stato(29)),))
    esito = compose_proof_session(
        run, registro_altra, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="registro altrui")
    assert isinstance(esito, Failure)


def test_conio_sessione_malformato_fallisce():
    # H2.5: l'id non si inietta piu', si conia dentro. Istante/entropia
    # malformati diventano Failure di composizione, mai eccezione.
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=-1,
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="istante malformato")
    assert type(esito) is Failure
    assert not isinstance(esito, (Refusal, ProofSession))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(0),
        session_entropy=b"corta",
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="entropia malformata")
    assert type(esito) is Failure
    assert not isinstance(esito, (Refusal, ProofSession))


def test_document_profile_vuoto_fallisce():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="  ", source_sha=SHA_FIXTURE, detail="profilo vuoto")
    assert isinstance(esito, Failure)


def test_source_sha_malformato_fallisce():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha="zzz",
        detail="sha malformato")
    assert isinstance(esito, Failure)


def test_detail_vuoto_fallisce():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="   ")
    assert isinstance(esito, Failure)


def test_produttore_della_sessione_composta_e_il_compositore():
    run = _run_d1()
    esito, _ = _componi(run, 0)
    assert isinstance(esito, ProofSession)
    assert esito.provenance.producer == COMPOSER_ID
