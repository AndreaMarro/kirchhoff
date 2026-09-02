"""Corpus differenziale P1-M0: MNA, tableau e due oracoli esterni non autorevoli."""

from __future__ import annotations

import shutil

import pytest

pytest.importorskip("lcapy", reason="oracolo esterno disponibile solo nell'extra research")
if shutil.which("ngspice") is None:
    pytest.skip("ngspice disponibile solo nel workflow research", allow_module_level=True)

from kirchhoff.domain import mna
from kirchhoff.domain.independent_dc import solve_dc_tableau
from lab.fixtures.cases import generated_cases
from lab.oracles.lcapy_adapter import lcapy_value
from lab.oracles.ngspice_adapter import ngspice_value


def test_duecento_casi_sono_triagiati_su_quattro_percorsi_espliciti():
    lcapy_matches = 0
    ngspice_matches = 0
    for case in generated_cases(200):
        mna_value = mna.solve_dc(case.ir)[case.request.target][case.request.quantity]
        tableau_value = solve_dc_tableau(case.ir)[case.request.target][case.request.quantity]
        assert tableau_value == mna_value, case.case_id
        assert lcapy_value(case.ir, case.request) == mna_value, case.case_id
        lcapy_matches += 1
        observed = ngspice_value(case.ir, case.request)
        assert abs(float(mna_value) - observed) <= 1e-10 + 1e-8 * max(
            abs(float(mna_value)), abs(observed)), case.case_id
        ngspice_matches += 1

    assert lcapy_matches == 200
    assert ngspice_matches == 200
