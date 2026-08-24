"""Schema dell'IR: versionato, con unità, con provenienza.

L'IR è l'unico contratto fra stadi (AD-1). Perché regga, tre cose devono essere
impossibili da sbagliare, non solo scoraggiate:

**Nessun numero nudo.** Una grandezza fisica è magnitudine *più* unità. Finché il
valore di un componente era una `Fraction`, dieci ohm e dieci farad erano lo stesso
oggetto, e nulla impediva a uno stadio a valle di leggere una capacità come una
resistenza. L'unità non sta accanto al valore: sta dentro il tipo, ed è imposta dal
tipo di componente. Un resistore in farad non si costruisce.

**Versione semantica.** `ir_version` dice se un IR salvato ieri è leggibile oggi.
`"1.0"` non lo dice: non distingue una correzione da un cambio di formato.

**Provenienza dove serve, e solo dove serve.** Quando la sorgente è un'immagine ogni
componente porta l'area da cui è stato letto, altrimenti la conferma dell'utente non
ha nulla da ancorare (FR-5). Quando la sorgente non è un'immagine, un'area di
provenienza è inventata — ed è peggio di nessuna.

Nessuna I/O, nessun orologio, nessuna casualità: questo modulo sta sotto `domain/`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

ComponentType = Literal[
    "resistor",
    "capacitor",
    "inductor",
    "voltage_source_dc",
    "current_source_dc",
    "voltage_source_ac",
]

Quantity = Literal[
    "voltage",
    "current",
    "time_constant",
    "initial_value",
    "final_value",
    "root_1",
    "root_2",
]

SourceKind = Literal["netlist", "latex", "image", "generated"]

REFERENCE_NODE = "0"

#: Le sorgenti da cui un IR può nascere. Chiusa.
SOURCE_KINDS: tuple[str, ...] = ("netlist", "latex", "image", "generated")

#: Unità SI imposta da ogni tipo di componente. Non è una convenzione di scrittura:
#: è il vincolo che impedisce di scambiare una capacità per una resistenza.
EXPECTED_UNIT: dict[str, str] = {
    "resistor": "ohm",
    "capacitor": "farad",
    "inductor": "henry",
    "voltage_source_dc": "volt",
    "voltage_source_ac": "volt",
    "current_source_dc": "ampere",
}

#: Componenti il cui valore è una grandezza fisica strettamente positiva.
POSITIVE_VALUED: frozenset[str] = frozenset({"resistor", "capacitor", "inductor"})

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True, slots=True)
class Magnitude:
    """Una grandezza fisica: quanto, e di che cosa. Mai l'uno senza l'altra."""

    amount: Fraction
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Fraction):
            raise TypeError(
                f"magnitudine {type(self.amount).__name__}, serve una Fraction: "
                "un float porta rumore binario dentro un oracolo esatto")
        if not self.unit:
            raise ValueError("grandezza senza unità: SI internamente, mai un numero nudo")


@dataclass(frozen=True, slots=True)
class Provenance:
    """Area della sorgente da cui il componente è stato letto, normalizzata in [0,1].

    Normalizzata e non in pixel: un ritaglio o un ridimensionamento della sorgente
    non deve invalidare l'ancoraggio.
    """

    x: Fraction
    y: Fraction
    width: Fraction
    height: Fraction

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"area di provenienza con lato non positivo "
                             f"({self.width} x {self.height})")
        if self.x < 0 or self.y < 0 or self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("riquadro di provenienza fuori dalla sorgente: "
                             "le coordinate sono normalizzate in [0,1]")


@dataclass(frozen=True, slots=True)
class Component:
    id: str
    type: ComponentType
    terminals: tuple[str, str]
    value: Magnitude
    symbolic: str
    phase_steps: int = 0
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.value, Magnitude):
            raise TypeError(
                f"{self.id}: valore senza unità ({type(self.value).__name__}). "
                "Una grandezza fisica è magnitudine più unità, sempre.")
        attesa = EXPECTED_UNIT[self.type]
        if self.value.unit != attesa:
            raise ValueError(
                f"{self.id}: un {self.type} espresso in {self.value.unit}, "
                f"attesa l'unità {attesa}")
        if self.terminals[0] == self.terminals[1]:
            raise ValueError(f"{self.id}: terminali coincidenti ({self.terminals[0]})")
        if self.type in POSITIVE_VALUED and self.value.amount <= 0:
            raise ValueError(
                f"{self.id}: valore non positivo per {self.type} ({self.value.amount})")
        if self.phase_steps and self.type != "voltage_source_ac":
            raise ValueError(f"{self.id}: sfasamento su un {self.type}, che non ne ha uno")

    @staticmethod
    def of(
        cid: str,
        ctype: ComponentType,
        terminals: tuple[str, str],
        amount: Fraction,
        symbolic: str,
        *,
        phase_steps: int = 0,
        provenance: Provenance | None = None,
    ) -> Component:
        """Costruisce con l'unità che il tipo impone. Il numero non resta mai nudo."""
        return Component(cid, ctype, terminals, Magnitude(amount, EXPECTED_UNIT[ctype]),
                         symbolic, phase_steps, provenance)


