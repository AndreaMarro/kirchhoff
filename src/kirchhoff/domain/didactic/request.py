"""Risoluzione didattica di una Request sulla soluzione nodale già calcolata.

Trasforma Request + semantica del componente + DerivationSolution nella
grandezza fisica chiesta. Non rilegge il circuito per risolverlo di nuovo:
le tensioni nodali arrivano dalla derivazione P1-G.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..ir import IR, REFERENCE_NODE, Component, Magnitude, Request
from .solve import DerivationSolution

_RESOLVABLE_QUANTITIES: frozenset[str] = frozenset({"voltage", "current"})
_RESOLVABLE_TYPES: frozenset[str] = frozenset({
    "resistor",
    "current_source_dc",
    "voltage_source_dc",
})


@dataclass(frozen=True, slots=True)
class ResolvedQuantity:
    """Grandezza fisica esatta, orientata e con unità."""

    derivation_id: str
    request_id: str
    target: str
    quantity: str
    orientation: tuple[str, str]
    value: Magnitude

    def __post_init__(self) -> None:
        if not self.derivation_id:
            raise ValueError("ResolvedQuantity senza derivation_id")
        if not self.request_id:
            raise ValueError("ResolvedQuantity senza request_id")
        if not self.target:
            raise ValueError("ResolvedQuantity senza target")
        if self.quantity not in _RESOLVABLE_QUANTITIES:
            raise ValueError(
                f"quantity {self.quantity!r} fuori da "
                f"{', '.join(sorted(_RESOLVABLE_QUANTITIES))}")
        if len(self.orientation) != 2 or self.orientation[0] == self.orientation[1]:
            raise ValueError(
                f"orientation {self.orientation!r}: servono esattamente "
                "due nodi distinti")
        if not isinstance(self.value, Magnitude):
            raise TypeError(
                f"value {type(self.value).__name__}, serve una Magnitude")
        if self.quantity == "voltage" and self.value.unit != "volt":
            raise ValueError(
                f"quantity voltage con unità {self.value.unit!r}, serve volt")
        if self.quantity == "current" and self.value.unit != "ampere":
            raise ValueError(
                f"quantity current con unità {self.value.unit!r}, serve ampere")


def resolve_request(
    ir: IR,
    request: Request,
    solution: DerivationSolution,
) -> ResolvedQuantity:
    """Deriva la grandezza chiesta dalle tensioni nodali già risolte."""
    _validare_contesto(ir, request, solution)
    componente = ir.component(request.target)
    tensioni = _tensioni_nodali(solution)
    if request.quantity == "voltage":
        amount = _tensione_del_componente(componente, tensioni)
        unita = "volt"
    else:
        amount = _corrente_del_componente(ir, componente, tensioni)
        unita = "ampere"
    return ResolvedQuantity(
        derivation_id=solution.derivation_id,
        request_id=request.id,
        target=request.target,
        quantity=request.quantity,
        orientation=componente.terminals,
        value=Magnitude(amount, unita),
    )


def _validare_contesto(
    ir: IR,
    request: Request,
    solution: DerivationSolution,
) -> None:
    if ir.domain != "dc":
        raise ValueError(
            f"dominio {ir.domain!r}: resolve_request opera solo in continua")
    try:
        componente = ir.component(request.target)
    except KeyError as exc:
        raise ValueError(
            f"{request.id}: target {request.target!r} assente dall'IR"
        ) from exc
    if request.quantity not in _RESOLVABLE_QUANTITIES:
        raise ValueError(
            f"{request.id}: quantity {request.quantity!r} non risolvibile "
            f"in P1-H (ammesse: {', '.join(sorted(_RESOLVABLE_QUANTITIES))})")
    if componente.type not in _RESOLVABLE_TYPES:
        raise ValueError(
            f"{request.id}: {componente.type} non è un tipo risolvibile "
            f"({', '.join(sorted(_RESOLVABLE_TYPES))})")
    _assert_chiusura_soluzione_ir(ir, solution)


def _assert_chiusura_soluzione_ir(ir: IR, solution: DerivationSolution) -> None:
    solution_nodes = {item.variable.node for item in solution.values}
    ir_nodes = set(ir.nodes)
    mancanti = ir_nodes - solution_nodes
    if mancanti:
        raise ValueError(
            f"{solution.derivation_id}: la soluzione manca i nodi IR "
            f"{', '.join(sorted(mancanti))}")
    extra = solution_nodes - ir_nodes
    if extra:
        raise ValueError(
            f"{solution.derivation_id}: la soluzione contiene nodi extra "
            f"{', '.join(sorted(extra))}")


def _tensioni_nodali(solution: DerivationSolution) -> dict[str, Fraction]:
    return {item.variable.node: item.value for item in solution.values}


def _tensione_ai_terminali(
    terminals: tuple[str, str],
    tensioni: dict[str, Fraction],
) -> Fraction:
    p, q = terminals
    return tensioni[p] - tensioni[q]


def _tensione_del_componente(
    componente: Component,
    tensioni: dict[str, Fraction],
) -> Fraction:
    vd = _tensione_ai_terminali(componente.terminals, tensioni)
    if componente.type == "voltage_source_dc" and vd != componente.value.amount:
        raise ValueError(
            f"{componente.id}: tensione derivata {vd} "
            f"≠ amount {componente.value.amount}")
    return vd


def _corrente_del_componente(
    ir: IR,
    componente: Component,
    tensioni: dict[str, Fraction],
) -> Fraction:
    if componente.type == "resistor":
        return _tensione_ai_terminali(componente.terminals, tensioni) / componente.value.amount
    if componente.type == "current_source_dc":
        return componente.value.amount
    return _corrente_generatore_tensione(ir, componente, tensioni)


def _branch_current_from_solution(
    component: Component,
    tensioni: dict[str, Fraction],
) -> Fraction:
    """Corrente di un altro ramo, positiva terminals[0] → terminals[1]."""
    if component.type == "resistor":
        return _tensione_ai_terminali(component.terminals, tensioni) / component.value.amount
    if component.type == "current_source_dc":
        return component.value.amount
    if component.type == "voltage_source_dc":
        raise ValueError(
            f"unsupported topology: voltage source {component.id} "
            "incident on another voltage-source terminal")
    raise ValueError(
        f"unsupported branch type {component.type} while deriving "
        "voltage-source current")


def _uscente_dal_nodo(nodo: str, component: Component, corrente: Fraction) -> Fraction:
    p, _q = component.terminals
    if nodo == p:
        return corrente
    return -corrente


def _somma_uscenti(
    ir: IR,
    nodo: str,
    escluso: str,
    tensioni: dict[str, Fraction],
) -> Fraction:
    totale = Fraction(0)
    for componente in ir.components:
        if componente.id == escluso or nodo not in componente.terminals:
            continue
        corrente = _branch_current_from_solution(componente, tensioni)
        totale += _uscente_dal_nodo(nodo, componente, corrente)
    return totale


def _corrente_generatore_tensione(
    ir: IR,
    sorgente: Component,
    tensioni: dict[str, Fraction],
) -> Fraction:
    p, q = sorgente.terminals
    if q == REFERENCE_NODE:
        return -_somma_uscenti(ir, p, sorgente.id, tensioni)
    if p == REFERENCE_NODE:
        return _somma_uscenti(ir, q, sorgente.id, tensioni)
    candidato_p = -_somma_uscenti(ir, p, sorgente.id, tensioni)
    candidato_q = _somma_uscenti(ir, q, sorgente.id, tensioni)
    if candidato_p != candidato_q:
        raise ValueError(
            "derived voltage-source current violates terminal KCL agreement")
    return candidato_p
