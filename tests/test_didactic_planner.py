"""Spine didattico 0.1: planner deterministico e capacita realmente eseguibili.

Il ponte e quello gia certificato da `tests/test_percorso_b.py` (A == B).
Nessun nome di fixture decide la strategia.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

from kirchhoff.domain.didactic import DidacticPlan, pianifica
from kirchhoff.domain.didactic.capabilities import (
    DIDACTIC_NODAL_COMPONENT_TYPES,
    contribuisce,
    nodale_disponibile,
    riduzioni_che_contribuiscono,
    riduzioni_eseguibili,
)
from kirchhoff.domain.ir import IR, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import SUPPORTED, implemented
from kirchhoff.domain.transform.applicability import (
    ExecutableTransform,
    enumerate_executable_transforms,
)
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve

from test_percorso_b import PONTE

GOLDEN_NETLIST = Path(__file__).resolve().parent / "golden" / "ponte_dc.netlist"
