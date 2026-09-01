"""Refusal: esito di dominio con controllo fallito, non guasto tecnico."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

Cause = Literal[
    "topology", "units", "unsolvable",
    "path_disagreement", "residual", "sanity",
    "identity_violation", "preserve_nonmaximal", "empty_boundary",
    "claim_unsupported",
]

SubjectKind = Literal["node", "component", "request", "operation"]

CAUSES: frozenset[str] = frozenset(get_args(Cause))
SUBJECT_KINDS: frozenset[str] = frozenset(get_args(SubjectKind))


@dataclass(frozen=True, slots=True)
class Refusal:
    """Controllo fallito, elemento coinvolto, diagnosi leggibile."""

    cause: Cause
    subject: str
    subject_kind: SubjectKind
    diagnosis: str

    def __post_init__(self) -> None:
        if self.cause not in CAUSES:
            raise ValueError(
                f"causa {self.cause!r} fuori dall'enumerazione chiusa: "
                f"{', '.join(sorted(CAUSES))}. Aggiungerne una e' una modifica dello spine.")
        if self.subject_kind not in SUBJECT_KINDS:
            raise ValueError(f"genere di soggetto {self.subject_kind!r} sconosciuto")
        if not self.subject:
            raise ValueError(
                "Rifiuto senza soggetto: una diagnosi che non nomina l'elemento coinvolto "
                "non e' riusabile come Domanda mirata (FR-4, AD-19)")
        if not self.diagnosis:
            raise ValueError("Rifiuto senza diagnosi")

    def __str__(self) -> str:
        return f"rifiutato da «{self.cause}» su {self.subject}: {self.diagnosis}"
