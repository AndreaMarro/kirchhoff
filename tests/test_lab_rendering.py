"""Il benchmark confronta SVG dalla stessa topologia, senza introdurre autolayout."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("schemdraw", reason="renderer di riferimento disponibile solo nell'extra research")

from lab.rendering.benchmark import comparable_cases, run_renderer_benchmark


def test_renderer_benchmark_ha_sei_topologie_e_quattro_visual_step_certificati(tmp_path):
    result = run_renderer_benchmark(tmp_path)

    assert len(comparable_cases()) >= 6
    assert len(result["static"]) >= 6
    assert len(result["visual_steps"]) >= 4
    assert all(item["kirchhoff_svg"].endswith("-kirchhoff.svg") for item in result["static"])
    assert all(item["reference_svg"].endswith("-schemdraw.svg") for item in result["static"])
    assert all(item["component_ids"] for item in result["static"])
    assert all(item["max_surviving_component_displacement"] == "0" for item in result["visual_steps"])
    assert all((tmp_path / item["before_svg"]).exists() for item in result["visual_steps"])
    manifest = json.loads((tmp_path / "renderer-benchmark-manifest.json").read_text(encoding="utf-8"))
    assert manifest == result
