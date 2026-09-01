"""P1-J: contratto osservativo e lineage della Request."""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from kirchhoff.domain.didactic.observation import (
    ObservationContract,
    ObservationEffect,
    RequestLineageStep,
    apply_observation_effect,
    observation_effect,
    validate_request_lineage,
)
from kirchhoff.domain.ir import Request
from kirchhoff.domain.transform import transform
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PARALLELO, PARTITORE


def _outcome(netlist: str, operation: str, request: Request):
    before = replace(leggi(netlist), requests=(request,))
    outcome = transform(before, operation, "R1", "R2")
    assert not isinstance(outcome, Exception)
    after, result = outcome
    return before, after, result


@pytest.mark.parametrize(
    ("operation", "netlist", "quantity", "kind"),
    (
        ("serie", PARTITORE, "voltage", "blocked"),
        ("serie", PARTITORE, "current", "retarget"),
        ("parallelo", PARALLELO, "voltage", "retarget"),
        ("parallelo", PARALLELO, "current", "blocked"),
    ),
)
def test_tabella_verita_target_consumato(operation, netlist, quantity, kind):
    request = Request("q1", quantity, "R1")  # type: ignore[arg-type]
    before, after, result = _outcome(netlist, operation, request)
    effect = observation_effect(
        before, after, result, operation, ObservationContract.from_request(request))
    assert effect.kind == kind
    assert (effect.target_after is None) is (kind == "blocked")


@pytest.mark.parametrize(
    ("operation", "netlist", "quantity"),
    (
        ("serie", PARTITORE, "voltage"),
        ("serie", PARTITORE, "current"),
        ("parallelo", PARALLELO, "voltage"),
        ("parallelo", PARALLELO, "current"),
    ),
)
def test_tabella_verita_target_intatto(operation, netlist, quantity):
    request = Request("q1", quantity, "V1")  # type: ignore[arg-type]
    before, after, result = _outcome(netlist, operation, request)
    effect = observation_effect(
        before, after, result, operation, ObservationContract.from_request(request))
    assert effect == ObservationEffect("identity", "V1", "il target osservato sopravvive invariato")


def test_contratti_immutabili_e_vocabolari_chiusi():
    request = Request("q1", "current", "R1")
    assert ObservationContract.from_request(request) == ObservationContract("q1", "R1", "current")
    with pytest.raises(ValueError, match="request_id"):
        ObservationContract("", "R1", "current")
    with pytest.raises(ValueError, match="target"):
        ObservationContract("q1", "", "current")
    with pytest.raises(ValueError, match="ammesse"):
        ObservationContract("q1", "R1", "time_constant")
    with pytest.raises(ValueError, match="target_after"):
        ObservationEffect("blocked", "R12eq", "x")
    with pytest.raises(ValueError, match="target_after"):
        ObservationEffect("retarget", None, "x")
    with pytest.raises(ValueError, match="vocabolario"):
        ObservationEffect("inventato", None, "x")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="motivazione"):
        ObservationEffect("blocked", None, "")
    with pytest.raises(ValueError, match="request_id"):
        RequestLineageStep("", "current", "R1", "R12eq", "serie", "retarget")
    with pytest.raises(ValueError, match="non osservabile"):
        RequestLineageStep("q1", "time_constant", "R1", "R12eq", "serie", "retarget")
    with pytest.raises(ValueError, match="target_before"):
        RequestLineageStep("q1", "current", "", "R12eq", "serie", "retarget")
    with pytest.raises(ValueError, match="operation"):
        RequestLineageStep("q1", "current", "R1", "R12eq", "", "retarget")
    with pytest.raises(ValueError, match="sconosciuto"):
        RequestLineageStep("q1", "current", "R1", "R12eq", "serie", "inventato")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocked"):
        RequestLineageStep("q1", "current", "R1", "R12eq", "serie", "blocked")
    with pytest.raises(ValueError, match="senza target_after"):
        RequestLineageStep("q1", "current", "R1", None, "serie", "identity")
    with pytest.raises(TypeError, match="invece di Request"):
        ObservationContract.from_request(object())  # type: ignore[arg-type]


def test_retarget_conserva_id_e_quantita_e_registra_lineage():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    successor, lineage = apply_observation_effect(request, effect, operation="serie")
    assert successor is not None
    assert successor.id == request.id
    assert successor.quantity == request.quantity
    assert successor.target == effect.target_after
    assert lineage == RequestLineageStep("q1", "current", "R1", successor.target, "serie", "retarget")
    validate_request_lineage(before, after, request, effect, successor, lineage, operation="serie")


