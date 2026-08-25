"""`Refusal`: esito di dominio con controllo fallito, non guasto tecnico.

AD-13 tiene `Refusal` e `Failure` su tipi e canali diversi, perche' un Rifiuto e' un
atto di onesta' del sistema e un guasto e' un difetto: renderli sullo stesso canale
trasforma il primo nel secondo agli occhi di chi legge. Ne segue che `Refusal` **non
e' un'eccezione**: si restituisce, non si solleva.

AD-19 impone che `cause` venga da un'enumerazione chiusa e che il payload porti
**sempre** `subject`, l'elemento coinvolto. Una diagnosi che nomina la regola violata
senza nominare il nodo o il componente non e' utilizzabile: FR-4 chiede che il testo
sia riusabile come Domanda mirata senza riscrittura manuale.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

#: Cause emesse da `domain/validate` (AD-19, riga v1 della tabella) e, dalla
#: Story 2.6, da `domain/transform/check` (righe v2 della stessa tabella).
#:
#: Le tre cause di trasformazione arrivano **adesso** e non prima perche' prima non
#: esisteva lo stadio che le emette: `domain/validate` sta *prima* che una
#: trasformazione esista, e infatti nessuna delle sue tre cause copriva «una entita'
#: preservata ha cambiato identita'». Uno stadio obbligato a rifiutare senza una
#: causa legale degrada a eccezione generica o a `sanity`, e in entrambi i casi
#: l'utente perde la localizzazione, che e' cio' che K-3 promette (AD-19 em.).
#:
#: Le cause di `domain/verify`, `render/`, `domain/truthfulness`, `perception/` e
#: `corpus/` vivranno accanto a queste quando quegli stadi nasceranno:
#: l'enumerazione e' chiusa, non privata. Aggiungerne una **non** e' una modifica di
#: questo modulo: e' una modifica dello spine, gia' scritta nella tabella di AD-19.
Cause = Literal[
    # domain/validate — v1
    "topology", "units", "unsolvable",
    # domain/transform/check — v2
    "identity_violation", "preserve_nonmaximal", "empty_boundary",
]

SubjectKind = Literal["node", "component", "request"]

# **Una sola fonte autoritativa.** Questi due insiemi erano scritti a mano accanto
# ai `Literal` e tenuti allineati dalla disciplina di chi modificava: e' il gesto
# che E-62 descrive — un vocabolario scritto due volte diverge, e diverge nel posto
# dove nessuno guarda. Derivandoli, la divergenza non e' piu' evitata: e' impossibile.
# `get_args` su un `Literal` restituisce i suoi membri nell'ordine di dichiarazione.
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
