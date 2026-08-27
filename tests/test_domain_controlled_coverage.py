"""Rami domain/ scoperti solo dalle sorgenti controllate."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.ir import Component, IR
from kirchhoff.domain.mna import solve_dc
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.verify import _rifiuta_scarto_potenza, verify
from kirchhoff.pipeline.resolve import Solved, resolve

F = Fraction


def test_vccs_cp_a_massa_e_uscita_flottante():
    """p e q non a massa, cp a massa: stamp MNA con cp a riferimento."""
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A", "B", "C"),
        (
            Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
            Component.of("R1", "resistor", ("A", "B"), F(5), "R_1"),
            Component.of("R2", "resistor", ("B", "0"), F(5), "R_2"),
            Component.of(
                "G1", "voltage_controlled_current_source", ("C", "B"),
                F(1, 10), "G_1", control_nodes=("0", "A"),
            ),
            Component.of("R3", "resistor", ("C", "0"), F(10), "R_3"),
        ),
        (),
    )
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["G1"]["current"] == solve_dc(ir)["G1"]["current"]


def test_rifiuta_scarto_potenza_zero_e_niente():
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (
            Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
            Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        ),
        (),
    )
    assert _rifiuta_scarto_potenza(ir, F(0)) is None
    assert _rifiuta_scarto_potenza(ir, 0) is None
    assert _rifiuta_scarto_potenza(ir, None) is None
    esito = _rifiuta_scarto_potenza(ir, F(3))
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert "scarto" in esito.diagnosis
    assert "bilancio di potenza" in esito.diagnosis


def test_verify_rifiuta_bilancio_di_potenza(monkeypatch):
    import kirchhoff.domain.verify as ver

    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "constitutive_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(3))
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (
            Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
            Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        ),
        (),
    )
    sol = {
        "V1": {"voltage": F(10), "current": F(-1)},
        "R1": {"voltage": F(10), "current": F(1)},
    }
    esito = ver.verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert "scarto" in esito.diagnosis


def test_verify_rifiuta_legge_costitutiva_con_kcl_kvl_ok():
    """KCL e KVL passano; la legge Vout = μ Vcontrol no.

    Correre solo la tensione della VCVS fa fallire KVL prima. Qui le due
    tensioni sul nodo di uscita restano coerenti fra loro, cosi' verify
    arriva al residuo costitutivo.
    """
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A", "C"),
        (
            Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
            Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
            Component.of(
                "E1", "voltage_controlled_voltage_source", ("C", "0"),
                F(2), "E_1", control_nodes=("A", "0"),
            ),
            Component.of("R2", "resistor", ("C", "0"), F(5), "R_2"),
        ),
        (),
    )
    sol = {
        "V1": {"voltage": F(10), "current": F(-1)},
        "R1": {"voltage": F(10), "current": F(1)},
        "E1": {"voltage": F(21), "current": F(-4)},
        "R2": {"voltage": F(21), "current": F(4)},
    }
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert esito.subject == "E1"
    assert "legge costitutiva" in esito.diagnosis
