"""Forma canonica dell'IR: ordinare l'arbitrario, non toccare il resto.

Due descrizioni dello stesso circuito possono elencare i componenti in ordine
diverso, i nodi in ordine diverso, e nominare i due capi di un resistore
nell'ordine che capita. Nessuna di queste differenze dice qualcosa del circuito, e
finché sopravvivono i due IR non si possono confrontare.

L'ordine dei terminali di un **generatore** invece dice qualcosa: è la polarità.
Riordinarlo produrrebbe un circuito diverso che si dichiara uguale — l'errore
silenzioso che il prodotto esiste per prevenire. Per questo la simmetria si applica
solo ai bipoli che sono davvero simmetrici.

I nodi di controllo di una sorgente controllata fanno parte dell'identità:
lo stesso ramo di uscita con un altro (cp, cq) è un altro componente.

Pura e idempotente: restituisce un nuovo IR e non tocca quello ricevuto.
"""

from __future__ import annotations

from dataclasses import replace

from .schema import IR, Component

#: Bipoli il cui comportamento non cambia scambiando i due terminali.
SYMMETRIC: frozenset[str] = frozenset({"resistor", "capacitor", "inductor"})


def orienta(c: Component) -> Component:
    """L'orientamento canonico di un bipolo simmetrico. Identita' per gli altri.

    **Pubblica perche' serve fuori di qui.** `domain/transform/check` deve
    confrontare i terminali di due componenti per decidere se sono la stessa
    entita', e farlo per uguaglianza sintattica di tupla contraddiceva questo
    stesso modulo: due IR che `canonicalize` dichiara identici davano `Pₖ` diversi,
    e un passo che non toccava nulla riceveva quattro violazioni. Una falsa accusa.

    Riusare la regola invece di riscriverla e' E-62: due definizioni della stessa
    simmetria divergerebbero nel posto dove nessuno guarda, e questa decide se
    un'entita' e' la stessa.
    """
    if c.type in SYMMETRIC and c.terminals[1] < c.terminals[0]:
        return replace(c, terminals=(c.terminals[1], c.terminals[0]))
    return c


def canonicalize(ir: IR) -> IR:
    """La forma su cui due IR dello stesso circuito devono coincidere."""
    componenti = tuple(sorted(
        (orienta(c) for c in ir.components),
        key=lambda c: (c.type, c.id, c.terminals, c.control_nodes),
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
