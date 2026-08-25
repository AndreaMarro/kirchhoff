"""`TransformResult` — cio' che una Trasformazione produce oltre al circuito.

AD-2 em.: `transform(CircuitIR, params) -> (CircuitIR, TransformResult) | Refusal`.
Il secondo membro **non e' un disegno**: `Drawing` e' stato ritirato il 15 agosto
(AD-18 em.). La Trasformazione dice *cosa cambia*; il renderer dice *come appare*.
Confonderli rimetterebbe il `preserve set` nelle mani di chi disegna, che e'
esattamente cio' che AD-22 chiude.

## I sei membri, e perche' nessuno e' opzionale

AD-22: *«Ogni campo e' non-vuoto o il prodotto non e' costruibile, non solo
`Certificate`.»* Un `TransformResult` a cui manca un membro non e' un risultato
parziale: e' un risultato che non si puo' verificare, e uno stadio a valle lo
leggerebbe come «niente da controllare» invece che come «controllo mancante».

| Membro | Che domanda risponde |
|---|---|
| `preserve` | che cosa e' sopravvissuto identico (`Pₖ`) |
| `delta` | che cosa e' diventato che cosa |
| `boundary` | dove il sottografo toccato confina col resto (`∂Tₖ`) |
| `layout_patch` | che cosa il renderer deve conservare, togliere, creare |
| `equation` | l'uguaglianza che giustifica il passo |
| `certificate` | quali controlli sono stati eseguiti, e su che cosa |

## Perche' `LayoutPatch` sta nel dominio senza violare AD-1

I suoi campi nominano **entita', non coordinate**: `preserve`, `remove`, `create`
sono insiemi di identificatori, `node_mapping` e' una mappa fra identificatori,
`reroute_scope` delimita cio' che il renderer puo' reinstradare. Nessun numero,
nessuna posizione. Il dominio non sa cosa sia un pixel — e dalla v2 non sa nemmeno
cosa sia una posizione (AD-18 em., AD-21).

Il tipo lo rende difficile da sbagliare: ogni campo e' `EntityRef` o `str`, mai
`int` ne' `Fraction`. Difficile non basta pero': CV5 ricorda che lo stack e' Python
senza type checker, quindi la guardia c'e' comunque, e un test l'ha vista sollevare.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CATALOG, TransformationKind
from .delta import Delta, EntityRef


def _ordinate(entita: tuple[EntityRef, ...], campo: str) -> tuple[EntityRef, ...]:
    """Ordine canonico e nessun duplicato: due patch semanticamente uguali sono
    uguali anche come oggetti, e serializzano identiche."""
    for e in entita:
        if not isinstance(e, EntityRef):
            raise TypeError(
                f"{campo}: {type(e).__name__} invece di EntityRef. Un `LayoutPatch` "
                "nomina entita', non coordinate: un numero qui sarebbe geometria "
                "nel dominio (AD-18 em., AD-21).")
    if len(set(entita)) != len(entita):
        raise ValueError(f"{campo}: entita' ripetuta")
    return tuple(sorted(entita))


@dataclass(frozen=True, slots=True)
class LayoutPatch:
    """Che cosa il renderer deve conservare, togliere e creare. Solo identificatori.

    **`node_mapping` e' stata ritirata (AD-22 v2.2).** Il campo esisteva per
    dichiarare rinomine, ma le clausole della v2 e della v2.1 lo rendevano
    inutilizzabile: `Pₖ` e' preso dopo la mappa, quindi un nodo mappato con successo
    entra in `Pₖ`, e li' l'identita' senza tolleranza gli vieta un nome diverso.
    L'unica mappa che attraversava il controllore aveva sorgente inesistente, cioe'
    era un riferimento a nulla.

    Nel contratto corrente la preservazione richiede identita' semantica stabile
    **e** identificatore semantico stabile: `rinomina != preservazione`. Una
    trasformazione che fonde, sostituisce o ricostruisce un'entita' usa
    `consume`/`create` piu' la lineage nel `Delta`. Il campo non e' sostituito da un
    altro nome finche' non esiste un caso d'uso concreto.
    """

    preserve: tuple[EntityRef, ...]
    remove: tuple[EntityRef, ...]
    create: tuple[EntityRef, ...]
    #: **L'unita' semantica di questo campo e' DIFFERITA alla Story 1.4.**
    #:
    #: Il docstring lo descriveva come «l'insieme dei rami la cui instradatura e'
    #: libera», mentre il motore vi scrive il componente creato piu' i **nodi** del
    #: boundary: due letture che non coincidono, e nemmeno il produttore interno
    #: rispettava quella dichiarata. La descrizione e' stata resa fedele al fatto —
    #: «delimita cio' che il renderer puo' reinstradare» — invece di continuare a
    #: contraddirlo.
    #:
    #: La domanda di accettazione, da rispondere in 1.4 e non prima:
    #:
    #:     Qual e' l'unita' semantica contenuta in `reroute_scope`: componenti,
    #:     nodi, branch/edge renderizzabili, o altro?
    #:
    #: Non e' oziosa: FR-38 lo usa come vincolo NORMATIVO del renderer — «il numero
    #: di elementi con coordinate cambiate e' limitato allo `reroute_scope`
    #: dichiarato» — quindi un renderer che lo rispetti ha bisogno di sapere che cosa
    #: sta contando. `check_patch` verifica gia' cio' che e' verificabile senza la
    #: risposta: nessun fantasma, insieme non vuoto.
    reroute_scope: tuple[EntityRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "preserve", _ordinate(self.preserve, "preserve"))
        object.__setattr__(self, "remove", _ordinate(self.remove, "remove"))
        object.__setattr__(self, "create", _ordinate(self.create, "create"))
        object.__setattr__(
            self, "reroute_scope", _ordinate(self.reroute_scope, "reroute_scope"))


@dataclass(frozen=True, slots=True)
class Boundary:
    """`∂Tₖ` — le entita' su cui il sottografo trasformato tocca il resto della rete.

    Non e' un dettaglio di presentazione: e' cio' che dice **dove guardare** per
    sapere che la trasformazione e' locale. Un `boundary` vuoto significherebbe che
    il sottografo non confina con nulla, cioe' che la trasformazione ha riscritto
    la rete intera spacciandola per un passo — ed e' rifiutato (`empty_boundary`).
    """

    entities: tuple[EntityRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", _ordinate(self.entities, "boundary"))
        if not self.entities:
            raise ValueError(
                "boundary vuoto: un sottografo che non confina con nulla non e' un "
                "passo, e' una riscrittura (AD-22, `empty_boundary`)")


@dataclass(frozen=True, slots=True)
class Equation:
    """L'uguaglianza che giustifica il passo, in forma simbolica.

    Simbolica e non numerica di proposito: FR-13 e AD-4 vogliono che il testo
    mostrato porti **segnaposto** risolti a valle dai risultati calcolati, mai cifre
    scelte da chi scrive il testo. Qui il dominio dichiara la relazione; chi
    renderizza sostituisce.
    """

    subject: str
    expression: str

    def __post_init__(self) -> None:
        if not self.subject:
            raise ValueError("equazione senza soggetto: non si sa cosa definisce")
        if not self.expression:
            raise ValueError(f"{self.subject}: equazione senza espressione")

    def __str__(self) -> str:
        return f"{self.subject} = {self.expression}"


@dataclass(frozen=True, slots=True)
class Certificate:
    """Quali controlli sono stati eseguiti, su quale operazione, con quale esito.

    E-65, dall'error ledger: *«un componente non certifica se stesso asserendolo»*.
    Il `Certificate` non dichiara «valido»: elenca i controlli **eseguiti**. Un
    controllo che non ha girato non compare, e la sua assenza si vede.
    """

    operation: TransformationKind
    checks: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.operation not in CATALOG:
            raise ValueError(
                f"certificato per l'operazione {self.operation!r}, fuori dal "
                "catalogo chiuso")
        if not self.checks:
            raise ValueError(
                f"{self.operation}: certificato senza alcun controllo eseguito. "
                "Un attestato vuoto si legge come «tutto a posto» e non lo e'.")
        if len(set(self.checks)) != len(self.checks):
            raise ValueError(f"{self.operation}: controllo elencato due volte")
        object.__setattr__(self, "checks", tuple(sorted(self.checks)))


@dataclass(frozen=True, slots=True)
class TransformResult:
    """`PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate`."""

    preserve: frozenset[EntityRef]
    delta: Delta
    boundary: Boundary
    layout_patch: LayoutPatch
    equation: Equation
    certificate: Certificate

    def __post_init__(self) -> None:
        # AD-22: ogni campo non-vuoto o il prodotto non e' costruibile. `boundary` e
        # `certificate` si difendono da soli; qui restano `preserve` e `delta`, che
        # sono contenitori e potrebbero arrivare vuoti senza protestare.
        if not self.preserve:
            raise ValueError(
                "TransformResult con `preserve` vuoto: conservare zero prende VCER "
                "perfetto e il kill criterion si autocertifica (AD-22)")
        if not self.delta.derivations:
            raise ValueError(
                "TransformResult con `delta` vuoto: un passo che non deriva nulla "
                "non e' un passo")

        # **`layout_patch` non era in nessuna delle due liste.** Il docstring di
        # AD-22 dichiara «ogni campo e' non-vuoto o il prodotto non e' costruibile,
        # non solo Certificate», e `boundary` e `certificate` si difendono da soli —
        # ma una `LayoutPatch((), (), (), ())` interamente vuota si costruiva senza
        # proteste, e uno stadio a valle l'avrebbe letta come «niente da conservare,
        # togliere o creare».
        if not (self.layout_patch.preserve or self.layout_patch.remove
                or self.layout_patch.create):
            raise ValueError(
                "TransformResult con `layout_patch` vuota: una patch che non "
                "conserva, non toglie e non crea non descrive alcun passo (AD-22).")

        # **`Pₖ` e' scritto due volte dentro lo stesso prodotto**, e nessun
        # controllore li confrontava: `check_transform` vede la patch, mai il
        # risultato. Il motore li teneva allineati per disciplina, riempiendoli dalla
        # stessa variabile — che e' esattamente il gesto che E-62 descrive: la stessa
        # cosa scritta due volte, tenuta uguale da chi scrive e non da un controllo.
        if frozenset(self.layout_patch.preserve) != self.preserve:
            solo_qui = sorted(self.preserve - frozenset(self.layout_patch.preserve))
            solo_patch = sorted(frozenset(self.layout_patch.preserve) - self.preserve)
            raise ValueError(
                "TransformResult: `preserve` e `layout_patch.preserve` divergono. "
                f"Solo nel risultato: {', '.join(str(e) for e in solo_qui) or 'nessuna'}. "
                f"Solo nella patch: {', '.join(str(e) for e in solo_patch) or 'nessuna'}.")

        # Il `Certificate` attesta i controlli di **un'operazione**; le derivazioni
        # del `Delta` ne nominano una. Se non e' la stessa, l'attestato certifica un
        # passo diverso da quello compiuto.
        operazioni = {d.operation for d in self.delta.derivations}
        if operazioni != {self.certificate.operation}:
            raise ValueError(
                f"TransformResult: il certificato attesta l'operazione "
                f"«{self.certificate.operation}», il Delta ne deriva "
                f"{', '.join(sorted(f'«{o}»' for o in operazioni))}.")

        # --- le altre coppie di canali ---------------------------------------
        #
        # La prima chiusura si fermava a `preserve` e all'operazione: due coppie su
        # sei. L'argomento che l'aveva motivata — «`Pₖ` e' scritto due volte dentro
        # lo stesso prodotto e nessuno li confronta» — vale parola per parola per
        # **cio' che sparisce**, scritto in `delta.consumed` e in `patch.remove`, e
        # per **cio' che nasce**, scritto in `delta.produced` e in `patch.create`.
        #
        # Tutti questi invarianti sono verificabili **senza i circuiti**, che e'
        # esattamente il livello a cui questa difesa vive: il motore li produce
        # coerenti perche' i controllori girano contro `Cₖ` e `Cₖ₊₁`, ma un prodotto
        # assemblato da fuori non attraversa quei controllori.
        consumate = self.delta.consumed
        prodotte = self.delta.produced

        # Una preservata non puo' essere consumata: due canali che affermano
        # l'opposto sulla stessa entita'.
        contraddette = sorted(consumate & self.preserve)
        if contraddette:
            raise ValueError(
                "TransformResult: "
                f"{', '.join(str(e) for e in contraddette)} "
                "compare fra le preservate e fra le consumate dal Delta.")

        # Cio' che sparisce, scritto una volta sola.
        rimosse = frozenset(self.layout_patch.remove)
        if consumate != rimosse:
            raise ValueError(
                "TransformResult: `delta.consumed` e `layout_patch.remove` divergono. "
                f"Solo nel Delta: {', '.join(str(e) for e in sorted(consumate - rimosse)) or 'nessuna'}. "
                f"Solo nella patch: {', '.join(str(e) for e in sorted(rimosse - consumate)) or 'nessuna'}.")

        # Cio' che nasce, scritto una volta sola. Si sottrae `preserve` perche' una
        # fusione puo' atterrare su un'entita' preservata — e' il caso che
        # `check_delta` ammette esplicitamente — e quella non e' una creazione.
        create = frozenset(self.layout_patch.create)
        nate = prodotte - self.preserve
        if nate != create:
            raise ValueError(
                "TransformResult: cio' che il Delta produce e cio' che la patch crea "
                f"divergono. Solo nel Delta: {', '.join(str(e) for e in sorted(nate - create)) or 'nessuna'}. "
                f"Solo nella patch: {', '.join(str(e) for e in sorted(create - nate)) or 'nessuna'}.")

        # `∂Tₖ` sta dentro cio' che sopravvive: e' dove il sottografo tocca il resto
        # della rete, e cio' che non sopravvive e' dentro il sottografo, non al confine.
        fuori = sorted(frozenset(self.boundary.entities) - self.preserve)
        if fuori:
            raise ValueError(
                "TransformResult: il boundary nomina "
                f"{', '.join(str(e) for e in fuori)}, che il prodotto non conserva.")

        # L'equazione definisce cio' che il passo produce, non un simbolo qualunque.
        if self.equation.subject not in {e.id for e in prodotte}:
            raise ValueError(
                f"TransformResult: l'equazione definisce «{self.equation.subject}», "
                f"che nessuna derivazione produce.")
