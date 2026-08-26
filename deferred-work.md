
## Story 1.7 — tre rilievi della ri-revisione, registrati e non chiusi

Misurati il 26/08/2026, ciascuno verificato per esecuzione e non per lettura.

### 1. La guardia FR-38 in `applica` non puo' fallire su cio' che il motore produce

`engine.py:249` scrive `reroute_scope=(prodotto, *boundary.entities)`, `patch.create`
e' `(prodotto,)`, e `applica` riusa gli oggetti `Placement` dei preservati: quindi le
mosse coincidono con `create`, incluso in `reroute_scope`, per costruzione. Misurato
sul passo della storia: `mosse = {component:R1R2eq}`, `reroute_scope =
{component:R1R2eq, node:0, node:b}`. L'unico test che la vede sollevare costruisce
una patch a mano.

Ne segue che l'affermazione in `result.py` — «Ne segue che l'unita' e' l'entita'» —
non e' sostenuta dal consumatore che la cita: nulla nel controllo distingue entita'
da ramo, perche' i nodi di boundary nello scope non si muovono mai.

**Perche' resta aperto:** una guardia vacua sul percorso interno e' un difetto E-65,
ma renderla efficace significa decidere COSA deve poter fallire, e quella e' la
semantica di FR-38.

### 2. `TransformOverlay` ammette `confine` e `preservato` vuoti

`__post_init__` guarda `cambiato` e non i suoi fratelli, mentre a monte `Boundary`
rifiuta un confine vuoto — «un sottografo che non confina con nulla non e' un passo,
e' una riscrittura» — e AD-22 vuole `preserve` non vuoto. Misurato:
`TransformOverlay((C('R1'),), (), (), eq)` si costruisce, e `render` emette un layer
6 con zero ancore.

**Riparazione tentata e RITIRATA il 26/08/2026.** Aggiunte le due guardie mancanti,
quattro test esistenti sono diventati rossi: costruiscono l'overlay con quei campi
vuoti di proposito, per isolare altre guardie. Chiudere il rilievo rompendo i loro
test significherebbe decidere se `TransformOverlay` e' un oggetto stretto derivato
dal prodotto o una vista permissiva — e quella e' architettura, non manutenzione.

### 3. Niente compone il passo dentro `src/`

`annota` ha ZERO chiamanti in `src/` fuori dalla propria definizione (verificato con
grep sulle sole chiamate); le occorrenze di `applica` e `render` sono firme e
docstring. La sequenza che K-0 chiede — transform, applica, annota, render — esiste
solo dentro `_passo()` nel file di test, che e' anche l'unico posto in cui gli AC
della storia sono scritti: non esiste `spec-1-7-*` in `implementation-artifacts/`,
mentre 1.1, 1.3 e 1.4 ce l'hanno.

**Contesto che ridimensiona il rilievo:** `pipeline/`, `api/` e `adapters/` erano
gia' vuoti su `main` PRIMA di questa storia — 0 righe ciascuno, verificato con
`git show main:`. Il buco precede 1.7 e gli AC non chiedono di chiuderlo. Scegliere
qui dove vive il punto di composizione del prodotto e' una decisione di architettura.
