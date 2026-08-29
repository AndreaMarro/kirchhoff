"""`DerivationState`: progresso matematico esatto ancorato a un nodo di prova.

Non è un secondo `CircuitIR` e non è un CAS. Registra variabili nodali,
legami con i nodi del circuito, le convenzioni già poste e le equazioni
ormai attive. Puro.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
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


@dataclass(frozen=True, slots=True, order=True)
class NodalTerm:
    """Termine di conducibilità in una KCL: G · (v_plus − v_minus).

    `conductance` è esatta (`Fraction`). Nessun float, nessuna stringa come
    unica fonte semantica.
    """

    component: str
    conductance: Fraction
    plus_node: str
    minus_node: str

    def __post_init__(self) -> None:
        if not isinstance(self.conductance, Fraction):
            raise TypeError(
                f"{self.component}: conductance {type(self.conductance).__name__}, "
                "serve una Fraction")
        if self.conductance <= 0:
            raise ValueError(
                f"{self.component}: conductance non positiva ({self.conductance})")
        if self.plus_node == self.minus_node:
            raise ValueError(
                f"{self.component}: termine KCL fra lo stesso nodo {self.plus_node}")


@dataclass(frozen=True, slots=True)
class ExactEquation:
    """Equazione strutturata. Il rendering può aggiungersi dopo; il contenuto è qui."""

    kind: str
    node: str
    terms: tuple[NodalTerm, ...]

    def __post_init__(self) -> None:
        if self.kind != "kcl":
            raise ValueError(
                f"equazione {self.kind!r}: in questo slice esiste solo kind 'kcl'")
        if not self.node:
            raise ValueError("KCL senza nodo")
        object.__setattr__(self, "terms", tuple(sorted(self.terms)))
        if not self.terms:
            raise ValueError(f"KCL al nodo {self.node} senza termini")


@dataclass(frozen=True, slots=True)
class DerivationState:
    """Stato matematico immutabile. L'identificatore è locale alla derivazione."""

    identifier: str
    proof_node: str
    reference_node: str | None = None
    variables: tuple[NodalVariable, ...] = ()
    assumptions: tuple[str, ...] = ()
    equations: tuple[ExactEquation, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("DerivationState senza identificatore")
        if not self.proof_node:
            raise ValueError(f"{self.identifier}: manca il riferimento al ProofNode")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(self, "equations", tuple(self.equations))
        for eq in self.equations:
            if not isinstance(eq, ExactEquation):
                raise TypeError(
                    f"{self.identifier}: {type(eq).__name__} fra le equazioni "
                    "invece di ExactEquation")
        viste = list(self.equations)
        doppie = [eq for i, eq in enumerate(viste) if eq in viste[:i]]
        if doppie:
            raise ValueError(
                f"{self.identifier}: equazioni duplicate "
                f"{', '.join(f'{eq.kind}@{eq.node}' for eq in doppie)}")
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
