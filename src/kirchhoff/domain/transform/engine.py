"""`transform(CircuitIR, params) -> (CircuitIR, TransformResult) | Refusal` (AD-2 em.).

Il catalogo e' un **registro chiuso caricato all'avvio**: `_REGISTRO` si costruisce
al momento dell'import e non espone alcuna funzione per aggiungervi una voce a
runtime. Chiedere un'operazione che non c'e' fallisce **prima di eseguire qualunque
calcolo** — la ricerca nel registro e' la prima riga di `transform`, non un
controllo a valle del lavoro.

## Perche' un'operazione fuori catalogo solleva invece di restituire un `Refusal`

AD-19 tiene chiusa l'enumerazione delle cause e assegna a questo pacchetto
esattamente tre: `identity_violation`, `preserve_nonmaximal`, `empty_boundary`.
Nessuna dice «questa operazione non esiste» o «questi due resistori non sono in
serie». Un `Refusal` e' un esito di dominio — il sistema ha guardato il circuito e
onestamente non certifica; una richiesta malformata e' invece un difetto di chi
chiama, e degradarla a `sanity` farebbe perdere all'utente la localizzazione che K-3
promette. Finche' lo spine non nomina una causa per il caso, questo modulo solleva e
lo dichiara, invece di scegliersene una.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from ..ir import IR, Component
from ..refusal import Refusal
from .catalog import CATALOG, TransformationKind
from .check import check_transform, preserve_set
from .delta import Delta, EntityRef, StructuralDerivation
from .result import Boundary, Certificate, Equation, LayoutPatch, TransformResult

#: I controlli che `check_transform` esegue, nell'ordine in cui li esegue. Il
#: `Certificate` li elenca perche' siano **verificabili**, non perche' siano
#: rassicuranti: un controllo che non ha girato non compare (E-65).
CONTROLLI: tuple[str, ...] = ("boundary", "identita'", "massimalita' di preserve")


def _resistore(ir: IR, cid: str) -> Component:
    c = ir.component(cid)
    if c.type != "resistor":
        raise ValueError(
            f"{cid}: {c.type}, e la riduzione vale fra resistori. "
            "Un'impedenza complessa e' un'altra voce del catalogo.")
    return c


def _nuovo_id(ir: IR, primo: str, secondo: str) -> str:
    """Identita' **nuova** per l'equivalente, e deterministica.

    Non si riusa il nome di una consumata: riusarlo la farebbe rientrare in `Pₖ` per
    coincidenza d'identificatore, ed e' precisamente il difetto dell'istruttoria
    R2-A. Il suffisso cresce finche' il nome e' libero, cosi' il risultato non
    dipende da quali componenti esistono gia'.
    """
    base = f"{primo}{secondo}eq"
    presi = {c.id for c in ir.components}
    nome = base
    while nome in presi:
        nome += "_"
    return nome


def _prodotto(
    prima: IR,
    dopo: IR,
    operazione: TransformationKind,
    consumati: tuple[EntityRef, ...],
    prodotto: EntityRef,
    rimossi: tuple[EntityRef, ...],
    boundary: Boundary,
    equazione: Equation,
) -> tuple[IR, TransformResult] | Refusal:
    """Assembla i sei membri, dopo che `check_transform` ha dato il proprio esito.

    `boundary` arriva gia' costruito: le due riduzioni qui sotto ne hanno sempre uno,
    perche' una fusione confina per definizione con i nodi che le restano attorno.
    `empty_boundary` non e' percio' irraggiungibile — e' raggiungibile da dove deve
    esserlo, cioe' da `check_transform`, che e' il controllore e riceve anche
    `boundary` dichiarati da altri produttori.
    """
    preservate = preserve_set(prima, dopo, operation=operazione)
    patch = LayoutPatch(
        preserve=tuple(sorted(preservate)),
        remove=rimossi,
        create=(prodotto,),
        node_mapping=(),
        reroute_scope=(prodotto, *boundary.entities),
    )

    rifiuto = check_transform(prima, dopo, operazione, patch, boundary)
    if rifiuto is not None:
        return rifiuto

    return dopo, TransformResult(
        preserve=preservate,
        delta=Delta((StructuralDerivation(operazione, consumati, (prodotto,)),)),
        boundary=boundary,
        layout_patch=patch,
        equation=equazione,
        certificate=Certificate(operazione, CONTROLLI),
    )


def _serie(ir: IR, primo: str, secondo: str) -> tuple[IR, TransformResult] | Refusal:
    """`R1 (a,b)` e `R2 (b,c)` diventano una equivalente `(a,c)`, e `b` sparisce."""
    a, b = _resistore(ir, primo), _resistore(ir, secondo)
    comune = set(a.terminals) & set(b.terminals)
    if len(comune) != 1:
        raise ValueError(
            f"{primo} e {secondo} condividono {len(comune)} nodi: la serie ne vuole "
            "esattamente uno.")
    nodo = comune.pop()
    tocca = [c.id for c in ir.components if nodo in c.terminals]
    if len(tocca) != 2:
        raise ValueError(
            f"il nodo {nodo} ha grado {len(tocca)} ({', '.join(sorted(tocca))}): "
            "in serie ci stanno due componenti soli, altrimenti la corrente si "
            "divide e la somma delle resistenze non e' l'equivalente.")

    estremi = (
        next(t for t in a.terminals if t != nodo),
        next(t for t in b.terminals if t != nodo),
    )
    eq = Component.of(
        _nuovo_id(ir, primo, secondo), "resistor", estremi,
        a.value.amount + b.value.amount, f"({a.symbolic} + {b.symbolic})")
    dopo = _senza(ir, (primo, secondo), (nodo,), eq)

    return _prodotto(
        ir, dopo, "serie",
        consumati=(EntityRef("component", primo), EntityRef("component", secondo)),
        prodotto=EntityRef("component", eq.id),
        rimossi=(EntityRef("component", primo), EntityRef("component", secondo),
                 EntityRef("node", nodo)),
        boundary=Boundary((EntityRef("node", estremi[0]),
                           EntityRef("node", estremi[1]))),
        equazione=Equation(eq.symbolic, f"{a.symbolic} + {b.symbolic}"),
    )


def _parallelo(ir: IR, primo: str, secondo: str) -> tuple[IR, TransformResult] | Refusal:
    """`R1 (a,b)` e `R2 (a,b)` diventano una equivalente sugli stessi due nodi."""
    a, b = _resistore(ir, primo), _resistore(ir, secondo)
    if set(a.terminals) != set(b.terminals):
        raise ValueError(
            f"{primo} {a.terminals} e {secondo} {b.terminals} non stanno fra gli "
            "stessi due nodi: non sono in parallelo.")

    ra, rb = a.value.amount, b.value.amount
    eq = Component.of(
        _nuovo_id(ir, primo, secondo), "resistor", a.terminals,
        Fraction(ra * rb, ra + rb),
        f"({a.symbolic}·{b.symbolic} / ({a.symbolic} + {b.symbolic}))")
    dopo = _senza(ir, (primo, secondo), (), eq)

    return _prodotto(
        ir, dopo, "parallelo",
        consumati=(EntityRef("component", primo), EntityRef("component", secondo)),
        prodotto=EntityRef("component", eq.id),
        rimossi=(EntityRef("component", primo), EntityRef("component", secondo)),
        boundary=Boundary((EntityRef("node", a.terminals[0]),
                           EntityRef("node", a.terminals[1]))),
        equazione=Equation(
            eq.symbolic,
            f"{a.symbolic}·{b.symbolic} / ({a.symbolic} + {b.symbolic})"),
    )


def _senza(ir: IR, componenti: tuple[str, ...], nodi: tuple[str, ...],
           aggiunto: Component) -> IR:
    """`Cₖ₊₁`: gli stessi campi, meno cio' che e' stato consumato, piu' l'equivalente."""
    return IR(
        ir.ir_version, ir.domain, ir.source_kind,
        tuple(n for n in ir.nodes if n not in nodi),
        (*(c for c in ir.components if c.id not in componenti), aggiunto),
        ir.requests, ir.omega,
    )


#: Il registro chiuso, costruito all'import. Non esiste una `register()`: estenderlo
#: e' una modifica del catalogo, non una chiamata.
_REGISTRO: dict[str, Callable[..., tuple[IR, TransformResult] | Refusal]] = {
    "serie": _serie,
    "parallelo": _parallelo,
}


def implemented() -> frozenset[str]:
    """Le voci del catalogo che hanno gia' un'implementazione.

    Il catalogo e' chiuso e completo; le implementazioni arrivano una storia alla
    volta. Tenere i due insiemi distinti e interrogabili evita che «non ancora
    scritta» e «non esiste» si confondano — sono due risposte diverse a chi pianifica.
    """
    return frozenset(_REGISTRO)


def transform(
    ir: IR, operation: TransformationKind, *args: str,
) -> tuple[IR, TransformResult] | Refusal:
    """La firma di AD-2 em. Pura: nessuna I/O, nessun orologio, nessuna casualita'."""
    if operation not in CATALOG:
        raise ValueError(
            f"operazione {operation!r} fuori dal catalogo chiuso: "
            f"{', '.join(sorted(CATALOG))}. Il catalogo si carica all'avvio e non "
            "si estende a runtime.")
    if operation not in _REGISTRO:
        raise NotImplementedError(
            f"{operation}: nel catalogo ma senza implementazione. "
            f"Implementate finora: {', '.join(sorted(_REGISTRO))}.")
    return _REGISTRO[operation](ir, *args)
