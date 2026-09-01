"""Planner, piano e capability: decisioni reali, non mock."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import json

import pytest

from kirchhoff.domain.didactic import (
    DidacticPlan,
    PLAN_SCHEMA_VERSION,
    PROFILE,
    PlanReason,
    PlannedAction,
    pianifica,
)
from kirchhoff.domain.didactic.capabilities import (
    DIDACTIC_NODAL_COMPONENT_TYPES,
    contribuisce,
    nodale_disponibile,
    riduzioni_che_contribuiscono,
    riduzioni_eseguibili,
)
from kirchhoff.domain.didactic.capabilities import effetto_osservazione
from kirchhoff.domain.didactic.observation import ObservationContract
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import SUPPORTED, implemented
from kirchhoff.domain.transform.applicability import ExecutableTransform
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve

from test_percorso_b import CORRENTE, PARALLELO, PARTITORE, PONTE

F = Fraction
GOLDEN = Path(__file__).resolve().parent / "golden" / "ponte_dc.netlist"


def _req(target: str, quantity: str = "current", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _ir(nodes, comps, domain="dc") -> IR:
    return IR("1.0.0", domain, "netlist", tuple(nodes), tuple(comps), ())


def test_plan_reason_canonicalizza_i_nomi():
    r = PlanReason(False, False, False, False, ("zzz", "partitore_di_tensione"))
    assert r.unimplemented_supported_names == ("partitore_di_tensione", "zzz")


def test_piano_contratti_e_json_deterministico():
    ragione = PlanReason(True, True, True, False, ("b", "a"))
    with pytest.raises(ValueError, match="senza kind"):
        PlannedAction("", ("R1",))
    azione = PlannedAction("serie", ["R2", "R1"])  # type: ignore[arg-type]
    assert azione.operands == ("R2", "R1")
    with pytest.raises(ValueError, match="schema_version"):
        DidacticPlan("x", PROFILE, "q1", "nodal_analysis", ragione, (azione,))
    with pytest.raises(ValueError, match="profile"):
        DidacticPlan(PLAN_SCHEMA_VERSION, "x", "q1", "nodal_analysis", ragione, (azione,))
    with pytest.raises(ValueError, match="senza riferimento"):
        DidacticPlan(PLAN_SCHEMA_VERSION, PROFILE, "", "nodal_analysis", ragione, (azione,))
    with pytest.raises(ValueError, match="fuori dal vocabolario"):
        DidacticPlan(PLAN_SCHEMA_VERSION, PROFILE, "q1", "thevenin", ragione, (azione,))
    with pytest.raises(TypeError, match="PlanReason"):
        DidacticPlan(PLAN_SCHEMA_VERSION, PROFILE, "q1", "nodal_analysis", "x", (azione,))
    with pytest.raises(TypeError, match="PlannedAction"):
        DidacticPlan(PLAN_SCHEMA_VERSION, PROFILE, "q1", "nodal_analysis", ragione, ("serie",))
    with pytest.raises(ValueError, match="senza azioni"):
        DidacticPlan(PLAN_SCHEMA_VERSION, PROFILE, "q1", "nodal_analysis", ragione, ())
    piano = DidacticPlan(
        PLAN_SCHEMA_VERSION, PROFILE, "q1", "nodal_analysis", ragione,
        (PlannedAction("choose_reference", ()),),
    )
    assert piano.canonical_json() == piano.canonical_json()
    altro = DidacticPlan(
        PLAN_SCHEMA_VERSION, PROFILE, "q1", "nodal_analysis", ragione,
        (PlannedAction("choose_reference", ()),),
    )
    assert piano.canonical_json() == altro.canonical_json()
    blob = piano.canonical_json()
    assert '"technique":"nodal_analysis"' in blob
    assert '"choose_reference"' in blob
    assert blob.startswith("{") and blob.endswith("}")
    parsed = json.loads(blob)
    assert list(parsed) == sorted(parsed)
    assert parsed["actions"][0]["kind"] == "choose_reference"


def test_planner_ir_invalido_e_target_assente():
    illecito = _ir(("0", "n1", "n8", "n9"), (
        Component.of("V1", "voltage_source_dc", ("n1", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("n1", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("n8", "n9"), F(10), "R2"),
        Component.of("R3", "resistor", ("n8", "n9"), F(20), "R3"),
    ))
    esito = pianifica(illecito, _req("R1"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "topology"
    assert isinstance(pianifica(leggi(PONTE), _req("Rx")), Refusal)


def test_planner_sceglie_riduzione_certificata_quando_contribuisce():
    piano = pianifica(leggi(PARTITORE), _req("R2", "current"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "certified_transform_path"
    assert piano.actions[0].kind == "serie"
    assert piano.reason.contributing_certified_reduction
    assert "partitore_di_tensione" in SUPPORTED
    assert "partitore_di_tensione" not in implemented()
    assert "partitore_di_tensione" in piano.reason.unimplemented_supported_names


def test_planner_nodale_quando_le_riduzioni_non_contribuiscono():
    ir = leggi(GOLDEN.read_text())
    assert riduzioni_eseguibili(ir) == ()
    piano = pianifica(ir, ir.requests[0])
    assert piano.technique == "nodal_analysis"
    assert piano.canonical_json() == pianifica(ir, ir.requests[0]).canonical_json()


def test_planner_nodale_su_ponte_e_azioni():
    ir = leggi(PONTE)
    piano = pianifica(ir, _req("R4", "current"))
    assert piano.technique == "nodal_analysis"
    kinds = [a.kind for a in piano.actions]
    assert kinds[0] == "choose_reference"
    assert "define_nodal_unknowns" in kinds
    assert "write_kcl" in kinds
    kcl = next(a for a in piano.actions if a.kind == "write_kcl")
    assert kcl.operands == ("a",)


def test_azioni_nodali_senza_incognite_non_definiscono():
    massa = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    kinds = [a.kind for a in _azioni_nodali(massa)]
    assert kinds[0] == "choose_reference"
    assert "define_nodal_unknowns" not in kinds
    assert "write_kcl" not in kinds


def test_planner_rifiuta_quando_niente_e_eseguibile():
    ir = _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("b", "c"), F(3), "V2"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "0"), F(10), "R2"),
    ))
    kernel = resolve(replace(ir, requests=(_req("R1", "voltage"),)))
    assert isinstance(kernel, Solved)
    esito = pianifica(ir, _req("R1", "voltage"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert not nodale_disponibile(ir, "voltage")


def test_nodale_capability_boundaries():
    assert "current_source_dc" in DIDACTIC_NODAL_COMPONENT_TYPES
    ponte = leggi(PONTE)
    assert nodale_disponibile(ponte, "voltage")
    assert nodale_disponibile(ponte, "current")
    assert not nodale_disponibile(replace(ponte, domain="ac"), "voltage")
    assert not nodale_disponibile(ponte, "time_constant")
    vuoto = IR("1.0.0", "dc", "netlist", ("0",), (), ())
    assert not nodale_disponibile(vuoto, "voltage")
    assert nodale_disponibile(leggi(CORRENTE), "current")
    assert nodale_disponibile(leggi(CORRENTE), "voltage")
    vcvs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "E1", "voltage_controlled_voltage_source", ("C", "0"),
            F(2), "E1", control_nodes=("A", "0"),
        ),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    assert isinstance(resolve(replace(vcvs, requests=(_req("R3", "voltage"),))), Solved)
    assert not nodale_disponibile(vcvs, "voltage")
    assert isinstance(pianifica(vcvs, _req("R3", "voltage")), Refusal)
    flottante = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert isinstance(resolve(replace(flottante, requests=(_req("R1", "voltage"),))), Solved)
    assert nodale_disponibile(flottante, "voltage")


def test_contribuisce_e_ordinamento_riduzioni(monkeypatch):
    serie = ExecutableTransform("serie", "R1", "R2")
    par = ExecutableTransform("parallelo", "R1", "R2")
    part = leggi(PARTITORE)
    assert contribuisce(part, serie, ObservationContract("q1", "R1", "current"))
    assert not contribuisce(part, serie, ObservationContract("q1", "R1", "voltage"))
    par_ir = leggi(PARALLELO)
    assert contribuisce(par_ir, par, ObservationContract("q1", "R1", "voltage"))
    assert not contribuisce(par_ir, par, ObservationContract("q1", "R1", "current"))
    utili_i = riduzioni_che_contribuiscono(
        part, ObservationContract("q1", "R1", "current"))
    utili_v = riduzioni_che_contribuiscono(
        part, ObservationContract("q1", "R1", "voltage"))
    assert utili_i and all(r.operation == "serie" for r in utili_i)
    assert not utili_v
    elenco = riduzioni_eseguibili(part)
    assert elenco == tuple(sorted(elenco))
    assert riduzioni_eseguibili(par_ir)
    assert all(r.operation == "parallelo" for r in riduzioni_eseguibili(par_ir))

    monkeypatch.setattr(
        "kirchhoff.domain.didactic.capabilities.transform",
        lambda *_: Refusal("unsolvable", "q1", "request", "rifiuto sintetico"),
    )
    assert effetto_osservazione(
        part, serie, ObservationContract("q1", "R1", "current")).kind == "blocked"
