"""H2.5 — l'autorita' di pubblicazione deve sopravvivere alla persistenza.

Ipotesi: oggi `validate_publication` lega la sessione alla run viva con
l'identita' Python (`is`) su effetto, lineage e Claim, e la sessione non
porta la soluzione finale. Dopo serialize -> exit -> deserialize gli oggetti
non sono piu' gli stessi: l'autorita' `is` muore col processo e la risposta
3/80 A e' irraggiungibile senza la run viva.

Questi test definiscono il contratto durevole PRIMA dell'implementazione:

- A: la copia persistita (uguale ma non identica) fallisce sul validatore
  live e passa sul validatore durevole;
- B: la soluzione finale esatta e' raggiungibile dalla sola sessione;
- C: la verifica (Claim autorevole + catena di derivazione) e' raggiungibile
  dalla sola sessione;
- D: un Claim forgiato fallisce senza `is` (pin del verificatore);
- E: la catena di derivazione e' citata in modo ancorato al Claim;
- F: lo SHA di provenienza e' metadato dichiarato, non revisione verificata;
- G: il profilo documento e' un token chiuso, non una stringa qualsiasi;
- H: il compositore e' l'unico writer che conia `sess_`;
- I: VERIFIED di backend non pretende la chiusura visuale (K-0/AD-5, H5);
- J: al confine di prodotto un Refusal resta Refusal;
- K: la ricostruzione fresca (zero identita' originali) valida sul durevole.

Decisione di riferimento: docs/decisions/2026-09-03-proofsession-serialization-readiness.md
"""

from __future__ import annotations

import copy
import inspect
from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Magnitude
from kirchhoff.domain.proof.session import (
    DOCUMENT_PROFILE,
    SCHEMA_VERSION,
    ProofSession,
    SessionProvenance,
    SessionVersions,
)
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import VERIFIER_ID, VERIFIER_VERSION
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.proof_session import (
    COMPOSER_ID,
    compose_proof_session,
    validate_persisted_publication,
    validate_publication,
)
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


def _sessid_atteso(n: int) -> str:
    return conia("sess", _istante(n), _entropia(n))


def _run(netlist: str, offset: int = 0, n_stati: int = 6):
    ir = leggi(netlist)
    richiesta = next(iter(ir.requests))
    return orchestrate_didactic_run(
        ir, richiesta,
        state_ids=tuple(_stato(offset + i) for i in range(n_stati)))


def _run_d1() -> CertifiedDidacticRun:
    esito = _run(D1)
    assert isinstance(esito, CertifiedDidacticRun)
    return esito


def _componi(run: CertifiedDidacticRun, n: int = 0):
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(n),
        session_entropy=_entropia(n), document_profile=DOCUMENT_PROFILE,
        source_sha=SHA_FIXTURE, detail="fixture H2.5")
    assert isinstance(esito, ProofSession)
    return esito, run, registro


# --- A: il confine di persistenza rompe `is`, non il contenuto -----------------


def test_a_copia_persistita_fallisce_sul_validatore_live():
    sessione, run, registro = _componi(_run_d1())
    copia = copy.deepcopy(sessione)
    assert copia == sessione
    assert copia.final_claim is not run.final_execution.claim
    esito = validate_publication(copia, run, registro)
    assert isinstance(esito, Failure)


def test_a_copia_persistita_passa_sul_validatore_durevole():
    sessione, _, registro = _componi(_run_d1())
    copia = copy.deepcopy(sessione)
    esito = validate_persisted_publication(copia, registro)
    assert esito is copia


# --- B: la soluzione finale e' raggiungibile senza la run viva -----------------


def test_b_soluzione_finale_esatta_senza_run():
    sessione, _, registro = _componi(_run_d1())
    # Niente accesso alla run da qui in poi: solo sessione + registro.
    esito = validate_persisted_publication(sessione, registro)
    assert isinstance(esito, ProofSession)
    assert esito.final_solution.value.amount == Fraction(3, 80)
    assert esito.final_solution.value.unit == "ampere"
    assert esito.final_solution.target == esito.final_request.target == "R1R2eq"
    assert esito.final_solution.quantity == esito.final_request.quantity == "current"


