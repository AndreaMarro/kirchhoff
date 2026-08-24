"""Il catalogo chiuso delle Trasformazioni, nel dominio.

I nomi esistevano gia' in `eval/transformations.py`, che si dichiara «insieme
**chiuso**» e annota: *«Il Catalogo vero ... nasce con la Story 2.6 e dovra'
riconciliarsi con questa lista»*. Non puo' essere quella la fonte: `domain/` non
importa nulla fuori da se' (AD-1, recinto 1), quindi il catalogo autoritativo vive
qui e la lista di `eval/` diventa il riflesso.

La riconciliazione non e' una convenzione: `tests/test_delta.py` confronta i due
insiemi e fallisce se divergono. Un catalogo scritto due volte prima o poi diverge,
e il posto dove diverge e' invisibile (E-62 dell'error ledger).

## Tre cose distinte, e confonderle costa

- **Il vocabolario** (`CATALOG`) — i sedici nomi che una derivazione puo' portare.
  Chiuso per sempre: non lo si estende a runtime (AD-2).
- **Le applicabili** (`SUPPORTED`) — le tre dell'MVP. Un nome del vocabolario che
  non e' qui **esiste** e **non e' eseguibile**, e il sistema rifiuta invece di
  improvvisare (FR-43). Si apre solo con una decisione registrata: `CatalogOpening`.
- **Le implementate** (`engine.implemented()`) — quelle che hanno gia' un corpo.
  «Non ancora scritta» e «non esiste» sono risposte diverse a chi pianifica.

Puro: nessuna I/O, nessun orologio, nessuna casualita'. Anche la data di una
decisione di apertura entra come dato: qui non si legge un orologio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from types import MappingProxyType
from typing import Literal

TransformationKind = Literal[
    # riduzioni di rete
    "serie",
    "parallelo",
    "stella_triangolo",
    # ripartizioni
    "partitore_di_tensione",
    "partitore_di_corrente",
    # leggi costitutive
    "legge_di_ohm",
    "legge_di_ohm_fasoriale",
    "impedenza_complessa",
    # transitori
    "circuito_equivalente_a_t0",
    "circuito_equivalente_a_regime",
    "resistenza_equivalente_di_thevenin",
    "costante_di_tempo",
    "equazione_caratteristica",
    "radici_caratteristiche",
    # trifase
    "circuito_monofase_equivalente",
    "sfasamento_di_fase",
]

CATALOG: frozenset[str] = frozenset({
    "serie",
    "parallelo",
    "stella_triangolo",
    "partitore_di_tensione",
    "partitore_di_corrente",
    "legge_di_ohm",
    "legge_di_ohm_fasoriale",
    "impedenza_complessa",
    "circuito_equivalente_a_t0",
    "circuito_equivalente_a_regime",
    "resistenza_equivalente_di_thevenin",
    "costante_di_tempo",
    "equazione_caratteristica",
    "radici_caratteristiche",
    "circuito_monofase_equivalente",
    "sfasamento_di_fase",
})


#: Gli attributi che compongono l'identita' sostanziale di un componente. Non e'
#: l'elenco dei campi di `Component`: `provenance` dice da dove il componente e'
#: stato *letto*, non che cosa *e'*, e un ritaglio diverso non lo rende un altro
#: componente.
IDENTITY_ATTRIBUTES: tuple[str, ...] = (
    "type", "terminals", "value", "symbolic", "phase_steps",
)

#: **Il discriminante di AD-22 v2.1.** Per ciascuna operazione, gli attributi che
#: possono cambiare mentre l'identita' dell'entita' sopravvive.
#:
#: L'insieme predefinito e' **vuoto**: chi non dichiara nulla non muta nulla. Cosi'
#: una `R1` da 10 Ω che dopo una riduzione in parallelo vale 6⅔ Ω **non e'**
#: preservata — e' una rimozione piu' una creazione che ne ha riusato il nome, e
#: come tale deve comparire nel `Delta`.
#:
#: Perche' qui e non nel controllore: il discriminante lo dichiara **il Catalogo**,
#: mai la `Transform` misurata. Chi e' misurato non definisce il proprio
#: riferimento (AD-22, istruttoria R2-A del 24/08/2026).
#:
#: `serie` e `parallelo` non dichiarano nulla: fondono, non modificano in luogo.
#: Un'operazione futura che deve poterlo fare — la disattivazione di un generatore,
#: per esempio — dichiara **qui** l'attributo che le serve, e il controllo lo
#: consente per quella operazione soltanto. E' la riga da cambiare, e
#: `test_un_attributo_dichiarato_mutabile_lascia_l_entita_preservata` il posto dove
#: dichiarare il caso nuovo.
_MUTABILI: dict[str, frozenset[str]] = {nome: frozenset() for nome in sorted(CATALOG)}

#: La dichiarazione e' esposta come **vista di sola lettura**. `CATALOG` e
#: `SUPPORTED` sono `frozenset`; un `dict` ordinario avrebbe lasciato il
#: discriminante d'identita' riscrivibile con un'assegnazione — cioe' avrebbe
#: consentito di cambiare *senza alcuna decisione* il riferimento rispetto a cui
#: `Pₖ` e' misurato, nel modulo che dichiara il vocabolario chiuso per sempre.
#: Chi e' misurato non definisce il proprio riferimento (AD-22 v2.1): nemmeno
#: assegnando a una chiave. La riga da cambiare per dichiarare un attributo
#: mutabile e' `_MUTABILI` qui sopra, in un commit, non a runtime.
MUTABLE_ATTRIBUTES: MappingProxyType[str, frozenset[str]] = MappingProxyType(_MUTABILI)


def mutable_attributes(operation: str) -> frozenset[str]:
    """Gli attributi mutabili dichiarati da `operation`. Vuoto se non dichiara nulla.

    Solleva se l'operazione e' fuori dal catalogo: chiedere il discriminante di
    un'operazione che non esiste e' un errore di programmazione, non un caso di
    dominio, e rispondere «nessuno» lo renderebbe silenzioso.
    """
    if operation not in CATALOG:
        raise ValueError(
            f"operazione {operation!r} fuori dal catalogo chiuso: "
            "non ha attributi mutabili perche' non esiste.")
    return MUTABLE_ATTRIBUTES[operation]


# Il catalogo e la dichiarazione non possono divergere: una voce senza
# dichiarazione avrebbe discriminante indefinito, e la si leggerebbe come «tutto
# mutabile» o «niente mutabile» a seconda di chi la interroga.
if set(MUTABLE_ATTRIBUTES) != CATALOG:  # pragma: no cover - invariante di import
    raise RuntimeError(
        "il catalogo e la dichiarazione degli attributi mutabili sono divergenti")


# --- FR-43: il Catalogo e' chiuso, e la sua apertura e' una decisione registrata ---
#
# Il **vocabolario** e' chiuso e non si estende mai: `CATALOG` e' definitivo, e
# `transform` rifiuta un nome che non vi appartiene prima di qualunque calcolo.
#
# Le Trasformazioni **applicabili** sono un suo sottoinsieme. L'MVP ne supporta
# *«esattamente tre: serie, parallelo, partitore di tensione»*, e SM-C5 misura quel
# numero: deve restare tre finche' il kill criterion di Gate A non e' superato,
# perche' espandere il catalogo e' *«il modo piu' naturale per far salire VVDR
# senza aver dimostrato la continuita' visuale»* — cioe' per ottimizzare la cosa
# sbagliata proprio dove il prodotto vive o muore.
#
# Un caso di `reference-set` cita anche i nomi non applicabili, e non e' una
# contraddizione: **descrivere** un percorso risolutivo non e' eseguirlo.


def _dentro_il_vocabolario(nomi: frozenset[str], che_cosa: str) -> frozenset[str]:
    """Rifiuta ogni nome fuori dal vocabolario chiuso.

    Un solo predicato per i due punti che decidono chi e' applicabile — l'insieme
    dell'MVP e cio' che una decisione apre. E-62: la parte di un gate che decide
    cosa **non** controllare va calcolata con lo stesso predicato del gate,
    altrimenti i due si separano nel posto dove nessuno guarda.
    """
    fuori = nomi - CATALOG
    if fuori:
        raise ValueError(
            f"{che_cosa}: nomi fuori dal vocabolario chiuso: {', '.join(sorted(fuori))}. "
            "Una decisione apre il Catalogo, non lo estende (AD-2).")
    return nomi


#: Le tre dell'MVP. Un nome fuori di qui **esiste** nel vocabolario e **non e'
#: applicabile**: sono due risposte diverse, e confonderle e' precisamente cio' che
#: porta a improvvisare invece di rifiutare (FR-43).
SUPPORTED: frozenset[str] = _dentro_il_vocabolario(
    frozenset({"serie", "parallelo", "partitore_di_tensione"}),
    "trasformazioni applicabili dell'MVP")


_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True, slots=True)
class CatalogOpening:
    """La decisione registrata che rende applicabili altre Trasformazioni (FR-43).

    *«L'espansione del Catalogo richiede la decisione registrata che il kill
    criterion e' passato — non e' una scelta di implementazione. La registrazione
    contiene almeno: la misura di VCER e SM-18 sui due bracci del confronto, il
    corpus su cui e' stata presa, chi ha deciso e la data. Una registrazione priva
    di uno di questi campi non apre il Catalogo.»*

    L'incompletezza ha due forme e vanno chiuse entrambe: un campo **assente** e' un
    `TypeError` alla costruzione, un campo **presente e vuoto** e' un `ValueError`.
    La seconda e' quella che passerebbe inosservata, ed e' la ragione per cui le
    stringhe vuote non sono tollerate.

    `opens` nomina cio' che diventa applicabile e deve stare nel vocabolario: una
    decisione **apre** il Catalogo, non lo estende.

    `decided_on` e' un **giorno del calendario** in forma `AAAA-MM-GG` che **arriva
    da fuori**. Il dominio non legge orologi (AD-2): una registrazione che si datasse
    da sola sarebbe prodotta dal codice invece che dalla decisione, ed e' la decisione
    che deve essere registrata. La forma da sola non basta pero': `2026-13-99` la
    rispetta e non e' un giorno, e una decisione datata in un mese che non esiste non
    e' stata presa in alcun momento. Si verifica quindi la **forma** con l'espressione
    regolare — `date.fromisoformat` accetta anche altre sintassi ISO 8601 — e poi
    l'**esistenza** del giorno. `fromisoformat` interpreta una stringa: non e' un
    orologio, e nessuna riga di questo modulo chiede che ore sono.

    `opens` deve aprire **qualcosa**: una registrazione che nomina solo Trasformazioni
    gia' applicabili non apre il Catalogo, e accettarla produrrebbe una decisione
    archiviata come se avesse avuto un effetto che non ha avuto. E' la stessa forma
    dell'insieme vuoto, e riceve la stessa risposta.

    Le misure sono `Fraction` come ogni grandezza del dominio: un `float` porterebbe
    rumore binario dentro il numero che decide se il kill criterion e' passato.
    """

    vcer_arm_a: Fraction
    vcer_arm_b: Fraction
    sm18_arm_a: Fraction
    sm18_arm_b: Fraction
    corpus: str
    decided_by: str
    decided_on: str
    opens: frozenset[str]

    def __post_init__(self) -> None:
        for nome, misura in (
            ("vcer_arm_a", self.vcer_arm_a), ("vcer_arm_b", self.vcer_arm_b),
            ("sm18_arm_a", self.sm18_arm_a), ("sm18_arm_b", self.sm18_arm_b),
        ):
            if not isinstance(misura, Fraction):
                raise TypeError(
                    f"{nome}: {type(misura).__name__}, serve una Fraction. La misura "
                    "che apre il Catalogo non porta rumore binario.")
        for nome, testo in (("corpus", self.corpus), ("decided_by", self.decided_by)):
            if not testo:
                raise ValueError(
                    f"decisione di apertura senza {nome}: una registrazione priva di "
                    "uno di questi campi non apre il Catalogo (FR-43)")
        if not _DATA_ISO.match(self.decided_on):
            raise ValueError(
                f"decisione di apertura datata {self.decided_on!r}: serve una data "
                "nella forma AAAA-MM-GG")
        try:
            date.fromisoformat(self.decided_on)
        except ValueError as errore:
            raise ValueError(
                f"decisione di apertura datata {self.decided_on!r}: non e' un giorno "
                f"del calendario ({errore}). Una decisione presa in un mese che non "
                "esiste non e' stata presa.") from errore
        aperte = _dentro_il_vocabolario(
            frozenset(self.opens), "decisione di apertura")
        if not aperte - SUPPORTED:
            raise ValueError(
                "decisione di apertura che non apre nulla: "
                f"{', '.join(sorted(aperte)) or 'nessun nome'} — "
                f"gia' applicabile senza alcuna decisione. Una registrazione che non "
                "cambia l'insieme delle applicabili non apre il Catalogo (FR-43).")
        object.__setattr__(self, "opens", aperte)


def transformations_supported(opening: CatalogOpening | None = None) -> frozenset[str]:
    """Le Trasformazioni applicabili. La cardinalita' di questo insieme e' SM-C5.

    Senza una decisione di apertura registrata sono le tre dell'MVP. Con una, sono
    quelle piu' cio' che la decisione apre — e mai nomi nuovi, perche'
    `CatalogOpening` li ha gia' verificati dentro il vocabolario chiuso.

    Non e' una funzione di configurazione: non legge nulla e non ricorda nulla. Chi
    vuole il Catalogo aperto esibisce la registrazione a ogni chiamata, che e'
    esattamente il punto di FR-43.
    """
    return SUPPORTED if opening is None else SUPPORTED | opening.opens
