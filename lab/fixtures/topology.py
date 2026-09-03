"""Impronte topologiche pure del laboratorio, senza valori dei componenti."""

from __future__ import annotations

from hashlib import sha256

from kirchhoff.domain.ir import IR, REFERENCE_NODE, Request


def _digest(parts: tuple[str, ...]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def topology_fingerprint(ir: IR, request: Request | None = None) -> str:
    """WL deterministico di incidenza: identita'/valori non influenzano il risultato."""
    labels: dict[str, str] = {
        f"node:{node}": "ground" if node == REFERENCE_NODE else "node"
        for node in ir.nodes
    }
    adjacency: dict[str, set[str]] = {name: set() for name in labels}
    for component in ir.components:
        component_name = f"component:{component.id}"
        target = request is not None and component.id == request.target
        labels[component_name] = f"component:{component.type}:{'target' if target else 'other'}"
        adjacency[component_name] = set()
        for node in component.terminals:
            node_name = f"node:{node}"
            adjacency[component_name].add(node_name)
            adjacency[node_name].add(component_name)
    colors = {name: _digest((label,)) for name, label in labels.items()}
    for _ in range(len(labels)):
        refined = {
            name: _digest((labels[name], *sorted(colors[neighbour] for neighbour in adjacency[name])))
            for name in sorted(labels)
        }
        if refined == colors:
            break
        colors = refined
    return _digest(tuple(sorted(colors.values())))
