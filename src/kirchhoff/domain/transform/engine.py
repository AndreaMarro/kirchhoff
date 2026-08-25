"""`transform(CircuitIR, params) -> (CircuitIR, TransformResult) | Refusal` (AD-2 em.).

Il catalogo e' un **registro chiuso caricato all'avvio**: `_REGISTRO` si costruisce
al momento dell'import e non espone alcuna funzione per aggiungervi una voce a
runtime. Chiedere un'operazione che non c'e' fallisce **prima di eseguire qualunque
calcolo** — le tre porte in cima a `transform` sono le sue prime righe, non un
controllo a valle del lavoro.

## Le tre porte, che sono tre risposte diverse

«Non esiste», «esiste e non e' applicabile» (FR-43) e «applicabile ma non ancora
scritta». Confonderle costa a chi pianifica, ed e' precisamente cio' che il docstring
di `catalog.py` chiede di non fare. La seconda e' la conseguenza testabile di FR-43 —
*«il sistema rifiuta invece di improvvisare»* — e vive qui, non solo in un insieme
esportato: senza questa porta sarebbe un effetto collaterale del registro incompleto,
e una voce implementata ma non ancora aperta verrebbe eseguita senza che nulla
protesti.

## Perche' quelle tre sollevano invece di restituire un `Refusal`

AD-19 tiene chiusa l'enumerazione delle cause e assegna a questo pacchetto
esattamente tre: `identity_violation`, `preserve_nonmaximal`, `empty_boundary`.
Nessuna dice «questa operazione non esiste» o «questi due resistori non sono in
serie». Un `Refusal` e' un esito di dominio — il sistema ha guardato il circuito e
onestamente non certifica; una richiesta malformata e' invece un difetto di chi
chiama, e degradarla a `sanity` farebbe perdere all'utente la localizzazione che K-3
promette. Finche' lo spine non nomina una causa per il caso, questo modulo solleva e
lo dichiara, invece di scegliersene una.

## I Rifiuti che invece escono, e da dove vengono

Due sono di `domain/transform/check` — le tre cause di AD-19 qui sopra. Gli altri
sono **inoltrati** da `domain/validate`: `Cₖ` gia' rotto e `Cₖ₊₁` che non regge alla
validazione elettrica portano `topology`, `units` o `unsolvable`, che restano cause
di chi le emette. Il criterio della storia — *«il `CircuitIR` risultante supera la
validazione elettrica»* — non discende dai tre controlli strutturali: una riduzione
legittima puo' lasciare un nodo di grado uno, e senza la validazione del prodotto
usciva un `Certificate` completo su un circuito irrisolvibile.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from fractions import Fraction
from inspect import signature
from types import MappingProxyType

from ..ir import IR, REFERENCE_NODE, Component
from ..refusal import Refusal
from ..validate import validate
from .catalog import (
    CATALOG,
    CatalogOpening,
    TransformationKind,
    transformations_supported,
)
from .check import (
    check_boundary,
    check_delta,
    check_patch,
    check_transform,
    preserve_set,
)
from .delta import Delta, EntityRef, StructuralDerivation
from .result import Boundary, Certificate, Equation, LayoutPatch, TransformResult

#: I controlli eseguiti prima che il prodotto esista, nell'ordine in cui girano. Il
#: `Certificate` li elenca perche' siano **verificabili**, non perche' siano
#: rassicuranti: un controllo che non ha girato non compare (E-65).
#:
#: I due estremi sono la validazione elettrica, e non sono lo stesso controllo.
#: Quella su `Cₖ` viene **prima** di tutto: un passo applicato a un circuito gia'
#: rotto produrrebbe altrimenti una diagnosi che nomina il passo invece del difetto
#: preesistente — una falsa accusa. Quella su `Cₖ₊₁` e' il criterio della storia
#: («il `CircuitIR` risultante supera la validazione elettrica») e viene per ultima,
#: quando c'e' un prodotto da validare.
CONTROLLI: tuple[str, ...] = (
    "validazione elettrica di Cₖ",
    "boundary",
    "identita'",
    "massimalita' di preserve",
    "coerenza del Delta",
    "coerenza della LayoutPatch",
    "contenuto del boundary",
    "validazione elettrica di Cₖ₊₁",
)


class AttestazioneIncoerente(AssertionError):
    """Il motore ha prodotto un'attestazione incoerente con cio' che ha fatto.

    **Un solo invariante, tre canali.** Il proprietario l'ha enunciato cosi':

        cio' che appare e sparisce nel `CircuitIR`
          <-> cio' che dice il `Delta`
          <-> cio' che dice la `LayoutPatch`

    e il `Boundary` e' il quarto vertice — dice dove i tre si toccano col resto
    della rete. Tre eccezioni scorrelate suggerirebbero tre problemi diversi; sono
    lo stesso, visto da tre canali, e le sottoclassi servono solo a nominare quale
    ha parlato.

    **Non e' un `Refusal`, ed e' deliberato.** Un Rifiuto e' un atto di onesta' del
    sistema verso una richiesta che non si puo' soddisfare; qui la richiesta era
    soddisfacibile. AD-13 chiama guasto esattamente questo, e un guasto non si
    traveste da diagnosi di dominio. Non si aggiunge una causa a `Cause` per
    ospitarlo: l'enumerazione di AD-19 e' chiusa e vive nello spine.
    """


class DeltaIncoerente(AttestazioneIncoerente):
    """Il `Delta` emesso non regge `check_delta`: la lineage contraddice i circuiti."""


class PatchIncoerente(AttestazioneIncoerente):
    """`create` o `remove` contraddicono cio' che e' apparso e sparito fra i circuiti.

    **La lettura alternativa e' stata considerata.** Il progetto tratta gia' una
    patch non conforme come `Refusal` — `preserve_nonmaximal` — quindi si poteva
    seguire quel precedente. Non si e' fatto perche' il difetto e' della stessa
    famiglia di quello del `Delta`, e perche' ospitarlo in `Cause` richiederebbe una
    causa nuova in un'enumerazione chiusa. Se un produttore esterno arrivera' a
    fornire patch, la classificazione andra' rivista: e' scritto qui perche' non si
    scopra dopo.
    """


class BoundaryIncoerente(AttestazioneIncoerente):
    """`∂Tₖ` nomina entita' che non sopravvivono, o che non confinano col passo."""


