"""Regressione del costruttore nodale condiviso, senza cambiare la policy."""

from __future__ import annotations

from lab.fixtures.cases import generated_cases, topology_diverse_cases
from lab.strategy.corpus import deliberate_probes

from kirchhoff.domain.didactic.nodal_plan import build_nodal_actions
from kirchhoff.domain.didactic.planner import pianifica


def test_azioni_nodali_condivise_restano_identiche_su_generati_e_probe():
    rows = (*generated_cases(200), *topology_diverse_cases(200), *deliberate_probes())
    nodal = [pianifica(case.ir, case.request) for case in rows]

    for case, plan in zip(rows, nodal, strict=True):
        if plan.technique == "nodal_analysis":
            assert plan.actions == build_nodal_actions(case.ir), case.case_id


def test_snapshot_del_planner_congela_trasformazione_kcl_e_supernodo():
    cases = {case.case_id: case for case in (*generated_cases(4), *deliberate_probes())}

    assert pianifica(cases["generated-000"].ir, cases["generated-000"].request).canonical_json() == (
        '{"actions":[{"kind":"choose_reference","operands":[]},{"kind":"define_nodal_unknowns","operands":[]},{"kind":"write_kcl","operands":["a"]}],"profile":"student-dc-v0.1","reason":{"contributing_certified_reduction":false,"exact_solver_available":true,"request_reachable":true,"topology_reducible":false,"unimplemented_supported_names":["partitore_di_tensione"]},"request_id":"q_generated-000","schema_version":"didactic-plan.v0.2","technique":"nodal_analysis"}'
    )
    assert pianifica(cases["generated-001"].ir, cases["generated-001"].request).canonical_json() == (
        '{"actions":[{"kind":"parallelo","operands":["R1","R2"]}],"profile":"student-dc-v0.1","reason":{"contributing_certified_reduction":true,"exact_solver_available":true,"request_reachable":true,"topology_reducible":true,"unimplemented_supported_names":["partitore_di_tensione"]},"request_id":"q_generated-001","schema_version":"didactic-plan.v0.2","technique":"certified_transform_path"}'
    )
    assert pianifica(cases["generated-003"].ir, cases["generated-003"].request).canonical_json() == (
        '{"actions":[{"kind":"choose_reference","operands":[]},{"kind":"define_nodal_unknowns","operands":[]},{"kind":"write_kcl","operands":["V2","a","b"]},{"kind":"write_voltage_constraint","operands":["V2"]}],"profile":"student-dc-v0.1","reason":{"contributing_certified_reduction":false,"exact_solver_available":true,"request_reachable":true,"topology_reducible":false,"unimplemented_supported_names":["partitore_di_tensione"]},"request_id":"q_generated-003","schema_version":"didactic-plan.v0.2","technique":"nodal_analysis"}'
    )
    assert pianifica(cases["probe-00-target-in-series-pair"].ir, cases["probe-00-target-in-series-pair"].request).canonical_json() == (
        '{"actions":[{"kind":"serie","operands":["R1","R2"]}],"profile":"student-dc-v0.1","reason":{"contributing_certified_reduction":true,"exact_solver_available":true,"request_reachable":true,"topology_reducible":true,"unimplemented_supported_names":["partitore_di_tensione"]},"request_id":"q_probe_00","schema_version":"didactic-plan.v0.2","technique":"certified_transform_path"}'
    )
