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
from .result import Boundary, Certificate, IdentityAttestation, LayoutPatch


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


def _divergenze(before: IR, after: IR) -> dict[EntityRef, frozenset[str]]:
    """Per ogni entita' di `Cₖ` che ha un'immagine in `Cₖ₊₁`, cosa e' cambiato.

    **Un solo predicato d'identita' nel pacchetto.** `Pₖ`, le attestazioni e la
    diagnosi degli identificatori riusati sono tre letture dello stesso confronto:
    scriverlo tre volte lo farebbe divergere nel posto dove nessuno guarda (E-62), e
    la divergenza qui non produce un guasto ma una **falsa accusa** — un'entita'
    dichiarata preservata da un ramo e riusata da un altro.

    Chi non ha immagine in `Cₖ₊₁` non compare: non e' «cambiato», e' sparito, e
    quella e' una domanda del `Delta`, non dell'identita'.

    **Per i nodi il confronto e' vuoto per costruzione, ed e' dichiarato qui perche'
    e' un limite del contratto e non un dettaglio.** Un nodo che sopravvive per nome
    riceve `frozenset()` — nessuna divergenza possibile — quindi entra sempre in `Pₖ`,
    non compare mai fra gli identificatori riusati e non e' mai attestabile. La
    ragione e' che in questo IR un nodo **e'** il proprio nome: non ha attributi, e la
    sua incidenza non e' un suo campo ma una proprieta' derivata dai terminali dei
    componenti.

    La conseguenza va detta, perche' e' l'ipotesi su cui il resto poggia: un
    produttore che consumasse il nodo `b` e ne creasse uno nuovo, con incidenza
    completamente diversa, chiamandolo ancora `b`, otterrebbe `b ∈ Pₖ`. Cio' che lo
    rivela **indirettamente** e' che i componenti attorno cambierebbero terminali, e
    quelli il confronto li vede; cio' che non lo rivela e' il nodo in se'. Un
    discriminante d'incidenza per i nodi e' una modifica del contratto — decide che
    cosa sia l'identita' di un nodo, che nessun documento oggi definisce — ed e'
    registrata in `deferred-work.md`, non decisa qui.

    **I terminali si confrontano ORIENTATI, e su entrambi i lati.**
    `ir/canonical.py` dichiara `resistor`, `capacitor`, `inductor` simmetrici:
    «nessuna di queste differenze dice qualcosa del circuito». Confrontarli per
    uguaglianza sintattica di tupla contraddiceva quel modulo — misurato: due IR
    che `canonicalize` dichiara identici davano `Pₖ` diversi, e un passo che non
    toccava nulla riceveva quattro violazioni. Falsa accusa, sulla superficie
    che la decisione owner del 25/08 conserva per il produttore esterno.

    La regola e' **riusata**, non riscritta: `orienta` vive in `canonical.py` e
    non tocca i generatori, perche' li' l'ordine e' la polarita' e riordinarla
    produrrebbe un circuito diverso che si dichiara uguale.

    La normalizzazione era anche **unilaterale**: `tuple(prima.terminals)` su un
    lato solo, quindi un componente con terminali-lista risultava non preservato
    rispetto a se stesso. Ora entrambi i lati passano da `orienta` e da `tuple`.
    """
    nodi_dopo = frozenset(after.nodes)
    per_id = {c.id: c for c in after.components}
    divergenze: dict[EntityRef, frozenset[str]] = {}

    for e in entities_of(before):
        if e.kind == "node":
            # Un nodo e' il proprio nome: non ha attributi che possano divergere.
            # Sopravvive quando la **sua immagine** esiste in `Cₖ₊₁`.
            if e.id in nodi_dopo:
                divergenze[e] = frozenset()
            continue
        if e.id not in per_id:
            continue
        prima, dopo = before.component(e.id), per_id[e.id]
        atteso = attributes_of(prima)
        atteso["terminals"] = tuple(orienta(prima).terminals)
        osservato = attributes_of(dopo)
        osservato["terminals"] = tuple(orienta(dopo).terminals)
        divergenze[e] = frozenset(
            k for k, v in atteso.items() if osservato[k] != v)

    return divergenze


