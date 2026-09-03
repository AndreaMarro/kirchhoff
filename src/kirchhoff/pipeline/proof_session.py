"""Validatore di pubblicazione: dalla sessione all'evidenza autorevole (H1.5).

`validate_publication(sessione, run, registro)` prova che una `ProofSession`
ben formata risolve ogni riferimento obbligatorio fino agli artefatti
autoritativi vivi — la `CertifiedDidacticRun` e il `CircuitStateRegistry` —
senza ricalcolare nulla:

- non pianifica, non esegue, non trasforma, non certifica, non renderizza;
- non ricostruisce semantica: confronta identita' (`is`) dove la sessione
  proietta per riferimento (precedente: i campi di `Justification` in
  `render/step/schema.py` si confrontano con `is`, non con `==`) e uguaglianza
  (`==`) dove cita valori;
- ogni rottura diventa `Failure("publication", ...)`, mai `Refusal`: un legame
  corrotto e' un difetto applicativo, non un circuito fuori capability (AD-13);
- nessuna `except` ampia: solo `KeyError` dei registri, con la causa
  conservata nel messaggio.

Il compositore H2 restituira' direttamente l'esito di questa funzione: una
sessione che non si pubblica non e' una sessione quasi pronta.
"""

from __future__ import annotations

from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
from kirchhoff.domain.proof.session import (
    SCHEMA_VERSION,
    AnalyticalProofStep,
    ProofSession,
    SessionProvenance,
    SessionVersions,
    TransformProofStep,
)
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.state_registry import (
    CircuitStateRegistry,
    StateRef,
    stati_operativi,
)

#: L'unico produttore che la pubblicazione riconosce. Dichiarato qui, in H1.5,
#: prima che il compositore esista: H2 dovra' usarlo, non reinventarlo.
COMPOSER_ID = "kirchhoff.pipeline.proof_session.compose_proof_session"

_DOVE = "publication"


def validate_publication(
    sessione: ProofSession,
    run: CertifiedDidacticRun,
    registro: CircuitStateRegistry,
) -> ProofSession | Failure:
    """La sessione risolve ogni ref obbligatorio fino alla run autorevole."""
    if not isinstance(sessione, ProofSession):
        return Failure(
            _DOVE,
            f"pubblicazione di {type(sessione).__name__} invece di ProofSession")
    if not isinstance(run, CertifiedDidacticRun):
        return Failure(
            _DOVE,
            f"pubblicazione contro {type(run).__name__} invece di CertifiedDidacticRun")
    if not isinstance(registro, CircuitStateRegistry):
        return Failure(
            _DOVE,
            f"pubblicazione con {type(registro).__name__} invece di CircuitStateRegistry")
    if len(sessione.state_refs) != len(run.state_ids):
        return Failure(
            _DOVE,
            f"{len(sessione.state_refs)} state refs contro "
            f"{len(run.state_ids)} stati della run: "
            "la sessione non coincide con la run")
    if sessione.original_request != run.original_request:
        return Failure(
            _DOVE,
            "la domanda originale della sessione non coincide con la run")
    # Niente controllo separato su final_request: il modello la inchioda a
    # (originale, catena di lineage), gia' controllati qui e sopra. Una guardia
    # irraggiungibile e' un difetto E-65, non difesa in profondita'.
    if sessione.provenance.producer != COMPOSER_ID:
        return Failure(
            _DOVE,
            f"produttore {sessione.provenance.producer!r} diverso dal "
            f"compositore autorevole {COMPOSER_ID}")
    risolti = []
    for ref in sessione.state_refs:
        try:
            risolti.append(registro.resolve(StateRef(ref)))
        except KeyError as exc:
            return Failure(
                _DOVE, f"state ref {ref} senza legame nel registro: {exc}")
    if tuple(risolti) != stati_operativi(run):
        return Failure(
            _DOVE,
            "gli stati del registro non coincidono con gli stati operativi "
            "della run")
    for numero, esecuzione in enumerate(run.transform_executions):
        try:
            registro.ref_for(esecuzione.after)
        except KeyError:
            return Failure(
                _DOVE,
                f"manca l'evidenza dell'after letterale del passo {numero}: "
                "il prodotto certificato intermedio non e' legato a nessun ref")
    trasformazioni = []
    for passo in sessione.steps:
        if isinstance(passo, TransformProofStep):
            trasformazioni.append(passo)
    # Niente controllo sul conteggio: il modello impone passi-topologici ==
    # stati-1, la run ha esecuzioni == stati-1 per costruzione, e i conteggi
    # degli stati coincidono dal controllo sopra. Guardia irraggiungibile (E-65).
    for numero, (passo, esecuzione) in enumerate(
            zip(trasformazioni, run.transform_executions)):
        if passo.operation != esecuzione.plan.actions[0].kind:
            return Failure(
                _DOVE,
                f"il passo {numero} dice {passo.operation!r} mentre la run ha "
                f"certificato {esecuzione.plan.actions[0].kind!r}: "
                "la sessione non coincide con la run")
        if passo.effect is not esecuzione.observation_effect:
            return Failure(
                _DOVE,
                f"l'effetto del passo {numero} non e' l'oggetto certificato "
                "della run")
        if passo.lineage is not esecuzione.request_lineage:
            return Failure(
                _DOVE,
                f"la lineage del passo {numero} non e' l'oggetto certificato "
                "della run")
    nodale = run.final_execution.execution
    attesi = [(p.kind, p.derivation_before, p.derivation_after)
              for p in nodale.steps]
    ottenuti = [(p.kind, p.derivation_before, p.derivation_after)
                for p in sessione.steps
                if isinstance(p, AnalyticalProofStep)]
    if ottenuti != attesi:
        return Failure(
            _DOVE,
            "i passi analitici non coincidono con la derivazione autorevole "
            "dell'esecuzione nodale")
    # Niente controllo separato su final_derivation_id: il modello lo inchioda
    # all'ultimo passo analitico, qui confrontato con l'esecuzione autorevole.
    # Guardia irraggiungibile (E-65).
    if sessione.final_claim is not run.final_execution.claim:
        return Failure(
            _DOVE,
            "il Claim della sessione non e' l'artefatto autorevole della run: "
            "un Claim strutturalmente valido non prova che il gate abbia girato")
    return sessione


