"""P1-I: binding, tampering, proof_node e invarianti dei result type."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    NodalExecution,
    PlannedAction,
    TransformExecution,
    execute_plan,
    pianifica,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PARTITORE

F = Fraction
PROOF = conia("ir", 3, bytes(range(10)))


def _req(target: str, quantity: str = "current", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _semplice(request: Request | None = None) -> tuple[IR, Request]:
    if request is None:
        request = _req("R1", "current")
    ir = IR(
        "1.0.0", "dc", "netlist", ("0", "a"),
        (
            Component.of("I1", "current_source_dc", ("0", "a"), F(2), "I1"),
            Component.of("R1", "resistor", ("a", "0"), F(5), "R1"),
        ),
        (request,),
    )
    return ir, request


def _piano_nodale(ir: IR, request: Request):
    piano = pianifica(ir, request)
    assert not isinstance(piano, Refusal)
    assert piano.technique == "nodal_analysis"
    return piano


def test_p1_request_id_mismatch():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    altro = _req("R1", "current", rid="q-altro")
    with pytest.raises(ValueError, match="request_id"):
        execute_plan(ir, altro, piano, proof_node=PROOF)


def test_p2_request_non_in_ir():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    nudo = replace(ir, requests=())
    with pytest.raises(ValueError, match="non appartiene"):
        execute_plan(nudo, request, piano, proof_node=PROOF)


def test_p3_stesso_id_target_diverso():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    diverso = Request("q1", "current", "I1")
    with pytest.raises(ValueError, match="context mismatch"):
        execute_plan(ir, diverso, piano, proof_node=PROOF)


def test_p4_stesso_id_quantity_diversa():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    diverso = Request("q1", "voltage", "R1")
    with pytest.raises(ValueError, match="context mismatch"):
        execute_plan(ir, diverso, piano, proof_node=PROOF)


def test_p5_request_id_duplicato_fail_closed():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    doppio = replace(ir, requests=(request, Request("q1", "voltage", "I1")))
    with pytest.raises(ValueError, match="ambiguo"):
        execute_plan(doppio, request, piano, proof_node=PROOF)


def test_p6_technique_action_family_mismatch():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    rotto = replace(piano, actions=(PlannedAction("serie", ("I1", "R1")),))
    with pytest.raises(ValueError, match="technique/action mismatch"):
        execute_plan(ir, request, rotto, proof_node=PROOF)


def test_p7_operandi_analitici_malformati():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    rotto = replace(
        piano,
        actions=(
            PlannedAction("choose_reference", ()),
            PlannedAction("define_nodal_unknowns", ()),
            PlannedAction("write_kcl", ()),
        ),
    )
    with pytest.raises(ValueError, match="write_kcl"):
        execute_plan(ir, request, rotto, proof_node=PROOF)


def test_p8_azione_analitica_mancante_la_solve_rifiuta():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    incompleto = replace(piano, actions=piano.actions[:-1])
    with pytest.raises(ValueError, match="incompleta|incognita"):
        execute_plan(ir, request, incompleto, proof_node=PROOF)


def test_p9_azioni_riordinate_illegalmente():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    kcl = next(a for a in piano.actions if a.kind == "write_kcl")
    rotto = replace(
        piano,
        actions=(kcl, PlannedAction("choose_reference", ())),
    )
    with pytest.raises(ValueError):
        execute_plan(ir, request, rotto, proof_node=PROOF)


def test_i1_proof_node_ir_valido():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert esito.proof_node == PROOF


def test_i2_proof_node_lay_rifiutato():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    lay = conia("lay", 1, bytes(range(10)))
    with pytest.raises(ValueError, match="prefisso"):
        execute_plan(ir, request, piano, proof_node=lay)


def test_i3_proof_node_arbitrario():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    with pytest.raises(ValueError):
        execute_plan(ir, request, piano, proof_node="foo")


def test_i4_proof_node_ir_malformato():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    with pytest.raises(ValueError):
        execute_plan(ir, request, piano, proof_node="ir_not-a-ulid")


def test_plan_non_didacticplan():
    ir, request = _semplice()
    with pytest.raises(TypeError, match="DidacticPlan"):
        execute_plan(ir, request, {"technique": "nodal_analysis"}, proof_node=PROOF)


def _nodal_valido() -> NodalExecution:
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, NodalExecution)
    return esito


def test_r1_nodal_rifiuta_tecnica_non_nodale():
    base = _nodal_valido()
    transform_plan = replace(base.plan, technique="certified_transform_path")
    with pytest.raises(ValueError, match="nodal_analysis"):
        NodalExecution(
            base.proof_node, transform_plan, base.steps,
            base.derivation, base.solution, base.resolved,
        )


def test_r2_nodal_rifiuta_conteggio_passi():
    base = _nodal_valido()
    with pytest.raises(ValueError, match="passi"):
        NodalExecution(
            base.proof_node, base.plan, base.steps[:-1],
            base.derivation, base.solution, base.resolved,
        )


def test_r3_nodal_rifiuta_kind_mismatch():
    base = _nodal_valido()
    piano = replace(
        base.plan,
        actions=tuple(
            replace(a, kind="write_voltage_constraint") if i == 0 else a
            for i, a in enumerate(base.plan.actions)
        ),
    )
    with pytest.raises(ValueError, match="kind"):
        NodalExecution(
            base.proof_node, piano, base.steps,
            base.derivation, base.solution, base.resolved,
        )


def test_r4_nodal_rifiuta_catena_spezzata():
    base = _nodal_valido()
    rotto = list(base.steps)
    rotto[1] = replace(rotto[1], derivation_before="DX")
    with pytest.raises(ValueError, match="spezzata|D0"):
        NodalExecution(
            base.proof_node, base.plan, tuple(rotto),
            base.derivation, base.solution, base.resolved,
        )


def test_r5_nodal_rifiuta_derivation_id_finale():
    base = _nodal_valido()
    with pytest.raises(ValueError, match="derivation"):
        NodalExecution(
            base.proof_node, base.plan, base.steps,
            replace(base.derivation, identifier="DX"),
            base.solution, base.resolved,
        )


def test_r6_nodal_rifiuta_solution_mismatch():
    base = _nodal_valido()
    with pytest.raises(ValueError, match="solution"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, base.derivation,
            replace(base.solution, derivation_id="DX"),
            base.resolved,
        )


def test_r7_nodal_rifiuta_resolved_request_mismatch():
    base = _nodal_valido()
    with pytest.raises(ValueError, match="request_id"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, base.derivation,
            base.solution, replace(base.resolved, request_id="altro"),
        )


def _transform_valido() -> TransformExecution:
    request = _req("R2", "current")
    ir = replace(leggi(PARTITORE), requests=(request,))
    piano = pianifica(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    return esito


def test_r8_transform_rifiuta_tecnica_non_transform():
    base = _transform_valido()
    piano = replace(base.plan, technique="nodal_analysis")
    with pytest.raises(ValueError, match="certified_transform_path"):
        TransformExecution(
            base.proof_node, piano, base.before, base.after, base.results,
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )


def test_r9_transform_rifiuta_zero_results():
    base = _transform_valido()
    with pytest.raises(ValueError, match="senza risultati"):
        TransformExecution(
            base.proof_node, base.plan, base.before, base.after, (),
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )


def test_r10_transform_rifiuta_conteggio_results():
    base = _transform_valido()
    with pytest.raises(ValueError, match="risultati"):
        TransformExecution(
            base.proof_node, base.plan, base.before, base.after,
            base.results + base.results,
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )


def test_execution_conserva_il_piano():
    ir, request = _semplice()
    piano = _piano_nodale(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert esito.plan == piano


def test_nodal_type_guards():
    base = _nodal_valido()
    with pytest.raises(TypeError, match="DidacticPlan"):
        NodalExecution(
            base.proof_node, object(), base.steps,
            base.derivation, base.solution, base.resolved,
        )
    with pytest.raises(ValueError, match="senza passi"):
        NodalExecution(
            base.proof_node, base.plan, (),
            base.derivation, base.solution, base.resolved,
        )
    with pytest.raises(TypeError, match="AnalyticalStep"):
        NodalExecution(
            base.proof_node, base.plan, ("x",) * len(base.plan.actions),
            base.derivation, base.solution, base.resolved,
        )
    rotto = list(base.steps)
    rotto[0] = replace(rotto[0], derivation_before="DX")
    with pytest.raises(ValueError, match="D0"):
        NodalExecution(
            base.proof_node, base.plan, tuple(rotto),
            base.derivation, base.solution, base.resolved,
        )
    with pytest.raises(TypeError, match="DerivationState"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, object(),
            base.solution, base.resolved,
        )
    with pytest.raises(ValueError, match="proof_node"):
        NodalExecution(
            base.proof_node, base.plan, base.steps,
            replace(base.derivation, proof_node="altro"),
            base.solution, base.resolved,
        )
    with pytest.raises(TypeError, match="DerivationSolution"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, base.derivation,
            object(), base.resolved,
        )
    with pytest.raises(TypeError, match="ResolvedQuantity"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, base.derivation,
            base.solution, object(),
        )
    with pytest.raises(ValueError, match="resolved.derivation_id"):
        NodalExecution(
            base.proof_node, base.plan, base.steps, base.derivation,
            base.solution, replace(base.resolved, derivation_id="DX"),
        )


def test_transform_type_guards():
    base = _transform_valido()
    with pytest.raises(TypeError, match="DidacticPlan"):
        TransformExecution(
            base.proof_node, object(), base.before, base.after, base.results,
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )
    with pytest.raises(TypeError, match="before"):
        TransformExecution(
            base.proof_node, base.plan, object(), base.after, base.results,
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )
    with pytest.raises(TypeError, match="after"):
        TransformExecution(
            base.proof_node, base.plan, base.before, object(), base.results,
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )
    with pytest.raises(TypeError, match="TransformResult"):
        TransformExecution(
            base.proof_node, base.plan, base.before, base.after, ("x",),
            base.observation, base.observation_effect, base.successor_request,
            base.request_lineage,
        )


def test_esecutore_contraddizioni_dopo_applica(monkeypatch):
    from kirchhoff.domain.didactic.analytical import applica_passo as reale
    from kirchhoff.domain.didactic import execute as modulo

    ir, request = _semplice()
    piano = _piano_nodale(ir, request)

    def _kind(*a, **k):
        step, state = reale(*a, **k)
        return replace(step, kind="write_kcl"), state

    monkeypatch.setattr(modulo, "applica_passo", _kind)
    with pytest.raises(ValueError, match="passo"):
        execute_plan(ir, request, piano, proof_node=PROOF)

    def _anchor(*a, **k):
        step, state = reale(*a, **k)
        return replace(step, proof_node="x"), replace(state, proof_node="x")

    monkeypatch.setattr(modulo, "applica_passo", _anchor)
    with pytest.raises(ValueError, match="proof_node"):
        execute_plan(ir, request, piano, proof_node=PROOF)

    def _before(*a, **k):
        step, state = reale(*a, **k)
        return replace(step, derivation_before="DX"), state

    monkeypatch.setattr(modulo, "applica_passo", _before)
    with pytest.raises(ValueError, match="derivation_before"):
        execute_plan(ir, request, piano, proof_node=PROOF)

    def _after(*a, **k):
        step, state = reale(*a, **k)
        return replace(step, derivation_after="DX"), state

    monkeypatch.setattr(modulo, "applica_passo", _after)
    with pytest.raises(ValueError, match="derivation_after"):
        execute_plan(ir, request, piano, proof_node=PROOF)


def test_t8_transform_refusal_propagato(monkeypatch):
    from kirchhoff.domain.didactic import execute as modulo

    request = _req("R2", "current")
    ir = replace(leggi(PARTITORE), requests=(request,))
    piano = pianifica(ir, request)
    rifiuto = Refusal("empty_boundary", "R1", "component", "confine vuoto")
    monkeypatch.setattr(modulo, "transform", lambda *a, **k: rifiuto)
    assert execute_plan(ir, request, piano, proof_node=PROOF) is rifiuto
