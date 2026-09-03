"""P1-L: orchestrazione deterministica di piani didattici mono-passo."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import kirchhoff.domain.didactic as didactic
import kirchhoff.domain.didactic.orchestrate as orchestrate
from kirchhoff.domain.didactic import DidacticPlan, PlanReason, PlannedAction, pianifica
from kirchhoff.domain.didactic.kinds import PLAN_SCHEMA_VERSION, PROFILE
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.didactic.execute import TransformExecution, execute_plan
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


def _traccia_valida_ma_non_scelta_dal_planner() -> CertifiedDidacticRun:
    ir, request = _input(MULTI_SERIE, "R1", "current")
    selected = pianifica(ir, request)
    assert isinstance(selected, DidacticPlan)
    alternative = replace(
        selected,
        actions=(PlannedAction("serie", ("R2", "R3")),),
    )
    first = execute_plan(ir, request, alternative, proof_node=_states(1, start=500)[0])
    assert isinstance(first, TransformExecution)
    assert first.plan != selected
    assert first.successor_request is not None

    next_ir = orchestrate._bind_successor_request(first.after, first.successor_request)
    continuation = orchestrate_didactic_run(
        next_ir,
        first.successor_request,
        state_ids=_states(2, start=600),
    )
    assert isinstance(continuation, CertifiedDidacticRun)
    return CertifiedDidacticRun(
        ir,
        request,
        (first, *continuation.transform_executions),
        continuation.final_ir,
        continuation.final_request,
        continuation.final_execution,
    )


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


def test_api_pubblica_didactic_esporta_solo_l_orchestrazione_pubblica():
    from kirchhoff.domain.didactic import (
        CertifiedDidacticRun as imported_run,
        orchestrate_didactic_run as imported_orchestrate,
    )

    assert imported_run is CertifiedDidacticRun
    assert imported_orchestrate is orchestrate_didactic_run
    assert "CertifiedDidacticRun" in didactic.__all__
    assert "orchestrate_didactic_run" in didactic.__all__
    assert "_bind_successor_request" not in didactic.__all__
    assert "_validate_transform_continuity" not in didactic.__all__
    assert "_validate_state_ids" not in didactic.__all__


def test_run_rifiuta_certificazione_finale_valida_ma_di_un_altro_circuito():
    ir_a, request_a = _input(
        "I1 0 a 2 ampere\nR1 a 0 5 ohm\n", "R1", "current")
    ir_b, request_b = _input(
        "I1 0 a 3 ampere\nR1 a 0 5 ohm\n", "R1", "current")
    run_a = orchestrate_didactic_run(ir_a, request_a, state_ids=_states(1))
    run_b = orchestrate_didactic_run(ir_b, request_b, state_ids=_states(1, start=200))

    assert isinstance(run_a, CertifiedDidacticRun)
    assert isinstance(run_b, CertifiedDidacticRun)
    assert run_a.final_execution.execution.resolved.value != run_b.final_execution.execution.resolved.value

    with pytest.raises(ValueError, match="certificazione finale"):
        CertifiedDidacticRun(
            ir_a,
            request_a,
            (),
            ir_a,
            request_a,
            run_b.final_execution,
        )


def test_run_rifiuta_un_percorso_valido_ma_non_selezionato_dal_planner():
    with pytest.raises(ValueError, match="piano pianificato"):
        _traccia_valida_ma_non_scelta_dal_planner()


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
        ("successor_request", lambda out: Request("q0", out.successor_request.quantity, out.successor_request.target), "successor_request.id"),
        ("successor_request", lambda out: Request(out.successor_request.id, "voltage", out.successor_request.target), "successor_request.quantity"),
        ("successor_request", lambda out: Request(out.successor_request.id, out.successor_request.quantity, "A"), "successor_request.target"),
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


def test_state_id_supply_rifiuta_tipo_invalidi_duplicati_ed_esaurimento():
    ir, request = _input(SERIE, "R1", "current")
    with pytest.raises(TypeError, match="tuple"):
        orchestrate_didactic_run(ir, request, state_ids=list(_states(2)))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="identificatore"):
        orchestrate_didactic_run(ir, request, state_ids=("ir_non-valido",))
    with pytest.raises(ValueError, match="riusare"):
        orchestrate_didactic_run(ir, request, state_ids=(_states(1)[0],) * 2)
    with pytest.raises(ValueError, match="insufficienti"):
        orchestrate_didactic_run(ir, request, state_ids=_states(1))


def test_state_id_supply_accetta_un_limite_superiore_e_espone_solo_il_prefisso_usato():
    ir, request = _input(SERIE, "R1", "current")
    exact = _states(2)
    upper_bound = _states(len(ir.components), start=100)

    exact_run = orchestrate_didactic_run(ir, request, state_ids=exact)
    upper_bound_run = orchestrate_didactic_run(ir, request, state_ids=upper_bound)

    assert isinstance(exact_run, CertifiedDidacticRun)
    assert isinstance(upper_bound_run, CertifiedDidacticRun)
    assert exact_run.state_ids == exact
    assert upper_bound_run.state_ids == upper_bound[:2]
    assert upper_bound_run.transform_executions[0].proof_node == upper_bound[0]
    assert upper_bound_run.final_execution.execution.proof_node == upper_bound[1]


def test_state_id_supply_valida_anche_il_suffisso_non_consumato():
    ir, request = _input(SERIE, "R1", "current")
    exact = _states(2)

    with pytest.raises(ValueError, match="riusare"):
        orchestrate_didactic_run(ir, request, state_ids=(*exact, exact[0]))
    with pytest.raises(ValueError, match="identificatore"):
        orchestrate_didactic_run(ir, request, state_ids=(*exact, "ir_non-valido"))


def test_state_id_non_consumati_non_cambiano_la_run_deterministica():
    ir, request = _input(MULTI_PARALLELO, "R1", "voltage")
    consumed = _states(3, start=800)
    first_supply = (*consumed, *_states(2, start=900))
    second_supply = (*consumed, *_states(2, start=1000))

    first = orchestrate_didactic_run(ir, request, state_ids=first_supply)
    second = orchestrate_didactic_run(ir, request, state_ids=second_supply)

    assert isinstance(first, CertifiedDidacticRun)
    assert first == second
    assert first.state_ids == consumed


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


def test_il_risultato_ispezionabile_rifiuta_un_passo_non_transform_execution():
    run = _series_run()

    with pytest.raises(TypeError, match="TransformExecution"):
        replace(run, transform_executions=(object(),))


@pytest.mark.parametrize(
    ("mutate", "match"),
    (
        (lambda run: object.__setattr__(run.final_execution.execution.plan, "request_id", "q0"), "piano nodale"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "request_id", "q0"), "quantita' risolta"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "target", "z_target"), "final_request.target"),
        (lambda run: object.__setattr__(run.final_execution.execution.resolved, "quantity", "amperes"), "final_request.quantity"),
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


def test_il_risultato_ispezionabile_rifiuta_una_certificazione_senza_nodale():
    run = _zero_run()
    object.__setattr__(run.final_execution, "execution", object())

    with pytest.raises(ValueError, match="senza NodalExecution"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_il_risultato_ispezionabile_rifiuta_un_replay_finale_non_nodale(monkeypatch):
    run = _zero_run()
    wrong_execution = _series_run().transform_executions[0]
    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: wrong_execution)

    with pytest.raises(ValueError, match="esecuzione nodale non riproducibile"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_il_risultato_ispezionabile_rifiuta_una_ricertificazione_finale_rifiutata(monkeypatch):
    run = _zero_run()
    refusal = Refusal("path_disagreement", "R1", "component", "gate rifiutato")
    monkeypatch.setattr(orchestrate, "certify_execution", lambda *_: refusal)

    with pytest.raises(ValueError, match="certificazione finale rifiutata"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_il_risultato_ispezionabile_rifiuta_una_ricertificazione_diversa(monkeypatch):
    run = _zero_run()
    other = orchestrate_didactic_run(
        *_input("I1 0 a 3 ampere\nR1 a 0 5 ohm\n", "R1", "current"),
        state_ids=_states(1, start=250),
    )
    assert isinstance(other, CertifiedDidacticRun)
    monkeypatch.setattr(orchestrate, "certify_execution", lambda *_: other.final_execution)

    with pytest.raises(ValueError, match="certificazione finale non corrisponde"):
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
        ("observation.request_id", "q0", "observation.request_id"),
        ("observation.quantity", "amperes", "observation.quantity"),
        ("lineage.request_id", "q0", "lineage.request_id"),
        ("lineage.quantity", "amperes", "lineage.quantity"),
        ("lineage.target_before", "A", "lineage.target_before"),
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


def test_guardia_successore_rifiuta_una_quantita_lessicograficamente_minore():
    """Falsifica `!= -> >` senza costruire una Request non valida pubblicamente."""
    run = _series_run()
    execution = run.transform_executions[0]
    assert execution.successor_request is not None
    object.__setattr__(execution.successor_request, "quantity", "amperes")

    with pytest.raises(ValueError, match="successor_request.quantity"):
        orchestrate._validate_transform_continuity(
            execution, run.initial_ir, run.original_request, 0)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    (
        ("observation.request_id", "z", "observation.request_id"),
        ("observation.target", "z", "observation.target"),
        ("observation.quantity", "z", "observation.quantity"),
        ("lineage.request_id", "z", "lineage.request_id"),
        ("lineage.quantity", "z", "lineage.quantity"),
        ("lineage.target_before", "z", "lineage.target_before"),
        ("successor.id", "z", "successor_request.id"),
        ("successor.target", "z", "successor_request.target"),
    ),
)
def test_guardie_continuita_rifiutano_un_valore_lessicograficamente_maggiore(
    monkeypatch, path, value, match,
):
    """Distingue `!=` da `<` senza affidarsi alle guardie successive."""
    run = _series_run()
    execution = run.transform_executions[0]
    owner, field = path.split(".")
    if owner == "observation":
        subject = execution.observation
    elif owner == "lineage":
        subject = execution.request_lineage
    else:
        assert execution.successor_request is not None
        subject = execution.successor_request
    object.__setattr__(subject, field, value)
    monkeypatch.setattr(orchestrate, "validate_observation_lineage", lambda *_: None)
    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: execution)

    with pytest.raises(ValueError, match=match):
        orchestrate._validate_transform_continuity(
            execution, run.initial_ir, run.original_request, 0)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    (
        ("plan.request_id", "z", "piano nodale finale"),
        ("resolved.request_id", "z", "quantita' risolta"),
        ("resolved.target", "A", "Claim P1-K finale.*target"),
        ("resolved.quantity", "z", "Claim P1-K finale.*quantity"),
    ),
)
def test_run_rifiuta_campi_finali_non_uguali_anche_nella_direzione_opposta(
    path, value, match,
):
    """Distingue i confronti finali `!=` dalle varianti `<` e `>`."""
    run = _zero_run()
    owner, field = path.split(".")
    subject = run.final_execution.execution.plan if owner == "plan" else run.final_execution.execution.resolved
    object.__setattr__(subject, field, value)

    with pytest.raises(ValueError, match=match):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_binding_del_successore_richiede_uguaglianza_di_valore_non_identita():
    """L'IR deserializzato puo' ricreare Request e stringhe uguali ma non identiche."""
    run = _series_run()
    successor = run.transform_executions[0].successor_request
    assert successor is not None
    copied = Request(
        "".join((successor.id[:1], successor.id[1:])),
        "".join((successor.quantity[:1], successor.quantity[1:])),
        "".join((successor.target[:1], successor.target[1:])),
    )
    assert copied == successor and copied is not successor
    assert copied.id == successor.id and copied.id is not successor.id
    after = replace(run.transform_executions[0].after, requests=(copied,))

    assert orchestrate._bind_successor_request(after, successor) is after


def test_identity_accetta_un_successore_uguale_ma_non_identico():
    """Distingue `!=` da `is not` per la Request identity P1-J."""
    ir, request = _input(SERIE, "V1", "voltage")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(run, CertifiedDidacticRun)
    step = run.transform_executions[0]
    copied = Request(
        "".join((request.id[:1], request.id[1:])),
        "".join((request.quantity[:1], request.quantity[1:])),
        "".join((request.target[:1], request.target[1:])),
    )
    assert copied == request and copied is not request
    object.__setattr__(step, "successor_request", copied)

    orchestrate._validate_transform_continuity(step, ir, request, 0)


@pytest.mark.parametrize(
    "path",
    (
        "observation.request_id",
        "observation.target",
        "observation.quantity",
        "lineage.request_id",
        "lineage.quantity",
        "lineage.target_before",
        "successor.id",
        "successor.quantity",
        "successor.target",
    ),
)
def test_guardie_continuita_accettano_uguali_non_identici(path):
    """Le guardie confrontano valore, non l'identita' dell'oggetto deserializzato."""
    run = _series_run()
    execution = run.transform_executions[0]
    owner, field = path.split(".")
    if owner == "observation":
        subject = execution.observation
    elif owner == "lineage":
        subject = execution.request_lineage
    else:
        assert execution.successor_request is not None
        subject = execution.successor_request
    original = getattr(subject, field)
    dynamic = "".join((original[:1], original[1:]))
    assert dynamic == original and dynamic is not original
    object.__setattr__(subject, field, dynamic)

    orchestrate._validate_transform_continuity(
        execution, run.initial_ir, run.original_request, 0)


