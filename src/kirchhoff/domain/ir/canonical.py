"""Forma canonica dell'IR: ordinare l'arbitrario, non toccare il resto.

Due descrizioni dello stesso circuito possono elencare i componenti in ordine
diverso, i nodi in ordine diverso, e nominare i due capi di un resistore
nell'ordine che capita. Nessuna di queste differenze dice qualcosa del circuito, e
finché sopravvivono i due IR non si possono confrontare.

L'ordine dei terminali di un **generatore** invece dice qualcosa: è la polarità.
Riordinarlo produrrebbe un circuito diverso che si dichiara uguale — l'errore
silenzioso che il prodotto esiste per prevenire. Per questo la simmetria si applica
solo ai bipoli che sono davvero simmetrici.

Pura e idempotente: restituisce un nuovo IR e non tocca quello ricevuto.
"""

from __future__ import annotations

from dataclasses import replace

from .schema import IR, Component

#: Bipoli il cui comportamento non cambia scambiando i due terminali.
SYMMETRIC: frozenset[str] = frozenset({"resistor", "capacitor", "inductor"})


def _orienta(c: Component) -> Component:
    if c.type in SYMMETRIC and c.terminals[1] < c.terminals[0]:
        return replace(c, terminals=(c.terminals[1], c.terminals[0]))
    return c


def canonicalize(ir: IR) -> IR:
    """La forma su cui due IR dello stesso circuito devono coincidere."""
    componenti = tuple(sorted(
        (_orienta(c) for c in ir.components),
        key=lambda c: (c.type, c.id, c.terminals),
    ))
    return IR(
        ir.ir_version,
        ir.domain,
        ir.source_kind,
        tuple(sorted(ir.nodes)),
        componenti,
        tuple(sorted(ir.requests, key=lambda r: r.id)),
        ir.omega,
    )
