
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

**Rettifica del 26/08/2026 (seconda revisione, contesto fresco).** La voce era
archiviata su una misura incompleta. Altre due condizioni della stessa classe erano
esigite e non dichiarate: l'**arita'** (`engine.py:648` — `transform(c, "serie",
"R1")` → `ValueError: vuole 2 identificatori`) e la **validita' elettrica di `Cₖ`**
(`engine.py:241`, `validate(prima)` in `_prodotto` — su un circuito col nodo `z`
pendente estraneo alla coppia, `Refusal(topology, z)` con tutte le precondizioni
dichiarate soddisfatte). Entrambe sono ora **dichiarate** nel Catalogo e falsificate
da `TestLePrecondizioniSonoFalsificabili`. Il controesempio di questa voce resta in
piedi per la meta' che gli appartiene: il rifiuto di `validate` sul **prodotto**
(`test_un_rifiuto_si_restituisce_e_non_lascia_niente_nei_registri`) continua a non
essere una precondizione — e' una proprieta' di `Cₖ₊₁` — quindi il verso *esigita →
dichiarata* resta non meccanizzabile. Ma la frase *«la condizione che manca non e'
una precondizione»* era vera del prodotto e falsa di `Cₖ`, e la conclusione era piu'
larga della misura che la sosteneva.

## Story 1.8 — seconda revisione a contesto fresco, 26/08/2026

Il revisore ha prodotto undici rilievi, tutti confermati per esecuzione. Otto sono
stati riparati nella stessa iterazione — la guardia d'attribuzione dei fotogrammi
sui due tipi (lo scambio superava ogni controllo), le guardie di `Justification`
(l'unico tipo esportato senza), il `patch_` che `esporta()` lasciava cadere, le due
precondizioni esigite e non dichiarate con la rettifica di §7 qui sopra,
l'attribuzione corretta nel docstring del test che la prova, la misura dell'unione
esatta di `entita` estesa alle quattro forme di passo con l'invariante citato,
l'oracolo sul ramo di `componi` che solleva, e la nota sul recinto che
`check_boundaries.py` non copre. I tre che seguono restano aperti, ciascuno con la
misura che lo rende ritrovabile e la ragione per cui chiuderlo e' una decisione.

### 8. `componi` scarta `Cₖ₊₁`: la catena riesegue la trasformazione

Misurato: `TestLaCatenaDiDuePassi._catena` chiama `transform(CATENA, "serie", "R1",
"R2")` **due volte** — una dentro `componi`, una di nuovo per ottenere il circuito
d'ingresso del secondo passo — perche' `componi` restituisce il `VisualStep`, e il
`VisualStep` e' una proiezione per riferimento: porta i `lay_` e il `patch_`, non il
`CircuitIR` prodotto. Il costo e' una `transform` in piu' per ogni passo
concatenato; su una funzione pura il risultato non cambia (AD-2), quindi il costo e'
ergonomico e computazionale, non di correttezza.

**Le alternative.** (1) `componi` restituisce anche `Cₖ₊₁` — cambia la firma
pubblica del punto di composizione. (2) `VisualStep` porta il circuito per valore —
contraddice AD-21. (3) un registro dei `CircuitIR` risolvibile per identificatore —
e' la stessa lacuna della voce 9. **Cosa la ribalterebbe:** la prima storia di
Epic 2 (il Piano didattico) che componga catene per davvero: chi scrive quel
chiamante decide la firma, e questa voce gli tiene la misura.

### 9. Il prodotto del passo non ha registro: perderlo perde tre campi su quattro

AD-21 v2: *«ricostruirla significa risolvere gli identificatori»*. Misurato: risolti
`prima`, `dopo` e `patch` si ottengono due `LayoutIR` e una `LayoutPatch`
(`render.layout` esporta `LayoutStore` e `PatchStore` e nessun altro registro), e
`delta`, `boundary`, `equation`, `certificate` vivono per valore dentro
`VisualStep.risultato` senza essere depositati da nessuna parte. Ne segue che tre
dei quattro campi di UX-DR23 e tutte e tre le risposte di FR-49 spariscono col
processo: il passo e' ripercorribile finche' l'oggetto vive, e non e' ricostruibile
dai registri. La storia verifica il verso *«gli identificatori si risolvono»*; il
verso *«risolverli ridà il passo»* oggi e' falso, e prima di questa voce non era
scritto da nessuna parte.

**Perche' resta aperto:** un registro per il `TransformResult` — o per la
`ProofSession` che AD-21 nomina — e' un'unita' di persistenza nuova con un
identificatore nuovo, e AD-8 elenca le righe persistite senza includerla: aggiungerla
e' una decisione sullo spine, non una manutenzione. **Nessun gate installato:** un
test che asserisse «non esiste un registro» inchioderebbe l'assenza come se fosse
voluta, e fallirebbe il giorno in cui la decisione venisse presa nel verso giusto —
e' il gate al contrario, come per §7. **Cosa la ribalterebbe:** la prima storia che
debba riaprire un passo da una sessione nuova (`resume_ref`, AD-8).

### 10. L'alternativa testuale non racconta il passo

Misurato: i due `<desc>` differiscono — *«Circuito: 3 componenti, 3 nodi…»* contro
*«Circuito: 2 componenti, 2 nodi… R1R2eq, resistore da 320 ohm»* — e nessuno dei
due dice che una trasformazione e' avvenuta, ne' da che cosa `R1R2eq` derivi:
l'equazione sta nel layer 6 **visuale** e in nessun testo alternativo. Per chi legge
con un lettore di schermo, AC1 e AC2 di questa storia non esistono.

**Perche' resta aperto:** il `<desc>` e' l'alternativa testuale della **topologia**
di un circuito (Story 1.4, `alternativa_testuale`), non del passo: fargli raccontare
la trasformazione significa decidere la narrazione accessibile del passo — quale
testo, in quale dei due fotogrammi, o in un canale terzo — cioe' la stessa famiglia
di decisioni della voce 5 (a quale momento appartiene l'equazione), su un canale che
nessun criterio della 1.8 nomina e che tocca FR-53. La 1.7 aveva registrato la meta'
*overlay*; questa e' la meta' *fra i due fotogrammi*, ed e' piu' precisa del rapporto
che la liquidava: la differenza fra i due testi c'e', e' la **narrazione** a mancare.

**Gate installato:**
`TestLeMisureRegistrate::test_l_alternativa_testuale_non_racconta_il_passo`.

### Nota sul recinto non coperto, per chi legge gli oracoli

`scripts/check_boundaries.py` cammina il solo recinto `domain`
(`check_boundaries.py:30`): il suo exit 0 e' evidenza sulle righe toccate in
`catalog.py` ed `engine.py` e su **niente** di `render/step/`, che fino alla
Story 1.5 (recinto 4 di AD-21, in backlog) non ha alcun controllo di confine. Non e'
un difetto da riparare qui — il recinto 4 e' dichiarato fuori ambito dalla spec —
ma una tabella di oracoli che presenti quel verde come copertura del codice nuovo
dice piu' di quel che il controllo misura, ed e' gia' successo una volta.
