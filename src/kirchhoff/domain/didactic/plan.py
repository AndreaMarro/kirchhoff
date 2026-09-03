"""`DidacticPlan`: oggetto immutabile, deterministico, serializzabile in forma canonica."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .kinds import PLAN_SCHEMA_VERSION, PROFILE, TECHNIQUES


@dataclass(frozen=True, slots=True)
class PlanReason:
    """Perché il planner ha scelto quella tecnica. Campi strutturali, non prosa."""

    topology_reducible: bool
    request_reachable: bool
    exact_solver_available: bool
    contributing_certified_reduction: bool
    unimplemented_supported_names: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "unimplemented_supported_names",
            tuple(sorted(self.unimplemented_supported_names)),
        )


@dataclass(frozen=True, slots=True)
class PlannedAction:
    """Un atto previsto, nominato e con operandi canonici."""

    kind: str
    operands: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.kind:
            raise ValueError("azione pianificata senza kind")
        object.__setattr__(self, "operands", tuple(self.operands))


@dataclass(frozen=True, slots=True)
class DidacticPlan:
    """Piano didattico minimo per lo slice 0.1."""

    schema_version: str
    profile: str
    request_id: str
    technique: str
    reason: PlanReason
    actions: tuple[PlannedAction, ...]

    def __post_init__(self) -> None:
        if self.schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version {self.schema_version!r}: attesa {PLAN_SCHEMA_VERSION}")
        if self.profile != PROFILE:
            raise ValueError(f"profile {self.profile!r}: atteso {PROFILE}")
        if not self.request_id:
            raise ValueError("piano senza riferimento alla Request")
        if self.technique not in TECHNIQUES:
            raise ValueError(
                f"tecnica {self.technique!r} fuori dal vocabolario eseguibile: "
                f"{', '.join(sorted(TECHNIQUES))}")
        if not isinstance(self.reason, PlanReason):
            raise TypeError(
                f"reason {type(self.reason).__name__} invece di PlanReason")
        object.__setattr__(self, "actions", tuple(self.actions))
        for azione in self.actions:
            if not isinstance(azione, PlannedAction):
                raise TypeError(
                    f"{type(azione).__name__} fra le azioni invece di PlannedAction")
        if not self.actions:
            raise ValueError(
                "piano senza azioni: una tecnica selezionata deve dire cosa fare")

    def canonical_json(self) -> str:
        """Serializzazione stabile: chiavi ordinate, tuple come liste."""
        payload = {
            "actions": [
                {"kind": a.kind, "operands": list(a.operands)} for a in self.actions
            ],
            "profile": self.profile,
            "reason": {
                "contributing_certified_reduction": (
                    self.reason.contributing_certified_reduction),
                "exact_solver_available": self.reason.exact_solver_available,
                "request_reachable": self.reason.request_reachable,
                "topology_reducible": self.reason.topology_reducible,
                "unimplemented_supported_names": list(
                    self.reason.unimplemented_supported_names),
            },
            "request_id": self.request_id,
            "schema_version": self.schema_version,
            "technique": self.technique,
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
