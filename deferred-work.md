
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

## Review di convergenza 2026-10-15 — H5/K4: navigazione delle evidenze

**P2, differito alla prima unita' di prodotto H5/K4.** Il Claim di una sessione
chiusa cita identificatori di derivazione (per esempio `D1`, `D2`), mentre i
`StepView.evidence_refs` dei passi analitici espongono solo il riferimento allo
stato circuitale. `EvidencePanel` mostra status, verificatore, soggetti e
provenienza, ma non offre un collegamento dall'evidenza del Claim al passo che
la produce. Non dichiarare completa l'ispezione di residui e cross-check.

**Esito richiesto:** conservare il legame derivazione-passo nella proiezione e
renderlo navigabile dalla prova, senza nuova risoluzione nel browser o renderer.
Un test deve seguire un'evidenza della risposta fino al passo corrispondente.
Fonte: review avversaria separata del candidato PR #15 `a98d37a`.

## Riconciliazione15→17 — oracolo live capabilities precedente a Laplace

**P2, preesistente in17; manutenzione separata prima della promozione.** La
spec `student-session-live.spec.ts`, test «il perimetro visibile coincide»,
pretende `transients=false` prima di navigare la pagina. La basea6b1e8f ha
già `product_capabilities` e test Laplace/MCP che richiedono `transients=true`
con risposta trasformata, step/impulse, nessuna antitrasformata o commutazione
di topologie e `certified_lesson=false`. La prova live corrente ha22PASS/2FAIL
(desktop/mobile su quella assert); non è24verdi né prova della paritàUI nel
test abortito. Il modulo capabilities esattoHEAD e HTTP reale concordano;
capabilities, server, StudentApp e vecchia spec sono byte-invariati rispetto
alla base. Non è una nuova suite browser baseline.

**Esito richiesto:** riallineare l'oracolo al contratto Laplace esistente,
conservando i limiti granulari e il confronto del testoUI col server. Il solo
cambio false→true non copre quei limiti. Nessun cambio di API, supporto
generico a tutti i transitori, Claim VERIFIED, soglie o skip è autorizzato
dalla classificazione. La nuova unione parser15→17 resta verificata nel suo
perimetro locale; nessuna promozione/main/quorum ne deriva.

### Seguito locale — oracolo capabilities/UI/Laplace, 15 ottobre 2026

L'oracolo sopra è stato riallineato in un'unità separata sulla base71aa0cf:
HTTP/schema/flags e limiti Laplace granulari, scope non vuoto e primo paragrafoUI
uguale al server. Live24PASS/0FAIL, comprese le due prove prima abortite;
14 mutanti del vero callback respinti prima di goto e controllo sano;
overlay separato browser-only del testo scope osservato in desktop/mobile.
Nessun prodotto/API/schema/Verified/skip cambiato, gli altri sei callback
restano byte-invariati. Review tecnica separata APPROVE sullo hash17cf86d2;
pin futuro del commit ancora pendente nella receipt. Il precedente22/2
rimane una misura storica. Questo chiude localmente il debito dell'oracolo,
non certifica main/quorum, ogni transitorio o le altre unità16/H5/K4.

## Recupero catalogo PR16 — 2026-10-15

La slice catalogo/provenienza recupera tredici sorgenti/test e dodici JSON: undici viste, nove chiusure e due rifiuti. Produttore committed 4a93e24c2cfea75c8d1038e68a0c4126ec49a27f; closure112 invariata e pin reale su tutti gli artifact. Non amplia automaticamente le famiglie StudentApp e non chiude H3.

La PR16 e il parent bfa restano parzialmente recuperati, non assorbiti in main. Restano sette finding FIX_REQUIRED nella prossima unità parent/host/operazioni: ingresso proof esplicito; smoke dinamico su tutti i corpi; verifier dei nuovi JSON; verifier degli asset effettivamente indicati nellHTML remoto; promessa CTA dopo navigazione; playbook manuale senza eliminare branch; delimitazione di brief e misure storiche. Preservare originali e genealogia nel recupero conservativo finale. I due falsi verdi del verifier e il fumo4vs11 non sono gate utilizzabili per dichiarare completo il catalogo. H5/K4 mantiene la destinazione prodotto separata, design e21famiglie restano aperti. Nessuna riduzione di soglie, skip, Verified o altri confini.

Receipt: 20261015T060236Z-catalogo-proof-undici-provenienza.md; review tecnica Codex precommit SHA256 35070c780b9137d004bb499a35a6ee0cfb128b6b1fae7974e68f7d1d6826c99a. Non equivale al quorum formale non-Codex, CI remota del nuovo candidato o approvazione main/deploy.


