"""Dominio reattivo: sorgenti di corrente, regime sinusoidale, frequenze naturali.

Ogni valore atteso qui e' calcolato a mano su carta e scritto come razionale esatto.
Se un giorno un confronto richiede una tolleranza, il bug e' nel codice, non nel test.
"""

from fractions import Fraction

import pytest

from kirchhoff.domain.exact import J, ONE, ZERO, Cyc12, determinant, zeta_pow
from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.mna import (
    kcl_residuals,
    mna_matrix_at,
    power_balance,
    solve_dc,
    solve_phasor,
)

Q = Fraction


# -- validazione dei nuovi tipi ------------------------------------------------


def test_capacita_e_induttanza_non_positive_rifiutate():
    with pytest.raises(ValueError):
        Component.of("C1", "capacitor", ("A", "0"), Q(0), "C_1")
    with pytest.raises(ValueError):
        Component.of("L1", "inductor", ("A", "0"), Q(-1), "L_1")


def test_sfasamento_solo_sulle_sorgenti_sinusoidali():
    Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1", phase_steps=4)
    with pytest.raises(ValueError):
        Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1", phase_steps=1)


def test_regime_sinusoidale_senza_pulsazione_rifiutato():
    with pytest.raises(ValueError):
        IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
           (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1"),
            Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1")),
           (Request("q1", "current", "R1"),))


# -- sorgente di corrente in continua ------------------------------------------


def test_sorgente_di_corrente():
    """I=2A iniettata nel nodo A su R=10 -> v_A = 20 V, esatti."""
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("I1", "current_source_dc", ("0", "A"), Q(2), "I_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1")),
            (Request("q1", "voltage", "R1"),))
    sol = solve_dc(ir)
    assert sol["R1"]["voltage"] == Q(20)
    assert sol["R1"]["current"] == Q(2)
    assert sol["I1"]["current"] == Q(2)
    assert all(r == 0 for r in kcl_residuals(ir, sol).values())
    assert power_balance(ir, sol) == 0


def test_tipo_non_ammesso_in_continua():
    ir = IR("1.0.0", "x", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1")),
            (Request("q1", "current", "R1"),), omega=Q(100))
    with pytest.raises(ValueError, match="continua"):
        solve_dc(ir)


# -- regime sinusoidale --------------------------------------------------------


def rl_series() -> IR:
    """E=10V, w=1000, R=30, L=40mH -> Z = 30 + j40, |Z| = 50."""
    return IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A", "B"),
              (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1"),
               Component.of("R1", "resistor", ("A", "B"), Q(30), "R_1"),
               Component.of("L1", "inductor", ("B", "0"), Q(40, 1000), "L_1")),
              (Request("q1", "current", "R1"),), omega=Q(1000))


def test_impedenza_serie_rl():
    """I = 10/(30+j40) = (30 - j40)/250 = 3/25 - j*4/25, esatto."""
    sol = solve_phasor(rl_series())
    atteso = Cyc12.of(Q(3, 25)) - J * Cyc12.of(Q(4, 25))
    assert sol["R1"]["current"] == atteso
    assert sol["L1"]["current"] == atteso
    assert sol["R1"]["voltage"] == atteso * Cyc12.of(30)


def test_kcl_e_potenza_nulli_anche_in_sinusoidale():
    ir = rl_series()
    sol = solve_phasor(ir)
    assert all(r == 0 for r in kcl_residuals(ir, sol).values())
    assert power_balance(ir, sol) == 0


def test_condensatore_e_induttore_in_parallelo():
    """A w=1000: Z_C = -j*100 (C=10uF), Z_L = +j*100 (L=100mH). In parallelo: aperto."""
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(50), "R_1"),
             Component.of("C1", "capacitor", ("A", "0"), Q(10, 10**6), "C_1"),
             Component.of("L1", "inductor", ("A", "0"), Q(100, 1000), "L_1")),
            (Request("q1", "current", "R1"),), omega=Q(1000))
    sol = solve_phasor(ir)
    assert sol["C1"]["current"] == J * Cyc12.of(Q(1, 10))
    assert sol["L1"]["current"] == -J * Cyc12.of(Q(1, 10))
    assert sol["C1"]["current"] + sol["L1"]["current"] == ZERO
    assert sol["E1"]["current"] == -Cyc12.of(Q(1, 5))


