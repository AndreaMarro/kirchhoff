from pathlib import Path
from fractions import Fraction
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, urlopen
import importlib.util
import json
import re
import shutil
import subprocess

import pytest

from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.spice import export_spice, import_spice

DIVIDER = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"


def test_dc_export_import_preserves_exact_components_topology_and_question():
    exported = export_spice(DIVIDER)
    assert "R2 a 0 220" in exported and "V1 b 0 DC 12" in exported
    restored = leggi(import_spice(exported))
    original = leggi(DIVIDER)
    assert {(c.id, c.type, c.terminals, c.value.amount) for c in restored.components} == {
        (c.id, c.type, c.terminals, c.value.amount) for c in original.components}
    assert [(r.quantity, r.target) for r in restored.requests] == [("voltage", "R2")]


def test_controlled_sources_and_prefix_case_are_explicit():
    source = "Title\nV1 A 0 dc 1k\nR1 A B 2M\nE1 B 0 A 0 2.5\nG1 B 0 A 0 1MEG\n* KIRCHHOFF_REQUEST current R1\n.op\n.end\n"
    ir = leggi(import_spice(source))
    values = {c.id: c.value.amount for c in ir.components}
    assert (values["V1"], values["R1"], values["E1"], values["G1"]) == (1000, Fraction(1, 500), Fraction(5, 2), 1_000_000)
    assert ir.component("E1").control_nodes == ("a", "0")
    assert "* KIRCHHOFF_REQUEST current R1" in export_spice(ir)


@pytest.mark.parametrize("source,reason", [
    ("Title\nR1 a 0 1k\n.tran 1m 1s\n.end", "direttiva"),
    ("Title\nF1 a 0 V1 2\n.end", "non supportato"),
    ("Title\nR1 a 0 {1/3}\n.end", "Valore SPICE"),
    ("Title\nR1 a 0 1k", "senza .end"),
    ("Title\nR1 a 0 1k\n.end\nR2 a 0 2k", "dopo .end"),
    ("Title\nV1 a 0 SIN(0 1 50)\n.end", "arità"),
])
def test_import_rejects_unsupported_dialect_instead_of_discarding(source, reason):
    with pytest.raises(ValueError, match=re.escape(reason)):
        import_spice(source)


def test_export_refuses_nonterminating_exact_fraction_and_case_collisions():
    with pytest.raises(ValueError, match="non esprimibile esattamente"):
        export_spice("V1 a 0 1 volt\nR1 a 0 1/3 ohm\n? current R1")
    with pytest.raises(ValueError, match="maiuscole"):
        export_spice("V1 a 0 1 volt\nR1 a A 1 ohm\nR2 A 0 2 ohm\n? current R1")


def test_http_spice_import_export_round_trip():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_spice_test", path)
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
        spice = post("/api/spice/export", dict(netlist=DIVIDER))
        assert spice["schema"] == "kirchhoff-spice-dc.v1"
        restored = post("/api/spice/import", dict(spice=spice["spice"]))
        assert "? voltage R2" in restored["netlist"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


@pytest.mark.skipif(shutil.which("ngspice") is None, reason="ngspice non installato")
def test_independent_ngspice_operating_point(tmp_path: Path):
    path = tmp_path / "divider.cir"
    path.write_text(export_spice(DIVIDER), encoding="utf-8")
    result = subprocess.run(["ngspice", "-b", str(path)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert re.search(r"^\s*a\s+8\.250000e\+00", result.stdout, re.MULTILINE)
