"""Benchmark ristretto: stessa topologia Kirchhoff/LayoutIR e Schemdraw.

Non introduce un autolayout. I sei circuiti sono maglie per cui il prodotto ha
gia' ``layout_a_maglia()``; la reference riceve gli stessi nodi e gli stessi id di
componente, invece di una strip lineare che non sarebbe un confronto topologico.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

import schemdraw
import schemdraw.elements as elm

from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import EntityRef
from kirchhoff.pipeline import layout_a_maglia
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.render.layout import LayoutIR, LayoutStore, PatchStore, Placement
from kirchhoff.render.serialize import render, scena
from kirchhoff.render.step import VisualStep, componi


@dataclass(frozen=True, slots=True)
class RendererCase:
    case_id: str
    ir: IR


@dataclass(frozen=True, slots=True)
class RenderedReference:
    case_id: str
    path: Path
    component_count: int
    renderer: str = "schemdraw-0.23-topology-preserving"


@dataclass(frozen=True, slots=True)
class GeometryMetrics:
    """Misure a geometria dichiarata; ``None`` significa NOT_COMPARABLE."""

    bounding_box: tuple[str, str, str, str]
    aspect_ratio: str
    crossings: int | None
    component_overlap: int | None
    wire_body_intrusion: int | None
    label_collisions: int | None
    bend_count: int | None


@dataclass(frozen=True, slots=True)
class StaticComparison:
    case_id: str
    component_ids: tuple[str, ...]
    kirchhoff_svg: Path
    reference_svg: Path
    kirchhoff: GeometryMetrics
    reference: GeometryMetrics


@dataclass(frozen=True, slots=True)
class VisualComparison:
    pair_id: str
    operation: str
    before_svg: Path
    after_svg: Path
    surviving_component_count: int
    max_surviving_component_displacement: str
    mean_surviving_component_displacement: str


_MESH_NETLISTS: tuple[tuple[str, str], ...] = (
    ("mesh-02", """V1 a 0 12 volt
R1 a 0 100 ohm
"""),
    ("mesh-03", """V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
"""),
    ("mesh-04", """V1 c 0 12 volt
R1 c b 100 ohm
R2 b a 220 ohm
R3 a 0 330 ohm
"""),
    ("mesh-05", """V1 d 0 12 volt
R1 d c 100 ohm
R2 c b 220 ohm
R3 b a 330 ohm
R4 a 0 470 ohm
"""),
    ("mesh-06", """V1 e 0 12 volt
R1 e d 100 ohm
R2 d c 220 ohm
R3 c b 330 ohm
R4 b a 470 ohm
R5 a 0 560 ohm
"""),
    ("mesh-07", """V1 f 0 12 volt
