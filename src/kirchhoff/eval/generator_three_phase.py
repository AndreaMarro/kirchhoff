"""Generatore del trifase equilibrato: carico a stella con neutro, e a triangolo.

La risposta per costruzione viene dal circuito monofase equivalente: una sola fase
risolta, le altre due ottenute ruotando di 120 gradi. La verifica indipendente
risolve invece l'intera rete a otto o nove nodi con l'analisi nodale, che della
simmetria non sa nulla e non la sfrutta.

Due proprieta' rendono questa classe il vero banco di prova dell'aritmetica esatta:
la somma delle tre correnti di fase e' **esattamente** zero — quindi il conduttore
di neutro porta zero, non "circa zero" — e nel carico a triangolo compare `sqrt(3)`,
che in virgola mobile chiuderebbe per sempre la porta a un confronto esatto.
"""

from __future__ import annotations

import random
from fractions import Fraction

from ..domain.exact import SQRT3, ZETA, Cyc12, J, zeta_pow
from ..domain.ir import IR, REFERENCE_NODE, Component, Request
from .generator import E24
from .transformations import validate

#: Tensioni di fase da esercizio, in volt.
TENSIONI = (127, 220, 230, 400)
#: Pulsazioni da esercizio: 314 rad/s e' la rete a 50 Hz.
PULSAZIONI = (314, 100, 1000)

#: Sfasamenti delle tre fasi, in passi di 30 gradi: 0, -120, +120.
FASI = (0, -4, 4)

Expected = dict[str, dict[str, Cyc12]]
Case = tuple[IR, Expected, tuple[str, ...]]

FORME = ("stella", "triangolo")


def _sorgenti(e: Fraction) -> tuple[Component, ...]:
    return tuple(
        Component.of(f"E{n}", "voltage_source_ac", (n, REFERENCE_NODE), e, f"E_{n}",
                  phase_steps=ph)
        for n, ph in zip(("a", "b", "c"), FASI)
    )


def _stella(rng: random.Random) -> Case:
    """Sorgente a stella, carico R-L a stella, neutro ideale di cui si legge la corrente."""
    e = Fraction(rng.choice(TENSIONI))
    omega = Fraction(rng.choice(PULSAZIONI))
    r = Fraction(rng.choice(E24))
    ind = Fraction(rng.choice(E24), 1000)
    z = Cyc12.of(r) + J * Cyc12.of(omega * ind)

    comps = list(_sorgenti(e))
    for n in ("a", "b", "c"):
        comps.append(Component.of(f"R{n}", "resistor", (n, f"{n}1"), r, f"R_{n}"))
        comps.append(Component.of(f"L{n}", "inductor", (f"{n}1", "N"), ind, f"L_{n}"))
    # il neutro: una sorgente a tensione nulla, cioe' un corto di cui si misura la corrente
    comps.append(Component.of("VN", "voltage_source_ac", ("N", REFERENCE_NODE),
                           Fraction(0), "V_N"))

    nodes = (REFERENCE_NODE, "a", "b", "c", "a1", "b1", "c1", "N")
    requests = (Request("q1", "current", "Ra"), Request("q2", "current", "VN"))
    ir = IR("1.0.0", "three_phase", "generated", nodes, tuple(comps), requests, omega)

    expected: Expected = {}
    for n, ph in zip(("a", "b", "c"), FASI):
        i_fase = Cyc12.of(e) * zeta_pow(ph) / z
        expected[f"R{n}"] = {"voltage": i_fase * Cyc12.of(r), "current": i_fase}
        expected[f"L{n}"] = {"voltage": i_fase * (J * Cyc12.of(omega * ind)),
                             "current": i_fase}
        expected[f"E{n}"] = {"voltage": Cyc12.of(e) * zeta_pow(ph), "current": -i_fase}
    # equilibrato: le tre correnti sommano a zero, quindi il neutro non porta nulla
    expected["VN"] = {"voltage": Cyc12.of(0), "current": Cyc12.of(0)}

    seq = validate(("impedenza_complessa", "circuito_monofase_equivalente",
                    "legge_di_ohm_fasoriale", "sfasamento_di_fase"))
    return ir, expected, seq


def _triangolo(rng: random.Random) -> Case:
    """Sorgente a stella, carico R-L a triangolo. Qui compare sqrt(3), esatto."""
    e = Fraction(rng.choice(TENSIONI))
    omega = Fraction(rng.choice(PULSAZIONI))
    r = Fraction(rng.choice(E24))
    ind = Fraction(rng.choice(E24), 1000)
    z = Cyc12.of(r) + J * Cyc12.of(omega * ind)

    lati = (("a", "b"), ("b", "c"), ("c", "a"))
    comps = list(_sorgenti(e))
    for x, y in lati:
        comps.append(Component.of(f"R{x}{y}", "resistor", (x, f"m{x}{y}"), r, f"R_{{{x}{y}}}"))
        comps.append(Component.of(f"L{x}{y}", "inductor", (f"m{x}{y}", y), ind, f"L_{{{x}{y}}}"))

    nodes = (REFERENCE_NODE, "a", "b", "c", "mab", "mbc", "mca")
    requests = (Request("q1", "current", "Rab"), Request("q2", "current", "Ea"))
    ir = IR("1.0.0", "three_phase", "generated", nodes, tuple(comps), requests, omega)

    # tensione concatenata: V_ab = E_a - E_b = E * sqrt(3) * zeta, in anticipo di 30 gradi
    fase_di = dict(zip(("a", "b", "c"), FASI))
    expected: Expected = {}
    correnti_di_lato: dict[str, Cyc12] = {}
    for x, y in lati:
        v_lato = Cyc12.of(e) * (zeta_pow(fase_di[x]) - zeta_pow(fase_di[y]))
        i_lato = v_lato / z
        correnti_di_lato[f"{x}{y}"] = i_lato
        expected[f"R{x}{y}"] = {"voltage": i_lato * Cyc12.of(r), "current": i_lato}
        expected[f"L{x}{y}"] = {"voltage": i_lato * (J * Cyc12.of(omega * ind)),
                                "current": i_lato}
    for x, entrante, uscente in (("a", "ab", "ca"), ("b", "bc", "ab"), ("c", "ca", "bc")):
        i_linea = correnti_di_lato[entrante] - correnti_di_lato[uscente]
        expected[f"E{x}"] = {"voltage": Cyc12.of(e) * zeta_pow(fase_di[x]),
                             "current": -i_linea}

    seq = validate(("impedenza_complessa", "stella_triangolo",
                    "circuito_monofase_equivalente", "legge_di_ohm_fasoriale",
                    "sfasamento_di_fase"))
    return ir, expected, seq


_COSTRUTTORI = {"stella": _stella, "triangolo": _triangolo}


def generate_case(seed: int) -> Case:
    """Restituisce (IR, risposta-per-costruzione, sequenza di Trasformazioni)."""
    rng = random.Random(seed)
    return _COSTRUTTORI[FORME[seed % len(FORME)]](rng)


def concatenata(e: Fraction) -> Cyc12:
    """Tensione concatenata di un sistema equilibrato: `E * sqrt(3)` a +30 gradi."""
    return Cyc12.of(e) * SQRT3 * ZETA
