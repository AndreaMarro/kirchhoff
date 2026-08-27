"""`Failure`: guasto tecnico, non esito di dominio.

AD-13 tiene `Refusal` e `Failure` su tipi e canali diversi. Un Rifiuto è un
atto di onestà del sistema — il circuito non si certifica, e si dice perché.
Un Failure è un difetto: qualcosa che il prodotto non doveva incontrare.

Non condividono gerarchia. Non si costruisce un Failure per un circuito
illecito, e non si costruisce un Refusal per un'eccezione inattesa.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Failure:
    """Guasto. `dove` nomina lo stadio, `messaggio` ciò che è andato storto."""

    dove: str
    messaggio: str

    def __post_init__(self) -> None:
        if not self.dove:
            raise ValueError("Failure senza stadio: non si sa dove è successo")
        if not self.messaggio:
            raise ValueError("Failure senza messaggio")

    def __str__(self) -> str:
        return f"guasto in «{self.dove}»: {self.messaggio}"
