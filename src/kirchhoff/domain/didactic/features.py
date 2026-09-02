"""Descrittori topologici puri per ricerca: fatti, mai una politica di scelta."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ..ir import IR, REFERENCE_NODE, Request
from .analytical import nodi_kcl_ordinarie, supernodi_semplici
from .capabilities import riduzioni_che_contribuiscono, riduzioni_eseguibili
from .observation import ObservationContract


@dataclass(frozen=True, slots=True)
class CircuitFeatures:
    """Fatti deterministici su un IR e la sua Request, senza ranking implicito."""

    component_count: int
    resistor_count: int
    source_count: int
    node_count: int
    connected_regions: int
    cycle_rank: int
    nodal_unknown_count: int
    ordinary_kcl_count: int
    simple_supernode_count: int
    executable_reduction_count: int
    admissible_reduction_count: int


def _connected_regions(ir: IR) -> int:
    adjacency = {node_id: set() for node_id in ir.nodes}
    for component in ir.components:
        p, q = component.terminals
        adjacency[p].add(q)
        adjacency[q].add(p)
    unseen = set(adjacency)
    regions = 0
    while unseen:
        regions += 1
        pending = deque((unseen.pop(),))
        while pending:
            node_id = pending.popleft()
            for neighbour in adjacency[node_id] & unseen:
                unseen.remove(neighbour)
                pending.append(neighbour)
    return regions


def _nodal_unknown_count(ir: IR) -> int:
    fixed: set[str] = set()
    for component in ir.components:
        if component.type != "voltage_source_dc":
            continue
        p, q = component.terminals
        if p == REFERENCE_NODE:
            fixed.add(q)
        elif q == REFERENCE_NODE:
            fixed.add(p)
    return sum(node_id != REFERENCE_NODE and node_id not in fixed for node_id in ir.nodes)


def extract_circuit_features(ir: IR, request: Request) -> CircuitFeatures:
    """Estrae definizioni Kirchhoff-native; nessuna dipendenza da `lab/`."""
    if not isinstance(ir, IR):
        raise TypeError(f"ir {type(ir).__name__} invece di IR")
    if not isinstance(request, Request):
        raise TypeError(f"request {type(request).__name__} invece di Request")
    regions = _connected_regions(ir)
    executable = riduzioni_eseguibili(ir)
    admissible = riduzioni_che_contribuiscono(
        ir, ObservationContract.from_request(request))
    return CircuitFeatures(
        component_count=len(ir.components),
        resistor_count=sum(component.type == "resistor" for component in ir.components),
        source_count=sum(component.type != "resistor" for component in ir.components),
        node_count=len(ir.nodes),
        connected_regions=regions,
        cycle_rank=len(ir.components) - len(ir.nodes) + regions,
        nodal_unknown_count=_nodal_unknown_count(ir),
        ordinary_kcl_count=len(nodi_kcl_ordinarie(ir)),
        simple_supernode_count=len(supernodi_semplici(ir)),
        executable_reduction_count=len(executable),
        admissible_reduction_count=len(admissible),
    )
