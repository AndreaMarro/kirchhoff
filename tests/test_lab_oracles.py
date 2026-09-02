"""Contratti minimi degli oracoli esterni: misurano, mai certificano."""

from fractions import Fraction

import pytest

pytest.importorskip("lcapy", reason="oracolo esterno disponibile solo nell'extra research")

from kirchhoff.domain import mna
from lab.fixtures.cases import case_for_seed
from lab.oracles.lcapy_adapter import lcapy_value
from lab.oracles.ngspice_adapter import ngspice_value


def test_lcapy_mappa_esattamente_un_valore_di_resistore():
    case = case_for_seed(0)
    expected = mna.solve_dc(case.ir)[case.request.target][case.request.quantity]

    assert lcapy_value(case.ir, case.request) == expected


def test_ngspice_rispetta_la_tolleranza_solo_nel_laboratorio():
    case = case_for_seed(1)
    expected = mna.solve_dc(case.ir)[case.request.target][case.request.quantity]
    observed = ngspice_value(case.ir, case.request)

    assert abs(float(expected) - observed) <= 1e-10 + 1e-8 * max(abs(float(expected)), abs(observed))


def test_generatore_del_laboratorio_conserva_fraction_e_request_legata():
    case = case_for_seed(2)

    assert case.ir.domain == "dc"
    assert case.request in case.ir.requests
    assert all(isinstance(component.value.amount, Fraction) for component in case.ir.components)
