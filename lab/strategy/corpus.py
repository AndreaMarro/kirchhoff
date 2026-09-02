"""Corpus P1-M0 con provenance e descrittori; nessuna scelta di produzione."""

from __future__ import annotations

from dataclasses import dataclass, replace

from kirchhoff.domain.didactic.candidates import (
    StrategyCandidate,
    enumerate_strategy_candidates,
)
from kirchhoff.domain.didactic.features import CircuitFeatures, extract_circuit_features
from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun, orchestrate_didactic_run
from kirchhoff.domain.didactic.plan import DidacticPlan
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform.engine import transform
from kirchhoff.pipeline.netlist import leggi

from lab.fixtures.cases import LabCase, generated_cases
from lab.graph.graph_view import GraphView


@dataclass(frozen=True, slots=True)
class ResearchCandidate:
    """Feature per-candidato di sola ricerca, derivata da un passo certificato."""

    candidate: StrategyCandidate
    touches_target: bool
    target_distance: int | None
    same_biconnected_region: bool
    component_delta: int
    node_delta: int
    nodal_unknown_delta: int
    equation_delta: int
    simple_supernode_delta: int


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


def _state_ids(seed: int, count: int = 8) -> tuple[str, ...]:
    return tuple(
        conia("ir", 1_700_000_000_000 + seed * 10 + index, bytes([seed % 256, index]) * 5)
        for index in range(count)
    )


def _describe_candidates(case: LabCase, before: CircuitFeatures) -> tuple[ResearchCandidate, ...]:
    view = GraphView.from_ir(case.ir)
    described: list[ResearchCandidate] = []
    for candidate in enumerate_strategy_candidates(case.ir, case.request):
        if candidate.operation is None:
            described.append(ResearchCandidate(
                candidate, False, None, False, 0, 0, 0, 0, 0))
            continue
        outcome = transform(case.ir, candidate.operation, *candidate.operands)
        if isinstance(outcome, Refusal):
            raise AssertionError(f"candidato eseguibile rifiutato: {candidate.operation}")
        after, _result = outcome
        after_features = extract_circuit_features(after, case.request)
        touches = case.request.target in candidate.operands
        described.append(ResearchCandidate(
            candidate=candidate,
            touches_target=touches,
            target_distance=view.target_distance(case.request.target, candidate.operands),
            same_biconnected_region=view.same_biconnected_region(
                case.request.target, candidate.operands),
            component_delta=after_features.component_count - before.component_count,
            node_delta=after_features.node_count - before.node_count,
            nodal_unknown_delta=after_features.nodal_unknown_count - before.nodal_unknown_count,
            equation_delta=_equation_count(after_features) - _equation_count(before),
            simple_supernode_delta=(after_features.simple_supernode_count
                                    - before.simple_supernode_count),
        ))
    return tuple(described)


def build_row(case: LabCase, *, provenance: str) -> CorpusRow:
    features = extract_circuit_features(case.ir, case.request)
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
        candidates=_describe_candidates(case, features),
        current_plan=plan,
        run=run,
    )


def build_generated_corpus(number: int = 200) -> tuple[CorpusRow, ...]:
    return tuple(build_row(case, provenance="generated-public-bounded") for case in generated_cases(number))


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
    ("two-target-distances", "mixed", _MIXED, "V1", "voltage"),
    ("component-not-unknown-reduction", "series", _SERIES, "R1", "current"),
    ("unknown-reduction", "parallel", _PARALLEL, "R1", "voltage"),
    ("bridge-rigid-core", "mixed", _MIXED, "V1", "voltage"),
    ("trivial-nodal", "supernode", _SUPERNODE, "R1", "voltage"),
    ("multi-step-ladder", "series", _MULTI_SERIES, "R1", "current"),
    ("current-retarget", "series", _SERIES, "R1", "current"),
    ("voltage-retarget", "parallel", _PARALLEL, "R1", "voltage"),
    ("identity-heavy-path", "peripheral", _MULTI_SERIES, "V1", "voltage"),
    ("supernode-compatible", "supernode", _SUPERNODE, "R1", "voltage"),
    ("equivalent-first-series", "series", _MULTI_SERIES, "R1", "current"),
    ("equivalent-first-parallel", "parallel", _MULTI_PARALLEL, "R1", "voltage"),
    ("reversed-source-polarity", "supernode", _SUPERNODE.replace("V2 a b 2", "V2 b a 2"), "R1", "voltage"),
    ("zero-current-source", "parallel", _PARALLEL.replace("I1 0 a 1", "I1 0 a 0"), "R1", "voltage"),
    ("awkward-rational-resistance", "series", _SERIES.replace("100 ohm", "7/3 ohm"), "R1", "current"),
    ("high-low-ratio", "parallel", _PARALLEL.replace("100 ohm", "1/1000 ohm").replace("300 ohm", "1000 ohm"), "R1", "voltage"),
    ("two-source-balance", "mixed", _MIXED.replace(
        "I1 0 b 1 ampere", "I1 0 b 1 ampere\nI2 b 0 1/3 ampere"), "V1", "voltage"),
    ("target-voltage-source", "mixed", _MIXED, "V1", "voltage"),
    ("target-current-source", "mixed", _MIXED, "I1", "current"),
    ("parallel-after-series", "mixed", _MIXED, "V1", "voltage"),
    ("series-after-parallel", "mixed", _MIXED, "V1", "voltage"),
    ("floating-source-identity", "supernode", _SUPERNODE, "V1", "voltage"),
    ("parallel-periphery", "peripheral", _MULTI_PARALLEL, "R4", "voltage"),
    ("series-periphery", "peripheral", _MULTI_SERIES, "R4", "current"),
    ("mixed-ambiguous", "mixed", _MIXED, "V1", "voltage"),
)


def deliberate_probes() -> tuple[LabCase, ...]:
    """Trenta configurazioni nominate, senza dati nascosti o fixture di prodotto."""
    cases: list[LabCase] = []
    for index, (probe_id, family, netlist, target, quantity) in enumerate(_PROBE_BLUEPRINTS):
        request = Request(f"q_probe_{index:02d}", quantity, target)  # type: ignore[arg-type]
        ir = replace(leggi(netlist), requests=(request,))
        cases.append(LabCase(1_000 + index, f"probe-{index:02d}-{probe_id}", family, ir, request))
    return tuple(cases)
