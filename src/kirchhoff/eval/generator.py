"""Generatore parametrico di reti resistive con risposta nota per costruzione.

La rete e' costruita come albero serie/parallelo. Durante la costruzione si
propagano tensione e corrente su ogni foglia con aritmetica esatta: quella e' la
risposta "per costruzione".

La verifica indipendente (Story 1.1, terzo criterio) NON usa questa propagazione:
appiattisce l'albero in un IR e lo risolve con l'analisi nodale modificata, che
non sa nulla della struttura serie/parallelo. Un oracolo che si autocertifica non
e' un oracolo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

from ..domain.ir import IR, REFERENCE_NODE, Component, Request
from .transformations import validate

# Serie E24, i valori che compaiono davvero in un esercizio (FR-4, controllo E12/E24)
E24 = (10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30,
       33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91)


@dataclass(frozen=True, slots=True)
class Leaf:
    name: str
    r: Fraction


@dataclass(frozen=True, slots=True)
class Series:
    children: tuple


@dataclass(frozen=True, slots=True)
class Parallel:
    children: tuple


Node = Leaf | Series | Parallel


def equivalent(t: Node) -> Fraction:
    if isinstance(t, Leaf):
        return t.r
    if isinstance(t, Series):
        return sum((equivalent(c) for c in t.children), Fraction(0))
    total = sum((Fraction(1) / equivalent(c) for c in t.children), Fraction(0))
    return Fraction(1) / total


def propagate(t: Node, v: Fraction, out: dict[str, dict[str, Fraction]]) -> None:
    """Distribuisce la tensione `v` applicata ai capi di `t` sulle foglie."""
    if isinstance(t, Leaf):
        out[t.name] = {"voltage": v, "current": v / t.r}
        return
    if isinstance(t, Series):
        i = v / equivalent(t)
        for c in t.children:
            propagate(c, i * equivalent(c), out)
        return
    for c in t.children:
        propagate(c, v, out)


def _rng_tree(rng: random.Random, depth: int, counter: list[int]) -> Node:
    if depth == 0 or rng.random() < 0.35:
        counter[0] += 1
        return Leaf(f"R{counter[0]}", Fraction(rng.choice(E24)))
    kind = rng.choice(("series", "parallel"))
    k = rng.randint(2, 3)
    children = tuple(_rng_tree(rng, depth - 1, counter) for _ in range(k))
    return Series(children) if kind == "series" else Parallel(children)


def _flatten(t: Node, a: str, b: str, comps: list[Component], fresh: list[int]) -> None:
    if isinstance(t, Leaf):
        comps.append(Component.of(t.name, "resistor", (a, b), t.r, t.name))
        return
    if isinstance(t, Series):
        prev = a
        for i, c in enumerate(t.children):
            nxt = b if i == len(t.children) - 1 else f"n{_next(fresh)}"
            _flatten(c, prev, nxt, comps, fresh)
            prev = nxt
        return
    for c in t.children:
        _flatten(c, a, b, comps, fresh)


def _next(fresh: list[int]) -> int:
    fresh[0] += 1
    return fresh[0]


def transformation_sequence(t: Node) -> tuple[str, ...]:
    """La sequenza di riferimento: si riduce dal basso, si applica Ohm, si ripartisce dall'alto."""
    riduzioni: list[str] = []
    ripartizioni: list[str] = []

    def giu(n: Node) -> None:
        if isinstance(n, Leaf):
            return
        for c in n.children:
            giu(c)
        riduzioni.append("serie" if isinstance(n, Series) else "parallelo")

    def su(n: Node) -> None:
        if isinstance(n, Leaf):
            return
        ripartizioni.append(
            "partitore_di_tensione" if isinstance(n, Series) else "partitore_di_corrente")
        for c in n.children:
            su(c)

    giu(t)
    su(t)
    return validate((*riduzioni, "legge_di_ohm", *ripartizioni))


def generate_case(
    seed: int, depth: int = 3
) -> tuple[IR, dict[str, dict[str, Fraction]], tuple[str, ...]]:
    """Restituisce (IR, risposta-per-costruzione, sequenza di Trasformazioni)."""
    rng = random.Random(seed)
    tree = _rng_tree(rng, depth, [0])
    e = Fraction(rng.choice((5, 9, 12, 15, 24)))

    comps: list[Component] = [Component.of("E1", "voltage_source_dc", ("A", REFERENCE_NODE), e, "E_1")]
    _flatten(tree, "A", REFERENCE_NODE, comps, [0])

    nodes = tuple(sorted({t for c in comps for t in c.terminals}))
    leaves = [c.id for c in comps if c.type == "resistor"]
    targets = sorted(leaves)[: min(2, len(leaves))]
    requests = tuple(
        Request(f"q{i+1}", "voltage" if i % 2 == 0 else "current", cid)
        for i, cid in enumerate(targets)
    )

    ir = IR("1.0.0", "dc_resistive", "generated", nodes, tuple(comps), requests)

    expected: dict[str, dict[str, Fraction]] = {}
    propagate(tree, e, expected)
    expected["E1"] = {"voltage": e, "current": -(e / equivalent(tree))}
    return ir, expected, transformation_sequence(tree)
