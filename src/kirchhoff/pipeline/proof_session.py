"""Validatore di pubblicazione: dalla sessione all'evidenza autorevole (H1.5, H2.5).

Due validatori, due confini di fiducia:

- `validate_publication(sessione, run, registro)` e' il gate di composizione:
  lega la sessione alla run viva. Su effetto, lineage e Claim pretende gli
  *stessi oggetti* certificati (`is`): e' un sanity check in-process contro la
  contraffazione al momento della composizione, non un'identita' durevole.
- `validate_persisted_publication(sessione, registro)` e' il gate durevole:
  dopo serialize -> exit -> deserialize non esiste piu' alcun `is`, quindi
  valida per uguaglianza (`==`) e risoluzione dei ref nel registro, senza la
  run viva. La soluzione finale e il Claim autorevole viaggiano per valore
  nella sessione; gli stati circuitali si risolvono nel registro.

Confine onesto (D-H2.5): il durevole prova coerenza della chiusura
(sessione + registro), non corrispondenza a una run dimenticata. Dopo la
persistenza la fiducia sta nella catena di integrita' (H3: hash e manifest),
non nella RAM del processo che ha composto.

- non pianifica, non esegue, non trasforma, non certifica, non renderizza;
- ogni rottura diventa `Failure("publication", ...)`, mai `Refusal`: un legame
  corrotto e' un difetto applicativo, non un circuito fuori capability (AD-13);
- nessuna `except` ampia: solo `KeyError` dei registri, con la causa
  conservata nel messaggio.

Il compositore H2 restituisce direttamente l'esito del validatore live: una
sessione che non si pubblica non e' una sessione quasi pronta.
"""

from __future__ import annotations

from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
from kirchhoff.domain.identity import conia
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
    if sessione.final_solution != nodale.resolved:
        return Failure(
            _DOVE,
            "la soluzione finale della sessione non e' la quantita' risolta "
            "dall'esecuzione nodale autorevole")
    if sessione.final_claim is not run.final_execution.claim:
        return Failure(
            _DOVE,
            "il Claim della sessione non e' l'artefatto autorevole della run: "
            "un Claim strutturalmente valido non prova che il gate abbia girato")
    return sessione


def validate_persisted_publication(
    sessione: ProofSession,
    registro: CircuitStateRegistry,
) -> ProofSession | Failure:
    """Valida la chiusura strutturale e referenziale senza la run viva.

    D-H2.5: dopo la persistenza gli oggetti certificati originali non esistono
    piu'; questo gate opera sui valori e sulla risoluzione dei riferimenti,
    non sull'identita' degli oggetti. Verifica che ogni state ref si risolva
    e che la sessione dichiari il compositore autorevole come produttore. Le
    invarianti interne della `ProofSession` restano responsabilita' del
    costruttore del modello a ogni costruzione e non vengono duplicate qui.

    Questo validator NON attesta l'integrita' del payload persistito ne'
    l'autenticita' storica della run. In particolare, da solo non puo'
    rilevare una manomissione isolata di `final_solution.amount`.
    L'integrita' dei byte canonici appartiene al gate H3.
    """
    if not isinstance(sessione, ProofSession):
        return Failure(
            _DOVE,
            f"pubblicazione di {type(sessione).__name__} invece di ProofSession")
    if not isinstance(registro, CircuitStateRegistry):
        return Failure(
            _DOVE,
            f"pubblicazione con {type(registro).__name__} invece di CircuitStateRegistry")
    if sessione.provenance.producer != COMPOSER_ID:
        return Failure(
            _DOVE,
            f"produttore {sessione.provenance.producer!r} diverso dal "
            f"compositore autorevole {COMPOSER_ID}")
    for ref in sessione.state_refs:
        try:
            registro.resolve(StateRef(ref))
        except KeyError as exc:
            return Failure(
                _DOVE, f"state ref {ref} senza legame nel registro: {exc}")
    return sessione


def compose_proof_session(
    run: CertifiedDidacticRun,
    registro: CircuitStateRegistry,
    *,
    session_instant_ms: int,
    session_entropy: bytes,
    document_profile: str,
    source_sha: str,
    detail: str,
) -> ProofSession | Failure:
    """Dalla run certificata alla sessione pubblicabile: proiezione soltanto.

    D-H2.5-5: il compositore e' l'unico writer che conia `sess_`
    (ownership singola): `session_instant_ms` e `session_entropy` entrano iniettati
    (AD-17, stessa disciplina di `ClockPort`) e l'identificatore nasce qui
    dentro con `conia`. Il chiamante non fornisce mai un id gia' coniato:
    a parita' di ingressi il conio e' riproducibile, a entropia fresca
    l'occurrence e' nuova. La freschezza dell'entropia resta dovere del
    chiamante (radice di composizione), come per ogni altro conio.

    Ogni oggetto certificato passa per riferimento, mai ricalcolato: le
    operazioni, gli effetti, le lineage, la soluzione risolta e il Claim sono
    gli stessi oggetti della run (il validatore live ne prova l'identita' con
    `is`, tranne la soluzione che lega per valore `==` come il percorso
    durevole). Gli unici valori nuovi sono l'involucro di sessione,
    l'identificatore coniato qui e i pin dichiarati dal chiamante
    (`document_profile`, `source_sha`, `detail`).

    Chiamate vietate qui dentro (vedi anche il test bianco
    `test_compositore_non_ricalcola_semantica`): pianificare, eseguire,
    trasformare, certificare, risolvere, renderizzare, depositare. Se per
    proiettare servisse un fatto semantico che la run non contiene, manca un
    artefatto a monte: aggiungerlo li', non ricalcolarlo qui.

    Un `Refusal` (o qualunque non-run) in ingresso e' corruzione del chiamante
    e diventa `Failure`: il compositore stretto non propaga Refusal, lo
    respinge. La propagazione "un rifiuto utente resta rifiuto" vive al
    confine di prodotto sopra di qui (orchestrare -> se Refusal restituirlo
    senza mai chiamare il compositore). Solo `TypeError`/`ValueError` del
    conio e del costruttore puro sono mappati, con la causa conservata:
    nessun'altra chiamata qui puo' sollevare.
    """
    if not isinstance(run, CertifiedDidacticRun):
        return Failure(
            "compose",
            f"composizione di {type(run).__name__} invece di "
            "CertifiedDidacticRun: un Refusal a monte non si compone")
    if not isinstance(registro, CircuitStateRegistry):
        return Failure(
            "compose",
            f"composizione con {type(registro).__name__} invece di "
            "CircuitStateRegistry")
    try:
        session_id = conia("sess", session_instant_ms, session_entropy)
    except (TypeError, ValueError) as exc:
        return Failure(
            "compose", f"identificatore di sessione non coniabile: {exc}")
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
            final_solution=nodale.resolved,
            final_claim=run.final_execution.claim,
        )
    except (TypeError, ValueError) as exc:
        return Failure("compose", f"input di composizione non valido: {exc}")
    return validate_publication(sessione, run, registro)
