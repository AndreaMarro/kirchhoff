"""Esecuzione offline di politiche sperimentali, senza toccare il planner."""

from __future__ import annotations

from dataclasses import dataclass, replace

from kirchhoff.domain.didactic.execute import NodalExecution, TransformExecution, execute_plan
from kirchhoff.domain.didactic.features import extract_circuit_features
from kirchhoff.domain.didactic.orchestrate import _bind_successor_request
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import certify_execution

from .corpus import CorpusRow, ResearchCandidate, _describe_candidates, _state_ids
from .policies import POLICIES


@dataclass(frozen=True, slots=True)
class PolicyRun:
    """Misure di una policy; il Claim resta quello certificato dal core."""

    policy: str
    case_id: str
    transform_count: int
    identity_count: int
    retarget_count: int
    peripheral_count: int
    final_nodal_unknown_count: int
    analytical_action_count: int
    final_claim_status: str


def _peripheral(candidate: ResearchCandidate) -> bool:
    """Definizione prudente: non target e nessuna riduzione di complessita' locale."""
    return (
        not candidate.touches_target
        and candidate.nodal_unknown_delta >= 0
        and candidate.equation_delta >= 0
    )


def simulate_policy(row: CorpusRow, policy_name: str) -> PolicyRun:
    """Esegue una traccia lab; i piani alternativi non diventano P1-L canonici."""
    chooser = POLICIES[policy_name]
    current_ir = row.case.ir
    current_request = row.case.request
    transforms = 0
    identities = 0
    retargets = 0
    peripheral = 0
    for state_index, proof_node in enumerate(_state_ids(row.case.seed)):
        features = extract_circuit_features(current_ir, current_request)
        current_case = replace(row.case, ir=current_ir, request=current_request)
        selected = chooser(_describe_candidates(current_case, features))
        canonical = pianifica(current_ir, current_request)
        if isinstance(canonical, Refusal):
            raise AssertionError(f"politica su stato non pianificabile: {row.case.case_id}")
        if selected.candidate.technique == "certified_transform_path":
            if canonical.technique != "certified_transform_path":
                raise AssertionError("una politica ha inventato una trasformazione non eseguibile")
            experimental_plan = replace(canonical, actions=selected.candidate.actions)
            outcome = execute_plan(
                current_ir, current_request, experimental_plan, proof_node=proof_node)
            if not isinstance(outcome, TransformExecution):
                raise AssertionError("trasformazione sperimentale non eseguita")
            if outcome.successor_request is None:
                raise AssertionError("candidato ammissibile senza successore Request")
            transforms += 1
            identities += outcome.observation_effect.kind == "identity"
            retargets += outcome.observation_effect.kind == "retarget"
            peripheral += _peripheral(selected)
            current_ir = _bind_successor_request(outcome.after, outcome.successor_request)
            current_request = outcome.successor_request
            continue
        if selected.candidate.technique != "nodal_analysis":
            raise AssertionError("tecnica sperimentale sconosciuta")
        if canonical.technique != "nodal_analysis":
            raise AssertionError("una politica ha saltato un percorso attualmente eseguibile")
        outcome = execute_plan(current_ir, current_request, canonical, proof_node=proof_node)
        if not isinstance(outcome, NodalExecution):
            raise AssertionError("piano nodale non eseguito")
        certified = certify_execution(current_ir, current_request, outcome)
        if isinstance(certified, Refusal):
            raise AssertionError("certificazione finale rifiutata")
        final = extract_circuit_features(current_ir, current_request)
        return PolicyRun(
            policy_name, row.case.case_id, transforms, identities, retargets,
            peripheral, final.nodal_unknown_count, len(outcome.steps), certified.claim.status,
        )
    raise AssertionError("supply P1-M0 esaurita: circuito oltre il bound dichiarato")
