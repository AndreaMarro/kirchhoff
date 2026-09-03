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
    validate_observation_lineage,
)
from kirchhoff.domain.didactic import DidacticPlan, pianifica
from kirchhoff.domain.ir import Request
from kirchhoff.domain.refusal import Refusal
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
    validate_observation_lineage(
        before, after, result, "serie", request, successor, lineage)


def test_corruzioni_della_lineage_sono_rifiutate():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    successor, lineage = apply_observation_effect(request, effect, operation="serie")
    assert successor is not None
    with pytest.raises(ValueError, match="lineage"):
        validate_observation_lineage(
            before, after, result, "serie", request, successor,
            replace(lineage, request_id="q_altra"))
    with pytest.raises(ValueError, match="lineage"):
        validate_observation_lineage(
            before, after, result, "serie", request, successor,
            replace(lineage, quantity="voltage"))
    with pytest.raises(ValueError, match="componente assente"):
        validate_observation_lineage(
            before, after, result, "serie", request,
            Request("q1", "current", "inventato"), lineage)


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
    validate_observation_lineage(
        before, after, result, "serie", request, successor_identity, lineage_identity)

    blocked_request = Request("q2", "voltage", "R1")
    before, after, result = _outcome(PARTITORE, "serie", blocked_request)
    blocked = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(blocked_request))
    successor, lineage = apply_observation_effect(blocked_request, blocked, operation="serie")
    assert successor is None
    assert lineage.target_after is None
    validate_observation_lineage(
        before, after, result, "serie", blocked_request, successor, lineage)


def test_piu_componenti_creati_fallisce_chiuso():
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    created = result.layout_patch.create[0]
    object.__setattr__(result.layout_patch, "create", (created, created))
    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))
    assert effect.kind == "blocked"
    assert effect.target_after is None


def test_zero_componenti_creati_fallisce_chiuso():
    """Il retarget richiede esattamente uno, non zero o uno."""
    request = Request("q1", "current", "R1")
    before, after, result = _outcome(PARTITORE, "serie", request)
    object.__setattr__(result.layout_patch, "create", ())

    effect = observation_effect(
        before, after, result, "serie", ObservationContract.from_request(request))

    assert effect.kind == "blocked"
    assert effect.target_after is None