def test_request_binding_accetta_una_request_uguale_ma_non_identica_e_un_related_id_minore():
    ir, request = _input(SERIE, "R1", "current")
    equal_request = Request("".join(("q", "1")), "".join(("cur", "rent")), "R1")
    assert equal_request == request and equal_request is not request
    orchestrate._assert_request_bound(ir, equal_request)

    lower = Request("q0", "voltage", "V1")
    with_lower = replace(ir, requests=(request, lower))
    orchestrate._assert_request_bound(with_lower, request)

    run = _series_run()
    step = run.transform_executions[0]
    assert step.successor_request is not None
    assert orchestrate._bind_successor_request(
        replace(step.after, requests=(lower,)), step.successor_request).requests[-1] == step.successor_request


def test_run_accetta_final_request_uguale_ma_non_identica():
    run = _series_run()
    same = Request(
        "".join((run.final_request.id[:1], run.final_request.id[1:])),
        "".join((run.final_request.quantity[:1], run.final_request.quantity[1:])),
        "".join((run.final_request.target[:1], run.final_request.target[1:])),
    )
    assert same == run.final_request and same is not run.final_request

    assert replace(run, final_request=same).final_request == same


@pytest.mark.parametrize("field", ("request_id", "quantity"))
def test_legame_nodale_finale_accetta_attributi_uguali_non_identici(field):
    run = _zero_run()
    execution = run.final_execution.execution
    subject = execution.plan if field == "request_id" else execution.resolved
    original = getattr(subject, field)
    dynamic = "".join((original[:1], original[1:]))
    assert dynamic == original and dynamic is not original
    object.__setattr__(subject, field, dynamic)

    assert CertifiedDidacticRun(
        run.initial_ir,
        run.original_request,
        run.transform_executions,
        run.final_ir,
        run.final_request,
        run.final_execution,
    ).final_execution == run.final_execution


