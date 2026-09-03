"""Attacchi generativi ai contratti P1-J/P1-L, sempre riproducibili."""

from __future__ import annotations

from hypothesis import given, settings

from kirchhoff.domain.didactic.capabilities import (
    effetto_osservazione,
    nodale_disponibile,
    riduzioni_eseguibili,
)
from kirchhoff.domain.didactic.candidates import enumerate_strategy_candidates
from kirchhoff.domain.didactic.observation import (
    ObservationContract,
    apply_observation_effect,
    validate_observation_lineage,
)
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform.engine import transform
from tests.strategies import bounded_dc_cases, deterministic_state_ids


@settings(max_examples=100, deadline=None, derandomize=True)
@given(case=bounded_dc_cases())
def test_p1j_effetto_e_lineage_sono_deterministici(case):
    contract = ObservationContract.from_request(case.request)
    for reduction in riduzioni_eseguibili(case.ir):
        outcome = transform(case.ir, reduction.operation, *reduction.operands)
        assert not isinstance(outcome, Refusal)
        after, result = outcome

        first = effetto_osservazione(case.ir, reduction, contract)
        second = effetto_osservazione(case.ir, reduction, contract)
        assert first == second

        successor, lineage = apply_observation_effect(
            case.request, first, operation=reduction.operation)
        validate_observation_lineage(
            case.ir, after, result, reduction.operation, case.request, successor, lineage)
        if first.kind == "identity":
            assert successor is case.request
        elif first.kind == "retarget":
            assert successor is not None
            assert successor.id == case.request.id
            assert successor.quantity == case.request.quantity
            assert successor.target == first.target_after
        else:
            assert successor is None


@settings(max_examples=100, deadline=None, derandomize=True)
@given(case=bounded_dc_cases())
def test_p1l_replay_e_suffix_di_state_id_non_cambiano_la_run(case):
    short = deterministic_state_ids(case.seed, 8)
    long = deterministic_state_ids(case.seed, 12)
    first = orchestrate_didactic_run(case.ir, case.request, state_ids=short)
    second = orchestrate_didactic_run(case.ir, case.request, state_ids=short)
    with_suffix = orchestrate_didactic_run(case.ir, case.request, state_ids=long)

    assert isinstance(first, CertifiedDidacticRun)
    assert first == second == with_suffix
    assert first.original_request is case.request
    assert first.final_request.id == case.request.id
    assert first.final_request.quantity == case.request.quantity
    assert len(first.state_ids) == len(set(first.state_ids))
    assert first.final_execution.claim.status == "VERIFIED"


@settings(max_examples=100, deadline=None, derandomize=True)
@given(case=bounded_dc_cases())
def test_candidati_p1m0_enumerano_fatti_indipendenti_dalla_scelta(case):
    """Ogni scelta eseguibile compare una volta; `pianifica` non fa da filtro."""
    before = pianifica(case.ir, case.request)
    first = enumerate_strategy_candidates(case.ir, case.request)
    second = enumerate_strategy_candidates(case.ir, case.request)

    assert not isinstance(first, Refusal)
    assert first == second
    transforms = tuple(candidate for candidate in first if candidate.operation is not None)
    reductions = riduzioni_eseguibili(case.ir)
    assert tuple((candidate.operation, candidate.operands) for candidate in transforms) == tuple(
        (reduction.operation, reduction.operands) for reduction in reductions
    )
    assert all(candidate.admissible == (candidate.observation_effect.kind != "blocked")
               for candidate in transforms if candidate.observation_effect is not None)
    nodal = tuple(candidate for candidate in first if candidate.technique == "nodal_analysis")
    assert len(nodal) == int(nodale_disponibile(case.ir, case.request.quantity))
    assert pianifica(case.ir, case.request) == before
