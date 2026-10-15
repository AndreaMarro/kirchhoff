"""Y AC di due porte: due eccitazioni esatte, correnti orientate, controllate attive."""

from dataclasses import replace
from fractions import Fraction as F

import pytest

import kirchhoff.domain.two_port as two_port_module
from kirchhoff.domain.exact import Cyc12, J
from kirchhoff.domain.ir import Provenance
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.two_port import (
    ACAdmittanceMatrix, admittance_to_impedance, analyze_ac_y_matrix,
)
from kirchhoff.pipeline.netlist import leggi


BASE = ("@ac 2 rad/s\nR1 a 0 3 ohm\nR2 b 0 3 ohm\n"
        "R3 a b 3 ohm")
PORTS = (("a", "0"), ("b", "0"))


def test_exact_symmetric_y_matrix_with_oriented_port_currents():
    ir = leggi(BASE)
    result = analyze_ac_y_matrix(ir, PORTS)
    assert result.unit == "siemens"
    assert result.omega == F(2)
    assert result.entries == ((Cyc12.of(F(2, 3)), Cyc12.of(-F(1, 3))),
                              (Cyc12.of(-F(1, 3)), Cyc12.of(F(2, 3))))
    assert analyze_ac_y_matrix(replace(ir, components=tuple(reversed(ir.components))),
                               PORTS) == result


def test_image_component_regions_do_not_break_generated_two_port_probes():
    netlist = leggi(BASE)
    region = Provenance(F(1, 10), F(1, 10), F(1, 5), F(1, 5))
    image = replace(netlist, source_kind="image",
                    components=tuple(replace(c, provenance=region) for c in netlist.components))
    assert analyze_ac_y_matrix(image, PORTS) == analyze_ac_y_matrix(netlist, PORTS)
    assert all(c.provenance == region for c in image.components)


def test_y_matrix_cannot_lie_about_units_or_embed_rounded_entries():
    result = analyze_ac_y_matrix(leggi(BASE), PORTS)
    with pytest.raises(ValueError, match="siemens"):
        replace(result, unit="ohm")
    with pytest.raises(TypeError, match="Cyc12"):
        replace(result, entries=((F(1), result.entries[0][1]), result.entries[1]))


def test_exact_y_to_z_conversion_preserves_ports_and_unit():
    admittance = analyze_ac_y_matrix(leggi(BASE), PORTS)
    impedance = admittance_to_impedance(admittance)
    assert impedance.unit == "ohm"
    assert impedance.ports == PORTS
    assert impedance.omega == F(2)
    assert impedance.entries == ((Cyc12.of(2), Cyc12.of(1)),
                                 (Cyc12.of(1), Cyc12.of(2)))
    for i in range(2):
        for j in range(2):
            assert sum((admittance.entries[i][k] * impedance.entries[k][j]
                        for k in range(2)), Cyc12.of(0)) == int(i == j)


def test_supplied_nonreciprocal_reactive_y_converts_exactly():
    admittance = ACAdmittanceMatrix(
        PORTS, F(2), ((Cyc12.of(1) + J, Cyc12.of(2)),
                      (Cyc12.of(3), Cyc12.of(4) - J)))
    impedance = admittance_to_impedance(admittance)
    for i in range(2):
        for j in range(2):
            assert sum((admittance.entries[i][k] * impedance.entries[k][j]
                        for k in range(2)), Cyc12.of(0)) == int(i == j)
    assert impedance.entries[0][1] != impedance.entries[1][0]


def test_singular_y_keeps_its_valid_representation_and_refuses_only_z():
    admittance = ACAdmittanceMatrix(
        PORTS, F(2), ((Cyc12.of(1), Cyc12.of(1)),
                      (Cyc12.of(1), Cyc12.of(1))))
    refusal = admittance_to_impedance(admittance)
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "claim_unsupported"
    assert admittance.entries[0][0] == Cyc12.of(1)


def test_two_port_matrix_rejects_wrong_shape_frequency_or_impedance_unit():
    admittance = analyze_ac_y_matrix(leggi(BASE), PORTS)
    with pytest.raises(ValueError, match="2×2"):
        replace(admittance, entries=((Cyc12.of(1),), (Cyc12.of(1),)))
    with pytest.raises(ValueError, match="positiva"):
        replace(admittance, omega=F(0))
    with pytest.raises(ValueError, match="coppie orientate"):
        replace(admittance, ports=(("a", "0"), ("0", "a")))
    impedance = admittance_to_impedance(admittance)
    with pytest.raises(ValueError, match="ohm"):
        replace(impedance, unit="siemens")


def test_y_to_z_requires_a_typed_y_matrix():
    with pytest.raises(TypeError, match="tipizzata"):
        admittance_to_impedance(None)


