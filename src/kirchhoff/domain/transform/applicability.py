"""Query pura sulle riduzioni realmente eseguibili su un circuito.

Una sola fonte per le guardie di serie e parallelo: le stesse precondizioni
topologiche che `engine._serie` e `engine._parallelo` impongono prima di
produrre un prodotto. Non esegue la trasformazione e non materializza un
`CircuitIR` successivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..ir import IR, REFERENCE_NODE, Component


@dataclass(frozen=True, slots=True, order=True)
class ExecutableTransform:
    """Operazione certificata applicabile a una coppia concreta, senza eseguirla."""

    operation: str
    first: str
    second: str

    @property
    def operands(self) -> tuple[str, str]:
        return (self.first, self.second)


def motivo_non_serie(ir: IR, a: Component, b: Component) -> str | None:
    """Perché la coppia non è una serie eseguibile, o `None` se lo è."""
    comune = set(a.terminals) & set(b.terminals)
    if len(comune) != 1:
        return (
            f"{a.id} e {b.id} condividono {len(comune)} nodi: la serie ne vuole "
            "esattamente uno.")
    nodo = next(iter(comune))
    if nodo == REFERENCE_NODE:
        return (
            f"{a.id} e {b.id} si toccano nel nodo di riferimento {nodo}: "
            "la serie elimina il nodo comune, e quello non si elimina perche' e' il "
            "potenziale rispetto a cui ogni tensione e' definita. Serve prima un "
            "altro riferimento, che non e' una Trasformazione del catalogo.")
    tocca = [c.id for c in ir.components if nodo in c.terminals]
    if len(tocca) != 2:
        return (
            f"il nodo {nodo} ha grado {len(tocca)} ({', '.join(sorted(tocca))}): "
            "in serie ci stanno due componenti soli, altrimenti la corrente si "
            "divide e la somma delle resistenze non e' l'equivalente.")
    return None


def motivo_non_parallelo(a: Component, b: Component) -> str | None:
    """Perché la coppia non è un parallelo eseguibile, o `None` se lo è."""
    if set(a.terminals) != set(b.terminals):
        return (
            f"{a.id} {a.terminals} e {b.id} {b.terminals} non stanno fra gli "
            "stessi due nodi: non sono in parallelo.")
    return None


def serie_applicabile(ir: IR, a: Component, b: Component) -> bool:
    return motivo_non_serie(ir, a, b) is None


def parallelo_applicabile(a: Component, b: Component) -> bool:
    return motivo_non_parallelo(a, b) is None


def enumerate_executable_transforms(ir: IR) -> tuple[ExecutableTransform, ...]:
    """Le riduzioni con corpo e precondizioni topologiche soddisfatte su questo IR.

    L'ordine è canonico: operazione, poi i due identificatori già ordinati.
    Permutare i componenti dell'IR non cambia il risultato. Non esegue il passo.
    """
    from .engine import implemented

    corpo = implemented()
    resistori = tuple(c for c in ir.components if c.type == "resistor")
    trovate: list[ExecutableTransform] = []
    for a, b in combinations(resistori, 2):
        primo, secondo = sorted((a.id, b.id))
        ca, cb = ir.component(primo), ir.component(secondo)
        if "serie" in corpo and serie_applicabile(ir, ca, cb):
            trovate.append(ExecutableTransform("serie", primo, secondo))
        if "parallelo" in corpo and parallelo_applicabile(ca, cb):
            trovate.append(ExecutableTransform("parallelo", primo, secondo))
    return tuple(sorted(trovate))
