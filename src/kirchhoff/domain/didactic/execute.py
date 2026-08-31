"""Esecutore deterministico di un `DidacticPlan` già deciso.

Il piano è un ingresso. Questo modulo non decide un nuovo piano, non riseleziona
una trasformazione e non remappa una Request il cui target è stato
consumato. Collega soltanto:

    piano.actions  →  applica_passo / transform
    DerivationState  →  solve_derivation
    DerivationSolution  →  resolve_request
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from ..identity import verifica
from ..ir import IR, Request
from ..refusal import Refusal
from ..transform.engine import transform
from ..transform.result import TransformResult
from .analytical import AnalyticalStep, applica_passo, stato_iniziale
from .derivation import DerivationState
from .kinds import ANALYTICAL_KINDS, PLAN_SCHEMA_VERSION
from .plan import DidacticPlan
from .request import ResolvedQuantity, resolve_request
from .solve import DerivationSolution, solve_derivation


@dataclass(frozen=True, slots=True)
class NodalExecution:
    """Replay completo di un piano `nodal_analysis`."""

    proof_node: str
    plan: DidacticPlan
    steps: tuple[AnalyticalStep, ...]
    derivation: DerivationState
    solution: DerivationSolution
    resolved: ResolvedQuantity

    def __post_init__(self) -> None:
        object.__setattr__(self, "proof_node", verifica(self.proof_node, "ir"))
        if not isinstance(self.plan, DidacticPlan):
            raise TypeError(
                f"plan {type(self.plan).__name__} invece di DidacticPlan")
        if self.plan.technique != "nodal_analysis":
            raise ValueError(
                f"NodalExecution con tecnica {self.plan.technique!r}, "
                "serve nodal_analysis")
        object.__setattr__(self, "steps", tuple(self.steps))
        if not self.steps:
            raise ValueError("NodalExecution senza passi analitici")
        if len(self.steps) != len(self.plan.actions):
            raise ValueError(
                f"NodalExecution: {len(self.steps)} passi contro "
                f"{len(self.plan.actions)} azioni pianificate")
        for i, (passo, azione) in enumerate(zip(self.steps, self.plan.actions)):
            if not isinstance(passo, AnalyticalStep):
                raise TypeError(
                    f"steps[{i}] {type(passo).__name__} invece di AnalyticalStep")
            if passo.kind != azione.kind:
                raise ValueError(
                    f"steps[{i}].kind {passo.kind!r} ≠ "
                    f"actions[{i}].kind {azione.kind!r}")
        if self.steps[0].derivation_before != "D0":
            raise ValueError(
                f"catena nodale: il primo passo parte da "
                f"{self.steps[0].derivation_before!r}, atteso D0")
        for i in range(len(self.steps) - 1):
            if self.steps[i].derivation_after != self.steps[i + 1].derivation_before:
                raise ValueError(
                    f"catena nodale spezzata fra i passi {i} e {i + 1}: "
                    f"{self.steps[i].derivation_after} → "
                    f"{self.steps[i + 1].derivation_before}")
        if not isinstance(self.derivation, DerivationState):
            raise TypeError(
                f"derivation {type(self.derivation).__name__} "
                "invece di DerivationState")
        if self.derivation.identifier != self.steps[-1].derivation_after:
            raise ValueError(
                f"derivation {self.derivation.identifier} ≠ "
                f"ultimo passo {self.steps[-1].derivation_after}")
        if self.derivation.proof_node != self.proof_node:
            raise ValueError(
                f"derivation.proof_node {self.derivation.proof_node!r} ≠ "
                f"{self.proof_node!r}")
        if not isinstance(self.solution, DerivationSolution):
            raise TypeError(
                f"solution {type(self.solution).__name__} "
                "invece di DerivationSolution")
        if self.solution.derivation_id != self.derivation.identifier:
            raise ValueError(
                f"solution.derivation_id {self.solution.derivation_id} ≠ "
                f"{self.derivation.identifier}")
        if not isinstance(self.resolved, ResolvedQuantity):
            raise TypeError(
                f"resolved {type(self.resolved).__name__} "
                "invece di ResolvedQuantity")
        if self.resolved.derivation_id != self.solution.derivation_id:
            raise ValueError(
                f"resolved.derivation_id {self.resolved.derivation_id} ≠ "
                f"{self.solution.derivation_id}")
        if self.resolved.request_id != self.plan.request_id:
            raise ValueError(
                f"resolved.request_id {self.resolved.request_id!r} ≠ "
                f"plan.request_id {self.plan.request_id!r}")


@dataclass(frozen=True, slots=True)
class TransformExecution:
    """Replay di un piano `certified_transform_path`. Non risolve la Request."""

    proof_node: str
    plan: DidacticPlan
    before: IR
    after: IR
    results: tuple[TransformResult, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "proof_node", verifica(self.proof_node, "ir"))
        if not isinstance(self.plan, DidacticPlan):
            raise TypeError(
                f"plan {type(self.plan).__name__} invece di DidacticPlan")
        if self.plan.technique != "certified_transform_path":
            raise ValueError(
                f"TransformExecution con tecnica {self.plan.technique!r}, "
                "serve certified_transform_path")
        if not isinstance(self.before, IR):
            raise TypeError(f"before {type(self.before).__name__} invece di IR")
        if not isinstance(self.after, IR):
            raise TypeError(f"after {type(self.after).__name__} invece di IR")
        object.__setattr__(self, "results", tuple(self.results))
        if not self.results:
            raise ValueError("TransformExecution senza risultati")
        if len(self.results) != len(self.plan.actions):
            raise ValueError(
                f"TransformExecution: {len(self.results)} risultati contro "
                f"{len(self.plan.actions)} azioni pianificate")
        for i, risultato in enumerate(self.results):
            if not isinstance(risultato, TransformResult):
                raise TypeError(
                    f"results[{i}] {type(risultato).__name__} "
                    "invece di TransformResult")


DidacticExecution: TypeAlias = NodalExecution | TransformExecution


def execute_plan(
    ir: IR,
    request: Request,
    plan: DidacticPlan,
    *,
    proof_node: str,
) -> DidacticExecution | Refusal:
    """Esegue esattamente le azioni del piano. Il piano è un ingresso."""
    if not isinstance(plan, DidacticPlan):
        raise TypeError(f"plan {type(plan).__name__} invece di DidacticPlan")
    proof_node = verifica(proof_node, "ir")
    _assert_request_plan_binding(request, plan)
    _assert_request_ir_binding(ir, request)
    if plan.technique == "nodal_analysis":
        return _execute_nodal(ir, request, plan, proof_node)
    if plan.technique == "certified_transform_path":
        return _execute_transform(ir, plan, proof_node)
    raise ValueError(  # pragma: no cover
        f"tecnica {plan.technique!r} senza percorso di esecuzione")


def _assert_request_plan_binding(request: Request, plan: DidacticPlan) -> None:
    if plan.request_id != request.id:
        raise ValueError(
            f"plan.request_id {plan.request_id!r} ≠ request.id {request.id!r}")


def _assert_request_ir_binding(ir: IR, request: Request) -> None:
    matching_by_id = tuple(r for r in ir.requests if r.id == request.id)
    if len(matching_by_id) == 0:
        raise ValueError(
            f"request {request.id!r} non appartiene all'IR")
    if len(matching_by_id) > 1:
        raise ValueError(
            f"request id {request.id!r} ambiguo nell'IR")
    if matching_by_id[0] != request:
        raise ValueError(
            f"request {request.id}: context mismatch fra argomento e IR "
            f"(quantity/target {request.quantity}/{request.target} ≠ "
            f"{matching_by_id[0].quantity}/{matching_by_id[0].target})")


def _execute_nodal(
    ir: IR,
    request: Request,
    plan: DidacticPlan,
    proof_node: str,
) -> NodalExecution:
    passi: list[AnalyticalStep] = []
    state = stato_iniziale(proof_node)
    for action in plan.actions:
        if action.kind not in ANALYTICAL_KINDS:
            raise ValueError(
                f"technique/action mismatch: piano nodal_analysis con "
                f"azione {action.kind!r}")
        before = state
        step, state = applica_passo(
            action.kind, ir, state, operands=action.operands,
        )
        if step.kind != action.kind:
            raise ValueError(
                f"esecutore: passo {step.kind!r} ≠ azione {action.kind!r}")
        if step.proof_node != proof_node or state.proof_node != proof_node:
            raise ValueError(
                f"esecutore: proof_node deriva a {step.proof_node!r}/"
                f"{state.proof_node!r}, atteso {proof_node!r}")
        if step.derivation_before != before.identifier:
            raise ValueError(
                f"esecutore: derivation_before {step.derivation_before} ≠ "
                f"{before.identifier}")
        if step.derivation_after != state.identifier:
            raise ValueError(
                f"esecutore: derivation_after {step.derivation_after} ≠ "
                f"{state.identifier}")
        passi.append(step)
    solution = solve_derivation(state)
    resolved = resolve_request(ir, request, solution)
    return NodalExecution(
        proof_node=proof_node,
        plan=plan,
        steps=tuple(passi),
        derivation=state,
        solution=solution,
        resolved=resolved,
    )


def _execute_transform(
    ir: IR,
    plan: DidacticPlan,
    proof_node: str,
) -> TransformExecution | Refusal:
    if plan.schema_version == PLAN_SCHEMA_VERSION and len(plan.actions) != 1:
        raise ValueError(
            "transform-path v0.2 requires exactly one action; "
            "multi-step execution requires explicit request lineage")
    action = plan.actions[0]
    outcome = transform(ir, action.kind, *action.operands)
    if isinstance(outcome, Refusal):
        return outcome
    after, result = outcome
    return TransformExecution(
        proof_node=proof_node,
        plan=plan,
        before=ir,
        after=after,
        results=(result,),
    )
