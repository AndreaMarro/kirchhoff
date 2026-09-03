"""Autorita' unica per gli atti canonici dell'analisi nodale P1-L."""

from __future__ import annotations

from ..ir import IR, REFERENCE_NODE
from .analytical import (
    _generatori_verso_riferimento,
    nodi_kcl_ordinarie,
    supernodi_semplici,
)
from .plan import PlannedAction


def build_nodal_actions(ir: IR) -> tuple[PlannedAction, ...]:
    """Costruisce gli atti nodali canonici senza scegliere quando usarli."""
    azioni = [PlannedAction("choose_reference", ())]
    fissi = _generatori_verso_riferimento(ir)
    if any(n != REFERENCE_NODE and n not in fissi for n in ir.nodes):
        azioni.append(PlannedAction("define_nodal_unknowns", ()))
    for nodo in nodi_kcl_ordinarie(ir):
        azioni.append(PlannedAction("write_kcl", (nodo,)))
    for sn in supernodi_semplici(ir):
        azioni.append(PlannedAction("write_kcl", (sn.source_id, sn.p, sn.q)))
        azioni.append(PlannedAction("write_voltage_constraint", (sn.source_id,)))
    return tuple(azioni)
