"""La tripla di CV6, risolta: gli operandi su cui VCER si calcola.

CV6: *«perche' la metrica sia calcolabile serve, per ogni passo, la tripla
`(LayoutPatch, LayoutIR_k, LayoutIR_{k+1})` **congiungibile**»*. `ProofGraph`
scrive i tre identificatori, `LayoutStore` e `PatchStore` ritengono i tre oggetti,
e questo modulo li congiunge — verificando che la giunzione regga davvero, invece
di presumerlo.

## Perche' una congiunzione verificata e non tre `risolvi`

Tre risoluzioni indipendenti riescono anche quando la tripla non significa nulla:
un nodo puo' nominare un `lay_` mai depositato, e un `LayoutPatch` puo' dichiarare
di preservare un'entita' che in uno dei due stati visuali non e' piazzata. In
quest'ultimo caso `p_k(x)` **non e' definita** per qualche `x ∈ Pₖ`, e il predicato
`p_{k+1}(x) ≈ p_k(x)` che SM-14 conta non ha operandi: la metrica misurerebbe un
`KeyError` invece della continuita' visuale. Le cinque condizioni sono qui, in un
posto solo, perche' un'evidenza che dice «VCER = 0.97» deve poter dire su quali
operandi.

## Che cosa questo modulo NON fa

**Non calcola VCER.** Non confronta due posizioni e non conosce la tolleranza del
`≈`, che e' owner-locked. Restituisce cio' su cui il confronto si fa, e chi lo fa e'
`eval/` (AD-15: *«TUTTE le metriche di §8 incluso VCER»*). La Story 1.3 rende
**osservabile**, non misura.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.proof import ProofGraph
from ...domain.transform import EntityRef, LayoutPatch
from .schema import LayoutIR
from .store import LayoutStore, PatchStore


@dataclass(frozen=True, slots=True)
class OperandiVCER:
    """Un passo, con i suoi tre operandi gia' risolti e gia' congiungibili."""

    patch_id: str
    patch: LayoutPatch
    prima: LayoutIR
    dopo: LayoutIR

    def dominio(self) -> tuple[EntityRef, ...]:
        """Le `x` su cui `p_{k+1}(x) ≈ p_k(x)` va deciso, cioe' `Pₖ`.

        E' `patch.preserve`, e `operandi_di_vcer` ha gia' verificato che ognuna sia
        piazzata in **entrambi** gli stati visuali: `prima.posizione(x)` e
        `dopo.posizione(x)` non sollevano per nessuna `x` di questa tupla.
        """
        return self.patch.preserve


def _fuori(entita: tuple[EntityRef, ...], piazzate: frozenset[EntityRef]) -> str:
    return ", ".join(sorted(str(e) for e in entita if e not in piazzate))


def operandi_di_vcer(
    grafo: ProofGraph, layout: LayoutStore, patch: PatchStore
) -> tuple[OperandiVCER, ...]:
    """Per ogni passo del grafo, la tripla risolta. Solleva su ogni giunzione rotta.

    Le cinque condizioni, nell'ordine in cui rompono la metrica:

    1. ogni `lay_` nominato da un nodo e' depositato in `layout`;
    2. ogni `patch_` nominato da un arco e' depositato in `patch`;
    3. `preserve ⊆ entita(LayoutIR_k) ∩ entita(LayoutIR_{k+1})` — altrimenti `p_k`
       o `p_{k+1}` non e' definita dove SM-14 la valuta;
    4. `remove ⊆ entita(LayoutIR_k)` — non si toglie cio' che non c'era;
    5. `create ⊆ entita(LayoutIR_{k+1})` — cio' che si crea dev'essere finito
       da qualche parte, o il passo ha ordinato al renderer una cosa che non ha fatto.

    Solleva invece di restituire un `Refusal`: AD-13 riguarda gli esiti di dominio
    che l'utente legge, e questa non e' una risposta all'utente — e' un'incoerenza
    fra un grafo e i due registri, cioe' un difetto del programma.
    """
    if not isinstance(grafo, ProofGraph):
        raise TypeError(f"{type(grafo).__name__} invece di ProofGraph")

    for nodo in grafo.nodes:
        if nodo.layout not in layout:
            raise KeyError(
                f"il nodo {nodo.identifier} nomina {nodo.layout}, che non e' "
                "depositato: la relazione nodo ↔ layout e' interrogabile ma non "
                f"risolvibile. Depositati: {', '.join(layout.identificatori()) or 'nessuno'}.")

    triple: list[OperandiVCER] = []
    for arco in grafo.edges:
        if arco.patch not in patch:
            raise KeyError(
                f"l'arco {arco.source} -{arco.operation}-> {arco.target} nomina "
                f"{arco.patch}, che non e' depositato: senza il `LayoutPatch` manca "
                "`preserve`, cioe' il dominio su cui VCER si calcola.")

        oggetto = patch.risolvi(arco.patch)
        prima = layout.risolvi(grafo.layout_di(arco.source))
        dopo = layout.risolvi(grafo.layout_di(arco.target))
        qui = frozenset(prima.entita())
        la = frozenset(dopo.entita())

        mancanti = _fuori(oggetto.preserve, qui & la)
        if mancanti:
            raise ValueError(
                f"{arco.patch}: {mancanti} in `preserve` ma non piazzata in "
                f"entrambi gli stati visuali ({prima.identifier}, {dopo.identifier}). "
                "SM-14 valuta `p_{k+1}(x) ≈ p_k(x)` per ogni `x ∈ Pₖ`, e li' quel "
                "confronto non ha due operandi.")
        mancanti = _fuori(oggetto.remove, qui)
        if mancanti:
            raise ValueError(
                f"{arco.patch}: {mancanti} in `remove` ma non piazzata in "
                f"{prima.identifier}. Il passo toglie al renderer cio' che non c'era.")
        mancanti = _fuori(oggetto.create, la)
        if mancanti:
            raise ValueError(
                f"{arco.patch}: {mancanti} in `create` ma non piazzata in "
                f"{dopo.identifier}. Il passo dichiara di crearla e lo stato visuale "
                "successivo non la contiene.")

        triple.append(OperandiVCER(arco.patch, oggetto, prima, dopo))

    return tuple(triple)
