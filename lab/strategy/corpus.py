"""Corpus P1-M0 con provenance e descrittori; nessuna scelta di produzione."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

from kirchhoff.domain.didactic.candidates import (
    StrategyCandidate,
    enumerate_strategy_candidates,
)
from kirchhoff.domain.didactic.features import CircuitFeatures, extract_circuit_features
from kirchhoff.domain.didactic.observation import apply_observation_effect
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun, orchestrate_didactic_run
from kirchhoff.domain.didactic.plan import DidacticPlan
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform.engine import transform
from kirchhoff.pipeline.netlist import leggi

from lab.fixtures.cases import LabCase, topology_diverse_cases
from lab.graph.graph_view import GraphView


@dataclass(frozen=True, slots=True)
class ResearchCandidate:
    """Feature per-candidato di sola ricerca, derivata da un passo certificato."""

    candidate: StrategyCandidate
    selected_by_current_planner: bool
    directly_resolves_request: bool
    touches_target: bool
    target_distance: int | None
    same_biconnected_region: bool
    resulting_component_count: int | None
    resulting_nodal_unknown_count: int | None
    resulting_equation_count: int | None
    transformation_count_cost: int


@dataclass(frozen=True, slots=True)
class CorpusRow:
    """Una riga che permette di riprodurre ogni decisione osservata."""

    case: LabCase
    provenance: str
    features: CircuitFeatures
    candidates: tuple[ResearchCandidate, ...]
    current_plan: DidacticPlan
    run: CertifiedDidacticRun


def _equation_count(features: CircuitFeatures) -> int:
    """KCL ordinarie + KCL/vincolo per supernodo semplice."""
    return features.ordinary_kcl_count + 2 * features.simple_supernode_count


def _state_ids(seed: int, count: int = 64) -> tuple[str, ...]:
    return tuple(
        conia("ir", 1_700_000_000_000 + seed * 10 + index, bytes([seed % 256, index]) * 5)
        for index in range(count)
    )


def _describe_candidates(
    case: LabCase, before: CircuitFeatures, current_plan: DidacticPlan,
) -> tuple[ResearchCandidate, ...]:
    view = GraphView.from_ir(case.ir)
    described: list[ResearchCandidate] = []
    candidates = enumerate_strategy_candidates(case.ir, case.request)
    if isinstance(candidates, Refusal):
        raise AssertionError(f"scope P1-M0 rifiutato: {candidates}")
    for candidate in candidates:
        current = (
            candidate.technique == current_plan.technique
            and candidate.actions == current_plan.actions
        )
        if candidate.operation is None:
            described.append(ResearchCandidate(
                candidate, current, True, True, 0, True,
                before.component_count, before.nodal_unknown_count,
                _equation_count(before), 0,
            ))
            continue
        outcome = transform(case.ir, candidate.operation, *candidate.operands)
        if isinstance(outcome, Refusal):
            raise AssertionError(f"candidato eseguibile rifiutato: {candidate.operation}")
        after, _result = outcome
        if candidate.observation_effect is None or candidate.observation_effect.kind == "blocked":
            described.append(ResearchCandidate(
                candidate, current, False,
                case.request.target in candidate.operands,
                view.target_distance(case.request.target, candidate.operands),
                view.same_biconnected_region(case.request.target, candidate.operands),
                None, None, None, 1,
            ))
            continue
        successor, _lineage = apply_observation_effect(
            case.request, candidate.observation_effect, operation=candidate.operation)
        if successor is None:
            raise AssertionError("candidato ammissibile senza Request successiva")
        after_features = extract_circuit_features(
            replace(after, requests=(successor,)), successor)
        if isinstance(after_features, Refusal):
            raise AssertionError(f"feature dopo trasformazione rifiutate: {after_features}")
        touches = case.request.target in candidate.operands
        described.append(ResearchCandidate(
            candidate=candidate,
            selected_by_current_planner=current,
            directly_resolves_request=False,
            touches_target=touches,
            target_distance=view.target_distance(case.request.target, candidate.operands),
            same_biconnected_region=view.same_biconnected_region(
                case.request.target, candidate.operands),
            resulting_component_count=after_features.component_count,
            resulting_nodal_unknown_count=after_features.nodal_unknown_count,
            resulting_equation_count=_equation_count(after_features),
            transformation_count_cost=1,
        ))
    return tuple(described)


def build_row(case: LabCase, *, provenance: str) -> CorpusRow:
    features = extract_circuit_features(case.ir, case.request)
    if isinstance(features, Refusal):
        raise AssertionError(f"caso P1-M0 fuori scope: {features}")
    plan = pianifica(case.ir, case.request)
    if isinstance(plan, Refusal):
        raise AssertionError(f"caso P1-M0 non pianificabile: {case.case_id}")
    run = orchestrate_didactic_run(case.ir, case.request, state_ids=_state_ids(case.seed))
    if isinstance(run, Refusal):
        raise AssertionError(f"caso P1-M0 non eseguibile: {case.case_id}")
    return CorpusRow(
        case=case,
        provenance=provenance,
        features=features,
        candidates=_describe_candidates(case, features, plan),
        current_plan=plan,
        run=run,
    )


@lru_cache(maxsize=1)
def _generated_corpus_200() -> tuple[CorpusRow, ...]:
    return tuple(
        build_row(case, provenance="generated-topology-diverse")
        for case in topology_diverse_cases(200)
    )


def build_generated_corpus(number: int = 200) -> tuple[CorpusRow, ...]:
    """Prefisso immutabile del corpus pubblico congelato di 200 topologie."""
    if number < 1 or number > 200:
        raise ValueError("il corpus strategico P1-M0 supporta da 1 a 200 casi")
    return _generated_corpus_200()[:number]


_SERIES = """V1 c 0 12 volt
R1 c a 100 ohm
R2 a b 220 ohm
R3 b 0 330 ohm
I1 0 b 1 ampere
"""
_PARALLEL = """V1 b 0 12 volt
R1 b a 100 ohm
R2 b a 300 ohm
R3 a 0 330 ohm
I1 0 a 1 ampere
"""
_MULTI_SERIES = """V1 d 0 12 volt
R1 d a 100 ohm
R2 a b 220 ohm
R3 b c 330 ohm
R4 c 0 470 ohm
I1 0 c 1 ampere
"""
_MULTI_PARALLEL = """V1 b 0 12 volt
R1 b a 100 ohm
R2 b a 220 ohm
R3 b a 330 ohm
R4 a 0 470 ohm
I1 0 a 1 ampere
"""
_MIXED = """V1 d 0 12 volt
R1 d a 100 ohm
R2 a b 220 ohm
R3 d b 330 ohm
R4 b 0 470 ohm
I1 0 b 1 ampere
"""
_SUPERNODE = """V1 s 0 9 volt
V2 a b 2 volt
R1 s a 3 ohm
R2 b 0 4 ohm
R3 a 0 5 ohm
I1 0 b 1 ampere
"""


_PROBE_BLUEPRINTS: tuple[tuple[str, str, str, str, str], ...] = (
    ("target-in-series-pair", "series", _SERIES, "R1", "current"),
    ("target-in-parallel-pair", "parallel", _PARALLEL, "R1", "voltage"),
    ("untouched-target-local-reduction", "peripheral", _MULTI_SERIES, "V1", "voltage"),
    ("untouched-target-far-reduction", "peripheral", _MULTI_PARALLEL, "V1", "voltage"),
    ("multiple-simultaneous-reductions", "mixed", _MULTI_SERIES, "R1", "current"),
    ("identity-observation", "peripheral", _MULTI_SERIES, "V1", "voltage"),
    ("component-not-unknown-reduction", "series", _SERIES, "R1", "current"),
    ("unknown-reduction", "parallel", _PARALLEL, "R1", "voltage"),
    ("bridge-rigid-core", "mixed", _MIXED, "V1", "voltage"),
    ("trivial-nodal", "supernode", _SUPERNODE, "R1", "voltage"),
)


def deliberate_probes() -> tuple[LabCase, ...]:
    """Trenta casi nominati: dieci mirati e venti topologie SP selezionate."""
    cases: list[LabCase] = []
    for index, (probe_id, family, netlist, target, quantity) in enumerate(_PROBE_BLUEPRINTS):
        request = Request(f"q_probe_{index:02d}", quantity, target)  # type: ignore[arg-type]
        ir = replace(leggi(netlist), requests=(request,))
        cases.append(LabCase(1_000 + index, f"probe-{index:02d}-{probe_id}", family, ir, request))
    for index, case in enumerate(topology_diverse_cases(20), start=len(cases)):
        request = Request(f"q_probe_{index:02d}", "voltage", case.request.target)
        ir = replace(case.ir, requests=(request,))
        cases.append(LabCase(
            2_000 + index,
            f"probe-{index:02d}-selected-{case.case_id}",
            case.family_id,
            ir,
            request,
        ))
    return tuple(cases)
