"""Il riconoscitore non può far passare una trascrizione tagliata per completa."""

import importlib.util
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from kirchhoff.pipeline.vision_response import VISION_SCHEMA, parse_vision_response


NETLIST = "V1 a 0 12 volt\nR1 a 0 6 ohm\n? current R1"
REGION = {"x1": 100, "y1": 200, "x2": 400, "y2": 350}


def response(netlist=NETLIST, *, complete=True, uncertainties=None, observations=None, status="completed"):
    lines = netlist.splitlines()
    payload = {
        "netlist": netlist,
        "complete": complete,
        "uncertainties": [] if uncertainties is None else uncertainties,
        "observations": ([{"line": line, "region": REGION} for line in lines]
                         if observations is None else observations),
    }
    return {"status": status, "output": [{"type": "message", "content": [
        {"type": "output_text", "text": json.dumps(payload)}]}]}


def test_complete_response_retains_line_level_image_regions():
    result = parse_vision_response(response())
    assert result["netlist"] == NETLIST
    assert result["model_reported_complete"] is True
    assert [item["line"] for item in result["observations"]] == NETLIST.splitlines()
    assert result["observations"][0]["region"] == REGION


@pytest.mark.parametrize("change,match", [
    (lambda r: r.update(status="incomplete"), "interrotta"),
    (lambda r: r["output"][0]["content"].append({"type": "refusal", "refusal": "no"}), "rifiutato"),
    (lambda r: r["output"][0]["content"].append({"type": "output_text", "text": "{}"}), "multipla"),
    (lambda r: r["output"][0].update(content=None), "interpretabile"),
    (lambda r: r["output"][0]["content"][0].update(text="non JSON"), "JSON"),
])
def test_incomplete_refused_or_ambiguous_provider_output_is_not_a_circuit(change, match):
    raw = response()
    change(raw)
    with pytest.raises(ValueError, match=match):
        parse_vision_response(raw)


def test_missing_or_invalid_source_region_rejects_even_when_model_claims_complete():
    raw = response(observations=[{"line": NETLIST.splitlines()[0], "region": REGION}])
    with pytest.raises(ValueError, match="riga"):
        parse_vision_response(raw)
    invalid = [{"line": line, "region": {**REGION, "x2": 100}}
               for line in NETLIST.splitlines()]
    with pytest.raises(ValueError, match="regione"):
        parse_vision_response(response(observations=invalid))


def test_oversize_netlist_is_rejected_without_silent_truncation():
    text = "R1 a 0 " + "1" * 16000 + " ohm\n? current R1"
    with pytest.raises(ValueError, match="16000"):
        parse_vision_response(response(text))


def test_partial_reading_must_name_doubts_and_remains_unconfirmed():
    partial = response("R1 a 0 6 ohm", complete=False,
                       uncertainties=["Il generatore in alto è tagliato."])
    result = parse_vision_response(partial)
    assert result["requires_confirmation"] is True
    assert result["model_reported_complete"] is False
    with pytest.raises(ValueError, match="dubbi"):
        parse_vision_response(response("R1 a 0 6 ohm", complete=False))


def test_complete_claim_without_a_question_is_rejected():
    with pytest.raises(ValueError, match="domanda"):
        parse_vision_response(response("R1 a 0 6 ohm"))


def test_http_recognizer_uses_strict_schema_and_does_not_send_invalid_image(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("student_vision_contract", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "3")
    sent = []

    class FakeHTTP:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(response()).encode()

    def fake_urlopen(request, timeout):
        sent.append(json.loads(request.data))
        assert timeout == 60
        return FakeHTTP()

    monkeypatch.setattr(server, "urlopen", fake_urlopen)
    image = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    result = server.recognize(image, "test-key", "configured-model")
    assert result["netlist"] == NETLIST and result["source_sha256"]
    assert len(sent) == 3
    assert all(call["text"]["format"] == VISION_SCHEMA for call in sent)
    assert len({call["input"][0]["content"][0]["text"] for call in sent}) == 3
    assert all(call["input"][0]["content"][1]["image_url"] == image for call in sent)
    assert result["extraction_passes"] == 3
    assert result["model_reported_complete"] is True
    with pytest.raises(ValueError, match="PNG"):
        server.recognize("https://example.org/image", "test-key", "configured-model")
    assert len(sent) == 3


def test_recognizer_disagreement_stays_incomplete_and_keeps_alternatives(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("student_vision_disagreement", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "3")
    readings = [response(), response(NETLIST.replace("12 volt", "13 volt")), response()]

    class FakeHTTP:
        def __init__(self, raw): self.raw = raw
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return json.dumps(self.raw).encode()

    def fake_urlopen(_request, timeout):
        assert timeout == 60
        return FakeHTTP(readings.pop(0))

    monkeypatch.setattr(server, "urlopen", fake_urlopen)
    image = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    result = server.recognize(image, "test-key", "configured-model")
    assert result["model_reported_complete"] is False
    assert len(result["candidates"]) == 2
    assert [candidate["netlist"] for candidate in result["candidates"]] == [NETLIST, NETLIST.replace("12 volt", "13 volt")]
    assert any("diverg" in doubt.lower() for doubt in result["uncertainties"])
    assert result["requires_confirmation"] is True


def test_recognizer_does_not_hide_disagreement_about_source_regions(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("student_vision_region_disagreement", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "3")
    shifted = [{"line": line, "region": {**REGION, "x1": REGION["x1"] + (20 if index == 1 else 0)}}
               for index, line in enumerate(NETLIST.splitlines())]
    readings = [response(), response(observations=shifted), response()]

    class FakeHTTP:
        def __init__(self, raw): self.raw = raw
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return json.dumps(self.raw).encode()

    monkeypatch.setattr(server, "urlopen", lambda _request, timeout: FakeHTTP(readings.pop(0)))
    image = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    result = server.recognize(image, "test-key", "configured-model")
    assert result["model_reported_complete"] is False
    assert [candidate["netlist"] for candidate in result["candidates"]] == [NETLIST, NETLIST]
    assert result["candidates"][0]["observations"] != result["candidates"][1]["observations"]
    assert any("region" in doubt.lower() for doubt in result["uncertainties"])


def test_recognizer_requires_protected_pass_count_before_network(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("student_vision_pass_policy", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    monkeypatch.delenv("KIRCHHOFF_EXTRACTION_PASSES", raising=False)
    monkeypatch.setattr(server, "urlopen", lambda *_args, **_kwargs: pytest.fail("network called"))
    image = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    with pytest.raises(ValueError, match="KIRCHHOFF_EXTRACTION_PASSES"):
        server.recognize(image, "test-key", "configured-model")
    assert server.vision_ready() is False
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "2")
    with pytest.raises(ValueError, match="almeno 3"):
        server.recognize(image, "test-key", "configured-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("KIRCHHOFF_VISION_MODEL", "configured-model")
    assert server.vision_ready() is False
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "3")
    assert server.vision_ready() is True


def test_provider_schema_rejection_is_reported_as_operational_failure(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("student_vision_http_error", path)
    server_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server_module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("KIRCHHOFF_VISION_MODEL", "configured-model")
    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "3")

    def reject(*_args, **_kwargs):
        raise HTTPError("https://api.openai.com/v1/responses", 400, "schema rejected", None, None)

    monkeypatch.setattr(server_module, "urlopen", reject)
    server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    image = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    request = Request(f"http://127.0.0.1:{server.server_port}/api/recognize",
                      data=json.dumps({"image": image}).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 502
        assert "provider ha respinto" in json.load(error.value)["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
