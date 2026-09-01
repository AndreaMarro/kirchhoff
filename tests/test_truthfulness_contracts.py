"""P1-K: contratti del gate e coerenza del certificato."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

import kirchhoff.domain.truthfulness as truthfulness
from kirchhoff.domain.didactic import NodalExecution, TransformExecution, execute_plan, pianifica
from kirchhoff.domain.didactic.plan import PlannedAction
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Magnitude, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import Claim, CertifiedNodalExecution, certify_execution, execute_certified_plan, truthfulness_gate
from kirchhoff.pipeline.netlist import leggi

from test_didactic_execute_nodal import _semplice
from test_didactic_execute_transform import PARTITORE

F = Fraction
PROOF = conia("ir", 22, bytes(range(10)))


def _nodal():
    ir, old = _semplice()
    request = Request("q-contract", "current", "R1")
    ir = replace(ir, requests=(request,))
    plan = pianifica(ir, request)
    execution = execute_plan(ir, request, plan, proof_node=PROOF)
    assert isinstance(execution, NodalExecution)
    return ir, request, execution


def _claim_and_execution():
    ir, request, execution = _nodal()
    claim = truthfulness_gate(ir, request, execution)
    assert isinstance(claim, Claim)
    return ir, request, execution, claim


def test_same_id_different_request_is_identity_violation():
    ir, _request, execution = _nodal()
    caller = Request("q-contract", "voltage", "R1")
    refused = truthfulness_gate(ir, caller, execution)
    assert isinstance(refused, Refusal)
    assert refused.cause == "identity_violation"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: object.__setattr__(c, "subject_ids", ("wrong", "R1")),
        lambda c: object.__setattr__(c, "subject_ids", ("q-contract", "I1")),
        lambda c: object.__setattr__(c, "evidence_ids", c.evidence_ids[:-1]),
        lambda c: object.__setattr__(c, "evidence_ids", (*c.evidence_ids, "DX")),
        lambda c: object.__setattr__(c, "evidence_ids", tuple(reversed(c.evidence_ids))),
        lambda c: object.__setattr__(c, "evidence_ids", ("fabricated",)),
        lambda c: object.__setattr__(c, "verifier_id", "other"),
        lambda c: object.__setattr__(c, "verifier_version", "9.9.9"),
        lambda c: object.__setattr__(c, "state_id", conia("ir", 23, bytes(range(10)))),
        lambda c: object.__setattr__(c, "status", "failed"),
    ],
)
def test_certified_execution_rejects_every_incoherent_claim(mutate):
    _ir, _request, execution, claim = _claim_and_execution()
    mutate(claim)
    with pytest.raises(ValueError):
        CertifiedNodalExecution(execution, claim)


def test_claim_status_is_not_public_input():
    _ir, _request, _execution, claim = _claim_and_execution()
    with pytest.raises(TypeError, match="status"):
        Claim(claim.claim_type, claim.state_id, claim.subject_ids, claim.evidence_ids, claim.verifier_id, claim.verifier_version, status="VERIFIED")


def test_certify_propagates_gate_refusal_and_execute_propagates_executor_refusal():
    request = Request("q-transform", "current", "R2")
    ir = replace(leggi(PARTITORE), requests=(request,))
    plan = pianifica(ir, request)
    execution = execute_plan(ir, request, plan, proof_node=PROOF)
    assert isinstance(execution, TransformExecution)
    assert certify_execution(ir, request, execution) == truthfulness_gate(ir, request, execution)
    rejected_plan = replace(plan, actions=(PlannedAction("serie", ("R1", "V1")),))
    result = execute_certified_plan(ir, request, rejected_plan, proof_node=PROOF)
    assert isinstance(result, Refusal)


@pytest.mark.parametrize(
    "solution",
    [
        {},
        {"R1": {}},
        {"R1": {"current": 1}},
    ],
)
def test_oracle_missing_or_non_fraction_fails_closed(solution):
    _ir, request, _execution = _nodal()
    refused = truthfulness._oracle_value(solution, request)
    assert isinstance(refused, Refusal)
    assert refused.cause == "path_disagreement"


def test_resolved_invalid_unit_or_type_is_path_disagreement():
    ir, request, execution = _nodal()
    object.__setattr__(execution.resolved, "value", Magnitude(F(2), "ohm"))
    assert truthfulness_gate(ir, request, execution).cause == "path_disagreement"
    ir, request, execution = _nodal()
    object.__setattr__(execution.resolved, "value", object())
    assert truthfulness_gate(ir, request, execution).cause == "path_disagreement"


def test_gate_propagates_missing_oracle_result(monkeypatch):
    ir, request, execution = _nodal()
    incomplete = {"I1": {"voltage": F(-10), "current": F(2)}}
    monkeypatch.setattr(truthfulness.mna, "solve_dc", lambda _ir: incomplete)
    monkeypatch.setattr(truthfulness, "solve_dc_tableau", lambda _ir: incomplete)
    monkeypatch.setattr(truthfulness, "verify", lambda *_args: None)
    refused = truthfulness_gate(ir, request, execution)
    assert isinstance(refused, Refusal)
    assert refused.cause == "path_disagreement"
