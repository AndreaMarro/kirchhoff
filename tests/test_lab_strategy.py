"""Corpus e politiche P1-M0: misurano il planner senza mutarlo."""

from __future__ import annotations

import pytest

pytest.importorskip("networkx", reason="corpus topologico disponibile solo nell'extra research")

from lab.strategy.corpus import build_generated_corpus, deliberate_probes
from lab.strategy.benchmark import simulate_policy
from lab.strategy.policies import POLICIES


def test_corpus_pubblico_contiene_duecento_generati_e_trenta_probe_nominati():
    generated = build_generated_corpus(200)
    probes = deliberate_probes()

    assert len(generated) == 200
    assert len({row.case.case_id for row in generated}) == 200
    assert len(probes) == 30
    assert len({probe.case_id for probe in probes}) == 30
    families = {probe.family_id for probe in probes}
    assert {"series", "parallel", "mixed", "supernode", "peripheral"} <= families


def test_politiche_scelgono_solo_candidati_e_current_replica_il_piano_osservato():
    for row in build_generated_corpus(40):
        choices = {name: policy(row.candidates) for name, policy in POLICIES.items()}
        assert all(choice in row.candidates for choice in choices.values())
        assert all(choice.candidate.admissible for choice in choices.values())
        current = choices["current"].candidate
        assert current.technique == row.current_plan.technique
        if current.operation is not None:
            assert current.operation == row.current_plan.actions[0].kind


def test_simulazione_offline_e_deterministica_e_conserva_la_certificazione_core():
    for row in build_generated_corpus(12):
        for policy in POLICIES:
            first = simulate_policy(row, policy)
            assert first == simulate_policy(row, policy)
            assert first.final_claim_status == "VERIFIED"