def test_guardie_effect_kind_confrontano_contenuto_non_identita(monkeypatch):
    run = _series_run()
    step = run.transform_executions[0]
    dynamic_blocked = "".join(("blo", "cked"))
    blocked = step.observation_effect.__class__(dynamic_blocked, None, "sentinella")  # type: ignore[arg-type]
    object.__setattr__(step, "observation_effect", blocked)
    monkeypatch.setattr(orchestrate, "observation_effect", lambda *_: blocked)

    with pytest.raises(RuntimeError, match="blocked"):
        orchestrate._validate_transform_continuity(
            step, run.initial_ir, run.original_request, 0)
    monkeypatch.undo()

    ir, request = _input(SERIE, "V1", "voltage")
    identity = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(identity, CertifiedDidacticRun)
    identity_step = identity.transform_executions[0]
    dynamic_identity = "".join(("iden", "tity"))
    object.__setattr__(identity_step.observation_effect, "kind", dynamic_identity)
    successor = Request(request.id, request.quantity, "A")
    object.__setattr__(identity_step, "successor_request", successor)
    object.__setattr__(identity_step.request_lineage, "target_after", successor.target)

    with pytest.raises(ValueError, match="identity"):
        orchestrate._validate_transform_continuity(identity_step, ir, request, 0)


