"""Generatore dei transitori RL/RC/RLC, a stato zero.

Quattro forme: RC e RL del primo ordine, RLC serie e RLC parallelo del secondo.

Per il secondo ordine i componenti si ricavano dalle radici, non viceversa. Un RLC
con `R, L, C` scelti a caso ha radici irrazionali quasi sempre; scegliendo invece
due radici razionali negative `s1, s2` e derivando i componenti da esse, il caso
resta esatto — e l'oracolo puo' ancora arrivarci dalla parte opposta, chiedendo
alla matrice MNA se quelle radici la annullano.

Convenzione della classe: **stato zero**. All'istante della chiusura il
condensatore e' scarico e l'induttore non porta corrente. E' la posa standard di un
esercizio di risposta al gradino, e rende il valore iniziale una conseguenza della
rete invece che un dato in piu' da annotare.

Le grandezze richieste sono valore iniziale e valore finale. La costante di tempo e
le radici caratteristiche stanno nella risposta attesa e sono verificate a ogni
costruzione, ma non compaiono fra le richieste: nessun risolutore le produce
ancora, e il sistema sotto test dell'harness non e' il prodotto (AD-15). Story 2.11
allarghera' le richieste quando il motore di Epic 2 sapra' rispondere.
"""

from __future__ import annotations

import random
from fractions import Fraction

from ..domain.ir import IR, REFERENCE_NODE, Component, Request
from .generator import E24
from .transformations import validate

#: Tensioni continue da esercizio.
SORGENTI = (5, 9, 12, 15, 24)
#: Correnti continue da esercizio, in ampere.
CORRENTI = (1, 2, 5)
#: Frequenze proprie in rad/s: le radici caratteristiche del secondo ordine.
RITMI = (50, 100, 200, 500, 1000, 2000)
#: Induttanze in henry.
INDUTTANZE = (Fraction(1, 100), Fraction(1, 20), Fraction(1, 10))
#: Capacita' in farad.
CAPACITA = (Fraction(10, 10**6), Fraction(22, 10**6), Fraction(47, 10**6),
            Fraction(100, 10**6))

Expected = dict[str, dict[str, Fraction]]
Case = tuple[IR, Expected, tuple[str, ...]]

FORME = ("rc", "rl", "rlc_serie", "rlc_parallelo")


def _resistenze(rng: random.Random) -> tuple[Fraction, Fraction]:
    return Fraction(rng.choice(E24) * 100), Fraction(rng.choice(E24) * 100)


