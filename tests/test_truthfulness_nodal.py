from dataclasses import replace
from fractions import Fraction
import pytest
import kirchhoff.domain.truthfulness as gate
from kirchhoff.domain.didactic import NodalExecution, TransformExecution, execute_plan, pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Component, IR, Magnitude, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import CertifiedNodalExecution, certify_execution, execute_certified_plan, truthfulness_gate
from kirchhoff.pipeline.netlist import leggi

F = Fraction
PROOF = conia("ir", 11, bytes(range(10)))

def req(target="R1", quantity="current", rid="q1"):
    return Request(rid, quantity, target)

def fixture(request=None):
    request = request or req()
    ir = IR("1.0.0", "dc", "generated", ("0", "a"), (
        Component.of("I1", "current_source_dc", ("0", "a"), F(2), "I1"),
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
    ), (request,))
    plan = pianifica(ir, request)
    outcome = execute_plan(ir, request, plan, proof_node=PROOF)
    assert isinstance(outcome, NodalExecution)
    return ir, request, outcome

@pytest.mark.parametrize("target,quantity", [("R1","voltage"),("R1","current"),("I1","voltage"),("I1","current")])
def test_happy(target, quantity):
    ir, request, outcome = fixture(req(target, quantity))
    claim = truthfulness_gate(ir, request, outcome)
    assert claim.status == "VERIFIED"
    assert claim.subject_ids == (request.id, request.target)
    assert claim.evidence_ids == tuple(s.derivation_after for s in outcome.steps)
    assert isinstance(certify_execution(ir, request, outcome), CertifiedNodalExecution)
    assert isinstance(execute_certified_plan(ir, request, outcome.plan, proof_node=PROOF), CertifiedNodalExecution)

def test_tampering(monkeypatch):
    ir, request, outcome = fixture()
    assert truthfulness_gate(ir, request, replace(outcome, resolved=replace(outcome.resolved, value=Magnitude(F(3), "ampere")))).cause == "path_disagreement"
    for changed in (replace(outcome, resolved=replace(outcome.resolved,target="I1")), replace(outcome, resolved=replace(outcome.resolved,request_id="bad"))):
        assert truthfulness_gate(ir, request, changed).cause == "identity_violation"
    assert truthfulness_gate(replace(ir, requests=()), request, outcome).cause == "identity_violation"
    assert truthfulness_gate(replace(ir, requests=(request, Request("q1","voltage","I1"))), request, outcome).cause == "identity_violation"
    mna = gate.mna.solve_dc
    monkeypatch.setattr(gate.mna, "solve_dc", lambda c: {**mna(c), "X":{"voltage":F(0),"current":F(0)}})
    assert truthfulness_gate(ir, request, outcome).cause == "path_disagreement"
    monkeypatch.setattr(gate.mna, "solve_dc", mna)
    tableau = gate.solve_dc_tableau
    monkeypatch.setattr(gate, "solve_dc_tableau", lambda c: {k:v for k,v in tableau(c).items() if k != "R1"})
    assert truthfulness_gate(ir, request, outcome).cause == "path_disagreement"
    monkeypatch.setattr(gate, "solve_dc_tableau", tableau)
    residual = Refusal("residual","a","node","bad")
    monkeypatch.setattr(gate, "verify", lambda *_: residual)
    assert truthfulness_gate(ir, request, outcome) is residual

def test_refusal_and_guards():
    ir, request, outcome = fixture()
    object.__setattr__(outcome, "proof_node", "ir_bad")
    assert truthfulness_gate(ir, request, outcome).cause == "identity_violation"
    ir, request, outcome = fixture()
    object.__setattr__(outcome.resolved, "value", Magnitude(F(2),"ohm"))
    assert truthfulness_gate(ir, request, outcome).cause == "path_disagreement"
    with pytest.raises(TypeError): truthfulness_gate(object(), request, outcome)
    with pytest.raises(TypeError): truthfulness_gate(ir, object(), outcome)
    with pytest.raises(TypeError): truthfulness_gate(ir, request, object())

def test_unsupported():
    request = req("R2","current")
    ir = replace(leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n"),requests=(request,))
    transformed = execute_plan(ir,request,pianifica(ir,request),proof_node=PROOF)
    assert isinstance(transformed,TransformExecution)
    assert truthfulness_gate(ir,request,transformed).cause == "claim_unsupported"
    ir,request,outcome = fixture()
    assert truthfulness_gate(replace(ir,domain="dc_resistive"),request,outcome).cause == "claim_unsupported"
    assert truthfulness_gate(ir,Request("q1","time_constant","R1"),outcome).cause == "claim_unsupported"


def test_remaining_gate_paths(monkeypatch):
    from kirchhoff.domain.exact import SingularSystemError
    from kirchhoff.domain.independent_dc import TableauSingularError
    from kirchhoff.domain.truthfulness import Claim
    ir, request, outcome = fixture()
    object.__setattr__(outcome.resolved, "quantity", "voltage")
    assert truthfulness_gate(ir, request, outcome).cause == "identity_violation"
    ir, request, outcome = fixture()
    object.__setattr__(outcome.plan, "request_id", "other")
    assert truthfulness_gate(ir, request, outcome).cause == "identity_violation"
    ir, request, outcome = fixture()
    monkeypatch.setattr(gate.mna, "solve_dc", lambda _ir: (_ for _ in ()).throw(SingularSystemError("x")))
    assert truthfulness_gate(ir, request, outcome).cause == "path_disagreement"
    monkeypatch.undo()
    monkeypatch.setattr(gate, "solve_dc_tableau", lambda _ir: (_ for _ in ()).throw(TableauSingularError("x")))
    assert truthfulness_gate(ir, request, outcome).cause == "path_disagreement"
    assert gate._oracle_value({}, request).cause == "path_disagreement"
    assert gate._oracle_value({"R1": {"current": 2}}, request).cause == "path_disagreement"
    claim = truthfulness_gate(ir, request, outcome)
    assert not isinstance(claim, Refusal)
    with pytest.raises(TypeError): CertifiedNodalExecution(object(), claim)
    with pytest.raises(TypeError): CertifiedNodalExecution(outcome, object())
    object.__setattr__(claim, "claim_type", "other")
    with pytest.raises(ValueError): CertifiedNodalExecution(outcome, claim)
    object.__setattr__(claim, "claim_type", "resolved_quantity")
    object.__setattr__(claim, "state_id", "ir_other")
    with pytest.raises(ValueError): CertifiedNodalExecution(outcome, claim)
