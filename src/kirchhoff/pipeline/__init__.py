"""Il punto in cui le parti del prodotto si incontrano.

L'ingresso è `resolve`. `risolvi` è lo stesso oggetto sotto il nome storico.
"""
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.resolve import Solved, resolve
from kirchhoff.pipeline.risolvi import (
    PASSO, Risolto, layout_a_maglia, risolvi,
)

__all__ = [
    "PASSO", "Failure", "Refusal", "Risolto", "Solved",
    "layout_a_maglia", "resolve", "risolvi",
]