def _identificatori_attesi(corpo: Callable[..., object]) -> int:
    """Quanti identificatori la voce del catalogo richiede, oltre al circuito.

    Derivato dalla firma invece che dichiarato, perche' una seconda dichiarazione da
    tenere allineata a mano e' esattamente E-62: due fonti per la stessa cosa
    divergono nel posto dove nessuno guarda. Qui la fonte e' la firma, e non puo'
    divergere da se stessa.
    """
    parametri = list(signature(corpo).parameters.values())
    return sum(
        1 for p in parametri[1:]
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        and p.default is p.empty
    )


def _resistore(ir: IR, cid: str) -> Component:
    c = ir.component(cid)
    if c.type != "resistor":
        raise ValueError(
            f"{cid}: {c.type}, e la riduzione vale fra resistori. "
            "Un'impedenza complessa e' un'altra voce del catalogo.")
    return c


def _nuovo_id(ir: IR, primo: str, secondo: str) -> str:
    """Identita' **nuova** per l'equivalente, e deterministica.

    Non si riusa il nome di una consumata: riusarlo la farebbe rientrare in `Pₖ` per
    coincidenza d'identificatore, ed e' precisamente il difetto dell'istruttoria
    R2-A. Il suffisso cresce finche' il nome e' libero, cosi' il risultato non
    dipende da quali componenti esistono gia'.
    """
    base = f"{primo}{secondo}eq"
    presi = {c.id for c in ir.components}
    nome = base
    while nome in presi:
        nome += "_"
    return nome


