"""`DerivationState`: progresso matematico esatto ancorato a un nodo di prova.

Non è un secondo `CircuitIR` e non è un CAS. Registra variabili nodali,
legami con i nodi del circuito, le convenzioni già poste e le equazioni
lineari ormai attive. Puro.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from ..ir import REFERENCE_NODE


VariableRole = Literal["reference", "unknown", "known_from_source"]
ROLES: frozenset[str] = frozenset(("reference", "unknown", "known_from_source"))

VariableKind = Literal["node_voltage"]
VARIABLE_KINDS: frozenset[str] = frozenset(("node_voltage",))

EquationKind = Literal["kcl", "voltage_constraint"]
EQUATION_KINDS: frozenset[str] = frozenset(("kcl", "voltage_constraint"))


@dataclass(frozen=True, slots=True, order=True)
class VariableRef:
    """Identità matematica di una variabile. Il rendering non è autorità."""

    kind: str
    node: str

    def __post_init__(self) -> None:
        if self.kind not in VARIABLE_KINDS:
            raise ValueError(
                f"variabile kind {self.kind!r} fuori da "
                f"{', '.join(sorted(VARIABLE_KINDS))}")
        if not self.node:
            raise ValueError("variabile nodale senza nodo")


@dataclass(frozen=True, slots=True)
class LinearTerm:
    """Termine algebrico `coefficient * variable`. Nessun float, nessun rendering."""

    coefficient: Fraction
    variable: VariableRef

    def __post_init__(self) -> None:
        if not isinstance(self.coefficient, Fraction):
            raise TypeError(
                f"coefficiente {type(self.coefficient).__name__}, serve una Fraction")
        if self.coefficient == 0:
            raise ValueError("termine lineare con coefficiente nullo")
        if not isinstance(self.variable, VariableRef):
            raise TypeError(
                f"variabile {type(self.variable).__name__}, serve un VariableRef")


@dataclass(frozen=True, slots=True, order=True)
class NodalVariable:
    """Dichiarazione di una tensione nodale nello stato di derivazione.

    L'identità matematica della variabile è `VariableRef`. Qui stanno
    ruolo didattico e, se serve, il generatore che la fissa.
    """

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

    def ref(self) -> VariableRef:
        """Identità matematica corrispondente a questa dichiarazione."""
        return VariableRef("node_voltage", self.node)


@dataclass(frozen=True, slots=True)
class ExactEquation:
    """Equazione lineare esatta `Σ a_i x_i = b`.

    Autorità matematica: `terms` e `rhs`. `kind` e `focus` sono metadata
    didattici (specie e ancoraggio topologico), distinti dall'algebra.
    """

    kind: str
    terms: tuple[LinearTerm, ...]
    rhs: Fraction
    focus: str = ""

    def __post_init__(self) -> None:
        if self.kind not in EQUATION_KINDS:
            raise ValueError(
                f"equazione {self.kind!r}: kind fuori da "
                f"{', '.join(sorted(EQUATION_KINDS))}")
        if self.kind == "kcl" and not self.focus:
            raise ValueError("KCL senza nodo")
        if not isinstance(self.rhs, Fraction):
            raise TypeError(
                f"rhs {type(self.rhs).__name__}, serve una Fraction")
        object.__setattr__(self, "terms", _termini_canonici(self.terms))
        if not self.terms:
            raise ValueError(
                f"equazione {self.kind} senza variabili dopo la canonicalizzazione")


def _termini_canonici(termini: tuple[LinearTerm, ...] | list[LinearTerm]) -> tuple[LinearTerm, ...]:
    """Aggrega i coefficienti per variabile, scarta i nulli, ordina per `VariableRef`."""
    acc: dict[VariableRef, Fraction] = {}
    for termine in termini:
        if not isinstance(termine, LinearTerm):
            raise TypeError(
                f"{type(termine).__name__} fra i termini invece di LinearTerm")
        acc[termine.variable] = acc.get(termine.variable, Fraction(0)) + termine.coefficient
    vivi = [
        LinearTerm(coeff, variabile)
        for variabile, coeff in acc.items()
        if coeff != 0
    ]
    vivi.sort(key=lambda t: t.variable)
    return tuple(vivi)


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
                f"{', '.join(_etichetta(eq) for eq in doppie)}")
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


def _etichetta(eq: ExactEquation) -> str:
    return f"{eq.kind}@{eq.focus}" if eq.focus else eq.kind


def nome_tensione(nodo: str) -> str:
    """Nome deterministico della tensione nodale. Il riferimento resta `v_0`.

    È rendering derivabile, non identità matematica.
    """
    if nodo == REFERENCE_NODE:
        return "v_0"
    return f"v_{nodo}"


def tensione_nodo(nodo: str) -> VariableRef:
    """Riferimento matematico alla tensione del nodo `nodo` del CircuitIR."""
    return VariableRef("node_voltage", nodo)
