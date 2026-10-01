import base64
from hashlib import sha256
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import importlib.util
import json

import pytest

from kirchhoff.pipeline.image_revision import source_receipt, confirm_revision, verify_revision

IMAGE = "data:image/png;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg=="
NETLIST = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"
SECRET = b"test-secret-only-not-a-production-key"


def test_image_confirmation_is_exact_revision_bound_and_expires():
    source = source_receipt(IMAGE, SECRET, now=1000)
    assert source["source_sha256"] == sha256(base64.b64decode(IMAGE.split(",")[1])).hexdigest()
    with pytest.raises(ValueError, match="Confronta la foto"):
        confirm_revision(source["source_token"], NETLIST, False, SECRET, now=1001)
    approval = confirm_revision(source["source_token"], NETLIST, True, SECRET, now=1001)
    provenance = verify_revision(approval["confirmation_token"], NETLIST, SECRET, now=1002)
    assert provenance["source_kind"] == "image"
    assert provenance["circuit_sha256"] == sha256(NETLIST.encode()).hexdigest()
    with pytest.raises(ValueError, match="circuito è cambiato"):
        verify_revision(approval["confirmation_token"], NETLIST.replace("220", "221"), SECRET, now=1002)
    with pytest.raises(ValueError, match="scaduta"):
        verify_revision(approval["confirmation_token"], NETLIST, SECRET, now=5000)
    with pytest.raises(ValueError, match="non valida"):
        verify_revision(approval["confirmation_token"][:-2] + "xx", NETLIST, SECRET, now=1002)


def test_untrusted_images_are_rejected_before_any_provider_call():
    for image in ("data:image/png;base64,@@@@", "data:image/gif;base64,AA==",
                  "data:image/jpeg;base64," + IMAGE.split(",")[1],
                  "data:image/png;base64," + base64.b64encode(base64.b64decode(IMAGE.split(",")[1])[:16] +
                        (100_000).to_bytes(4, "big") + (100_000).to_bytes(4, "big") +
                        base64.b64decode(IMAGE.split(",")[1])[24:]).decode()):
        with pytest.raises(ValueError):
            source_receipt(image, SECRET, now=1000)


def test_live_http_photo_requires_confirmation_of_the_current_netlist():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_photo_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def post(route, payload):
        request = Request(f"http://127.0.0.1:{server.server_port}{route}",
                          data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urlopen(request) as response:
            return json.load(response)
    try:
        with pytest.raises(HTTPError) as error:
            post("/api/solve", dict(netlist=NETLIST, source_kind="image"))
        assert error.value.code == 422
        source = post("/api/source", dict(image=IMAGE))
        approval = post("/api/confirm", dict(source_token=source["source_token"], netlist=NETLIST, confirmed=True))
        result = post("/api/solve", dict(netlist=NETLIST, source_kind="image", confirmation_token=approval["confirmation_token"]))
        assert result["outcome"] == "solved"
        assert result["input_provenance"]["source_sha256"] == source["source_sha256"]
        pdf_request = Request(f"http://127.0.0.1:{server.server_port}/api/pdf",
                              data=json.dumps(dict(netlist=NETLIST, source_kind="image",
                                  confirmation_token=approval["confirmation_token"])).encode(),
                              headers={"Content-Type": "application/json"})
        with urlopen(pdf_request) as response:
            pdf = response.read()
        assert b"Foto SHA256" in pdf and source["source_sha256"].encode() in pdf
        with pytest.raises(HTTPError) as error:
            post("/api/solve", dict(netlist=NETLIST.replace("220", "221"), source_kind="image",
                                    confirmation_token=approval["confirmation_token"]))
        assert error.value.code == 422
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