def test_b_compositore_proietta_la_quantita_risolta():
    run = _run_d1()
    sessione, _, _ = _componi(run)
    assert sessione.final_solution is run.final_execution.execution.resolved


def test_b_soluzione_manomessa_non_pubblica_sul_live():
    sessione, run, registro = _componi(_run_d1())
    manomessa = replace(
        sessione,
        final_solution=replace(
            sessione.final_solution,
            value=Magnitude(Fraction(1, 2), "ampere")))
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "soluzione" in esito.messaggio


def test_b_soluzione_incoerente_rifiutata_dal_modello():
    sessione, _, _ = _componi(_run_d1())
    with pytest.raises(ValueError, match="derivazione"):
        replace(sessione, final_solution=replace(
            sessione.final_solution, derivation_id="D9"))
    with pytest.raises(ValueError, match="final_request"):
        replace(sessione, final_solution=replace(
            sessione.final_solution, target="R9"))
    with pytest.raises(TypeError, match="ResolvedQuantity"):
        replace(sessione, final_solution="3/80 A")


# --- C/D: verifica durevole senza `is` ------------------------------------------


def test_c_claim_autorevole_raggiungibile_senza_run():
    sessione, _, registro = _componi(_run_d1())
    assert validate_persisted_publication(sessione, registro) is sessione
    assert sessione.final_claim.verifier_id == VERIFIER_ID
    assert sessione.final_claim.verifier_version == VERIFIER_VERSION
    assert sessione.final_claim.status == "VERIFIED"
    assert sessione.final_claim.state_id == sessione.final_state_ref


def test_d_verifier_non_autorevole_rifiutato_senza_is():
    sessione, _, _ = _componi(_run_d1())
    with pytest.raises(ValueError, match="verifier_id"):
        replace(sessione, final_claim=replace(
            sessione.final_claim, verifier_id="io-a-mano"))
    with pytest.raises(ValueError, match="verifier_version"):
        replace(sessione, final_claim=replace(
            sessione.final_claim, verifier_version="9.9.9"))


def test_d_claim_uguale_ma_non_autorevole_resta_respinto_al_live():
    # Il live conserva il tie `is` come sanity check di composizione;
    # il durevole accetta il contenuto identico (identita' di contenuto).
    sessione, run, registro = _componi(_run_d1())
    gemello = replace(run.final_execution.claim)
    assert gemello == run.final_execution.claim
    assert gemello is not run.final_execution.claim
    manomessa = replace(sessione, final_claim=gemello)
    assert isinstance(validate_publication(manomessa, run, registro), Failure)
    assert validate_persisted_publication(manomessa, registro) is manomessa


# --- E: derivazione ancorata -----------------------------------------------------


def test_e_catena_derivazione_ancorata_al_claim_senza_run():
    from kirchhoff.domain.proof.session import AnalyticalProofStep

    sessione, _, registro = _componi(_run_d1())
    assert validate_persisted_publication(sessione, registro) is sessione
    analitici = [p for p in sessione.steps if isinstance(p, AnalyticalProofStep)]
    assert analitici[0].derivation_before == "D0"
    assert tuple(p.derivation_after for p in analitici) == (
        sessione.final_claim.evidence_ids)
    assert analitici[-1].derivation_after == sessione.final_derivation_id
    assert sessione.final_solution.derivation_id == sessione.final_derivation_id


# --- F: provenienza dichiarata ----------------------------------------------------


def test_f_sha_sintetico_vale_come_provenienza_dichiarata():
    # Il campo e' metadato dichiarato dal produttore (forma SHA-40), non
    # revisione di checkout verificata: la radice di composizione dovra'
    # legarlo ai metadati reali di build. Il test inchioda il confine.
    provenienza = SessionProvenance(COMPOSER_ID, SHA_FIXTURE, "fixture H2.5")
    assert provenienza.source_sha == SHA_FIXTURE


# --- G: profilo documento chiuso ----------------------------------------------------


