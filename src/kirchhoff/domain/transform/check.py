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

from ..ir import IR, Component, orienta
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
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
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

    **`node_mapping` e' ritirata (AD-22 v2.2)**, e con lei lo strato di mappatura che
    stava fra i due circuiti. `Pₖ` e' ora un'intersezione per identificatore piu' il
    discriminante sugli attributi — che e' esattamente cio' che il calcolo faceva
    gia' in ogni corsa reale, perche' ogni produttore passava `node_mapping=()`.

    La conseguenza voluta: `rinomina != preservazione`. Un nodo che cambia nome fra
    `Cₖ` e `Cₖ₊₁` non entra in `Pₖ` sotto nessuno dei due nomi, ed e' corretto — una
    rinomina e' una consumata piu' una creata, con lineage nel `Delta`. Lo stesso per
    un componente i cui terminali cambiano: attributi diversi, identita' diversa.
    """
    mutabili = mutable_attributes(operation) if operation is not None else frozenset()
    nodi_dopo = frozenset(after.nodes)
    per_id = {c.id: c for c in after.components}
    preservate: set[EntityRef] = set()

    for e in entities_of(before):
        if e.kind == "node":
            # Un nodo e' il proprio nome: non ha attributi che possano divergere.
            # Sopravvive quando la **sua immagine** esiste in `Cₖ₊₁`.
            if e.id in nodi_dopo:
                preservate.add(e)
            continue
        if e.id not in per_id:
            continue
        # **I terminali si confrontano ORIENTATI, e su entrambi i lati.**
        # `ir/canonical.py` dichiara `resistor`, `capacitor`, `inductor` simmetrici:
        # «nessuna di queste differenze dice qualcosa del circuito». Confrontarli per
        # uguaglianza sintattica di tupla contraddiceva quel modulo — misurato: due IR
        # che `canonicalize` dichiara identici davano `Pₖ` diversi, e un passo che non
        # toccava nulla riceveva quattro violazioni. Falsa accusa, sulla superficie
        # che la decisione owner del 25/08 conserva per il produttore esterno.
        #
        # La regola e' **riusata**, non riscritta: `orienta` vive in `canonical.py` e
        # non tocca i generatori, perche' li' l'ordine e' la polarita' e riordinarla
        # produrrebbe un circuito diverso che si dichiara uguale.
        #
        # La normalizzazione era anche **unilaterale**: `tuple(prima.terminals)` su un
        # lato solo, quindi un componente con terminali-lista risultava non preservato
        # rispetto a se stesso. Ora entrambi i lati passano da `orienta` e da `tuple`.
        prima, dopo = before.component(e.id), per_id[e.id]
        atteso = attributes_of(prima)
        atteso["terminals"] = tuple(orienta(prima).terminals)
        osservato = attributes_of(dopo)
        osservato["terminals"] = tuple(orienta(dopo).terminals)
        cambiati = {k for k, v in atteso.items() if osservato[k] != v}
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
    #
    # **Si misura contro `Pₖ`, non contro l'intersezione per identificatore.** La
    # differenza e' l'entita' MUTATA IN LUOGO: `R1 (a,b) 10Ω` che diventa
    # `R1 (a,b) 6⅔Ω` sta in entrambi i circuiti per nome, quindi `prima - dopo` non
    # la vedeva, ma esce da `Pₖ` per il discriminante v2.1. AD-22 v2.1 dice gia' che
    # cosa e': «Un'entita' che fallisce la seconda condizione non e' preservata: e'
    # una rimozione piu' una creazione, **e come tale deve comparire nel Delta**».
    #
    # Misurato prima della correzione: sul caso fondativo dell'istruttoria R2-A, un
    # `Delta` che non nominava affatto `R1` passava senza violazioni, e due lineage
    # contraddittorie erano entrambe benedette.
    for e in sorted(prima - preservate):
        if e not in delta.consumed:
            trovate.append(DeltaViolation(
                "sparizione_non_spiegata", str(e),
                "non sopravvive al passo e nessuna derivazione la consuma"))

    # 5 — il verso simmetrico: cio' che nasce dev'essere prodotto da qualcuno.
    #
    # **Misurato contro `Pₖ`, come il verso 4.** Il ciclo era `dopo - prima` e la
    # correzione precedente ne aveva aggiunto uno accanto invece di cambiarlo: due
    # voci di vocabolario per lo stesso difetto, e la vecchia che non poteva mai
    # scattare da sola — `preservate ⊆ prima`, quindi `dopo - prima ⊆ dopo - preservate`.
    # Un controllo che non puo' fallire indipendentemente non protegge; duplicarlo
    # e' il gesto E-62 che questo pacchetto chiude altrove.
    for e in sorted(dopo - preservate):
        if e not in delta.produced:
            trovate.append(DeltaViolation(
                "comparsa_non_spiegata", str(e),
                "assente dal circuito di partenza e nessuna derivazione la produce"))

    return tuple(trovate)


# --- le tre cause di AD-19 assegnate a questo modulo --------------------------


@dataclass(frozen=True, slots=True, order=True)
class PatchViolation:
    code: str
    subject: str
    detail: str


def check_patch(
    patch: LayoutPatch,
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
) -> tuple[PatchViolation, ...]:
    """`create` e `remove` contro i due circuiti. Vuoto quando la patch regge.

    E' il terzo lato dell'invariante che AD-22 esige e che il pacchetto verificava
    solo a meta':

        cio' che appare e sparisce nel `CircuitIR`
          <-> cio' che dice il `Delta`
          <-> cio' che dice la `LayoutPatch`

    Il `Delta` ha il proprio controllore da quando `check_delta` e' cablato. La
    patch non ne aveva: `preserve` era confrontato con `Pₖ`, ma `create` e `remove`
    con nulla. Misurato: una patch con `create=(component:MaiEsistita,)` — o con
    `remove` — attraversava `check_transform` pulita, e un renderer che la seguisse
    riceverebbe istruzioni su entita' che nessuno dei due circuiti possiede.

    **Uguaglianza, non inclusione.** La Rule di AD-22 dice «diverso da `Pₖ`» e non
    «piu' piccolo di», e la stessa lettura vale qui: una patch che tace su cio' che e'
    sparito e' bugiarda quanto una che dichiara cio' che non c'e' mai stato. I due
    versi hanno codici distinti perche' la diagnosi deve dire quale dei due e'.

    Le due riduzioni del catalogo producono gia' l'uguaglianza esatta: questo
    controllo non stringe il contratto, lo rende verificato invece che sperato.
    """
    # **Rispetto a `Pₖ`, non all'intersezione per identificatore.** Un'entita' che
    # cambia attributi a nome fermo sta in entrambi i circuiti e non e' preservata:
    # per AD-22 v2.1 e' una rimozione piu' una creazione, e la patch deve dirlo in
    # entrambi i campi. Misurando per id, quell'entita' non era ne' apparsa ne'
    # sparita: la patch che taceva passava, e quella che diceva la verita' della
    # dottrina veniva rifiutata in entrambi i versi.
    preservate = preserve_set(before, after, operation=operation)
    apparse = entities_of(after) - preservate
    sparite = entities_of(before) - preservate
    dichiarate_create = frozenset(patch.create)
    dichiarate_remove = frozenset(patch.remove)
    trovate: list[PatchViolation] = []

    for e in sorted(dichiarate_create - apparse):
        trovate.append(PatchViolation(
            "create_non_apparsa", str(e),
            "dichiarata creata dalla patch ma assente dalle entita' comparse in Cₖ₊₁"))
    for e in sorted(apparse - dichiarate_create):
        trovate.append(PatchViolation(
            "apparsa_non_dichiarata", str(e),
            "compare in Cₖ₊₁ e non era in Cₖ, ma la patch non la dichiara creata"))
    for e in sorted(dichiarate_remove - sparite):
        trovate.append(PatchViolation(
            "remove_non_sparita", str(e),
            "dichiarata rimossa dalla patch ma ancora presente in Cₖ₊₁, o mai esistita"))
    for e in sorted(sparite - dichiarate_remove):
        trovate.append(PatchViolation(
            "sparita_non_dichiarata", str(e),
            "era in Cₖ e non e' in Cₖ₊₁, ma la patch non la dichiara rimossa"))

    # **Il quarto campo.** `reroute_scope` non era letto da nessun controllore:
    # una patch che vi nominava entita' inesistenti attraversava tutto, e anche una
    # che lo lasciava vuoto. Non e' decorativo — FR-38 lo usa come limite normativo
    # del renderer: «il numero di elementi con coordinate cambiate e' limitato allo
    # `reroute_scope` dichiarato». Un renderer che lo rispetta riceveva istruzioni su
    # entita' che nessuno dei due circuiti possiede, che e' parola per parola
    # l'argomento con cui questa funzione e' nata, un campo piu' in la'.
    #
    # Si verifica cio' che e' verificabile senza decidere la semantica: le entita'
    # devono esistere in almeno uno dei due circuiti, e l'insieme non puo' essere
    # vuoto. **Che cosa `reroute_scope` debba contenere resta aperto**: il docstring
    # lo definisce «l'insieme dei rami la cui instradatura e' libera», il motore vi
    # scrive il componente creato piu' i NODI del boundary, e le due letture non
    # coincidono. Registrato in `deferred-work.md`, non deciso qui.
    conosciute = entities_of(before) | entities_of(after)
    for e in sorted(frozenset(patch.reroute_scope) - conosciute):
        trovate.append(PatchViolation(
            "reroute_scope_fantasma", str(e),
            "la patch la dichiara reinstradabile, ma non e' in nessuno dei due circuiti"))
    if not patch.reroute_scope:
        trovate.append(PatchViolation(
            "reroute_scope_vuoto", "—",
            "nessuna instradatura libera: un passo che non permette di ridisegnare "
            "nulla non ha un prodotto visuale"))

    return tuple(trovate)


@dataclass(frozen=True, slots=True, order=True)
class BoundaryViolation:
    code: str
    subject: str
    detail: str


def _terminali(ir: IR, componenti: frozenset[EntityRef]) -> frozenset[EntityRef]:
    """I nodi che i componenti indicati toccano, come `EntityRef`."""
    return frozenset(
        EntityRef("node", t)
        for c in ir.components
        if EntityRef("component", c.id) in componenti
        for t in c.terminals
    )


def check_boundary(
    boundary: Boundary,
    patch: LayoutPatch,
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
) -> tuple[BoundaryViolation, ...]:
    """`∂Tₖ` nel contenuto. Vuoto quando regge.

    Il boundary era verificato solo come vuoto o non vuoto — `empty_boundary`. Non
    bastava: `Boundary((node:fantasma,))`, con un'entita' che nessuno dei due
    circuiti possiede, attraversava il controllore pulito. Un boundary che nomina
    entita' inesistenti non dice **dove guardare**: dice dove non c'e' niente.

    Due condizioni **necessarie**, misurate vere su tutte le riduzioni del catalogo
    prima di essere imposte:

    1. **Sopravvivenza.** `∂Tₖ ⊆ Pₖ`. Cio' che non sopravvive al passo non e' un
       punto di contatto col resto della rete: e' dentro il sottografo trasformato.
       Il nodo assorbito da una serie ne e' l'esempio — sparisce, quindi non
       confina.
    2. **Adiacenza.** Ogni entita' del boundary e' terminale di qualcosa che il
       passo ha tolto o creato. Un nodo lontano che sopravvive non confina con
       niente di trasformato, e dichiararlo allargherebbe la zona che il renderer
       annota senza che nulla lo giustifichi.

    **Necessarie, non sufficienti — e la scelta e' deliberata.** L'insieme
    `terminali(rimossi ∪ creati) ∩ Pₖ` coincide, su entrambe le riduzioni, con il
    boundary che producono: si potrebbe quindi imporre l'uguaglianza, come AD-22 fa
    per `preserve`. Non si fa, perche' imporla renderebbe il `Boundary` un campo
    **derivabile**, e un campo che nessun produttore puo' scegliere e' un campo che
    non serve dichiarare — la stessa domanda che ha portato al ritiro di
    `node_mapping`. Se `Boundary` debba restare dichiarato o diventare derivato e'
    una decisione di contratto, non un effetto collaterale di un controllo.
    """
    # `operation` come negli altri due controllori: senza, `Pₖ` qui era calcolato
    # con un discriminante diverso, e il giorno in cui il Catalogo dichiara un
    # attributo mutabile i controllori darebbero verdetti opposti sull'appartenenza
    # della stessa entita'.
    preservate = preserve_set(before, after, operation=operation)
    cambiati = frozenset(patch.remove) | frozenset(patch.create)
    adiacenti = _terminali(before, cambiati) | _terminali(after, cambiati)
    trovate: list[BoundaryViolation] = []

    for e in sorted(boundary.entities):
        if e not in preservate:
            trovate.append(BoundaryViolation(
                "fuori_da_pk", str(e),
                "il boundary la nomina ma non sopravvive al passo: non e' un punto "
                "di contatto col resto della rete, e' dentro il sottografo"))
            continue
        if e not in adiacenti:
            trovate.append(BoundaryViolation(
                "non_adiacente", str(e),
                "sopravvive ma non tocca nulla di rimosso o creato: non confina "
                "con il sottografo trasformato"))

    return tuple(trovate)


def check_transform(
    before: IR,
    after: IR,
    operation: TransformationKind,
    patch: LayoutPatch,
    boundary: Boundary | None,
) -> Refusal | None:
    """Boundary e massimalita'. `None` quando reggono entrambi.

    Erano tre. L'identita' e' uscita con `node_mapping` (AD-22 v2.2): senza strato
    di mappatura, `id_{k+1}(x) = id_k(x)` su `Pₖ` e' vero per costruzione, e un
    controllo che non puo' fallire non e' un controllo.

    Gira **prima** che il `TransformResult` sia costruito, e per questo puo' vedere
    un `boundary` assente: `Boundary` si rifiuta di esistere vuoto, quindi chi non e'
    riuscito a costruirlo passa `None` qui e riceve una causa legale invece di
    un'eccezione. Un rifiuto e' un atto di onesta' del sistema; un'eccezione e' un
    guasto (AD-13).

    L'ordine dei due controlli e' fisso e non e' indifferente: `empty_boundary` e' la
    condizione piu' grossolana e viene per prima, cosi' la diagnosi nomina il difetto
    piu' grande invece di un suo sintomo.
    """
    if boundary is None:
        return Refusal(
            "empty_boundary", operation, "operation",
            f"{operation}: ∂Tₖ = ∅. Un sottografo che non confina con nulla non e' "
            "un passo della derivazione: e' una riscrittura dell'intera rete.")

    # AD-22 v2.2: `id_{k+1}(x) = id_k(x)` per ogni `x ∈ Pₖ` vale ora **per
    # costruzione**. Con `node_mapping` ritirata, `Pₖ` e' un'intersezione per
    # identificatore: ogni entita' che vi appartiene porta lo stesso nome nei due
    # circuiti, per definizione dell'insieme. Non c'e' piu' niente da verificare.
    #
    # I quattro controlli che stavano qui — dominio della mappa, iniettivita' e i due
    # versi dell'identita' — esistevano tutti e soli per sorvegliare quel campo, e
    # sono stati rimossi con esso (decisione owner del 25/08/2026). Un controllo che
    # non puo' piu' fallire non protegge nulla, e lasciarlo suggerirebbe una
    # superficie che il contratto non ha piu'.
    #
    # **`identity_violation` resta dichiarata in `Cause` e senza produttori.** La
    # tabella delle cause vive in AD-19, che e' spine: rimuoverne una e' un'altra
    # decisione di proprieta', non un effetto collaterale di questa.
    preservate = preserve_set(before, after, operation=operation)

    # AD-22 em.: la massimalita' e' verificata **indipendentemente** dalla
    # `Transform` che la dichiara. «Diverso da `Pₖ`», non «piu' piccolo di»: la
    # causa copre entrambi i versi.
    dichiarate = frozenset(patch.preserve)
    if dichiarate != preservate:
        mancanti = sorted(preservate - dichiarate)
        eccedenti = sorted(dichiarate - preservate)
        return Refusal(
            "preserve_nonmaximal", operation, "operation",
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