R1 f e 100 ohm
R2 e d 220 ohm
R3 d c 330 ohm
R4 c b 470 ohm
R5 b a 560 ohm
R6 a 0 680 ohm
"""),
)


def comparable_cases() -> tuple[RendererCase, ...]:
    """Sei circuiti per cui Kirchhoff produce un LayoutIR legittimo, senza fallback."""
    return tuple(RendererCase(case_id, leggi(netlist)) for case_id, netlist in _MESH_NETLISTS)


# Layout espliciti soltanto per le tre maglie oltre il quadrilatero: il layout
# produttivo a maglia resta usato dove la sua geometria e' valida; questi fixture
# evitano che un gomito attraversi un nodo intermedio. Non e' un autolayout.
_EXPLICIT_NODE_POSITIONS: dict[str, dict[str, tuple[int, int]]] = {
    "mesh-05": {"0": (0, 100), "d": (70, 0), "c": (200, 50), "b": (200, 150), "a": (70, 200)},
    "mesh-06": {"0": (0, 100), "e": (50, 0), "d": (150, 0), "c": (200, 100), "b": (150, 200), "a": (50, 200)},
    "mesh-07": {"0": (0, 100), "f": (40, 0), "e": (130, 0), "d": (200, 70), "c": (200, 170), "b": (130, 240), "a": (40, 240)},
}


def benchmark_layout(case: RendererCase) -> LayoutIR:
    """LayoutIR produttivo dove possibile, altrimenti fixture dichiarato per caso."""
    if case.case_id not in _EXPLICIT_NODE_POSITIONS:
        return layout_a_maglia(case.ir)
    nodes = _EXPLICIT_NODE_POSITIONS[case.case_id]
    placements = [
        Placement(EntityRef("node", node), Fraction(x), Fraction(y))
        for node, (x, y) in nodes.items()
    ]
    for component in case.ir.components:
        first, second = nodes[component.terminals[0]], nodes[component.terminals[1]]
        placements.append(Placement(
            EntityRef("component", component.id),
            Fraction(first[0] + second[0], 2), Fraction(first[1] + second[1], 2),
        ))
    return LayoutIR.nuovo(
        tuple(placements), istante=1_760_000_100_000 + len(case.ir.components),
        casualita=bytes([len(case.ir.components)]) * 10,
    )


def _point(layout: LayoutIR, entity: EntityRef) -> tuple[float, float]:
    place = layout.posizione(entity)
    # Schemdraw usa coordinate in pollici; il benchmark mantiene la geometria e
    # cambia solo scala e verso Y, che non alterano topologia/crossing/bend.
    return float(place.x / 200), float(-place.y / 200)


def _reference_element(component_type: str):
    if component_type == "resistor":
        return elm.Resistor()
    if component_type == "voltage_source_dc":
        return elm.SourceV()
    raise ValueError(f"{component_type}: simbolo Schemdraw fuori dal benchmark DC")


def render_reference_case(case: RendererCase, layout: LayoutIR, output: Path) -> RenderedReference:
    """Disegna ogni ramo fra i *suoi* nodi, preservando identita' e topologia."""
    drawing = schemdraw.Drawing(show=False)
    for component in case.ir.components:
        start = _point(layout, EntityRef("node", component.terminals[0]))
        end = _point(layout, EntityRef("node", component.terminals[1]))
        drawing += _reference_element(component.type).at(start).to(end).label(component.id)
    for node in case.ir.nodes:
        drawing += elm.Dot().at(_point(layout, EntityRef("node", node))).label(node)
    output.parent.mkdir(parents=True, exist_ok=True)
    drawing.save(output)
    return RenderedReference(case.case_id, output, len(case.ir.components))


def render_reference_cases(
    cases: tuple[RendererCase, ...] | list[RendererCase], output_directory: Path,
) -> tuple[RenderedReference, ...]:
    """Compatibilita' minima per il vecchio chiamante, ora topologia-preserving."""
    return tuple(
        render_reference_case(case, benchmark_layout(case), output_directory / f"{case.case_id}.svg")
        for case in cases
    )


def _bbox(points: tuple[tuple[Fraction, Fraction], ...]) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    return (
        min(point[0] for point in points), min(point[1] for point in points),
        max(point[0] for point in points), max(point[1] for point in points),
    )


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _orientation(a, b, c) -> Fraction:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _proper_cross(a, b, c, d) -> bool:
    """Intersezione interna esatta: i contatti agli estremi non sono crossing."""
    first = _orientation(a, b, c), _orientation(a, b, d)
    second = _orientation(c, d, a), _orientation(c, d, b)
    return first[0] * first[1] < 0 and second[0] * second[1] < 0


