"""La GraphView di ricerca conserva le identita' elettriche, inclusi i paralleli."""

from __future__ import annotations

import pytest

pytest.importorskip("networkx", reason="GraphView disponibile solo nell'extra research")

from lab.fixtures.cases import case_for_seed, generated_cases
from lab.graph.graph_view import GraphView


def test_incidency_graph_non_collassa_resistori_paralleli():
    case = case_for_seed(1)
    view = GraphView.from_ir(case.ir)

    assert view.component_count == len(case.ir.components) == 5
    assert view.electrical_node_count == len(case.ir.nodes) == 3
    assert view.graph.has_node("component:R1")
    assert view.graph.has_node("component:R2")
    assert view.graph.degree["component:R1"] == 2
    assert view.graph.degree["component:R2"] == 2
    assert view.cycle_rank == 3


def test_graphview_riconcilia_componenti_nodi_e_rango_su_centocasi():
    for case in generated_cases(100):
        view = GraphView.from_ir(case.ir)
        assert view.component_count == len(case.ir.components)
        assert view.electrical_node_count == len(case.ir.nodes)
        assert view.cycle_rank == len(case.ir.components) - len(case.ir.nodes) + view.connected_regions