def _rc(rng: random.Random) -> Case:
    e = Fraction(rng.choice(SORGENTI))
    r1, r2 = _resistenze(rng)
    c = Fraction(rng.choice(E24), 10**6)

    ir = IR("1.0.0", "transient", "generated", ("0", "A", "B"),
            (Component.of("E1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "E_1"),
             Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
             Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
             Component.of("C1", "capacitor", ("B", REFERENCE_NODE), c, "C_1")),
            (Request("q1", "final_value", "C1"),
             Request("q2", "initial_value", "R1")))

    expected: Expected = {
        "C1": {"time_constant": (r1 * r2 / (r1 + r2)) * c,
               "initial_value": Fraction(0),
               "final_value": e * r2 / (r1 + r2)},
        # a t=0+ il condensatore scarico tiene il nodo B a zero: tutta la tensione su R1
        "R1": {"initial_value": e / r1},
    }
    seq = validate(("circuito_equivalente_a_t0", "legge_di_ohm",
                    "circuito_equivalente_a_regime", "partitore_di_tensione",
                    "resistenza_equivalente_di_thevenin", "parallelo", "costante_di_tempo"))
    return ir, expected, seq


def _rl(rng: random.Random) -> Case:
    e = Fraction(rng.choice(SORGENTI))
    r1, r2 = _resistenze(rng)
    ind = Fraction(rng.choice(E24), 1000)

    ir = IR("1.0.0", "transient", "generated", ("0", "A", "B"),
            (Component.of("E1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "E_1"),
             Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
             Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
             Component.of("L1", "inductor", ("B", REFERENCE_NODE), ind, "L_1")),
            (Request("q1", "final_value", "L1"),
             Request("q2", "initial_value", "R1")))

    expected: Expected = {
        "L1": {"time_constant": ind / (r1 * r2 / (r1 + r2)),
               "initial_value": Fraction(0),
               "final_value": e / r1},
        # a t=0+ l'induttore e' aperto: R1 e R2 in serie
        "R1": {"initial_value": e / (r1 + r2)},
    }
    seq = validate(("circuito_equivalente_a_t0", "serie", "legge_di_ohm",
                    "circuito_equivalente_a_regime", "resistenza_equivalente_di_thevenin",
                    "parallelo", "costante_di_tempo"))
    return ir, expected, seq


def _due_ritmi(rng: random.Random) -> tuple[Fraction, Fraction]:
    a, b = rng.sample(RITMI, 2)
    return Fraction(-a), Fraction(-b)


def _rlc_serie(rng: random.Random) -> Case:
    e = Fraction(rng.choice(SORGENTI))
    s1, s2 = _due_ritmi(rng)
    ind = rng.choice(INDUTTANZE)
    r = -(s1 + s2) * ind            # R/L = -(s1+s2)
    c = 1 / (s1 * s2 * ind)         # 1/(LC) = s1*s2

    ir = IR("1.0.0", "transient", "generated", ("0", "A", "B", "C"),
            (Component.of("E1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "E_1"),
             Component.of("R1", "resistor", ("A", "B"), r, "R_1"),
             Component.of("L1", "inductor", ("B", "C"), ind, "L_1"),
             Component.of("C1", "capacitor", ("C", REFERENCE_NODE), c, "C_1")),
            (Request("q1", "final_value", "C1"),
             Request("q2", "initial_value", "R1")))

    expected: Expected = {
        "C1": {"root_1": s1, "root_2": s2,
               "initial_value": Fraction(0), "final_value": e},
        "L1": {"initial_value": Fraction(0), "final_value": Fraction(0)},
        "R1": {"initial_value": Fraction(0)},
    }
    seq = validate(("serie", "equazione_caratteristica", "radici_caratteristiche",
                    "circuito_equivalente_a_t0", "circuito_equivalente_a_regime"))
    return ir, expected, seq


def _rlc_parallelo(rng: random.Random) -> Case:
    i0 = Fraction(rng.choice(CORRENTI))
    s1, s2 = _due_ritmi(rng)
    c = rng.choice(CAPACITA)
    r = 1 / (-(s1 + s2) * c)        # 1/(RC) = -(s1+s2)
    ind = 1 / (s1 * s2 * c)         # 1/(LC) = s1*s2

    ir = IR("1.0.0", "transient", "generated", ("0", "A"),
            (Component.of("I1", "current_source_dc", (REFERENCE_NODE, "A"), i0, "I_1"),
             Component.of("R1", "resistor", ("A", REFERENCE_NODE), r, "R_1"),
             Component.of("L1", "inductor", ("A", REFERENCE_NODE), ind, "L_1"),
             Component.of("C1", "capacitor", ("A", REFERENCE_NODE), c, "C_1")),
            (Request("q1", "final_value", "L1"),
             Request("q2", "initial_value", "R1")))

    expected: Expected = {
        "L1": {"root_1": s1, "root_2": s2,
               "initial_value": Fraction(0), "final_value": i0},
        "C1": {"initial_value": Fraction(0), "final_value": Fraction(0)},
        "R1": {"initial_value": Fraction(0)},
    }
    seq = validate(("parallelo", "equazione_caratteristica", "radici_caratteristiche",
                    "circuito_equivalente_a_t0", "circuito_equivalente_a_regime"))
    return ir, expected, seq


_COSTRUTTORI = {"rc": _rc, "rl": _rl, "rlc_serie": _rlc_serie, "rlc_parallelo": _rlc_parallelo}


def generate_case(seed: int) -> Case:
    """Restituisce (IR, risposta-per-costruzione, sequenza di Trasformazioni)."""
    rng = random.Random(seed)
    return _COSTRUTTORI[FORME[seed % len(FORME)]](rng)