def _prodotto(
    prima: IR,
    dopo: IR,
    operazione: TransformationKind,
    consumati: tuple[EntityRef, ...],
    prodotto: EntityRef,
    rimossi: tuple[EntityRef, ...],
    boundary: Boundary,
    equazione: Equation,
) -> tuple[IR, TransformResult] | Refusal:
    """Assembla i sei membri, dopo che `check_transform` ha dato il proprio esito.

    `boundary` arriva gia' costruito: le due riduzioni qui sotto ne hanno sempre uno,
    perche' una fusione confina per definizione con i nodi che le restano attorno.
    `empty_boundary` non e' percio' irraggiungibile — e' raggiungibile da dove deve
    esserlo, cioe' da `check_transform`, che e' il controllore e riceve anche
    `boundary` dichiarati da altri produttori.

    **La validazione elettrica gira qui e non in `transform`** perche' e' qui che il
    `Certificate` nasce: un attestato che elenca un controllo eseguito da un'altra
    funzione sarebbe vero per convenzione e non per costruzione, e E-65 dice
    precisamente che un componente non certifica se stesso asserendolo. I due
    Rifiuti che ne escono portano una causa di `domain/validate` — `topology`,
    `units`, `unsolvable` — perche' e' `domain/validate` a emetterli: questo modulo
    li inoltra, non se li attribuisce, e AD-19 resta rispettato senza cause nuove.
    """
    ingresso = validate(prima)
    if isinstance(ingresso, Refusal):
        return ingresso

    preservate = preserve_set(prima, dopo, operation=operazione)
    patch = LayoutPatch(
        preserve=tuple(sorted(preservate)),
        remove=rimossi,
        create=(prodotto,),
        reroute_scope=(prodotto, *boundary.entities),
    )

    rifiuto = check_transform(prima, dopo, operazione, patch, boundary)
    if rifiuto is not None:
        return rifiuto

    # **Il Delta attraversa il proprio controllore, e lo fa QUI.** Prima non lo
    # attraversava mai: `check_delta` esisteva nel pacchetto con zero consumatori in
    # produzione, e i sei membri potevano raccontare storie incompatibili sulla stessa
    # entita' — `LayoutPatch.remove` nominava il nodo assorbito, il `Delta` no.
    #
    # Il punto e' questo e non un altro per la stessa ragione che il docstring qui
    # sopra da' alla validazione elettrica: e' qui che il `Certificate` nasce, e un
    # attestato che elenca un controllo eseguito altrove sarebbe vero per convenzione
    # invece che per costruzione (E-65).
    # Il terzo lato dell'invariante: `create` e `remove` contro i due circuiti.
    # Sta qui accanto al controllo del Delta perche' e' lo stesso attestato che
    # nasce, e perche' l'incoerenza fra i due canali e' proprio cio' che il
    # controllo del Delta da solo non vedeva.
    guasti_patch = check_patch(patch, prima, dopo)
    if guasti_patch:
        raise PatchIncoerente(
            f"{operazione}: la LayoutPatch emessa viola il proprio controllore — "
            + "; ".join(f"{v.code} su {v.subject} ({v.detail})" for v in guasti_patch))

    guasti_boundary = check_boundary(boundary, patch, prima, dopo)
    if guasti_boundary:
        raise BoundaryIncoerente(
            f"{operazione}: il boundary emesso viola il proprio controllore — "
            + "; ".join(f"{v.code} su {v.subject} ({v.detail})" for v in guasti_boundary))

    delta = Delta((StructuralDerivation(operazione, consumati, (prodotto,)),))
    violazioni = check_delta(delta, prima, dopo, operation=operazione)
    if violazioni:
        raise DeltaIncoerente(
            f"{operazione}: il Delta emesso viola il proprio controllore — "
            + "; ".join(f"{v.code} su {v.subject} ({v.detail})" for v in violazioni))

    # Il criterio della storia: «il `CircuitIR` risultante supera la validazione
    # elettrica». I tre controlli strutturali non lo implicano — una riduzione puo'
    # lasciare un nodo di grado uno, che e' un ramo aperto — e senza questa riga il
    # prodotto usciva **certificato** e non risolvibile.
    uscita = validate(dopo)
    if isinstance(uscita, Refusal):
        return uscita

    return dopo, TransformResult(
        preserve=preservate,
        delta=delta,
        boundary=boundary,
        layout_patch=patch,
        equation=equazione,
        certificate=Certificate(operazione, CONTROLLI),
    )


