"""Quindici mappature nominate, ispezionabili prima del corpus bulk."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

import pytest

pytest.importorskip("lcapy", reason="oracolo esterno disponibile solo nell'extra research")

from kirchhoff.domain.ir import Request
from kirchhoff.pipeline.netlist import leggi
from lab.oracles.lcapy_adapter import lcapy_value
from lab.oracles.ngspice_adapter import ngspice_value


FIXTURES = Path(__file__).resolve().parent.parent / "lab" / "fixtures" / "adapter-mapping.json"


def test_quindici_fixture_rendono_esplicite_polarita_e_mappatura():
    records = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(records) == 15
    assert {record["id"] for record in records} == {
        "voltage-positive", "voltage-reversed", "current-positive", "current-reversed",
        "passive-current", "passive-voltage", "ground-lower", "ground-upper",
        "floating-source", "simple-supernode", "zero-current", "rational-resistance",
        "high-low-ratio", "parallel-path", "multiple-sources",
    }
    for record in records:
        request = Request(record["id"], record["quantity"], record["target"])
        ir = replace(leggi(record["netlist"]), requests=(request,))
        expected = Fraction(record["expected"])
        assert lcapy_value(ir, request) == expected, record["id"]
        observed = ngspice_value(ir, request)
        assert abs(float(expected) - observed) <= 1e-10 + 1e-8 * max(
            abs(float(expected)), abs(observed)), record["id"]