def compose_proof_session(
    run: CertifiedDidacticRun,
    registro: CircuitStateRegistry,
    *,
    session_id: str,
    document_profile: str,
    source_sha: str,
    detail: str,
) -> ProofSession | Failure:
    """Dalla run certificata alla sessione pubblicabile: proiezione soltanto.

    Ogni oggetto certificato passa per riferimento, mai ricalcolato: le
    operazioni, gli effetti, le lineage e il Claim sono gli stessi oggetti
    della run (il validatore ne prova l'identita' con `is`). Gli unici valori
    nuovi sono l'involucro di sessione e i pin dichiarati dal chiamante
    (`document_profile`, `source_sha`, `detail`, `session_id` coniato fuori).

    Chiamate vietate qui dentro (vedi anche il test bianco
    `test_compositore_non_ricalcola_semantica`): pianificare, eseguire,
    trasformare, certificare, risolvere, renderizzare, depositare. Se per
    proiettare servisse un fatto semantico che la run non contiene, manca un
    artefatto a monte: aggiungerlo li', non ricalcolarlo qui.

    Un `Refusal` (o qualunque non-run) in ingresso e' corruzione del chiamante
    e diventa `Failure`: un rifiuto utente resta rifiuto, non si traveste da
    sessione. Solo `TypeError`/`ValueError` del costruttore puro sono mappati,
    con la causa conservata: nessun'altra chiamata qui puo' sollevare.
    """
    if not isinstance(run, CertifiedDidacticRun):
        return Failure(
            "compose",
            f"composizione di {type(run).__name__} invece di "
            "CertifiedDidacticRun: un Refusal a monte resta Refusal")
    if not isinstance(registro, CircuitStateRegistry):
        return Failure(
            "compose",
            f"composizione con {type(registro).__name__} invece di "
            "CircuitStateRegistry")
    nodale = run.final_execution.execution
    passi = (
        *(TransformProofStep(
            i, esecuzione.proof_node, run.state_ids[i + 1],
            esecuzione.plan.actions[0].kind,
            esecuzione.observation_effect, esecuzione.request_lineage)
            for i, esecuzione in enumerate(run.transform_executions)),
        *(AnalyticalProofStep(
            len(run.transform_executions) + j, run.state_ids[-1],
            passo.kind, passo.derivation_before, passo.derivation_after)
            for j, passo in enumerate(nodale.steps)),
    )
    try:
        sessione = ProofSession(
            session_id=session_id,
            schema_version=SCHEMA_VERSION,
            versions=SessionVersions(
                PLAN_SCHEMA_VERSION, PROFILE, document_profile),
            provenance=SessionProvenance(COMPOSER_ID, source_sha, detail),
            original_request=run.original_request,
            initial_state_ref=run.state_ids[0],
            state_refs=tuple(run.state_ids),
            steps=passi,
            final_derivation_id=nodale.derivation.identifier,
            final_request=run.final_request,
            final_state_ref=run.state_ids[-1],
            final_claim=run.final_execution.claim,
        )
    except (TypeError, ValueError) as exc:
        return Failure("compose", f"input di composizione non valido: {exc}")
    return validate_publication(sessione, run, registro)
