"""Il vocabolario chiuso delle **riscritture strutturali**, un livello sotto il Catalogo.

## L'esito della ricerca che precede questo modulo

La Story 1.2 impone `search-before-build` e nomina i concetti da cercare: *primitive ·
rewrite · graph edit · internal transform · source suppression · reduction · substep ·
micro-step · atomic transform · edit script · operation vocabulary*. Cercati in PRD,
`ARCHITECTURE-SPINE.md`, UX, `KIRCHHOFF-KNOWLEDGE`, memlog, review e codice, il 26
agosto 2026. **Nessuna autorita' esiste**, e due documenti lo dicono esplicitamente:

- lo spine, dentro l'emendamento AD-22 v2.1: *«Quale delle due sia dipende dal
  **vocabolario delle primitive strutturali, che non esiste ancora**.»*
- `implementation-artifacts/matrice-impatto-cv1-cv6-su-delta.md`, che registra il
  disallineamento e **non lo risolve**: *«e' la scelta fra estendere il catalogo alle
  primitive atomiche, oppure tenere il catalogo al livello didattico e modellare le
  atomiche come derivazioni interne a un passo»*.

La Story sceglie la seconda: il catalogo resta didattico, le atomiche vivono qui.
`matrice-ac-ramo-2-6.md` misura lo stato di partenza — *«`PRIMITIVES` / vocabolario
strutturale: **ASSENTE**»*. Entrambi i registri sono stati aggiornati con l'esito,
perche' una decisione differita che poggia su una premessa falsa non e' differita:
e' persa.

## Perche' due vocabolari e non uno

`catalog.CATALOG` nomina **passi didattici**: `serie`, `parallelo`,
`resistenza_equivalente_di_thevenin`, `circuito_equivalente_a_t0`. Sono le unita' di
cui K-0 dice *«un passo senza disegno non e' un passo: e' una riga di calcolo, e va
fusa con quella precedente»*, e ognuna deve arrivare a uno stato visuale verificato.

Le riscritture qui sotto stanno un livello piu' in basso: sono le **modifiche
elementari del grafo** di cui un passo didattico e' composto. `serie` non e' una sola
riscrittura — fonde due componenti **e** cancella il nodo interno che li univa.

Tenerle nel Catalogo pedagogico costerebbe due cose, entrambe gia' nominate altrove:

- la cardinalita' delle applicabili e' **SM-C5**, e deve restare tre finche' il kill
  criterion di Gate A non e' superato (FR-43). Un catalogo che assorbe le
  micro-operazioni fa salire quel numero senza che nulla di didattico sia stato
  aggiunto;
- **K-0 imporrebbe un fotogramma a ciascuna**, cioe' un disegno per «il nodo `b` non
  c'e' piu'», che e' esattamente cio' che K-0 chiama riga di calcolo e chiede di
  fondere col passo precedente.

## Che cosa questo vocabolario NON decide

`REMOVE_LOAD` e `ZERO_VOLTAGE_SOURCE` sono i due esempi che la Story cita come
sotto-passi, e **hanno qui destini diversi**. Il primo e' coperto: si scrive
`rimozione_di_componente`, ed e' lo stesso concetto sotto un nome che non nomina il
carico. **Il secondo no, e l'assenza e' deliberata.** Lo spine lascia aperto se la
disattivazione di un generatore sia *«stessa entita', stato cambiato — oppure una
sostituzione strutturale con identita' nuova e lineage nel `Delta`»*, e la questione
e' registrata come decisione del proprietario in `deferred-work.md`. Dare qui un nome
proprio alla soppressione sceglierebbe la seconda lettura in un modulo, che e' il
gesto che quella registrazione vieta.

I due casi hanno percio' due test distinti, e non uno solo che li confonda:
`test_remove_load_e_coperto_sotto_un_altro_nome` e
`test_la_soppressione_di_un_generatore_non_e_nel_vocabolario`. Quando la decisione
sara' presa, **la riga da cambiare e' `StructuralPrimitive` qui sotto**, e il secondo
di quei due test il posto dove dichiarare il caso nuovo.

## Chiuso significa: nessuna estensione a runtime

Come `CATALOG`, e per la stessa ragione (AD-2). `PRIMITIVES` e' un `frozenset` e non
esiste alcuna funzione che vi aggiunga una voce: un nome nuovo e' un commit su questo
file, visibile in un diff, non un effetto collaterale di un chiamante.

**E scritto una volta sola.** `PRIMITIVES` si *deriva* da `StructuralPrimitive` con
`get_args`, come `refusal.CAUSES` si deriva da `Cause`. La prima stesura di questo
modulo riproduceva invece la duplicazione a mano di `catalog.py` — i cinque nomi in un
`Literal` e gli stessi cinque in un `frozenset` accanto — nel modulo il cui docstring
cita E-62 contro i predicati doppi. Un nome aggiunto all'uno e non all'altro non
faceva protestare nulla. Derivandoli, la divergenza non e' piu' evitata per
disciplina: e' impossibile.

## Le cinque riscritture, e la forma che ciascuna impone

| Nome | Che cosa dichiara accaduto | Forma |
|---|---|---|
| `fusione_di_componenti` | piu' componenti diventano un equivalente con identita' propria | ≥2 componenti → 1 componente |
| `fusione_di_nodi` | un nodo cessa di esistere dentro un altro nodo, che sopravvive | ≥1 nodo → 1 nodo |
| `eliminazione_di_nodo` | un nodo interno cessa di esistere e nessun nodo lo eredita | ≥1 nodo → nulla |
| `sostituzione_di_componente` | un componente e' sostituito da un altro | 1 componente → 1 componente |
| `rimozione_di_componente` | un componente e' tolto dalla rete e nulla lo sostituisce | ≥1 componente → nulla |

**La colonna di destra e' eseguibile, e la prima stesura non l'aveva.** Diceva invece
che la forma di una derivazione «e' gia' verificata dove la si puo' verificare
davvero, cioe' contro i due circuiti, da `check_delta`», e che un vincolo dichiarato
qui sarebbe stato un secondo predicato per la stessa cosa (E-62). Era falso, ed era
E-62 nella forma inversa: **non esisteva un primo predicato.** `check_delta` confronta
gli aggregati `consumed`/`produced` coi due circuiti e non guarda mai `d.operation`;
i cinque nomi erano quindi intercambiabili, e la coppia che questo vocabolario esiste
per separare — `fusione_di_nodi`, dove un nodo sopravvive, contro
`eliminazione_di_nodo`, dove nessuno eredita — viveva solo in questa tabella.
Misurato prima della correzione: `{node:b} --eliminazione_di_nodo--> {node:a}`,
`{node:b} --fusione_di_nodi--> {∅}`, `{R1} --rimozione_di_componente--> {R9}` e
`{node:a,node:b} --fusione_di_componenti--> {node:z}` si costruivano tutte senza
proteste, e scambiare i nomi fra le due derivazioni di una `serie` reale lasciava
`check_delta` a zero violazioni.

Le tre condizioni che `_verifica_forme` impone alla tabella dicono perche' basta:

1. **ogni riscrittura ha una forma.** Una senza sarebbe l'unica non vincolata, cioe'
   il difetto di sopra sopravvissuto in un angolo;
2. **le cinque forme sono distinte a due a due.** E' la traduzione eseguibile di «i
   nomi non sono intercambiabili»: se due riscritture ammettessero le stesse
   derivazioni, sceglierne una invece dell'altra non sarebbe piu' un'affermazione;
3. **nessuna ammette zero ingressi.** Deciso esplicitamente, non per comodita': nel
   vocabolario chiuso non esiste oggi una riscrittura che crei un'entita' senza
   ascendenza, e una tale entita' non avrebbe lineage interrogabile. Se ne comparira'
   una, **questa e' la condizione da cambiare**, e
   `test_nessuna_riscrittura_crea_senza_ascendenza` il posto dove dichiarare il caso
   nuovo.

Cio' che la forma **non** dice resta detto qui, per non ripetere l'errore inverso: la
forma vincola *genere e quantita'*, non l'identita' delle entita'. Che il nodo
consumato sia proprio quello sparito dal circuito lo verifica `check_delta`, contro
`Cₖ` e `Cₖ₊₁`, che sono gli unici a saperlo; che le riscritture emesse siano proprio
quelle di cui il passo si dichiara composto lo verifica `TransformResult` contro
`catalog.COMPOSITION`. Tre controlli, tre livelli, nessuno dei tre sostituibile dagli
altri due.

Il genere e' qui una stringa e non un tipo: `EntityKind` vive in `delta.py`, che
importa questo modulo, e importarlo indietro sarebbe un ciclo. Che i generi nominati
qui siano generi di entita' noti lo verifica `delta.py` all'import, dove i generi
esistono — un controllo, non una seconda dichiarazione.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from types import MappingProxyType
from typing import Literal, get_args

StructuralPrimitive = Literal[
    "fusione_di_componenti",
    "fusione_di_nodi",
    "eliminazione_di_nodo",
    "sostituzione_di_componente",
    "rimozione_di_componente",
]

#: **Derivato, mai riscritto a mano.** `get_args` su un `Literal` restituisce i suoi
#: membri nell'ordine di dichiarazione; l'insieme e' quindi lo stesso oggetto detto
#: due volte, non due oggetti da tenere allineati.
PRIMITIVES: frozenset[str] = frozenset(get_args(StructuralPrimitive))


@dataclass(frozen=True, slots=True)
class Forma:
    """Che cosa una riscrittura ammette ai due capi: un genere, due quantita'.

    **Un genere solo, e lo stesso ai due capi.** Nessuna delle riscritture note
    trasforma un nodo in un componente o viceversa: fondere due resistori produce un
    resistore, fondere due nodi produce un nodo. Un campo per capo lascerebbe
    esprimibile `{node:b} --eliminazione_di_nodo--> {component:Req}`, che e' la
    lineage falsa misurata prima di questa classe.
    """

    genere: str
    ingressi_minimi: int
    uscite: int
    #: Arita' massima in ingresso; `None` significa «nessun tetto».
    #:
    #: **Serve perche' un minimo da solo non separa due riscritture.**
    #: `sostituzione_di_componente` dichiarava `ingressi_minimi=1` — «uno o piu'» —
    #: mentre `fusione_di_componenti` chiede «due o piu'» dello stesso genere con la
    #: stessa uscita singola: ogni forma di fusione era percio' ANCHE una
    #: sostituzione valida. Misurato:
    #: `{R1,R2} --sostituzione_di_componente--> {R1R2eq}` si costruiva, cioe' una
    #: fusione che si dichiara sostituzione. L'intercambiabilita' che questa storia
    #: esiste per chiudere restava aperta in quel verso.
    #:
    #: Una sostituzione sostituisce UN componente; non ne fonde due.
    ingressi_massimi: int | None = None


_FORME: dict[str, Forma] = {
    "fusione_di_componenti": Forma("component", ingressi_minimi=2, uscite=1),
    "fusione_di_nodi": Forma("node", ingressi_minimi=1, uscite=1),
    "eliminazione_di_nodo": Forma("node", ingressi_minimi=1, uscite=0),
    "sostituzione_di_componente": Forma(
        "component", ingressi_minimi=1, uscite=1, ingressi_massimi=1),
    "rimozione_di_componente": Forma("component", ingressi_minimi=1, uscite=0),
}

#: Vista di sola lettura, per la stessa ragione di `catalog.MUTABLE_ATTRIBUTES`: un
#: `dict` ordinario lascerebbe riscrivibile con un'assegnazione il vincolo rispetto a
#: cui ogni derivazione e' costruita.
FORME: MappingProxyType[str, Forma] = MappingProxyType(_FORME)


def _verifica_forme(forme: Mapping[str, Forma]) -> None:
    """Le tre condizioni che rendono la tabella un vincolo e non un commento.

    Sono descritte per esteso nel docstring del modulo, sotto la tabella delle cinque
    riscritture. Qui restano le diagnosi, perche' un `RuntimeError` all'import e'
    l'unico lettore che le vedra'.
    """
    if set(forme) != PRIMITIVES:
        raise RuntimeError(
            "il vocabolario delle riscritture e la tabella delle forme sono "
            f"divergenti: solo nella tabella {sorted(set(forme) - PRIMITIVES)}, "
            f"solo nel vocabolario {sorted(PRIMITIVES - set(forme))}. Una "
            "riscrittura senza forma sarebbe l'unica a non vincolare nulla.")

    for (uno, a), (altro, b) in combinations(sorted(forme.items()), 2):
        if a == b:
            raise RuntimeError(
                f"le riscritture {uno} e {altro} hanno la stessa forma {a}: "
                "ammettono percio' esattamente le stesse derivazioni, e sceglierne "
                "una invece dell'altra non e' piu' un'affermazione verificabile.")

    senza_ascendenza = sorted(n for n, f in forme.items() if f.ingressi_minimi < 1)
    if senza_ascendenza:
        raise RuntimeError(
            f"riscritture che ammettono zero ingressi: {senza_ascendenza}. "
            "Un'entita' creata senza ascendenza non ha lineage interrogabile, e "
            "ammetterlo qui e' una decisione del vocabolario, non di una derivazione.")


_verifica_forme(FORME)

