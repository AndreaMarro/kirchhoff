"""Validazione elettrica: il gate che precede la risoluzione (FR-4).

Una batteria di controlli deterministici sull'IR. Fallendo, **nomina l'elemento
coinvolto** — il nodo, il ramo o il componente — e non soltanto la regola violata:
FR-4 chiede che la diagnosi sia riusabile come testo di una Domanda mirata senza
riscrittura manuale.

Due esiti, non tre. O l'IR e' promosso, eventualmente con dei **sospetti** che non
bloccano, oppure c'e' un `Refusal`. Il sospetto esiste perche' un valore fuori dalle
serie normalizzate in un esercizio manoscritto e' quasi sempre un errore di lettura,
ma «quasi sempre» non e' «sempre»: bloccare sarebbe arroganza, tacere sarebbe
complicita'. Diventa Ambiguita' residua a valle.

L'ordine dei controlli e' fisso e il primo che fallisce vince: due esecuzioni sullo
stesso IR danno lo stesso Rifiuto, sempre.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .ir import IR, REFERENCE_NODE, Component
from .ir.schema import EXPECTED_UNIT
from .refusal import Refusal, SubjectKind

#: Serie normalizzate dei valori resistivi, per decade. Un resistore manoscritto
#: fuori da E24 e' sospetto: non vietato.
_E12: tuple[int, ...] = (10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82)
_E24: frozenset[int] = frozenset(_E12 + (11, 13, 16, 20, 24, 30, 36, 43, 51, 62, 75, 91))


@dataclass(frozen=True, slots=True)
class Suspicion:
    """Rilievo che non blocca. Diventa Ambiguita' residua, non Rifiuto."""

    subject: str
    subject_kind: SubjectKind
    note: str


@dataclass(frozen=True, slots=True)
class Validated:
    """IR promosso. I sospetti viaggiano con lui, non al posto suo."""

    ir: IR
    suspicions: tuple[Suspicion, ...] = ()


class _Insiemi:
    """Union-find minimale. Serve due volte: connessione e maglie di soli generatori."""

    def __init__(self) -> None:
        self._padre: dict[str, str] = {}

    def _radice(self, x: str) -> str:
        self._padre.setdefault(x, x)
        while self._padre[x] != x:
            self._padre[x] = self._padre[self._padre[x]]
            x = self._padre[x]
        return x

    def unisci(self, a: str, b: str) -> bool:
        """Falso quando i due erano gia' nello stesso insieme: l'arco chiude un ciclo."""
        ra, rb = self._radice(a), self._radice(b)
        if ra == rb:
            return False
        self._padre[ra] = rb
        return True

    def connessi(self, a: str, b: str) -> bool:
        return self._radice(a) == self._radice(b)


def _fuori_serie(amount: Fraction) -> bool:
    """Vero quando la mantissa a due cifre non appartiene alla serie E24."""
    m = amount
    while m >= 100:
        m /= 10
    while m < 10:
        m *= 10
    return not (m.denominator == 1 and int(m) in _E24)


def _controlla_unita(ir: IR) -> Refusal | None:
    """Difesa in profondita': lo schema lo impedisce alla costruzione, il gate lo
    respinge come Rifiuto tipizzato invece che come eccezione, per un IR che
    arrivasse per altre vie."""
    for c in sorted(ir.components, key=lambda x: x.id):
        attesa = EXPECTED_UNIT[c.type]
        if c.value.unit != attesa:
            return Refusal(
                "units", c.id, "component",
                f"{c.id} e' un {c.type} ma il suo valore e' espresso in "
                f"{c.value.unit}; per quel tipo l'unita' e' {attesa}.")
    return None


def _controlla_richieste(ir: IR) -> Refusal | None:
    noti = {c.id for c in ir.components}
    for r in sorted(ir.requests, key=lambda x: x.id):
        if r.target not in noti:
            return Refusal(
                "unsolvable", r.target, "request",
                f"La richiesta {r.id} chiede {r.quantity} di {r.target}, "
                f"che non e' un componente di questo circuito.")
    return None


