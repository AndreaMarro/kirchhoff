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
    `_MUTABILI["serie"] = {"provenance"}` passava all'import (misurato). I due lati
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


# --- Story 1.2: di quali riscritture strutturali un passo pedagogico e' composto ---
#
# Il vocabolario delle riscritture vive in `primitives.py` e non sa nulla del Catalogo:
# una riscrittura e' una modifica del grafo, non il passo che la contiene. Il legame
# fra i due livelli e' **una dichiarazione del Catalogo**, per la stessa ragione per
# cui lo e' il discriminante d'identita': chi e' misurato non definisce il proprio
# riferimento (AD-22 v2.1). Se fosse il `Delta` a dire di quale passo fa parte, la
# `Transform` misurata sceglierebbe da se' il livello a cui viene letta.


def _verifica_livelli_distinti(
    catalogo: frozenset[str], riscritture: frozenset[str]
) -> None:
    """I due vocabolari non possono condividere un nome.

    Un nome in entrambi sarebbe accettato sia da `StructuralDerivation` sia da
    `Certificate`, e i due livelli tornerebbero indistinguibili **proprio nel punto
    che la Story 1.2 esiste per separare** — senza che nulla protesti, perche' ogni
    guardia presa da sola resterebbe soddisfatta. E' l'invariante che rende «distinto
    dal catalogo pedagogico» una proprieta' verificata e non un'intenzione.
    """
    condivisi = sorted(catalogo & riscritture)
    if condivisi:
        raise RuntimeError(
            "il catalogo pedagogico e il vocabolario delle riscritture strutturali "
            f"condividono {', '.join(condivisi)}: un nome solo per due livelli li "
            "rende indistinguibili, ed e' il difetto che tenerli separati chiude.")


_verifica_livelli_distinti(CATALOG, PRIMITIVES)


#: **Di quali riscritture strutturali ciascun passo pedagogico e' composto.**
#:
#: Una **tupla e non un insieme**, e la differenza e' misurata: come `frozenset` la
#: dichiarazione non poteva esprimere la molteplicita', e un passo futuro che elimina
#: due nodi si sarebbe dichiarato identico a uno che ne elimina uno. La tupla porta
#: quante volte ciascuna riscrittura compare; **non** porta un ordine, perche' le
#: derivazioni di un `Delta` non si concatenano e l'ordine canonico e' per contenuto.
#: Per non lasciar credere il contrario, `_verifica_composizione` pretende che ogni
#: tupla sia ordinata alfabeticamente: c'e' una sola forma in cui scriverla.
#:
#: La tupla vuota e' il predefinito, e vuoto qui non significa «nessun vincolo»: un
#: passo che non dichiara di che cosa e' fatto **non produce un `TransformResult`**
#: (`result.TransformResult`). Un vincolo che si spegne quando la dichiarazione manca
#: sarebbe un controllo che non puo' fallire proprio dove non e' mai stato pensato, e
#: un vuoto che somiglia a una misura e' peggio di un'assenza dichiarata.
#:
#: Dichiarano oggi le due operazioni che hanno un'implementazione (`engine.implemented`).
#: `partitore_di_tensione` e' applicabile e non implementata: quando avra' un corpo,
#: **questa e' la riga da cambiare**, altrimenti quel corpo non potra' emettere nulla —
#: e il posto dove dichiarare il caso nuovo e' il test
#: `test_ogni_operazione_implementata_dichiara_di_che_cosa_e_fatta`.
#:
#: `serie` ne dichiara **due**, e non e' un dettaglio: e' il caso di AC2 della Story —
#: una trasformazione pedagogica composta da piu' riscritture. `parallelo` ne dichiara
#: una sola, perche' entrambi i nodi sopravvivono alla fusione.
_COMPOSIZIONE: dict[str, tuple[str, ...]] = {nome: () for nome in sorted(CATALOG)}
_COMPOSIZIONE["serie"] = ("eliminazione_di_nodo", "fusione_di_componenti")
_COMPOSIZIONE["parallelo"] = ("fusione_di_componenti",)

#: Vista di sola lettura, per la stessa ragione di `MUTABLE_ATTRIBUTES`: un `dict`
#: ordinario lascerebbe riscrivibile con un'assegnazione la dichiarazione rispetto a
#: cui il `Delta` di un passo e' verificato.
COMPOSITION: MappingProxyType[str, tuple[str, ...]] = MappingProxyType(_COMPOSIZIONE)


def primitives_of(operation: str) -> tuple[str, ...]:
    """Le riscritture di cui `operation` si dichiara composta, con la loro molteplicita'.

    Solleva se l'operazione e' fuori dal catalogo, come `mutable_attributes`: chiedere
    la composizione di un passo che non esiste e' un errore di programmazione, e
    rispondere «nessuna» lo renderebbe silenzioso.
    """
    if operation not in CATALOG:
        raise ValueError(
            f"operazione {operation!r} fuori dal catalogo chiuso: "
            "non ha una composizione perche' non esiste.")
    return COMPOSITION[operation]


