"""P1-K: il comparatore DC richiede Fraction su tutto l'output."""

from fractions import Fraction

from kirchhoff.domain.verify import compare_exact_solution_paths

F = Fraction


def _solution():
    return {
        "A": {"voltage": F(1), "current": F(2)},
        "B": {"voltage": F(3), "current": F(4)},
    }


def test_comparator_structural_and_exact_regressions():
    a = _solution()
    assert compare_exact_solution_paths(a, _solution()) is None
    missing_a = _solution()
    del missing_a["A"]
    assert compare_exact_solution_paths(missing_a, _solution()).cause == "path_disagreement"
    missing_b = _solution()
    del missing_b["A"]["voltage"]
    assert compare_exact_solution_paths(_solution(), missing_b).cause == "path_disagreement"
    mismatch = _solution()
    mismatch["A"]["current"] = F(9)
    assert compare_exact_solution_paths(_solution(), mismatch).cause == "path_disagreement"


def test_comparator_rejects_identical_float_and_nonrequested_branch_float():
    float_a = _solution()
    float_b = _solution()
    float_a["A"]["voltage"] = float_b["A"]["voltage"] = 1.0
    assert compare_exact_solution_paths(float_a, float_b).cause == "path_disagreement"
    other_a = _solution()
    other_b = _solution()
    other_a["B"]["current"] = other_b["B"]["current"] = 4.0
    assert compare_exact_solution_paths(other_a, other_b).cause == "path_disagreement"


def test_comparator_rejects_non_fraction_from_path_b_and_missing_b_component():
    a = _solution()
    b = _solution()
    b["A"]["current"] = 2.0
    assert compare_exact_solution_paths(a, b).cause == "path_disagreement"
    b = _solution()
    del b["A"]
    assert compare_exact_solution_paths(a, b).cause == "path_disagreement"
