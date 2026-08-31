"""Passi analitici: il circuito resta fermo, lo stato matematico avanza."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from ..ir import IR, REFERENCE_NODE
from ..proof.graph import ProofGraph
from .derivation import (
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    nome_tensione,
    tensione_nodo,
)
from .kinds import ANALYTICAL_KINDS
