"""Contratto MCP reale; con ``uv run --extra mcp -m pytest``."""
import asyncio
from hashlib import sha256
import sys

import pytest

mcp = pytest.importorskip("mcp")
from mcp import Client, StdioServerParameters
from kirchhoff.api.mcp_server import APP_URI, build_server

NETLIST = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"


def test_headless_client_and_app_resource_share_canonical_result():
    async def run():
        async with Client(build_server()) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert {"solve_circuit", "diagnose_steps", "circuit_capabilities", "import_spice_dc", "export_spice_dc"} <= tools.keys()
            assert tools["solve_circuit"].meta["ui"]["resourceUri"] == APP_URI
            result = await client.call_tool("solve_circuit", {"netlist": NETLIST})
            assert not result.is_error
            assert result.structured_content["answer"]["exact"] == "33/4"
            assert result.structured_content["verification"]["product_verified"] is False
            resource = await client.read_resource(APP_URI)
            assert resource.contents[0].mime_type == "text/html;profile=mcp-app"
            assert "Kirchhoff" in resource.contents[0].text
            trace = dict(schema="student-trace.v1", circuit_fingerprint=sha256(NETLIST.encode()).hexdigest(),
                         steps=[dict(transcription="R1+R2=200", operation="serie", first="R1", second="R2",
                                     claimed_value="200", reading="clear")])
            diagnosis = await client.call_tool("diagnose_steps", {"netlist": NETLIST, "trace": trace})
            assert not diagnosis.is_error
            assert diagnosis.structured_content["outcome"] == "first_invalid"
            spice = await client.call_tool("export_spice_dc", {"netlist": NETLIST})
            assert not spice.is_error
            restored = await client.call_tool("import_spice_dc", {"spice": spice.structured_content["spice"]})
            assert not restored.is_error
            assert "? voltage R2" in restored.structured_content["netlist"]
            bad = await client.call_tool("solve_circuit", {"netlist": "R1 a b nope ohm"})
            assert bad.is_error
    asyncio.run(run())


def test_real_stdio_transport_answers_without_ui_host():
    async def run():
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "kirchhoff.api.mcp_server"])
        async with Client(params) as client:
            result = await client.call_tool("circuit_capabilities")
            assert not result.is_error
            assert result.structured_content["photo"] is False
            assert result.structured_content["product_verified"] is False
    asyncio.run(run())