def test_guardia_continuita_rifiuta_un_oggetto_che_non_e_una_transform_execution():
    run = _series_run()

    with pytest.raises(TypeError, match="TransformExecution"):
        orchestrate._validate_transform_continuity(
            object(), run.initial_ir, run.original_request, 0)


@pytest.mark.parametrize(
    ("mutate", "match"),
    (
        (lambda step: object.__setattr__(step, "plan", object()), "piano non DidacticPlan"),
        (lambda step: object.__setattr__(step.plan, "actions", ()), "un solo passo"),
        (lambda step: object.__setattr__(step, "results", ()), "risultato trasformativo"),
        (lambda step: object.__setattr__(step.observation, "target", "A"), "observation.target"),
    ),
)
def test_guardia_continuita_rifiuta_i_campi_strutturali_corotti(mutate, match):
    run = _series_run()
    step = run.transform_executions[0]
    mutate(step)

    with pytest.raises((TypeError, ValueError), match=match):
        orchestrate._validate_transform_continuity(
            step, run.initial_ir, run.original_request, 0)


def test_guardia_continuita_rifiuta_un_replay_trasformativo_non_riproducibile(monkeypatch):
    run = _series_run()
    wrong_execution = _zero_run().final_execution.execution
    monkeypatch.setattr(orchestrate, "execute_plan", lambda *_args, **_kwargs: wrong_execution)

    with pytest.raises(ValueError, match="risultato non riproducibile"):
        orchestrate._validate_transform_continuity(
            run.transform_executions[0], run.initial_ir, run.original_request, 0)


