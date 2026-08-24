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


def _immagine(identificatore: str, mappa: tuple[tuple[str, str], ...]) -> str:
    """L'immagine di un **nodo** attraverso `node_mapping`. Identita' se non mappato.

    Stessa semantica di `LayoutPatch.image_of`, e qui perche' `preserve_set` riceve
    la mappa e non la patch: `Pₖ` e' una proprieta' dei due circuiti piu' la mappa,
    non della struttura che la trasporta.

    **Solo nodi.** `node_mapping` lo dice nel nome, e AD-2 em. la descrive come la
    mappa fra identificatori di nodo che il renderer deve seguire. Applicarla anche
    agli identificatori di componente li fa collidere in un unico spazio di nomi che
    `EntityRef` tiene invece distinto: un componente di id `a` e un nodo di id `a`
    sono due entita' diverse, e una rinomina del secondo non riguarda il primo.
    """
    for sorgente, arrivo in mappa:
        if sorgente == identificatore:
            return arrivo
    return identificatore


def preserve_set(
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
    node_mapping: tuple[tuple[str, str], ...] = (),
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

    **L'intersezione si prende *dopo* `node_mapping`**, come AD-22 em. la definisce, e
    non prima. La differenza non e' formale: senza la mappa un nodo davvero rinominato
    fra `Cₖ` e `Cₖ₊₁` esce da `Pₖ` per il solo fatto di non chiamarsi piu' come prima,
    e il ciclo d'identita' di `check_transform` — che scorre `Pₖ` — non lo vede mai.
    Il controllo che AD-22 chiama `identity_violation` sarebbe cosi' **cieco alla
    violazione che nomina**, e scatterebbe solo su una patch che dichiara una rinomina
    non avvenuta. Con la mappa, `node:a` che diventa `node:a2` e' un sopravvissuto —
    la sua immagine esiste in `Cₖ₊₁` — e la rinomina e' una violazione, che e'
    esattamente cio' che l'emendamento pretende.

    Per la stessa ragione i **terminali** di un componente si confrontano attraverso
    la mappa: un componente il cui terminale cambia *solo* perche' il nodo che tocca e'
    stato assorbito non ha cambiato identita', e dichiararlo non preservato
    restringerebbe `Pₖ` proprio dove una fusione di nodi lo mette alla prova.

    `node_mapping=()` — il caso di ogni riduzione del registro, che non rinomina nulla
    — lascia il calcolo identico a un'intersezione per identificatore piu' attributi.
    """
    mutabili = mutable_attributes(operation) if operation is not None else frozenset()
    nodi_dopo = frozenset(after.nodes)
    per_id = {c.id: c for c in after.components}
    preservate: set[EntityRef] = set()

    for e in entities_of(before):
        if e.kind == "node":
            # Un nodo e' il proprio nome: non ha attributi che possano divergere.
            # Sopravvive quando la **sua immagine** esiste in `Cₖ₊₁`.
            if _immagine(e.id, node_mapping) in nodi_dopo:
                preservate.add(e)
            continue
        if e.id not in per_id:
            continue
        prima, dopo = before.component(e.id), per_id[e.id]
        atteso = attributes_of(prima)
        atteso["terminals"] = tuple(
            _immagine(t, node_mapping) for t in prima.terminals)
        cambiati = {k for k, v in atteso.items() if attributes_of(dopo)[k] != v}
        if cambiati <= mutabili:
            preservate.add(e)

    return frozenset(preservate)


def check_delta(
    delta: Delta,
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
) -> tuple[DeltaViolation, ...]:
    """Le violazioni, in ordine deterministico. Vuoto quando il `Delta` regge.

    **`Pₖ` si calcola con `preserve_set`, e in questo modulo esiste una sola volta.**
    Il controllo «una preservata non puo' essere consumata» usava l'intersezione per
    solo identificatore — il discriminante che l'istruttoria R2-A ha demolito, nello
    stesso file che ne ospita il sostituto. Due predicati per la stessa cosa divergono
    nel posto dove nessuno guarda (E-62), e qui la divergenza produceva una **falsa
    accusa**: `R1` fusa in una equivalente che ne riusa il nome coincide per
    identificatore, quindi risultava «preservata», quindi la derivazione che la
    consuma — quella vera — veniva segnalata come violazione. Accusare un passo
    corretto e' il difetto peggiore di questo prodotto.

    `operation` sceglie il discriminante dichiarato dal Catalogo, con la stessa
    convenzione di `preserve_set`: non dirla significa «nessuna mutazione ammessa»,
    che e' la lettura piu' stretta e quindi quella che accusa di meno.
    """
    prima = entities_of(before)
    dopo = entities_of(after)
    preservate = preserve_set(before, after, operation=operation)
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

    # AD-22 em.: `id_{k+1}(x) = id_k(x)` per ogni `x ∈ Pₖ`, **senza tolleranza**.
    # E' un controllo *inter*-passo: il round-trip, che confronta SVG(Cₖ₊₁) con
    # CircuitIR(Cₖ₊₁), non lo cattura, perche' una rinomina coerente sui due lati
    # gli passerebbe pulita.
    #
    # Ha due versi, e chiuderne uno solo lascia aperto l'altro.
    nodi_prima, nodi_dopo = frozenset(before.nodes), frozenset(after.nodes)

    # (a) La mappa dichiara una rinomina che `Cₖ₊₁` non conferma. Senza questo verso
    #     `node_mapping` diventa una via d'uscita: mappare un nodo davvero
    #     sopravvissuto su un nome inesistente lo farebbe cadere fuori da `Pₖ`, e un
    #     `preserve` che lo omette risulterebbe conforme perche' il riferimento si e'
    #     ristretto con lui — la stessa autocertificazione che l'emendamento chiude.
    for sorgente, arrivo in patch.node_mapping:
        if sorgente in nodi_prima and arrivo not in nodi_dopo:
            return Refusal(
                "identity_violation", sorgente, "node",
                f"node:{sorgente}: il node_mapping lo rinomina in {arrivo!r}, che in "
                f"Cₖ₊₁ non esiste. Una mappa che dichiara una rinomina non avvenuta "
                "non e' verificabile contro il circuito che pretende di descrivere.")

    preservate = preserve_set(
        before, after, operation=operation, node_mapping=patch.node_mapping)

    # (b) Un'entita' che sopravvive davvero, e che la mappa rinomina. `Pₖ` e' preso
    #     **dopo** `node_mapping` (AD-22 em.), quindi il nodo rinominato ci sta
    #     dentro ed e' qui che lo si vede. La mappa riguarda i soli nodi: un
    #     componente e un nodo omonimi sono due entita' distinte, e `image_of`
    #     applicata a un componente produrrebbe un `identity_violation` spurio su
    #     un'entita' che nessuno ha rinominato.
    for e in sorted(preservate):
        if e.kind != "node":
            continue
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
