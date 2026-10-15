"""Contratto MCP reale; con ``uv run --extra mcp -m pytest``."""
import asyncio
from hashlib import sha256
import sys

import pytest

mcp = pytest.importorskip("mcp")
from mcp import Client, StdioServerParameters
from kirchhoff.api.mcp_server import APP_URI, build_server
from kirchhoff.pipeline.capabilities import product_capabilities

NETLIST = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"


def test_headless_client_and_app_resource_share_canonical_result():
    async def run():
        async with Client(build_server()) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert {"solve_circuit", "diagnose_steps", "circuit_capabilities", "import_spice_dc", "export_spice_dc", "export_circuitikz"} <= tools.keys()
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
            circuitikz = await client.call_tool("export_circuitikz", {"netlist": NETLIST})
            assert not circuitikz.is_error
            assert "\\begin{circuitikz}" in circuitikz.structured_content["tex"]
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


def test_capabilities_reflect_served_lesson_not_only_kernel():
    async def run():
        async with Client(build_server()) as client:
            base = (await client.call_tool("circuit_capabilities")).structured_content
            assert base == product_capabilities()
            assert base["solve"] is True
            assert base["controlled_sources"] is False
            assert base["ac"] is True and base["transients"] is True
            assert base["ac_scope"]["certified_lesson"] is False
            assert base["kernel_controlled_sources"] == ["VCVS", "VCCS"]

            good = (await client.call_tool("circuit_capabilities", {"netlist": NETLIST})).structured_content
            solved = (await client.call_tool("solve_circuit", {"netlist": NETLIST})).structured_content
            assert good["circuit"]["outcome"] == solved["outcome"] == "solved"
            assert good["circuit"]["available_methods"] == solved["available"]

            controlled = (
                "V1 a 0 10 volt\nR0 a 0 10 ohm\n"
                "E1 b 0 a 0 2\nR1 b 0 5 ohm\n? current R1"
            )
            unsupported = (await client.call_tool("circuit_capabilities", {"netlist": controlled})).structured_content
            actual = (await client.call_tool("solve_circuit", {"netlist": controlled})).structured_content
            assert unsupported["circuit"]["outcome"] == actual["outcome"] == "refusal"
            assert unsupported["circuit"]["available_methods"] == []
    asyncio.run(run())


def test_real_stdio_laplace_lesson_matches_canonical_service():
    from kirchhoff.pipeline.lesson import create_lesson
    text = "@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 1/3 farad\n@initial C1 voltage 4 volt\n? voltage C1"
    expected = create_lesson(text, 'laplace')
    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "kirchhoff.api.mcp_server"])
        async with Client(params) as client:
            result = await client.call_tool("solve_circuit", {"netlist":text,"method":"laplace"})
            assert not result.is_error
            assert result.structured_content == expected
            capability = (await client.call_tool("circuit_capabilities", {"netlist":text})).structured_content
            assert capability["circuit"]["available_methods"] == ["auto","laplace"]
            assert capability["laplace_scope"]["inverse_transform"] is False
            assert expected["verification"]["product_verified"] is False
    asyncio.run(run())
