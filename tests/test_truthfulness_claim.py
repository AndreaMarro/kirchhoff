"""P1-K: contratto del Claim verificato."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kirchhoff.domain.identity import conia
from kirchhoff.domain.truthfulness import Claim

STATE = conia("ir", 7, bytes(range(10)))


def _claim(**changes) -> Claim:
    data = {
        "claim_type": "resolved_quantity",
        "state_id": STATE,
        "subject_ids": ["q1", "R1"],
        "evidence_ids": ["D1", "D2"],
        "verifier_id": "kirchhoff.truthfulness.nodal_dc",
        "verifier_version": "1.0.0",
    }
    data.update(changes)
    return Claim(**data)


def test_claim_valido_normalizza_e_deterministico():
    a = _claim()
    b = _claim(subject_ids=("q1", "R1"), evidence_ids=("D1", "D2"))
    assert a == b
    assert a.subject_ids == ("q1", "R1")
    assert a.evidence_ids == ("D1", "D2")
    assert a.status == "VERIFIED"


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"claim_type": "anything"}, "claim_type"),
        ({"state_id": "ir_falso"}, "identificatore"),
        ({"subject_ids": ()}, "subject_ids"),
        ({"subject_ids": ("q1", "q1")}, "duplicati"),
        ({"subject_ids": "q1"}, "sequenza"),
        ({"subject_ids": ("q1", 3)}, "vuoto o non testuale"),
        ({"evidence_ids": ()}, "evidence_ids"),
        ({"evidence_ids": ("D1", "D1")}, "duplicati"),
        ({"verifier_id": ""}, "verifier_id"),
        ({"verifier_id": object()}, "verifier_id"),
        ({"verifier_version": ""}, "verifier_version"),
        ({"verifier_version": object()}, "verifier_version"),
        ({"verifier_version": "1.0"}, "verifier_version"),
        ({"status": "failed"}, "status"),
    ],
)
def test_claim_rifiuta_invarianti(changes, match):
    with pytest.raises((TypeError, ValueError), match=match):
        _claim(**changes)


def test_claim_immutabile():
    claim = _claim()
    with pytest.raises(FrozenInstanceError):
        claim.status = "VERIFIED"
