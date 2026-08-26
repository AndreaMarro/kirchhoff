"""`Delta` — che cosa e' diventato che cosa.

Il `TransformResult` di AD-2 v2 porta `PreserveSet + Delta + Boundary + LayoutPatch
+ Equation + Certificate`. Di questi, `Delta` era **nominato due volte e mai
definito**: qui viene definito, e solo per il proprio dominio.

## Che cosa `Delta` e'

Una collezione ordinata di **derivazioni strutturali**: insiemi di entita' in
ingresso, una **riscrittura** del vocabolario strutturale chiuso (`primitives.py`),
insiemi di entita' in uscita.

    {R1, R2}  --fusione_di_componenti-->  {Req}
    {b}       --eliminazione_di_nodo-->   {}

Le due righe qui sopra sono **un solo** passo pedagogico: la riduzione in serie. Il
passo lo nomina il `Certificate`, una volta; il `Delta` nomina le riscritture di cui
e' fatto, una per derivazione (Story 1.2).

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

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .primitives import FORME, PRIMITIVES, Forma, StructuralPrimitive

#: Le entita' che il `CircuitIR` conosce. Non un namespace nuovo: i componenti si
#: identificano col loro `id`, i nodi col loro nome, gli stessi che `IR.nodes` e
#: `Component.id` gia' usano. Sottoinsieme di `SubjectKind` di `refusal.py`, meno
#: `request`, che non e' un'entita' del circuito.
EntityKind = Literal["component", "node"]

ENTITY_KINDS: frozenset[str] = frozenset({"component", "node"})


def _verifica_generi_delle_forme(
    forme: Mapping[str, Forma], generi: frozenset[str]
) -> None:
    """I generi che `primitives.py` nomina sono generi di entita' che esistono qui.

    Il vocabolario delle riscritture non puo' importare `EntityKind`: `delta.py`
    importa `primitives.py`, e l'inverso sarebbe un ciclo. Il genere e' quindi una
    stringa la', e la riconciliazione avviene qui — dove i generi sono definiti.
    Non e' una seconda dichiarazione dello stesso insieme: e' un controllo di una
    dichiarazione contro l'altra, che e' esattamente cio' che E-62 chiede al posto
    della disciplina.
    """
    ignoti = sorted({f.genere for f in forme.values()} - generi)
    if ignoti:
        raise RuntimeError(
            f"il vocabolario delle riscritture nomina generi di entita' che non "
            f"esistono: {ignoti}. I generi sono {', '.join(sorted(generi))}.")


_verifica_generi_delle_forme(FORME, ENTITY_KINDS)


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
    """`inputs --operation--> outputs`. Gli insiemi sono tuple ordinate canonicamente.

    **`operation` e' una riscrittura strutturale, non un passo del Catalogo** (Story
    1.2). Puntava al catalogo pedagogico, ed era il livello sbagliato: `serie` fonde
    due componenti **e** cancella il nodo interno, quindi scrivere `serie` su ciascuna
    delle due derivazioni faceva leggere due passi didattici dove ce n'e' uno — e K-0
    pretende un fotogramma per ogni passo didattico.

    Il passo pedagogico resta **uno solo** e vive in `Certificate.operation`. Da qui e'
    sparito, e non e' una perdita d'informazione: era la stessa cosa scritta due volte
    dentro lo stesso prodotto (E-62). Quale composizione un passo ammette lo dichiara
    il Catalogo (`catalog.COMPOSITION`), e `TransformResult` lo verifica.

    **Il nome vincola la derivazione**, per la forma che `primitives.FORME` gli
    assegna: genere delle entita' ai due capi, quanti ingressi come minimo, quante
    uscite esattamente. Senza quel vincolo i cinque nomi sarebbero decorazioni
    intercambiabili — misurato: `{node:b} --eliminazione_di_nodo--> {node:a}` si
    costruiva, e con esso ogni lineage falsa che rispettasse i soli aggregati.
    """

    operation: StructuralPrimitive
    inputs: tuple[EntityRef, ...]
    outputs: tuple[EntityRef, ...]

    def __post_init__(self) -> None:
        if self.operation not in PRIMITIVES:
            raise ValueError(
                f"riscrittura {self.operation!r} fuori dal vocabolario strutturale "
                f"chiuso. Le riscritture sono {', '.join(sorted(PRIMITIVES))}: "
                "aggiungerne una e' una modifica del vocabolario, non di una "
                "derivazione, e un passo del catalogo pedagogico non e' una di esse.")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError(f"derivazione {self.operation!r} con un ingresso ripetuto")
        if len(set(self.outputs)) != len(self.outputs):
            raise ValueError(f"derivazione {self.operation!r} con un'uscita ripetuta")

        # **La forma che la riscrittura impone**, dalla tabella di `primitives.py`.
        # I duplicati si contestano prima, perche' un ingresso ripetuto e' un difetto
        # della derivazione e non della sua forma, e diagnosticarlo come «ne servono
        # almeno due» nominerebbe la cosa sbagliata.
        forma = FORME[self.operation]
        estranei = sorted(
            {e.kind for e in (*self.inputs, *self.outputs)} - {forma.genere})
        if estranei:
            raise ValueError(
                f"derivazione {self.operation!r} su entita' di genere "
                f"{', '.join(estranei)}: opera su {forma.genere}, e ai due capi. "
                "Nessuna riscrittura trasforma un nodo in un componente.")
        if len(self.inputs) < forma.ingressi_minimi:
            raise ValueError(
                f"derivazione {self.operation!r} con {len(self.inputs)} entita' in "
                f"ingresso: ne vuole almeno {forma.ingressi_minimi}. Sotto quella "
                "soglia la riscrittura afferma qualcosa di diverso da cio' che "
                "il suo nome dichiara.")
        if forma.ingressi_massimi is not None and len(self.inputs) > forma.ingressi_massimi:
            raise ValueError(
                f"derivazione {self.operation!r} con {len(self.inputs)} entita' in "
                f"ingresso: ne ammette al massimo {forma.ingressi_massimi}. Sopra "
                "quella soglia la riscrittura e' un'altra: una sostituzione che "
                "consuma due componenti e ne produce uno e' una FUSIONE, e "
                "chiamarla altrimenti rende i due nomi intercambiabili — cio' che "
                "il vocabolario chiuso esiste per impedire.")
        if len(self.outputs) != forma.uscite:
            raise ValueError(
                f"derivazione {self.operation!r} con {len(self.outputs)} entita' in "
                f"uscita: ne vuole esattamente {forma.uscite}. E' il capo su cui "
                "«un nodo sopravvive» e «nessuno eredita» si distinguono.")

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

        # **La lineage non puo' chiudersi in cerchio.** Le derivazioni di un `Delta`
        # descrivono lo stesso salto `Cₖ → Cₖ₊₁` da piu' punti, non una pipeline: non
        # c'e' un «prima» e un «dopo» fra due riscritture dello stesso passo, e
        # l'ordine canonico e' per contenuto, non per causalita'. Un'entita' prodotta
        # da una riscrittura e consumata da un'altra pretenderebbe quell'ordine, e
        # nulla nel modello lo porta.
        #
        # Con una derivazione sola la condizione non poteva darsi; dai `Delta`
        # multi-derivazione della Story 1.2 e' reale. Misurato prima della guardia:
        # `{R1} --sostituzione--> {R2}` accanto a `{R2} --sostituzione--> {R1}` si
        # costruiva, e `derived_from` rispondeva in cerchio.
        #
        # L'incrocio si cerca fra derivazioni **distinte**: dentro una sola,
        # ingresso e uscita possono coincidere, ed e' la forma con cui AD-22 v2.1
        # vuole scritta l'entita' mutata in luogo.
        # `prodotte - d.outputs` sono le uscite delle **altre** derivazioni: la
        # guardia sopra ha gia' escluso che due ne producano la stessa.
        prodotte = {e for d in ordinate for e in d.outputs}
        for d in ordinate:
            incrocio = (prodotte & set(d.inputs)) - set(d.outputs)
            if incrocio:
                raise ValueError(
                    f"entita' prodotta da una derivazione e consumata da un'altra: "
                    f"{', '.join(sorted(str(e) for e in incrocio))}. Le riscritture "
                    "di un passo non si concatenano: descrivono lo stesso salto, e "
                    "una lineage che si chiude in cerchio non ha origine.")

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