def _controlla_connessione(ir: IR) -> Refusal | None:
    insiemi = _Insiemi()
    for c in ir.components:
        insiemi.unisci(c.terminals[0], c.terminals[1])
    for nodo in sorted(ir.nodes):
        if nodo == REFERENCE_NODE:
            continue
        if not insiemi.connessi(nodo, REFERENCE_NODE):
            return Refusal(
                "topology", nodo, "node",
                f"Il nodo {nodo} non e' collegato al resto del circuito: nessun percorso "
                f"lo unisce al nodo di riferimento {REFERENCE_NODE}.")
    return None


def _controlla_grado(ir: IR) -> Refusal | None:
    grado: dict[str, int] = {n: 0 for n in ir.nodes}
    for c in ir.components:
        for t in c.terminals:
            grado[t] += 1
    for nodo in sorted(ir.nodes):
        if grado[nodo] == 1:
            incidente = next(c.id for c in ir.components if nodo in c.terminals)
            return Refusal(
                "topology", nodo, "node",
                f"Nel nodo {nodo} arriva un solo terminale, quello di {incidente}: "
                f"il ramo e' aperto e non puo' passarci corrente.")
    return None


def _controlla_maglie_di_soli_generatori(ir: IR) -> Refusal | None:
    """Una maglia di soli generatori di tensione impone due valori alla stessa
    differenza di potenziale: il circuito e' contraddittorio, non difficile."""
    insiemi = _Insiemi()
    for c in sorted(ir.components, key=lambda x: x.id):
        if c.type not in ("voltage_source_dc", "voltage_source_ac"):
            continue
        if not insiemi.unisci(c.terminals[0], c.terminals[1]):
            return Refusal(
                "topology", c.id, "component",
                f"{c.id} chiude una maglia fatta di soli generatori di tensione: "
                f"due generatori ideali imporrebbero valori diversi alla stessa tensione.")
    return None


def _controlla_tagli_di_soli_generatori(ir: IR) -> Refusal | None:
    """Un nodo in cui incidono solo generatori di corrente viola la KCL, salvo che
    le correnti si annullino. Questo controllo copre il taglio piu' semplice — il
    singolo nodo — e non il caso generale a piu' nodi, che resta aperto."""
    incidenti: dict[str, list[Component]] = {n: [] for n in ir.nodes}
    for c in ir.components:
        for t in c.terminals:
            incidenti[t].append(c)
    for nodo in sorted(ir.nodes):
        rami = incidenti[nodo]
        if not rami or not all(c.type == "current_source_dc" for c in rami):
            continue
        netta = sum(
            (c.value.amount if c.terminals[1] == nodo else -c.value.amount) for c in rami)
        if netta != 0:
            return Refusal(
                "topology", nodo, "node",
                f"Nel nodo {nodo} incidono soltanto generatori di corrente e la somma "
                f"delle correnti entranti vale {netta} A invece di zero: la legge di "
                f"Kirchhoff delle correnti non puo' essere soddisfatta.")
    return None


#: I controlli, nell'ordine in cui girano. Il primo che fallisce vince.
_CONTROLLI = (
    _controlla_unita,
    _controlla_richieste,
    _controlla_connessione,
    _controlla_grado,
    _controlla_maglie_di_soli_generatori,
    _controlla_tagli_di_soli_generatori,
)


def _sospetti(ir: IR) -> tuple[Suspicion, ...]:
    """Solo su sorgente fotografica: in un IR generato o scritto a mano in netlist
    un valore fuori serie e' una scelta, non un probabile errore di lettura."""
    if ir.source_kind != "image":
        return ()
    trovati = [
        Suspicion(
            c.id, "component",
            f"{c.id} vale {c.value.amount} ohm, che non appartiene alle serie "
            f"normalizzate E12/E24: possibile errore di lettura.")
        for c in sorted(ir.components, key=lambda x: x.id)
        if c.type == "resistor" and _fuori_serie(c.value.amount)
    ]
    return tuple(trovati)


def validate(ir: IR) -> Validated | Refusal:
    """Il gate. Promuove l'IR oppure restituisce il primo Rifiuto, mai entrambi."""
    for controllo in _CONTROLLI:
        rifiuto = controllo(ir)
        if rifiuto is not None:
            return rifiuto
    return Validated(ir, _sospetti(ir))
