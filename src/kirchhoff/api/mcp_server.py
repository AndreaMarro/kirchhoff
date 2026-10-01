"""MCP stdio: stesso ingresso canonico usato dal banco studente.

Installazione opzionale: ``uv sync --extra mcp``. Avvio:
``uv run --extra mcp python -m kirchhoff.api.mcp_server``.
Il tool resta utilizzabile da client MCP senza UI; l'estensione Apps aggiunge
una risorsa interattiva ai soli host che la supportano.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from mcp.server import MCPServer
from mcp.server.apps import Apps

from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.student_trace import diagnose_payload
from kirchhoff.pipeline.spice import import_spice, export_spice, SCHEMA as SPICE_SCHEMA
from kirchhoff.pipeline.circuitikz import export_circuitikz, SCHEMA as CIRCUITIKZ_SCHEMA


APP_URI = "ui://kirchhoff/circuit-lesson.html"
ROOT = Path(__file__).resolve().parents[3]


def app_html() -> str:
    template = (ROOT / "web/mcp-app-template.html").read_text(encoding="utf-8")
    bundle = ROOT / "web/dist/mcp/kirchhoff-mcp-app.iife.js"
    if not bundle.is_file():
        script = "document.getElementById('status').textContent='MCP App non compilata: esegui npm run build in web/.';"
    else:
        script = re.sub(r"</script", r"<\\/script", bundle.read_text(encoding="utf-8"), flags=re.IGNORECASE)
    return template.replace("/* KIRCHHOFF_MCP_APP_BUNDLE */", script)


def build_server() -> MCPServer:
    apps = Apps()
    apps.add_html_resource(APP_URI, app_html(), title="CircuitCheck · lezione interattiva",
                           description="Circuito, passaggi, equazioni e risultato verificato")
    server = MCPServer("kirchhoff-circuitcheck", version="0.1.0", extensions=[apps])

    @server.tool(name="solve_circuit", meta={"ui": {"resourceUri": APP_URI}},
                 description="Risolve un circuito DC resistivo confermato e restituisce una derivazione verificata. Non interpreta fotografie.",
                 structured_output=True)
    def solve_circuit(netlist: str, method: str = "auto") -> dict[str, Any]:
        return create_lesson(netlist, method)

    @server.tool(name="diagnose_steps", description="Trova il primo errore dimostrabile in riduzioni semantiche dello studente; altri metodi restano non valutabili.", structured_output=True)
    def diagnose_steps(netlist: str, trace: dict[str, Any]) -> dict[str, Any]:
        return diagnose_payload(netlist, trace)

    @server.tool(name="circuit_capabilities", description="Dichiara il perimetro realmente esposto dagli strumenti MCP.", structured_output=True)
    def circuit_capabilities() -> dict[str, Any]:
        return dict(schema="kirchhoff-capabilities.v1", solve="DC resistivo, R/V/I indipendenti e casi VCVS/VCCS del kernel",
                    diagnosis="riduzioni di due resistori in serie o parallelo",
                    spice=SPICE_SCHEMA, circuitikz=CIRCUITIKZ_SCHEMA,
                    photo=False, ac=False, transients=False, product_verified=False)

    @server.tool(name="import_spice_dc", description="Importa solo il sottoinsieme SPICE DC dichiarato, preservando i valori esatti e rifiutando direttive ignote.", structured_output=True)
    def import_spice_dc(spice: str) -> dict[str, Any]:
        return dict(schema=SPICE_SCHEMA, netlist=import_spice(spice))

    @server.tool(name="export_spice_dc", description="Esporta il circuito confermato nel sottoinsieme SPICE DC; frazioni periodiche vengono rifiutate.", structured_output=True)
    def export_spice_dc(netlist: str) -> dict[str, Any]:
        return dict(schema=SPICE_SCHEMA, spice=export_spice(netlist))

    @server.tool(name="export_circuitikz", description="Esporta la revisione DC come documento CircuitikZ deterministico con nodi a etichetta.", structured_output=True)
    def export_circuitikz_tool(netlist: str) -> dict[str, Any]:
        return dict(schema=CIRCUITIKZ_SCHEMA, tex=export_circuitikz(netlist))

    return server


if __name__ == "__main__":
    build_server().run("stdio")