def test_replay_del_planner_rifiuta_piano_non_didactic_e_esito_sconosciuto(monkeypatch):
    run = _zero_run()

    with pytest.raises(TypeError, match="invece di DidacticPlan"):
        orchestrate._require_canonical_plan(
            run.initial_ir, run.original_request, object(), phase="test")
    monkeypatch.setattr(orchestrate, "pianifica", lambda *_: SimpleNamespace())
    with pytest.raises(RuntimeError, match="esito sconosciuto"):
        orchestrate._require_canonical_plan(
            run.initial_ir,
            run.original_request,
            run.final_execution.execution.plan,
            phase="test",
        )


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


@pytest.mark.parametrize(
    ("corrupt", "match"),
    (
        (
            lambda step: object.__setattr__(step.observation_effect, "kind", "blocked"),
            "effetto osservativo",
        ),
        (
            lambda step: object.__setattr__(step.observation_effect, "target_after", "R3"),
            "effetto osservativo",
        ),
        (
            lambda step: object.__setattr__(step.request_lineage, "effect", "identity"),
            "lineage della Request",
        ),
        (
            lambda step: object.__setattr__(step.request_lineage, "operation", "parallelo"),
            "lineage della Request",
        ),
        (
            lambda step: object.__setattr__(
                step.results[0].equation, "subject", "risultato_corrotto"),
            "risultato certificato",
        ),
    ),
)
def test_run_riapplica_le_autorita_p1j_contro_tampering_della_trace(corrupt, match):
    run = _series_run()
    step = run.transform_executions[0]
    corrupt(step)

    with pytest.raises(ValueError, match=match):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_run_rifiuta_risultato_trasformativo_sostituito_con_un_altro_passaggio():
    series = _series_run()
    parallel_ir, parallel_request = _input(PARALLELO, "R1", "voltage")
    parallel = orchestrate_didactic_run(
        parallel_ir, parallel_request, state_ids=_states(2, start=700))
    assert isinstance(parallel, CertifiedDidacticRun)
    object.__setattr__(
        series.transform_executions[0],
        "results",
        parallel.transform_executions[0].results,
    )

    with pytest.raises(ValueError, match="operazione|risultato certificato"):
        CertifiedDidacticRun(
            series.initial_ir,
            series.original_request,
            series.transform_executions,
            series.final_ir,
            series.final_request,
            series.final_execution,
        )


