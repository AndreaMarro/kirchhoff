"""Il punto in cui le parti del prodotto si incontrano.

Fino al 26/08/2026 questo pacchetto era vuoto, e la revisione della Story 1.7 lo
aveva misurato: le parti si componevano solo dentro i test.
"""
from kirchhoff.pipeline.risolvi import (
    PASSO, Rifiuto, Risolto, layout_a_maglia, risolvi,
)

__all__ = ["PASSO", "Rifiuto", "Risolto", "layout_a_maglia", "risolvi"]