def _kirchhoff_metrics(case: RendererCase, layout: LayoutIR) -> GeometryMetrics:
    drawing = scena(case.ir, layout)
    low, high = drawing.estensione()
    width, height = high.x - low.x, high.y - low.y
    segments = tuple(
        (wire.componente, wire.indice, first, second)
        for wire in drawing.fili for first, second in zip(wire.punti, wire.punti[1:])
    )
    crossings = sum(
        _proper_cross(a, b, c, d)
        for index, (component, terminal, a, b) in enumerate(segments)
        for other_component, other_terminal, c, d in segments[index + 1:]
        if (component, terminal) != (other_component, other_terminal)
    )
    boxes = tuple(symbol.riquadro() for symbol in drawing.simboli)
    overlaps = sum(
        max(left_a.x, left_b.x) < min(right_a.x, right_b.x)
        and max(left_a.y, left_b.y) < min(right_a.y, right_b.y)
        for index, (left_a, right_a) in enumerate(boxes)
        for left_b, right_b in boxes[index + 1:]
    )
    intrusions = sum(
        _proper_cross(first, second, box_low, box_high)
        for component, _terminal, first, second in segments
        for symbol, (box_low, box_high) in zip(drawing.simboli, boxes)
        if component != symbol.componente
    )
    return GeometryMetrics(
        (_fmt(low.x), _fmt(low.y), _fmt(high.x), _fmt(high.y)),
        _fmt(width / height) if height else "NOT_COMPARABLE",
        crossings, overlaps, intrusions, None,
        sum(len(wire.punti) - 2 for wire in drawing.fili),
    )


def _reference_metrics(case: RendererCase, layout: LayoutIR) -> GeometryMetrics:
    points = tuple((placement.x, placement.y) for placement in layout.placements)
    low_x, low_y, high_x, high_y = _bbox(points)
    width, height = high_x - low_x, high_y - low_y
    branches = tuple(
        (component.id,
         layout.posizione(EntityRef("node", component.terminals[0])),
         layout.posizione(EntityRef("node", component.terminals[1])))
        for component in case.ir.components
    )
    crossings = sum(
        _proper_cross(a, b, c, d)
        for index, (component, a, b) in enumerate(branches)
        for other_component, c, d in branches[index + 1:]
        if component != other_component
    )
    # Schemdraw non espone una geometria stabile dei simboli/testi nel suo SVG:
    # overlap, intrusion, label e bend restano dichiaratamente non comparabili.
    return GeometryMetrics(
        (_fmt(low_x), _fmt(low_y), _fmt(high_x), _fmt(high_y)),
        _fmt(width / height) if height else "NOT_COMPARABLE",
        crossings, None, None, None, None,
    )


def _visual_pairs() -> tuple[tuple[str, IR, str, tuple[str, ...]], ...]:
    return (
        ("series", leggi("""V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
"""), "serie", ("R1", "R2")),
        ("parallel", leggi("""V1 b 0 12 volt
R1 b 0 100 ohm
R2 b 0 220 ohm
"""), "parallelo", ("R1", "R2")),
        ("chain-first", leggi("""V1 c 0 12 volt
R1 c b 100 ohm
R2 b a 220 ohm
R3 a 0 330 ohm
"""), "serie", ("R1", "R2")),
        ("chain-second-shape", leggi("""V1 c 0 12 volt
R4 c b 100 ohm
R5 b a 220 ohm
R6 a 0 330 ohm
"""), "serie", ("R4", "R5")),
    )


