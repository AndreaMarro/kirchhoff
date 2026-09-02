"""Schemdraw reference artifacts for visual inspection, intentionally lab-only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

from lab.fixtures.cases import LabCase


@dataclass(frozen=True, slots=True)
class RenderedReference:
    case_id: str
    path: Path
    component_count: int
    renderer: str = "schemdraw-0.23-linear-reference"


def _element(component_type: str):
    if component_type == "resistor":
        return elm.Resistor().right()
    if component_type == "voltage_source_dc":
        return elm.SourceV().right()
    if component_type == "current_source_dc":
        return elm.SourceI().right()
    raise ValueError(f"{component_type}: tipo non renderizzabile nel subset P1-M0")


def render_reference_cases(
    cases: tuple[LabCase, ...] | list[LabCase], output_directory: Path,
) -> tuple[RenderedReference, ...]:
    """Produce una strip SVG per caso, non una sostituzione di layout Kirchhoff.

    Schemdraw riceve volutamente un inventario lineare dei componenti: questa
    baseline rende leggibili simboli/etichette, ma non finge di conservare una
    topologia o di misurare incroci del renderer di produzione.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    artifacts: list[RenderedReference] = []
    for case in cases:
        drawing = schemdraw.Drawing(show=False)
        for component in case.ir.components:
            drawing += _element(component.type).label(component.id)
        path = output_directory / f"{case.case_id}.svg"
        drawing.save(path)
        artifacts.append(RenderedReference(case.case_id, path, len(case.ir.components)))
    return tuple(artifacts)
