"""Coerenza di un `Delta` con i due circuiti che collega.

Le guardie in `delta.py` rendono impossibile un `Delta` malformato *in se'*. Qui
si verifica cio' che un solo oggetto non puo' sapere: che gli ingressi esistessero
prima, che le uscite esistano dopo, e che nulla sparisca o compaia senza essere
spiegato.

**Perche' questi controlli non restituiscono un `Refusal`.** AD-19 tiene chiusa
l'enumerazione delle cause e assegna a `domain/transform/check` esattamente tre
cause: `identity_violation`, `preserve_nonmaximal`, `empty_boundary`. Nessuna
copre «una entita' e' sparita senza derivazione». Aggiungerne una *«e' una modifica
dello spine, non di un modulo»*, ed e' una decisione del proprietario. Quei controlli
continuano quindi a produrre `DeltaViolation`, e restano dove sono.

**Le tre cause di AD-19 arrivano invece adesso.** `check_transform` piu' in basso
emette `identity_violation`, `preserve_nonmaximal` e `empty_boundary` come `Refusal`,
perche' quelle tre lo spine le ha gia' assegnate a questo modulo. La distinzione non
e' burocratica: cio' che ha una causa legale diventa un Rifiuto che nomina l'elemento
coinvolto e si legge come Domanda mirata; cio' che non ce l'ha resta una violazione
interna, e inventarle una causa la trasformerebbe in `sanity` — dove l'utente perde
la localizzazione che K-3 promette.

**Nessuno di questi controlli legge il `LayoutIR`**, e nessuno puo': sono proprieta'
di insiemi di entita', e la firma non ammette geometria (AD-2 em., AD-21).

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ir import IR, Component
from ..refusal import Refusal
from .catalog import IDENTITY_ATTRIBUTES, TransformationKind, mutable_attributes
from .delta import Delta, EntityRef
from .result import Boundary, LayoutPatch


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


def attributes_of(c: Component) -> dict[str, object]:
    """Gli attributi sostanziali di un componente, per il confronto d'identita'."""
    return {nome: getattr(c, nome) for nome in IDENTITY_ATTRIBUTES}


def preserve_set(
    before: IR, after: IR, *, operation: TransformationKind | None = None,
) -> frozenset[EntityRef]:
    """`Pₖ` (AD-22 em. v2.1): coincidenza dell'identificatore **e** degli attributi.

    Calcolato **qui**, dal confronto dei due circuiti, e mai dedotto dal `Delta` ne'
    dal disegno: e' il difetto che CV1 descrive e che AD-22 chiude.

    L'intersezione per solo identificatore non bastava, ed e' stato dimostrato con
    codice eseguito (istruttoria R2-A): `R1 (a,b) 10Ω` e `R2 (a,b) 20Ω` che fondono
    in una equivalente battezzata `R1 (a,b) 6⅔Ω` hanno tipo e terminali coincidenti,
    e `R1 ∈ Pₖ` risultava vero. In serie i terminali sarebbero cambiati e il difetto
    non si sarebbe visto: **un discriminante che regge su un caso solo non e' un
    discriminante.**

    Quali attributi possano cambiare lo dichiara il **Catalogo**, per operazione, e
    l'insieme predefinito e' vuoto. `operation=None` significa quindi «nessuna
    mutazione ammessa», che e' la lettura piu' stretta e mai quella piu' comoda: chi
    non dice quale operazione sta misurando non ottiene indulgenza.
    """
    mutabili = mutable_attributes(operation) if operation is not None else frozenset()
    per_id = {c.id: c for c in after.components}
    preservate: set[EntityRef] = set()

    for e in entities_of(before) & entities_of(after):
        if e.kind == "node":
            # Un nodo e' il proprio nome: non ha attributi che possano divergere.
            preservate.add(e)
            continue
        prima, dopo = before.component(e.id), per_id[e.id]
        cambiati = {k for k, v in attributes_of(prima).items()
                    if attributes_of(dopo)[k] != v}
        if cambiati <= mutabili:
            preservate.add(e)

    return frozenset(preservate)


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


# --- le tre cause di AD-19 assegnate a questo modulo --------------------------


def check_transform(
    before: IR,
    after: IR,
    operation: TransformationKind,
    patch: LayoutPatch,
    boundary: Boundary | None,
) -> Refusal | None:
    """Massimalita', identita' e boundary. `None` quando reggono tutti e tre.

    Gira **prima** che il `TransformResult` sia costruito, e per questo puo' vedere
    un `boundary` assente: `Boundary` si rifiuta di esistere vuoto, quindi chi non e'
    riuscito a costruirlo passa `None` qui e riceve una causa legale invece di
    un'eccezione. Un rifiuto e' un atto di onesta' del sistema; un'eccezione e' un
    guasto (AD-13).

    L'ordine dei tre controlli e' fisso e non e' indifferente: `empty_boundary` e' la
    condizione piu' grossolana e viene per prima, cosi' la diagnosi nomina il difetto
    piu' grande invece di un suo sintomo.
    """
    if boundary is None:
        return Refusal(
            "empty_boundary", operation, "request",
            f"{operation}: ∂Tₖ = ∅. Un sottografo che non confina con nulla non e' "
            "un passo della derivazione: e' una riscrittura dell'intera rete.")

    preservate = preserve_set(before, after, operation=operation)

    # AD-22 em.: `id_{k+1}(x) = id_k(x)` per ogni `x ∈ Pₖ`, **senza tolleranza**.
    # E' un controllo *inter*-passo: il round-trip, che confronta SVG(Cₖ₊₁) con
    # CircuitIR(Cₖ₊₁), non lo cattura, perche' una rinomina coerente sui due lati
    # gli passerebbe pulita.
    for e in sorted(preservate):
        immagine = patch.image_of(e.id)
        if immagine != e.id:
            return Refusal(
                "identity_violation", e.id, e.kind,
                f"{e}: sopravvive alla trasformazione {operation} ma il "
                f"node_mapping la rinomina in {immagine!r}. Un'entita' preservata "
                "conserva il proprio identificatore, senza tolleranza.")

    # AD-22 em.: la massimalita' e' verificata **indipendentemente** dalla
    # `Transform` che la dichiara. «Diverso da `Pₖ`», non «piu' piccolo di»: la
    # causa copre entrambi i versi.
    dichiarate = frozenset(patch.preserve)
    if dichiarate != preservate:
        mancanti = sorted(preservate - dichiarate)
        eccedenti = sorted(dichiarate - preservate)
        return Refusal(
            "preserve_nonmaximal", operation, "request",
            f"{operation}: `preserve` diverso da `Pₖ`. "
            f"Sopravvissute non dichiarate: "
            f"{', '.join(str(e) for e in mancanti) or 'nessuna'}. "
            f"Dichiarate ma non sopravvissute: "
            f"{', '.join(str(e) for e in eccedenti) or 'nessuna'}.")

    # Il verso che l'emendamento del 15 agosto chiude: dichiarare «creata»
    # un'entita' in realta' sopravvissuta restringeva `Pₖ`, il `preserve` risultava
    # conforme perche' il riferimento si era ristretto con lui, e VCER tornava
    # perfetto.
    intruse = sorted(frozenset(patch.create) & preservate)
    if intruse:
        return Refusal(
            "preserve_nonmaximal", intruse[0].id, intruse[0].kind,
            f"{intruse[0]}: dichiarata in `create` ma sopravvive a {operation}. "
            "Chi e' misurato non definisce il proprio riferimento.")

    return None
