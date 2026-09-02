"""P1-M0 e' osservazionale rispetto alla fixture P1-L gia' certificata."""

from __future__ import annotations

from dataclasses import replace

from kirchhoff.domain.didactic.candidates import enumerate_strategy_candidates
from kirchhoff.domain.didactic.features import extract_circuit_features
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun, orchestrate_didactic_run
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.pipeline.netlist import leggi


SERIE_P1L = """V1 c 0 12 volt
R1 c a 100 ohm
R2 a b 220 ohm
R3 b 0 330 ohm
I1 0 b 1 ampere
"""


def _state_ids() -> tuple[str, ...]:
    return tuple(conia("ir", 4_000 + index, bytes([index]) * 10) for index in range(3))


def test_features_e_candidati_non_alterano_plan_o_run_p1l():
    request = Request("q1", "current", "R1")
    ir = replace(leggi(SERIE_P1L), requests=(request,))
    expected_plan = pianifica(ir, request)
    expected_run = orchestrate_didactic_run(ir, request, state_ids=_state_ids())

    extract_circuit_features(ir, request)
    enumerate_strategy_candidates(ir, request)

    assert pianifica(ir, request) == expected_plan
    observed_run = orchestrate_didactic_run(ir, request, state_ids=_state_ids())
    assert isinstance(expected_run, CertifiedDidacticRun)
    assert observed_run == expected_run
