"""Vista di incidenza lossless: ogni componente resta un nodo distinto."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from kirchhoff.domain.ir import IR


def _electrical_node(node_id: str) -> str:
    return f"node:{node_id}"


def _component_node(component_id: str) -> str:
    return f"component:{component_id}"


@dataclass(frozen=True, slots=True)
class GraphView:
    """Bipartito IR-node ↔ component-node; non usa componenti come edge."""

    graph: nx.Graph
    electrical_node_count: int
    component_count: int
    connected_regions: int
    cycle_rank: int

    @classmethod
    def from_ir(cls, ir: IR) -> "GraphView":
        graph = nx.Graph()
        for node_id in ir.nodes:
            graph.add_node(_electrical_node(node_id), kind="electrical", source_id=node_id)
        for component in ir.components:
            component_node = _component_node(component.id)
            graph.add_node(
                component_node, kind="component", source_id=component.id,
                component_type=component.type,
            )
            for node_id in component.terminals:
                graph.add_edge(component_node, _electrical_node(node_id))
        connected_regions = nx.number_connected_components(graph) if graph.nodes else 0
        cycle_rank = len(ir.components) - len(ir.nodes) + connected_regions
        return cls(graph, len(ir.nodes), len(ir.components), connected_regions, cycle_rank)

    @property
    def articulation_electrical_nodes(self) -> tuple[str, ...]:
        return tuple(sorted(
            self.graph.nodes[node_id]["source_id"]
            for node_id in nx.articulation_points(self.graph)
            if self.graph.nodes[node_id]["kind"] == "electrical"
        ))

    @property
    def bridge_components(self) -> tuple[str, ...]:
        """Componenti la cui rimozione aumenta le regioni dell'incidenza."""
        before = self.connected_regions
        bridges: list[str] = []
        for node_id, data in self.graph.nodes(data=True):
            if data["kind"] != "component":
                continue
            remaining = self.graph.copy()
            remaining.remove_node(node_id)
            after = nx.number_connected_components(remaining) if remaining.nodes else 0
            if after > before:
                bridges.append(data["source_id"])
        return tuple(sorted(bridges))

    def target_distance(self, target_component_id: str, component_ids: tuple[str, ...]) -> int | None:
        """Numero minimo di salti componente-componente dalla query all'azione."""
        target = _component_node(target_component_id)
        if target not in self.graph:
            return None
        distances: list[int] = []
        for component_id in component_ids:
            candidate = _component_node(component_id)
            if candidate not in self.graph:
                return None
            try:
                path_length = nx.shortest_path_length(self.graph, target, candidate)
            except nx.NetworkXNoPath:
                return None
            distances.append(path_length // 2)
        return min(distances) if distances else None

    def same_biconnected_region(
        self, target_component_id: str, component_ids: tuple[str, ...],
    ) -> bool:
        target = _component_node(target_component_id)
        candidates = {_component_node(component_id) for component_id in component_ids}
        return any(
            target in region and candidates <= region
            for region in nx.biconnected_components(self.graph)
        )