def test_effetti_e_operazioni_uguali_non_dipendono_dall_identita_della_stringa():
    """Le guardie semantiche confrontano contenuto, anche per input deserializzato."""
    dynamic_blocked = "".join(("blo", "cked"))
    dynamic_identity = "".join(("iden", "tity"))
    dynamic_retarget = "".join(("re", "target"))
    dynamic_series = "".join(("ser", "ie"))
    dynamic_parallel = "".join(("par", "allelo"))
    dynamic_current = "".join(("cur", "rent"))
    dynamic_voltage = "".join(("volt", "age"))
    literal_blocked, literal_identity, literal_series = "blocked", "identity", "serie"
    assert dynamic_blocked == literal_blocked and dynamic_blocked is not literal_blocked
    assert dynamic_identity == literal_identity and dynamic_identity is not literal_identity
    assert dynamic_series == literal_series and dynamic_series is not literal_series
    with pytest.raises(ValueError, match="target_after"):
        ObservationEffect(dynamic_blocked, "R12eq", "x")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="target_after"):
        ObservationEffect(dynamic_identity, None, "x")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="senza target_after"):
        RequestLineageStep("q1", "current", "R1", None, "serie", dynamic_identity)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lineage blocked"):
        RequestLineageStep("q1", "current", "R1", "R12eq", "serie", dynamic_blocked)  # type: ignore[arg-type]
    assert RequestLineageStep(
        "q1", "current", "R1", None, "serie", dynamic_blocked,  # type: ignore[arg-type]
    ).effect == "blocked"

    request = Request("q1", dynamic_current, "R1")  # type: ignore[arg-type]
    before, after, result = _outcome(PARTITORE, "serie", request)
    effect = observation_effect(
        before, after, result, dynamic_series, ObservationContract.from_request(request))
    assert effect.kind == "retarget"

    parallel_request = Request("q2", dynamic_voltage, "R1")  # type: ignore[arg-type]
    before_parallel, after_parallel, parallel_result = _outcome(
        PARALLELO, "parallelo", parallel_request)
    assert observation_effect(
        before_parallel,
        after_parallel,
        parallel_result,
        dynamic_parallel,
        ObservationContract.from_request(parallel_request),
    ).kind == "retarget"

    identity_target = "".join(("V", "1"))
    identity_request = Request("q3", "voltage", "V1")
    identity_successor, _identity_lineage = apply_observation_effect(
        identity_request,
        ObservationEffect(dynamic_identity, identity_target, "identita' dinamica"),  # type: ignore[arg-type]
        operation="serie",
    )
    assert identity_successor is identity_request
    retarget_successor, _retarget_lineage = apply_observation_effect(
        request,
        ObservationEffect(dynamic_retarget, "R12eq", "retarget dinamico"),  # type: ignore[arg-type]
        operation="serie",
    )
    assert retarget_successor == Request("q1", "current", "R12eq")
    with pytest.raises(ValueError, match="diversa dal risultato"):
        observation_effect(
            before, after, result, "zz_operazione", ObservationContract.from_request(request))
    with pytest.raises(ValueError, match="identity"):
        apply_observation_effect(
            identity_request,
            ObservationEffect(dynamic_identity, "z_target", "target scorretto"),  # type: ignore[arg-type]
            operation="serie",
        )


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
    with pytest.raises(ValueError, match="successore Request"):
        validate_observation_lineage(
            before, after_without_successor, result, "serie", request, successor, lineage)
    before_without_request_target = replace(
        before,
        components=tuple(c for c in before.components if c.id != request.target),
        requests=(),
    )
    with pytest.raises(ValueError, match="partenza"):
        validate_observation_lineage(
            before_without_request_target, after, result, "serie", request, successor, lineage)


@pytest.mark.parametrize(
    ("operation", "netlist", "quantity", "forced_kind"),
    (
        ("serie", PARTITORE, "current", "blocked"),
        ("serie", PARTITORE, "voltage", "retarget"),
        ("parallelo", PARALLELO, "voltage", "blocked"),
        ("parallelo", PARALLELO, "current", "retarget"),
    ),
)
def test_validator_rifiuta_effetti_corotti_ma_internamente_coerenti(
    operation, netlist, quantity, forced_kind,
):
    request = Request("q1", quantity, "R1")  # type: ignore[arg-type]
    before, after, result = _outcome(netlist, operation, request)
    target_after = (
        None if forced_kind == "blocked" else result.layout_patch.create[0].id
    )
    forced = ObservationEffect(forced_kind, target_after, "corruzione")  # type: ignore[arg-type]
    successor, lineage = apply_observation_effect(request, forced, operation=operation)
    with pytest.raises(ValueError, match="successore Request|lineage"):
        validate_observation_lineage(
            before, after, result, operation, request, successor, lineage)


@pytest.mark.parametrize(
    "quantity",
    ("time_constant", "initial_value", "final_value", "root_1", "root_2"),
)
def test_planner_rifiuta_quantity_valida_ma_non_osservabile_senza_sollevare(quantity):
    request = Request("q1", quantity, "R1")  # type: ignore[arg-type]
    ir = replace(leggi(PARTITORE), requests=(request,))
    assert isinstance(pianifica(ir, request), Refusal)


@pytest.mark.parametrize(
    ("quantity", "technique"),
    (("current", "certified_transform_path"), ("voltage", "nodal_analysis")),
)
def test_planner_mantiene_il_comportamento_per_quantita_osservabili(quantity, technique):
    request = Request("q1", quantity, "R1")  # type: ignore[arg-type]
    ir = replace(leggi(PARTITORE), requests=(request,))
    plan = pianifica(ir, request)
    assert isinstance(plan, DidacticPlan)
    assert plan.technique == technique


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
