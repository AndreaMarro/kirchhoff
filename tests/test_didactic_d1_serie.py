"""D1 canonica: serie con target in corrente, retarget fino a VERIFIED.

V1 b 0 12 volt / R1 b a 100 ohm / R2 a 0 220 ohm, ? current R1.

Semantica attesa: pianifica sceglie certified_transform_path serie(R1,R2),
l'effetto osservativo fa retarget sulla Request successiva I(R1R2eq), la
continuazione terminale risolve esattamente 3/80 A e il TruthfulnessGate
emette VERIFIED. Non sostituire con una ladder piu' grande, non cambiare
la quantity in voltage, non toccare la truth table P1-J.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic.analytical import applica_passo, stato_iniziale

from kirchhoff.domain.didactic.execute import TransformExecution
from kirchhoff.domain.didactic.capabilities import nodale_disponibile
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.didactic.plan import DidacticPlan, PlannedAction
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.didactic.solve import _solve_known_only, solve_derivation
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi
from test_didactic_solve import kcl, nv, stato


D1_SERIE = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
"""


def _d1_input() -> tuple:
    request = Request("q_d1", "current", "R1")  # type: ignore[arg-type]
    return replace(leggi(D1_SERIE), requests=(request,)), request


def _states(number: int, *, start: int = 100) -> tuple[str, ...]:
    return tuple(
        conia("ir", start + index, bytes(range(index, index + 10)))
        for index in range(number)
    )


def test_d1_pianifica_serie_sul_target_in_corrente():
    ir, request = _d1_input()
    plan = pianifica(ir, request)
    assert isinstance(plan, DidacticPlan)
    assert plan.technique == "certified_transform_path"
    assert plan.actions == (PlannedAction("serie", ("R1", "R2")),)


def test_d1_serie_current_retarget_fino_a_verified():
    ir, request = _d1_input()
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(run, CertifiedDidacticRun)
    assert len(run.transform_executions) == 1
    first = run.transform_executions[0]
    assert isinstance(first, TransformExecution)
    assert first.observation_effect.kind == "retarget"
    assert first.successor_request is not None
    assert first.successor_request.quantity == "current"
    assert first.successor_request.target == "R1R2eq"
    assert run.final_request == first.successor_request
    resolved = run.final_execution.execution.resolved
    assert resolved.quantity == "current"
    assert resolved.target == "R1R2eq"
    assert resolved.value.amount == Fraction(3, 80)
    assert resolved.value.unit == "ampere"
    assert run.final_execution.claim.status == "VERIFIED"


TERMINALE = """\
V1 b 0 12 volt
R1R2eq b 0 320 ohm
"""


def _terminale_input(quantity="current"):
    request = Request("q_t", quantity, "R1R2eq")  # type: ignore[arg-type]
    return replace(leggi(TERMINALE), requests=(request,)), request


def test_terminale_tensione_su_noto_zero_trasformazioni():
    ir, request = _terminale_input("voltage")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(1))
    assert isinstance(run, CertifiedDidacticRun)
    assert run.transform_executions == ()
    resolved = run.final_execution.execution.resolved
    assert resolved.value.amount == Fraction(12)
    assert resolved.value.unit == "volt"
    assert run.final_execution.claim.status == "VERIFIED"


def test_terminale_nodo_non_coperto_rifiuta():
    request = Request("q_t", "current", "R1")  # type: ignore[arg-type]
    flottante = IR(
        "1.0.0", "dc", "netlist", ("0", "a", "b"),
        (
            Component.of("V1", "voltage_source_dc", ("b", "0"), Fraction(12), "V1"),
            Component.of("V2", "voltage_source_dc", ("a", "b"), Fraction(2), "V2"),
            Component.of("R1", "resistor", ("a", "0"), Fraction(100), "R1"),
        ),
        (request,),
    )
    assert nodale_disponibile(flottante, "current") is False
    assert isinstance(pianifica(flottante, request), Refusal)


def test_terminale_catena_flottante_rifiuta():
    ir = IR(
        "1.0.0", "dc", "netlist", ("0", "a", "b", "c"),
        (
            Component.of("V1", "voltage_source_dc", ("a", "b"), Fraction(5), "V1"),
            Component.of("V2", "voltage_source_dc", ("b", "c"), Fraction(3), "V2"),
            Component.of("R1", "resistor", ("a", "0"), Fraction(10), "R1"),
            Component.of("R2", "resistor", ("c", "0"), Fraction(10), "R2"),
        ),
        (),
    )
    request = Request("q_c", "voltage", "R1")  # type: ignore[arg-type]
    mir = replace(ir, requests=(request,))
    assert nodale_disponibile(mir, "voltage") is False
    assert isinstance(pianifica(mir, request), Refusal)


def test_componente_non_supportato_rifiuta():
    ir, request = _terminale_input()
    with_cap = IR(
        "1.0.0", "dc", "netlist", ir.nodes,
        (*ir.components,
         Component.of("C1", "capacitor", ("b", "0"), Fraction(1), "C1")),
        ir.requests,
    )
    assert nodale_disponibile(with_cap, "current") is False
    assert isinstance(pianifica(with_cap, request), Refusal)


def test_target_assente_rifiuta():
    ir, _ = _terminale_input()
    ghost = Request("q_g", "current", "Rfantasma")  # type: ignore[arg-type]
    assert isinstance(pianifica(ir, ghost), Refusal)


def test_noti_contraddittori_rifiutano():
    s = stato(
        variables=(nv("0", "reference"), nv("k", "known_from_source", 5, "Vk")),
        equations=(kcl((1, "k"), rhs=7, focus="k"),),
    )
    with pytest.raises(ValueError, match="contraddittoria"):
        solve_derivation(s)


def test_noti_tautologia_accetta():
    s = stato(
        variables=(nv("0", "reference"), nv("k", "known_from_source", 5, "Vk")),
        equations=(kcl((1, "k"), rhs=5, focus="k"),),
    )
    sol = solve_derivation(s)
    assert sol.value_of(nv("k", "known_from_source", 5, "Vk").ref()) == Fraction(5)


def test_noti_senza_equazioni_accettano():
    s = stato(
        variables=(nv("0", "reference"), nv("k", "known_from_source", 5, "Vk")),
        equations=(),
    )
    sol = solve_derivation(s)
    assert sol.derivation_id == "D4"
    assert len(sol.values) == 2


def test_percorso_noto_con_incognite_rifiuta():
    s = stato(
        variables=(nv("0", "reference"), nv("a", "unknown")),
        equations=(),
    )
    with pytest.raises(ValueError, match="incognite presenti"):
        _solve_known_only(s)


def test_define_senza_nodi_oltre_riferimento_rifiuta():
    solo_massa = IR("1.0.0", "dc", "netlist", ("0",), (), ())
    _, d1 = applica_passo(
        "choose_reference", solo_massa, stato_iniziale("nodo-prova"), operands=())
    with pytest.raises(ValueError, match="niente da dichiarare"):
        applica_passo("define_nodal_unknowns", solo_massa, d1, operands=())
