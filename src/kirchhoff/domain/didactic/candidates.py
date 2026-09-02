"""Enumerazione descrittiva delle sole tecniche eseguibili oggi."""

from __future__ import annotations

from dataclasses import dataclass

from ..ir import IR, Request
from ..refusal import Refusal
from .capabilities import effetto_osservazione, riduzioni_eseguibili
from .observation import ObservationContract, ObservationEffect
from .plan import PlannedAction
from .planner import pianifica


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    """Una scelta eseguibile descritta, non una scelta raccomandata."""

    technique: str
    operation: str | None
    operands: tuple[str, ...]
    actions: tuple[PlannedAction, ...]
    observation_effect: ObservationEffect | None
    admissible: bool


def enumerate_strategy_candidates(ir: IR, request: Request) -> tuple[StrategyCandidate, ...]:
    """Elenca trasformazioni certificate e il nodale che il piano corrente esegue.

    Le trasformazioni includono anche quelle P1-J bloccate: restano fatti utili al
    laboratorio, ma `admissible=False` impedisce di scambiarle per un percorso
    selezionabile.  Non vengono introdotte tecniche, punteggi o chiamate esterne.
    """
    if not isinstance(ir, IR):
        raise TypeError(f"ir {type(ir).__name__} invece di IR")
    if not isinstance(request, Request):
        raise TypeError(f"request {type(request).__name__} invece di Request")
    selected = pianifica(ir, request)
    if isinstance(selected, Refusal):
        return ()
    contract = ObservationContract.from_request(request)
    candidates = tuple(
        StrategyCandidate(
            technique="certified_transform_path",
            operation=reduction.operation,
            operands=reduction.operands,
            actions=(PlannedAction(reduction.operation, reduction.operands),),
            observation_effect=effect,
            admissible=effect.kind != "blocked",
        )
        for reduction in riduzioni_eseguibili(ir)
        for effect in (effetto_osservazione(ir, reduction, contract),)
    )
    if selected.technique == "nodal_analysis":
        return (*candidates, StrategyCandidate(
            technique="nodal_analysis",
            operation=None,
            operands=(),
            actions=selected.actions,
            observation_effect=None,
            admissible=True,
        ))
    return candidates
