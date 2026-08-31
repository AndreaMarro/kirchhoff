"""Planner didattico puro e deterministico.

Ingresso: IR validato e una `Request` esistente.
Uscita: `DidacticPlan` oppure `Refusal`.
Niente LLM, niente orologio, niente I/O, niente nomi di fixture.
"""

from __future__ import annotations

from ..ir import IR, REFERENCE_NODE, Request
from ..refusal import Refusal
from ..transform.catalog import SUPPORTED
from ..transform.engine import implemented
from ..validate import validate, Validated
from .capabilities import (
    nodale_disponibile,
    riduzioni_che_contribuiscono,
    riduzioni_eseguibili,
)
from .kinds import PLAN_SCHEMA_VERSION, PROFILE
from .plan import DidacticPlan, PlanReason, PlannedAction


def _nomi_supportati_senza_corpo() -> tuple[str, ...]:
    return tuple(sorted(SUPPORTED - implemented()))


def _azioni_nodali(ir: IR) -> tuple[PlannedAction, ...]:
    from .analytical import _generatori_verso_riferimento, nodi_kcl_ordinarie

    azioni = [PlannedAction("choose_reference", ())]
    fissi = _generatori_verso_riferimento(ir)
    if any(n != REFERENCE_NODE and n not in fissi for n in ir.nodes):
        azioni.append(PlannedAction("define_nodal_unknowns", ()))
    for nodo in nodi_kcl_ordinarie(ir):
        azioni.append(PlannedAction("write_kcl", (nodo,)))
    return tuple(azioni)


def pianifica(ir: IR, request: Request) -> DidacticPlan | Refusal:
    """Classifica il circuito e sceglie l'unica tecnica eseguibile che serve."""
    esito = validate(ir)
    if not isinstance(esito, Validated):
        return esito

    try:
        ir.component(request.target)
    except KeyError:
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: la grandezza {request.quantity} è chiesta su "
            f"{request.target}, che non è un componente di questo circuito.",
        )

    riduzioni = riduzioni_eseguibili(ir)
    utili = riduzioni_che_contribuiscono(ir, request.target, request.quantity)
    solver = nodale_disponibile(ir, request.quantity)
    raggiungibile = bool(utili) or solver
    reason = PlanReason(
        topology_reducible=bool(riduzioni),
        request_reachable=raggiungibile,
        exact_solver_available=solver,
        contributing_certified_reduction=bool(utili),
        unimplemented_supported_names=_nomi_supportati_senza_corpo(),
    )

    if utili:
        prima = utili[0]
        return DidacticPlan(
            PLAN_SCHEMA_VERSION, PROFILE, request.id,
            "certified_transform_path", reason,
            (PlannedAction(prima.operation, prima.operands),),
        )

    if solver:
        return DidacticPlan(
            PLAN_SCHEMA_VERSION, PROFILE, request.id,
            "nodal_analysis", reason, _azioni_nodali(ir),
        )

    return Refusal(
        "unsolvable", request.id, "request",
        f"{request.id}: nessuna tecnica eseguibile raggiunge "
        f"{request.quantity} su {request.target}. "
        f"Riduzioni certificate utili: nessuna. "
        f"Analisi nodale disponibile: no. "
        f"Nomi supportati senza corpo: {', '.join(reason.unimplemented_supported_names) or 'nessuno'}.",
    )
