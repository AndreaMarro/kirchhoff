"""`render/step` — il passo come oggetto: due fotogrammi, e le risposte gia' pronte.

E' il punto in cui la continuita' visuale smette di essere una promessa e diventa
misurabile: i due stati escono dalla **stessa** sorgente semantica (AD-10), il
rendering e' puro (AD-35), e cio' che sta in `preserve` si puo' confrontare fra i
due disegni invece che dentro uno solo (A-0).

Due moduli, e la linea che li separa e' fra **costruire** e **rispondere**:

- `compose.componi` mette in fila i cinque atti di un passo — la sequenza che
  K-0 richiede e che prima di questa storia viveva solo dentro un file di test;
- `schema` porta i tipi: `VisualStep` (la proiezione per riferimento),
  `InteractionState` (la quarta rappresentazione di AD-21), `Justification` (i
  quattro campi di UX-DR23) e `StaticStep` (la forma per l'export).

Il pacchetto **non pubblica e non marca**: `publish()` e i suoi otto controlli
sono AD-5, la Marcatura di provenienza e' FR-18/FR-19. Compone un passo, e non
afferma niente sulla sua certificazione oltre a cio' che il `Certificate` che
porta gia' dice.
"""

from .compose import componi
from .schema import InteractionState, Justification, StaticStep, VisualStep

__all__ = [
    "InteractionState",
    "Justification",
    "StaticStep",
    "VisualStep",
    "componi",
]
