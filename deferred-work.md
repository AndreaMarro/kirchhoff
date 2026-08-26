
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

### 3. Niente compone il passo dentro `src/` — **CHIUSO dalla Story 1.8**

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

**Chiuso il 26/08/2026.** `render/step/compose.componi` mette in fila i cinque atti,
e i tre nomi hanno ora un chiamante vero in `src/` — verificato con `grep` sulle sole
chiamate, non per lettura:

    annota(   → compose.py:85
    applica(  → compose.py:82
    render(   → compose.py:108 e :109

Non e' stato chiuso *scegliendo* dove vive il punto di composizione del prodotto —
quella resta la decisione di architettura che questa voce segnalava, e `pipeline/`,
`api/` e `adapters/` restano vuoti. E' stato chiuso perche' la Story 1.8 **non e'
scrivibile senza**: percorrere avanti e indietro un passaggio richiede che il
passaggio sia un oggetto, e un oggetto lo costruisce qualcuno. Il punto vive in
`render/` perche' e' l'unico pacchetto che gia' puo' vedere sia il prodotto del
dominio sia i due registri del layout; se domani `pipeline/` reclama quel ruolo, a
spostarsi e' una funzione, non un tipo.

**Le voci 1 e 2 restano aperte e non sono state toccate.** Nessuna delle due e'
nominata dai criteri della Story 1.8.

## Story 1.8 — quattro rilievi della revisione, registrati e non chiusi

Il revisore ne ha prodotti dieci. Sei sono stati riparati nella stessa iterazione —
le guardie di `StaticStep`, la guardia sui due disegni di `VisualStep`, la guardia
sull'entita' estranea nelle tre risposte di FR-49, le due precondizioni esigite e
non dichiarate, il controllo di forma su `_verifica_precondizioni`, i due oracoli
che sostituivano un simbolo irraggiungibile — e la catena di due passi ha ora un
test che la percorre davvero. I quattro che seguono restano aperti, ciascuno con la
misura che lo rende ritrovabile e la ragione per cui chiuderlo e' una decisione e
non una manutenzione.

Misurati il 26/08/2026, ciascuno verificato per esecuzione e non per lettura.

### 4. Le due `viewBox` del passo differiscono di origine **e** di dimensione

Misurato: `prima` = `-24 -36.8 543.4 224.8`, `dopo` = `-24 -28.8 493.4 216.8`.
L'`<svg>` non porta `width`/`height` — scala col contenitore (UX-DR27) — quindi
commutando dentro un riquadro di larghezza fissa ogni entita' preservata si sposta
**a schermo**, pur non essendosi mossa in spazio utente.

UX-DR17 definisce A-0 come invariante *«semantico-spaziale, non pixel-perfect»*:
`p_{k+1}(x) ≈ p_k(x)` *«salvo necessita' geometriche dimostrabili, comunque misurate
e penalizzate da VCER»*. `TestA0FraIDueStati` confronta coordinate in spazio utente,
che e' esattamente cio' che `p_k(x)` significa: **quei test misurano la cosa giusta**,
e il rilievo non li falsifica. Cio' che mancava e' la misura della necessita'
geometrica, che UX-DR17 non lascia facoltativa.

**Perche' resta aperto:** unificare le due `viewBox` significa decidere che i due
fotogrammi di un passo condividono un riquadro, cioe' scegliere quale delle due
letture di FR-53 governi — la decisione che la voce corrispondente della Story 1.7
ha registrato per non chiudere D4 per inerzia (*«renderer stack web vs PDF»*, aperta,
blocca Gate A). Il rilievo della 1.7 riguardava *overlay vs senza overlay*, dove
l'**origine restava uguale**; questa e' la variante *fra i due fotogrammi dello
stesso passo*, e ha una forma diversa.

**Gate installato:** `TestLeMisureRegistrate::test_i_due_fotogrammi_hanno_viewbox_
diverse`. Non ripara: fissa la misura, e fa fallire chi cambia il comportamento
senza prendere la decisione.

### 5. Il fotogramma d'apertura porta gia' l'equazione del passo

Misurato: il layer 6 di `fotogrammi[prima]` emette
`<text class="kf-equazione-testo">R1R2eq = R1 + R2</text>` — il nome dell'equivalente
che in `Cₖ` non esiste, e la sua formula. `apertura()` restituisce `prima` con un
docstring che invoca UX-DR22 (*«aprire su `dopo` mostrerebbe il passo gia'
compiuto»*), e il fotogramma d'apertura enuncia il passo compiuto lo stesso. La
causa e' la scelta di `componi` di usare **un solo overlay** per i due render, che
porta con se' l'equazione su entrambi.

`test_cio_che_cambia_invece_non_compare_in_entrambi` sta accanto al fatto e non lo
vede: asserisce che `R1R2eq` non e' fra i `data-component-id` di `prima` — vero — e
non guarda il testo del layer 6.

**Perche' resta aperto:** `EXPERIENCE.md` distingue **tre** momenti — 3-4 *PRIMA*
(*«non e' ancora comparso un solo carattere di testo»*), 5 *AZIONE* (l'equazione
compare), 6 *DOPO* — e `VisualStep` ne ha **due**. Decidere a quale dei due
fotogrammi appartenga l'equazione e' una scelta di sequenza UX che nessun criterio
della Story 1.8 prende, e realizzarla richiede di rendere opzionale
`TransformOverlay.equazione`, cioe' allentare una guardia che la Story 1.7 ha
scritto apposta e che il docstring di `overlay/schema.py` difende per esteso.

**Gate installato:** `TestLeMisureRegistrate::test_il_fotogramma_di_apertura_porta_
gia_l_equazione_del_passo`.

### 6. `componi` conia due identificatori dalla stessa entropia

Misurato: `lay_01K2F2DMF8000G40R40M30E209` e `patch_01K2F2DMF8000G40R40M30E209` —
26 cifre identiche, ciascuna ricavabile dall'altra. Un solo `(istante, casualita)`
alimenta il conio dentro `applica` e quello dentro `patches.deposita`.

**Il danno oggi e' nullo, e va detto:** i due generi hanno prefissi diversi, quindi
non collidono in nessun registro — e la collisione e' precisamente la ragione per
cui `conia` chiede entropia nuova. Cio' che e' violato e' il **contratto
dichiarato** (`conia`: *«nuovi a ogni conio»*; `PatchStore.deposita`: *«entropia
nuova a ogni chiamata»*), e il costo si presenta il giorno in cui `componi` conia
due identificatori dello **stesso** genere.

**Perche' resta aperto:** le due strade sono cambiare la firma pubblica di `componi`
perche' accetti due entropie, o derivarne una seconda da quella ricevuta — cioe'
introdurre un meccanismo di derivazione che nessun port dello spine nomina. Il
docstring di `domain/identity` registra gia' che **non esiste un `EntropyPort`**: e'
la stessa lacuna, e va chiusa li' e non con un'invenzione locale.

**Gate installato:** `TestLeMisureRegistrate::test_i_due_identificatori_del_passo_
nascono_dalla_stessa_entropia`.

### 7. `PRECONDITIONS` — il verso *esigita → dichiarata* non e' meccanizzabile

Le due condizioni comuni alle due riduzioni — i componenti nominati esistono
(porta di `transform`, `engine.py:656`, prima dello smistamento) e sono entrambi
resistori (`engine._resistore`, `engine.py:192`) — erano esigite e non dichiarate. Sono state **aggiunte**, e
ognuna ha ora il circuito che la vede respingere (`TestLePrecondizioniSonoFalsificabili`).

Cio' che resta aperto e' il verso, non le due righe. `_verifica_le_precondizioni_
degli_implementati` controlla che l'elenco di un'operazione implementata non sia
vuoto; `TestLePrecondizioniSonoFalsificabili` controlla *dichiarata → esigita*. Il
verso *esigita → dichiarata* — «ogni guardia che respinge un circuito ha una riga
nell'elenco» — non e' controllato da niente, e non e' meccanizzabile senza una
relazione esplicita fra ciascuna guardia e la propria riga.

La suite contiene gia' il controesempio che lo dimostra irriducibile:
`test_un_rifiuto_si_restituisce_e_non_lascia_niente_nei_registri` costruisce un
`parallelo` in cui **tutte** le precondizioni dichiarate sono soddisfatte e il passo
e' rifiutato lo stesso — da `validate` sul prodotto, non da una guardia
dell'operazione. Un elenco completo delle precondizioni non renderebbe quel rifiuto
prevedibile, perche' la condizione che manca non e' una precondizione: e' una
proprieta' di `Cₖ₊₁`. Distinguere le due e' semantica di FR-49, non manutenzione.

**Nessun gate installato**, e la ragione e' che un gate qui sarebbe il gate scritto e
non installato al contrario: un controllo che non puo' fallire.
