"""Modello stateful vero per il loop P1-L, senza sostituirne l'oracolo."""

from __future__ import annotations

from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, precondition, rule

from kirchhoff.domain.didactic.execute import NodalExecution, TransformExecution, execute_plan
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    _bind_successor_request,
    orchestrate_didactic_run,
)
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import certify_execution
from lab.fixtures.cases import case_for_seed
from tests.strategies import deterministic_state_ids


class DidacticReplayMachine(RuleBasedStateMachine):
    """Interpreta plan/execute/rebind/certify come stati distinti e verificabili."""

    @initialize(seed=st.integers(min_value=0, max_value=199))
    def start(self, seed: int) -> None:
        self.case = case_for_seed(seed)
        self.ids = deterministic_state_ids(seed, 12)
        self.current_ir = self.case.ir
        self.current_request = self.case.request
        self.executions: list[TransformExecution] = []
        self.finished = False

    @precondition(lambda self: not self.finished)
    @rule()
    def plan_is_canonical(self) -> None:
        assert pianifica(self.current_ir, self.current_request) == pianifica(
            self.current_ir, self.current_request)

    @precondition(lambda self: not self.finished and getattr(
        pianifica(self.current_ir, self.current_request), "technique", None
    ) == "certified_transform_path")
    @rule()
    def execute_selected_transform(self) -> None:
        plan = pianifica(self.current_ir, self.current_request)
        outcome = execute_plan(
            self.current_ir, self.current_request, plan,
            proof_node=self.ids[len(self.executions)],
        )
        assert isinstance(outcome, TransformExecution)
        assert len(outcome.after.components) < len(outcome.before.components)
        assert outcome.successor_request is not None
        self.executions.append(outcome)
        self.current_ir = _bind_successor_request(outcome.after, outcome.successor_request)
        self.current_request = outcome.successor_request

    @precondition(lambda self: not self.finished and getattr(
        pianifica(self.current_ir, self.current_request), "technique", None
    ) == "nodal_analysis")
    @rule()
    def execute_terminal_nodal_and_certify(self) -> None:
        plan = pianifica(self.current_ir, self.current_request)
        outcome = execute_plan(
            self.current_ir, self.current_request, plan,
            proof_node=self.ids[len(self.executions)],
        )
        assert isinstance(outcome, NodalExecution)
        certified = certify_execution(self.current_ir, self.current_request, outcome)
        assert not isinstance(certified, Refusal)
        assembled = CertifiedDidacticRun(
            self.case.ir, self.case.request, tuple(self.executions),
            self.current_ir, self.current_request, certified,
        )
        replay = orchestrate_didactic_run(
            self.case.ir, self.case.request, state_ids=self.ids)
        assert assembled == replay
        self.finished = True

    @precondition(lambda self: self.finished)
    @rule()
    def terminal_evidence_is_stable(self) -> None:
        """Il terminale resta osservabile senza introdurre nuove transizioni."""
        assert pianifica(self.current_ir, self.current_request).technique == "nodal_analysis"

    @invariant()
    def request_e_stato_restano_continui(self) -> None:
        assert self.current_request.id == self.case.request.id
        assert self.current_request.quantity == self.case.request.quantity
        assert self.current_request in self.current_ir.requests
        assert len({execution.proof_node for execution in self.executions}) == len(self.executions)


TestDidacticReplayMachine = DidacticReplayMachine.TestCase
TestDidacticReplayMachine.settings = settings(
    max_examples=40, stateful_step_count=12, deadline=None, derandomize=True,
)
