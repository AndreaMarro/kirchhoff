"""Generatore deterministico di reti DC con VCVS o VCCS.

Ogni seed produce un circuito distinto: guadagno, polarità, controllo
ground/floating, resistenze e topologia dell'uscita cambiano. Non è una
copia dello stesso schema con μ diverso.
"""

from __future__ import annotations

import random
from fractions import Fraction

from kirchhoff.domain.ir import IR, REFERENCE_NODE, Component, Request

E24 = (10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82)


def _r(rng: random.Random) -> Fraction:
    return Fraction(rng.choice(E24)) * Fraction(10) ** rng.choice((0, 0, 1))


def _gain(rng: random.Random, *, voltage: bool) -> Fraction:
    num = Fraction(rng.choice((1, 2, 3, 4, 5, 1, 2)))
    den = Fraction(1) if voltage else Fraction(rng.choice((1, 2, 5, 10)))
    segno = Fraction(-1) if rng.random() < 0.45 else Fraction(1)
    return segno * num / den


def generate_vcvs_case(seed: int) -> IR:
    rng = random.Random(seed)
    e = Fraction(rng.choice((5, 9, 12, 15, 24)))
    mu = _gain(rng, voltage=True)
    famiglia = seed % 5
    comps: list[Component]
    if famiglia == 0:
        r1, rload = _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", REFERENCE_NODE), r1, "R_1"),
            Component.of("E1", "voltage_controlled_voltage_source", ("C", REFERENCE_NODE),
                         mu, "E_1", control_nodes=("A", REFERENCE_NODE)),
            Component.of("R2", "resistor", ("C", REFERENCE_NODE), rload, "R_2"),
        ]
    elif famiglia == 1:
        r1, r2, rload = _r(rng), _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
            Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
            Component.of("E1", "voltage_controlled_voltage_source", ("C", REFERENCE_NODE),
                         mu, "E_1", control_nodes=("A", "B")),
            Component.of("R3", "resistor", ("C", REFERENCE_NODE), rload, "R_3"),
        ]
    elif famiglia == 2:
        r1, r2, r3 = _r(rng), _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
            Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
            Component.of("E1", "voltage_controlled_voltage_source", ("C", "B"),
                         mu, "E_1", control_nodes=("A", REFERENCE_NODE)),
            Component.of("R3", "resistor", ("C", REFERENCE_NODE), r3, "R_3"),
        ]
    elif famiglia == 3:
        r1, r2, r3, r4, rg = _r(rng), _r(rng), _r(rng), _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("P", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("P", "X"), r1, "R_1"),
            Component.of("R2", "resistor", ("P", "Y"), r2, "R_2"),
            Component.of("R3", "resistor", ("X", REFERENCE_NODE), r3, "R_3"),
            Component.of("R4", "resistor", ("Y", REFERENCE_NODE), r4, "R_4"),
            Component.of("Rg", "resistor", ("X", "Y"), rg, "R_g"),
            Component.of("E1", "voltage_controlled_voltage_source", ("C", REFERENCE_NODE),
                         mu, "E_1", control_nodes=("X", "Y")),
            Component.of("Rl", "resistor", ("C", REFERENCE_NODE), _r(rng), "R_l"),
        ]
    else:
        r1, r2 = _r(rng), _r(rng)
        mu2 = _gain(rng, voltage=True)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", REFERENCE_NODE), r1, "R_1"),
            Component.of("E1", "voltage_controlled_voltage_source", ("C", REFERENCE_NODE),
                         mu, "E_1", control_nodes=("A", REFERENCE_NODE)),
            Component.of("E2", "voltage_controlled_voltage_source", ("D", REFERENCE_NODE),
                         mu2, "E_2", control_nodes=("C", REFERENCE_NODE)),
            Component.of("R2", "resistor", ("D", REFERENCE_NODE), r2, "R_2"),
        ]
    nodes = tuple(sorted({t for c in comps for t in c.terminals}))
    requests = (Request("q1", "voltage", "E1"), Request("q2", "current", "E1"))
    return IR("1.0.0", "dc", "generated", nodes, tuple(comps), requests)


def generate_vccs_case(seed: int) -> IR:
    rng = random.Random(seed + 1000)
    e = Fraction(rng.choice((5, 9, 12, 15, 24)))
    g = _gain(rng, voltage=False)
    famiglia = seed % 5
    comps: list[Component]
    if famiglia == 0:
        r1, rload = _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", REFERENCE_NODE), r1, "R_1"),
            Component.of("G1", "voltage_controlled_current_source", ("C", REFERENCE_NODE),
                         g, "G_1", control_nodes=("A", REFERENCE_NODE)),
            Component.of("R2", "resistor", ("C", REFERENCE_NODE), rload, "R_2"),
        ]
    elif famiglia == 1:
        r1, r2, rload = _r(rng), _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
            Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
            Component.of("G1", "voltage_controlled_current_source", ("C", REFERENCE_NODE),
                         g, "G_1", control_nodes=("A", "B")),
            Component.of("R3", "resistor", ("C", REFERENCE_NODE), rload, "R_3"),
        ]
    elif famiglia == 2:
        r1, r2 = _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", "B"), r1, "R_1"),
            Component.of("R2", "resistor", ("B", REFERENCE_NODE), r2, "R_2"),
            Component.of("G1", "voltage_controlled_current_source", ("B", REFERENCE_NODE),
                         g, "G_1", control_nodes=("A", REFERENCE_NODE)),
        ]
    elif famiglia == 3:
        r1, r2, r3, r4, rg = _r(rng), _r(rng), _r(rng), _r(rng), _r(rng)
        comps = [
            Component.of("V1", "voltage_source_dc", ("P", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("P", "X"), r1, "R_1"),
            Component.of("R2", "resistor", ("P", "Y"), r2, "R_2"),
            Component.of("R3", "resistor", ("X", REFERENCE_NODE), r3, "R_3"),
            Component.of("R4", "resistor", ("Y", REFERENCE_NODE), r4, "R_4"),
            Component.of("Rg", "resistor", ("X", "Y"), rg, "R_g"),
            Component.of("G1", "voltage_controlled_current_source", ("C", REFERENCE_NODE),
                         g, "G_1", control_nodes=("X", "Y")),
            Component.of("Rl", "resistor", ("C", REFERENCE_NODE), _r(rng), "R_l"),
        ]
    else:
        r1, r2 = _r(rng), _r(rng)
        g2 = _gain(rng, voltage=False)
        comps = [
            Component.of("V1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "V_1"),
            Component.of("R1", "resistor", ("A", REFERENCE_NODE), r1, "R_1"),
            Component.of("G1", "voltage_controlled_current_source", ("C", REFERENCE_NODE),
                         g, "G_1", control_nodes=("A", REFERENCE_NODE)),
            Component.of("G2", "voltage_controlled_current_source", ("D", REFERENCE_NODE),
                         g2, "G_2", control_nodes=("C", REFERENCE_NODE)),
            Component.of("R2", "resistor", ("C", REFERENCE_NODE), r2, "R_2"),
            Component.of("R3", "resistor", ("D", REFERENCE_NODE), _r(rng), "R_3"),
        ]
    nodes = tuple(sorted({t for c in comps for t in c.terminals}))
    requests = (Request("q1", "voltage", "G1"), Request("q2", "current", "G1"))
    return IR("1.0.0", "dc", "generated", nodes, tuple(comps), requests)