def test_corrupted_inverse_fails_exact_matrix_identity(monkeypatch):
    admittance = analyze_ac_y_matrix(leggi(BASE), PORTS)
    monkeypatch.setattr(Cyc12, "__truediv__", lambda _self, _other: Cyc12.of(0))
    refusal = admittance_to_impedance(admittance)
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "residual"


def test_reversing_one_port_changes_both_off_diagonal_signs():
    forward = analyze_ac_y_matrix(leggi(BASE), PORTS).entries
    reverse = analyze_ac_y_matrix(leggi(BASE), (("0", "a"), ("b", "0"))).entries
    assert reverse == ((forward[0][0], -forward[0][1]),
                       (-forward[1][0], forward[1][1]))


def test_controlled_source_can_make_the_y_matrix_nonreciprocal():
    ir = leggi(BASE + "\nG1 a 0 b 0 1/2 siemens")
    result = analyze_ac_y_matrix(ir, PORTS)
    assert result.entries[0][1] == Cyc12.of(F(1, 6))
    assert result.entries[1][0] == Cyc12.of(-F(1, 3))


def test_reactive_admittance_is_exactly_in_the_diagonal():
    ir = leggi(BASE + "\nC1 a 0 1/2 farad")
    result = analyze_ac_y_matrix(ir, PORTS)
    assert result.entries[0][0] == Cyc12.of(F(2, 3)) + J
    assert result.entries[0][1] == Cyc12.of(-F(1, 3))


def test_independent_ac_source_is_extinguished_for_all_matrix_columns():
    ir = leggi(BASE + "\nV1 c 0 6 volt 90deg\nR4 c a 3 ohm")
    result = analyze_ac_y_matrix(ir, PORTS)
    assert result.entries[0][0] == Cyc12.of(1)
    assert result.entries[0][1] == Cyc12.of(-F(1, 3))


def test_probe_identity_collision_preserves_the_matrix():
    ir = leggi(BASE)
    renamed = replace(ir, components=(replace(ir.components[0], id="V_port_probe_1"),
                                      *ir.components[1:]))
    assert analyze_ac_y_matrix(renamed, PORTS).entries == analyze_ac_y_matrix(ir, PORTS).entries


def test_balanced_current_only_island_is_singular_even_with_port_voltages():
    ir = leggi(BASE + "\nI1 x 0 1 ampere 0deg\nI2 0 x 1 ampere 0deg")
    refusal = analyze_ac_y_matrix(ir, PORTS)
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "unsolvable"


def test_independent_tableau_disagreement_blocks_y_matrix(monkeypatch):
    ir = leggi(BASE)
    real_tableau = two_port_module.solve_phasor_tableau

    def corrupted(measured):
        result = real_tableau(measured)
        result["R1"]["current"] += Cyc12.of(1)
        return result

    monkeypatch.setattr(two_port_module, "solve_phasor_tableau", corrupted)
    assert analyze_ac_y_matrix(ir, PORTS).cause == "path_disagreement"


def test_matching_wrong_currents_are_rejected_by_residuals(monkeypatch):
    ir = leggi(BASE)
    real_nodal = two_port_module.solve_phasor
    real_tableau = two_port_module.solve_phasor_tableau

    def corrupted(real):
        def run(measured):
            result = real(measured)
            result["R1"]["current"] += Cyc12.of(1)
            return result
        return run

    monkeypatch.setattr(two_port_module, "solve_phasor", corrupted(real_nodal))
    monkeypatch.setattr(two_port_module, "solve_phasor_tableau", corrupted(real_tableau))
    assert analyze_ac_y_matrix(ir, PORTS).cause == "residual"


def test_second_column_failure_cannot_publish_a_partial_y_matrix(monkeypatch):
    ir = leggi(BASE)
    real_column = two_port_module._column

    def second_fails(measured, ports, driven):
        if driven == 1:
            return Refusal("unsolvable", "due porte AC", "operation", "seconda prova interrotta")
        return real_column(measured, ports, driven)

    monkeypatch.setattr(two_port_module, "_column", second_fails)
    assert analyze_ac_y_matrix(ir, PORTS).cause == "unsolvable"


def test_redundant_port_or_conflicting_ideal_source_refuses_a_matrix():
    ir = leggi(BASE)
    for ports in ((("a", "0"), ("0", "a")), (("a", "0"), ("missing", "0"))):
        refusal = analyze_ac_y_matrix(ir, ports)
        assert isinstance(refusal, Refusal)
        assert refusal.cause == "claim_unsupported"
    conflict = leggi(BASE + "\nV1 a 0 6 volt 0deg")
    refusal = analyze_ac_y_matrix(conflict, PORTS)
    assert isinstance(refusal, Refusal)
    assert refusal.cause == "topology"
    assert analyze_ac_y_matrix(leggi(BASE.replace("@ac 2 rad/s\n", "")), PORTS).cause == "claim_unsupported"
