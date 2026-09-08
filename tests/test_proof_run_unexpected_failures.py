"""Regressioni H2.75: eccezioni inattese restano Failure tipizzati."""

from datetime import datetime, timezone

import pytest

from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.proof_run import run_proof_session

D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

SHA_FIXTURE = "0123456789abcdef0123456789abcdef01234567"


class OrologioFermo:
    def now(self) -> datetime:
        return datetime(2026, 9, 8, 8, 0, 0, tzinfo=timezone.utc)


def _entropy_source():
    values = [bytes((i + 1,)) * 10 for i in range(20)]

    def next_entropy() -> bytes:
        if not values:
            raise StopIteration("entropia esaurita")
        return values.pop(0)

    return next_entropy


def _run_d1():
    ir = leggi(D1)
    request = next(iter(ir.requests))
    return run_proof_session(
        ir,
        request,
        clock=OrologioFermo(),
        entropy=_entropy_source(),
        document_profile="student-pdf.v0.1",
        source_sha=SHA_FIXTURE,
        detail="regressione P2 H2.75",
    )


@pytest.mark.parametrize(
    "exc",
    [KeyError("stato fantasma"), AssertionError("invariante rotta")],
)
def test_unexpected_orchestrator_exception_is_staged_failure(monkeypatch, exc):
    """KeyError/AssertionError non possono attraversare il confine applicativo."""
    import kirchhoff.pipeline.proof_run as boundary

    def broken_orchestrator(*args, **kwargs):
        raise exc

    monkeypatch.setattr(boundary, "orchestrate_didactic_run", broken_orchestrator)
    outcome = _run_d1()

    assert type(outcome) is Failure
    assert outcome.dove == "orchestrate"
    assert not isinstance(outcome, Refusal)


def test_invalid_orchestrator_return_is_staged_failure(monkeypatch):
    """Un ritorno invalido del collaboratore non deve attivare un assert leak."""
    import kirchhoff.pipeline.proof_run as boundary

    monkeypatch.setattr(boundary, "orchestrate_didactic_run", lambda *a, **k: None)
    outcome = _run_d1()

    assert type(outcome) is Failure
    assert outcome.dove == "orchestrate"
    assert "NoneType" in outcome.messaggio
    assert not isinstance(outcome, Refusal)
