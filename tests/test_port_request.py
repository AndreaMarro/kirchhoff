"""La domanda di porta conserva morsetti e orientazione senza un componente fittizio."""

from fractions import Fraction

import pytest

import kirchhoff.pipeline.lesson as lesson_module
from kirchhoff.domain.ir import PortRequest, canonicalize
from kirchhoff.domain.port import analyze_dc_port
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import validate
from kirchhoff.pipeline.circuitikz import export_circuitikz
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.pipeline.lesson_svg import schematic
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import resolve
from kirchhoff.pipeline.spice import export_spice, import_spice


BASE = "R1 a 0 3 ohm\nR2 a 0 6 ohm"


def test_dc_port_question_is_typed_and_canonicalized_without_fake_component():
    ir = leggi(BASE + "\n? resistance a 0")
    question = ir.requests[0]
    assert isinstance(question, PortRequest)
    assert question.quantity == "equivalent_resistance"
    assert question.port == ("a", "0")
    assert question.id == "q1"
    assert canonicalize(ir).requests == (question,)
    assert {c.id for c in ir.components} == {"R1", "R2"}
    assert leggi(BASE + "\n? resistance 0 a").requests[0].port == ("0", "a")


def test_port_question_rejects_same_unknown_or_missing_terminal():
    with pytest.raises(ValueError, match="distinti"):
        leggi(BASE + "\n? resistance a a")
    with pytest.raises(ValueError, match="sconosciuto"):
        leggi(BASE + "\n? resistance a missing")
    with pytest.raises(ValueError, match="domanda"):
        leggi(BASE + "\n? resistance a")


def test_port_request_schema_and_validator_reject_invalid_terminal_metadata():
    with pytest.raises(ValueError, match="sconosciuta"):
        PortRequest("q", "power", ("a", "0"))
    with pytest.raises(TypeError, match="coppia ordinata"):
        PortRequest("q", "equivalent_resistance", ["a", "0"])
    with pytest.raises(ValueError, match="distinti"):
        PortRequest("q", "equivalent_resistance", ("a",))
    with pytest.raises(TypeError, match="nomi non vuoti"):
        PortRequest("q", "equivalent_resistance", ("a", 0))
    ir = leggi(BASE + "\n? resistance a 0")
    object.__setattr__(ir, "requests", (PortRequest("q", "equivalent_resistance", ("a", "missing")),))
    refusal = validate(ir)
    assert isinstance(refusal, Refusal) and refusal.cause == "topology"


def test_port_question_fails_closed_in_component_only_proof_path():
    ir = leggi(BASE + "\n? resistance a 0")
    assert isinstance(resolve(ir, source_sha="a" * 40), Refusal)


def test_passive_port_lesson_uses_exact_test_current_and_returns_to_original():
    lesson = create_lesson(BASE + "\n? resistance a 0", source_sha="a" * 40)
    assert lesson["outcome"] == "solved"
    assert lesson["answer"] == dict(exact="2", decimal="2", unit="Ω", reference="a → 0")
    assert lesson["netlist"] == BASE + "\n? resistance a 0"
    assert lesson["method"] == "test_current"
    assert lesson["verification"]["product_verified"] is False
    assert lesson["verification"]["electrical_claim"] != "VERIFIED"
    assert len(lesson["steps"]) >= 4
    assert "1 A" in " ".join(str(step["equations"]) for step in lesson["steps"])
    assert lesson["steps"][-1]["svg"] == lesson["original"]
    assert export_pdf(lesson).startswith(b"%PDF")


def test_source_deactivation_and_port_orientation_match_independent_kernel():
    source = "V1 a 0 12 volt\nR1 a 0 3 ohm\nR2 a 0 6 ohm"
    for port in (("a", "0"), ("0", "a")):
        netlist = source + f"\n? resistance {port[0]} {port[1]}"
        kernel = analyze_dc_port(leggi(netlist), port)
        assert not isinstance(kernel, Refusal)
        lesson = create_lesson(netlist, source_sha="a" * 40)
        assert lesson["outcome"] == "solved"
        assert Fraction(lesson["answer"]["exact"]) == kernel.resistance.amount
        assert "12" in lesson["original"]
        assert "0" in lesson["steps"][2]["svg"]


def test_wrong_test_probe_cannot_publish_a_port_resistance(monkeypatch):
    real_probe = lesson_module._probe

    def corrupted(ir, port, amperes, *, off):
        return real_probe(ir, port, Fraction(0) if off else amperes, off=off)

    monkeypatch.setattr(lesson_module, "_probe", corrupted)
    with pytest.raises(ValueError, match="non coincidono"):
        create_lesson(BASE + "\n? resistance a 0", source_sha="a" * 40)


def test_unsupported_method_and_reactive_port_do_not_publish_a_value():
    with pytest.raises(ValueError, match="Corrente di prova"):
        create_lesson(BASE + "\n? resistance a 0", "millman", source_sha="a" * 40)
    with pytest.raises(ValueError, match="richiede una domanda"):
        create_lesson(BASE + "\n? voltage R1", "test_current", source_sha="a" * 40)
    reactive = create_lesson("C1 a 0 1 farad\nR1 a 0 3 ohm\n? resistance a 0", source_sha="a" * 40)
    assert reactive["outcome"] == "refusal"
    assert reactive["cause"] == "claim_unsupported"


def test_port_renderers_preserve_the_original_two_terminal_question():
    ir = leggi(BASE + "\n? resistance a 0")
    assert schematic(ir).startswith("<svg")
    tex = export_circuitikz(ir)
    assert "resistenza vista" in tex and "\\texttt{a}" in tex
    spice = export_spice(ir)
    assert "* KIRCHHOFF_REQUEST resistance a 0" in spice
    assert leggi(import_spice(spice)).requests == ir.requests


def test_unchanged_component_request_remains_a_component_request():
    ir = leggi(BASE + "\n? voltage R1")
    assert not isinstance(ir.requests[0], PortRequest)
    assert ir.requests[0].target == "R1"
