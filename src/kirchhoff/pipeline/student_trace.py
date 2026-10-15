"""Ingresso strutturato condiviso fra HTTP e MCP per StudentTrace."""
from __future__ import annotations

from kirchhoff.domain.student_trace import StudentStep, StudentTrace, diagnose
from kirchhoff.pipeline.netlist import leggi


def diagnose_payload(netlist: str, trace: dict) -> dict:
    if not isinstance(netlist, str) or len(netlist) > 16000:
        raise ValueError("Circuito mancante o troppo lungo: massimo 16000 caratteri.")
    ir = leggi(netlist)
    if len(ir.components) > 32 or len(ir.nodes) > 24:
        raise ValueError("Questo banco accetta al massimo 32 componenti e 24 nodi.")
    if not isinstance(trace, dict) or not isinstance(trace.get("steps"), list) or len(trace["steps"]) > 32:
        raise ValueError("Serve un procedimento strutturato di massimo 32 passaggi.")
    steps = []
    for item in trace["steps"]:
        if not isinstance(item, dict):
            raise ValueError("Passaggio non interpretabile.")
        steps.append(StudentStep(**item))
    semantic = StudentTrace(trace.get("circuit_fingerprint"), tuple(steps), trace.get("schema"))
    return diagnose(ir, semantic, netlist)
