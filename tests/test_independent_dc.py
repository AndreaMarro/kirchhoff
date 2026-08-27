"""Kernel lineare e tableau di ramo del Percorso B, isolati da MNA."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.independent_dc import (
    TableauBuildError,
    TableauSingularError,
    solve_dc_tableau,
    solve_tableau_linear,
)
from kirchhoff.domain.ir import IR, Component

F = Fraction


def test_tableau_1x1():
    assert solve_tableau_linear([[F(1)]], [F(3)]) == [F(3)]


def test_tableau_2x2():
    x = solve_tableau_linear(
        [[F(2), F(1)], [F(1), F(-1)]],
        [F(5), F(1)],
    )
    assert x == [F(2), F(1)]


def test_tableau_pivot_nullo_scambia_righe():
    x = solve_tableau_linear(
        [[F(0), F(1)], [F(1), F(0)]],
        [F(3), F(4)],
    )
    assert x == [F(4), F(3)]


def test_tableau_coefficienti_fraction():
    x = solve_tableau_linear(
        [[F(1, 2), F(1, 3)], [F(1, 4), F(1, 5)]],
        [F(1), F(1)],
    )
    assert all(isinstance(v, Fraction) for v in x)
    assert x[0] == F(-8)
    assert x[1] == F(15)


def test_tableau_sistema_singolare():
    with pytest.raises(TableauSingularError, match="singolare"):
        solve_tableau_linear(
            [[F(1), F(2)], [F(2), F(4)]],
            [F(1), F(2)],
        )


def test_tableau_deterministico():
    a = [[F(3), F(1)], [F(1), F(2)]]
    b = [F(7), F(8)]
    assert solve_tableau_linear(a, b) == solve_tableau_linear(a, b)


def test_tableau_niente_float_in_uscita():
    x = solve_tableau_linear([[F(2)]], [F(1)])
    assert x == [F(1, 2)]
    assert type(x[0]) is Fraction


def test_tableau_rifiuta_float_in_ingresso():
    with pytest.raises(TypeError, match="Fraction"):
        solve_tableau_linear([[1.5]], [3.0])


def test_tableau_matrice_non_quadra():
    with pytest.raises(TableauBuildError):
        solve_tableau_linear([[F(1), F(2)]], [F(1)])


def test_tableau_vuoto():
    assert solve_tableau_linear([], []) == []


def _dc(comps, nodes=None):
    if nodes is None:
        nodes = tuple(sorted({t for c in comps for t in c.terminals}))
    return IR("1.0.0", "dc", "generated", nodes, comps, ())


def test_vr_semplice():
    ir = _dc((
        Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
        Component.of("R1", "resistor", ("A", "0"), F(5), "R_1"),
    ))
    sol = solve_dc_tableau(ir)
    assert sol["R1"]["voltage"] == F(10)
    assert sol["R1"]["current"] == F(2)
    assert sol["E1"]["voltage"] == F(10)
    assert sol["E1"]["current"] == F(-2)
    assert all(isinstance(sol[c][q], Fraction) for c in sol for q in sol[c])


def test_tipo_non_ammesso():
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (Component.of("C1", "capacitor", ("A", "0"), F(1, 1000), "C_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        (),
    )
    with pytest.raises(ValueError, match="non ammesso"):
        solve_dc_tableau(ir)


def test_tableau_accetta_int():
    assert solve_tableau_linear([[1]], [3]) == [F(3)]


def test_tableau_senza_rami():
    ir = IR("1.0.0", "dc", "generated", ("0",), (), ())
    with pytest.raises(TableauBuildError, match="senza rami"):
        solve_dc_tableau(ir)


def test_segno_e_percorso_albero():
    from kirchhoff.domain.independent_dc import (
        _albero_ricoprente,
        _percorso_albero,
        _segno_percorrenza,
    )

    ir = _dc((
        Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
        Component.of("R1", "resistor", ("A", "B"), F(5), "R_1"),
        Component.of("R2", "resistor", ("B", "0"), F(5), "R_2"),
        Component.of("R3", "resistor", ("A", "0"), F(10), "R_3"),
    ))
    parent, _usati = _albero_ricoprente(ir)
    assert _percorso_albero(ir, parent, "A", "A") == []
    verso_ref = _percorso_albero(ir, parent, "A", "0")
    assert verso_ref
    assert _percorso_albero(ir, parent, "0", "A")
    with pytest.raises(TableauBuildError, match="percorrenza"):
        _segno_percorrenza(ir.component("R1"), "A", "0")
    parent_rotto = dict(parent)
    parent_rotto["Z"] = None
    with pytest.raises(TableauBuildError, match="antenato"):
        _percorso_albero(ir, parent_rotto, "A", "Z")


def test_costitutiva_tipo_estraneo():
    from kirchhoff.domain.independent_dc import _costitutiva

    c = Component.of("C1", "capacitor", ("A", "0"), F(1, 1000), "C_1")
    with pytest.raises(ValueError, match="non ammesso"):
        _costitutiva(c, 0, 1, [F(0), F(0)], [F(0)])


def test_albero_incompleto():
    ir = _dc(
        (
            Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
            Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
            Component.of("R2", "resistor", ("B", "C"), F(10), "R_2"),
            Component.of("R3", "resistor", ("B", "C"), F(20), "R_3"),
        ),
        ("0", "A", "B", "C"),
    )
    with pytest.raises(TableauBuildError, match="incompleto"):
        solve_dc_tableau(ir)