## Recupero locale host/operazioni PR16 — 15 ottobre 2026

Seguito della slice catalogo: recuperati guscio, guida, strumenti, test e documenti del parent bfa tramite merge conservativo proposto con head originale0adc. I sette finding F1–F6/F8 sono affrontati localmente e approvati nella review tecnica separata; F7 resta corretto dal produttore reale4a93 con closure112 e catalogo25 invariati. Non è prova di assorbimento in main, quorum formale, deploy o chiusura16. La receipt di questo giro contiene SHA, controprove, attribuzione dei run e limiti.

Smoke dinamico e verifier intera dist non sono solver o firmaH3; ogni Failure è intenzionalmente guasto per il profilo operativo, senza cambiare il vero schema/UI. Corrette le attestazioni positive nei rifiuti e la divergenza lessicale del razionale; mantenuti controlli sani. Fullscreen conserva iframe, link/fallback iniziali dichiarati, popup non millantato. Header mobile scorre via entro480px: RED discriminante2FAIL e intero host26PASS dopo correzione, due setup precedenti non discriminanti conservati. Il vecchio oracolo tastiera è riallineato agli action già esistenti, non al prodotto cambiato.

**P3, prossima unità isolata UX scroll host/frame:** il caricamento mobile360×780 con scala step0after ha mosso la pagina ospite a scrollY349; la causa non è ancora isolata. La correzione CSS elimina la sovrapposizione dell'header, non questo movimento iniziale. Conservarne sorgente e metriche, verificare il focus e lo scroll interno/esterno prima di una modifica al Picker. H5/K4, design e21famiglie mantengono le destinazioni precedenti.

**Deviazione nelle prove storiche:** il writer ha riusato per errore una directory Playwright del catalogo durante la controprova route; sei PNG default storici sono persi, non rigenerati come storici. Log/risultati e quattro PNG specifici catalogo separati sono conservati; nuove immagini host/viewport hanno directory nuove e pin propri. Non dichiarare preservazione completa dei vecchi screenshot.


## Correzioni della review consolidata701 — 15 ottobre 2026

C701-1 P2 (busy StudentTrace dopo edit durante controllo) e C701-2 P2 (promessa privacy del quaderno v2) sono affrontati localmente: reset sincrono del busy con guardie generazionali conservate, avviso accanto a Salva quaderno coerente con ownership e byte esportati. C701-3 P3 README è riallineato ai limiti DC/AC/Laplace reali. Quattro nuovi RED browser pertinenti, poi student-session12PASS;191unit/typecheck/build PASS. La suite completa registra timeout ancora da diagnosticare, foto/PDF live e CI del nuovo SHA sono pendenti: non dichiarare gate o main verdi. Receipt20261015T080500Z conserva prove e limiti.

Il proprietario consente reviewer Codex separato al posto della seconda famiglia soltanto per questa esecuzione, con tutti gli altri gate e protezioni invariati; nessuna modifica permanente della policy. H5/K4 P2 e scroll host349 P3 mantengono le destinazioni sopra, come21famiglie/design/pilot/H3. Ardesia rimane solo locale.

Seguito delle verifiche, fonte4 invariata: default140PASS/4FAIL/54SKIP, poi i quattro casi passano nella singola replica invariata. Foto/PDF reali3PASS/1FAIL, poi una replica invariata del PDFdesktop1PASS; nel primo trace solveHTTP200 impiega5890.991ms oltre attesa5000ms, body non catturato. Preservare entrambi i fallimenti; non chiamare verdi le suite originali. CI completa del nuovo SHA e gate main ancora pendenti.


## H5/K4 — collegamento Claim → derivazione → passo, 15 ottobre 2026

**P2 navigazione: affrontato nei contenuti del candidato, promozione ancora
pendente al pin/CI/main.** Checkpoint producer committed pulito `8a580e9658098b6f91fb16febe5396502c46c268`;
`derivation_ref` conserva il vero `derivation_after`, separato dagli IR refs.
Profilo nuovo completo e legacy onesto; ID opachi, salto al passo/focus anche
se corrente, contesto nuovo senza focus ereditato. Scala D1→indice3 eD2→4;
ponte D3→2/KCL. Nessun nuovo solver o cambiamento di Verified.

