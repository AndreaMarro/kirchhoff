"""`ProofGraph` — i nodi della derivazione, e il layout che ciascuno possiede.

AD-29: *«nodi = stati circuitali, archi = `Transform`. Diramazione e
ricongiungimento sono supportati dallo schema e dalla persistenza fin da subito,
anche se l'MVP non li produce.»* AD-8: `ProofGraph` → `domain/proof`, scrittore unico.

## Il proprietario del riferimento, cercato e non presupposto

La Story 1.3 chiede di **cercarlo**: *«`ProofGraph`, nodo di timeline, stato di
replay o struttura gia' prevista — non si patcha `ProofSession` solo perche' e' il
primo posto disponibile»*. La ricerca ha una risposta gia' scritta, in AD-8 em. del
24 agosto:

> Il proprietario del riferimento e' **il nodo**, non la sessione: AD-29 definisce i
> nodi come **stati circuitali**, e il `LayoutIR` e' lo stato visuale di quello stato
> circuitale. Il nodo porta **l'identificatore** del proprio layout, mai la struttura.

E AD-21 v2.1 dice cosa ne segue per la sessione — *«dei `LayoutIR` porta **un
identificatore per nodo del `ProofGraph`**, non un identificatore singolo»* — cioe'
che la `ProofSession` **legge** questa relazione invece di possederla. La sessione e'
la Story 6.1 e non e' toccata qui.

## Il nodo non contiene lo stato circuitale, lo nomina

`ProofNode.identifier` e' l'`ir_` dello stato circuitale, `ProofNode.layout` e' il
`lay_` del suo stato visuale. Nessuna delle due strutture entra nel nodo: AD-21
*«ammette il riferimento per identificatore e vieta il contenimento»*, e un grafo che
portasse i circuiti per valore renderebbe la derivazione un aggregato invece di una
relazione — proprio il collasso che AD-21 chiude sulla `ProofSession`.

## Che cosa questo modulo NON fa

Non risolve gli identificatori: non conosce `render/layout` — non potrebbe, il
recinto 2 di AD-21 vieta `domain/ → render/` — e non conosce il registro dei
`CircuitIR`. Non decide quale sia la soluzione finale, non persiste, non produce
passi: qui c'e' la relazione, e solo quella. Chi risolve la coppia
`(LayoutIR_k, LayoutIR_{k+1})` e' `eval/`, che vede entrambi i lati.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..identity import IdentityKind, verifica
from ..transform.catalog import CATALOG, TransformationKind

#: I tre generi di identificatore che questo grafo maneggia, per il ruolo che hanno
#: qui. Nominati una volta: il vocabolario chiuso sta in `domain/identity`.
_STATO_CIRCUITALE: IdentityKind = "ir"
_STATO_VISUALE: IdentityKind = "lay"
_PATCH: IdentityKind = "patch"


@dataclass(frozen=True, slots=True)
class ProofNode:
    """Uno stato circuitale, e l'identificatore del suo stato visuale.

    Due identificatori e nessuna struttura. Il nodo **e'** lo stato circuitale
    (AD-29), quindi la sua identita' e' quella del `CircuitIR` che denota: non c'e'
    un secondo nome da coniare e da tenere allineato al primo.
    """

    identifier: str
    layout: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "identifier", verifica(self.identifier, _STATO_CIRCUITALE))
        object.__setattr__(self, "layout", verifica(self.layout, _STATO_VISUALE))


@dataclass(frozen=True, slots=True)
class ProofEdge:
    """Un passo pedagogico fra due stati circuitali, e la patch che lo descrive.

    `patch` e' il terzo lato del triangolo che CV6 chiede: *«perche' la metrica sia
    calcolabile serve, per ogni passo, la tripla `(LayoutPatch, LayoutIR_k,
    LayoutIR_{k+1})` **congiungibile**»*. SM-14 conta i `LayoutPatch` che violano la
    continuita': senza il suo identificatore sull'arco, il denominatore di VCER non
    e' riconducibile ai due operandi del predicato.

    `operation` e' il passo **pedagogico** e non una riscrittura strutturale: e' il
    livello a cui K-0 pretende un fotogramma, ed e' lo stesso livello di
    `Certificate.operation`. Le riscritture di cui il passo e' composto stanno nel
    `Delta` (Story 1.2) e non risalgono fin qui.
    """

    source: str
    target: str
    operation: TransformationKind
    patch: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", verifica(self.source, _STATO_CIRCUITALE))
        object.__setattr__(self, "target", verifica(self.target, _STATO_CIRCUITALE))
        object.__setattr__(self, "patch", verifica(self.patch, _PATCH))
        if self.operation not in CATALOG:
            raise ValueError(
                f"arco etichettato {self.operation!r}, fuori dal catalogo chiuso: "
                f"{', '.join(sorted(CATALOG))}. Gli archi sono `Transform` (AD-29), "
                "e le Trasformazioni sono quelle.")
        if self.source == self.target:
            raise ValueError(
                f"{self.source}: arco su se stesso. Un passo che parte e arriva "
                "allo stesso stato circuitale non e' un passo, e darebbe a VCER due "
                "operandi che sono lo stesso layout.")


@dataclass(frozen=True, slots=True)
class ProofGraph:
    """I nodi, gli archi, e le due direzioni della relazione nodo ↔ layout.

    Immutabile e append-only: `con_passo` restituisce un grafo **nuovo**, e le
    guardie del costruttore rifiutano ogni estensione che riscriverebbe una
    relazione gia' stabilita. Non c'e' un metodo che sostituisce il layout di un
    nodo, e non e' un'omissione: e' la forma che AD-8 v2.1 impone.
    """

    nodes: tuple[ProofNode, ...] = ()
    edges: tuple[ProofEdge, ...] = ()

    def __post_init__(self) -> None:
        # Normalizzare a tupla **prima** di controllare: una lista passata qui
        # resterebbe condivisa col chiamante, e un `append` esterno aggiungerebbe
        # un nodo dopo che le guardie sono passate — cioe' il grafo potrebbe finire
        # con due nodi sullo stesso `lay_` proprio nel modo che la guardia sotto
        # vieta. E' la stessa ragione per cui `LayoutIR` congela i piazzamenti.
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        for n in self.nodes:
            if not isinstance(n, ProofNode):
                raise TypeError(f"{type(n).__name__} fra i nodi invece di ProofNode")
        for a in self.edges:
            if not isinstance(a, ProofEdge):
                raise TypeError(f"{type(a).__name__} fra gli archi invece di ProofEdge")

        stati = [n.identifier for n in self.nodes]
        doppi = sorted({s for s in stati if stati.count(s) > 1})
        if doppi:
            raise ValueError(
                f"stato circuitale ripetuto fra i nodi: {', '.join(doppi)}. Due nodi "
                "con lo stesso nome sono un nodo che e' stato riscritto.")

        # **Un layout appartiene a un nodo solo.** E' la meta' strutturale della
        # ritenzione: il registro di `render/layout` impedisce di sovrascrivere uno
        # stato visuale, questa guardia impedisce di *riusarlo*. Senza, due nodi
        # potrebbero dichiarare lo stesso `lay_` e `nodo_di` smetterebbe di essere
        # una funzione — cioe' la direzione layout → nodo che AC3 chiede non
        # esisterebbe, pur essendo interrogabile.
        visuali = [n.layout for n in self.nodes]
        condivisi = sorted({v for v in visuali if visuali.count(v) > 1})
        if condivisi:
            raise ValueError(
                f"stato visuale condiviso da piu' nodi: {', '.join(condivisi)}. "
                "Ogni nodo ha il proprio `LayoutIR` (AD-8 v2.1): due nodi sullo "
                "stesso layout dicono che uno dei due e' stato sovrascritto.")

        noti = set(stati)
        for a in self.edges:
            ignoti = [e for e in (a.source, a.target) if e not in noti]
            if ignoti:
                raise ValueError(
                    f"l'arco {a.operation} nomina {', '.join(ignoti)}, che non e' un "
                    f"nodo di questo grafo. Nodi: {', '.join(sorted(noti)) or 'nessuno'}.")

        elenco = [(a.source, a.target, a.operation, a.patch) for a in self.edges]
        ripetuti = sorted({f"{s} -{o}-> {t}" for s, t, o, p in elenco
                           if elenco.count((s, t, o, p)) > 1})
        if ripetuti:
            raise ValueError(
                f"arco ripetuto: {', '.join(ripetuti)}. Lo stesso passo dichiarato "
                "due volte conta due volte nel denominatore di VCER.")

        # **Un `patch_` appartiene a un arco solo.** SM-14 conta i `LayoutPatch`
        # che violano la continuita': se due archi ne condividessero uno,
        # un'evidenza «`patch_X` viola VCER» non saprebbe a quale passo riferirsi, e
        # il denominatore conterebbe un contenuto invece di un passo. Il registro di
        # `render/layout` conia un `patch_` per deposito e non per contenuto proprio
        # perche' questa guardia sia soddisfacibile.
        patch = [a.patch for a in self.edges]
        riusati = sorted({p for p in patch if patch.count(p) > 1})
        if riusati:
            raise ValueError(
                f"`LayoutPatch` condiviso da piu' archi: {', '.join(riusati)}. Ogni "
                "passo deposita la propria patch e ne riceve il nome: due archi "
                "sullo stesso `patch_` rendono l'evidenza di SM-14 non riferibile a "
                "un passo.")

        self._verifica_aciclicita()

    def _verifica_aciclicita(self) -> None:
        """Nessuno stato circuitale discende da se stesso.

        AD-29 vuole diramazione e ricongiungimento — quindi un DAG, non un albero e
        non una lista. Un ciclo li' dentro non sarebbe una derivazione: sarebbe uno
        stato che si deriva da se stesso, e chi ripercorre la timeline non
        terminerebbe. La stessa guardia che `check_delta` mette sulle riscritture di
        un singolo passo, un livello sopra.
        """
        successori: dict[str, list[str]] = {n.identifier: [] for n in self.nodes}
        entranti: dict[str, int] = {n.identifier: 0 for n in self.nodes}
        for a in self.edges:
            successori[a.source].append(a.target)
            entranti[a.target] += 1

        coda = [s for s, quanti in entranti.items() if quanti == 0]
        raggiunti = 0
        while coda:
            stato = coda.pop()
            raggiunti += 1
            for prossimo in successori[stato]:
                entranti[prossimo] -= 1
                if entranti[prossimo] == 0:
                    coda.append(prossimo)
        if raggiunti != len(self.nodes):
            nel_ciclo = sorted(s for s, quanti in entranti.items() if quanti > 0)
            raise ValueError(
                f"la derivazione ha un ciclo, fra {', '.join(nel_ciclo)}: uno stato "
                "circuitale discende da se stesso.")

    # --- le due direzioni della relazione ------------------------------------

    def layout_di(self, stato: str) -> str:
        """Il `lay_` dello stato visuale di quel nodo. Direzione nodo → layout."""
        for n in self.nodes:
            if n.identifier == stato:
                return n.layout
        raise KeyError(
            f"{stato!r} non e' un nodo di questo grafo. "
            f"Nodi: {', '.join(n.identifier for n in self.nodes) or 'nessuno'}.")

    def nodo_di(self, layout: str) -> str:
        """Lo stato circuitale che possiede quel layout. Direzione layout → nodo.

        E' una funzione, non una relazione, perche' il costruttore vieta a due nodi
        di dichiarare lo stesso `lay_`. Non e' un secondo registro: e' una scansione
        dell'unica direzione scritta, che e' cio' che E-62 chiede al posto di due
        mappe da tenere allineate.
        """
        for n in self.nodes:
            if n.layout == layout:
                return n.identifier
        raise KeyError(
            f"{layout!r} non e' il layout di alcun nodo di questo grafo. "
            f"Layout: {', '.join(n.layout for n in self.nodes) or 'nessuno'}.")

    # --- estensione append-only ----------------------------------------------

    def con_passo(self, nodo: ProofNode, arco: ProofEdge) -> ProofGraph:
        """Il grafo con un nodo e l'arco che ci porta. Restituisce, non modifica.

        Le guardie non stanno qui ma nel costruttore, perche' un grafo va verificato
        anche quando arriva assemblato da fuori: `ProofGraph(nodi, archi)` e'
        pubblico, e questo metodo non e' l'unica strada per costruirne uno. Qui resta
        solo cio' che questo metodo puo' dire in piu': che l'arco deve arrivare **al**
        nodo aggiunto, altrimenti «passo» e' la parola sbagliata.
        """
        if arco.target != nodo.identifier:
            raise ValueError(
                f"il passo aggiunge {nodo.identifier} ma l'arco arriva a "
                f"{arco.target}: un passo porta allo stato che aggiunge.")
        return ProofGraph((*self.nodes, nodo), (*self.edges, arco))

    def con_stato_iniziale(self, nodo: ProofNode) -> ProofGraph:
        """Il grafo con un nodo senza archi entranti — la radice, o un'altra radice.

        Esiste separato da `con_passo` perche' il primo stato circuitale non e'
        prodotto da alcuna `Transform`: darle un arco fittizio significherebbe
        dichiarare un passo che nessun `Certificate` attesta.
        """
        return ProofGraph((*self.nodes, nodo), self.edges)

    # --- cio' che serve a VCER ------------------------------------------------

    def transizioni(self) -> tuple[tuple[str, str, str], ...]:
        """Per ogni passo, la tripla `(patch_, lay_k, lay_{k+1})` di CV6.

        E' la forma in cui `eval/` riceve gli operandi di SM-14 senza rieseguire la
        derivazione: risolve i due `lay_` nel registro di `render/layout` e conta i
        `patch_` che violano `p_{k+1}(x) ≈ p_k(x)`. La tolleranza del `≈` e'
        owner-locked e non si decide qui; la rappresentazione su cui si misura e'
        il `LayoutIR`, ed e' l'aggancio che mancava.
        """
        return tuple(
            (a.patch, self.layout_di(a.source), self.layout_di(a.target))
            for a in self.edges)
