"""P1-G: rifiuti strutturali del solver di derivazione."""
from __future__ import annotations

import pytest

from kirchhoff.domain.didactic import (
    DerivationSolution,
    DerivationState,
    SolvedVariable,
    build_linear_system,
    solve_derivation,
)
from kirchhoff.domain.exact import SingularSystemError

from test_didactic_solve import F, NODO, V, kcl, nv, stato


def test_n1_senza_riferimento():
    s = DerivationState(
        "D1", NODO, reference_node=None,
        variables=(nv("a", "unknown"),),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="riferimento assente"):
        build_linear_system(s)


def test_n2_riferimento_non_dichiarato():
    s = stato(
        variables=(nv("a", "unknown"),),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
        reference="0",
    )
    with pytest.raises(ValueError, match="non dichiarato"):
        build_linear_system(s)


def test_n3_ruolo_riferimento_sbagliato():
    s = stato(
        variables=(nv("0", "known_from_source", 0, "V0"), nv("a", "unknown")),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="ruolo"):
        build_linear_system(s)


def test_n4_zero_incognite():
    s = DerivationState(
        "D1", NODO, reference_node="0",
        variables=(nv("0", "reference"), nv("k", "known_from_source", 5, "Vk")),
    )
    with pytest.raises(ValueError, match="nessuna incognita"):
        build_linear_system(s)


def test_n5_variabile_equazione_non_dichiarata():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(kcl((1, "ghost"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="non dichiarato"):
        build_linear_system(s)


def test_n6_poche_equazioni():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="incompleta|insufficient"):
        build_linear_system(s)


def test_n7_troppe_equazioni():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(
            kcl((1, "a"), rhs=1, focus="a"),
            kcl((2, "a"), rhs=2, focus="b"),
        ),
    )
    with pytest.raises(ValueError, match="non quadrata|excess"):
        build_linear_system(s)


def test_n8_tautologia_dopo_sostituzione():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(kcl((1, "0"), rhs=0, focus="a"),),
    )
    with pytest.raises(ValueError, match="tautolog"):
        build_linear_system(s)


def test_n9_contraddizione_dopo_sostituzione():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(kcl((1, "0"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="contraddittor"):
        build_linear_system(s)


def test_n10_colonna_nulla():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((1, "a"), rhs=1, focus="a"),
            kcl((2, "a"), rhs=3, focus="x"),
        ),
    )
    with pytest.raises(ValueError, match="unconstrained"):
        build_linear_system(s)


def test_n11_singolare_non_banale():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((1, "a"), (1, "b"), rhs=1, focus="a"),
            kcl((2, "a"), (2, "b"), rhs=2, focus="b"),
        ),
    )
    with pytest.raises(SingularSystemError):
        solve_derivation(s)


def test_n12_valore_finale_duplicato():
    with pytest.raises(ValueError, match="duplicato"):
        DerivationSolution("D1", (
            SolvedVariable(V("a"), F(1)),
            SolvedVariable(V("a"), F(2)),
        ))


def test_n13_value_of_assente():
    sol = DerivationSolution("D1", (SolvedVariable(V("a"), F(1)),))
    with pytest.raises(KeyError):
        sol.value_of(V("ghost"))


def test_riferimento_corrotto_non_zero():
    riferimento = nv("0", "reference")
    object.__setattr__(riferimento, "known_value", F(1))
    s = stato(
        variables=(riferimento, nv("a", "unknown")),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="known_value"):
        build_linear_system(s)


def test_noto_corrotto_senza_valore():
    noto = nv("k", "known_from_source", 5, "Vk")
    object.__setattr__(noto, "known_value", None)
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), noto),
        equations=(kcl((1, "a"), rhs=1, focus="a"),),
    )
    with pytest.raises(ValueError, match="senza known_value"):
        build_linear_system(s)
