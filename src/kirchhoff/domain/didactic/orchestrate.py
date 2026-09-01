"""Orchestrazione didattica deterministica sopra planner ed esecutore.

Ogni ``DidacticPlan`` resta un piano mono-tecnica: questo modulo concatena solo
esecuzioni certificate, ripianificando sullo stato risultante. Non sceglie fra
strategie, non chiama CAS e non costruisce Claim: l'unico Claim finale resta quello
emesso da ``truthfulness.certify_execution``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..identity import verifica
from ..ir import IR, Request
from ..refusal import Refusal
from ..truthfulness import CertifiedNodalExecution, certify_execution
from .execute import NodalExecution, TransformExecution, execute_plan
from .observation import (
    ObservationContract,
    observation_effect,
    validate_observation_lineage,
)
from .plan import DidacticPlan
from .planner import pianifica


@dataclass(frozen=True, slots=True)
class CertifiedDidacticRun:
    """Traccia immutabile dei passi e del solo Claim finale P1-K.

    ``final_ir`` e' lo stato operativo sul quale e' stata eseguita l'analisi
    nodale. Dopo un retarget incorpora la ``final_request`` certificata da P1-J:
    il ``TransformExecution.after`` rimane invece il prodotto letterale della
    trasformazione, senza una rimappatura nascosta dentro ``execute.py``.
    """

    initial_ir: IR
    original_request: Request
    transform_executions: tuple[TransformExecution, ...]
    final_ir: IR
    final_request: Request
    final_execution: CertifiedNodalExecution

    def __post_init__(self) -> None:
        if not isinstance(self.initial_ir, IR):
            raise TypeError("initial_ir deve essere un IR")
        if not isinstance(self.original_request, Request):
            raise TypeError("original_request deve essere una Request")
        if not isinstance(self.final_ir, IR):
            raise TypeError("final_ir deve essere un IR")
        if not isinstance(self.final_request, Request):
            raise TypeError("final_request deve essere una Request")
        if not isinstance(self.final_execution, CertifiedNodalExecution):
            raise TypeError("final_execution deve essere CertifiedNodalExecution")

        executions = tuple(self.transform_executions)
        object.__setattr__(self, "transform_executions", executions)
        current_ir = self.initial_ir
        current_request = self.original_request
        _assert_request_bound(current_ir, current_request)
        for index, execution in enumerate(executions):
            if not isinstance(execution, TransformExecution):
                raise TypeError(
                    f"trasformazione {index}: {type(execution).__name__} invece di TransformExecution")
            _require_canonical_plan(
                current_ir, current_request, execution.plan, phase=f"trasformazione {index}")
            _validate_transform_continuity(execution, current_ir, current_request, index)
            successor = execution.successor_request
            assert successor is not None  # garantito da _validate_transform_continuity
            current_ir = _bind_successor_request(execution.after, successor)
            current_request = successor

        if self.final_ir != current_ir:
            raise ValueError("final_ir non coincide con l'ultimo stato operativo")
        if self.final_request != current_request:
            raise ValueError("final_request non coincide con la lineage delle trasformazioni")
        _assert_request_bound(self.final_ir, self.final_request)

        execution = self.final_execution.execution
        if not isinstance(execution, NodalExecution):
            raise ValueError("certificazione finale senza NodalExecution")
        resolved = execution.resolved
        if execution.plan.request_id != self.final_request.id:
            raise ValueError("il piano nodale finale non appartiene alla final_request")
        if resolved.request_id != self.final_request.id:
            raise ValueError("la quantita' risolta non appartiene alla final_request")
        if resolved.target != self.final_request.target:
            raise ValueError("il Claim P1-K finale non riguarda final_request.target")
        if resolved.quantity != self.final_request.quantity:
            raise ValueError("il Claim P1-K finale non riguarda final_request.quantity")
        _require_canonical_plan(
            self.final_ir, self.final_request, execution.plan, phase="stato nodale finale")
        state_ids = tuple(step.proof_node for step in executions) + (execution.proof_node,)
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("la run riusa un state-id fra stati circuitali distinti")

        replayed_execution = execute_plan(
            self.final_ir, self.final_request, execution.plan, proof_node=execution.proof_node)
        if not isinstance(replayed_execution, NodalExecution):
            raise ValueError("certificazione finale: esecuzione nodale non riproducibile")
        if replayed_execution != execution:
            raise ValueError("certificazione finale: esecuzione nodale non corrisponde al suo IR")
        recertified = certify_execution(self.final_ir, self.final_request, execution)
        if isinstance(recertified, Refusal):
            raise ValueError("certificazione finale rifiutata sul suo IR")
        if recertified != self.final_execution:
            raise ValueError("certificazione finale non corrisponde al suo IR")

    @property
    def state_ids(self) -> tuple[str, ...]:
        """Identificatori effettivamente consumati dalla trace, nell'ordine."""
        return tuple(step.proof_node for step in self.transform_executions) + (
            self.final_execution.execution.proof_node,
        )