def test_g_profilo_arbitrario_rifiutato():
    with pytest.raises(ValueError, match="document_profile"):
        SessionVersions(PLAN_SCHEMA_VERSION, PROFILE, "banana")
    assert DOCUMENT_PROFILE == "student-pdf.v0.1"


def test_g_profilo_arbitrario_al_compositore_fallisce():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito = compose_proof_session(
        run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0), document_profile="banana",
        source_sha=SHA_FIXTURE, detail="profilo arbitrario")
    assert type(esito) is Failure


# --- H: un solo writer per `sess_` ----------------------------------------------------


def test_h_compositore_unico_writer_di_sess():
    firma = inspect.signature(compose_proof_session)
    assert "session_id" not in firma.parameters
    assert "session_instant_ms" in firma.parameters
    assert "session_entropy" in firma.parameters
    run = _run_d1()
    prima, _, _ = _componi(run, n=0)
    assert prima.session_id == _sessid_atteso(0)
    # Stessi ingressi -> stesso identificatore (purezza, replay riproducibile).
    bis, _, _ = _componi(_run_d1(), n=0)
    assert bis.session_id == prima.session_id
    # Entropia diversa -> occurrence diversa.
    altra, _, _ = _componi(run, n=1)
    assert altra.session_id != prima.session_id


def test_h_istante_entropia_malformati_falliscono():
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    for istante in ("ora", True, -1, 1 << 48):
        esito = compose_proof_session(
            run, registro, session_instant_ms=istante,
            session_entropy=_entropia(0), document_profile=DOCUMENT_PROFILE,
            source_sha=SHA_FIXTURE, detail="istante malformato")
        assert type(esito) is Failure, istante
    for entropia in ("casuale", b"corta", bytes(11)):
        esito = compose_proof_session(
            run, registro, session_instant_ms=_istante(0),
            session_entropy=entropia, document_profile=DOCUMENT_PROFILE,
            source_sha=SHA_FIXTURE, detail="entropia malformata")
        assert type(esito) is Failure, entropia


# --- I: VERIFIED di backend non pretende la chiusura visuale --------------------------


def test_i_sessione_backend_senza_chiusura_visuale():
    # K-0/AD-5: il badge prodotto richiede anche il round-trip visuale (H5).
    # Lo schema v0.1 non porta ProofGraph/layout/view: il suo VERIFIED e'
    # chiusura di pubblicazione di backend (integrita' referenziale +
    # Claim elettrico), non il badge prodotto. Il test inchioda il confine.
    sessione, _, registro = _componi(_run_d1())
    assert sessione.publication_status == "VERIFIED"
    assert validate_persisted_publication(sessione, registro) is sessione
    for campo in ("proof_graph_ref", "layout_ref", "view_ref",
                  "didactic_plan_ref", "content_hash"):
        assert not hasattr(sessione, campo), campo


# --- J: il confine di prodotto propaga il Refusal ----------------------------------------


def test_j_confine_prodotto_rifiuto_resta_rifiuto():
    def confine(netlist: str):
        ir = leggi(netlist)
        richiesta = next(iter(ir.requests))
        esito_run = orchestrate_didactic_run(
            ir, richiesta,
            state_ids=tuple(_stato(i) for i in range(6)))
        if isinstance(esito_run, Refusal):
            return esito_run
        assert isinstance(esito_run, CertifiedDidacticRun)
        registro = componi_registro(
            esito_run, refs_evidenza=(StateRef(_stato(9)),))
        return compose_proof_session(
            esito_run, registro, session_instant_ms=_istante(0),
            session_entropy=_entropia(0), document_profile=DOCUMENT_PROFILE,
            source_sha=SHA_FIXTURE, detail="confine di prodotto")

    rifiuto = confine(FUORI_CAPABILITY)
    assert type(rifiuto) is Refusal
    assert not isinstance(rifiuto, (Failure, ProofSession))
    verde = confine(D1)
    assert isinstance(verde, ProofSession)


