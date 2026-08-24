"""Oracolo dei transitori: circuiti equivalenti a t=0+ e a regime, frequenze naturali.

Nessuna esponenziale compare qui. Cio' che un esercizio di transitorio chiede — la
costante di tempo, il valore iniziale, il valore finale, le radici caratteristiche —
e' tutto razionale, e resta esatto.
"""

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.transient import (
    CHARACTERISTIC_QUANTITY,
    initial_state,
    is_natural_frequency,
    steady_state,
)

Q = Fraction


def rc() -> IR:
    """E=12, R1=2, R2=4, C=3. tau = (2||4)*3 = 4. v_C(inf) = 12*4/6 = 8."""
    return IR("1.0.0", "transient", "generated", ("0", "A", "B"),
              (Component.of("E1", "voltage_source_dc", ("A", "0"), Q(12), "E_1"),
               Component.of("R1", "resistor", ("A", "B"), Q(2), "R_1"),
               Component.of("R2", "resistor", ("B", "0"), Q(4), "R_2"),
               Component.of("C1", "capacitor", ("B", "0"), Q(3), "C_1")),
              (Request("q1", "time_constant", "C1"),))


def rl() -> IR:
    """E=12, R1=2, R2=4, L=8. tau = 8/(2||4) = 6. i_L(inf) = 12/2 = 6."""
    return IR("1.0.0", "transient", "generated", ("0", "A", "B"),
              (Component.of("E1", "voltage_source_dc", ("A", "0"), Q(12), "E_1"),
               Component.of("R1", "resistor", ("A", "B"), Q(2), "R_1"),
               Component.of("R2", "resistor", ("B", "0"), Q(4), "R_2"),
               Component.of("L1", "inductor", ("B", "0"), Q(8), "L_1")),
              (Request("q1", "time_constant", "L1"),))


def test_regime_rc_condensatore_aperto():
    sol = steady_state(rc())
    assert sol["C1"]["voltage"] == Q(8)
    assert sol["C1"]["current"] == 0
    assert sol["R1"]["current"] == Q(2)


def test_stato_iniziale_rc_condensatore_scarico_e_un_corto():
    sol = initial_state(rc())
    assert sol["C1"]["voltage"] == 0
    assert sol["R1"]["current"] == Q(6)          # 12/2, il nodo B e' a zero


def test_regime_rl_induttore_in_corto():
    sol = steady_state(rl())
    assert sol["L1"]["current"] == Q(6)
    assert sol["L1"]["voltage"] == 0
    assert sol["R2"]["current"] == 0


def test_stato_iniziale_rl_induttore_aperto():
    sol = initial_state(rl())
    assert sol["L1"]["current"] == 0
    assert sol["R1"]["current"] == Q(2)          # 12/(2+4)


def test_costante_di_tempo_come_frequenza_naturale():
    """tau vale 4 se e solo se s = -1/4 annulla il determinante. Nessuna formula."""
    assert is_natural_frequency(rc(), Q(-1, 4))
    assert not is_natural_frequency(rc(), Q(-1, 3))
    assert is_natural_frequency(rl(), Q(-1, 6))
    assert not is_natural_frequency(rl(), Q(-1, 5))


def test_grandezza_caratteristica_per_tipo():
    assert CHARACTERISTIC_QUANTITY["capacitor"] == "voltage"
    assert CHARACTERISTIC_QUANTITY["inductor"] == "current"
    assert CHARACTERISTIC_QUANTITY["resistor"] == "current"


def test_una_rete_senza_elementi_di_accumulo_non_ha_frequenze_naturali():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Q(1), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(1), "R_1")),
            (Request("q1", "voltage", "R1"),))
    assert not is_natural_frequency(ir, Q(-1))


def test_sorgente_sinusoidale_fuori_dal_transitorio():
    ir = IR("1.0.0", "x", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), Q(1), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Q(1), "R_1")),
            (Request("q1", "voltage", "R1"),), omega=Q(10))
    with pytest.raises(ValueError):
        steady_state(ir)
