"""Confine fail-closed per i fatti di strategia P1-M0."""

from __future__ import annotations

from ..ir import IR, Request
from ..refusal import Refusal
from ..validate import Validated, validate
from .capabilities import DIDACTIC_NODAL_COMPONENT_TYPES
from .observation import OBSERVABLE_QUANTITIES


def strategy_scope_refusal(ir: IR, request: Request) -> Refusal | None:
    """Rifiuta fatti P1-M0 fuori da DC osservabile e dal subset didattico attuale."""
    matching_ids = tuple(item for item in ir.requests if item.id == request.id)
    if len(matching_ids) != 1:
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: l'identificatore Request deve comparire una sola volta nell'IR.",
        )
    if matching_ids[0] != request:
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: la Request passata non e' quella dichiarata nell'IR.",
        )
    try:
        ir.component(request.target)
    except KeyError:
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: il target {request.target} non appartiene al circuito.",
        )
    validation = validate(ir)
    if not isinstance(validation, Validated):
        return validation
    if ir.domain != "dc":
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: P1-M0 espone candidati solo per il dominio dc.",
        )
    if request.quantity not in OBSERVABLE_QUANTITIES:
        return Refusal(
            "unsolvable", request.id, "request",
            f"{request.id}: P1-M0 espone candidati solo per voltage o current.",
        )
    unsupported = tuple(
        component.id for component in ir.components
        if component.type not in DIDACTIC_NODAL_COMPONENT_TYPES
    )
    if unsupported:
        return Refusal(
            "unsolvable", unsupported[0], "component",
            f"{unsupported[0]}: tipo fuori dal subset didattico DC P1-M0.",
        )
    return None
