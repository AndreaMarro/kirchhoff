"""`Refusal`: esito di dominio con controllo fallito, non guasto tecnico.

AD-13 tiene `Refusal` e `Failure` su tipi e canali diversi, perche' un Rifiuto e' un
atto di onesta' del sistema e un guasto e' un difetto: renderli sullo stesso canale
trasforma il primo nel secondo agli occhi di chi legge. Ne segue che `Refusal` **non
e' un'eccezione**: si restituisce, non si solleva.

`Failure` non vive qui: sta in `pipeline.failure`. Metterli nello stesso modulo
sarebbe condividerne il canale sotto un altro nome.

AD-19 impone che `cause` venga da un'enumerazione chiusa e che il payload porti
**sempre** `subject`, l'elemento coinvolto. Una diagnosi che nomina la regola violata
senza nominare il nodo o il componente non e' utilizzabile: FR-4 chiede che il testo
sia riusabile come Domanda mirata senza riscrittura manuale.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

Cause = Literal[
    "topology", "units", "unsolvable",
    "path_disagreement", "residual", "sanity",
    "identity_violation", "preserve_nonmaximal", "empty_boundary",
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
