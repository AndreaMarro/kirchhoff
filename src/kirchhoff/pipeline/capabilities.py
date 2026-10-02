"""Capacità del percorso prodotto, distinte da quelle del kernel matematico.

Il risultato per un circuito passa dallo stesso ingresso di ``solve_circuit``:
una sintassi leggibile o un solver capace non implicano una lezione disponibile.
"""

from __future__ import annotations

from typing import Any

from kirchhoff.domain.didactic.capabilities import DIDACTIC_NODAL_COMPONENT_TYPES
from kirchhoff.pipeline.circuitikz import SCHEMA as CIRCUITIKZ_SCHEMA
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.spice import SCHEMA as SPICE_SCHEMA


SOLVE_DESCRIPTION = (
    "Risolve un circuito DC resistivo confermato con R/V/I indipendenti "
    "quando il percorso didattico e' applicabile. Restituisce un rifiuto "
    "negli altri casi; non interpreta fotografie."
)
SCOPE = (
    "Circuiti resistivi in continua con resistori e sorgenti indipendenti di "
    "tensione o corrente, quando esiste un percorso didattico applicabile. "
    "Le sorgenti controllate VCVS/VCCS sono accettate dal kernel, ma non "
    "hanno ancora una lezione. AC e transitori non sono esposti nel prodotto."
)


def product_capabilities(netlist: str | None = None, *, vision: bool = False) -> dict[str, Any]:
    """Contratto comune a HTTP, MCP e testo di ambito della UI.

    La disponibilità per una netlist viene misurata sul percorso servito e
    restituisce soltanto esito e metodi, senza spacciare il parser per un solver.
    """
    result: dict[str, Any] = dict(
        schema="kirchhoff-capabilities.v1",
        solve=True,
        scope=SCOPE,
        component_types=sorted(DIDACTIC_NODAL_COMPONENT_TYPES),
        controlled_sources=False,
        kernel_controlled_sources=["VCVS", "VCCS"],
        diagnosis="riduzioni R, KCL al nodo, KVL su maglia chiusa e valori DC di corrente/tensione sul circuito originale; le semplificazioni incerte non sono giudicate",
        spice=SPICE_SCHEMA,
        circuitikz=CIRCUITIKZ_SCHEMA,
        photo=vision,
        vision=vision,
        ac=False,
        transients=False,
        product_verified=False,
    )
    if netlist is not None:
        try:
            lesson = create_lesson(netlist)
        except ValueError as exc:
            result["circuit"] = dict(outcome="invalid", available_methods=[], message=str(exc))
        else:
            result["circuit"] = dict(
                outcome=lesson["outcome"],
                available_methods=lesson.get("available", []),
                message=lesson.get("message"),
            )
    return result
