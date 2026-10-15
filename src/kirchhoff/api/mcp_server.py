"""MCP stdio: stesso ingresso canonico usato dal banco studente.

Installazione opzionale: ``uv sync --extra mcp``. Avvio:
``uv run --extra mcp python -m kirchhoff.api.mcp_server``.
Il tool resta utilizzabile da client MCP senza UI; l'estensione Apps aggiunge
una risorsa interattiva ai soli host che la supportano.
"""
from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.server.apps import Apps

from kirchhoff.api.app_resource import load_app_html
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.capabilities import product_capabilities, SOLVE_DESCRIPTION
from kirchhoff.pipeline.student_trace import diagnose_payload
from kirchhoff.pipeline.spice import import_spice, export_spice, SCHEMA as SPICE_SCHEMA
from kirchhoff.pipeline.circuitikz import export_circuitikz, SCHEMA as CIRCUITIKZ_SCHEMA


APP_URI = "ui://kirchhoff/circuit-lesson.html"
def app_html() -> str:
    return load_app_html()


def build_server() -> MCPServer:
    apps = Apps()
    apps.add_html_resource(APP_URI, app_html(), title="CircuitCheck · lezione interattiva",
                           description="Circuito, passaggi, equazioni e risultato verificato")
    server = MCPServer("kirchhoff-circuitcheck", version="0.1.0", extensions=[apps])

    @server.tool(name="solve_circuit", meta={"ui": {"resourceUri": APP_URI}},
                 description=SOLVE_DESCRIPTION,
                 structured_output=True)
    def solve_circuit(netlist: str, method: str = "auto") -> dict[str, Any]:
        return create_lesson(netlist, method)

    @server.tool(name="diagnose_steps", description="Trova il primo errore dimostrabile in riduzioni semantiche dello studente; altri metodi restano non valutabili.", structured_output=True)
    def diagnose_steps(netlist: str, trace: dict[str, Any]) -> dict[str, Any]:
        return diagnose_payload(netlist, trace)

    @server.tool(name="circuit_capabilities", description="Dichiara il perimetro realmente esposto dagli strumenti MCP.", structured_output=True)
    def circuit_capabilities(netlist: str | None = None) -> dict[str, Any]:
        return product_capabilities(netlist)

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