def _serie(ir: IR, primo: str, secondo: str) -> tuple[IR, TransformResult] | Refusal:
    """`R1 (a,b)` e `R2 (b,c)` diventano una equivalente `(a,c)`, e `b` sparisce."""
    a, b = _resistore(ir, primo), _resistore(ir, secondo)
    comune = set(a.terminals) & set(b.terminals)
    if len(comune) != 1:
        raise ValueError(
            f"{primo} e {secondo} condividono {len(comune)} nodi: la serie ne vuole "
            "esattamente uno.")
    nodo = comune.pop()
    if nodo == REFERENCE_NODE:
        # Elettricamente la coppia e' in serie: la corrente che attraversa la prima
        # attraversa la seconda. Fondere le due elimina pero' il nodo comune, e quel
        # nodo e' il **riferimento** — il potenziale rispetto a cui ogni tensione del
        # circuito e' definita. Il prodotto non sarebbe un circuito con un difetto:
        # non sarebbe un circuito. Prima di questa guardia il caso moriva due strati
        # piu' in basso, nel costruttore dell'IR, con «manca il nodo di riferimento»:
        # una diagnosi vera che non nominava ne' l'operazione ne' la coppia.
        raise ValueError(
            f"{primo} e {secondo} si toccano nel nodo di riferimento {nodo}: "
            "la serie elimina il nodo comune, e quello non si elimina perche' e' il "
            "potenziale rispetto a cui ogni tensione e' definita. Serve prima un "
            "altro riferimento, che non e' una Trasformazione del catalogo.")
    tocca = [c.id for c in ir.components if nodo in c.terminals]
    if len(tocca) != 2:
        raise ValueError(
            f"il nodo {nodo} ha grado {len(tocca)} ({', '.join(sorted(tocca))}): "
            "in serie ci stanno due componenti soli, altrimenti la corrente si "
            "divide e la somma delle resistenze non e' l'equivalente.")

    estremi = (
        next(t for t in a.terminals if t != nodo),
        next(t for t in b.terminals if t != nodo),
    )
    eq = Component.of(
        _nuovo_id(ir, primo, secondo), "resistor", estremi,
        a.value.amount + b.value.amount, f"({a.symbolic} + {b.symbolic})")
    dopo = _senza(ir, (primo, secondo), (nodo,), eq)

    return _prodotto(
        ir, dopo, "serie",
        # **Il nodo comune e' consumato, non solo rimosso.** `rimossi` lo nominava
        # gia'; `consumati` no, e i due canali raccontavano storie diverse sulla
        # stessa entita'. La lineage che `delta.py` promette — «e' li' che n2 e'
        # finito» — era interrogabile per i componenti e muta per il nodo assorbito:
        # `what_happened_to(node:b)` rispondeva `None` su un nodo che la fusione ha
        # inghiottito. Assorbire e' consumare.
        consumati=(EntityRef("component", primo), EntityRef("component", secondo),
                   EntityRef("node", nodo)),
        prodotto=EntityRef("component", eq.id),
        rimossi=(EntityRef("component", primo), EntityRef("component", secondo),
                 EntityRef("node", nodo)),
        boundary=Boundary((EntityRef("node", estremi[0]),
                           EntityRef("node", estremi[1]))),
        # Il soggetto e' l'IDENTIFICATORE dell'equivalente, non la sua espressione.
        # Passando `eq.symbolic` l'uguaglianza diceva «(R1 + R2) = R1 + R2»: vera,
        # tautologica, e muta sul simbolo che il passo introduce. Chi legge la
        # derivazione deve poter risalire da `R1R2eq` alla formula che lo definisce.
        equazione=Equation(eq.id, f"{a.symbolic} + {b.symbolic}"),
    )


