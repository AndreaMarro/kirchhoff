"""Contratto della `ProofSession` canonica (H1 + H1.5): modello tipizzato.

H1.5: versioni solo autorevoli, provenance strutturata con SHA, session_id di
genere `sess_`, ordinamento v0.1 (trasformazioni poi analitica sul finale).
Ogni guardia ha un test che l'ha vista sollevare. Le fixture valide sono
proiettate da una `CertifiedDidacticRun` D1 reale.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.observation import ObservationEffect, RequestLineageStep
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
from kirchhoff.domain.didactic.orchestrate import orchestrate_didactic_run
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.proof.session import (
    SCHEMA_VERSION,
    AnalyticalProofStep,
    ProofSession,
    SessionProvenance,
    SessionVersions,
    TransformProofStep,
)
from kirchhoff.domain.truthfulness import VERIFIER_ID, VERIFIER_VERSION, Claim
from kirchhoff.pipeline.proof_session import COMPOSER_ID
from kirchhoff.pipeline.netlist import leggi

D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

SHA_FIXTURE = "0123456789abcdef0123456789abcdef01234567"


def _stato(n: int) -> str:
    """Un `ir_` vero, deterministico: stessa entropia, stesso identificatore."""
    return conia("ir", 1700000000000 + n, bytes((n + 1,)) * 10)


def _sessid(n: int) -> str:
    return conia("sess", 1700000000000 + n, bytes((n + 101,)) * 10)


def _versioni() -> SessionVersions:
    return SessionVersions(PLAN_SCHEMA_VERSION, PROFILE, "student-pdf.v0.1")


def _provenienza() -> SessionProvenance:
    return SessionProvenance(COMPOSER_ID, SHA_FIXTURE, "run D1, fixture H1")


def _run_d1() -> CertifiedDidacticRun:
    ir = leggi(D1)
    richiesta = next(iter(ir.requests))
    esito = orchestrate_didactic_run(
        ir, richiesta, state_ids=(_stato(0), _stato(1), _stato(2)))
    assert isinstance(esito, CertifiedDidacticRun)
    return esito


def _kwargs_d1() -> dict:
    run = _run_d1()
    trasformazione = run.transform_executions[0]
    nodale = run.final_execution.execution
    analitici = tuple(
        AnalyticalProofStep(
            i + 1, run.state_ids[-1],
            passo.kind, passo.derivation_before, passo.derivation_after)
        for i, passo in enumerate(nodale.steps))
    passi = (
        TransformProofStep(
            0, run.state_ids[0], run.state_ids[1],
            trasformazione.plan.actions[0].kind,
            trasformazione.observation_effect, trasformazione.request_lineage),
        *analitici)
    return {
        "session_id": _sessid(0),
        "schema_version": SCHEMA_VERSION,
        "versions": _versioni(),
        "provenance": _provenienza(),
        "original_request": run.original_request,
        "initial_state_ref": run.state_ids[0],
        "state_refs": tuple(run.state_ids),
        "steps": passi,
        "final_derivation_id": nodale.derivation.identifier,
        "final_request": run.final_request,
        "final_state_ref": run.state_ids[-1],
        "final_claim": run.final_execution.claim,
    }


def _kwargs_ponte() -> dict:
    """Sessione a zero trasformazioni (forma D7): un solo stato, solo analitica."""
    rif = _stato(7)
    domanda = Request("q9", "voltage", "R1")
    return {
        "session_id": _sessid(7),
        "schema_version": SCHEMA_VERSION,
        "versions": _versioni(),
        "provenance": _provenienza(),
        "original_request": domanda,
        "initial_state_ref": rif,
        "state_refs": (rif,),
        "steps": (AnalyticalProofStep(0, rif, "write_kcl", "D0", "D1"),),
        "final_derivation_id": "D1",
        "final_request": domanda,
        "final_state_ref": rif,
        "final_claim": Claim(
            "resolved_quantity", rif, ("q9", "R1"), ("D1",),
            VERIFIER_ID, VERIFIER_VERSION),
    }


# --- versioni: solo autorita' -------------------------------------------------


def test_versioni_autorevoli_valide():
    versioni = _versioni()
    assert versioni.planner_schema_version == PLAN_SCHEMA_VERSION
    assert versioni.curriculum_profile == PROFILE


def test_planner_schema_non_autorevole_rifiutato():
    with pytest.raises(ValueError, match="planner"):
        replace(_versioni(), planner_schema_version="didactic-plan.v9.9")


def test_profilo_non_autorevole_rifiutato():
    with pytest.raises(ValueError, match="curriculum"):
        replace(_versioni(), curriculum_profile="universita-reale-v1")


def test_document_profile_vuoto_rifiutato():
    with pytest.raises(ValueError, match="document"):
        replace(_versioni(), document_profile="   ")


def test_document_profile_non_stringa_rifiutato():
    with pytest.raises(ValueError, match="document"):
        replace(_versioni(), document_profile=None)


# --- provenienza strutturata ---------------------------------------------------


def test_provenienza_valida():
    provenienza = _provenienza()
    assert provenienza.producer == COMPOSER_ID
    assert len(provenienza.source_sha) == 40


def test_produttore_vuoto_rifiutato():
    with pytest.raises(ValueError, match="produttore"):
        replace(_provenienza(), producer="")


def test_produttore_non_stringa_rifiutato():
    with pytest.raises(ValueError, match="produttore"):
        replace(_provenienza(), producer=123)


def test_sha_malformato_rifiutato():
    with pytest.raises(ValueError, match="sha"):
        replace(_provenienza(), source_sha="non-uno-sha")


def test_sha_non_stringa_rifiutato():
    with pytest.raises(ValueError, match="sha"):
        replace(_provenienza(), source_sha=None)


def test_dettaglio_vuoto_rifiutato():
    with pytest.raises(ValueError, match="dettaglio"):
        replace(_provenienza(), detail="  ")


def test_dettaglio_non_stringa_rifiutato():
    with pytest.raises(ValueError, match="dettaglio"):
        replace(_provenienza(), detail=None)


# --- identita' di sessione --------------------------------------------------------


def test_session_id_sess_valido():
    sessione = ProofSession(**_kwargs_d1())
    assert sessione.session_id.startswith("sess_")


def test_session_id_narrativo_rifiutato():
    with pytest.raises(ValueError, match="sess"):
        ProofSession(**{**_kwargs_d1(), "session_id": "sessione-d1-prova-001"})


def test_session_id_di_genere_sbagliato_rifiutato():
    with pytest.raises(ValueError, match="sess"):
        ProofSession(**{**_kwargs_d1(), "session_id": _stato(0)})


def test_session_id_non_stringa_rifiutato():
    with pytest.raises(TypeError, match="invece di str"):
        ProofSession(**{**_kwargs_d1(), "session_id": 7})


# --- passo topologico --------------------------------------------------------


def _trasformazione_d1() -> TransformProofStep:
    return _kwargs_d1()["steps"][0]


def test_passo_topologico_valido():
    passo = _trasformazione_d1()
    assert passo.operation == "serie"
    assert passo.effect.kind == "retarget"


def test_indice_topologico_non_intero_rifiutato():
    with pytest.raises(TypeError):
        replace(_trasformazione_d1(), index="0")


def test_indice_topologico_bool_rifiutato():
    with pytest.raises(TypeError):
        replace(_trasformazione_d1(), index=True)


def test_indice_topologico_negativo_rifiutato():
    with pytest.raises(ValueError):
        replace(_trasformazione_d1(), index=-1)


def test_passo_topologico_sullo_stesso_stato_rifiutato():
    passo = _trasformazione_d1()
    with pytest.raises(ValueError):
        replace(passo, after_state_ref=passo.before_state_ref)


def test_operazione_fuori_catalogo_rifiutata():
    with pytest.raises(ValueError):
        replace(_trasformazione_d1(), operation="thevenin")


def test_effetto_non_observation_rifiutato():
    with pytest.raises(TypeError):
        replace(_trasformazione_d1(), effect="retarget")


def test_effetto_blocked_rifiutato_nella_sessione():
    passo = _trasformazione_d1()
    bloccato = ObservationEffect("blocked", None, "tensione sul ramo coinvolto")
    with pytest.raises(ValueError):
        replace(passo, effect=bloccato)


def test_lineage_non_requestlineage_rifiutata():
    with pytest.raises(TypeError):
        replace(_trasformazione_d1(), lineage={"a": 1})


def test_lineage_su_altra_operazione_rifiutata():
    passo = _trasformazione_d1()
    with pytest.raises(ValueError):
        replace(passo, lineage=replace(passo.lineage, operation="parallelo"))


def test_lineage_con_effetto_diverso_rifiutata():
    passo = _trasformazione_d1()
    with pytest.raises(ValueError):
        replace(passo, lineage=replace(passo.lineage, effect="identity"))


def test_target_fra_effetto_e_lineage_divergenti_rifiutato():
    passo = _trasformazione_d1()
    with pytest.raises(ValueError):
        replace(
            passo, effect=replace(passo.effect, target_after="R1R2ALTRO"))


# --- passo analitico ----------------------------------------------------------


def _analitico_d1() -> AnalyticalProofStep:
    return _kwargs_d1()["steps"][1]


def test_passo_analitico_valido():
    passo = _analitico_d1()
    assert passo.derivation_before == "D0"


def test_indice_analitico_non_intero_rifiutato():
    with pytest.raises(TypeError):
        replace(_analitico_d1(), index="1")


def test_indice_analitico_bool_rifiutato():
    with pytest.raises(TypeError):
        replace(_analitico_d1(), index=False)


def test_indice_analitico_negativo_rifiutato():
    with pytest.raises(ValueError):
        replace(_analitico_d1(), index=-2)


def test_kind_analitico_sconosciuto_rifiutato():
    with pytest.raises(ValueError):
        replace(_analitico_d1(), kind="create_supernode")


def test_derivation_before_non_str_rifiutata():
    with pytest.raises(TypeError):
        replace(_analitico_d1(), derivation_before=5)


def test_derivation_before_vuota_rifiutata():
    with pytest.raises(ValueError):
        replace(_analitico_d1(), derivation_before="")


def test_derivation_after_non_str_rifiutata():
    with pytest.raises(TypeError):
        replace(_analitico_d1(), derivation_after=9)


def test_derivation_after_vuota_rifiutata():
    with pytest.raises(ValueError):
        replace(_analitico_d1(), derivation_after="")


def test_derivazione_ferma_rifiutata():
    with pytest.raises(ValueError):
        replace(_analitico_d1(), derivation_after="D0")


# --- sessione verde ------------------------------------------------------------


def test_sessione_d1_valida():
    sessione = ProofSession(**_kwargs_d1())
    assert len(sessione.state_refs) == 2
    assert len(sessione.steps) == 3
    assert sessione.final_claim.status == "VERIFIED"
    assert sessione.publication_status == "VERIFIED"
    assert sessione.final_derivation_id == "D2"
    assert sessione.final_claim.evidence_ids == ("D1", "D2")
    topologici = [p for p in sessione.steps if isinstance(p, TransformProofStep)]
    analitici = [p for p in sessione.steps if isinstance(p, AnalyticalProofStep)]
    assert [p.index for p in topologici] == [0]
    assert all(p.state_ref == sessione.final_state_ref for p in analitici)


def test_sessione_ponte_senza_trasformazioni_valida():
    sessione = ProofSession(**_kwargs_ponte())
    assert sessione.state_refs == (sessione.initial_state_ref,)
    assert len(sessione.steps) == 1
    assert sessione.final_request == sessione.original_request


def test_liste_come_ingressi_vengono_congelate():
    kwargs = _kwargs_d1()
    kwargs["state_refs"] = list(kwargs["state_refs"])
    kwargs["steps"] = list(kwargs["steps"])
    sessione = ProofSession(**kwargs)
    assert isinstance(sessione.state_refs, tuple)
    assert isinstance(sessione.steps, tuple)


def test_sessione_congelata():
    sessione = ProofSession(**_kwargs_d1())
    with pytest.raises(FrozenInstanceError):
        sessione.session_id = "sess_altra"  # type: ignore[misc]


# --- ordinamento v0.1 -------------------------------------------------------------


def test_trasformazione_dopo_analitica_rifiutata():
    kwargs = _kwargs_d1()
    disordinati = (kwargs["steps"][1], kwargs["steps"][2], kwargs["steps"][0])
    rinumerati = tuple(replace(p, index=i) for i, p in enumerate(disordinati))
    with pytest.raises(ValueError, match="dopo un passo analitico"):
        ProofSession(**{**kwargs, "steps": rinumerati})


def test_analitico_sullo_stato_vecchio_rifiutato():
    kwargs = _kwargs_d1()
    passi = (kwargs["steps"][0],
             replace(kwargs["steps"][1], state_ref=kwargs["state_refs"][0]),
             kwargs["steps"][2])
    with pytest.raises(ValueError, match="finale"):
        ProofSession(**{**kwargs, "steps": passi})


# --- sessione rossa: busta ------------------------------------------------------


def test_schema_sconosciuto_rifiutato():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "schema_version": "proof-session.v9.9"})


def test_versions_non_sessionversions_rifiutate():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "versions": {"planner": "x"}})


def test_provenance_non_sessionprovenance_rifiutata():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "provenance": "prodotta-qui"})


def test_original_non_request_rifiutata():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "original_request": "q1"})


def test_final_non_request_rifiutata():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "final_request": None})


def test_final_con_id_diverso_rifiutata():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs, "final_request": replace(kwargs["final_request"], id="q2")})


def test_final_con_quantity_diversa_rifiutata():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_request": replace(kwargs["final_request"], quantity="voltage")})


def test_final_derivation_non_str_rifiutata():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "final_derivation_id": 2})


def test_final_derivation_vuota_rifiutata():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "final_derivation_id": ""})


def test_state_refs_vuoti_rifiutati():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "state_refs": ()})


def test_state_refs_duplicati_rifiutati():
    kwargs = _kwargs_d1()
    duplicati = (kwargs["state_refs"][0], kwargs["state_refs"][0])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "state_refs": duplicati})


def test_primo_ref_non_iniziale_rifiutato():
    kwargs = _kwargs_d1()
    invertiti = (kwargs["state_refs"][1], kwargs["state_refs"][0])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "state_refs": invertiti})


def test_final_non_ultimo_stato_rifiutato():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "final_state_ref": _stato(5)})


def test_passo_di_tipo_sconosciuto_rifiutato():
    kwargs = _kwargs_d1()
    with pytest.raises(TypeError):
        ProofSession(**{**kwargs, "steps": ("non-un-passo", *kwargs["steps"])})


def test_indici_non_consecutivi_rifiutati():
    kwargs = _kwargs_d1()
    passi = (kwargs["steps"][0], replace(kwargs["steps"][1], index=7),
             kwargs["steps"][2])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_conteggio_topologico_contro_stati_rifiutato():
    kwargs = _kwargs_d1()
    rinumerati = tuple(
        replace(passo, index=i) for i, passo in enumerate(kwargs["steps"][1:]))
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": rinumerati})


def test_mappatura_stati_errata_rifiutata():
    kwargs = _kwargs_d1()
    passo = kwargs["steps"][0]
    scambiato = replace(
        passo, before_state_ref=passo.after_state_ref,
        after_state_ref=passo.before_state_ref)
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": (scambiato, *kwargs["steps"][1:])})


# --- sessione rossa: lineage -----------------------------------------------------


def test_lineage_su_altra_request_rifiutata():
    kwargs = _kwargs_d1()
    passo = kwargs["steps"][0]
    lineage = replace(passo.lineage, request_id="q2")
    passi = (replace(passo, lineage=lineage), *kwargs["steps"][1:])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_lineage_su_altra_quantity_rifiutata():
    kwargs = _kwargs_d1()
    passo = kwargs["steps"][0]
    lineage = replace(passo.lineage, quantity="voltage")
    passi = (replace(passo, lineage=lineage), *kwargs["steps"][1:])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_lineage_discontinua_rifiutata():
    kwargs = _kwargs_d1()
    passo = kwargs["steps"][0]
    lineage = replace(passo.lineage, target_before="R9")
    passi = (replace(passo, lineage=lineage), *kwargs["steps"][1:])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_final_fuori_lineage_rifiutata():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_request": replace(kwargs["final_request"], target="R9")})


def test_ponte_con_final_diversa_rifiutato():
    kwargs = _kwargs_ponte()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_request": replace(kwargs["final_request"], target="R2")})


# --- sessione rossa: analitica e claim --------------------------------------------


def test_senza_analitici_rifiutata():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": kwargs["steps"][:1]})


def test_derivazione_non_parte_da_d0_rifiutata():
    kwargs = _kwargs_d1()
    passi = (kwargs["steps"][0], replace(kwargs["steps"][1],
                                        derivation_before="D5",
                                        derivation_after="D6"),
             kwargs["steps"][2])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_catena_di_derivazione_spezzata_rifiutata():
    kwargs = _kwargs_d1()
    passi = (kwargs["steps"][0], kwargs["steps"][1],
             replace(kwargs["steps"][2], derivation_before="D9"))
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_analitico_su_stato_estraneo_rifiutato():
    kwargs = _kwargs_d1()
    passi = (kwargs["steps"][0], replace(kwargs["steps"][1], state_ref=_stato(9)),
             kwargs["steps"][2])
    with pytest.raises(ValueError):
        ProofSession(**{**kwargs, "steps": passi})


def test_final_derivation_non_coincide_rifiutata():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "final_derivation_id": "D9"})


def test_final_claim_non_claim_rifiutato():
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs_d1(), "final_claim": "VERIFIED"})


def test_claim_su_altro_stato_rifiutato():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_claim": replace(kwargs["final_claim"], state_id=_stato(8))})


def test_claim_su_altro_subject_rifiutato():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_claim": replace(
                kwargs["final_claim"], subject_ids=("q1", "R9"))})


def test_evidenze_non_coincidenti_rifiutate():
    kwargs = _kwargs_d1()
    with pytest.raises(ValueError):
        ProofSession(**{
            **kwargs,
            "final_claim": replace(kwargs["final_claim"], evidence_ids=("D1",))})


def test_publication_status_sconosciuto_rifiutato():
    with pytest.raises(ValueError):
        ProofSession(**{**_kwargs_d1(), "publication_status": "DRAFT"})


def test_lineage_blocked_costruibile_ma_mai_in_sessione():
    """Il vocabolario blocked esiste; la sessione lo respinge (vedi sopra)."""
    lineage = RequestLineageStep("q1", "current", "R1", None, "serie", "blocked")
    assert lineage.target_after is None
