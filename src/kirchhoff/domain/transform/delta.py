"""`Delta` — che cosa e' diventato che cosa.

Il `TransformResult` di AD-2 v2 porta `PreserveSet + Delta + Boundary + LayoutPatch
+ Equation + Certificate`. Di questi, `Delta` era **nominato due volte e mai
definito**: qui viene definito, e solo per il proprio dominio.

## Che cosa `Delta` e'

Una collezione ordinata di **derivazioni strutturali**: insiemi di entita' in
ingresso, un'operazione del catalogo chiuso, insiemi di entita' in uscita.

    {R1, R2}  --serie-->  {Req}

## Che cosa `Delta` NON e'

- **Non e' geometria.** Nessuna posizione, nessun ingombro, nessun ordine sul
  canvas, nessun suggerimento di animazione, nessun colore. Quello e' `LayoutPatch`
  e vive in `render/` (AD-18 em., AD-21).
- **Non e' il complemento di `PreserveSet`.** CV1 mostra il difetto che nasce
  quando un insieme viene ricavato dall'altro: un renderer che deduce i preservati
  come «tutto cio' che non e' cambiato» reintroduce l'autocertificazione che AD-22
  ha chiuso, e il verdetto di Gate A resta leggibile diventando falso. `Pₖ` e
  `Delta` si calcolano **entrambi** da `Cₖ` e `Cₖ₊₁`; nessuno dei due si deduce
  dall'altro, e `check` verifica che siano coerenti.
- **Non e' l'identita' ordinaria.** Un'entita' che sopravvive senza essere toccata
  sta in `PreserveSet` e non compare qui. `{R3} -> {R3}` non si scrive.
- **Non e' temporale ne' di dominio.** Una commutazione (`0⁻ → 0⁺`) e un passaggio
  ai fasori non sono derivazioni di entita': la prima ha bisogno di un invariante
  di stato attraverso il confine, il secondo e' una proiezione della stessa rete in
  un'altra algebra. Entrambi si comporranno **accanto** a `Delta`, non dentro.

## Una entita' puo' essere insieme preservata e in uscita

Una fusione puo' assorbire in un sopravvissuto: unendo i nodi `n1` e `n2`, `n1`
resta e `n2` sparisce. `n1` e' in `Pₖ` per definizione (AD-22: `Pₖ` e'
l'intersezione) **e** compare come uscita, perche' e' li' che `n2` e' finito.
Vietarlo costringerebbe a perdere la destinazione della fusione. Cio' che resta
vietato e' il contrario: **un'entita' preservata non puo' essere consumata.**

## Perche' i controlli girano a runtime e non stanno «nel tipo»

CV5: *«Lo stack e' Python senza type checker ... "il vincolo e' nel tipo" non e' una
proprieta' del sistema: e' una convenzione.»* Ogni invariante qui sotto ha quindi una
guardia che solleva e un test che l'ha vista sollevare.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .catalog import CATALOG, TransformationKind

#: Le entita' che il `CircuitIR` conosce. Non un namespace nuovo: i componenti si
#: identificano col loro `id`, i nodi col loro nome, gli stessi che `IR.nodes` e
#: `Component.id` gia' usano. Sottoinsieme di `SubjectKind` di `refusal.py`, meno
#: `request`, che non e' un'entita' del circuito.
EntityKind = Literal["component", "node"]

ENTITY_KINDS: frozenset[str] = frozenset({"component", "node"})


@dataclass(frozen=True, slots=True, order=True)
class EntityRef:
    """Riferimento a un'entita' del circuito. `order=True` per l'ordine canonico."""

    kind: EntityKind
    id: str

    def __post_init__(self) -> None:
        if self.kind not in ENTITY_KINDS:
            raise ValueError(
                f"genere di entita' {self.kind!r} sconosciuto: "
                f"{', '.join(sorted(ENTITY_KINDS))}")
        if not self.id:
            raise ValueError("riferimento a un'entita' senza identificatore")

    def __str__(self) -> str:
        return f"{self.kind}:{self.id}"


