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

- **Il vocabolario** (`CATALOG`) — i sedici nomi di **passo pedagogico**. Chiuso per
  sempre: non lo si estende a runtime (AD-2).
- **Le applicabili** (`SUPPORTED`) — le tre dell'MVP. Un nome del vocabolario che
  non e' qui **esiste** e **non e' eseguibile**, e il sistema rifiuta invece di
  improvvisare (FR-43). Si apre solo con una decisione registrata: `CatalogOpening`.
- **Le implementate** (`engine.implemented()`) — quelle che hanno gia' un corpo.
  «Non ancora scritta» e «non esiste» sono risposte diverse a chi pianifica.

## E una quarta cosa, che non e' in questo modulo

**I nomi qui dentro non sono quelli che una derivazione porta**, e la riga che lo
diceva e' rimasta falsa fino alla Story 1.2. Una `StructuralDerivation` porta una
**riscrittura strutturale** — `primitives.PRIMITIVES` — perche' un passo pedagogico
puo' essere composto da piu' riscritture e K-0 pretende un fotogramma per ogni passo,
non per ogni riscrittura. Il legame fra i due livelli e' `COMPOSITION`, dichiarata piu'
sotto: e' il Catalogo a dire di che cosa un suo passo e' fatto, mai il `Delta`.

Puro: nessuna I/O, nessun orologio, nessuna casualita'. Anche la data di una
decisione di apertura entra come dato: qui non si legge un orologio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

from .primitives import PRIMITIVES

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
    "control_nodes",
)

#: **Il discriminante di AD-22 v2.1.** Per ciascuna operazione, gli attributi che
#: possono cambiare mentre l'identita' dell'entita' sopravvive.
#:
#: L'insieme predefinito e' **vuoto**: chi non dichiara nulla non muta nulla. Cosi'
#: una `R1` da 10 Ω che dopo una riduzione in parallelo vale 6⅔ Ω **non e'**
#: preservata.
#:
#: **Che cosa le accade poi e' cambiato con la Story 1.1, e la riga di prima era
#: rimasta indietro.** Diceva «e' una rimozione piu' una creazione che ne ha riusato
#: il nome, e come tale deve comparire nel `Delta`», citando AD-22 v2.1. Quella
#: clausola descrive cio' che il `Delta` deve dichiarare, e `check_delta` continua a
#: esigerlo; ma `check_transform` **rifiuta** ora il passo prima di arrivarci, perche'
#: un identificatore che compare in `Cₖ` e in `Cₖ₊₁` senza nominare la stessa entita'
#: rende `Pₖ` leggibile e falso (CV1). La forma «rimozione piu' creazione col nome
#: riusato» non e' quindi una rappresentazione ammessa del passo: e' la forma
#: rifiutata. Quella ammessa da' all'entita' di `Cₖ₊₁` un **identificatore proprio**.
#: La divergenza fra questa emissione e le due clausole owner-locked che la
#: descrivono e' registrata in `deferred-work.md`, non decisa qui.
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
#:
#: **`type` e' dichiarabile mutabile, e non e' una svista.** Nulla qui vieta a
#: un'operazione di licenziare il cambio di tipo — un condensatore che diventa un
#: resistore «restando la stessa entita'» — e la domanda e' stata posta
#: esplicitamente. La risposta e' che l'esempio *illustrativo* di AD-22 v2.1 e'
#: proprio questo caso: «la disattivazione di un generatore indipendente **potrebbe**
#: essere una di queste — stessa entita', stato cambiato — oppure una sostituzione
#: strutturale con identita' nuova». Un generatore disattivato modellato come corto
#: circuito **e'** un cambio di `type`, e vietarlo qui deciderebbe in anticipo, e in
#: un modulo, una questione che lo spine lascia aperta al vocabolario delle primitive
#: strutturali. **Quel vocabolario esiste dalla Story 1.2 e continua a non decidere
#: la questione**: `primitives.py` non nomina la soppressione di un generatore, e
#: dichiara perche'. La licenza resta quindi esprimibile e resta **non esercitata**: nessuna
#: voce di `_MUTABILI` la concede, e il giorno in cui una la concedesse sarebbe un
#: commit visibile su questa riga, non un effetto a runtime. Registrato in
#: `deferred-work.md` come decisione del proprietario.
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


def _verifica_dichiarazione(dichiarazione: Mapping[str, frozenset[str]]) -> None:
    """Le due condizioni che rendono `_MUTABILI` un discriminante e non un elenco.

    **Le chiavi.** Il catalogo e la dichiarazione non possono divergere: una voce
    senza dichiarazione avrebbe discriminante indefinito, e la si leggerebbe come
    «tutto mutabile» o «niente mutabile» a seconda di chi la interroga.

    **I valori.** Lo stesso invariante era guardato **su un lato solo**.
    `IdentityAttestation` rifiuta un attributo fuori da `IDENTITY_ATTRIBUTES` —
    «`provenance` non compone l'identita' sostanziale, quindi il suo cambiamento non
    ha bisogno di licenza» — mentre qui si controllavano le sole chiavi, e
    `_MUTABILI[\"serie\"] = {\"provenance\"}` passava all'import (misurato). I due lati
    dicono la stessa cosa: cio' che non compone l'identita' non e' licenziabile,
    perche' concederne la licenza non concede nulla. Una dichiarazione simile non
    sarebbe dannosa — nessun confronto la userebbe mai — ma sarebbe **leggibile e
    falsa**: chi legge il Catalogo vedrebbe una licenza dove non ce n'e' una.

    E' una funzione e non due righe in linea perche' un invariante di import senza
    test e' una guardia che nessuno ha visto sollevare (CV5): cosi' la si puo'
    interrogare con una dichiarazione guasta senza guastare il modulo.
    """
    if set(dichiarazione) != CATALOG:
        raise RuntimeError(
            "il catalogo e la dichiarazione degli attributi mutabili sono divergenti: "
            f"solo nella dichiarazione {sorted(set(dichiarazione) - CATALOG)}, "
            f"solo nel catalogo {sorted(CATALOG - set(dichiarazione))}")
    sostanziali = set(IDENTITY_ATTRIBUTES)
    fuori = {
        nome: sorted(attributi - sostanziali)
        for nome, attributi in sorted(dichiarazione.items())
        if attributi - sostanziali
    }
    if fuori:
        raise RuntimeError(
            "attributi dichiarati mutabili che non compongono l'identita' "
            f"sostanziale: {fuori}. Gli attributi d'identita' sono "
            f"{', '.join(IDENTITY_ATTRIBUTES)}: licenziare il cambiamento di cio' "
            "che non e' identita' non concede nulla, e si legge come se lo facesse.")


_verifica_dichiarazione(MUTABLE_ATTRIBUTES)
