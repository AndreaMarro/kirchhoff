"""P1-G: restanti casi positivi del solver di derivazione."""
from __future__ import annotations

from kirchhoff.domain.didactic import build_linear_system, solve_derivation

from test_didactic_solve import F, V, kcl, nv, stato, vincolo


def test_t7_supernodo_con_generatore_di_corrente():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown"), nv("b", "unknown")),
        equations=(
            kcl((F(1, 10), "a"), (F(1, 20), "b"), rhs=-1, focus="V1"),
            vincolo((1, "a"), (-1, "b"), rhs=6, focus="V1"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-14, 3)
    assert sol.value_of(V("b")) == F(-32, 3)


def test_t8_supernodi_disgiunti():
    s = stato(
        variables=(
            nv("0", "reference"),
            nv("a", "unknown"),
            nv("b", "unknown"),
            nv("c", "unknown"),
            nv("d", "unknown"),
        ),
        equations=(
            kcl((1, "a"), (F(1, 2), "b"), rhs=0, focus="V1"),
            vincolo((1, "a"), (-1, "b"), rhs=6, focus="V1"),
            kcl((1, "c"), (1, "d"), rhs=0, focus="V2"),
            vincolo((1, "c"), (-1, "d"), rhs=3, focus="V2"),
        ),
    )
    sistema = build_linear_system(s)
    assert sistema.variables == (V("a"), V("b"), V("c"), V("d"))
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(2)
    assert sol.value_of(V("b")) == F(-4)
    assert sol.value_of(V("c")) == F(3, 2)
    assert sol.value_of(V("d")) == F(-3, 2)


def test_t9_misto_noto_ordinario_supernodo():
    s = stato(
        variables=(
            nv("0", "reference"),
            nv("a", "unknown"),
            nv("b", "unknown"),
            nv("c", "unknown"),
            nv("k", "known_from_source", -5, "Vk"),
        ),
        equations=(
            kcl((F(3, 10), "a"), (F(-1, 5), "k"), (F(-1, 10), "0"), rhs=0, focus="a"),
            kcl((F(1, 4), "b"), (F(1, 4), "c"), rhs=0, focus="V2"),
            vincolo((1, "b"), (-1, "c"), rhs=4, focus="V2"),
        ),
    )
    sol = solve_derivation(s)
    assert sol.value_of(V("a")) == F(-10, 3)
    assert sol.value_of(V("b")) == F(2)
    assert sol.value_of(V("c")) == F(-2)
    assert sol.value_of(V("k")) == F(-5)


def test_t10_tutti_i_valori_finali_in_ordine_canonico():
    s = stato(
        variables=(
            nv("a", "unknown"),
            nv("k", "known_from_source", -5, "Vk"),
            nv("0", "reference"),
        ),
        equations=(kcl((1, "a"), rhs=3, focus="a"),),
    )
    sol = solve_derivation(s)
    refs = tuple(item.variable for item in sol.values)
    assert refs == (V("0"), V("a"), V("k"))
    assert sol.value_of(V("0")) == F(0)
    assert sol.value_of(V("k")) == F(-5)
    assert sol.value_of(V("a")) == F(3)