def _parallelo(ir: IR, primo: str, secondo: str) -> tuple[IR, TransformResult] | Refusal:
    """`R1 (a,b)` e `R2 (a,b)` diventano una equivalente sugli stessi due nodi."""
    a, b = _resistore(ir, primo), _resistore(ir, secondo)
    if set(a.terminals) != set(b.terminals):
        raise ValueError(
            f"{primo} {a.terminals} e {secondo} {b.terminals} non stanno fra gli "
            "stessi due nodi: non sono in parallelo.")

    ra, rb = a.value.amount, b.value.amount
    eq = Component.of(
        _nuovo_id(ir, primo, secondo), "resistor", a.terminals,
        Fraction(ra * rb, ra + rb),
        f"({a.symbolic}·{b.symbolic} / ({a.symbolic} + {b.symbolic}))")
    dopo = _senza(ir, (primo, secondo), (), eq)

    return _prodotto(
        ir, dopo, "parallelo",
        consumati=(EntityRef("component", primo), EntityRef("component", secondo)),
        prodotto=EntityRef("component", eq.id),
        rimossi=(EntityRef("component", primo), EntityRef("component", secondo)),
        boundary=Boundary((EntityRef("node", a.terminals[0]),
                           EntityRef("node", a.terminals[1]))),
        equazione=Equation(
            eq.id,
            f"{a.symbolic}·{b.symbolic} / ({a.symbolic} + {b.symbolic})"),
    )


def _senza(ir: IR, componenti: tuple[str, ...], nodi: tuple[str, ...],
           aggiunto: Component) -> IR:
    """`Cₖ₊₁`: meno cio' che e' stato consumato, piu' l'equivalente — e **derivato**.

    Tre campi non si copiano invariati, e copiarli produceva un IR che il proprio
    costruttore rifiutava — cioe' un'eccezione al posto di uno dei due esiti che AD-2
    em. ammette, su circuiti perfettamente validi.

    **`source_kind` diventa `generated`.** Dice da dove l'IR e' stato *letto*, e
    `Cₖ₊₁` non e' stato letto da nessuna parte: e' stato calcolato qui. Tenere
    `image` era la contraddizione piu' visibile — lo schema pretende allora che
    **ogni** componente porti la propria area di provenienza (FR-5), e l'equivalente
    non ne ha una: non compare in nessuna fotografia, perche' non c'e' mai stato.
    Inventargliela sarebbe peggio che non averla, e lo schema lo dice per primo.

    **La provenienza cade con la sorgente.** Un componente che sopravvive la perde
    perche' `Cₖ₊₁` non e' piu' un IR fotografico, e lo schema vieta un'area di
    provenienza su una sorgente che non e' un'immagine. Non e' una perdita:
    l'ancoraggio vive su `C₀`, dove la conferma dell'utente avviene, e il `Delta`
    tiene il filo fra i due. `provenance` non e' fra gli `IDENTITY_ATTRIBUTES` —
    «dice da dove il componente e' stato letto, non che cosa e'» — quindi nessuna
    entita' esce da `Pₖ` per questo.

    **Le richieste seguono il proprio bersaglio.** Una `Request` su un componente che
    la riduzione consuma non puo' viaggiare su `Cₖ₊₁`: il costruttore la respinge, e
    ha ragione — quel componente li' non esiste. Ridirigerla sull'equivalente sarebbe
    molto peggio di un'eccezione: la tensione ai capi di `R1` **non e'** la tensione
    ai capi di `R1+R2`, e la domanda dell'utente cambierebbe di nascosto. Resta
    quindi su `Cₖ`, che e' il circuito in cui il suo bersaglio esiste, e non si perde:
    `Delta.what_happened_to(EntityRef("component", "R1"))` restituisce la derivazione
    che l'ha consumata, ed e' cosi' che la risalita ritrova la grandezza chiesta dopo
    aver risolto il circuito ridotto. La lineage e' interrogabile per costruzione
    (invariante 8 di `Delta`): non serve un settimo membro del risultato.
    """
    rimasti = tuple(
        c if c.provenance is None else replace(c, provenance=None)
        for c in ir.components if c.id not in componenti
    )
    superstiti = {c.id for c in rimasti} | {aggiunto.id}
    return IR(
        ir.ir_version, ir.domain, "generated",
        tuple(n for n in ir.nodes if n not in nodi),
        (*rimasti, aggiunto),
        tuple(r for r in ir.requests if r.target in superstiti),
        ir.omega,
    )


