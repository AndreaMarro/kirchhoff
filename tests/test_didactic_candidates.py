"""L'enumerazione descrive scelte gia' eseguibili, ma non sceglie."""

from __future__ import annotations

import pytest
from dataclasses import replace

from lab.fixtures.cases import case_for_seed

from kirchhoff.domain.didactic.capabilities import (
    nodale_disponibile,
    riduzioni_eseguibili,
)
from kirchhoff.domain.didactic.candidates import enumerate_strategy_candidates
from kirchhoff.domain.didactic.planner import pianifica
import kirchhoff.domain.didactic.candidates as candidate_module
from kirchhoff.domain.ir import Request
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.domain.refusal import Refusal


def test_candidati_enumerano_trasformazione_e_nodale_prima_della_scelta_del_planner():
    """BLOCKER A: il piano corrente sceglie una riduzione ma il nodale esiste."""
    case = case_for_seed(1)

    assert riduzioni_eseguibili(case.ir)
    assert nodale_disponibile(case.ir, case.request.quantity) is True
    assert pianifica(case.ir, case.request).technique == "certified_transform_path"

    candidates = enumerate_strategy_candidates(case.ir, case.request)

    assert [candidate.technique for candidate in candidates] == [
        "certified_transform_path", "nodal_analysis",
    ]


def test_candidati_trasformativi_espongono_l_effetto_p1j_autorevole():
    case = case_for_seed(1)
    candidates = enumerate_strategy_candidates(case.ir, case.request)

    transforms = [candidate for candidate in candidates if candidate.technique == "certified_transform_path"]
    assert transforms
    assert all(candidate.operation is not None for candidate in transforms)
    assert all(candidate.observation_effect is not None for candidate in transforms)
    assert all(candidate.admissible == (candidate.observation_effect.kind != "blocked") for candidate in transforms)
    assert pianifica(case.ir, case.request).actions[0].kind == transforms[0].operation


def test_candidato_nodale_ha_azioni_canoniche_quando_e_eseguibile():
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


def test_candidati_validi_senza_nodale_restituiscono_solo_le_riduzioni_eseguibili():
    ir = leggi("V1 a 0 3 volt\nR1 a 0 3 ohm\n")
    request = Request("q_fissa", "current", "V1")
    ir = replace(ir, requests=(request,))

    assert nodale_disponibile(ir, request.quantity) is False
    assert riduzioni_eseguibili(ir) == ()
    assert enumerate_strategy_candidates(ir, request) == ()


def test_candidati_non_mutano_il_piano_produzione():
    case = case_for_seed(1)
    before = pianifica(case.ir, case.request)
    assert not isinstance(before, Refusal)

    enumerate_strategy_candidates(case.ir, case.request)

    assert pianifica(case.ir, case.request) == before


def test_esistenza_dei_candidati_non_cambia_se_il_planner_cambiasse_preferenza(monkeypatch):
    """Falsificazione B: candidates non ha un canale di ritorno verso pianifica."""
    case = case_for_seed(1)
    before = enumerate_strategy_candidates(case.ir, case.request)

    import kirchhoff.domain.didactic.planner as planner_module
    monkeypatch.setattr(planner_module, "pianifica", lambda *_args: "altra-preferenza")

    assert enumerate_strategy_candidates(case.ir, case.request) == before


def test_candidati_rifiutano_tipi_errati_e_fuori_scope_invece_di_consultare_il_planner():
    case = case_for_seed(1)

    foreign = Request("q_estranea", "voltage", case.request.target)
    refusal = enumerate_strategy_candidates(case.ir, foreign)
    assert isinstance(refusal, Refusal)
    assert refusal.subject == foreign.id
    assert not hasattr(candidate_module, "pianifica")
    with pytest.raises(TypeError, match="invece di IR"):
        enumerate_strategy_candidates(object(), case.request)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di Request"):
        enumerate_strategy_candidates(case.ir, object())  # type: ignore[arg-type]


def test_candidati_rifiutano_request_omonima_ma_non_coerente_col_suo_ir():
    case = case_for_seed(1)
    mismatched = Request(case.request.id, "current", case.request.target)

    refusal = enumerate_strategy_candidates(case.ir, mismatched)

    assert isinstance(refusal, Refusal)
    assert refusal.subject == case.request.id
    assert "non e' quella dichiarata" in refusal.diagnosis


@pytest.mark.parametrize(
    ("build_ir", "build_request", "subject"),
    (
        pytest.param(
            lambda case: case.ir,
            lambda case: Request("q_estranea", "voltage", case.request.target),
            "q_estranea",
            id="request-estranea",
        ),
        pytest.param(
            lambda case: replace(
                case.ir,
                requests=(case.request, Request(case.request.id, "current", "R2")),
            ),
            lambda case: case.request,
            "q_generated-001",
            id="request-id-duplicato",
        ),
        pytest.param(
            lambda case: replace(case.ir, domain="dc_resistive"),
            lambda case: case.request,
            "q_generated-001",
            id="dominio-non-dc",
        ),
        pytest.param(
            lambda case: replace(
                case.ir,
                requests=(Request(case.request.id, "time_constant", case.request.target),),
            ),
            lambda case: Request(case.request.id, "time_constant", case.request.target),
            "q_generated-001",
            id="quantita-non-supportata",
        ),
        pytest.param(
            lambda case: replace(case.ir, nodes=(*case.ir.nodes, "isolato")),
            lambda case: case.request,
            "isolato",
            id="ir-elettricamente-non-valido",
        ),
    ),
)
def test_candidati_rifiutano_chiaramente_lo_scope_p1m0(build_ir, build_request, subject):
    case = case_for_seed(1)

    refusal = enumerate_strategy_candidates(build_ir(case), build_request(case))

    assert isinstance(refusal, Refusal)
    assert refusal.subject == subject


def test_candidati_rifiutano_un_target_assente_anche_se_un_input_corrotto_bypassa_lo_schema():
    case = case_for_seed(1)
    # Un IR normale non puo' contenere una Request senza target: il controllo qui
    # protegge anche una deserializzazione o una mutazione impropria a valle.
    corrupt = replace(case.ir)
    missing = Request(case.request.id, "voltage", "MANCANTE")
    object.__setattr__(corrupt, "requests", (missing,))
    refusal = enumerate_strategy_candidates(corrupt, missing)

    assert isinstance(refusal, Refusal)
    assert refusal.subject == missing.id
    assert "target MANCANTE" in refusal.diagnosis
