"""`render/layout` — scrittore unico del `LayoutIR`, e i registri della continuita'.

AD-8: `LayoutIR` → `render/layout`, **mai** `domain/`. AD-8 v2.1 aggiunge la
ritenzione che mancava: un `LayoutIR` per nodo del `ProofGraph`, append-only, mai
sovrascritto.

Chi tiene la relazione fra nodo e layout non e' questo pacchetto: e' `ProofGraph`,
sotto `domain/proof`, perche' il proprietario del riferimento e' **il nodo**. Qui ci
sono i tre operandi che quella relazione nomina — i due `LayoutIR` e il
`LayoutPatch` — e la funzione che li congiunge, `operandi_di_vcer`.

## Il contratto dell'applicatore, scritto in 1.3 e **onorato in 1.7**

La Story 1.3 dichiarava non-goal il renderer e lasciava qui il contratto di
`applica`, perche' la minaccia che CV6 descrive vive esattamente dentro quella
funzione. `apply.py` la implementa ora; il contratto resta scritto qui perche' e'
cio' che l'implementazione deve continuare a soddisfare, e la sola differenza e' la
firma — `applica` prende anche il `Delta`, per la ragione scritta nel suo docstring:
la `LayoutPatch` non porta la lineage, quindi da sola non sa da quali entita' una
creata derivi.

> **U2 — la lettura naturale, e quella vietata.** *«Applicare un `LayoutPatch`
> aggiorna il layout in luogo.»* Sotto U2, *«`p_k` non esiste piu' nel momento in cui
> servirebbe misurarlo»* e VCER e' incalcolabile senza rieseguire la derivazione.

Il contratto, che `apply.py` soddisfa:

    applica(prima: LayoutIR, patch: LayoutPatch, delta: Delta, *, istante: int,
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

Dalla Story 1.7 c'e' una quarta condizione, che il contratto del 1.3 non nominava
perche' il suo canale non aveva ancora lettori: **FR-38**, *«il rerouting delle
coordinate cambiate e' limitato allo `reroute_scope` dichiarato»*. Si calcola con
`mosse`, che e' esposta apposta — il predicato ha una meta' che `applica` non sa
produrre, e una guardia che non si puo' vedere lavorare non e' una guardia.
"""

from .apply import applica, mosse
from .continuity import OperandiVCER, operandi_di_vcer
from .schema import LayoutIR, Placement
from .store import LayoutStore, PatchStore

__all__ = [
    "LayoutIR",
    "LayoutStore",
    "OperandiVCER",
    "PatchStore",
    "Placement",
    "applica",
    "mosse",
    "operandi_di_vcer",
]
