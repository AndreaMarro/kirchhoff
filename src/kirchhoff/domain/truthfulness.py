"""Claim di dominio: nessuna evidenza, nessuna affermazione."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Literal, get_args

from .identity import verifica

ClaimType = Literal["resolved_quantity"]
ClaimStatus = Literal["VERIFIED"]

CLAIM_TYPES: frozenset[str] = frozenset(get_args(ClaimType))
CLAIM_STATUSES: frozenset[str] = frozenset(get_args(ClaimStatus))
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _normalizza_ids(nome: str, ids: Iterable[str]) -> tuple[str, ...]:
    if isinstance(ids, str):
        raise TypeError(f"{nome} deve essere una sequenza di identificatori, non una stringa")
    normalizzati = tuple(ids)
    if not normalizzati:
        raise ValueError(f"{nome} non puo' essere vuoto")
    for identifier in normalizzati:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{nome} contiene un identificatore vuoto o non testuale")
    if len(set(normalizzati)) != len(normalizzati):
        raise ValueError(f"{nome} contiene identificatori duplicati")
    return normalizzati


@dataclass(frozen=True, slots=True)
class Claim:
    """Affermazione verificata con stato, soggetti ed evidenze ispezionabili."""

    claim_type: ClaimType
    state_id: str
    subject_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verifier_id: str
    verifier_version: str
    status: ClaimStatus = "VERIFIED"

    def __post_init__(self) -> None:
        if self.claim_type not in CLAIM_TYPES:
            raise ValueError(
                f"claim_type {self.claim_type!r} fuori dal vocabolario chiuso: "
                f"{', '.join(sorted(CLAIM_TYPES))}")
        object.__setattr__(self, "state_id", verifica(self.state_id, "ir"))
        object.__setattr__(self, "subject_ids", _normalizza_ids("subject_ids", self.subject_ids))
        object.__setattr__(self, "evidence_ids", _normalizza_ids("evidence_ids", self.evidence_ids))
        if not isinstance(self.verifier_id, str) or not self.verifier_id:
            raise ValueError("Claim senza verifier_id")
        if not isinstance(self.verifier_version, str) or not _SEMVER.fullmatch(self.verifier_version):
            raise ValueError("Claim con verifier_version non semantica")
        if self.status not in CLAIM_STATUSES:
            raise ValueError(
                f"status {self.status!r} fuori dal vocabolario chiuso: "
                f"{', '.join(sorted(CLAIM_STATUSES))}")


__all__ = [
    "CLAIM_STATUSES",
    "CLAIM_TYPES",
    "Claim",
    "ClaimStatus",
    "ClaimType",
]