def test_trace_composta_rifiuta_se_il_planner_ora_rifiuta_lo_stato(monkeypatch):
    run = _series_run()
    refusal = Refusal("unsolvable", run.original_request.id, "request", "planner rifiuta")
    monkeypatch.setattr(orchestrate, "pianifica", lambda *_: refusal)

    with pytest.raises(ValueError, match="planner ha rifiutato"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            run.transform_executions,
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_trace_composta_rifiuta_trasformazioni_nell_ordine_sbagliato():
    ir, request = _input(MULTI_SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(3))
    assert isinstance(run, CertifiedDidacticRun)
    assert len(run.transform_executions) == 2

    with pytest.raises(ValueError, match="piano pianificato|before non coincide"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            tuple(reversed(run.transform_executions)),
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_trace_composta_rifiuta_un_passaggio_duplicato_o_omesso():
    ir, request = _input(MULTI_SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(3))
    assert isinstance(run, CertifiedDidacticRun)
    first, second = run.transform_executions

    with pytest.raises(ValueError, match="piano pianificato|before non coincide"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            (first, first, second),
            run.final_ir,
            run.final_request,
            run.final_execution,
        )
    with pytest.raises(ValueError, match="final_ir"):
        CertifiedDidacticRun(
            run.initial_ir,
            run.original_request,
            (first,),
            run.final_ir,
            run.final_request,
            run.final_execution,
        )


def test_trace_composta_rifiuta_finale_di_altro_circuito_anche_con_lineage_corretta():
    ir_a, request_a = _input(SERIE, "R1", "current")
    ir_b, request_b = _input(
        SERIE.replace("I1 0 b 1 ampere", "I1 0 b 2 ampere"), "R1", "current")
    run_a = orchestrate_didactic_run(ir_a, request_a, state_ids=_states(2))
    run_b = orchestrate_didactic_run(ir_b, request_b, state_ids=_states(2, start=300))
    assert isinstance(run_a, CertifiedDidacticRun)
    assert isinstance(run_b, CertifiedDidacticRun)

    with pytest.raises(ValueError, match="certificazione finale"):
        CertifiedDidacticRun(
            run_a.initial_ir,
            run_a.original_request,
            run_a.transform_executions,
            run_a.final_ir,
            run_a.final_request,
            run_b.final_execution,
        )


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


def test_retarget_mantiene_after_letterale_e_lega_il_successore_solo_nello_stato_operativo():
    run = _series_run()
    step = run.transform_executions[0]
    assert step.successor_request is not None

    assert step.after.requests == ()
    operational_after = orchestrate._bind_successor_request(
        step.after, step.successor_request)
    assert operational_after is not step.after
    assert operational_after.requests == (step.successor_request,)


def test_identity_riusa_l_ir_after_quando_la_request_sopravvive():
    ir, request = _input(SERIE, "V1", "voltage")
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(run, CertifiedDidacticRun)
    step = run.transform_executions[0]
    assert step.successor_request is request

    assert orchestrate._bind_successor_request(step.after, request) is step.after


def test_rebinding_preserva_le_request_non_correlate():
    ir, request = _input(SERIE, "R1", "current")
    unrelated = Request("q2", "voltage", "V1")
    ir = replace(ir, requests=(request, unrelated))
    run = orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert isinstance(run, CertifiedDidacticRun)
    step = run.transform_executions[0]
    assert step.successor_request is not None

    assert step.after.requests == (unrelated,)
    operational_after = orchestrate._bind_successor_request(
        step.after, step.successor_request)
    assert operational_after.requests == (unrelated, step.successor_request)


def test_trasformazione_non_decrescente_e_rifiutata_prima_del_replan(monkeypatch):
    ir, request = _input(SERIE, "R1", "current")
    original_execute = orchestrate.execute_plan
    original_plan = orchestrate.pianifica
    planner_calls = 0

    def count_plans(*args):
        nonlocal planner_calls
        planner_calls += 1
        return original_plan(*args)

    def non_decreasing(*args, **kwargs):
        outcome = original_execute(*args, **kwargs)
        if isinstance(outcome, TransformExecution):
            object.__setattr__(outcome, "after", outcome.before)
        return outcome

    monkeypatch.setattr(orchestrate, "pianifica", count_plans)
    monkeypatch.setattr(orchestrate, "execute_plan", non_decreasing)

    with pytest.raises(ValueError, match="non riduce"):
        orchestrate_didactic_run(ir, request, state_ids=_states(2))
    assert planner_calls == 1


def test_stessi_input_e_state_id_danno_una_run_strutturalmente_identica():
    ir, request = _input(MULTI_PARALLELO, "R1", "voltage")
    states = _states(len(ir.components))

    assert orchestrate_didactic_run(ir, request, state_ids=states) == orchestrate_didactic_run(
        ir, request, state_ids=states)


def test_confini_architetturali_restano_intatti_e_senza_ricerca_o_cas():
    root = Path(__file__).resolve().parents[1]
    execute = (root / "src/kirchhoff/domain/didactic/execute.py").read_text()
    truthfulness = (root / "src/kirchhoff/domain/truthfulness.py").read_text()
    orchestration = Path(orchestrate.__file__).read_text()
    engine = (root / "src/kirchhoff/domain/transform/engine.py").read_text()
    execute_tree = ast.parse(execute)
    truthfulness_tree = ast.parse(truthfulness)
    orchestration_tree = ast.parse(orchestration)
    engine_tree = ast.parse(engine)

    def imported_modules(tree):
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        return modules

    execute_modules = imported_modules(execute_tree)
    truthfulness_modules = imported_modules(truthfulness_tree)
    orchestration_modules = imported_modules(orchestration_tree)
    engine_modules = imported_modules(engine_tree)

    assert not any("planner" in module for module in execute_modules)
    assert not any("orchestrate" in module for module in execute_modules)
    assert not any("truthfulness" in module for module in execute_modules)
    assert not any(module.endswith("mna") or "tableau" in module for module in execute_modules)
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "pianifica"
        for node in ast.walk(execute_tree)
    )
    assert not any("planner" in module for module in truthfulness_modules)
    assert not any("orchestrate" in module for module in truthfulness_modules)
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "pianifica"
        for node in ast.walk(truthfulness_tree)
    )
    assert not any(
        forbidden in module
        for forbidden in ("mna", "independent_dc", "tableau", "render", "pipeline")
        for module in orchestration_modules
    )
    assert not any("planner" in module or "orchestrate" in module for module in engine_modules)
    assert "Request" not in engine_modules
    assert all(term not in orchestration for term in (
        "StrategyScore(", "beam_search(", "graph_search(", "import lcapy", "from lcapy",
    ))