#: Il registro chiuso, costruito all'import. Non esiste una `register()`: estenderlo
#: e' una modifica del catalogo, non una chiamata.
#: Le implementazioni, per nome. **Chiuso anche a runtime, non solo a parole.**
#:
#: Il docstring del modulo dichiarava «non espone alcuna funzione per aggiungervi una
#: voce a runtime»: vero, e insufficiente — un `dict` non ha bisogno che gliela si
#: esponga. `_REGISTRO["serie"] = altra` sostituiva l'implementazione della serie
#: senza attraversare nessuna delle quattro porte di `transform`, sotto un docstring
#: che lo dichiarava chiuso.
#:
#: `MUTABLE_ATTRIBUTES` era gia' blindato cosi' in `catalog.py`. Il registro che
#: decide **quale codice viene eseguito** no: stessa classe di difetto, chiusa in un
#: modulo e lasciata aperta in quello accanto.
#:
#: Nessun caso legittimo di registrazione tardiva esiste — il registro e' un letterale
#: costruito una volta all'import, non un punto di estensione — quindi blindarlo non
#: toglie niente a nessuno.
_IMPLEMENTAZIONI: dict[str, Callable[..., tuple[IR, TransformResult] | Refusal]] = {
    "serie": _serie,
    "parallelo": _parallelo,
}

_REGISTRO: Mapping[str, Callable[..., tuple[IR, TransformResult] | Refusal]] = (
    MappingProxyType(_IMPLEMENTAZIONI))


def implemented() -> frozenset[str]:
    """Le voci del catalogo che hanno gia' un'implementazione.

    Il catalogo e' chiuso e completo; le implementazioni arrivano una storia alla
    volta. Tenere i tre insiemi distinti e interrogabili evita che «non ancora
    scritta», «non applicabile» e «non esiste» si confondano — sono tre risposte
    diverse a chi pianifica, e `transform` le tiene su tre porte separate.

    Non e' `SUPPORTED`, e non deve diventarlo per costruzione: l'insieme applicabile
    lo decide FR-43, questo lo decide il lavoro fatto. Che oggi `implemented()`
    contenga meno di `SUPPORTED` e' un debito dichiarato, non un difetto nascosto —
    `partitore_di_tensione` e' applicabile e senza corpo, e chi la chiede riceve
    esattamente quella risposta.
    """
    return frozenset(_REGISTRO)


