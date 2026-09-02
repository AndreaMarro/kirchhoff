"""Fatti topologici puri: nessun ranking o oracolo esterno."""

from __future__ import annotations

from dataclasses import replace

import pytest

from lab.fixtures.cases import case_for_seed

from kirchhoff.domain.didactic.features import extract_circuit_features
from kirchhoff.domain.ir import Request
from kirchhoff.pipeline.netlist import leggi


def test_features_descrive_il_circuito_senza_float_o_stato_nascosto():
    case = case_for_seed(1)

    first = extract_circuit_features(case.ir, case.request)
    second = extract_circuit_features(case.ir, case.request)

    assert first == second
    assert first.component_count == 5
    assert first.resistor_count == 3
    assert first.source_count == 2
    assert first.node_count == 3
    assert first.connected_regions == 1
    assert first.cycle_rank == 3
    assert first.executable_reduction_count >= first.admissible_reduction_count


def test_features_conta_unknown_e_kcl_con_le_definizioni_del_planner():
    case = case_for_seed(3)
    features = extract_circuit_features(case.ir, case.request)

    assert features.nodal_unknown_count == 2
    assert features.ordinary_kcl_count == 0
    assert features.simple_supernode_count == 1


def test_features_rifiuta_tipi_non_ir_e_conta_sorgente_inversa_verso_massa():
    request = Request("q_inverse", "voltage", "R1")
    ir = replace(leggi("V1 0 p 7 volt\nR1 p 0 3 ohm\n"), requests=(request,))

    assert extract_circuit_features(ir, request).nodal_unknown_count == 0
    with pytest.raises(TypeError, match="invece di IR"):
        extract_circuit_features(object(), request)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di Request"):
        extract_circuit_features(ir, object())  # type: ignore[arg-type]