@dataclass(frozen=True, slots=True)
class Request:
    id: str
    quantity: Quantity
    target: str


@dataclass(frozen=True, slots=True)
class IR:
    ir_version: str
    domain: str
    source_kind: SourceKind
    nodes: tuple[str, ...]
    components: tuple[Component, ...]
    requests: tuple[Request, ...]
    #: Pulsazione in rad/s. Zero fuori dal regime sinusoidale.
    omega: Fraction = field(default_factory=lambda: Fraction(0))

    def __post_init__(self) -> None:
        if not _SEMVER.match(self.ir_version):
            raise ValueError(
                f"ir_version {self.ir_version!r}: serve una versione semantica "
                "nella forma MAGGIORE.MINORE.CORREZIONE")
        if self.source_kind not in SOURCE_KINDS:
            raise ValueError(
                f"sorgente {self.source_kind!r} sconosciuta. "
                f"Attese: {', '.join(SOURCE_KINDS)}.")
        if not isinstance(self.omega, Fraction):
            raise TypeError(f"pulsazione {type(self.omega).__name__}, serve una Fraction")
        if REFERENCE_NODE not in self.nodes:
            raise ValueError("manca il nodo di riferimento")

        known = set(self.nodes)
        da_immagine = self.source_kind == "image"
        for c in self.components:
            for t in c.terminals:
                if t not in known:
                    raise ValueError(f"{c.id}: terminale su nodo sconosciuto {t}")
            if da_immagine and c.provenance is None:
                raise ValueError(
                    f"{c.id}: manca l'area di provenienza, obbligatoria quando la "
                    "sorgente è un'immagine")
            if not da_immagine and c.provenance is not None:
                raise ValueError(
                    f"{c.id}: area di provenienza su una sorgente {self.source_kind}. "
                    "Una provenienza inventata è peggio di nessuna provenienza.")

        ids = {c.id for c in self.components}
        if len(ids) != len(self.components):
            # La soluzione è indicizzata per id: due componenti omonimi si
            # sovrascriverebbero, e il secondo sparirebbe senza che nulla protesti.
            visti: set[str] = set()
            doppi = sorted({c.id for c in self.components
                            if c.id in visti or visti.add(c.id)})  # type: ignore[func-returns-value]
            raise ValueError(f"identificatori di componente ripetuti: {', '.join(doppi)}")
        for r in self.requests:
            if r.target not in ids:
                raise ValueError(f"{r.id}: grandezza richiesta su componente inesistente {r.target}")
        if any(c.type == "voltage_source_ac" for c in self.components) and self.omega <= 0:
            raise ValueError("regime sinusoidale senza pulsazione positiva")

    def component(self, cid: str) -> Component:
        for c in self.components:
            if c.id == cid:
                return c
        raise KeyError(cid)
