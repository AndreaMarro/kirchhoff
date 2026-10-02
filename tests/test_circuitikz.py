"""Export CircuitikZ: origine canonica, ordine stabile, rifiuto di TeX ostile."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, urlopen
import importlib.util
import json

import pytest

from kirchhoff.pipeline.circuitikz import export_circuitikz


DIVIDER = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"


def test_output_is_deterministic_and_retains_oriented_terminal_topology():
    result = export_circuitikz(DIVIDER)
    assert result == export_circuitikz("R2 a 0 220 ohm\nV1 b 0 12 volt\nR1 b a 100 ohm\n? voltage R2")
    assert r"\documentclass" in result and r"\usepackage[american]{circuitikz}" in result
    assert r"node[left]{$ \texttt{b} $} to[R,l_={$ \texttt{R1}=100\, \Omega $}] (6,0) node[right]{$ \texttt{a} $}" in result
    assert r"node[left]{$ \texttt{a} $} to[R,l_={$ \texttt{R2}=220\, \Omega $}] (6,-2) node[right]{$ \texttt{0} $}" in result
    assert r"node[left]{$ \texttt{b} $} to[V,l_={$ \texttt{V1}=12\, \mathrm{V} $}] (6,-4) node[right]{$ \texttt{0} $}" in result
    assert "sinistra a destra.\\par\n\\begin{circuitikz}" in result


def test_controlled_source_reference_and_fraction_are_visible():
    netlist = "V1 a 0 1 volt\nE1 b 0 a 0 3/2\nG1 b 0 a 0 1/10 siemens\nR1 b 0 4 ohm\n? voltage R1"
    result = export_circuitikz(netlist)
    assert r"to[cV,l_" in result and r"to[cI" in result
    assert r"\frac{3}{2}" in result
    assert r"V(\texttt{a})-V(\texttt{0})" in result


def test_tex_payload_is_refused_not_interpreted():
    with pytest.raises(ValueError, match="non rappresentabile"):
        export_circuitikz("V1 a 0 1 volt\nR\\write18 a 0 3 ohm\n? voltage V1")


def test_http_export_uses_same_function():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_circuitikz_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(f"http://127.0.0.1:{server.server_port}/api/circuitikz/export",
                          data=json.dumps({"netlist": DIVIDER}).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request) as response:
            result = json.load(response)
        assert result["schema"] == "kirchhoff-circuitikz-netlabels.v1"
        assert result["tex"] == export_circuitikz(DIVIDER)
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