def test_sfasamento_di_120_gradi_resta_esatto():
    """Tre sorgenti equilibrate su tre resistori uguali: la somma delle correnti e' zero."""
    ir = IR("1.0.0", "three_phase", "generated", ("0", "a", "b", "c"),
            (Component.of("Ea", "voltage_source_ac", ("a", "0"), Q(230), "E_a"),
             Component.of("Eb", "voltage_source_ac", ("b", "0"), Q(230), "E_b", phase_steps=-4),
             Component.of("Ec", "voltage_source_ac", ("c", "0"), Q(230), "E_c", phase_steps=4),
             Component.of("Ra", "resistor", ("a", "0"), Q(23), "R_a"),
             Component.of("Rb", "resistor", ("b", "0"), Q(23), "R_b"),
             Component.of("Rc", "resistor", ("c", "0"), Q(23), "R_c")),
            (Request("q1", "current", "Ra"),), omega=Q(314))
    sol = solve_phasor(ir)
    somma = sol["Ra"]["current"] + sol["Rb"]["current"] + sol["Rc"]["current"]
    assert somma == ZERO
    assert sol["Ra"]["current"] == Cyc12.of(10)
    assert sol["Rb"]["current"] == Cyc12.of(10) * zeta_pow(-4)


def test_tipo_non_ammesso_in_sinusoidale():
    ir = IR("1.0.0", "x", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Q(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1")),
            (Request("q1", "current", "R1"),), omega=Q(100))
    with pytest.raises(ValueError, match="sinusoidale"):
        solve_phasor(ir)


# -- frequenze naturali --------------------------------------------------------


def rlc_series() -> IR:
    """R=3, L=1, C=1/2 -> s^2 + 3s + 2 = 0 -> radici -1 e -2."""
    return IR("1.0.0", "transient", "generated", ("0", "A", "B", "C"),
              (Component.of("E1", "voltage_source_dc", ("A", "0"), Q(12), "E_1"),
               Component.of("R1", "resistor", ("A", "B"), Q(3), "R_1"),
               Component.of("L1", "inductor", ("B", "C"), Q(1), "L_1"),
               Component.of("C1", "capacitor", ("C", "0"), Q(1, 2), "C_1")),
              (Request("q1", "root_1", "C1"),))


def test_le_radici_annullano_il_determinante_della_matrice_mna():
    """La definizione di frequenza naturale, non una formula: det M(s) = 0."""
    ir = rlc_series()
    assert determinant(mna_matrix_at(ir, Q(-1))) == 0
    assert determinant(mna_matrix_at(ir, Q(-2))) == 0
    assert determinant(mna_matrix_at(ir, Q(-3))) != 0
    assert determinant(mna_matrix_at(ir, Q(1))) != 0


def test_la_matrice_delle_frequenze_naturali_ha_le_sorgenti_spente():
    """Spegnere le sorgenti e' cio' che rende il problema omogeneo."""
    ir = IR("1.0.0", "transient", "generated", ("0", "A"),
            (Component.of("I1", "current_source_dc", ("0", "A"), Q(5), "I_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(2), "R_1"),
             Component.of("C1", "capacitor", ("A", "0"), Q(3), "C_1")),
            (Request("q1", "time_constant", "C1"),))
    # tau = RC = 6 -> s = -1/6
    assert determinant(mna_matrix_at(ir, Q(-1, 6))) == 0
    assert determinant(mna_matrix_at(ir, Q(-1, 5))) != 0


def test_tipo_non_ammesso_nel_dominio_di_laplace():
    ir = IR("1.0.0", "x", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1")),
            (Request("q1", "current", "R1"),), omega=Q(100))
    with pytest.raises(ValueError, match="Laplace"):
        mna_matrix_at(ir, Q(-1))


def test_uno_e_zero_del_campo_restano_a_disposizione():
    assert ONE * Cyc12.of(7) == Cyc12.of(7)