def _ammessi(operation: TransformationKind | None) -> frozenset[str]:
    """Gli attributi che `operation` puo' cambiare senza perdere l'identita'.

    `operation=None` significa «nessuna mutazione ammessa», che e' la lettura piu'
    stretta e mai quella piu' comoda: chi non dice quale operazione sta misurando
    non ottiene indulgenza.
    """
    return mutable_attributes(operation) if operation is not None else frozenset()


def _perche_diversa(
    cambiati: frozenset[str],
    operation: TransformationKind | None,
) -> str:
    """Quali attributi rendono un'entita' diversa da se stessa, per la diagnosi.

    Si chiama **solo** su un'entita' presente in entrambi i circuiti e fuori da `Pₖ`,
    quindi la differenza esiste: `cambiati <= ammessi` e' falso per definizione di
    quell'insieme. Non c'e' un ramo «nessuna differenza» perche' non c'e' un caso.

    AD-19 pretende che un rifiuto nomini l'elemento coinvolto; K-3 pretende di piu' —
    che la diagnosi si rilegga come Domanda mirata. «`R1` e' un'altra entita'» non lo
    e'; «di `R1` cambia il valore» lo e'.

    **Riceve le divergenze gia' calcolate invece dei due circuiti.** Le ricalcolava,
    ed era una settima corsa di `_divergenze` dentro un controllo che l'aveva appena
    fatta girare: non un costo che qui interessi, ma una seconda strada verso la
    stessa risposta, che e' esattamente la forma che E-62 chiude altrove in questo
    modulo.
    """
    return "cambia " + ", ".join(sorted(cambiati - _ammessi(operation)))


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

    Il confronto vive in `_divergenze`, che e' l'unico predicato d'identita' del
    pacchetto: `Pₖ`, `identity_attestations` e la diagnosi degli identificatori
    riusati sono tre letture dello stesso confronto, mai tre confronti.
    """
    ammessi = _ammessi(operation)
    return frozenset(
        e for e, cambiati in _divergenze(before, after).items()
        if cambiati <= ammessi)


def identity_attestations(
    before: IR,
    after: IR,
    *,
    operation: TransformationKind | None = None,
) -> tuple[IdentityAttestation, ...]:
    """Le preservazioni **non banali**, con la ragione per cui reggono.

    Un'entita' entra in `Pₖ` per una di due strade: o non e' cambiata, e la ragione
    e' leggibile confrontando i due circuiti, oppure e' cambiata **entro la licenza**
    che il Catalogo concede a quella operazione (CV3: preservato non significa
    immutato). La seconda strada e' il caso non banale, e non lascia traccia: chi
    riceve `Pₖ` vede un'entita' preservata e non vede che la sua appartenenza
    dipendeva da una licenza. Un'attestazione la rende leggibile.

    Cio' che **non** e' qui e' altrettanto significativo. Un'entita' cambiata **oltre**
    la licenza non riceve un'attestazione debole: non e' preservata affatto, esce da
    `Pₖ`, e `check_transform` la rifiuta come identificatore riusato. Non esistono
    gradi intermedi fra giustificata e rifiutata, ed e' deliberato — un'attestazione
    che potesse dire «cambiata, ma non troppo» sarebbe il posto dove tornerebbe ad
    abitare l'autocertificazione che AD-22 chiude.

    Ordine canonico: due corse sugli stessi circuiti producono attestazioni uguali e
    ugualmente ordinate, e il `Certificate` che le porta serializza identico.

    **Con `operation=None` il risultato e' `()` sempre, per costruzione.** La
    convenzione e' la stessa di `preserve_set` — chi non dice quale operazione sta
    misurando non ottiene indulgenza — ma qui non produce la lettura piu' stretta:
    la produce **muta**. Nessuna mutazione ammessa significa che ogni entita' cambiata
    esce da `Pₖ`, quindi nessuna preservazione ha avuto bisogno di licenza, quindi non
    c'e' niente da attestare; e un chiamante che dimentica l'argomento riceve un
    insieme vuoto invece di un errore. Il trabocchetto non e' chiuso qui, perche'
    chiuderlo renderebbe `operation` obbligatoria in una funzione sola su quattro. E'
    chiuso a valle: `check_certificate` interroga questa funzione con
    `certificate.operation`, che il `Certificate` porta sempre, quindi un attestato
    reticente viene contestato anche se chi l'ha assemblato ha dimenticato l'argomento.
    """
    ammessi = _ammessi(operation)
    return tuple(sorted(
        IdentityAttestation(e, tuple(sorted(cambiati)))
        for e, cambiati in _divergenze(before, after).items()
        if cambiati and cambiati <= ammessi))


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
    # Quella clausola resta il contratto **di questo controllore** e non e' cambiata.
    # Cio' che e' cambiato e' che un passo intero non arriva piu' fin qui: se
    # l'identificatore e' lo stesso in entrambi i circuiti, `check_transform` rifiuta
    # prima. Un `Delta` conforme a questa riga e' quindi necessario e non sufficiente,
    # e la divergenza fra le due letture e' registrata in `deferred-work.md`.
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
    # entrambi i campi. Come per `check_delta`, e' il contratto di questo controllore
    # e resta vero; il passo intero viene pero' rifiutato prima da `check_transform`,
    # e una patch conforme non lo salva — `test_la_patch_irreprensibile_non_salva_il_passo`. Misurando per id, quell'entita' non era ne' apparsa ne'
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


@dataclass(frozen=True, slots=True, order=True)
class CertificateViolation:
    code: str
    subject: str
    detail: str


def check_certificate(
    certificate: Certificate,
    before: IR,
    after: IR,
) -> tuple[CertificateViolation, ...]:
    """Le attestazioni del `Certificate` contro i due circuiti. Vuoto quando reggono.

    **Il lato mancante del contratto.** `IdentityAttestation` verificava la propria
    forma, `Certificate` la propria coerenza interna e la licenza del Catalogo,
    `TransformResult` che l'entita' attestata fosse fra le preservate. Nessuno dei tre
    vede `Cₖ` e `Cₖ₊₁`, quindi nessuno dei tre poteva chiedere la sola domanda che
    l'attestazione esiste per porre: **e' vero?** Misurato prima di questa funzione,
    con `parallelo` che licenzia `value` e `R1 ∈ Pₖ` per quella licenza, lo stesso
    `TransformResult` accettava tre certificati incompatibili fra loro:
    `attestations=()`, `R1 (symbolic)` e `R1 (terminals, type)`. Un attestato che si
    autocertifica e' precisamente E-65, e AC2 chiede che il `Certificate` **porti**
    l'attestazione, non che possa portarla.

    Il riferimento e' `identity_attestations` sugli stessi due circuiti e sulla
    **stessa** operazione che il certificato dichiara: un controllo che ricalcolasse
    l'identita' per conto proprio sarebbe il secondo predicato che E-62 chiude in
    questo modulo, e la sua divergenza produrrebbe una falsa accusa.

    **Uguaglianza, non inclusione**, come in `check_patch`. I tre versi hanno codici
    distinti perche' dicono cose diverse a chi ripara:

    - `licenza_taciuta` — l'entita' e' preservata **solo** grazie a una licenza, e il
      certificato non lo dice. E' il difetto che AD-22 chiude: una licenza esercitata
      in silenzio non e' distinguibile da un'identita' riusata.
    - `attestazione_infondata` — il certificato giustifica una preservazione che non
      aveva bisogno di giustificazione. Non e' innocuo: chi conta le preservazioni non
      banali conterebbe una licenza che nessuno ha esercitato.
    - `attestazione_discorde` — l'entita' e' attestata sull'attributo sbagliato.
      Leggibile e falsa, la forma che CV1 descrive.

    **Non emette un `Refusal`**, per la ragione che la testa del modulo enuncia:
    AD-19 tiene chiusa l'enumerazione delle cause e non ne assegna una a questo caso.
    Inventarne una sarebbe una modifica dello spine; riusarne una porterebbe l'utente
    a leggere una diagnosi che parla di un'altra cosa.

    Puro: nessuna I/O, nessun orologio, nessuna casualita'.
    """
    dovute = {
        a.entity: a for a in identity_attestations(
            before, after, operation=certificate.operation)}
    dichiarate = {a.entity: a for a in certificate.attestations}
    trovate: list[CertificateViolation] = []

    for e in sorted(set(dovute) - set(dichiarate)):
        trovate.append(CertificateViolation(
            "licenza_taciuta", str(e),
            f"sopravvive a {certificate.operation} solo perche' il Catalogo ne "
            f"dichiara mutabile {', '.join(dovute[e].changed)}, e il certificato "
            "tace: una licenza esercitata in silenzio non e' distinguibile da "
            "un'identita' riusata"))
    for e in sorted(set(dichiarate) - set(dovute)):
        trovate.append(CertificateViolation(
            "attestazione_infondata", str(e),
            f"il certificato ne attesta l'identita' per "
            f"{', '.join(dichiarate[e].changed)}, ma fra i due circuiti nulla di "
            "cio' che comporrebbe una licenza le cambia: e' una preservazione banale, "
            "e attestarla la fa contare fra quelle che hanno avuto bisogno di una"))
    for e in sorted(set(dovute) & set(dichiarate)):
        if dichiarate[e].changed != dovute[e].changed:
            trovate.append(CertificateViolation(
                "attestazione_discorde", str(e),
                f"il certificato attesta {', '.join(dichiarate[e].changed)}; "
                f"fra i due circuiti cambia {', '.join(dovute[e].changed)}"))

    return tuple(trovate)


def check_transform(
    before: IR,
    after: IR,
    operation: TransformationKind,
    patch: LayoutPatch,
    boundary: Boundary | None,
) -> Refusal | None:
    """Boundary, identita' e massimalita'. `None` quando reggono tutti e tre.

    **L'identita' torna, e non e' il controllo che era uscito.** Quello sorvegliava
    `node_mapping` — la mappa fra identificatori — ed e' uscito con essa (AD-22
    v2.2): senza strato di mappatura, `id_{k+1}(x) = id_k(x)` su `Pₖ` e' vero per
    costruzione. Questo verifica la cosa opposta, e non e' vera per costruzione:
    che un'entita' presente in entrambi i circuiti **sia** la stessa entita'. Il
    primo guardava chi e' dentro `Pₖ`; questo guarda chi ci sta per coincidenza di
    nome.

    Gira **prima** che il `TransformResult` sia costruito, e per questo puo' vedere
    un `boundary` assente: `Boundary` si rifiuta di esistere vuoto, quindi chi non e'
    riuscito a costruirlo passa `None` qui e riceve una causa legale invece di
    un'eccezione. Un rifiuto e' un atto di onesta' del sistema; un'eccezione e' un
    guasto (AD-13).

    L'ordine dei tre controlli e' fisso e non e' indifferente: si va dal difetto piu'
    grande al suo sintomo. `empty_boundary` e' la condizione piu' grossolana — un
    passo che non confina con nulla non e' un passo. `identity_violation` viene poi,
    perche' non dipende da nulla di dichiarato e perche' un identificatore riusato
    compromette `Pₖ`, che e' il metro del controllo successivo. `preserve_nonmaximal`
    per ultima: misura una dichiarazione contro quel metro, e nominarla per prima
    farebbe leggere come errore del produttore un difetto della trasformazione.
    """
    if boundary is None:
        return Refusal(
            "empty_boundary", operation, "operation",
            f"{operation}: ∂Tₖ = ∅. Un sottografo che non confina con nulla non e' "
            "un passo della derivazione: e' una riscrittura dell'intera rete.")

    preservate = preserve_set(before, after, operation=operation)

    # **La direzione che AD-22 lasciava aperta, e la ragione per cui viene qui.**
    #
    # La Rule chiude un verso solo — «rifiuta se un'entita' presente in entrambi
    # compare in `create`» — e lo chiude piu' in basso, con `intruse`. L'altro verso
    # e' questo: un'entita' che compare in **entrambi** i circuiti e **non** e' in
    # `Pₖ` porta lo stesso identificatore di una che il passo ha consumato, ed e'
    # un'entita' diversa. L'identificatore e' stato riusato.
    #
    # E' il difetto dell'istruttoria R2-A visto dal lato del contratto: se una
    # trasformazione battezza `R1` la nuova resistenza equivalente, il discriminante
    # v2.1 la tiene fuori da `Pₖ` — necessario, e non sufficiente. Restava
    # rappresentabile come «rimozione piu' creazione» con lineage nel `Delta`, e un
    # passo cosi' e' **leggibile e falso**: chi legge `R1` in `Cₖ₊₁` legge il nome di
    # una cosa che non c'e' piu', e nessuna riga glielo dice. CV1, un bug che si
    # legge come dato.
    #
    # **Prima della massimalita', e non e' indifferente.** `preserve_nonmaximal`
    # misura cio' che il produttore dichiara *contro* `Pₖ`; ma con un identificatore
    # riusato `Pₖ` non e' piu' un riferimento su cui appoggiarsi, ed emettere quella
    # causa nominerebbe un sintomo misurato contro un metro gia' compromesso. Questa
    # non dipende da nulla di dichiarato: si legge nei due circuiti e nell'operazione,
    # cioe' esattamente in cio' che il produttore non controlla.
    #
    # Cio' che una trasformazione deve fare invece e' nel motore, in `_nuovo_id`:
    # identita' **nuova** per l'equivalente, lineage nel `Delta`, e il nome vecchio
    # non torna. La rinomina segue la stessa regola: AD-22 v2.2 la dichiara «una
    # consumata piu' una creata», e non e' un'operazione del contratto corrente.
    #
    # **La diagnosi dice cio' che il controllo constata, non come ci si e' arrivati.**
    # Diceva «{operation} produce un'entita' che riusa l'identificatore di una
    # consumata», e su due dei tre casi che la fanno scattare e' falso. Misurato: su
    # una rinomina del nodo `b` in `z` la diagnosi accusava `R1` di riusare
    # l'identificatore di una consumata, mentre `R1` non e' stata consumata da nessuno
    # — le e' cambiato sotto il nodo che tocca; su una mutazione in luogo, `RL` da 5Ω a
    # 7Ω, idem. Il controllo osserva un identificatore presente in entrambi i circuiti
    # che non nomina la stessa entita': **il riuso e' una delle spiegazioni possibili,
    # non il fatto**. K-3 vuole che la diagnosi si rilegga come Domanda mirata, e una
    # Domanda costruita su una causa presunta manda chi legge a cercare la cosa
    # sbagliata — che e' la falsa accusa, il difetto peggiore di questo prodotto.
    #
    # **Le nomina tutte.** Ne nominava una e taceva sulle altre. Il precedente citato
    # per giustificarlo diceva il contrario: il primo ramo di `preserve_nonmaximal`,
    # qui sotto, elenca per intero mancanti ed eccedenti. `subject` resta la prima in
    # ordine canonico — AD-19 vuole *un* elemento coinvolto e `Refusal.subject` e' uno
    # — ma la diagnosi le porta tutte, perche' chi ripara due entita' divergenti
    # dovendone scoprire una alla volta fa due giri invece di uno.
    riusati = sorted((entities_of(before) & entities_of(after)) - preservate)
    if riusati:
        colpevole = riusati[0]
        divergenze = _divergenze(before, after)
        elenco = ", ".join(
            f"{e} ({_perche_diversa(divergenze[e], operation)})" for e in riusati)
        return Refusal(
            "identity_violation", colpevole.id, colpevole.kind,
            f"{operation}: {len(riusati)} identificator"
            f"{'e compare' if len(riusati) == 1 else 'i compaiono'} in Cₖ e in Cₖ₊₁ "
            f"senza nominare la stessa entita' — {elenco}. Il controllo constata la "
            "divergenza, non la sua causa: un identificatore riusato da un'entita' "
            "nuova, una rinomina e una mutazione in luogo la producono allo stesso "
            "modo. In tutti e tre i casi l'entita' di Cₖ₊₁ ha bisogno di un "
            "identificatore proprio e della propria lineage nel Delta, oppure di una "
            "licenza che il Catalogo dichiari per quell'attributo sotto "
            f"{operation}; tenere il nome fermo fa apparire preservato cio' che non "
            "lo e'.")

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
