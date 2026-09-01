"""P1-I: replay esatto di un DidacticPlan certified_transform_path."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    PlannedAction,
    TransformExecution,
    execute_plan,
    pianifica,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PARALLELO, PARTITORE

F = Fraction
PROOF = conia("ir", 2, bytes(range(10)))


def _req(target: str, quantity: str, rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _con(ir, request: Request):
    return replace(ir, requests=(request,))


def test_t1_serie_esegue_esattamente_gli_operandi():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    assert piano.technique == "certified_transform_path"
    assert piano.actions == (PlannedAction("serie", ("R1", "R2")),)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    assert esito.before == ir
    assert esito.after != ir
    assert len(esito.results) == 1
    ids_dopo = {c.id for c in esito.after.components}
    assert "R1" not in ids_dopo or "R2" not in ids_dopo


def test_t2_parallelo_esegue_esattamente_gli_operandi():
    request = _req("R1", "voltage")
    ir = _con(leggi(PARALLELO), request)
    piano = pianifica(ir, request)
    assert piano.technique == "certified_transform_path"
    assert piano.actions[0].kind == "parallelo"
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    assert esito.after != ir
    assert len(esito.results) == 1
    assert esito.plan == piano


def test_t3_target_consumato_nessun_remap():
    request = _req("R1", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    assert piano.technique == "certified_transform_path"
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    assert not hasattr(esito, "resolved")
    ids_dopo = {c.id for c in esito.after.components}
    assert "R1" not in ids_dopo
    assert all(r.target != "R1" for r in esito.after.requests)
    assert all(r.target in ids_dopo for r in esito.after.requests)
    equivalenti = ids_dopo - {c.id for c in ir.components}
    assert not any(r.target in equivalenti for r in esito.after.requests)


def test_t4_parallelo_tensione_target_consumato():
    request = _req("R1", "voltage")
    ir = _con(leggi(PARALLELO), request)
    piano = pianifica(ir, request)
    assert piano.technique == "certified_transform_path"
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    ids_dopo = {c.id for c in esito.after.components}
    assert "R1" not in ids_dopo
    equivalenti = ids_dopo - {c.id for c in ir.components}
    assert not any(r.target in equivalenti for r in esito.after.requests)


def test_t4b_esecutore_registra_la_lineage_senza_remappare_l_ir():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    assert esito.observation_effect is not None
    assert esito.observation_effect.kind == "retarget"
    assert esito.successor_request is not None
    assert esito.successor_request.id == request.id
    assert esito.successor_request.quantity == request.quantity
    assert esito.successor_request.target not in {c.id for c in ir.components}
    assert esito.request_lineage is not None
    assert esito.request_lineage.target_before == request.target
    assert esito.request_lineage.target_after == esito.successor_request.target
    assert all(r.target != esito.successor_request.target for r in esito.after.requests)


def test_t4c_transform_execution_rifiuta_lineage_parziale_o_incoerente():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)
    with pytest.raises(ValueError, match="parziale"):
        replace(esito, observation=None)
    legacy = replace(
        esito,
        observation=None,
        observation_effect=None,
        successor_request=None,
        request_lineage=None,
    )
    assert legacy.observation is None
    assert esito.observation is not None
    with pytest.raises(ValueError, match="diversa dal piano"):
        replace(esito, observation=replace(esito.observation, request_id="q_altra"))
    doppio = replace(esito.plan, actions=(esito.plan.actions[0], esito.plan.actions[0]))
    with pytest.raises(ValueError, match="un solo passo"):
        replace(esito, plan=doppio, results=(esito.results[0], esito.results[0]))
    with pytest.raises(ValueError, match="effetto osservativo"):
        replace(esito, observation_effect=esito.observation_effect.__class__(
            "blocked", None, "corrotto"))


def test_t5_non_chiama_pianifica(monkeypatch):
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)

    def boom(*_a, **_k):
        raise AssertionError("pianifica called")

    monkeypatch.setattr("kirchhoff.domain.didactic.planner.pianifica", boom)
    monkeypatch.setattr("kirchhoff.domain.didactic.pianifica", boom)
    esito = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(esito, TransformExecution)


def test_t6_multi_azione_v02_rifiutata():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    doppio = replace(
        piano,
        actions=(
            piano.actions[0],
            PlannedAction("serie", piano.actions[0].operands),
        ),
    )
    with pytest.raises(ValueError, match="request lineage"):
        execute_plan(ir, request, doppio, proof_node=PROOF)


def test_t7_operandi_trasformazione_errati():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    rotto = replace(piano, actions=(PlannedAction("serie", ("R1", "V1")),))
    with pytest.raises(ValueError):
        execute_plan(ir, request, rotto, proof_node=PROOF)


def test_d2_determinismo_transform():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    a = execute_plan(ir, request, piano, proof_node=PROOF)
    b = execute_plan(ir, request, piano, proof_node=PROOF)
    assert isinstance(a, TransformExecution)
    assert isinstance(b, TransformExecution)
    assert a.after == b.after
    assert a.results == b.results


def test_immutabilita_transform():
    request = _req("R2", "current")
    ir = _con(leggi(PARTITORE), request)
    piano = pianifica(ir, request)
    comps, reqs, azioni = ir.components, ir.requests, piano.actions
    execute_plan(ir, request, piano, proof_node=PROOF)
    assert ir.components is comps
    assert ir.requests is reqs
    assert piano.actions is azioni
