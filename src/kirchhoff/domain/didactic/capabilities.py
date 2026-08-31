"""Capacità realmente eseguibili sul circuito corrente.

Quattro concetti distinti, e il planner interroga l'ultimo:

- nome nel catalogo
- tecnica permessa dal profilo (`SUPPORTED`)
- implementazione esistente (`engine.implemented`)
- azione applicabile *a questo* circuito

`partitore_di_tensione` è nel catalogo e in `SUPPORTED` ma non ha corpo: qui
non compare mai fra le riduzioni eseguibili.

Le guardie di serie/parallelo non vivono qui: la sola fonte è
`transform.applicability.enumerate_executable_transforms`.
"""

from __future__ import annotations

from ..ir import IR, REFERENCE_NODE
from ..transform.applicability import (
    ExecutableTransform,
    enumerate_executable_transforms,
)
from .analytical import _generatori_verso_riferimento, nodi_kcl_ordinarie

#: Sottoinsieme per cui lo slice didattico sa davvero scrivere equazioni.
#: I generatori di corrente indipendenti entrano nel termine noto della
#: KCL ordinaria. Le sorgenti controllate e i supernodi restano fuori.
DIDACTIC_NODAL_COMPONENT_TYPES: frozenset[str] = frozenset({
    "resistor",
    "voltage_source_dc",
    "current_source_dc",
})

QUANTITA_NODALI: frozenset[str] = frozenset({"voltage", "current"})

RiduzioneEseguibile = ExecutableTransform


def riduzioni_eseguibili(ir: IR) -> tuple[RiduzioneEseguibile, ...]:
    """Le riduzioni con corpo *e* precondizioni soddisfatte su questo IR."""
    return enumerate_executable_transforms(ir)


def contribuisce(riduzione: RiduzioneEseguibile, target: str, quantity: str) -> bool:
    """La riduzione aiuta a raggiungere la grandezza richiesta.

    Il target sopravvive, oppure la grandezza è condivisa dalla coppia fusa:
    la corrente in serie, la tensione in parallelo.
    """
    fusi = {riduzione.first, riduzione.second}
    if target not in fusi:
        return True
    if riduzione.operation == "serie" and quantity == "current":
        return True
    if riduzione.operation == "parallelo" and quantity == "voltage":
        return True
    return False


def riduzioni_che_contribuiscono(
    ir: IR, target: str, quantity: str,
) -> tuple[RiduzioneEseguibile, ...]:
    return tuple(
        r for r in riduzioni_eseguibili(ir)
        if contribuisce(r, target, quantity)
    )


def _generatori_tensione_verso_riferimento(ir: IR) -> bool:
    for c in ir.components:
        if c.type != "voltage_source_dc":
            continue
        if REFERENCE_NODE not in c.terminals:
            return False
    return True


def _nodi_incogniti(ir: IR) -> tuple[str, ...]:
    """Nodi che `define_nodal_unknowns` dichiarerebbe `unknown`.

    Non è una seconda discovery delle KCL: è il complemento di
    riferimento e generatori verso massa, in ordine canonico.
    """
    fissi = _generatori_verso_riferimento(ir)
    return tuple(sorted(
        n for n in ir.nodes
        if n != REFERENCE_NODE and n not in fissi
    ))


def nodale_disponibile(ir: IR, quantity: str) -> bool:
    """Vero solo se plan → azioni analitiche → equazioni esatte è eseguibile.

    Nello slice attuale «eseguibile» significa: ogni tensione nodale
    `unknown` ha esattamente una KCL ordinaria formulabile. Una sola
    KCL su un sottoinsieme delle incognite non basta.
    """
    if ir.domain != "dc":
        return False
    if quantity not in QUANTITA_NODALI:
        return False
    if not ir.components:
        return False
    if not all(c.type in DIDACTIC_NODAL_COMPONENT_TYPES for c in ir.components):
        return False
    if not _generatori_tensione_verso_riferimento(ir):
        return False
    incogniti = _nodi_incogniti(ir)
    return bool(incogniti) and incogniti == nodi_kcl_ordinarie(ir)
