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
`reroute_scope` e' l'insieme dei rami la cui instradatura e' libera. Nessun numero,
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

    `node_mapping` e' una tupla di coppie e non un `dict` per due ragioni che
    contano entrambe: la struttura resta congelabile insieme al resto, e l'ordine
    e' canonico invece che d'inserimento — E-62 nasce da confronti che dipendevano
    dall'iterazione di una mappa.
    """

    preserve: tuple[EntityRef, ...]
    remove: tuple[EntityRef, ...]
    create: tuple[EntityRef, ...]
    node_mapping: tuple[tuple[str, str], ...]
    reroute_scope: tuple[EntityRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "preserve", _ordinate(self.preserve, "preserve"))
        object.__setattr__(self, "remove", _ordinate(self.remove, "remove"))
        object.__setattr__(self, "create", _ordinate(self.create, "create"))
        object.__setattr__(
            self, "reroute_scope", _ordinate(self.reroute_scope, "reroute_scope"))

        sorgenti = [a for a, _ in self.node_mapping]
        immagini = [b for _, b in self.node_mapping]
        for nome in (*sorgenti, *immagini):
            if not isinstance(nome, str) or not nome:
                raise ValueError(
                    "node_mapping: una mappa fra identificatori, e un identificatore "
                    "vuoto non identifica nulla")
        # AD-22 em.: totale e **iniettiva** sui sopravvissuti. Senza iniettivita' due
        # entita' distinte collasserebbero in una, e `Pₖ` si restringerebbe di
        # conseguenza: e' la stessa autocertificazione che l'emendamento chiude.
        if len(set(sorgenti)) != len(sorgenti):
            raise ValueError("node_mapping: identificatore mappato due volte")
        if len(set(immagini)) != len(immagini):
            raise ValueError(
                "node_mapping: due entita' distinte mappate sullo stesso "
                "identificatore, e la mappatura non e' iniettiva")
        object.__setattr__(self, "node_mapping", tuple(sorted(self.node_mapping)))

    def image_of(self, identifier: str) -> str:
        """L'identificatore in `Cₖ₊₁` di cio' che in `Cₖ` si chiamava `identifier`.

        Chi non compare nella mappa conserva il proprio nome: la mappa dichiara le
        rinomine, non ripete l'identita'.
        """
        for a, b in self.node_mapping:
            if a == identifier:
                return b
        return identifier


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
