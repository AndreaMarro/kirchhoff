"""Capacità realmente eseguibili sul circuito corrente.

Quattro concetti distinti, e il planner interroga l'ultimo:

- nome nel catalogo
- tecnica permessa dal profilo (`SUPPORTED`)
- implementazione esistente (`engine.implemented`)
- azione applicabile *a questo* circuito

`partitore_di_tensione` è nel catalogo e in `SUPPORTED` ma non ha corpo: qui
non compare mai fra le riduzioni eseguibili.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..ir import IR, REFERENCE_NODE, Component
from ..transform.engine import implemented

#: I tipi su cui l'analisi nodale DC esatta del core sa formulare un sistema.
NODAL_COMPONENT_TYPES: frozenset[str] = frozenset({
    "resistor",
    "voltage_source_dc",
    "current_source_dc",
    "voltage_controlled_voltage_source",
    "voltage_controlled_current_source",
})

QUANTITA_NODALI: frozenset[str] = frozenset({"voltage", "current"})


@dataclass(frozen=True, slots=True, order=True)
class RiduzioneEseguibile:
    """Una riduzione certificata applicabile a una coppia concreta."""

    operation: str
    first: str
    second: str

    @property
    def operands(self) -> tuple[str, str]:
        return (self.first, self.second)


def _resistori(ir: IR) -> tuple[Component, ...]:
    return tuple(c for c in ir.components if c.type == "resistor")


def _grado(ir: IR, nodo: str) -> tuple[str, ...]:
    return tuple(sorted(c.id for c in ir.components if nodo in c.terminals))


def _serie_applicabile(ir: IR, a: Component, b: Component) -> bool:
    comune = set(a.terminals) & set(b.terminals)
    if len(comune) != 1:
        return False
    nodo = next(iter(comune))
    if nodo == REFERENCE_NODE:
        return False
    return _grado(ir, nodo) == tuple(sorted((a.id, b.id)))


def _parallelo_applicabile(a: Component, b: Component) -> bool:
    return set(a.terminals) == set(b.terminals)


def riduzioni_eseguibili(ir: IR) -> tuple[RiduzioneEseguibile, ...]:
    """Le riduzioni con corpo *e* precondizioni soddisfatte su questo IR.

    L'ordine è canonico: operazione, poi i due identificatori già ordinati.
    Permutare i componenti dell'IR non cambia il risultato.
    """
    corpo = implemented()
    trovate: list[RiduzioneEseguibile] = []
    for a, b in combinations(_resistori(ir), 2):
        primo, secondo = sorted((a.id, b.id))
        ca, cb = ir.component(primo), ir.component(secondo)
        if "serie" in corpo and _serie_applicabile(ir, ca, cb):
            trovate.append(RiduzioneEseguibile("serie", primo, secondo))
        if "parallelo" in corpo and _parallelo_applicabile(ca, cb):
            trovate.append(RiduzioneEseguibile("parallelo", primo, secondo))
    return tuple(sorted(trovate))


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


def nodale_disponibile(ir: IR, quantity: str) -> bool:
    if ir.domain != "dc":
        return False
    if quantity not in QUANTITA_NODALI:
        return False
    if not ir.components:
        return False
    return all(c.type in NODAL_COMPONENT_TYPES for c in ir.components)
