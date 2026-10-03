"""Topology-driven layout for the lesson's supported two-terminal components.

Nodes occupy rows; interval colouring lets series edges share a column.  A long
edge never crosses a symbol: its symbol lives in its first row interval and its
remaining lead uses explicit bridges at unrelated horizontal node buses.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from collections import deque

from kirchhoff.domain.transform import EntityRef
from .schema import LayoutIR, Placement

SUPPORTED = frozenset({'resistor', 'capacitor', 'inductor', 'voltage_source_dc',
                       'current_source_dc', 'voltage_source_ac', 'current_source_ac'})


@dataclass(frozen=True)
class ConnectedLayout:
    layout: LayoutIR
    rows: dict[str, int]
    buses: dict[str, tuple[int, int]]
    width: int
    height: int


def connected_layout(ir, label_width: int, *, istante: int, casualita: bytes):
    """No electrical solving and no special circuit recognizers."""
    if not ir.components or any(c.type not in SUPPORTED or len(c.terminals) != 2
                                for c in ir.components):
        raise ValueError('Schema connesso: tipo di componente non ancora supportato')
    adjacency = {n: set() for n in ir.nodes}
    for c in ir.components:
        a, b = c.terminals
        adjacency[a].add(b); adjacency[b].add(a)
    if any(not neighbours for neighbours in adjacency.values()):
        raise ValueError('Schema connesso: nodo senza terminali')
    roots = [c.terminals[0] for c in sorted(ir.components, key=lambda c: c.id)
             if c.type.startswith('voltage_source') and c.terminals[0] != '0']
    order = []
    for seed in roots + sorted(n for n in ir.nodes if n != '0'):
        queue = deque([seed])
        while queue:
            n = queue.popleft()
            if n in order or n == '0':
                continue
            order.append(n)
            queue.extend(sorted(adjacency[n] - {'0'}))
    if '0' in ir.nodes:
        order.append('0')
    rows = {n: 70 + 150 * i for i, n in enumerate(order)}
    columns: list[list[tuple[int, int]]] = []
    component_columns = {}
    intervals = {c.id: tuple(sorted(rows[n] for n in c.terminals)) for c in ir.components}
    # Long edges on the outside, independent of request or teaching focus.
    for c in sorted(ir.components, key=lambda c: (-(intervals[c.id][1]-intervals[c.id][0]), c.id)):
        a, b = intervals[c.id]
        col = next((i for i, occupied in enumerate(columns)
                    if all(b <= lo or a >= hi for lo, hi in occupied)), len(columns))
        if col == len(columns):
            columns.append([])
        columns[col].append((a, b)); component_columns[c.id] = col
    spacing = max(190, label_width + 105, max(map(len, ir.nodes)) * 10 + 60)
    xs = {c.id: 100 + component_columns[c.id] * spacing for c in ir.components}
    buses = {n: (min(xs[c.id] for c in ir.components if n in c.terminals),
                 max(xs[c.id] for c in ir.components if n in c.terminals)) for n in ir.nodes}
    placements = tuple(Placement(EntityRef('component', c.id), F(xs[c.id]), F(intervals[c.id][0] + 75))
                       for c in ir.components) + tuple(
        Placement(EntityRef('node', n), F(buses[n][0]), F(rows[n])) for n in ir.nodes)
    layout = LayoutIR.nuovo(placements, istante=istante, casualita=casualita)
    return ConnectedLayout(layout, rows, buses, max(xs.values()) + label_width + 85,
                           max(rows.values()) + 55)


def lead_path(x, start, end, crossings):
    """A continuous conductor with visible, unconnected crossover bridges."""
    direction = 1 if end > start else -1
    path = f'M{x} {start}'
    for y in sorted((y for y in crossings if min(start, end) < y < max(start, end)),
                    reverse=direction < 0):
        path += (f' L{x} {y-8*direction}'
                 f' C{x+12} {y-8*direction} {x+12} {y+8*direction} {x} {y+8*direction}')
    return path + f' L{x} {end}'


def bus_path(lo, hi, y, crossing_xs):
    """The short gap visibly puts the bus underneath each curved crossover."""
    path = f'M{lo} {y}'
    for x in sorted(crossing_xs):
        path += f' L{x+5} {y} M{x+13} {y}'
    return path + f' L{hi} {y}'
