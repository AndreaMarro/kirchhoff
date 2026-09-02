"""Politiche deterministiche offline: confrontano, non mutano `pianifica`."""

from __future__ import annotations

from collections.abc import Callable

from .corpus import ResearchCandidate


def _admissible(candidates: tuple[ResearchCandidate, ...]) -> tuple[ResearchCandidate, ...]:
    allowed = tuple(candidate for candidate in candidates if candidate.candidate.admissible)
    if not allowed:
        raise ValueError("nessun candidato ammissibile")
    return allowed


def current(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    """Replica l'ordine osservato dal planner corrente sui candidati ammissibili."""
    return _admissible(candidates)[0]


def target_first(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        candidate.candidate.technique == "nodal_analysis",
        not candidate.touches_target,
        candidate.target_distance is None,
        candidate.target_distance if candidate.target_distance is not None else 10**9,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


def complexity_first(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        candidate.candidate.technique == "nodal_analysis",
        candidate.nodal_unknown_delta,
        candidate.equation_delta,
        candidate.component_delta,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


def lexicographic(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        candidate.candidate.technique == "nodal_analysis",
        not candidate.touches_target,
        candidate.target_distance is None,
        candidate.target_distance if candidate.target_distance is not None else 10**9,
        candidate.nodal_unknown_delta,
        candidate.equation_delta,
        candidate.component_delta,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


POLICIES: dict[str, Callable[[tuple[ResearchCandidate, ...]], ResearchCandidate]] = {
    "current": current,
    "target-first": target_first,
    "complexity": complexity_first,
    "lexicographic": lexicographic,
}
