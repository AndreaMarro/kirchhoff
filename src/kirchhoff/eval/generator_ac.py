"""Generatore del regime sinusoidale: rete serie/parallelo di R, L, C.

Stessa struttura ad albero del generatore in continua, con una differenza sola: la
foglia non porta una resistenza ma un'impedenza, elemento esatto di Q(zeta_12). La
risposta per costruzione si ottiene propagando il fasore sull'albero; la verifica
indipendente risolve l'IR appiattito con l'analisi nodale, che dell'albero non sa
nulla.

La pulsazione e' razionale in rad/s, come la pone un testo di elettrotecnica
("omega = 314 rad/s"). La frequenza in hertz sarebbe `omega/2pi`, irrazionale e
inutile all'oracolo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

from ..domain.exact import J, ONE, Cyc12
from ..domain.ir import IR, REFERENCE_NODE, Component, Request
from .generator import E24
from .transformations import validate

#: Pulsazioni da esercizio, in rad/s. 314 e' la rete a 50 Hz.
PULSAZIONI = (100, 314, 1000, 2000)
#: Tensioni efficaci da esercizio.
SORGENTI = (10, 24, 100, 230)

Expected = dict[str, dict[str, Cyc12]]
Case = tuple[IR, Expected, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class Leaf:
    name: str
    kind: str
    value: Fraction
    z: Cyc12


@dataclass(frozen=True, slots=True)
class Series:
    children: tuple


@dataclass(frozen=True, slots=True)
class Parallel:
    children: tuple


Node = Leaf | Series | Parallel


def impedance(kind: str, value: Fraction, omega: Fraction) -> Cyc12:
    if kind == "resistor":
        return Cyc12.of(value)
    if kind == "inductor":
        return J * Cyc12.of(omega * value)
    return ONE / (J * Cyc12.of(omega * value))       # condensatore


def equivalent(t: Node) -> Cyc12:
    if isinstance(t, Leaf):
        return t.z
    if isinstance(t, Series):
        out = Cyc12.of(0)
        for c in t.children:
            out = out + equivalent(c)
        return out
    total = Cyc12.of(0)
    for c in t.children:
        total = total + ONE / equivalent(c)
    return ONE / total


def propagate(t: Node, v: Cyc12, out: dict[str, dict[str, Cyc12]]) -> None:
    """Distribuisce il fasore di tensione `v` applicato ai capi di `t` sulle foglie."""
    if isinstance(t, Leaf):
        out[t.name] = {"voltage": v, "current": v / t.z}
        return
    if isinstance(t, Series):
        i = v / equivalent(t)
        for c in t.children:
            propagate(c, i * equivalent(c), out)
        return
    for c in t.children:
        propagate(c, v, out)


def _leaf(rng: random.Random, omega: Fraction, counter: list[int]) -> Leaf:
    counter[0] += 1
    kind = rng.choice(("resistor", "resistor", "inductor", "capacitor"))
    if kind == "resistor":
        value = Fraction(rng.choice(E24) * 10)
        name = f"R{counter[0]}"
    elif kind == "inductor":
        value = Fraction(rng.choice(E24), 1000)
        name = f"L{counter[0]}"
    else:
        value = Fraction(rng.choice(E24), 10**6)
        name = f"C{counter[0]}"
    return Leaf(name, kind, value, impedance(kind, value, omega))


def _rng_tree(rng: random.Random, omega: Fraction, depth: int, counter: list[int]) -> Node:
    if depth == 0 or rng.random() < 0.4:
        return _leaf(rng, omega, counter)
    k = rng.randint(2, 3)
    children = tuple(_rng_tree(rng, omega, depth - 1, counter) for _ in range(k))
    return Series(children) if rng.random() < 0.5 else Parallel(children)


def _flatten(t: Node, a: str, b: str, comps: list[Component], fresh: list[int]) -> None:
    if isinstance(t, Leaf):
        comps.append(Component.of(t.name, t.kind, (a, b), t.value, t.name))  # type: ignore[arg-type]
        return
    if isinstance(t, Series):
        prev = a
        for i, c in enumerate(t.children):
            fresh[0] += 1
            nxt = b if i == len(t.children) - 1 else f"n{fresh[0]}"
            _flatten(c, prev, nxt, comps, fresh)
            prev = nxt
        return
    for c in t.children:
        _flatten(c, a, b, comps, fresh)


def generate_case(seed: int, depth: int = 2) -> Case:
    """Restituisce (IR, risposta-per-costruzione, sequenza di Trasformazioni).

    Solleva `ZeroDivisionError` quando il sorteggio produce una risonanza esatta —
    un ramo LC in serie a impedenza nulla o in parallelo ad ammettenza nulla. Il
    caso viene scartato e contato, non aggiustato.
    """
    rng = random.Random(seed)
    omega = Fraction(rng.choice(PULSAZIONI))
    tree = _rng_tree(rng, omega, depth, [0])
    e_val = Fraction(rng.choice(SORGENTI))
    e = Cyc12.of(e_val)

    comps: list[Component] = [
        Component.of("E1", "voltage_source_ac", ("A", REFERENCE_NODE), e_val, "E_1")]
    _flatten(tree, "A", REFERENCE_NODE, comps, [0])

    nodes = tuple(sorted({t for c in comps for t in c.terminals}))
    passivi = [c.id for c in comps if c.id != "E1"]
    targets = sorted(passivi)[: min(2, len(passivi))]
    requests = tuple(
        Request(f"q{i+1}", "voltage" if i % 2 == 0 else "current", cid)
        for i, cid in enumerate(targets)
    )

    ir = IR("1.0.0", "ac_sinusoidal", "generated", nodes, tuple(comps), requests, omega)

    expected: Expected = {}
    propagate(tree, e, expected)
    expected["E1"] = {"voltage": e, "current": -(e / equivalent(tree))}

    seq = validate(("impedenza_complessa", "serie", "parallelo",
                    "legge_di_ohm_fasoriale", "partitore_di_tensione"))
    return ir, expected, seq