def test_j_refusal_all_ingresso_del_compositore_e_corruzione():
    # Il compositore stretto mappa il Refusal in Failure; la propagazione
    # Refusal vive al confine sopra (test_j_confine...), mai dentro.
    run = _run_d1()
    registro = componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))
    esito_run = _run(FUORI_CAPABILITY)
    assert isinstance(esito_run, Refusal)
    esito = compose_proof_session(
        esito_run, registro, session_instant_ms=_istante(0),
        session_entropy=_entropia(0), document_profile=DOCUMENT_PROFILE,
        source_sha=SHA_FIXTURE, detail="refusal in ingresso")
    assert type(esito) is Failure
    assert not isinstance(esito, (Refusal, ProofSession))


# --- K: ricostruzione fresca --------------------------------------------------------------


def test_k_ricostruzione_fresca_valida_solo_sul_durevole():
    from kirchhoff.domain.proof.session import (
        AnalyticalProofStep,
        TransformProofStep,
    )

    sessione, run, registro = _componi(_run_d1())
    passi = tuple(
        replace(p, effect=replace(p.effect), lineage=replace(p.lineage))
        if isinstance(p, TransformProofStep)
        else replace(p)
        for p in sessione.steps)
    assert all(nuovo is not vecchio for nuovo, vecchio in zip(passi, sessione.steps))
    fresca = ProofSession(
        session_id=sessione.session_id,
        schema_version=sessione.schema_version,
        versions=replace(sessione.versions),
        provenance=replace(sessione.provenance),
        original_request=replace(sessione.original_request),
        initial_state_ref=sessione.initial_state_ref,
        state_refs=tuple(sessione.state_refs),
        steps=passi,
        final_derivation_id=sessione.final_derivation_id,
        final_request=replace(sessione.final_request),
        final_state_ref=sessione.final_state_ref,
        final_solution=replace(sessione.final_solution),
        final_claim=replace(sessione.final_claim),
        publication_status=sessione.publication_status,
    )
    assert fresca == sessione
    assert fresca.final_claim is not run.final_execution.claim
    assert isinstance(validate_publication(fresca, run, registro), Failure)
    assert validate_persisted_publication(fresca, registro) is fresca


def test_k_ponte_zero_trasformazioni_valida_sul_durevole():
    esito_run = _run(PONTE)
    assert isinstance(esito_run, CertifiedDidacticRun)
    assert esito_run.transform_executions == ()
    registro = componi_registro(esito_run)
    esito = compose_proof_session(
        esito_run, registro, session_instant_ms=_istante(5),
        session_entropy=_entropia(5), document_profile=DOCUMENT_PROFILE,
        source_sha=SHA_FIXTURE, detail="ponte H2.5")
    assert isinstance(esito, ProofSession)
    copia = copy.deepcopy(esito)
    assert validate_persisted_publication(copia, registro) is copia


# --- validatore durevole: fallimenti chiusi -------------------------------------------


def test_durevole_tipi_sbagliati_falliscono_chiusi():
    sessione, _, registro = _componi(_run_d1())
    assert type(validate_persisted_publication(
        "non-una-sessione", registro)) is Failure
    assert type(validate_persisted_publication(
        sessione, "non-un-registro")) is Failure
    esito = validate_persisted_publication(sessione, "non-un-registro")
    assert not isinstance(esito, Refusal)


def test_durevole_produttore_non_autorevole_fallisce():
    sessione, _, registro = _componi(_run_d1())
    manomessa = replace(
        sessione, provenance=replace(sessione.provenance, producer="io-a-mano"))
    esito = validate_persisted_publication(manomessa, registro)
    assert isinstance(esito, Failure)
    assert "compositore autorevole" in esito.messaggio


def test_durevole_ref_pendente_fallisce():
    from kirchhoff.pipeline.state_registry import (
        CircuitStateRegistry,
        StateBinding,
    )

    sessione, run, _ = _componi(_run_d1())
    dimezzato = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[0]), run.initial_ir),))
    esito = validate_persisted_publication(sessione, dimezzato)
    assert isinstance(esito, Failure)
    assert "senza legame" in esito.messaggio
