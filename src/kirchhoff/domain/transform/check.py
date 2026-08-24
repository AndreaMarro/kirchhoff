"""Coerenza di un `Delta` con i due circuiti che collega.

Le guardie in `delta.py` rendono impossibile un `Delta` malformato *in se'*. Qui
si verifica cio' che un solo oggetto non puo' sapere: che gli ingressi esistessero
prima, che le uscite esistano dopo, e che nulla sparisca o compaia senza essere
spiegato.

**Perche' questi controlli non restituiscono un `Refusal`.** AD-19 tiene chiusa
l'enumerazione delle cause e assegna a `domain/transform/check` esattamente tre
cause: `identity_violation`, `preserve_nonmaximal`, `empty_boundary`. Nessuna
copre «una entita' e' sparita senza derivazione». Aggiungerne una *«e' una modifica
dello spine, non di un modulo»*, ed e' una decisione del proprietario. Fino ad
allora questi controlli producono violazioni tipizzate che la Story 2.6 tradurra'
nel canale giusto.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ir import IR
from .delta import Delta, EntityRef


@dataclass(frozen=True, slots=True)
class DeltaViolation:
    code: str
    subject: str
    detail: str


def entities_of(ir: IR) -> frozenset[EntityRef]:
    """Le entita' che il circuito conosce: i suoi componenti e i suoi nodi."""
    return frozenset(
        [EntityRef("component", c.id) for c in ir.components]
        + [EntityRef("node", n) for n in ir.nodes]
    )


def preserve_set(before: IR, after: IR) -> frozenset[EntityRef]:
    """`Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` (AD-22).

    Calcolato **qui**, dal confronto dei due circuiti, e mai dedotto dal `Delta`
    ne' dal disegno: e' il difetto che CV1 descrive e che AD-22 chiude.
    """
    return entities_of(before) & entities_of(after)


def check_delta(delta: Delta, before: IR, after: IR) -> tuple[DeltaViolation, ...]:
    """Le violazioni, in ordine deterministico. Vuoto quando il `Delta` regge."""
    prima = entities_of(before)
    dopo = entities_of(after)
    preservate = prima & dopo
    trovate: list[DeltaViolation] = []

    # 2 — ogni ingresso esisteva prima.
    for e in sorted(delta.consumed):
        if e not in prima:
            trovate.append(DeltaViolation(
                "input_inesistente", str(e),
                "consumata da una derivazione ma assente dal circuito di partenza"))

    # 3 — ogni uscita esiste dopo.
    for e in sorted(delta.produced):
        if e not in dopo:
            trovate.append(DeltaViolation(
                "output_inesistente", str(e),
                "prodotta da una derivazione ma assente dal circuito di arrivo"))

    # 1 — un'entita' preservata non puo' essere consumata.
    #     Il caso simmetrico e' invece lecito: una preservata puo' essere uscita,
    #     perche' e' li' che una fusione atterra.
    for e in sorted(delta.consumed & preservate):
        trovate.append(DeltaViolation(
            "preservata_consumata", str(e),
            "sopravvive nel circuito di arrivo e non puo' essere stata consumata"))

    # 4 — completezza della lineage, nelle due direzioni.
    for e in sorted(prima - dopo):
        if e not in delta.consumed:
            trovate.append(DeltaViolation(
                "sparizione_non_spiegata", str(e),
                "assente dal circuito di arrivo e nessuna derivazione la consuma"))
    for e in sorted(dopo - prima):
        if e not in delta.produced:
            trovate.append(DeltaViolation(
                "comparsa_non_spiegata", str(e),
                "assente dal circuito di partenza e nessuna derivazione la produce"))

    return tuple(trovate)