def test_corruzioni_della_lineage_sono_rifiutate():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    successor, lineage = apply_observation_effect(request, effect, operation="serie")
    assert successor is not None
    with pytest.raises(ValueError, match="lineage"):
        validate_request_lineage(
            before, after, request, effect, successor,
            replace(lineage, request_id="q_altra"), operation="serie")
    with pytest.raises(ValueError, match="lineage"):
        validate_request_lineage(
            before, after, request, effect, successor,
            replace(lineage, quantity="voltage"), operation="serie")
    with pytest.raises(ValueError, match="successore Request"):
        validate_request_lineage(
            before, after, request, effect, Request("q1", "current", "inventato"),
            lineage, operation="serie")


def test_identity_e_blocked_non_ammettono_successori_inventati():
    request = Request("q1", "voltage", "V1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    identity = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    with pytest.raises(ValueError, match="identity"):
        apply_observation_effect(
            request, ObservationEffect("identity", "R12eq", "corrotto"), operation="serie")
    successor_identity, lineage_identity = apply_observation_effect(
        request, identity, operation="serie")
    assert successor_identity is request
    validate_request_lineage(
        before, after, request, identity, successor_identity, lineage_identity,
        operation="serie")

    blocked_request = Request("q2", "voltage", "R1")
    before, after, result = _outcome(PARTITORE, "serie", blocked_request)
    blocked = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(blocked_request))
    successor, lineage = apply_observation_effect(blocked_request, blocked, operation="serie")
    assert successor is None
    assert lineage.target_after is None
    validate_request_lineage(
        before, after, blocked_request, blocked, successor, lineage, operation="serie")


def test_piu_componenti_creati_fallisce_chiuso():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    created = result.layout_patch.create[0]
    object.__setattr__(result.layout_patch, "create", (created, created))
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    assert effect.kind == "blocked"
    assert effect.target_after is None


def test_authorita_fallisce_chiusa_su_input_o_provenienza_corotti():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    contract = ObservationContract.from_request(request)
    with pytest.raises(TypeError, match="IR prima e dopo"):
        observation_effect(object(), after, result, "serie", contract)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransformResult"):
        observation_effect(before, after, object(), "serie", contract)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ObservationContract"):
        observation_effect(before, after, result, "serie", object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="diversa dal risultato"):
        observation_effect(before, after, result, "parallelo", contract)
    absent = observation_effect(
        before, after, result, "serie", ObservationContract("q1", "R9", "current"))
    assert absent.kind == "blocked"

    consumed = result.layout_patch.remove
    object.__setattr__(result.layout_patch, "remove", ())
    uncertified = observation_effect(before, after, result, "serie", contract)
    assert uncertified.kind == "blocked"
    object.__setattr__(result.layout_patch, "remove", consumed)

    without_equivalent = replace(
        after,
        components=tuple(c for c in after.components if c.id != result.layout_patch.create[0].id),
    )
    missing = observation_effect(before, without_equivalent, result, "serie", contract)
    assert missing.kind == "blocked"


def test_applicazione_e_validazione_rifiutano_input_corrotto():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    successor, lineage = apply_observation_effect(request, effect, operation="serie")
    with pytest.raises(TypeError, match="invece di Request"):
        apply_observation_effect(object(), effect, operation="serie")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di ObservationEffect"):
        apply_observation_effect(request, object(), operation="serie")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="senza operation"):
        apply_observation_effect(request, effect, operation="")
    assert successor is not None
    after_without_successor = replace(
        after,
        components=tuple(c for c in after.components if c.id != successor.target),
    )
    with pytest.raises(ValueError, match="componente assente"):
        validate_request_lineage(
            before, after_without_successor, request, effect, successor, lineage,
            operation="serie")
    before_without_request_target = replace(
        before,
        components=tuple(c for c in before.components if c.id != request.target),
        requests=(),
    )
    with pytest.raises(ValueError, match="partenza"):
        validate_request_lineage(
            before_without_request_target, after, request, effect, successor, lineage,
            operation="serie")


def test_p1j_non_aggiunge_planner_o_cas_runtime():
    root = Path(__file__).resolve().parents[1]
    execute_tree = ast.parse(
        (root / "src/kirchhoff/domain/didactic/execute.py").read_text())
    imports = [node.module for node in ast.walk(execute_tree) if isinstance(node, ast.ImportFrom)]
    calls = [node.func.id for node in ast.walk(execute_tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert "planner" not in imports
    assert "pianifica" not in calls
    production = (root / "src/kirchhoff/domain/didactic/observation.py").read_text()
    assert all(name not in production for name in ("lcapy", "sympy", "numpy", "scipy", "egglog"))
    assert 'dependencies = []' in (root / "pyproject.toml").read_text()
