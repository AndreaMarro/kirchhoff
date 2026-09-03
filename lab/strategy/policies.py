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
    """Replica il piano corrente con un flag esplicito, non con l'ordine della tupla."""
    selected = tuple(candidate for candidate in candidates if candidate.selected_by_current_planner)
    if len(selected) != 1:
        raise ValueError("il corpus non identifica una sola scelta del planner corrente")
    return selected[0]


def _count(value: int | None) -> int:
    return value if value is not None else 10**9


def target_first(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        not candidate.touches_target,
        candidate.target_distance is None,
        candidate.target_distance if candidate.target_distance is not None else 10**9,
        not candidate.directly_resolves_request,
        _count(candidate.resulting_equation_count),
        _count(candidate.resulting_nodal_unknown_count),
        candidate.transformation_count_cost,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


def complexity_first(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        _count(candidate.resulting_equation_count),
        _count(candidate.resulting_nodal_unknown_count),
        _count(candidate.resulting_component_count),
        candidate.transformation_count_cost,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


def lexicographic(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    return min(_admissible(candidates), key=lambda candidate: (
        not candidate.touches_target,
        candidate.target_distance is None,
        candidate.target_distance if candidate.target_distance is not None else 10**9,
        not candidate.directly_resolves_request,
        _count(candidate.resulting_equation_count),
        _count(candidate.resulting_nodal_unknown_count),
        _count(candidate.resulting_component_count),
        candidate.transformation_count_cost,
        candidate.candidate.operation or "",
        candidate.candidate.operands,
    ))


def direct_nodal(candidates: tuple[ResearchCandidate, ...]) -> ResearchCandidate:
    """Baseline estremo: il nodale prevale soltanto se e' davvero eseguibile."""
    allowed = _admissible(candidates)
    nodal = tuple(
        candidate for candidate in allowed
        if candidate.candidate.technique == "nodal_analysis"
    )
    if nodal:
        if len(nodal) != 1:
            raise ValueError("il corpus espone piu' candidati nodali")
        return nodal[0]
    return min(allowed, key=lambda candidate: (
        candidate.candidate.operation or "", candidate.candidate.operands,
    ))


POLICIES: dict[str, Callable[[tuple[ResearchCandidate, ...]], ResearchCandidate]] = {
    "current": current,
    "direct-nodal": direct_nodal,
    "target-first": target_first,
    "complexity": complexity_first,
    "lexicographic": lexicographic,
}
