"""Corpus e politiche P1-M0: misurano il planner senza mutarlo."""

from __future__ import annotations

import pytest

pytest.importorskip("networkx", reason="corpus topologico disponibile solo nell'extra research")

from lab.fixtures.topology import topology_fingerprint
from lab.fixtures.cases import case_for_seed
from lab.strategy.corpus import build_generated_corpus, deliberate_probes
from lab.strategy.benchmark import simulate_policy
from lab.strategy.policies import POLICIES


def test_corpus_pubblico_contiene_duecento_generati_e_trenta_probe_nominati():
    generated = build_generated_corpus(200)
    probes = deliberate_probes()

    assert len(generated) == 200
    assert len({row.case.case_id for row in generated}) == 200
    assert len({topology_fingerprint(row.case.ir, row.case.request) for row in generated}) >= 60
    assert len(probes) == 30
    assert len({probe.case_id for probe in probes}) == 30
    assert len({topology_fingerprint(probe.ir, probe.request) for probe in probes}) >= 20
    families = {probe.family_id for probe in probes}
    assert {"series", "parallel", "mixed", "supernode", "peripheral"} <= families


def test_politiche_scelgono_solo_candidati_e_current_replica_il_piano_osservato():
    for row in build_generated_corpus(40):
        choices = {name: policy(row.candidates) for name, policy in POLICIES.items()}
        assert all(choice in row.candidates for choice in choices.values())
        assert all(choice.candidate.admissible for choice in choices.values())
        current = choices["current"].candidate
        assert current.technique == row.current_plan.technique
        assert choices["current"].candidate.actions == row.current_plan.actions
        assert POLICIES["current"](tuple(reversed(row.candidates))) == choices["current"]


def test_candidati_e_politiche_non_escludono_il_nodale_quando_esiste_una_riduzione():
    row = next(
        row for row in build_generated_corpus(40)
        if any(candidate.candidate.operation is not None for candidate in row.candidates)
        and any(candidate.candidate.technique == "nodal_analysis" for candidate in row.candidates)
    )

    assert len([candidate for candidate in row.candidates
                if candidate.candidate.technique == "nodal_analysis"]) == 1
    assert POLICIES["direct-nodal"](row.candidates).candidate.technique == "nodal_analysis"
    assert any(
        POLICIES[name](row.candidates).candidate.technique == "nodal_analysis"
        for name in ("target-first", "complexity", "lexicographic")
    )


def test_impronta_distingue_topologie_ma_ignora_i_valori():
    same_topology_other_values = case_for_seed(4)  # seed 0 e 4: stessa famiglia serie
    series = case_for_seed(0)
    parallel = case_for_seed(1)

    assert topology_fingerprint(series.ir, series.request) == topology_fingerprint(
        same_topology_other_values.ir, same_topology_other_values.request)
    assert topology_fingerprint(series.ir, series.request) != topology_fingerprint(
        parallel.ir, parallel.request)


def test_simulazione_offline_e_deterministica_e_conserva_la_certificazione_core():
    for row in build_generated_corpus(12):
        for policy in POLICIES:
            first = simulate_policy(row, policy)
            assert first == simulate_policy(row, policy)
            assert first.final_claim_status == "VERIFIED"
