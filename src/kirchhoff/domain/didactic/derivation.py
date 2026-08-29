"""`DerivationState`: progresso matematico esatto ancorato a un nodo di prova.

Non è un secondo `CircuitIR` e non è un CAS. Registra variabili nodali,
legami con i nodi del circuito, e le convenzioni già poste. Puro.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..ir import REFERENCE_NODE


VariableRole = Literal["reference", "unknown", "known_from_source"]
ROLES: frozenset[str] = frozenset(("reference", "unknown", "known_from_source"))


@dataclass(frozen=True, slots=True, order=True)
class NodalVariable:
    """Una tensione nodale legata a un nodo reale del circuito."""

    name: str
    node: str
    role: str
    source_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("variabile nodale senza nome")
        if not self.node:
            raise ValueError(f"{self.name}: variabile senza nodo")
        if self.role not in ROLES:
            raise ValueError(
                f"{self.name}: ruolo {self.role!r} fuori da {', '.join(sorted(ROLES))}")
        if self.role == "known_from_source" and not self.source_id:
            raise ValueError(
                f"{self.name}: tensione nota da generatore senza source_id")
        if self.role != "known_from_source" and self.source_id is not None:
            raise ValueError(
                f"{self.name}: source_id su un ruolo {self.role}")


@dataclass(frozen=True, slots=True)
class DerivationState:
    """Stato matematico immutabile. L'identificatore è locale alla derivazione."""

    identifier: str
    proof_node: str
    reference_node: str | None = None
    variables: tuple[NodalVariable, ...] = ()
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("DerivationState senza identificatore")
        if not self.proof_node:
            raise ValueError(f"{self.identifier}: manca il riferimento al ProofNode")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        nomi = [v.name for v in self.variables]
        doppi = sorted({n for n in nomi if nomi.count(n) > 1})
        if doppi:
            raise ValueError(f"{self.identifier}: variabili ripetute {', '.join(doppi)}")
        nodi = [v.node for v in self.variables]
        doppi_n = sorted({n for n in nodi if nodi.count(n) > 1})
        if doppi_n:
            raise ValueError(
                f"{self.identifier}: due variabili sullo stesso nodo {', '.join(doppi_n)}")
        if self.reference_node == "":
            raise ValueError(f"{self.identifier}: reference_node vuoto")

    def variabile_del_nodo(self, nodo: str) -> NodalVariable:
        for v in self.variables:
            if v.node == nodo:
                return v
        raise KeyError(nodo)


def nome_tensione(nodo: str) -> str:
    """Nome deterministico della tensione nodale. Il riferimento resta `v_0`."""
    if nodo == REFERENCE_NODE:
        return "v_0"
    return f"v_{nodo}"
