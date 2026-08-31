"""P1-FD: applica_passo onora gli operands della PlannedAction."""
from __future__ import annotations

import inspect
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    applica_passo,
    pianifica,
    stato_iniziale,
)
from kirchhoff.domain.didactic.kinds import ANALYTICAL_KINDS, AnalyticalStepKind
from kirchhoff.domain.ir import Component, IR, Request

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str = "R1", quantity: str = "voltage") -> Request:
    return Request("q1", quantity, target)  # type: ignore[arg-type]


def _due_ordinari() -> IR:
    return _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("R3", "resistor", ("a", "b"), F(5), "R3"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
    ))


def _due_supernodi() -> IR:
    return _ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(6), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("V2", "voltage_source_dc", ("c", "d"), F(3), "V2"),
        Component.of("R3", "resistor", ("c", "0"), F(1), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(1), "R4"),
    ))


def _fino_alle_incognite(ir: IR):
    _, d1 = applica_passo(
        "choose_reference", ir, stato_iniziale(NODO), operands=(),
    )
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    return d2


def test_firma_operandi_obbligatori_keyword_only():
    firma = inspect.signature(applica_passo)
    param = firma.parameters["operands"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        applica_passo("choose_reference", _due_ordinari(), stato_iniziale(NODO))


def test_ordinary_explicit_node_non_il_primo():
    ir = _due_ordinari()
    prima = _fino_alle_incognite(ir)
    passo, dopo = applica_passo("write_kcl", ir, prima, operands=("b",))
    assert passo.focused_entities == ("b",)
    assert dopo.equations[0].focus == "b"
    assert dopo.equations[0].focus != "a"


def test_secondo_supernodo_non_il_primo():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    passo, dopo = applica_passo(
        "write_kcl", ir, prima, operands=("V2", "c", "d"),
    )
    assert passo.kind == "write_kcl"
    assert passo.focused_entities == ("V2", "c", "d")
    assert dopo.equations[0].kind == "kcl"
    assert dopo.equations[0].focus == "V2"
    assert dopo.equations[0].focus != "V1"


def test_secondo_vincolo_di_tensione():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    passo, dopo = applica_passo(
        "write_voltage_constraint", ir, prima, operands=("V2",),
    )
    assert passo.kind == "write_voltage_constraint"
    assert passo.focused_entities == ("V2",)
    assert dopo.equations[0].kind == "voltage_constraint"
    assert dopo.equations[0].focus == "V2"
    assert dopo.equations[0].focus != "V1"


def test_operandi_supernodo_corrotti_pq_invertiti():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match=r"non coincidono.*\('V1', 'a', 'b'\)"):
        applica_passo("write_kcl", ir, prima, operands=("V1", "b", "a"))


def test_source_id_inesistente():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match="NOPE"):
        applica_passo("write_kcl", ir, prima, operands=("NOPE", "a", "b"))


def test_arita_ordinaria_illegale():
    ir = _due_ordinari()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match=r"kind 'write_kcl'.*operands ricevuti \(\)"):
        applica_passo("write_kcl", ir, prima, operands=())
    with pytest.raises(ValueError, match=r"operands ricevuti \('a', 'b'\)"):
        applica_passo("write_kcl", ir, prima, operands=("a", "b"))


def test_arita_supernodo_illegale():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match=r"operands ricevuti \('V1', 'a', 'b', 'extra'\)"):
        applica_passo(
            "write_kcl", ir, prima, operands=("V1", "a", "b", "extra"),
        )


def test_arita_vincolo_illegale():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match=r"kind 'write_voltage_constraint'.*\(\)"):
        applica_passo("write_voltage_constraint", ir, prima, operands=())
    with pytest.raises(ValueError, match=r"operands ricevuti \('V1', 'extra'\)"):
        applica_passo(
            "write_voltage_constraint", ir, prima, operands=("V1", "extra"),
        )


def test_kind_senza_operandi_rifiuta_extra():
    ir = _due_ordinari()
    d0 = stato_iniziale(NODO)
    with pytest.raises(ValueError, match=r"kind 'choose_reference'.*\('extra',\)"):
        applica_passo("choose_reference", ir, d0, operands=("extra",))
    _, d1 = applica_passo("choose_reference", ir, d0, operands=())
    with pytest.raises(ValueError, match=r"kind 'define_nodal_unknowns'.*\('extra',\)"):
        applica_passo("define_nodal_unknowns", ir, d1, operands=("extra",))
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    assert any(v.role == "unknown" for v in d2.variables)


def test_ogni_azione_del_piano_e_accettata_dalla_grammatica():
    ir = _due_supernodi()
    piano = pianifica(ir, _req("R1"))
    assert piano.technique == "nodal_analysis"
    kinds_analitici = set(ANALYTICAL_KINDS)
    stato = stato_iniziale(NODO)
    accettate = []
    for azione in piano.actions:
        if azione.kind not in kinds_analitici:
            continue
        passo, stato = applica_passo(
            azione.kind, ir, stato, operands=azione.operands,
        )
        accettate.append((azione.kind, azione.operands, passo.focused_entities))
    assert [k for k, _, _ in accettate] == [
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_voltage_constraint",
        "write_kcl",
        "write_voltage_constraint",
    ]
    assert accettate[2][1] == ("V1", "a", "b")
    assert accettate[4][1] == ("V2", "c", "d")


def test_replay_deterministico_ordine_pianificato():
    ir = _due_supernodi()
    piano = pianifica(ir, _req("R1"))
    stato = stato_iniziale(NODO)
    foci = []
    for azione in piano.actions:
        if azione.kind not in ANALYTICAL_KINDS:
            continue
        _, stato = applica_passo(
            azione.kind, ir, stato, operands=azione.operands,
        )
        if azione.kind in {"write_kcl", "write_voltage_constraint"}:
            foci.append((stato.equations[-1].kind, stato.equations[-1].focus))
    assert foci == [
        ("kcl", "V1"),
        ("voltage_constraint", "V1"),
        ("kcl", "V2"),
        ("voltage_constraint", "V2"),
    ]
    assert [eq.focus for eq in stato.equations] == ["V1", "V1", "V2", "V2"]


def test_mutation_guard_non_prende_il_primo():
    ir = _due_supernodi()
    prima = _fino_alle_incognite(ir)
    _, dopo_kcl = applica_passo(
        "write_kcl", ir, prima, operands=("V2", "c", "d"),
    )
    assert dopo_kcl.equations[0].focus == "V2"
    _, dopo_v = applica_passo(
        "write_voltage_constraint", ir, prima, operands=("V2",),
    )
    assert dopo_v.equations[0].focus == "V2"
    ir_ord = _due_ordinari()
    prima_ord = _fino_alle_incognite(ir_ord)
    _, dopo_b = applica_passo("write_kcl", ir_ord, prima_ord, operands=("b",))
    assert dopo_b.equations[0].focus == "b"


def test_kind_analitici_invariati():
    assert ANALYTICAL_KINDS == frozenset({
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_voltage_constraint",
    })
    assert set(AnalyticalStepKind.__args__) == ANALYTICAL_KINDS
