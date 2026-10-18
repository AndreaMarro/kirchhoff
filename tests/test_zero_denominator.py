"""Un ingresso non razionale è errore utente, anche ai confini pubblici."""
import asyncio
from fractions import Fraction
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from kirchhoff.pipeline.capabilities import product_capabilities
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.netlist import NetlistInputError, leggi


@pytest.mark.parametrize("component", [
    "R1 a 0 1/0 ohm", "V1 a 0 1/0 volt", "I1 a 0 1/0 ampere",
    "E1 a 0 c 0 1/0", "G1 a 0 c 0 1/0 siemens",
])
def test_denominatore_nullo_identifica_la_riga_prima_del_solve(component):
    with pytest.raises(NetlistInputError, match="riga 2.*1/0"):
        leggi("# ingresso originale sintetico\n" + component)


@pytest.mark.parametrize("value,expected", [("1/2", Fraction(1, 2)),
    ("2", Fraction(2)), ("-1/2", Fraction(-1, 2)), ("0.125", Fraction(1, 8))])
def test_magnitudini_razionali_conservano_il_valore_esatto(value, expected):
    ir = leggi(f"V1 a 0 {value} volt\nR1 a 0 1 ohm\n? current R1")
    assert ir.components[0].value.amount == expected


BAD = "V1 a 0 1 volt\nR1 a 0 1/0 ohm\n? current R1"


def test_capability_riporta_input_invalido_invece_di_crash():
    result = product_capabilities(BAD)
    assert result["circuit"]["outcome"] == "invalid"
    assert "riga 2" in result["circuit"]["message"]


def test_http_restituisce_422_per_input_invalido():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_zero_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(f"http://127.0.0.1:{server.server_port}/api/solve",
            data=json.dumps(dict(netlist=BAD)).encode(),
            headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 422
        assert "riga 2" in json.load(error.value)["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mcp_rifiuta_input_e_conserva_diagnostica_utente():
    from mcp import Client
    from kirchhoff.api.mcp_server import build_server
    async def run():
        async with Client(build_server()) as client:
            result = await client.call_tool("solve_circuit", {"netlist": BAD})
            assert result.is_error
            assert "riga 2" in str(result.content)
            capability = await client.call_tool("circuit_capabilities", {"netlist": BAD})
            assert not capability.is_error
            assert capability.structured_content["circuit"]["outcome"] == "invalid"
    asyncio.run(run())


def test_mcp_non_scambia_un_guasto_del_solutore_per_input_errato(monkeypatch):
    from mcp import Client
    import kirchhoff.api.mcp_server as server
    def guasto(*args, **kwargs):
        raise ValueError("guasto interno sintetico del solutore")
    monkeypatch.setattr(server, "create_lesson", guasto)
    async def run():
        async with Client(server.build_server()) as client:
            result = await client.call_tool("solve_circuit", {"netlist": BAD})
            assert result.is_error
            assert "guasto interno" not in str(result.content)
    asyncio.run(run())


def test_partitore_caricato_conserva_gold_analitico():
    unloaded = "V1 s 0 12 volt\nR1 s a 2000 ohm\nR2 a 0 1000 ohm\n? voltage R2"
    loaded = unloaded.replace("? voltage R2", "RL a 0 1000 ohm\n? voltage R2")
    assert create_lesson(unloaded)["answer"]["exact"] == "4"
    assert create_lesson(loaded)["answer"]["exact"] == "12/5"
    historic = "V1 s 0 13 volt\nR1 s a 2 ohm\nR2 a 0 7 ohm\n? voltage R2"
    assert create_lesson(historic)["answer"]["exact"] == "91/9"
