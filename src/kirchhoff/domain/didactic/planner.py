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
from .observation import OBSERVABLE_QUANTITIES, ObservationContract
from .plan import DidacticPlan, PlanReason, PlannedAction


def _nomi_supportati_senza_corpo() -> tuple[str, ...]:
    return tuple(sorted(SUPPORTED - implemented()))


def _azioni_nodali(ir: IR) -> tuple[PlannedAction, ...]:
    from .analytical import (
        nodi_kcl_ordinarie,
        supernodi_semplici,
    )

    azioni = [PlannedAction("choose_reference", ())]
    if any(n != REFERENCE_NODE for n in ir.nodes):
        # Dichiara anche i noti da generatore verso massa: uno stato
        # terminale senza incognite conserva comunque le tensioni note.
        azioni.append(PlannedAction("define_nodal_unknowns", ()))
    for nodo in nodi_kcl_ordinarie(ir):
        azioni.append(PlannedAction("write_kcl", (nodo,)))
    for sn in supernodi_semplici(ir):
        azioni.append(PlannedAction("write_kcl", (sn.source_id, sn.p, sn.q)))
        azioni.append(PlannedAction("write_voltage_constraint", (sn.source_id,)))
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
    utili = (
        riduzioni_che_contribuiscono(
            ir, ObservationContract.from_request(request))
        if request.quantity in OBSERVABLE_QUANTITIES
        else ()
    )
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
