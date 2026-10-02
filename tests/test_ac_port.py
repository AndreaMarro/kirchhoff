"""Impedenza AC di porta con prova fasoriale e controllo indipendente."""

from fractions import Fraction as F

import pytest

import kirchhoff.domain.port as port_module
from kirchhoff.domain.exact import Cyc12, J
from kirchhoff.domain.ir import IR
from kirchhoff.domain.port import PhasorMagnitude, analyze_ac_port
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi


def test_series_rl_port_has_exact_complex_impedance():
    ir = leggi("@ac 2 rad/s\nR1 a b 3 ohm\nL1 b 0 2 henry")
    result = analyze_ac_port(ir, ("a", "0"))
    assert result.voltage.amount == 0
    assert result.impedance.amount == Cyc12.of(3) + J * Cyc12.of(4)
    assert result.impedance.unit == "ohm"
    assert result.norton_current.amount == 0


def test_parallel_rc_port_inverts_admittance_without_float_approximation():
    ir = leggi("@ac 2 rad/s\nR1 a 0 3 ohm\nC1 a 0 1/2 farad")
    result = analyze_ac_port(ir, ("a", "0"))
    assert result.impedance.amount == Cyc12.of(F(3, 10)) - J * Cyc12.of(F(9, 10))


def test_ac_thevenin_port_preserves_source_phase_and_orientation():
    ir = leggi("@ac 2 rad/s\nV1 x 0 6 volt 90deg\nR1 x a 4 ohm\nR2 a 0 4 ohm")
    forward = analyze_ac_port(ir, ("a", "0"))
    reverse = analyze_ac_port(ir, ("0", "a"))
    assert forward.voltage.amount == J * Cyc12.of(3)
    assert forward.impedance.amount == Cyc12.of(2)
    assert forward.norton_current.amount == J * Cyc12.of(F(3, 2))
    assert reverse.voltage.amount == -forward.voltage.amount
    assert reverse.impedance.amount == forward.impedance.amount


def test_ac_controlled_source_stays_active_after_independent_source_is_off():
    ir = leggi("@ac 2 rad/s\nV1 x 0 6 volt 90deg\nR1 x a 5 ohm\n"
              "R2 a 0 10 ohm\nG1 0 a a 0 1/5 siemens")
    result = analyze_ac_port(ir, ("a", "0"))
    assert result.voltage.amount == J * Cyc12.of(12)
    assert result.impedance.amount == Cyc12.of(10)
    assert result.norton_current.amount == J * Cyc12.of(F(6, 5))


def test_ac_ideal_voltage_source_has_zero_impedance_and_no_finite_norton():
    ir = leggi("@ac 2 rad/s\nV1 a 0 6 volt 0deg\nR1 a 0 3 ohm")
    result = analyze_ac_port(ir, ("a", "0"))
    assert result.voltage.amount == Cyc12.of(6)
    assert result.impedance.amount == 0
    assert result.norton_current is None


def test_port_phasor_carries_exact_value_and_supported_unit():
    with pytest.raises(TypeError, match="Cyc12"):
        PhasorMagnitude(F(1), "volt")
    with pytest.raises(ValueError, match="unita"):
        PhasorMagnitude(Cyc12.of(1), "farad")


def test_probe_identity_collision_does_not_change_ac_port_result():
    ir = leggi("@ac 2 rad/s\nI_port_probe 0 a 1 ampere 0deg\nR1 a 0 2 ohm")
    result = analyze_ac_port(ir, ("a", "0"))
    assert result.voltage.amount == Cyc12.of(2)
    assert result.impedance.amount == Cyc12.of(2)


def test_dangling_ac_branch_and_singular_current_network_are_refused():
    dangling = leggi("@ac 2 rad/s\nR1 a 0 2 ohm\nR2 b 0 4 ohm")
    singular = leggi("@ac 2 rad/s\nI1 a 0 1 ampere 0deg\nI2 0 a 1 ampere 0deg")
    assert analyze_ac_port(dangling, ("a", "0")).cause == "topology"
    assert analyze_ac_port(singular, ("a", "0")).cause == "unsolvable"


def test_ac_tableau_disagreement_blocks_port_claim(monkeypatch):
    ir = leggi("@ac 2 rad/s\nR1 a 0 3 ohm\nC1 a 0 1/2 farad")
    real_tableau = port_module.solve_phasor_tableau

    def corrupted(measured):
        result = real_tableau(measured)
        result["R1"]["current"] += Cyc12.of(1)
        return result

    monkeypatch.setattr(port_module, "solve_phasor_tableau", corrupted)
    assert analyze_ac_port(ir, ("a", "0")).cause == "path_disagreement"


def test_matching_corruption_is_still_rejected_by_ac_residuals(monkeypatch):
    ir = leggi("@ac 2 rad/s\nR1 a 0 3 ohm\nC1 a 0 1/2 farad")
    real_nodal = port_module.solve_phasor
    real_tableau = port_module.solve_phasor_tableau

    def corrupted(real):
        def run(measured):
            result = real(measured)
            result["R1"]["current"] += Cyc12.of(1)
            return result
        return run

    monkeypatch.setattr(port_module, "solve_phasor", corrupted(real_nodal))
    monkeypatch.setattr(port_module, "solve_phasor_tableau", corrupted(real_tableau))
    assert analyze_ac_port(ir, ("a", "0")).cause == "residual"


def test_second_ac_probe_failure_cannot_be_published_as_impedance(monkeypatch):
    ir = leggi("@ac 2 rad/s\nR1 a 0 3 ohm\nC1 a 0 1/2 farad")
    real_measure = port_module._measure_ac

    def second_fails(measured, terminals, amperes, *, off):
        if off:
            return Refusal("unsolvable", "a→0", "operation", "prova interrotta")
        return real_measure(measured, terminals, amperes, off=off)

    monkeypatch.setattr(port_module, "_measure_ac", second_fails)
    assert analyze_ac_port(ir, ("a", "0")).cause == "unsolvable"


def test_dc_and_invalid_port_are_refused_in_ac_service():
    dc = leggi("R1 a 0 3 ohm\nR2 a 0 6 ohm")
    ac = leggi("@ac 2 rad/s\nR1 a 0 3 ohm\nR2 a 0 6 ohm")
    empty = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "a"), (), (), omega=F(2))
    dc_source = leggi("V1 a 0 3 volt\nR1 a 0 6 ohm")
    unsupported = IR("1.0.0", "ac_sinusoidal", "generated", dc_source.nodes,
                     dc_source.components, (), omega=F(2))
    for ir, port in ((dc, ("a", "0")), (ac, ("a", "a")), (ac, ("a", "missing")),
                     (empty, ("a", "0")), (unsupported, ("a", "0"))):
        result = analyze_ac_port(ir, port)
        assert isinstance(result, Refusal)
        assert result.cause == "claim_unsupported"
