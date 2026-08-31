"""P1-H: confine architetturale, firma e assenza di CAS/MNA in produzione."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from kirchhoff.domain.didactic import resolve_request
from kirchhoff.domain.didactic.request import ResolvedQuantity


def test_firma_senza_derivation_state():
    assert list(inspect.signature(resolve_request).parameters) == [
        "ir",
        "request",
        "solution",
    ]


def test_produzione_senza_import_vietati():
    percorso = Path(__file__).resolve().parents[1] / "src/kirchhoff/domain/didactic/request.py"
    testo = percorso.read_text(encoding="utf-8")
    albero = ast.parse(testo, filename=str(percorso))
    moduli: set[str] = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            moduli.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            moduli.add(nodo.module)
    vietati = {
        "kirchhoff.domain.mna",
        "kirchhoff.domain.independent_dc",
        "kirchhoff.pipeline",
        "kirchhoff.render",
        "kirchhoff.eval",
        "mna",
        "independent_dc",
        "pipeline",
        "render",
        "eval",
        "sympy",
        "lcapy",
        "numpy",
        "scipy",
        "egglog",
    }
    assert moduli.isdisjoint(vietati)
    for frammento in (
        "from ..mna",
        "from ...mna",
        "import kirchhoff.domain.mna",
        "solve_dc",
        "solve_dc_tableau",
        "from ..independent_dc",
        "import sympy",
        "import lcapy",
        "import numpy",
        "import scipy",
        "import egglog",
    ):
        assert frammento not in testo


def test_nessun_letterale_float():
    percorso = Path(__file__).resolve().parents[1] / "src/kirchhoff/domain/didactic/request.py"
    albero = ast.parse(percorso.read_text(encoding="utf-8"), filename=str(percorso))
    assert [
        n.value for n in ast.walk(albero)
        if isinstance(n, ast.Constant) and isinstance(n.value, float)
    ] == []


def test_helper_kcl_non_esportati():
    import kirchhoff.domain.didactic as pacchetto
    for nome in (
        "_branch_current_from_solution",
        "_somma_uscenti",
        "_corrente_generatore_tensione",
        "_uscente_dal_nodo",
    ):
        assert not hasattr(pacchetto, nome)
    assert hasattr(pacchetto, "ResolvedQuantity")
    assert hasattr(pacchetto, "resolve_request")
    assert pacchetto.ResolvedQuantity is ResolvedQuantity
