"""P1-L: orchestrazione deterministica di piani didattici mono-passo."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import kirchhoff.domain.didactic.orchestrate as orchestrate
from kirchhoff.domain.didactic import DidacticPlan, PlanReason, PlannedAction, pianifica
from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.truthfulness import CertifiedNodalExecution
from kirchhoff.pipeline.netlist import leggi


SERIE = """\
V1 c 0 12 volt
R1 c a 100 ohm
R2 a b 220 ohm
R3 b 0 330 ohm
I1 0 b 1 ampere
"""
PARALLELO = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 b a 300 ohm
R3 a 0 330 ohm
I1 0 a 1 ampere
"""
MULTI_SERIE = """\
V1 d 0 12 volt
R1 d a 100 ohm
R2 a b 220 ohm
R3 b c 330 ohm
R4 c 0 470 ohm
I1 0 c 1 ampere
"""
MULTI_PARALLELO = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 b a 220 ohm
R3 b a 330 ohm
R4 a 0 470 ohm
I1 0 a 1 ampere
"""
MISTO = """\
V1 d 0 12 volt
R1 d a 100 ohm
R2 a b 220 ohm
R3 d b 330 ohm
R4 b 0 470 ohm
I1 0 b 1 ampere
"""


def _states(number: int, *, start: int = 100) -> tuple[str, ...]:
    return tuple(
        conia("ir", start + index, bytes(range(index, index + 10)))
        for index in range(number)
    )


def _input(netlist: str, target: str, quantity: str, *, request_id: str = "q1"):
    request = Request(request_id, quantity, target)  # type: ignore[arg-type]
    return replace(leggi(netlist), requests=(request,)), request


def _series_run() -> CertifiedDidacticRun:
    ir, request = _input(SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(run, CertifiedDidacticRun)
    return run


def _zero_run() -> CertifiedDidacticRun:
    ir, request = _input("I1 0 a 2 ampere\nR1 a 0 5 ohm\n", "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(1))
    assert isinstance(run, CertifiedDidacticRun)
    return run


def test_zero_transform_esegue_nodale_e_certifica_il_claim_finale():
    ir, request = _input("I1 0 a 2 ampere\nR1 a 0 5 ohm\n", "R1", "current")
    run = orchestrate_didactic_run(
        ir,
        request,
        state_ids=_states(1),
    )

    assert isinstance(run, CertifiedDidacticRun)
    assert isinstance(run.final_execution, CertifiedNodalExecution)
    assert run.transform_executions == ()
    assert run.final_execution.claim.status == "VERIFIED"


@pytest.mark.parametrize(
    ("netlist", "quantity", "operation"),
    ((SERIE, "current", "serie"), (PARALLELO, "voltage", "parallelo")),
)
def test_una_riduzione_permessa_e_poi_nodale(netlist, quantity, operation):
    ir, request = _input(netlist, "R1", quantity)
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))

    assert isinstance(run, CertifiedDidacticRun)
    assert [step.plan.actions[0].kind for step in run.transform_executions] == [operation]
    assert run.final_request.target == run.transform_executions[-1].request_lineage.target_after
    assert run.final_execution.claim.subject_ids == (request.id, run.final_request.target)


@pytest.mark.parametrize(
    ("netlist", "quantity", "operations"),
    (
        (MULTI_SERIE, "current", ["serie", "serie"]),
        (MULTI_PARALLELO, "voltage", ["parallelo", "parallelo"]),
        (MISTO, "voltage", ["serie", "parallelo"]),
    ),
)
def test_ripianifica_dopo_ogni_trasformazione_certificata(netlist, quantity, operations):
    ir, request = _input(netlist, "R1" if netlist != MISTO else "V1", quantity)
    run = orchestrate_didactic_run(ir, request, state_ids=_states(len(operations) + 1))

    assert isinstance(run, CertifiedDidacticRun)
    assert [step.plan.actions[0].kind for step in run.transform_executions] == operations
    assert run.final_execution.claim.status == "VERIFIED"
    assert run.final_request.target in {component.id for component in run.final_ir.components}
    assert run.final_execution.execution.proof_node == _states(len(operations) + 1)[-1]


def test_identity_target_resta_immutabile_attraverso_una_trasformazione():
    ir, request = _input(SERIE, "V1", "voltage")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))

    step = run.transform_executions[0]
    assert step.observation_effect.kind == "identity"
    assert step.successor_request is request
    assert run.final_request is request
    assert run.final_execution.claim.subject_ids == (request.id, "V1")


def test_lineage_preserva_request_id_quantity_target_chain_e_oggetto_originale():
    ir, request = _input(MULTI_SERIE, "R1", "current")
    original = (request.id, request.quantity, request.target)
    run = orchestrate_didactic_run(ir, request, state_ids=_states(3))

    assert (request.id, request.quantity, request.target) == original
    assert run.original_request is request
    assert run.final_request.id == request.id
    assert run.final_request.quantity == request.quantity
    targets = [request.target]
    for step in run.transform_executions:
        assert step.observation.request_id == request.id
        assert step.observation.quantity == request.quantity
        assert step.request_lineage.request_id == request.id
        assert step.request_lineage.quantity == request.quantity
        assert step.request_lineage.target_before == targets[-1]
        targets.append(step.request_lineage.target_after)
    assert targets[-1] == run.final_request.target


def test_claim_finale_e_solo_quello_p1k_e_non_e_costruito_a_mano():
    ir, request = _input(SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))

    claim = run.final_execution.claim
    assert claim.claim_type == "resolved_quantity"
    assert claim.status == "VERIFIED"
    assert claim.subject_ids == (run.final_request.id, run.final_request.target)
    assert claim.evidence_ids == tuple(
        step.derivation_after for step in run.final_execution.execution.steps)
    assert "Claim(" not in Path(orchestrate.__file__).read_text()
    assert "class Claim" not in Path(orchestrate.__file__).read_text()


def test_refusal_del_planner_si_propaga(monkeypatch):
    ir, request = _input(SERIE, "R1", "current")
    refusal = Refusal("unsolvable", request.id, "request", "rifiuto planner")
    monkeypatch.setattr(orchestrate, "pianifica", lambda *_: refusal)

    assert orchestrate_didactic_run(ir, request, state_ids=_states(1)) is refusal


def test_refusal_della_trasformazione_si_propaga(monkeypatch):
    ir, request = _input(SERIE, "R1", "current")
    refusal = Refusal("unsolvable", request.id, "request", "rifiuto trasformazione")
    original = orchestrate.execute_plan

    def refuse_transform(*args, **kwargs):
        if args[2].technique == "certified_transform_path":
            return refusal
        return original(*args, **kwargs)

    monkeypatch.setattr(orchestrate, "execute_plan", refuse_transform)
    assert orchestrate_didactic_run(ir, request, state_ids=_states(2)) is refusal


def test_refusal_della_certificazione_finale_si_propaga(monkeypatch):
    ir, request = _input("I1 0 a 2 ampere\nR1 a 0 5 ohm\n", "R1", "current")
    refusal = Refusal("path_disagreement", "R1", "component", "gate rifiutato")
    monkeypatch.setattr(orchestrate, "certify_execution", lambda *_: refusal)

    assert orchestrate_didactic_run(ir, request, state_ids=_states(1)) is refusal


def test_blocked_selezionato_dal_planner_e_violazione_interna(monkeypatch):
    ir, request = _input(SERIE, "R1", "voltage")
    allowed = pianifica(replace(ir, requests=(Request("q1", "current", "R1"),)), Request("q1", "current", "R1"))
    assert isinstance(allowed, DidacticPlan)
    forced = replace(allowed, request_id=request.id)
    monkeypatch.setattr(orchestrate, "pianifica", lambda *_: forced)

    with pytest.raises(RuntimeError, match="blocked"):
        orchestrate_didactic_run(ir, request, state_ids=_states(2))


@pytest.mark.parametrize(
    ("field", "replacement", "match"),
    (
        ("successor_request", lambda out: Request("q_altro", out.successor_request.quantity, out.successor_request.target), "successor_request.id"),
        ("successor_request", lambda out: Request(out.successor_request.id, "voltage", out.successor_request.target), "successor_request.quantity"),
        ("successor_request", lambda out: Request(out.successor_request.id, out.successor_request.quantity, "R3"), "successor_request.target"),
        ("before", lambda out: out.after, "before non coincide"),
        ("after", lambda out: out.before, "non riduce"),
    ),
)
def test_corruzioni_della_traccia_sono_rifiutate(monkeypatch, field, replacement, match):
    ir, request = _input(SERIE, "R1", "current")
    original = orchestrate.execute_plan

    def corrupt(*args, **kwargs):
        outcome = original(*args, **kwargs)
        if outcome.__class__.__name__ == "TransformExecution":
            object.__setattr__(outcome, field, replacement(outcome))
        return outcome

    monkeypatch.setattr(orchestrate, "execute_plan", corrupt)
    with pytest.raises(ValueError, match=match):
        orchestrate_didactic_run(ir, request, state_ids=_states(2))


def test_state_id_supply_e_esplicita_unica_ed_esatta():
    ir, request = _input(SERIE, "R1", "current")
    with pytest.raises(TypeError, match="tuple"):
        orchestrate_didactic_run(ir, request, state_ids=list(_states(2)))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="identificatore"):
        orchestrate_didactic_run(ir, request, state_ids=("ir_non-valido",))
    with pytest.raises(ValueError, match="riusare"):
        orchestrate_didactic_run(ir, request, state_ids=(_states(1)[0],) * 2)
    with pytest.raises(ValueError, match="insufficienti"):
        orchestrate_didactic_run(ir, request, state_ids=_states(1))
    with pytest.raises(ValueError, match="eccedenti"):
        orchestrate_didactic_run(ir, request, state_ids=_states(3))


def test_il_risultato_ispezionabile_non_accetta_state_id_riusati():
    ir, request = _input(SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    object.__setattr__(run.final_execution.execution, "proof_node", run.transform_executions[0].proof_node)

    with pytest.raises(ValueError, match="riusa"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


@pytest.mark.parametrize(
    "field",
    ("initial_ir", "original_request", "final_ir", "final_request", "final_execution"),
)
def test_il_risultato_ispezionabile_valida_i_tipi_dei_sei_campi(field):
    run = _series_run()

    with pytest.raises(TypeError):
        replace(run, **{field: object()})


def test_il_risultato_ispezionabile_valida_final_ir_e_final_request():
    run = _series_run()
    with pytest.raises(ValueError, match="final_ir"):
        replace(run, final_ir=run.initial_ir)
    with pytest.raises(ValueError, match="final_request"):
        replace(run, final_request=run.original_request)


@pytest.mark.parametrize(
    ("mutate", "match"),
    (
        (lambda run: object.__setattr__(run.final_execution.execution.plan, "request_id", "q_altro"), "piano nodale"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "request_id", "q_altro"), "quantita' risolta"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "target", "I1"), "final_request.target"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "quantity", "voltage"), "final_request.quantity"),
    ),
)
def test_il_risultato_ispezionabile_valida_il_legame_finale_p1k(mutate, match):
    run = _zero_run()
    mutate(run)

    with pytest.raises(ValueError, match=match):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_orchestratore_valida_gli_input_e_il_legame_request_ir():
    ir, request = _input(SERIE, "R1", "current")
    with pytest.raises(TypeError, match="initial_ir"):
        orchestrate_didactic_run(object(), request, state_ids=_states(1))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="original_request"):
        orchestrate_didactic_run(ir, object(), state_ids=_states(1))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non puo' essere vuota"):
        orchestrate_didactic_run(ir, request, state_ids=())
    with pytest.raises(ValueError, match="esattamente una volta"):
        orchestrate_didactic_run(replace(ir, requests=()), request, state_ids=_states(2))
    with pytest.raises(ValueError, match="non coerente"):
        orchestrate_didactic_run(
            replace(ir, requests=(Request(request.id, "voltage", request.target),)),
            request,
            state_ids=_states(2),
        )


def test_il_piano_con_tecnica_impossibile_fallisce_rumorosamente(monkeypatch):
    ir, request = _input(SERIE, "R1", "current")
    monkeypatch.setattr(orchestrate, "pianifica", lambda *_: SimpleNamespace(technique="impossibile"))

    with pytest.raises(RuntimeError, match="impossibile"):
        orchestrate_didactic_run(ir, request, state_ids=_states(1))


def test_esiti_esecutore_non_coerenti_col_piano_falliscono_rumorosamente(monkeypatch):
    ir, request = _input(SERIE, "R1", "current")
    zero = _zero_run()
    wrong_nodal = zero.final_execution.execution
    wrong_transform = _series_run().transform_executions[0]
    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: wrong_nodal)
    with pytest.raises(RuntimeError, match="TransformExecution"):
        orchestrate_didactic_run(ir, request, state_ids=_states(2))

    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: wrong_transform)
    with pytest.raises(RuntimeError, match="NodalExecution"):
        orchestrate_didactic_run(
            zero.initial_ir,
            zero.original_request,
            state_ids=_states(1),
        )


def test_refusal_dell_esecutore_nodale_si_propaga(monkeypatch):
    zero = _zero_run()
    refusal = Refusal("unsolvable", "q1", "request", "rifiuto nodale")
    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: refusal)

    assert orchestrate_didactic_run(
        zero.initial_ir,
        zero.original_request,
        state_ids=_states(1),
    ) is refusal


@pytest.mark.parametrize(
    ("path", "value", "match"),
    (
        ("observation.request_id", "q_altro", "observation.request_id"),
        ("observation.quantity", "voltage", "observation.quantity"),
        ("lineage.request_id", "q_altro", "lineage.request_id"),
        ("lineage.quantity", "voltage", "lineage.quantity"),
        ("lineage.target_before", "R3", "lineage.target_before"),
    ),
)
def test_guardie_lineage_rifiutano_i_campi_corotti(path, value, match):
    run = _series_run()
    execution = run.transform_executions[0]
    owner, field = path.split(".")
    target = execution.observation if owner == "observation" else execution.request_lineage
    object.__setattr__(target, field, value)

    with pytest.raises(ValueError, match=match):
        orchestrate._validate_transform_continuity(
            execution, run.initial_ir, run.original_request, 0)


def test_guardia_rifiuta_successore_mancante_e_identity_che_cambia_request():
    run = _series_run()
    execution = run.transform_executions[0]
    object.__setattr__(execution, "successor_request", None)
    with pytest.raises(RuntimeError, match="senza Request"):
        orchestrate._validate_transform_continuity(
            execution, run.initial_ir, run.original_request, 0)

    ir, request = _input(SERIE, "V1", "voltage")
    identity = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(identity, CertifiedDidacticRun)
    step = identity.transform_executions[0]
    successor = Request(request.id, request.quantity, "R3")
    object.__setattr__(step, "successor_request", successor)
    object.__setattr__(step.request_lineage, "target_after", successor.target)
    with pytest.raises(ValueError, match="identity"):
        orchestrate._validate_transform_continuity(step, ir, request, 0)


def test_binding_del_successore_rifiuta_un_omonimo_non_certificato():
    run = _series_run()
    step = run.transform_executions[0]
    assert step.successor_request is not None
    corrupt_after = replace(
        step.after,
        requests=(Request(step.successor_request.id, step.successor_request.quantity, "R3"),),
    )

    with pytest.raises(ValueError, match="omonima"):
        orchestrate._bind_successor_request(corrupt_after, step.successor_request)


def test_stessi_input_e_state_id_danno_una_run_strutturalmente_identica():
    ir, request = _input(MULTI_PARALLELO, "R1", "voltage")
    states = _states(3)

    assert orchestrate_didactic_run(ir, request, state_ids=states) == orchestrate_didactic_run(
        ir, request, state_ids=states)


def test_confini_architetturali_restano_intatti_e_senza_ricerca_o_cas():
    root = Path(__file__).resolve().parents[1]
    execute = (root / "src/kirchhoff/domain/didactic/execute.py").read_text()
    truthfulness = (root / "src/kirchhoff/domain/truthfulness.py").read_text()
    orchestration = Path(orchestrate.__file__).read_text()
    execute_tree = ast.parse(execute)
    truthfulness_tree = ast.parse(truthfulness)

    imported = {
        node.module
        for node in ast.walk(execute_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any("planner" in module for module in imported)
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "pianifica"
        for node in ast.walk(execute_tree)
    )
    assert not any(
        isinstance(node, ast.ImportFrom) and node.module and "planner" in node.module
        for node in ast.walk(truthfulness_tree)
    )
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "pianifica"
        for node in ast.walk(truthfulness_tree)
    )
    assert all(term not in orchestration for term in (
        "StrategyScore(", "beam_search(", "graph_search(", "import lcapy", "from lcapy",
    ))
