"""`render/layout` — scrittore unico del `LayoutIR`, e i registri della continuita'.

AD-8: `LayoutIR` → `render/layout`, **mai** `domain/`. AD-8 v2.1 aggiunge la
ritenzione che mancava: un `LayoutIR` per nodo del `ProofGraph`, append-only, mai
sovrascritto.

Chi tiene la relazione fra nodo e layout non e' questo pacchetto: e' `ProofGraph`,
sotto `domain/proof`, perche' il proprietario del riferimento e' **il nodo**. Qui ci
sono i tre operandi che quella relazione nomina — i due `LayoutIR` e il
`LayoutPatch` — e la funzione che li congiunge, `operandi_di_vcer`.

## Il contratto che vincola chi scrivera' l'applicatore (Story 1.7)

La Story 1.3 dichiara **non-goal** il renderer, quindi qui non c'e' `applica`. La
minaccia che CV6 descrive vive pero' esattamente dentro quella funzione, e va
scritta prima che qualcuno la implementi, non dopo:

> **U2 — la lettura naturale, e quella vietata.** *«Applicare un `LayoutPatch`
> aggiorna il layout in luogo.»* Sotto U2, *«`p_k` non esiste piu' nel momento in cui
> servirebbe misurarlo»* e VCER e' incalcolabile senza rieseguire la derivazione.

Il contratto, per chi in 1.7 scrivera' l'applicatore:

    applica(prima: LayoutIR, patch: LayoutPatch, *, istante: int,
            casualita: bytes) -> LayoutIR

- **restituisce un `LayoutIR` nuovo**, con un `lay_` nuovo coniato dall'istante
  iniettato: non muta `prima`, non ne riusa l'identificatore, non lo rideposita;
- `prima` resta risolvibile dal `LayoutStore` dopo la chiamata, identica nei
  piazzamenti — e' l'AC1 di questa storia, e un applicatore in luogo lo violerebbe
  senza che nessun test di 1.7 se ne accorga;
- il risultato soddisfa le condizioni che `operandi_di_vcer` verifica: cio' che la
  patch preserva e' piazzato in entrambi, cio' che rimuove spariva, cio' che crea
  compare.

Il posto in cui questo contratto si controlla esiste gia': depositare `prima` e il
risultato nello stesso `LayoutStore` fallisce se l'applicatore riusa il `lay_`, e
`operandi_di_vcer` fallisce se il risultato non regge le cinque condizioni.
"""

from .continuity import OperandiVCER, operandi_di_vcer
from .schema import LayoutIR, Placement
from .store import LayoutStore, PatchStore

__all__ = [
    "LayoutIR",
    "LayoutStore",
    "OperandiVCER",
    "PatchStore",
    "Placement",
    "operandi_di_vcer",
]
