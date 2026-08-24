"""Oracolo dei transitori: stato iniziale, regime permanente, frequenze naturali.

Un esercizio di transitorio non chiede la funzione del tempo: chiede la costante di
tempo, il valore iniziale, il valore finale, e per il secondo ordine le radici
dell'equazione caratteristica. Tutte queste grandezze sono razionali, quindi
l'oracolo resta esatto e nessuna esponenziale compare mai.

Le tre risposte si ottengono per sostituzione strutturale, non per formula:

    a regime      il condensatore e' un circuito aperto, l'induttore un corto
    a t = 0+      a stato zero il condensatore scarico e' un corto, l'induttore
                  a corrente nulla un aperto
    frequenze     `s` e' una frequenza naturale quando la matrice MNA della rete
    naturali      a sorgenti spente e' singolare in `s`

L'ultima e' la definizione stessa, e vale per qualunque topologia: chi genera un
caso sceglie le radici e ne deriva i componenti, chi verifica parte dai componenti
e chiede alla matrice se quelle radici la annullano. Le due vie non si incontrano
mai a meta' strada.

Puro: nessuna I/O, nessuna casualita', nessun orologio.
"""

from __future__ import annotations

from fractions import Fraction

from .exact import determinant
from .ir import IR, Component
from .mna import mna_matrix_at, solve_dc

ZERO = Fraction(0)

#: La grandezza che caratterizza un componente in un transitorio. Un condensatore
#: si racconta con la sua tensione, tutto il resto con la propria corrente.
CHARACTERISTIC_QUANTITY: dict[str, str] = {
    "capacitor": "voltage",
    "inductor": "current",
    "resistor": "current",
    "voltage_source_dc": "current",
    "current_source_dc": "voltage",
}


def _substitute(ir: IR, capacitor_as: str, inductor_as: str) -> IR:
    """Sostituisce gli elementi di accumulo con l'equivalente richiesto, a zero."""
    comps: list[Component] = []
    for c in ir.components:
        if c.type == "capacitor":
            comps.append(Component.of(c.id, capacitor_as, c.terminals, ZERO, c.symbolic))  # type: ignore[arg-type]
        elif c.type == "inductor":
            comps.append(Component.of(c.id, inductor_as, c.terminals, ZERO, c.symbolic))  # type: ignore[arg-type]
        else:
            comps.append(c)
    return IR(ir.ir_version, ir.domain, ir.source_kind, ir.nodes, tuple(comps),
              ir.requests, ir.omega)


def steady_state(ir: IR) -> dict[str, dict[str, Fraction]]:
    """Soluzione a t che tende a infinito: condensatore aperto, induttore in corto."""
    return solve_dc(_substitute(ir, "current_source_dc", "voltage_source_dc"))


def initial_state(ir: IR) -> dict[str, dict[str, Fraction]]:
    """Soluzione a t = 0+, a stato zero: condensatore in corto, induttore aperto."""
    return solve_dc(_substitute(ir, "voltage_source_dc", "current_source_dc"))


def is_natural_frequency(ir: IR, s: Fraction) -> bool:
    """Vero quando la matrice MNA a sorgenti spente e' singolare in `s`."""
    return determinant(mna_matrix_at(ir, s)) == 0