def orchestrate_didactic_run(
    initial_ir: IR,
    original_request: Request,
    *,
    state_ids: tuple[str, ...],
) -> CertifiedDidacticRun | Refusal:
    """Esegue il loop P1-L con una supply esplicita di identificatori ``ir_``.

    La supply e' un input del chiamante: il dominio non conia identificatori, non
    introduce un registro oggetto↔identificatore e non riusa un proof-node per
    due stati distinti. La supply puo' essere sovradimensionata: gli identificatori
    non consumati non entrano nella trace risultante.
    """
    if not isinstance(initial_ir, IR):
        raise TypeError(f"initial_ir {type(initial_ir).__name__} invece di IR")
    if not isinstance(original_request, Request):
        raise TypeError(
            f"original_request {type(original_request).__name__} invece di Request")
    identifiers = _validate_state_ids(state_ids)
    _assert_request_bound(initial_ir, original_request)

    current_ir = initial_ir
    current_request = original_request
    transform_executions: list[TransformExecution] = []
    state_index = 0

    while True:
        plan = pianifica(current_ir, current_request)
        if isinstance(plan, Refusal):
            return plan
        if state_index >= len(identifiers):
            raise ValueError("state_ids insufficienti per lo stato da eseguire")
        proof_node = identifiers[state_index]

        if plan.technique == "certified_transform_path":
            outcome = execute_plan(
                current_ir, current_request, plan, proof_node=proof_node)
            if isinstance(outcome, Refusal):
                return outcome
            if not isinstance(outcome, TransformExecution):
                raise RuntimeError("piano trasformativo eseguito senza TransformExecution")
            _validate_transform_continuity(
                outcome, current_ir, current_request, len(transform_executions))
            successor = outcome.successor_request
            assert successor is not None  # garantito da _validate_transform_continuity

            transform_executions.append(outcome)
            current_ir = _bind_successor_request(outcome.after, successor)
            current_request = successor
            state_index += 1
            continue

        if plan.technique == "nodal_analysis":
            outcome = execute_plan(
                current_ir, current_request, plan, proof_node=proof_node)
            if isinstance(outcome, Refusal):
                return outcome
            if not isinstance(outcome, NodalExecution):
                raise RuntimeError("piano nodale eseguito senza NodalExecution")
            certified = certify_execution(current_ir, current_request, outcome)
            if isinstance(certified, Refusal):
                return certified
            state_index += 1
            return CertifiedDidacticRun(
                initial_ir,
                original_request,
                tuple(transform_executions),
                current_ir,
                current_request,
                certified,
            )

        raise RuntimeError(f"tecnica pianificata impossibile: {plan.technique!r}")