@dataclass(frozen=True, slots=True)
class StructuralDerivation:
    """`inputs --operation--> outputs`. Gli insiemi sono tuple ordinate canonicamente."""

    operation: TransformationKind
    inputs: tuple[EntityRef, ...]
    outputs: tuple[EntityRef, ...]

    def __post_init__(self) -> None:
        if self.operation not in CATALOG:
            raise ValueError(
                f"operazione {self.operation!r} fuori dal catalogo chiuso. "
                "Aggiungerne una e' una modifica del catalogo, non di una derivazione.")
        if not self.inputs:
            # Deciso esplicitamente, non per comodita': nel catalogo chiuso non esiste
            # oggi una trasformazione che crei un'entita' senza ascendenza. Se ne
            # comparira' una, questa guardia e' la riga da cambiare, e il test
            # `test_una_derivazione_senza_ingressi_e_rifiutata` e' il posto dove
            # dichiarare il caso nuovo.
            raise ValueError(
                f"derivazione {self.operation!r} senza entita' in ingresso: "
                "una creazione senza ascendenza non ha lineage interrogabile")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError(f"derivazione {self.operation!r} con un ingresso ripetuto")
        if len(set(self.outputs)) != len(self.outputs):
            raise ValueError(f"derivazione {self.operation!r} con un'uscita ripetuta")
        # Ordine canonico imposto alla costruzione: due derivazioni semanticamente
        # uguali sono uguali anche come oggetti, e serializzano identiche.
        object.__setattr__(self, "inputs", tuple(sorted(self.inputs)))
        object.__setattr__(self, "outputs", tuple(sorted(self.outputs)))

    def __str__(self) -> str:
        dentro = ", ".join(str(e) for e in self.inputs)
        fuori = ", ".join(str(e) for e in self.outputs) or "∅"
        return f"{{{dentro}}} --{self.operation}--> {{{fuori}}}"


def _chiave(d: StructuralDerivation) -> tuple:
    """Ordine canonico fra derivazioni: non dipende dall'ordine di inserimento,
    ne' dall'iterazione di un set, ne' dal traversal di chi le ha prodotte."""
    return (tuple((e.kind, e.id) for e in d.inputs),
            d.operation,
            tuple((e.kind, e.id) for e in d.outputs))


@dataclass(frozen=True, slots=True)
class Delta:
    """Collezione ordinata canonicamente di derivazioni strutturali."""

    derivations: tuple[StructuralDerivation, ...] = ()

    def __post_init__(self) -> None:
        ordinate = tuple(sorted(self.derivations, key=_chiave))
        if len(set(_chiave(d) for d in ordinate)) != len(ordinate):
            raise ValueError("derivazione ripetuta identica nello stesso Delta")

        # Un'entita' consumata una volta non puo' essere ingresso di una seconda
        # derivazione: sarebbero due destini incompatibili per lo stesso oggetto.
        visti_in: set[EntityRef] = set()
        for d in ordinate:
            doppi = visti_in & set(d.inputs)
            if doppi:
                raise ValueError(
                    f"entita' consumata due volte nello stesso passo: "
                    f"{', '.join(sorted(str(e) for e in doppi))}")
            visti_in |= set(d.inputs)

        # Due derivazioni non possono creare la stessa entita'.
        visti_out: set[EntityRef] = set()
        for d in ordinate:
            doppi = visti_out & set(d.outputs)
            if doppi:
                raise ValueError(
                    f"entita' prodotta da due derivazioni: "
                    f"{', '.join(sorted(str(e) for e in doppi))}")
            visti_out |= set(d.outputs)

        object.__setattr__(self, "derivations", ordinate)

    # --- interrogabilita' (invariante 8): entrambe le direzioni cadono dal modello,
    #     senza costruire un indice parallelo.

    def what_happened_to(self, entity: EntityRef) -> StructuralDerivation | None:
        """La derivazione che ha consumato `entity`, se e' stata consumata."""
        for d in self.derivations:
            if entity in d.inputs:
                return d
        return None

    def derived_from(self, entity: EntityRef) -> tuple[EntityRef, ...]:
        """Le entita' da cui `entity` deriva. Vuoto se non e' stata prodotta qui."""
        for d in self.derivations:
            if entity in d.outputs:
                return d.inputs
        return ()

    @property
    def consumed(self) -> frozenset[EntityRef]:
        return frozenset(e for d in self.derivations for e in d.inputs)

    @property
    def produced(self) -> frozenset[EntityRef]:
        return frozenset(e for d in self.derivations for e in d.outputs)
