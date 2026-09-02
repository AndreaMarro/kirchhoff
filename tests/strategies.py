"""Strategie Hypothesis limitate ai circuiti DC che il laboratorio sa spiegare."""

from __future__ import annotations

from hypothesis import strategies as st

from kirchhoff.domain.identity import conia
from lab.fixtures.cases import LabCase, case_for_seed


@st.composite
def bounded_dc_cases(draw) -> LabCase:
    """Un caso valido, riproducibile e senza dipendere dal reference-set."""
    seed = draw(st.integers(min_value=0, max_value=199))
    return case_for_seed(seed)


def deterministic_state_ids(seed: int, count: int) -> tuple[str, ...]:
    """Supply P1-L valida: suffisso aggiuntivo e identita' restano osservabili."""
    if not 0 <= seed <= 199:
        raise ValueError("seed fuori dal corpus bounded")
    if count < 1:
        raise ValueError("serve almeno uno state id")
    return tuple(
        conia("ir", 1_700_000_000_000 + index, bytes([seed, index]) * 5)
        for index in range(count)
    )
