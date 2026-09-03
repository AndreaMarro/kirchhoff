"""P1-K: contratti del gate e coerenza del certificato."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

import kirchhoff.domain.truthfulness as truthfulness
from kirchhoff.domain.didactic import NodalExecution, TransformExecution, execute_plan, pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Magnitude, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import Claim, CertifiedNodalExecution, certify_execution, execute_certified_plan, truthfulness_gate
from kirchhoff.pipeline.netlist import leggi

from test_didactic_execute_nodal import _semplice
from test_didactic_execute_transform import PARTITORE

F = Fraction
PROOF = conia("ir", 22, bytes(range(10)))


def _nodal(quantity: str = "current"):
    ir, old = _semplice()
    request = Request("q-contract", quantity, "R1")
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


def _fresh_text(value: str) -> str:
    """Ricostruisce un testo uguale senza riusare l'oggetto chiamante."""
    replica = "".join((value[: len(value) // 2], value[len(value) // 2 :]))
    assert replica == value
    assert replica is not value
    return replica


@pytest.mark.parametrize(
    "caller",
    (
        lambda request: Request(request.id, "voltage", request.target),
        lambda request: Request(request.id, request.quantity, "I1"),
    ),
)
def test_same_id_different_request_is_identity_violation(caller):
    ir, _request, execution = _nodal()
    refused = truthfulness_gate(ir, caller(_request), execution)
    assert isinstance(refused, Refusal)
    assert refused.cause == "identity_violation"


@pytest.mark.parametrize("extra_id", ("a", "z"))
def test_context_non_confonde_l_uguaglianza_request_con_un_confronto_lessicografico(extra_id):
    ir, request, execution = _nodal()
    extra = Request(extra_id, request.quantity, request.target)
    claim = truthfulness_gate(replace(ir, requests=(request, extra)), request, execution)
    assert isinstance(claim, Claim)


def test_context_accetta_binding_uguale_ma_non_identico():
    ir, request, execution = _nodal()
    from_ir = Request(_fresh_text(request.id), request.quantity, request.target)
    caller = Request(_fresh_text(request.id), request.quantity, request.target)
    assert from_ir == caller
    assert from_ir is not caller
    assert from_ir.id is not caller.id
    claim = truthfulness_gate(replace(ir, requests=(from_ir,)), caller, execution)
    assert isinstance(claim, Claim)


@pytest.mark.parametrize("target", ("A", "Z"))
def test_context_rifiuta_target_didattico_diverso_su_entrambi_i_lati_lessicografici(target):
    ir, request, execution = _nodal()
    changed = replace(execution, resolved=replace(execution.resolved, target=target))
    refused = truthfulness_gate(ir, request, changed)
    assert isinstance(refused, Refusal)
    assert refused.cause == "identity_violation"


@pytest.mark.parametrize("foreign_id", ("a", "z"))
def test_nodal_execution_blocca_request_risolta_diversa_dal_piano(foreign_id):
    _ir, _request, execution = _nodal()
    with pytest.raises(ValueError, match="resolved.request_id"):
        replace(execution, resolved=replace(execution.resolved, request_id=foreign_id))


@pytest.mark.parametrize("foreign_id", ("a", "z"))
def test_context_rifiuta_piano_di_una_request_esterna_con_diagnosi_propria(foreign_id):
    ir, request, execution = _nodal()
    changed = replace(
        execution,
        plan=replace(execution.plan, request_id=foreign_id),
        resolved=replace(execution.resolved, request_id=foreign_id),
    )
    refused = truthfulness_gate(ir, request, changed)
    assert isinstance(refused, Refusal)
    assert refused.cause == "identity_violation"
    assert "execution.plan.request_id" in refused.diagnosis


@pytest.mark.parametrize(
    "alter",
    [
        lambda c: replace(c, subject_ids=("wrong", "R1")),
        lambda c: replace(c, subject_ids=("q-contract", "I1")),
        lambda c: replace(c, evidence_ids=c.evidence_ids[:-1]),
        lambda c: replace(c, evidence_ids=(*c.evidence_ids, "DX")),
        lambda c: replace(c, evidence_ids=tuple(reversed(c.evidence_ids))),
        lambda c: replace(c, evidence_ids=("fabricated",)),
        lambda c: replace(c, verifier_id="another.valid.authority"),
        lambda c: replace(c, verifier_version="9.9.9"),
        lambda c: replace(c, state_id=conia("ir", 23, bytes(range(10)))),
    ],
)
def test_certified_execution_rejects_every_incoherent_public_claim(alter):
    _ir, _request, execution, claim = _claim_and_execution()
    altered = alter(claim)
    with pytest.raises(ValueError):
        CertifiedNodalExecution(execution, altered)


@pytest.mark.parametrize(
    "field",
    ("claim_type", "state_id", "verifier_id", "verifier_version"),
)
def test_certified_execution_accetta_valori_autorevoli_uguali_ma_non_identici(field):
    _ir, _request, execution, claim = _claim_and_execution()
    expected = getattr(claim, field)
    altered = replace(claim, **{field: _fresh_text(expected)})
    assert getattr(altered, field) == expected
    assert getattr(altered, field) is not expected
    assert CertifiedNodalExecution(execution, altered).claim == altered


@pytest.mark.parametrize("version", ("0.0.0", "9.9.9"))
def test_certified_execution_rifiuta_versioni_semver_esterne_su_entrambi_i_lati_lessicografici(version):
    _ir, _request, execution, claim = _claim_and_execution()
    altered = replace(claim, verifier_version=version)
    with pytest.raises(ValueError, match="verifier_version"):
        CertifiedNodalExecution(execution, altered)


@pytest.mark.parametrize("verifier_id", ("a", "z"))
def test_certified_execution_rifiuta_verifier_id_esterni_su_entrambi_i_lati_lessicografici(verifier_id):
    _ir, _request, execution, claim = _claim_and_execution()
    altered = replace(claim, verifier_id=verifier_id)
    with pytest.raises(ValueError, match="verifier_id"):
        CertifiedNodalExecution(execution, altered)


@pytest.mark.parametrize("instant", (21, 23))
def test_certified_execution_rifiuta_stati_ir_esteri_su_entrambi_i_lati_lessicografici(instant):
    _ir, _request, execution, claim = _claim_and_execution()
    altered = replace(claim, state_id=conia("ir", instant, bytes(range(10))))
    with pytest.raises(ValueError, match="stato diverso"):
        CertifiedNodalExecution(execution, altered)


def test_context_accetta_target_uguale_ma_non_identico():
    ir, request, execution = _nodal()
    changed = replace(
        execution,
        resolved=replace(execution.resolved, target=_fresh_text(request.target)),
    )
    assert changed.resolved.target is not request.target
    assert isinstance(truthfulness_gate(ir, request, changed), Claim)


@pytest.mark.parametrize(
    ("request_quantity", "resolved_quantity", "unit"),
    (("current", "voltage", "volt"), ("voltage", "current", "ampere")),
)
def test_context_rifiuta_quantita_risolta_esterna_su_entrambi_i_lati_lessicografici(
    request_quantity, resolved_quantity, unit,
):
    ir, request, execution = _nodal(request_quantity)
    changed = replace(
        execution,
        resolved=replace(
            execution.resolved,
            quantity=resolved_quantity,
            value=Magnitude(execution.resolved.value.amount, unit),
        ),
    )
    refused = truthfulness_gate(ir, request, changed)
    assert isinstance(refused, Refusal)
    assert refused.cause == "identity_violation"


def test_context_accetta_quantita_uguale_ma_non_identica():
    ir, request, execution = _nodal()
    changed = replace(
        execution,
        resolved=replace(execution.resolved, quantity=_fresh_text(request.quantity)),
    )
    assert changed.resolved.quantity is not request.quantity
    assert isinstance(truthfulness_gate(ir, request, changed), Claim)


def test_claim_status_is_not_public_input():
    _ir, _request, _execution, claim = _claim_and_execution()
    with pytest.raises(TypeError, match="status"):
        Claim(claim.claim_type, claim.state_id, claim.subject_ids, claim.evidence_ids, claim.verifier_id, claim.verifier_version, status="VERIFIED")
    with pytest.raises(ValueError, match="init=False"):
        replace(claim, status="FAILED")


def test_certify_propagates_gate_refusal_and_execute_propagates_executor_refusal():
    request = Request("q-transform", "current", "R2")
    ir = replace(leggi(PARTITORE), requests=(request,))
    plan = pianifica(ir, request)
    execution = execute_plan(ir, request, plan, proof_node=PROOF)
    assert isinstance(execution, TransformExecution)
    assert certify_execution(ir, request, execution) == truthfulness_gate(ir, request, execution)


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
