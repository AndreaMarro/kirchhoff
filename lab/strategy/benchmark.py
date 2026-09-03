"""Esecuzione offline di politiche sperimentali, senza toccare il planner."""

from __future__ import annotations

from dataclasses import dataclass, replace

from kirchhoff.domain.didactic.execute import NodalExecution, TransformExecution, execute_plan
from kirchhoff.domain.didactic.features import extract_circuit_features
from kirchhoff.domain.didactic.orchestrate import _bind_successor_request
from kirchhoff.domain.didactic.plan import DidacticPlan
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
    decision_trace: tuple[str, ...]
    directly_nodal: bool
    first_choice: str
    final_nodal_unknown_count: int
    analytical_action_count: int
    final_claim_status: str


def _peripheral(candidate: ResearchCandidate, before) -> bool:
    """Definizione prudente: non target e nessuna riduzione di complessita' locale."""
    return (
        not candidate.touches_target
        and candidate.resulting_nodal_unknown_count is not None
        and candidate.resulting_equation_count is not None
        and candidate.resulting_nodal_unknown_count >= before.nodal_unknown_count
        and candidate.resulting_equation_count >= (
            before.ordinary_kcl_count + 2 * before.simple_supernode_count)
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
    first_choice = ""
    directly_nodal = False
    trace: list[str] = []
    for state_index, proof_node in enumerate(_state_ids(row.case.seed, 64)):
        features = extract_circuit_features(current_ir, current_request)
        if isinstance(features, Refusal):
            raise AssertionError(f"feature fuori scope durante policy: {features}")
        current_case = replace(row.case, ir=current_ir, request=current_request)
        canonical = pianifica(current_ir, current_request)
        if isinstance(canonical, Refusal):
            raise AssertionError(f"politica su stato non pianificabile: {row.case.case_id}")
        selected = chooser(_describe_candidates(current_case, features, canonical))
        if policy_name == "current" and (
            selected.candidate.technique != canonical.technique
            or selected.candidate.actions != canonical.actions
        ):
            raise AssertionError("current non replica pianifica esattamente")
        if not first_choice:
            first_choice = selected.candidate.technique
            directly_nodal = selected.candidate.technique == "nodal_analysis"
        trace.append(": ".join((
            selected.candidate.technique,
            selected.candidate.operation or "nodal",
            ",".join(selected.candidate.operands),
        )))
        if selected.candidate.technique == "certified_transform_path":
            experimental_plan = DidacticPlan(
                canonical.schema_version, canonical.profile, current_request.id,
                "certified_transform_path", canonical.reason, selected.candidate.actions,
            )
            outcome = execute_plan(
                current_ir, current_request, experimental_plan, proof_node=proof_node)
            if not isinstance(outcome, TransformExecution):
                raise AssertionError("trasformazione sperimentale non eseguita")
            if outcome.successor_request is None:
                raise AssertionError("candidato ammissibile senza successore Request")
            transforms += 1
            identities += outcome.observation_effect.kind == "identity"
            retargets += outcome.observation_effect.kind == "retarget"
            peripheral += _peripheral(selected, features)
            current_ir = _bind_successor_request(outcome.after, outcome.successor_request)
            current_request = outcome.successor_request
            continue
        if selected.candidate.technique != "nodal_analysis":
            raise AssertionError("tecnica sperimentale sconosciuta")
        experimental_plan = DidacticPlan(
            canonical.schema_version, canonical.profile, current_request.id,
            "nodal_analysis", canonical.reason, selected.candidate.actions,
        )
        outcome = execute_plan(current_ir, current_request, experimental_plan, proof_node=proof_node)
        if not isinstance(outcome, NodalExecution):
            raise AssertionError("piano nodale non eseguito")
        certified = certify_execution(current_ir, current_request, outcome)
        if isinstance(certified, Refusal):
            raise AssertionError("certificazione finale rifiutata")
        final = extract_circuit_features(current_ir, current_request)
        if isinstance(final, Refusal):
            raise AssertionError(f"feature terminali fuori scope: {final}")
        return PolicyRun(
            policy_name, row.case.case_id, transforms, identities, retargets,
            peripheral, tuple(trace), directly_nodal, first_choice,
            final.nodal_unknown_count, len(outcome.steps), certified.claim.status,
        )
    raise AssertionError("supply P1-M0 esaurita: circuito oltre il bound dichiarato")