def _visual_comparison(
    pair_id: str, before: IR, operation: str, operands: tuple[str, ...], output: Path, index: int,
) -> VisualComparison:
    if pair_id == "parallel":
        # Fixture esplicito della visual slice: tre rami paralleli non sono una
        # maglia semplice, quindi chiedere a layout_a_maglia sarebbe una violazione
        # del suo contratto, non un benchmark piu' ricco.
        layout = LayoutIR.nuovo((
            Placement(EntityRef("node", "b"), Fraction(0), Fraction(0)),
            Placement(EntityRef("node", "0"), Fraction(0), Fraction(160)),
            Placement(EntityRef("component", "V1"), Fraction(0), Fraction(80)),
            Placement(EntityRef("component", "R1"), Fraction(100), Fraction(80)),
            Placement(EntityRef("component", "R2"), Fraction(200), Fraction(80)),
        ), istante=1_760_000_050_000, casualita=bytes([90]) * 10)
    else:
        layout = layout_a_maglia(before)
    stores, patches = LayoutStore(), PatchStore()
    step = componi(
        before, operation, *operands, layout=layout, layouts=stores, patches=patches,
        istante=1_760_000_000_000 + index, casualita=bytes([index + 1]) * 10,
    )
    if isinstance(step, Refusal):
        raise AssertionError(f"{pair_id}: passo visivo certificato rifiutato: {step}")
    if not isinstance(step, VisualStep):
        raise AssertionError(f"{pair_id}: {type(step).__name__} invece di VisualStep")
    output.mkdir(parents=True, exist_ok=True)
    before_path, after_path = output / f"{pair_id}-before.svg", output / f"{pair_id}-after.svg"
    before_path.write_text(step.fotogrammi[step.prima], encoding="utf-8")
    after_path.write_text(step.fotogrammi[step.dopo], encoding="utf-8")
    after_layout = stores.risolvi(step.dopo)
    preserved = tuple(
        entity for entity in step.risultato.layout_patch.preserve
        if entity.kind == "component"
    )
    displacements = tuple(
        abs(layout.posizione(entity).x - after_layout.posizione(entity).x)
        + abs(layout.posizione(entity).y - after_layout.posizione(entity).y)
        for entity in preserved
    )
    return VisualComparison(
        pair_id, operation, before_path, after_path, len(preserved),
        _fmt(max(displacements, default=Fraction(0))),
        _fmt(sum(displacements, Fraction(0)) / len(displacements)) if displacements else "0",
    )


def run_renderer_benchmark(output_directory: Path) -> dict[str, Any]:
    """Genera SVG e manifest riproducibili; l'archivio e' responsabilita' della CI."""
    static_dir, visual_dir = output_directory / "static", output_directory / "visual-steps"
    static_dir.mkdir(parents=True, exist_ok=True)
    comparisons: list[StaticComparison] = []
    for case in comparable_cases():
        layout = benchmark_layout(case)
        kirchhoff_path = static_dir / f"{case.case_id}-kirchhoff.svg"
        kirchhoff_path.write_text(render(case.ir, layout), encoding="utf-8")
        reference = render_reference_case(case, layout, static_dir / f"{case.case_id}-schemdraw.svg")
        comparisons.append(StaticComparison(
            case.case_id, tuple(component.id for component in case.ir.components),
            kirchhoff_path, reference.path, _kirchhoff_metrics(case, layout),
            _reference_metrics(case, layout),
        ))
    visuals = tuple(
        _visual_comparison(pair_id, circuit, operation, operands, visual_dir, index)
        for index, (pair_id, circuit, operation, operands) in enumerate(_visual_pairs())
    )
    payload = {
        "static": [
            {
                **asdict(item),
                "kirchhoff_svg": str(item.kirchhoff_svg.relative_to(output_directory)),
                "reference_svg": str(item.reference_svg.relative_to(output_directory)),
            }
            for item in comparisons
        ],
        "visual_steps": [
            {
                **asdict(item),
                "before_svg": str(item.before_svg.relative_to(output_directory)),
                "after_svg": str(item.after_svg.relative_to(output_directory)),
            }
            for item in visuals
        ],
        "not_comparable": [
            "Schemdraw component overlap, wire-body intrusion, labels and bends: SVG geometry is not a stable public API.",
            "Label collisions: neither renderer exposes font metrics suitable for an exact cross-renderer measure.",
            "Schemdraw has no Kirchhoff VisualStep/lineage counterpart, therefore step-to-step displacement is Kirchhoff-only.",
        ],
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    (output_directory / "renderer-benchmark-manifest.json").write_text(
        serialized, encoding="utf-8")
    # Il chiamante riceve esattamente il manifest riproducibile, non una quasi
    # equivalente struttura Python con tuple non serializzabili in JSON.
    return json.loads(serialized)