def _validate_state_ids(state_ids: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(state_ids, tuple):
        raise TypeError("state_ids deve essere una tuple di identificatori ir_")
    if not state_ids:
        raise ValueError("state_ids non puo' essere vuota")
    identifiers = tuple(verifica(identifier, "ir") for identifier in state_ids)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("state_ids non puo' riusare un identificatore fra stati distinti")
    return identifiers


def _assert_request_bound(ir: IR, request: Request) -> None:
    matches = tuple(candidate for candidate in ir.requests if candidate.id == request.id)
    if len(matches) != 1:
        raise ValueError(
            f"request {request.id!r} deve comparire esattamente una volta nello stato IR")
    if matches[0] != request:
        raise ValueError("Request non coerente con lo stato IR")


def _bind_successor_request(after: IR, successor: Request) -> IR:
    """Rende esplicito lo stato operativo dopo una lineage P1-J.

    Una trasformazione conserva il proprio ``after`` letterale e non riscrive le
    Request. Se P1-J ha retargettato la domanda, l'orchestratore lega il successore
    certificato all'IR immutabile prima di ripianificare/eseguire il piano seguente.
    """
    matches = tuple(request for request in after.requests if request.id == successor.id)
    if len(matches) == 1 and matches[0] == successor:
        return after
    if matches:
        raise ValueError("IR dopo trasformazione con Request omonima incoerente")
    return replace(after, requests=(*after.requests, successor))


def _validate_transform_continuity(
    execution: TransformExecution,
    current_ir: IR,
    current_request: Request,
    index: int,
) -> None:
    if not isinstance(execution, TransformExecution):
        raise TypeError(
            f"trasformazione {index}: {type(execution).__name__} invece di TransformExecution")
    if execution.before != current_ir:
        raise ValueError(f"trasformazione {index}: before non coincide con lo stato corrente")
    if not isinstance(execution.plan, DidacticPlan):
        raise TypeError(f"trasformazione {index}: piano non DidacticPlan")
    if len(execution.plan.actions) != 1:
        raise ValueError(f"trasformazione {index}: piano senza un solo passo")
    if not isinstance(execution.results, tuple) or len(execution.results) != 1:
        raise ValueError(f"trasformazione {index}: risultato trasformativo non singolo")
    if execution.observation.request_id != current_request.id:
        raise ValueError(f"trasformazione {index}: observation.request_id corrotto")
    if execution.observation.target != current_request.target:
        raise ValueError(f"trasformazione {index}: observation.target discontinuo")
    if execution.observation.quantity != current_request.quantity:
        raise ValueError(f"trasformazione {index}: observation.quantity corrotta")
    lineage = execution.request_lineage
    if lineage.request_id != current_request.id:
        raise ValueError(f"trasformazione {index}: lineage.request_id corrotto")
    if lineage.quantity != current_request.quantity:
        raise ValueError(f"trasformazione {index}: lineage.quantity corrotta")
    if lineage.target_before != current_request.target:
        raise ValueError(f"trasformazione {index}: lineage.target_before discontinuo")
    if len(execution.after.components) >= len(execution.before.components):
        raise ValueError(
            f"trasformazione {index}: non riduce il numero di componenti "
            f"({len(execution.before.components)} -> {len(execution.after.components)})")
    action = execution.plan.actions[0]
    expected_effect = observation_effect(
        current_ir,
        execution.after,
        execution.results[0],
        action.kind,
        ObservationContract.from_request(current_request),
    )
    if execution.observation_effect != expected_effect:
        raise ValueError(f"trasformazione {index}: effetto osservativo non autorevole")
    if expected_effect.kind == "blocked":
        raise RuntimeError(
            "violazione interna: trasformazione selezionata con osservazione blocked")

    successor = execution.successor_request
    if successor is None:
        raise RuntimeError("trasformazione non blocked senza Request successiva")
    if successor.id != current_request.id:
        raise ValueError(f"trasformazione {index}: successor_request.id corrotto")
    if successor.quantity != current_request.quantity:
        raise ValueError(f"trasformazione {index}: successor_request.quantity corrotta")
    if successor.target != lineage.target_after:
        raise ValueError(f"trasformazione {index}: successor_request.target discontinuo")
    if execution.observation_effect.kind == "identity" and successor != current_request:
        raise ValueError(f"trasformazione {index}: identity ha cambiato Request")
    validate_observation_lineage(
        current_ir,
        execution.after,
        execution.results[0],
        action.kind,
        current_request,
        successor,
        lineage,
    )

    replayed = execute_plan(
        current_ir, current_request, execution.plan, proof_node=execution.proof_node)
    if not isinstance(replayed, TransformExecution):
        raise ValueError(f"trasformazione {index}: risultato non riproducibile")
    if replayed != execution:
        raise ValueError(
            f"trasformazione {index}: risultato certificato non corrisponde agli stati")


def _require_canonical_plan(
    ir: IR,
    request: Request,
    supplied: DidacticPlan,
    *,
    phase: str,
) -> None:
    """Rigioca il planner: una CertifiedDidacticRun e' la trace canonica P1-L."""
    if not isinstance(supplied, DidacticPlan):
        raise TypeError(f"{phase}: piano {type(supplied).__name__} invece di DidacticPlan")
    expected = pianifica(ir, request)
    if isinstance(expected, Refusal):
        raise ValueError(f"{phase}: il planner ha rifiutato lo stato della trace")
    if not isinstance(expected, DidacticPlan):
        raise RuntimeError(f"{phase}: il planner ha prodotto un esito sconosciuto")
    if supplied != expected:
        raise ValueError(f"{phase}: piano pianificato diverso dalla trace certificata")


__all__ = ["CertifiedDidacticRun", "orchestrate_didactic_run"]
