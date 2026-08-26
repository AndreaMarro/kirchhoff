"""`LayoutIR` — dove ogni cosa sta, per **uno** stato visuale.

AD-21 enumera quattro rappresentazioni disgiunte: `CircuitIR` (cosa il circuito e'),
**`LayoutIR` (dove ogni cosa sta)**, `TransformOverlay` (cosa la trasformazione
annota), `InteractionState` (cosa l'utente sta facendo). *«Nessuno dei quattro
contiene un riferimento a un altro se non per identificatore. Nessuno scrive in un
altro.»*

## Perche' sta in `render/` e non in `domain/`

AD-8 da' al `LayoutIR` un solo scrittore, `render/layout`, e scrive **«mai
`domain/`»**. La ragione e' AD-18 em.: dalla v2 il dominio *«non sa nemmeno cosa sia
una posizione»*. Un tipo che porta coordinate non puo' quindi vivere sotto `domain/`
neppure come dichiarazione — sarebbe il collasso che AD-21 chiude, ottenuto
rispettando ogni parola.

Il verso opposto e' invece lecito e necessario: questo modulo importa `EntityRef` da
`domain/`, perche' un layout deve nominare le stesse entita' che il `LayoutPatch`
nomina, o la coppia non e' congiungibile. `check_boundaries.py` vieta
`domain/ → render/`, non `render/ → domain/`.

## Perche' `Fraction` e non `float`

Non e' la regola del dominio — questo non e' dominio — ma SM-20 e AD-35: il
rendering dev'essere deterministico *«stessi byte»*, e VCER confronta due posizioni
per stabilire se il prodotto continua a esistere. Un `0.1 + 0.2` dentro l'operando
di quel confronto e' rumore binario dentro un oracolo esatto.

## Che cosa questo modulo NON decide

Il renderer. La Story 1.3 rende **osservabile** uno stato visuale, non lo disegna:
non c'e' un autolayout, non c'e' un applicatore di `LayoutPatch`, non c'e' una
serializzazione. Quelli sono 1.4 e 1.7, e inventarli qui vorrebbe dire scegliere
l'algoritmo di piazzamento in una storia che dichiara di non farlo.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ...domain.identity import IdentityKind, conia, verifica
from ...domain.transform import EntityRef

#: Il genere di questa entita' nel vocabolario chiuso di `domain/identity`. Nominato
#: una volta e riusato, invece di ripetere `"lay"` a ogni chiamata.
_LAYOUT: IdentityKind = "lay"


@dataclass(frozen=True, slots=True, order=True)
class Placement:
    """Dove **una** entita' sta. `order=True` per l'ordine canonico.

    L'entita' e' un `EntityRef` e non una stringa nuda per la stessa ragione per cui
    lo e' nel `LayoutPatch`: `component:R1` e `node:R1` sono due entita' diverse, e
    un layout che le confondesse piazzerebbe il filo dove sta il resistore.
    """

    entity: EntityRef
    x: Fraction
    y: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.entity, EntityRef):
            raise TypeError(
                f"piazzamento di {type(self.entity).__name__} invece di EntityRef: "
                "un layout nomina le entita' del circuito, con lo stesso vocabolario "
                "che il `LayoutPatch` usa, o le due non sono congiungibili.")
        for nome, valore in (("x", self.x), ("y", self.y)):
            if not isinstance(valore, Fraction):
                raise TypeError(
                    f"{self.entity}: coordinata {nome} di tipo "
                    f"{type(valore).__name__}, serve una Fraction. VCER confronta "
                    "due posizioni per decidere se il prodotto continua a esistere "
                    "(SM-14), e un float ci porta dentro rumore binario.")


@dataclass(frozen=True, slots=True)
class LayoutIR:
    """Uno stato visuale, immutabile, con identita' propria.

    ## L'identificatore

    `Consistency Conventions`, dalla v2.1: prefisso `lay_`, *«che senza identita' non
    [e'] citabile da evidenza, replay ed eval»*. E' un ULID, come le convenzioni
    chiedono: `render/layout` ha un orologio — glielo iniettano — quindi due layout
    dello stesso stato visuale restano **due**, e ordinano per istante. Il
    `LayoutPatch` riceve il proprio `patch_` con la stessa regola, ma al deposito
    (`PatchStore`), perche' chi lo produce e' `transform` e AD-2 le vieta l'orologio.

    Che siano due e non uno e' il punto della ritenzione: un identificatore derivato
    dal contenuto darebbe lo stesso nome a due stati visuali identici, e
    `ProofGraph.nodo_di` smetterebbe di essere una funzione.

    ## Che cosa NON porta

    **Non porta l'identificatore del nodo che lo possiede.** La relazione e' scritta
    una volta sola, sul nodo (AD-8 v2.1: *«Il nodo porta l'identificatore del proprio
    layout, mai la struttura»*), e il verso inverso e' un indice che `ProofGraph`
    deriva. Scriverla ai due capi sarebbe E-62 — la stessa cosa scritta due volte,
    tenuta allineata da chi modifica — su una relazione che deve reggere un gate.
    """

    identifier: str
    placements: tuple[Placement, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", verifica(self.identifier, _LAYOUT))
        for p in self.placements:
            if not isinstance(p, Placement):
                raise TypeError(
                    f"{type(p).__name__} fra i piazzamenti invece di Placement")
        if not self.placements:
            raise ValueError(
                f"{self.identifier}: uno stato visuale senza alcun piazzamento non "
                "e' uno stato visuale. Conservarlo darebbe a VCER un operando su "
                "cui ogni confronto riesce, cioe' continuita' perfetta per vuoto.")
        entita = [p.entity for p in self.placements]
        if len(set(entita)) != len(entita):
            doppie = sorted({str(e) for e in entita if entita.count(e) > 1})
            raise ValueError(
                f"{self.identifier}: {', '.join(doppie)} piazzata piu' di una volta. "
                "Due posizioni per la stessa entita' rendono `p_k(x)` ambiguo, e "
                "VCER lo legge come operando.")
        object.__setattr__(self, "placements", tuple(sorted(self.placements)))

    @staticmethod
    def nuovo(
        placements: tuple[Placement, ...], *, istante: int, casualita: bytes
    ) -> LayoutIR:
        """Conia il `lay_` e costruisce. L'orologio si inietta, non si legge.

        Stessa disciplina di `ClockPort` (AD-17): l'istante e l'entropia entrano
        dalla firma, cosi' che un replay con gli stessi ingressi dia gli stessi
        identificatori e un test possa fermare il tempo.

        `casualita` sono **dieci byte nuovi a ogni chiamata** — vedi il docstring di
        `domain.identity`. A entropia costante due layout coniati nello stesso
        millisecondo prendono lo stesso `lay_`, e il `LayoutStore` solleva «gia'
        depositato» accusando chi deposita di un difetto di chi ha scelto l'entropia.
        Un test che ferma l'orologio puo' fissare anche l'entropia, perche' li' gli
        istanti sono distinti per costruzione.
        """
        return LayoutIR(conia(_LAYOUT, istante, casualita), placements)

    def posizione(self, entita: EntityRef) -> Placement:
        """Il piazzamento di `entita`, o `KeyError`. E' `p_k(x)` di SM-14."""
        for p in self.placements:
            if p.entity == entita:
                return p
        raise KeyError(entita)

    def entita(self) -> frozenset[EntityRef]:
        """Le entita' piazzate. Il dominio su cui `p_k` e' definita."""
        return frozenset(p.entity for p in self.placements)

