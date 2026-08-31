"""P1-I: replay esatto di un DidacticPlan nodale."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    NodalExecution,
    PlannedAction,
    execute_plan,
    pianifica,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.domain.refusal import Refusal

F = Fraction
PROOF = conia("ir", 1, bytes(range(10)))


def _req(target: str, quantity: str = "voltage", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _ir(nodes, comps, request: Request) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), (request,))


def _semplice() -> tuple[IR, Request]:
    request = _req("R1", "current")
    ir = _ir(("0", "a"), (
        Component.of("I1", "current_source_dc", ("0", "a"), F(2), "I1"),
        Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
    ), request)
    return ir, request


def _due_ordinari() -> tuple[IR, Request]:
    request = _req("R1", "voltage")
    ir = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("R3", "resistor", ("a", "b"), F(5), "R3"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
        Component.of("I2", "current_source_dc", ("b", "0"), F(1), "I2"),
    ), request)
    return ir, request


def _due_supernodi() -> tuple[IR, Request]:
    request = _req("R1", "voltage")
    ir = _ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(6), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("V2", "voltage_source_dc", ("c", "d"), F(3), "V2"),
        Component.of("R3", "resistor", ("c", "0"), F(1), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(1), "R4"),
    ), request)
    return ir, request


def _noto_e_ordinario() -> tuple[IR, Request]:
    request = _req("R2", "voltage")
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(4), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(12), "R2"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
    ), request)
    return ir, request


def _ponte_v1_corrente() -> tuple[IR, Request]:
    request = _req("V1", "current")
    ir = _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("c", "a"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("a", "0"), F(30), "R3"),
        Component.of("R4", "resistor", ("b", "0"), F(40), "R4"),
        Component.of("Rg", "resistor", ("a", "b"), F(50), "Rg"),
    ), request)
    return ir, request


def _flottante_invertito() -> tuple[IR, Request]:
    request = _req("V1", "voltage")
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "a"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ), request)
    return ir, request


def _esegui(ir: IR, request: Request) -> NodalExecution:
    piano = pianifica(ir, request)
    assert not isinstance(piano, Refusal)
    assert piano.technique == "nodal_analysis"
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, NodalExecution)
    return esito


def test_n1_semplice_end_to_end():
    ir, request = _semplice()
    execution = _esegui(ir, request)
    piano = execution.plan
    assert len(execution.steps) == len(piano.actions)
    assert execution.resolved.value.amount == F(2)
    assert execution.resolved.value.unit == "ampere"
    assert execution.resolved.request_id == request.id
    assert execution.resolved.orientation == ("a", "0")


def test_n2_ordine_azioni_preservato():
    ir, request = _due_ordinari()
    execution = _esegui(ir, request)
    assert [s.kind for s in execution.steps] == [a.kind for a in execution.plan.actions]
    for passo, azione in zip(execution.steps, execution.plan.actions):
        assert passo.kind == azione.kind
        if azione.operands:
            assert passo.focused_entities[0] == azione.operands[0]


def test_n3_due_supernodi_ordine_del_piano():
    ir, request = _due_supernodi()
    execution = _esegui(ir, request)
    azioni = list(execution.plan.actions)
    assert [a.kind for a in azioni] == [
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_voltage_constraint",
        "write_kcl",
        "write_voltage_constraint",
    ]
    assert azioni[2].operands[0] == "V1"
    assert azioni[3].operands == ("V1",)
    assert azioni[4].operands[0] == "V2"
    assert azioni[5].operands == ("V2",)
    assert [s.kind for s in execution.steps] == [a.kind for a in azioni]
    assert execution.steps[2].focused_entities[0] == "V1"
    assert execution.steps[4].focused_entities[0] == "V2"


def test_n4_secondo_supernodo_non_riesegue_il_primo():
    ir, request = _due_supernodi()
    piano = pianifica(ir, request)
    assert piano.technique == "nodal_analysis"
    v1 = [a for a in piano.actions if a.kind == "write_kcl" and a.operands[0] == "V1"]
    v2 = [a for a in piano.actions if a.kind == "write_kcl" and a.operands[0] == "V2"]
    c1 = [a for a in piano.actions if a.kind == "write_voltage_constraint" and a.operands == ("V1",)]
    c2 = [a for a in piano.actions if a.kind == "write_voltage_constraint" and a.operands == ("V2",)]
    invertito = replace(
        piano,
        actions=(
            piano.actions[0],
            piano.actions[1],
            v2[0],
            c2[0],
            v1[0],
            c1[0],
        ),
    )
    execution = execute_plan(ir, request, invertito, proof_node=PROOF)
    assert isinstance(execution, NodalExecution)
    assert execution.steps[2].focused_entities[0] == "V2"
    assert execution.steps[2].focused_entities[0] != "V1"
    assert execution.steps[4].focused_entities[0] == "V1"


def test_n5_request_corrente_resistore():
    ir, request = _semplice()
    execution = _esegui(ir, request)
    assert execution.resolved.quantity == "current"
    assert execution.resolved.target == "R1"
    assert execution.resolved.value.amount == F(2)


def test_n6_corrente_generatore_tensione_via_executor():
    ir, request = _ponte_v1_corrente()
    execution = _esegui(ir, request)
    assert execution.resolved.quantity == "current"
    assert execution.resolved.target == "V1"
    assert execution.resolved.orientation == ("c", "0")
    assert execution.resolved.value.unit == "ampere"
    assert execution.resolved.value.amount < 0


def test_n7_sorgente_invertita_mantiene_orientamento():
    ir, request = _flottante_invertito()
    execution = _esegui(ir, request)
    assert execution.resolved.orientation == ("b", "a")
    assert execution.resolved.value.amount == F(5)
    assert execution.resolved.value.unit == "volt"


def test_n8_nodo_noto_catena_completa():
    ir, request = _noto_e_ordinario()
    execution = _esegui(ir, request)
    kinds = [a.kind for a in execution.plan.actions]
    assert kinds[0] == "choose_reference"
    assert "define_nodal_unknowns" in kinds
    assert "write_kcl" in kinds
    assert execution.derivation.identifier == execution.steps[-1].derivation_after
    assert execution.solution.derivation_id == execution.derivation.identifier
    assert execution.resolved.request_id == request.id
    assert execution.resolved.value.amount == F(6)
    assert execution.resolved.orientation == ("a", "0")


def test_d1_determinismo_strutturale():
    ir, request = _semplice()
    piano = pianifica(ir, request)
    a = execute_plan(ir, request, piano, proof_node=PROOF)
    b = execute_plan(ir, request, piano, proof_node=PROOF)
    assert a == b


def test_immutabilita_ingressi():
    ir, request = _semplice()
    piano = pianifica(ir, request)
    nodi, componenti, richieste = ir.nodes, ir.components, ir.requests
    azioni = piano.actions
    execute_plan(ir, request, piano, proof_node=PROOF)
    assert ir.nodes is nodi
    assert ir.components is componenti
    assert ir.requests is richieste
    assert piano.actions is azioni
