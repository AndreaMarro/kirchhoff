"""Il punto in cui le parti del prodotto si incontrano.

La radice applicativa canonica e' `run_proof_session`
(`kirchhoff.pipeline.proof_run`). `resolve` e' la compatibilita' storica:
delega ogni domanda alla radice e ne proietta le chiusure in `Solved`.
`risolvi` e' lo stesso oggetto sotto il nome storico.
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
