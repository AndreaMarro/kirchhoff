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

from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
from kirchhoff.domain.proof.session import (
    AnalyticalProofStep,
    ProofSession,
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
