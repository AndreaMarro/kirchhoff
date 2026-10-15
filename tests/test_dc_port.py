"""Gli equivalenti di porta spengono solo le sorgenti indipendenti."""

from dataclasses import replace
from fractions import Fraction as F

import kirchhoff.domain.port as port_module
from kirchhoff.domain.ir import IR, Magnitude, Provenance
from kirchhoff.domain.port import analyze_dc_port
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi


def test_passive_port_uses_one_ampere_without_inventing_a_source_in_the_answer():
    ir = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    result = analyze_dc_port(ir, ("a", "0"))
    assert result.voltage == Magnitude(F(0), "volt")
    assert result.resistance == Magnitude(F(2), "ohm")
    assert result.norton_current == Magnitude(F(0), "ampere")
    assert analyze_dc_port(replace(ir, domain="dc_resistive"), ("a", "0")) == result
    assert analyze_dc_port(replace(ir, components=tuple(reversed(ir.components))), ("a", "0")) == result


def test_image_component_regions_do_not_break_generated_dc_port_probes():
    netlist = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    region = Provenance(F(1, 10), F(1, 10), F(1, 5), F(1, 5))
    image = replace(netlist, source_kind="image",
                    components=tuple(replace(c, provenance=region) for c in netlist.components))
    assert analyze_dc_port(image, ("a", "0")) == analyze_dc_port(netlist, ("a", "0"))
    assert all(c.provenance == region for c in image.components)


def test_port_equivalent_extinguishes_independent_voltage_sources():
    ir = leggi("V1 x 0 12 volt\nR1 x a 4 ohm\nR2 a 0 4 ohm")
    forward = analyze_dc_port(ir, ("a", "0"))
    reverse = analyze_dc_port(ir, ("0", "a"))
    assert (forward.voltage.amount, forward.resistance.amount,
            forward.norton_current.amount) == (F(6), F(2), F(3))
    assert (reverse.voltage.amount, reverse.resistance.amount,
            reverse.norton_current.amount) == (-F(6), F(2), -F(3))


def test_port_equivalent_extinguishes_independent_current_sources():
    ir = leggi("I1 0 a 2 ampere\nR1 a 0 3 ohm")
    result = analyze_dc_port(ir, ("a", "0"))
    assert result.voltage.amount == 6
    assert result.resistance.amount == 3


def test_controlled_current_source_remains_active_during_port_test():
    ir = leggi("V1 x 0 10 volt\nR1 x a 5 ohm\nR2 a 0 10 ohm\n"
              "G1 0 a a 0 1/5 siemens")
    result = analyze_dc_port(ir, ("a", "0"))
    assert result.voltage.amount == 20
    assert result.resistance.amount == 10
    assert result.norton_current.amount == 2


def test_zero_resistance_has_no_finite_norton_current():
    ir = leggi("V1 a 0 9 volt\nR1 a 0 3 ohm")
    result = analyze_dc_port(ir, ("a", "0"))
    assert result.voltage.amount == 9
    assert result.resistance.amount == 0
    assert result.norton_current is None


def test_probe_does_not_reuse_an_existing_component_identity():
    ir = leggi("I_port_probe 0 a 1 ampere\nR1 a 0 2 ohm")
    result = analyze_dc_port(ir, ("a", "0"))
    assert result.voltage.amount == 2
    assert result.resistance.amount == 2


def test_dangling_branch_and_singular_current_network_are_refused():
    dangling = leggi("R1 a 0 2 ohm\nR2 b 0 4 ohm")
    singular = leggi("I1 a 0 1 ampere\nI2 0 a 1 ampere")
    assert analyze_dc_port(dangling, ("a", "0")).cause == "topology"
    assert analyze_dc_port(singular, ("a", "0")).cause == "unsolvable"


def test_independent_path_disagreement_blocks_port_claim(monkeypatch):
    ir = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    real_tableau = port_module.solve_dc_tableau

    def corrupted(measured):
        result = real_tableau(measured)
        result["R1"]["current"] += F(1)
        return result

    monkeypatch.setattr(port_module, "solve_dc_tableau", corrupted)
    refusal = analyze_dc_port(ir, ("a", "0"))
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "path_disagreement"


def test_shared_wrong_branch_state_is_caught_by_residual_check(monkeypatch):
    ir = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    real_nodal = port_module.solve_dc
    real_tableau = port_module.solve_dc_tableau

    def corrupted(real):
        def run(measured):
            result = real(measured)
            result["R1"]["current"] += F(1)
            return result
        return run

    monkeypatch.setattr(port_module, "solve_dc", corrupted(real_nodal))
    monkeypatch.setattr(port_module, "solve_dc_tableau", corrupted(real_tableau))
    refusal = analyze_dc_port(ir, ("a", "0"))
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "residual"


def test_second_probe_failure_cannot_be_reported_as_a_resistance(monkeypatch):
    ir = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    real_measure = port_module._measure

    def second_fails(measured, terminals, amperes, *, off):
        if off:
            return Refusal("unsolvable", "a→0", "operation", "prova interrotta")
        return real_measure(measured, terminals, amperes, off=off)

    monkeypatch.setattr(port_module, "_measure", second_fails)
    assert analyze_dc_port(ir, ("a", "0")).cause == "unsolvable"


def test_invalid_or_unserved_port_is_a_typed_refusal():
    dc = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    ac = leggi("@ac 2 rad/s\nV1 a 0 3 volt 0deg\nR1 a 0 3 ohm")
    empty = IR("1.0.0", "dc", "generated", ("0", "a"), (), ())
    reactive = leggi("C1 a 0 1 farad\nR1 a 0 3 ohm")
    for ir, port in ((dc, ("a", "a")), (dc, ("a", "missing")),
                     (ac, ("a", "0")), (empty, ("a", "0")),
                     (reactive, ("a", "0"))):
        refusal = analyze_dc_port(ir, port)
        assert isinstance(refusal, Refusal)
        assert refusal.cause == "claim_unsupported"