def transform(
    ir: IR,
    operation: TransformationKind,
    *args: str,
    opening: CatalogOpening | None = None,
) -> tuple[IR, TransformResult] | Refusal:
    """La firma di AD-2 em. Pura: nessuna I/O, nessun orologio, nessuna casualita'.

    Le tre porte in cima sono **tre risposte diverse**, e tenerle distinte e' il
    punto di FR-43. Nell'ordine in cui si attraversano:

    1. **«non esiste»** — il nome e' fuori dal vocabolario chiuso. Fallisce prima di
       qualunque calcolo, e il vocabolario non si estende mai.
    2. **«esiste e non e' applicabile»** — il nome sta nel vocabolario ma non fra le
       Trasformazioni applicabili. FR-43: *«una trasformazione non nel Catalogo non e'
       applicabile: il sistema rifiuta invece di improvvisare»*. Questa porta e' la
       ragione per cui `SUPPORTED` esiste; senza di essa la conseguenza testabile di
       FR-43 sarebbe solo un effetto collaterale del registro incompleto, e una voce
       implementata ma non ancora aperta verrebbe eseguita senza che nulla protesti.
       `opening` e' la registrazione che apre il Catalogo, esibita a ogni chiamata:
       non c'e' uno stato globale da mettere in una configurazione.
    3. **«applicabile, non ancora scritta»** — il corpo manca. E' l'unica delle tre
       che il tempo risolve, e per questo non deve somigliare alle altre due.

    Nessuna delle tre e' un `Refusal`: AD-19 assegna a questo pacchetto tre cause, e
    nessuna dice «questa operazione non si puo' eseguire». Sono pero' tipi di
    eccezione **diversi** — `ValueError` per cio' che non si potra' fare,
    `NotImplementedError` per cio' che non si e' ancora fatto — cosi' che chi chiama
    possa distinguerle senza leggere un messaggio.
    """
    if operation not in CATALOG:
        raise ValueError(
            f"operazione {operation!r} fuori dal catalogo chiuso: "
            f"{', '.join(sorted(CATALOG))}. Il catalogo si carica all'avvio e non "
            "si estende a runtime.")
    applicabili = transformations_supported(opening)
    if operation not in applicabili:
        raise ValueError(
            f"{operation}: nel vocabolario ma non applicabile. Applicabili oggi: "
            f"{', '.join(sorted(applicabili))}. Il sistema rifiuta invece di "
            "improvvisare (FR-43); ad aprire il Catalogo e' una decisione registrata "
            "(`CatalogOpening`), non una scelta di implementazione.")
    if operation not in _REGISTRO:
        raise NotImplementedError(
            f"{operation}: applicabile ma senza implementazione. "
            f"Implementate finora: {', '.join(sorted(_REGISTRO))}.")

    # **La quarta porta: gli argomenti.** Le tre sopra riguardano l'operazione; questa
    # riguarda cio' che le si passa, ed era l'unica scoperta. Misurato: un
    # identificatore inesistente usciva come `KeyError('RX')` da `IR.component`, e
    # un'arita' sbagliata come `TypeError: _serie() missing 1 required positional
    # argument`. Un quarto tipo che il contratto non dichiara, senza operazione ne'
    # diagnosi — e col nome della funzione privata dentro il messaggio, cioe' una
    # fuga di implementazione che racconta al chiamante come e' fatto dentro invece
    # di che cosa ha sbagliato.
    #
    # Entrambi sono «cio' che non si potra' fare» e vanno quindi in `ValueError`,
    # come le altre due porte di quella classe.
    corpo = _REGISTRO[operation]
    attesi = _identificatori_attesi(corpo)
    if len(args) != attesi:
        raise ValueError(
            f"{operation}: vuole {attesi} identificatori, ne ha ricevuti "
            f"{len(args)}{' (' + ', '.join(args) + ')' if args else ''}.")

    # Tutte le voci del catalogo corrente nominano **componenti**. Se una voce futura
    # nominasse nodi, il Catalogo dovrebbe dichiarare il genere degli argomenti:
    # dedurlo qui sarebbe un'euristica dentro un punto che deve restare deterministico.
    noti = {c.id for c in ir.components}
    ignoti = [a for a in args if a not in noti]
    if ignoti:
        raise ValueError(
            f"{operation}: {', '.join(ignoti)} non "
            f"{'e' if len(ignoti) == 1 else 'sono'} un componente di questo circuito. "
            f"Componenti: {', '.join(sorted(noti))}.")

    return corpo(ir, *args)