I gate locali sul contenuto finale sono 2544 Python PASS/97,37% con soglia95,
domain100% e confini0;227unit web/13suite/typecheck/build,16nuovi browser mirati
e160default PASS/54skip opzionali invariati/zeroFAIL o flaky. I16sono inclusi
nei160. Primo Python1FAIL2543PASS per drift del fingerprint globale conservato;
risolto rigenerando anche18lezioni/18PDF dal producer canonico pulito, senza
indebolire test o identità. Proof12output/112closure eStudentApp37/113closure
legati allo stesso Csrc8a. Due indici byteidentici, formule e SVG invariati;
nei PDF cambiano solo Subject/footer di revisione. Dettagli nella receipt
20261015T104216Z-claim-derivazione-passo.md. Review separata dei contenuti APPROVE, SHA256
`650b545100afcfcf5183f9fb0a9bf7d7854177eecf449377e921155b10619be2`.
Non attribuire già CI, merge o verifica main a questo checkpoint preparatorio.

**P2 residuo, DEFERRED → prossima unità prodotto H5/K4:** ispezione completa di
residui, cross-check, terminal mapping e provenienza. **P2 autenticazione,
DEFERRED → H3:** il legacy dichiarato non autentica un produttore ostile.
**P3 runtime, DEFERRED → issue20; P3 scroll349, DEFERRED → unità isolata UX
host/frame** già descritta sopra. Formule lunghe restano scorrevoli nel
riquadro; non dichiarare WCAG/design globale,21famiglie complete o pilot.
Ardesia22e5 rimane soltanto locale; probe dei18payload/roundtripJSON non è
una nuova prova browser/IndexedDB/durabilità o fullsuite Ardesia.


## H5/K4 — provenienza dichiarata ispezionabile (15 ottobre 2026)

Stato locale: contenuto provato/revisionato, candidato/CI/main ancora PENDING.
Il pannello espone i tre metadati completi, assenza e limite di autenticità;
la leggibilità locale è verificata con otto casi permanenti desktop/mobile
e due probe di scroll. Non chiude H3, residui/cross-check/terminal mapping
H5/K4, né le 21 famiglie, design/accessibilità globali o pilot.
La receipt del giro registra i successi e i run falliti/incompleti distinti.
Le destinazioni preesistenti issue #20 e host/scroll349 restano aperte.

## Dipendenze web esistenti — 15 ottobre 2026

**P2, OPEN → unità separata `WEB-DEPENDENCY-TRIAGE-2026-10-15`.**
Questa è una destinazione di lavoro interna, non un numero di issue GitHub.
L'audit del lockfile SHA256
`0dc61e1b553cfda843b68daa2822663e60b11b6be440c1a4e9c67832ac37a278`,
byteidentico al parent `1b2ac783898ae273367e5586d6afb8942d39218e`, segnala
quattro voci package: Vitest/tinypool critical, source-map-js high e
@vitest/mocker moderate. La voce Vitest aggrega i transitivi: non sono
quattro exploit indipendenti. La patch di provenienza non modifica il lock.

Il triage delimitato non ha dimostrato un P0/P1 specifico della patch UI;
non dichiara i package non sfruttabili. Restano aperti il percorso da mappe
non fidate a PostCSS/source-map-js, le primitive di prototype pollution a
monte dei gadget tinypool e le configurazioni/esposizioni del mocker.
Essere dipendenze dev o avere `sourcemap: false` non chiude questi rischi.

La futura unità deve verificare reachability e prerequisiti, scegliere una
strategia compatibile, revisionare il diff del lock e ripetere i gate
pertinenti, inclusi packaging MCP e audit esatto. Non applicare `audit fix`
automatico, override senza analisi, nuovi skip o riduzioni delle soglie.
Nessuna versione major suggerita dal registry è già approvata.

