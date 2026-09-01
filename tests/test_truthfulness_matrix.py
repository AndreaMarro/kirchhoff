"""P1-K: matrice reale nodale attraverso planner, executor e gate."""

from __future__ import annotations

from dataclasses import replace

import pytest

from kirchhoff.domain.didactic import NodalExecution, pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import CertifiedNodalExecution, execute_certified_plan

from test_didactic_execute_nodal import (
    _due_ordinari,
    _due_supernodi,
    _flottante_invertito,
    _noto_e_ordinario,
    _ponte_v1_corrente,
    _semplice,
)

PROOF = conia("ir", 21, bytes(range(10)))


def _certify(factory, target, quantity):
    ir, _old = factory()
    request = Request("q-cert", quantity, target)
    ir = replace(ir, requests=(request,))
    plan = pianifica(ir, request)
    assert not isinstance(plan, Refusal)
    result = execute_certified_plan(ir, request, plan, proof_node=PROOF)
    assert isinstance(result, CertifiedNodalExecution)
    assert isinstance(result.execution, NodalExecution)
    assert result.claim.status == "VERIFIED"
    return result


@pytest.mark.parametrize(
    ("factory", "target", "quantity"),
    [
        (_semplice, "R1", "voltage"),
        (_semplice, "R1", "current"),
        (_semplice, "I1", "voltage"),
        (_semplice, "I1", "current"),
        (_ponte_v1_corrente, "V1", "voltage"),
        (_ponte_v1_corrente, "V1", "current"),
        (_flottante_invertito, "V1", "voltage"),
        (_flottante_invertito, "V1", "current"),
        (_noto_e_ordinario, "R2", "voltage"),
        (_due_ordinari, "R1", "voltage"),
        (_due_supernodi, "R1", "voltage"),
    ],
)
def test_certified_nodal_matrix(factory, target, quantity):
    result = _certify(factory, target, quantity)
    assert result.claim.subject_ids == ("q-cert", target)


def test_reversed_orientation_keeps_signed_value():
    result = _certify(_flottante_invertito, "V1", "voltage")
    assert result.execution.resolved.orientation == ("b", "a")
    assert result.execution.resolved.value.amount > 0
