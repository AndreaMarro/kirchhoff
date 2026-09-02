"""L'enumerazione descrive scelte gia' eseguibili, ma non sceglie."""

from __future__ import annotations

import pytest

from lab.fixtures.cases import case_for_seed

from kirchhoff.domain.didactic.candidates import enumerate_strategy_candidates
from kirchhoff.domain.didactic.planner import pianifica
import kirchhoff.domain.didactic.candidates as candidate_module
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.refusal import Refusal


def test_candidati_trasformativi_espongono_l_effetto_p1j_autorevole():
    case = case_for_seed(1)
    candidates = enumerate_strategy_candidates(case.ir, case.request)

    transforms = [candidate for candidate in candidates if candidate.technique == "certified_transform_path"]
    assert transforms
    assert all(candidate.operation is not None for candidate in transforms)
    assert all(candidate.observation_effect is not None for candidate in transforms)
    assert all(candidate.admissible == (candidate.observation_effect.kind != "blocked") for candidate in transforms)
    assert pianifica(case.ir, case.request).actions[0].kind == transforms[0].operation


def test_candidato_nodale_e_esposto_solo_quando_e_il_piano_eseguibile_corrente():
    case = case_for_seed(2)
    candidates = enumerate_strategy_candidates(case.ir, case.request)

    nodal_candidates = [candidate for candidate in candidates if candidate.technique == "nodal_analysis"]
    assert len(nodal_candidates) == 1
    nodal = nodal_candidates[0]
    assert nodal.technique == "nodal_analysis"
    assert nodal.operation is None
    assert nodal.observation_effect is None
    assert nodal.admissible is True
    assert nodal.actions == pianifica(case.ir, case.request).actions
    blocked = [candidate for candidate in candidates if not candidate.admissible]
    assert len(blocked) == 1
    assert blocked[0].observation_effect.kind == "blocked"


def test_candidati_non_mutano_il_piano_produzione():
    case = case_for_seed(1)
    before = pianifica(case.ir, case.request)
    assert not isinstance(before, Refusal)

    enumerate_strategy_candidates(case.ir, case.request)

    assert pianifica(case.ir, case.request) == before


def test_candidati_rifiutano_tipi_errati_e_non_inventano_scopo_se_il_planner_rifiuta(monkeypatch):
    case = case_for_seed(1)
    monkeypatch.setattr(
        candidate_module, "pianifica",
        lambda _ir, _request: Refusal("unsolvable", case.request.id, "request", "rifiuto test"),
    )

    assert enumerate_strategy_candidates(case.ir, case.request) == ()
    with pytest.raises(TypeError, match="invece di IR"):
        enumerate_strategy_candidates(object(), case.request)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di Request"):
        enumerate_strategy_candidates(case.ir, object())  # type: ignore[arg-type]
