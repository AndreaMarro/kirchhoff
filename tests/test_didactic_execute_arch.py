"""P1-I: confine architetturale dell'executor."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from kirchhoff.domain.didactic import (
    DidacticExecution,
    NodalExecution,
    TransformExecution,
    execute_plan,
)
from kirchhoff.domain.didactic.execute import DidacticExecution as Alias


PERCORSO = (
    Path(__file__).resolve().parents[1]
    / "src/kirchhoff/domain/didactic/execute.py"
)


def _moduli_e_testo() -> tuple[set[str], str]:
    testo = PERCORSO.read_text(encoding="utf-8")
    albero = ast.parse(testo, filename=str(PERCORSO))
    moduli: set[str] = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            moduli.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            moduli.add(nodo.module)
    return moduli, testo


def test_firma_execute_plan():
    assert list(inspect.signature(execute_plan).parameters) == [
        "ir",
        "request",
        "plan",
        "proof_node",
    ]
    param = inspect.signature(execute_plan).parameters["proof_node"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY


def test_nessun_import_planner():
    moduli, testo = _moduli_e_testo()
    assert "planner" not in moduli
    assert ".planner" not in moduli
    assert "from .planner" not in testo
    assert "pianifica(" not in testo
    assert "import planner" not in testo


def test_nessun_import_vietato():
    moduli, testo = _moduli_e_testo()
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
        "from ..pipeline",
        "import sympy",
        "import lcapy",
        "import numpy",
        "import scipy",
        "import egglog",
        "from .planner",
        "pianifica(",
    ):
        assert frammento not in testo


def test_nessun_letterale_float():
    albero = ast.parse(PERCORSO.read_text(encoding="utf-8"), filename=str(PERCORSO))
    assert [
        n.value for n in ast.walk(albero)
        if isinstance(n, ast.Constant) and isinstance(n.value, float)
    ] == []


def test_export_pubblici_e_helper_privati():
    import kirchhoff.domain.didactic as pacchetto
    assert pacchetto.NodalExecution is NodalExecution
    assert pacchetto.TransformExecution is TransformExecution
    assert pacchetto.execute_plan is execute_plan
    assert pacchetto.DidacticExecution is DidacticExecution is Alias
    for nome in (
        "_execute_nodal",
        "_execute_transform",
        "_assert_request_plan_binding",
        "_assert_request_ir_binding",
    ):
        assert not hasattr(pacchetto, nome)
    import kirchhoff.domain.didactic.execute as modulo
    assert hasattr(modulo, "_execute_nodal")