def _verifica_composizione(dichiarazione: Mapping[str, tuple[str, ...]]) -> None:
    """Le tre condizioni che rendono `_COMPOSIZIONE` una dichiarazione e non un elenco.

    **Le chiavi**, come per `_MUTABILI`: catalogo e dichiarazione non possono
    divergere, o una voce avrebbe composizione indefinita invece che vuota.

    **I valori**: cio' che si dichiara dev'essere una riscrittura del vocabolario
    chiuso. Senza questa meta', `_COMPOSIZIONE["serie"] = ("parallelo",)` passerebbe
    all'import e dichiarerebbe un passo pedagogico come sotto-passo di un altro —
    esattamente la confusione di livello che questo modulo separa.

    **L'ordine**: ogni tupla e' ordinata alfabeticamente. La tupla porta molteplicita',
    non sequenza, e due scritture della stessa dichiarazione che differissero solo per
    l'ordine farebbero credere a un ordine che il `Delta` non ha.
    """
    if set(dichiarazione) != CATALOG:
        raise RuntimeError(
            "il catalogo e la dichiarazione di composizione sono divergenti: "
            f"solo nella dichiarazione {sorted(set(dichiarazione) - CATALOG)}, "
            f"solo nel catalogo {sorted(CATALOG - set(dichiarazione))}")
    fuori = {
        nome: sorted(set(riscritture) - PRIMITIVES)
        for nome, riscritture in sorted(dichiarazione.items())
        if set(riscritture) - PRIMITIVES
    }
    if fuori:
        raise RuntimeError(
            "riscritture dichiarate fuori dal vocabolario strutturale chiuso: "
            f"{fuori}. Le riscritture sono {', '.join(sorted(PRIMITIVES))}: un passo "
            "pedagogico non e' un sotto-passo di un altro passo pedagogico.")
    disordinate = sorted(
        nome for nome, riscritture in dichiarazione.items()
        if list(riscritture) != sorted(riscritture))
    if disordinate:
        raise RuntimeError(
            f"composizioni non ordinate alfabeticamente: {disordinate}. La tupla "
            "porta la molteplicita' delle riscritture, non il loro ordine: il `Delta` "
            "non ne ha uno, e scriverne uno qui lo farebbe credere.")


_verifica_composizione(COMPOSITION)


#: **Le riscritture che nessun passo dichiara**, col perche' di ciascuna.
#:
#: Un nome del vocabolario che nessuna voce di `COMPOSITION` nomina non e' emettibile
#: da alcun prodotto: `TransformResult` lo rifiuterebbe qualunque sia il passo. Non e'
#: un difetto — un vocabolario si chiude sui concetti, non sull'implementazione del
#: momento — ma **taciuto** e' indistinguibile da una dimenticanza, e il divario fra
#: `CATALOG` e `SUPPORTED` ha per contro un meccanismo (`CatalogOpening`), una misura
#: (SM-C5) e tre porte in `transform()`. Qui il meccanismo e' piu' piccolo, ed e'
#: questo: la partizione e' dichiarata, e `_verifica_dormienti` la impone esatta.
#: Usare una dormiente senza toglierla di qui fa fallire l'import, come lasciarla
#: dormiente dopo averla usata.
_DORMIENTI: dict[str, str] = {
    "fusione_di_nodi": (
        "nessun passo implementato fonde due nodi conservandone uno: `serie` elimina "
        "il nodo interno senza erede, `parallelo` non tocca i nodi. Serve al primo "
        "passo che assorbe un nodo in un altro — la riduzione di un corto circuito."),
    "sostituzione_di_componente": (
        "l'unico produttore odierno e' `transform()`, e nessuna sua voce sostituisce "
        "in luogo: `check_transform` rifiuta anzi il riuso di un identificatore fra "
        "`Cₖ` e `Cₖ₊₁` (CV1). La riscrittura esiste perche' AD-22 v2.1 chiede che una "
        "mutata in luogo compaia nel `Delta`, e un controllore la riceve gia' dai test."),
    "rimozione_di_componente": (
        "e' `REMOVE_LOAD` — il sotto-passo che la Story cita — e nessun passo del "
        "catalogo lo esercita finche' `resistenza_equivalente_di_thevenin` non ha un "
        "corpo: e' li' che il carico si stacca."),
}

#: Vista di sola lettura, come le altre dichiarazioni di questo modulo.
DORMANT: MappingProxyType[str, str] = MappingProxyType(_DORMIENTI)


def _verifica_dormienti(
    dichiarazione: Mapping[str, tuple[str, ...]], dormienti: Mapping[str, str]
) -> None:
    """Ogni riscrittura o e' esercitata da un passo, o e' dichiarata dormiente. Mai
    entrambe, mai nessuna delle due."""
    esercitate = {r for riscritture in dichiarazione.values() for r in riscritture}
    doppie = sorted(esercitate & set(dormienti))
    if doppie:
        raise RuntimeError(
            f"riscritture insieme esercitate e dichiarate dormienti: {doppie}. "
            "Una delle due affermazioni e' vecchia, e non si sa quale.")
    mute = sorted(PRIMITIVES - esercitate - set(dormienti))
    if mute:
        raise RuntimeError(
            f"riscritture che nessun passo esercita e che nulla dichiara dormienti: "
            f"{mute}. Un nome non emettibile e non registrato e' indistinguibile da "
            "una dimenticanza.")


_verifica_dormienti(COMPOSITION, DORMANT)


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

