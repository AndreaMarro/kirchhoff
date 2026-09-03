"""H1.5 — la pubblicazione chiude la catena fino all'evidenza autorevole.

Ipotesi: una sessione costruibile non e' ancora pubblicabile. Questi test
provano il validatore `validate_publication`, non il solo costruttore: ogni
RED arriva al validatore con una sessione che il modello accetta e chiede
`Failure` tipizzato (mai `Refusal`, mai eccezione inghiottita).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.proof.session import (
    SCHEMA_VERSION,
    AnalyticalProofStep,
    ProofSession,
    SessionProvenance,
    SessionVersions,
    TransformProofStep,
)
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import VERIFIER_ID, VERIFIER_VERSION, Claim
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.proof_session import (
    COMPOSER_ID,
    validate_publication,
)
from kirchhoff.pipeline.state_registry import (
    CircuitStateRegistry,
    StateBinding,
    StateRef,
    componi_registro,
)

D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

SHA_FIXTURE = "0123456789abcdef0123456789abcdef01234567"


def _stato(n: int) -> str:
    return conia("ir", 1700000000000 + n, bytes((n + 1,)) * 10)


def _sessid(n: int) -> str:
    return conia("sess", 1700000000000 + n, bytes((n + 101,)) * 10)


def _versioni() -> SessionVersions:
    return SessionVersions(PLAN_SCHEMA_VERSION, PROFILE, "student-pdf.v0.1")


def _provenienza() -> SessionProvenance:
    return SessionProvenance(COMPOSER_ID, SHA_FIXTURE, "run D1, fixture H1.5")


def _run_d1(offset: int = 0) -> CertifiedDidacticRun:
    from kirchhoff.pipeline.netlist import leggi

    ir = leggi(D1)
    richiesta = next(iter(ir.requests))
    esito = orchestrate_didactic_run(
        ir, richiesta,
        state_ids=(_stato(offset), _stato(offset + 1), _stato(offset + 2)))
    assert isinstance(esito, CertifiedDidacticRun)
    return esito


def _registro(run: CertifiedDidacticRun) -> CircuitStateRegistry:
    return componi_registro(run, refs_evidenza=(StateRef(_stato(9)),))


def _kwargs(run: CertifiedDidacticRun, sid: str) -> dict:
    trasformazione = run.transform_executions[0]
    nodale = run.final_execution.execution
    passi = (
        TransformProofStep(
            0, run.state_ids[0], run.state_ids[1],
            trasformazione.plan.actions[0].kind,
            trasformazione.observation_effect, trasformazione.request_lineage),
        *(AnalyticalProofStep(
            i + 1, run.state_ids[-1],
            passo.kind, passo.derivation_before, passo.derivation_after)
            for i, passo in enumerate(nodale.steps)),
    )
    return {
        "session_id": sid,
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
        "final_solution": nodale.resolved,
        "final_claim": run.final_execution.claim,
    }


def _pubblicazione_valida() -> tuple[ProofSession, CertifiedDidacticRun,
                                     CircuitStateRegistry]:
    run = _run_d1()
    registro = _registro(run)
    sessione = ProofSession(**_kwargs(run, _sessid(0)))
    return sessione, run, registro


# --- superficie di import (§20): il percorso pubblico si importa ----------------


def test_superficie_pubblica_si_importa():
    import kirchhoff.domain.proof.session as modello
    import kirchhoff.pipeline.proof_session as pubblicazione

    assert callable(pubblicazione.validate_publication)
    assert modello.ProofSession is ProofSession


# --- verde: la catena si chiude ---------------------------------------------------


def test_pubblicazione_valida_restituisce_la_sessione():
    sessione, run, registro = _pubblicazione_valida()
    esito = validate_publication(sessione, run, registro)
    assert esito is sessione
    assert registro.resolve(StateRef(sessione.initial_state_ref)) == run.initial_ir
    assert registro.resolve(StateRef(sessione.final_state_ref)) == run.final_ir


# --- R1: Claim forgiato strutturalmente valido non pubblica ------------------------


def test_r1_claim_forgiato_non_pubblica():
    sessione, run, registro = _pubblicazione_valida()
    forgiato = Claim(
        "resolved_quantity", sessione.final_state_ref,
        (sessione.final_request.id, sessione.final_request.target),
        sessione.final_claim.evidence_ids, VERIFIER_ID, VERIFIER_VERSION)
    assert forgiato == run.final_execution.claim  # il modello lo accetterebbe
    contraffatta = replace(sessione, final_claim=forgiato)
    esito = validate_publication(contraffatta, run, registro)
    assert isinstance(esito, Failure)
    assert "autorevole" in esito.messaggio


# --- R2: session_id arbitrario non pubblica ------------------------------------------


def test_r2_session_id_narrativo_rifiutato_dal_modello():
    kwargs = _kwargs(_run_d1(), "sessione-d1-prova-001")
    with pytest.raises(ValueError, match="sess"):
        ProofSession(**kwargs)


def test_r2_session_id_di_genere_sbagliato_rifiutato():
    kwargs = _kwargs(_run_d1(), _stato(0))
    with pytest.raises(ValueError, match="sess"):
        ProofSession(**kwargs)


def test_r2_session_id_non_stringa_rifiutato():
    kwargs = _kwargs(_run_d1(), 7)
    with pytest.raises(TypeError, match="invece di str"):
        ProofSession(**kwargs)


# --- R3/R4: ref pendenti -----------------------------------------------------------------


def test_r3_initial_ref_pendente_fallisce():
    sessione, run, _ = _pubblicazione_valida()
    registro = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[-1]), run.final_ir),))
    esito = validate_publication(sessione, run, registro)
    assert isinstance(esito, Failure)
    assert "senza legame" in esito.messaggio


def test_r4_final_ref_pendente_fallisce():
    sessione, run, _ = _pubblicazione_valida()
    registro = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[0]), run.initial_ir),))
    esito = validate_publication(sessione, run, registro)
    assert isinstance(esito, Failure)
    assert "senza legame" in esito.messaggio


def test_conteggio_stati_contro_run_fallisce():
    from fractions import Fraction

    from kirchhoff.domain.didactic.request import ResolvedQuantity
    from kirchhoff.domain.ir import Magnitude, Request
    from kirchhoff.domain.truthfulness import Claim

    run = _run_d1()
    rif = _stato(7)
    domanda = Request("q9", "voltage", "R1")
    ponte = ProofSession(
        session_id=_sessid(7), schema_version=SCHEMA_VERSION,
        versions=_versioni(), provenance=_provenienza(),
        original_request=domanda, initial_state_ref=rif, state_refs=(rif,),
        steps=(AnalyticalProofStep(0, rif, "write_kcl", "D0", "D1"),),
        final_derivation_id="D1", final_request=domanda, final_state_ref=rif,
        final_solution=ResolvedQuantity(
            "D1", "q9", "R1", "voltage", ("a", "b"),
            Magnitude(Fraction(1), "volt")),
        final_claim=Claim(
            "resolved_quantity", rif, ("q9", "R1"), ("D1",),
            VERIFIER_ID, VERIFIER_VERSION))
    esito = validate_publication(ponte, run, _registro(run))
    assert isinstance(esito, Failure)
    assert "non coincide con la run" in esito.messaggio


def test_domanda_originale_di_un_altro_mondo_fallisce():
    from kirchhoff.domain.ir import Request

    sessione, run, registro = _pubblicazione_valida()
    passo = sessione.steps[0]
    lineage_q7 = replace(passo.lineage, request_id="q7")
    passo_q7 = replace(passo, lineage=lineage_q7)
    domanda_q7 = Request("q7", "current", "R1")
    finale_q7 = Request("q7", "current", "R1R2eq")
    pretesa_q7 = Claim(
        "resolved_quantity", sessione.final_state_ref, ("q7", "R1R2eq"),
        sessione.final_claim.evidence_ids, VERIFIER_ID, VERIFIER_VERSION)
    soluzione_q7 = replace(sessione.final_solution, request_id="q7")
    altra_domanda = replace(
        sessione,
        original_request=domanda_q7, final_request=finale_q7,
        steps=(passo_q7, *sessione.steps[1:]), final_claim=pretesa_q7,
        final_solution=soluzione_q7)
    esito = validate_publication(altra_domanda, run, registro)
    assert isinstance(esito, Failure)
    assert "domanda originale della sessione non coincide con la run" in esito.messaggio


def test_operazione_diversa_da_quella_certificata_fallisce():
    sessione, run, registro = _pubblicazione_valida()
    passo = sessione.steps[0]
    lineage = replace(passo.lineage, operation="parallelo")
    parallelo = replace(passo, operation="parallelo", lineage=lineage)
    manomessa = replace(sessione, steps=(parallelo, *sessione.steps[1:]))
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "la sessione non coincide con la run" in esito.messaggio


def test_lineage_copiata_ma_non_autorevole_fallisce():
    sessione, run, registro = _pubblicazione_valida()
    passo = sessione.steps[0]
    copia = replace(passo, lineage=replace(passo.lineage))
    assert copia.lineage == passo.lineage and copia.lineage is not passo.lineage
    manomessa = replace(sessione, steps=(copia, *sessione.steps[1:]))
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "la lineage del passo 0 non e' l'oggetto certificato della run" in esito.messaggio


# --- R5: nessuno spazio per ref fantasma ----------------------------------------------------


def test_r5_schema_chiuso_nessun_ref_fantasma():
    run = _run_d1()
    with pytest.raises(TypeError):
        ProofSession(**{**_kwargs(run, _sessid(0)), "proof_graph_ref": "pg_1"})


# --- R6: verifica non ancorata alla run --------------------------------------------------------


def test_r6_sessione_di_un_altra_run_non_pubblica():
    # Stessa rete, occurrence diversa: valori uguali, oggetti certificati
    # diversi. Il tie `is` deve respingere la verifica non ancorata a run.
    sessione, run, registro = _pubblicazione_valida()
    altra = _run_d1(offset=20)
    esito = validate_publication(sessione, altra, registro)
    assert isinstance(esito, Failure)
    assert "l'oggetto certificato della run" in esito.messaggio


# --- R7: derivation ref pendente ------------------------------------------------------------------


def test_r7_derivazione_inesistente_non_pubblica():
    sessione, run, registro = _pubblicazione_valida()
    passi = (
        sessione.steps[0],
        replace(sessione.steps[1], derivation_after="D9"),
    )
    base = _kwargs(run, sessione.session_id)
    manomessa = ProofSession(**{
        **base,
        "steps": passi,
        "final_derivation_id": "D9",
        "final_solution": replace(
            base["final_solution"], derivation_id="D9"),
        "final_claim": Claim(
            "resolved_quantity", sessione.final_state_ref,
            (sessione.final_request.id, sessione.final_request.target),
            ("D9",), VERIFIER_ID, VERIFIER_VERSION),
    })
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "derivazione" in esito.messaggio


# --- R8/R9/R10: ancoraggio e ordine v0.1 (modello, messaggi distinti) ------------------------------


def test_r8_passo_analitico_su_stato_estraneo_rifiutato():
    run = _run_d1()
    kwargs = _kwargs(run, _sessid(0))
    passi = (kwargs["steps"][0],
             replace(kwargs["steps"][1], state_ref=_stato(30)),
             kwargs["steps"][2])
    with pytest.raises(ValueError, match="non e' uno stato"):
        ProofSession(**{**kwargs, "steps": passi})


def test_r9_passo_analitico_sullo_stato_vecchio_rifiutato():
    run = _run_d1()
    kwargs = _kwargs(run, _sessid(0))
    passi = (kwargs["steps"][0],
             replace(kwargs["steps"][1], state_ref=run.state_ids[0]),
             kwargs["steps"][2])
    with pytest.raises(ValueError, match="finale"):
        ProofSession(**{**kwargs, "steps": passi})


def test_r10_trasformazione_dopo_analitica_rifiutata():
    run = _run_d1()
    kwargs = _kwargs(run, _sessid(0))
    disordinati = (kwargs["steps"][1], kwargs["steps"][2], kwargs["steps"][0])
    rinumerati = tuple(replace(p, index=i) for i, p in enumerate(disordinati))
    with pytest.raises(ValueError, match="dopo un passo analitico"):
        ProofSession(**{**kwargs, "steps": rinumerati})


# --- R11: passo senza evidenza autorevole ---------------------------------------------------------------


def test_r11_evict_transform_senza_oggetto_certificato_non_pubblica():
    sessione, run, registro = _pubblicazione_valida()
    passo = sessione.steps[0]
    copia = replace(
        passo,
        effect=replace(passo.effect),
        lineage=replace(passo.lineage))
    assert copia == passo and copia is not passo
    manomessa = replace(sessione, steps=(copia, *sessione.steps[1:]))
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "certificato della run" in esito.messaggio


# --- R12: Claim uguale ma non autorevole ---------------------------------------------------------------------


def test_r12_claim_uguale_ma_non_autorevole_non_pubblica():
    sessione, run, registro = _pubblicazione_valida()
    gemello = replace(run.final_execution.claim)
    assert gemello == run.final_execution.claim and gemello is not run.final_execution.claim
    manomessa = replace(sessione, final_claim=gemello)
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "autorevole" in esito.messaggio


# --- R13: version pin inventato ----------------------------------------------------------------------------------


def test_r13_pin_di_versione_inventato_rifiutato():
    run = _run_d1()
    with pytest.raises(ValueError, match="planner"):
        ProofSession(**{**_kwargs(run, _sessid(0)),
                        "versions": SessionVersions(
                            "didactic-plan.v9.9", PROFILE, "student-pdf.v0.1")})


# --- R14: provenienza malformata --------------------------------------------------------------------------------------


def test_r14_provenienza_malformata_rifiutata():
    run = _run_d1()
    with pytest.raises(ValueError, match="sha"):
        ProofSession(**{**_kwargs(run, _sessid(0)),
                        "provenance": SessionProvenance(
                            COMPOSER_ID, "non-uno-sha", "dettaglio")})
    with pytest.raises(ValueError, match="produttore"):
        ProofSession(**{**_kwargs(run, _sessid(1)),
                        "provenance": SessionProvenance(
                            "", SHA_FIXTURE, "dettaglio")})


def test_r14_produttore_non_autorevole_non_pubblica():
    sessione, run, registro = _pubblicazione_valida()
    manomessa = replace(
        sessione,
        provenance=replace(sessione.provenance, producer="io-a-mano"))
    esito = validate_publication(manomessa, run, registro)
    assert isinstance(esito, Failure)
    assert "compositore autorevole" in esito.messaggio


# --- R15: artefatto obbligatorio mancante -------------------------------------------------------------------------------


def test_r15_registro_vuoto_fallisce_chiuso():
    sessione, run, _ = _pubblicazione_valida()
    esito = validate_publication(sessione, run, CircuitStateRegistry())
    assert isinstance(esito, Failure)
    assert "senza legame" in esito.messaggio


def test_r15_evidenza_after_letterale_mancante_fallisce():
    sessione, run, _ = _pubblicazione_valida()
    senza_evidenza = CircuitStateRegistry(tuple(
        StateBinding(StateRef(sid), stato)
        for sid, stato in zip(run.state_ids,
                              (run.initial_ir, run.final_ir), strict=True)))
    esito = validate_publication(sessione, run, senza_evidenza)
    assert isinstance(esito, Failure)
    assert "evidenza" in esito.messaggio


def test_r15_registro_sbagliato_con_valori_diversi_fallisce():
    from kirchhoff.pipeline.netlist import leggi

    sessione, run, _ = _pubblicazione_valida()
    # Stessi ref, valori diversi per davvero (R2 da 221 ohm): la risoluzione
    # riesce ma gli artefatti non sono quelli della run.
    altra_ir = leggi(D1.replace("R2 a 0 220 ohm", "R2 a 0 221 ohm"))
    assert altra_ir != run.initial_ir
    evidenze = tuple(
        b for b in _registro(run).bindings
        if b.ref.identifier not in sessione.state_refs)
    assert evidenze, "D1 deve avere l'evidenza dell'after letterale"
    registrone = CircuitStateRegistry((
        StateBinding(StateRef(sessione.state_refs[0]), altra_ir),
        StateBinding(StateRef(sessione.state_refs[1]), run.final_ir),
        *evidenze,
    ))
    esito = validate_publication(sessione, run, registrone)
    assert isinstance(esito, Failure)
    assert "non coincidono" in esito.messaggio


# --- R16: la corruzione interna non diventa mai Refusal -----------------------------------------------------------


def test_r16_corruzione_non_diventa_mai_refusal():
    sessione, run, _ = _pubblicazione_valida()
    registro = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[0]), run.initial_ir),))
    esito = validate_publication(sessione, run, registro)
    assert type(esito) is Failure
    assert not isinstance(esito, Refusal)


def test_r16_tipi_inattesi_falliscono_chiusi():
    sessione, run, registro = _pubblicazione_valida()
    assert type(validate_publication("non-una-sessione", run, registro)) is Failure
    assert type(validate_publication(sessione, "non-una-run", registro)) is Failure
    assert type(validate_publication(sessione, run, "non-un-registro")) is Failure
    assert not isinstance(
        validate_publication(sessione, "non-una-run", registro), Refusal)


def test_pubblicazione_non_risolleva_mai():
    sessione, run, _ = _pubblicazione_valida()
    esito = validate_publication(sessione, run, CircuitStateRegistry())
    assert isinstance(esito, Failure)
