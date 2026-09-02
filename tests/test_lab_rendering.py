"""Il benchmark renderer genera artefatti ispezionabili senza toccare il renderer core."""

from __future__ import annotations

import pytest

pytest.importorskip("schemdraw", reason="renderer di riferimento disponibile solo nell'extra research")

from lab.rendering.benchmark import render_reference_cases
from lab.strategy.corpus import deliberate_probes


def test_schemdraw_produce_dodici_svg_ispezionabili(tmp_path):
    rendered = render_reference_cases(deliberate_probes()[:12], tmp_path)

    assert len(rendered) == 12
    assert all(item.path.exists() for item in rendered)
    assert all(item.path.read_text(encoding="utf-8").lstrip().startswith("<?xml") for item in rendered)
    assert all(item.component_count > 0 for item in rendered)
