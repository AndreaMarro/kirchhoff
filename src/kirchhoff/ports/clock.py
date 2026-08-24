"""`ClockPort` — l'unico modo di sapere che ore sono (AD-17).

Nessun modulo chiama direttamente l'orologio di sistema: il tempo si inietta. La
ragione è che un transitorio, una scadenza di `resume_ref` e un TTL di immagine
sono tutti verificabili solo se l'orologio si può fermare, e un `datetime.now()`
sparso nel codice non si ferma.

`domain/` non importa nemmeno questo: le Trasformazioni sono pure e non hanno
bisogno di sapere l'ora. Il controllo dei confini lo impone.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Restituisce l'istante corrente in UTC, con offset esplicito (convenzioni)."""

    def now(self) -> datetime:
        raise NotImplementedError
