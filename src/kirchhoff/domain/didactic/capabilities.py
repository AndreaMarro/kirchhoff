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
from .analytical import nodo_della_prima_kcl

#: Sottoinsieme per cui lo slice didattico sa davvero scrivere equazioni.
#: MNA risolve anche generatori di corrente e sorgenti controllate; il
#: formulatore KCL di questo slice costruisce soltanto termini resistivi e
#: tensioni fissate da un generatore verso il riferimento.
DIDACTIC_NODAL_COMPONENT_TYPES: frozenset[str] = frozenset({
    "resistor",
    "voltage_source_dc",
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


def nodale_disponibile(ir: IR, quantity: str) -> bool:
    """Vero solo se plan → azioni analitiche → equazioni esatte è eseguibile."""
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
    return nodo_della_prima_kcl(ir) is not None
