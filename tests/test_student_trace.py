from hashlib import sha256
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import importlib.util
import json

import pytest

from kirchhoff.domain.student_trace import StudentStep, StudentTrace, diagnose
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi


SERIES = "V1 a 0 12 volt\nR1 a b 100 ohm\nR2 b 0 200 ohm\n? current R2"
BRANCH = "V1 a 0 12 volt\nR1 a b 100 ohm\nR2 b 0 200 ohm\nR3 b 0 300 ohm\n? current R2"


def trace(text, *steps):
    return StudentTrace(sha256(text.encode()).hexdigest(), steps)


def test_first_invalid_topology_precedes_later_result():
    steps = (StudentStep("R1 e R2 in serie", "serie", "R1", "R2", "300"),
             StudentStep("R2 e R3 in serie", "serie", "R2", "R3", "500"))
    result = diagnose(leggi(BRANCH), trace(BRANCH, *steps), BRANCH)
    assert (result["outcome"], result["step"], result["category"]) == ("first_invalid", 1, "topology")
    assert "grado 3" in result["message"]


def test_valid_series_and_wrong_arithmetic_are_distinct():
    valid = diagnose(leggi(SERIES), trace(SERIES, StudentStep("R1+R2", "serie", "R1", "R2", "300")), SERIES)
    assert valid["outcome"] == "valid_so_far"
    wrong = diagnose(leggi(SERIES), trace(SERIES, StudentStep("R1+R2", "serie", "R1", "R2", "200")), SERIES)
    assert (wrong["outcome"], wrong["category"]) == ("first_invalid", "algebra")


def test_different_method_and_uncertain_reading_are_not_accused():
    for step in (StudentStep("KCL al nodo b", "kcl", "b", "", None),
                 StudentStep("?", "serie", "R1", "R2", None, "ambiguous")):
        result = diagnose(leggi(BRANCH), trace(BRANCH, step), BRANCH)
        assert result["outcome"] == "not_assessable"


def test_trace_is_bound_to_exact_circuit_revision():
    old = trace(SERIES, StudentStep("R1+R2", "serie", "R1", "R2"))
    with pytest.raises(ValueError, match="circuito è cambiato"):
        diagnose(leggi(BRANCH), old, BRANCH)


def test_image_cannot_be_a_semantic_step():
    with pytest.raises((TypeError, ValueError)):
        StudentTrace(sha256(SERIES.encode()).hexdigest(), (b"image/png",))


@pytest.mark.parametrize("step,error", [
    (dict(transcription="?", operation="serie", first="R1", second="R2", reading="maybe"), ValueError),
    (dict(transcription=42, operation="serie", first="R1", second="R2"), TypeError),
    (dict(transcription="R1+R2", operation="serie", first="R1", second="R2", claimed_value=300), TypeError),
    (dict(transcription="x"*501, operation="serie", first="R1", second="R2"), ValueError),
])
def test_untrusted_step_fields_are_rejected(step, error):
    with pytest.raises(error):
        StudentStep(**step)


def test_trace_contract_rejects_bad_version_hash_and_length():
    fingerprint = sha256(SERIES.encode()).hexdigest()
    step = StudentStep("R1+R2", "serie", "R1", "R2")
    for args in ((fingerprint, (step,), "student-trace.v0"),
                 ("short", (step,), "student-trace.v1"),
                 (fingerprint, (), "student-trace.v1"),
                 (fingerprint, (step,)*33, "student-trace.v1")):
        with pytest.raises(ValueError):
            StudentTrace(*args)


def test_unknown_or_nonresistor_is_not_called_an_error():
    for step in (StudentStep("R1 + RX", "serie", "R1", "RX"),
                 StudentStep("R1 + R1", "serie", "R1", "R1"),
                 StudentStep("V1 + R1", "serie", "V1", "R1")):
        assert diagnose(leggi(SERIES), trace(SERIES, step), SERIES)["outcome"] == "not_assessable"


def test_parallel_topology_and_value_are_checked():
    text = "I1 0 a 2 ampere\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2"
    correct = StudentStep("R1||R2", "parallelo", "R1", "R2", "2")
    assert diagnose(leggi(text), trace(text, correct), text)["outcome"] == "valid_so_far"
    unknown_value = StudentStep("R1||R2", "parallelo", "R1", "R2")
    assert diagnose(leggi(text), trace(text, unknown_value), text)["outcome"] == "valid_so_far"
    unreadable_value = StudentStep("R1||R2", "parallelo", "R1", "R2", "due")
    assert diagnose(leggi(text), trace(text, unreadable_value), text)["category"] == "transcription"
    assert diagnose(leggi(SERIES), trace(SERIES, StudentStep("R1||R2", "parallelo", "R1", "R2")), SERIES)["category"] == "topology"


def test_proof_refusal_or_unavailable_transform_is_not_a_student_error(monkeypatch):
    import kirchhoff.domain.student_trace as module
    valid = trace(SERIES, StudentStep("R1+R2", "serie", "R1", "R2"))
    def unavailable(*_args):
        raise NotImplementedError("test-only unavailable")
    monkeypatch.setattr(module, "transform", unavailable)
    assert diagnose(leggi(SERIES), valid, SERIES)["outcome"] == "not_assessable"
    monkeypatch.setattr(module, "transform", lambda *_args: Refusal("topology", "R1", "component", "test-only refusal"))
    assert diagnose(leggi(SERIES), valid, SERIES)["outcome"] == "not_assessable"


def test_live_http_contract_diagnoses_and_rejects_stale_revision():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for fingerprint, status in ((sha256(BRANCH.encode()).hexdigest(), 200),
                                    (sha256(SERIES.encode()).hexdigest(), 422)):
            payload = dict(netlist=BRANCH, trace=dict(schema="student-trace.v1",
                circuit_fingerprint=fingerprint, steps=[dict(transcription="R1+R2",
                    operation="serie", first="R1", second="R2", claimed_value="300", reading="clear")]))
            request = Request(f"http://127.0.0.1:{server.server_port}/api/diagnose",
                              data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            if status == 200:
                with urlopen(request) as response:
                    assert response.status == 200
                    assert json.load(response)["category"] == "topology"
            else:
                with pytest.raises(HTTPError) as error:
                    urlopen(request)
                assert error.value.code == 422
                assert "circuito è cambiato" in error.value.read().decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