Fonti primarie: [mocker](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9),
[tinypool worker options](https://github.com/tinylibs/tinypool/security/advisories/GHSA-5gmw-xhrv-c9v3),
[tinypool run options](https://github.com/tinylibs/tinypool/security/advisories/GHSA-85c8-ppgw-ccpr),
[source-map-js correzione upstream](https://github.com/7rulnik/source-map-js/pull/79).

H3, report completo residui/cross-check/terminal mapping H5/K4, issue20,
scroll349, 21 famiglie, design globale e pilot mantengono le destinazioni
precedenti. La correzione della leggibilità della provenienza non li chiude.


## Source-map-js — qualificazione locale differita, 15 ottobre 2026

**P2, DEFERRED → WEB-DEPENDENCY-TRIAGE-2026-10-15; gate browser non soddisfatto.** Risoluzione locale1.2.1→1.2.2 limitata a tre campi del lock e guardia reale del consumer Vite/PostCSS. RED qualificato6FAIL2PASS→GREEN8PASS;235unitweb e2544Python/97.37%/domain100/type/build/boundaries PASS,923HTTPMATCH. Il primo8FAIL comprendeva anche due errori dei controlli sani, preservati e corretti prima del lock senza indebolire gli assert.

Il primo defaultbrowser ha167PASS/54skip opzionali invariati/1timeout. Una non riproduzione isolata1PASS non lo promuove. La conferma e fermata con5PASS3timeout1interrotto213senza risultato; summary214skipped non sono skip eseguiti. Un caso raggiunge UI/expect prima del timeout: nessuna attribuzione collettiva al solo page setup. Cause individuali ignote, pressione del sistema osservata. Review separata DEFER dell'unita, nessun content APPROVE; approvata soltanto preservazione privata verificata. Nessun commit candidato,push,PR,CI o merge; source-map e gli altri advisory restano aperti su main. Receipt del giro conserva pin, esecuzioni e limiti.

**P2 ulteriore:** la guardia sana usa SourceNode; non corregge il percorso legacy SourceMapGenerator.fromSourceMap/IndexedSourceMapConsumer.sourceRoot. Rilevanza concreta da triagiare. Audit locale ancora exit1 per Vitest/tinypool/mocker; nessun audit fix o override major applicato, nessuna chiusura di sicurezza globale.

**P3 → issue20:** ritardi/affidabilita runtime e fixture, conservare trace e conteggi, senza causa dimostrata. Non aumentare budget/retry o introdurre skip per promuovere il giro. K4/H3/scroll349/21famiglie/design/pilot mantengono destinazioni precedenti. Ardesia rimane soltanto locale; nuovi timeout di lettura Git non riattestano4237 come identita corrente.


## K4 — giustificazione del passo IN_REVIEW, 15 ottobre 2026

Quattro campi gia canonici esposti dalla stessa esecuzione: terminali del
boundary, precondizioni ordinate, formula e certificato completo. Csrc
`fec4fff5fd347e899501010185edb4b0d2393175`; fonte e guardie provate, cataloghi rigenerati con closure
esatta.355 unit web/2594 Python,12 browser mirati,6 viewport e2 journey reali
PASS delimitati. Non equivale a completare K4 o autenticare la provenienza.

**P2, BLOCK per promozione attuale → diagnosi CI exactcandidate e review
finale della stessa unita.** Due full locali completi, ciascuno179PASS,
54 skip annotati e1timeout; tutti234 identita/expected/annotazioni uguali,
retry0. Timeout in due casi diversi, creazione pagina rispettivamente
17.67s e25.54s; callback/UI raggiunte e assert oltre deadline, nessuna causa
host o regressione semantica specifica dimostrata. Nessun terzo run locale,
nessun budget/skip modificato o gate passato per somma. Una eventuale PR
draft serve soltanto alla CI test-only su runner diverso; nessun merge o
quorum anticipato. La receipt 20261015T173935Z conserva gli esiti.

**P2, DEFERRED → prossima unita H5/K4:** residui numerici, cross-check e
terminal mapping completi restano irrisolti. **P2 → H3:** nessuna nuova
autenticazione. **P3, DEFERRED → issue20:** ritardi/affidabilita del runner,
senza attribuzione causale. Scroll349 non e corretto dal probe viewport.
Interoperabilita Ardesia NOT_CHECKED_CURRENT; solo locale, nessuna nuova
identita corrente attestata.44 accettazioni di reader Kirchhoff precedenti
non sono test Ardesia. Source-map/advisory,21famiglie, design globale,
accessibilita e pilot mantengono le destinazioni gia registrate.


## K4 — integrazione parziale verificata, 15 ottobre 2026

PR23 MERGED; main `e1375fb47f306fa1709d5952f6072e0e3eb3d01f`, tree `54687a9b09f376d5c6df865401cf4470ae33a9ca`.
Due APPROVE esatti e4CI candidato verdi, gate comment6199099346; poi2CI main
verdi,923HTTP,12K4+6viewport+2DC reali PASS. La precedente IN_REVIEW/FAIL
resta storica e i due full locali restano FAIL. Review separata differisce
i timeout come P2→issue20; primario accetta la sola integrazione delimitata
e mantiene affidabilità P3→issue20. Vedi receipt `vault/70-Receipt-di-giro/20261015T183042Z-giustificazione-passo-main-verificato.md`.
Quattro campi canonici esposti; residui numerici/cross-check/terminal mapping
generale restano P2→prossimo H5/K4; autenticazione/forgiature coerenti→H3.
WEB-DEPENDENCY-TRIAGE-2026-10-15, UX host/frame/scroll349,21famiglie/design/pilot
e Ardesia localonly NOT_CHECKED_CURRENT restano aperti. Nessun deploy o
nuovo Verified. Goal ATTIVO; nessun terzo full locale per source-map.
