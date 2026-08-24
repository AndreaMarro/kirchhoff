# Review — lente: continuità visuale

**Oggetto:** `ARCHITECTURE-SPINE.md` v2 (872 righe, AD-1…AD-33, `updated: 2026-08-15`)
**Lente:** continuità visuale — A-0, R-Visual-1, i quattro bracci, VCER/SM-14, `TransformOverlay`
**Data:** 15 agosto 2026
**Revisioni già rientrate e lette per non ripetere:** `review-avversario.md` (C1…C8),
`review-invarianti.md` (R1…R6), `review-confini.md` (R1…R5), `review-veridicita.md` (V1…V5).

---

## Metodo

Ogni rilievo qui sotto nomina **due unità** che possono essere scritte da due persone diverse,
**entrambe conformi** alla lettera dello spine, e che **divergono** su qualcosa che Gate A misura.
Ogni affermazione porta `file:riga`. Dove ho verificato una porta e l'ho trovata chiusa, l'ho
scritto nella sezione finale invece di tacerla.

Non propongo soglie: VVDR, RRC, TVR, VCER, SEC, VDR restano owner-locked (`prd.md:1801`).
Non riscrivo lo spine. Non rinumero nulla: gli emendamenti proposti sono **in loco** su AD
esistenti, salvo dove indico esplicitamente un AD nuovo.

---

## Verdetto

**Lo spine protegge molto bene il braccio A e non sa dire cosa siano i bracci B, C e 0.**

Il lavoro fatto su A-0 è solido: `preserve` non è autocertificabile (AD-22:474-501), il dominio non
conosce posizioni (AD-18:376-383), `TransformOverlay` ha uno scrittore e non è persistito
(AD-8:233), i layer sono una scala fissa (AD-23:509-511). Su quell'asse lo spine regge.

Il difetto è sull'asse ortogonale, ed è lo stesso in sei forme: **l'esperimento di Gate A è
descritto come una variazione di rendering, ma la variabile che distingue i bracci non è
tipizzata da nessuna parte.** «Codifica visiva» (AD-26:546-547) è l'unica cosa che separa A da B
da C, e non è nessuna delle quattro rappresentazioni di AD-21:441. Da lì discendono: un test
permanente che i bracci B e C falliscono per costruzione (CV2), una R-Visual-1 che l'ordine dei
layer non implica e che nessuno stadio esegue (CV3), tre affermazioni incompatibili sul `LayoutIR`
del braccio 0 (CV4), un vincolo dichiarato «nel tipo» in uno stack che AD-21 stesso dichiara privo
di tipi (CV5), e una metrica di kill criterion i cui due operandi non hanno entità, identificatore
né regola di ritenzione (CV6).

Detto nel modo più corto: **il braccio A è architettura; i bracci 0, B e C sono ancora prosa.**
E il verdetto di Gate A è un confronto — un confronto in cui tre termini su quattro non hanno tipo
non è misurabile.

| # | Rilievo | Severità |
|---|---|---|
| CV1 | «Codifica visiva» è il canale che distingue i bracci e non è una rappresentazione | **critico** |
| CV2 | Il test permanente di A-0 (AD-23) è falso per costruzione sui bracci B e C | **critico** |
| CV3 | R-Visual-1 non è implicata dall'ordine dei layer, e nessuno stadio la esegue | **critico** |
| CV4 | Il `LayoutIR` del braccio 0: titolo, Rule, AD-8 e Deferred dicono quattro cose | **alto** |
| CV5 | «Il vincolo è nel tipo» è falsificato da AD-21 nello stesso documento | **alto** |
| CV6 | VCER confronta due `LayoutIR` che non hanno entità, identità né ritenzione | **alto** |
| CV7 | `FR-47` dice «braccio B» dove intende «braccio 0»; AD-26 corregge in silenzio | **medio** |

---

## CV1 — «Codifica visiva» è la variabile dell'esperimento, e non è una delle quattro rappresentazioni — **critico**

### Il testo

`ARCHITECTURE-SPINE.md:546-547`

> A, B, C condividono `LayoutIR` e differiscono **solo** nel `TransformOverlay` e nella
> codifica visiva.

`ARCHITECTURE-SPINE.md:441-445` (AD-21) enumera **quattro** rappresentazioni — `CircuitIR`,
`LayoutIR`, `TransformOverlay`, `InteractionState` — e chiude: «Nessuno scrive in un altro».
`ARCHITECTURE-SPINE.md:651` lo ripete come convenzione: «Un tipo che ne contenesse un altro è un
errore di modellazione».

«Codifica visiva» non compare in AD-21, non ha scrittore in AD-8:229-238, non ha layer in
AD-23:509-511, non ha prefisso in `Consistency Conventions:642`, non ha pacchetto nell'albero
sorgente (`:793-820`). `Consistency Conventions:654` la chiama «un parametro di rendering» e si
ferma lì.

### Cosa il braccio B e il braccio C richiedono davvero

Non è una sottigliezza di nomenclatura. Guardo cosa producono i due bracci, dai documenti che li
definiscono:

- **Braccio B** — `DESIGN.md:188-193`: `unchanged-marker`, `stroke-dasharray: '2 3'`,
  `stroke: {colors.ink-muted}`, `arm: 'B'`. Applicato **ai preservati**.
- **Braccio C** — `DESIGN.md:183-187`: `attenuation`, `opacity: '0.38'`, `arm: 'C'`. Applicato
  **ai preservati**.
- Il mock lo conferma nel modo più letterale (`passo-a-meta-trasformazione.html:88-91`):
  `svg[data-arm="B"] .keep .shape { stroke-dasharray:2 3 }` e
  `svg[data-arm="C"] .keep { opacity:.38 }` — entrambi selezionano `.keep`, cioè
  **le primitive dell'entità preservata**, ai layer 2, 3 e 4.

Nessuno dei due è un overlay ancorato: sono **modifiche del rendering dell'entità sottostante**.
È esattamente ciò che `prd.md:1260-1263` definisce come la negazione di A-0, ed è deliberato —
`DESIGN.md:193` lo dice: «È l'esatta negazione di A-0, ed è lì apposta».

Ma allora il canale che li porta **non può essere** il `TransformOverlay`, che AD-8:233 definisce
come «derivato dal `boundary` della `Transform`» e che `DESIGN.md:177` descrive come «un segno
sovrapposto… Vive nel `TransformOverlay`, non nel `LayoutIR`». E non può essere il `LayoutIR`, che
è geometria e che AD-26:546 dichiara **condiviso** fra A, B e C. Serve un quinto canale — per
entità, non geometrico, non ancorato — e AD-21:441-445 dice che i canali sono quattro.

### Le due unità

**U1 — `render/serialize`.** Legge AD-26:546 «differiscono solo nel `TransformOverlay` e nella
codifica visiva» e implementa la codifica come **funzione di serializzazione**:
`(LayoutIR, TransformOverlay, arm) → SVG`, con `arm` che seleziona un foglio di stile applicato
alle primitive già emesse. Conforme: non ha creato una quinta rappresentazione, ha aggiunto un
parametro a uno stadio di rendering, come autorizza `Consistency Conventions:654`.

**U2 — `experiment/`.** Legge AD-11:290-294 («`experiment/` misura contro un `ParticipantToken`…
Vive in `experiment/` e in nessun altro modulo») e AD-26:542 (`Binds: render/, experiment/`), e
conclude che i bracci sono materia di `experiment/`. Implementa un `ArmEncoding` — una mappa
`entity_id → visual_state` costruita da `Pₖ` — e lo passa al renderer. Conforme: non ha toccato
nessuna delle quattro rappresentazioni e ha tenuto l'esperimento dentro il suo pacchetto.

### La forma divergente

| | U1 | U2 |
|---|---|---|
| Dove vive la codifica | foglio di stile in `render/serialize` | struttura dati in `experiment/` |
| Cosa la indicizza | selettori CSS su classi emesse dal renderer | `entity_id`, cioè `Pₖ` |
| Chi decide quali entità attenuare | **il renderer**, per classe | `Pₖ`, calcolato da `domain/transform/check` |
| Il braccio C attenua… | tutto ciò che non porta la classe «changed» | esattamente `Pₖ` |
| Determinismo (SM-20) | dipende dall'ordine di emissione delle classi | dipende solo da `Pₖ` |

**U1 reintroduce l'autocertificazione che AD-22 ha appena chiuso.** AD-22:481-483 vieta al renderer
di proporre un `preserve` proprio; U1 non lo propone — lo **ricalcola implicitamente** come
complemento della classe «changed» in fase di serializzazione. Se le due definizioni divergono di
una entità, i bracci B e C attenuano o marcano un insieme diverso da `Pₖ`, e la misura 2 di SM-21
(`prd.md:1376`, «errori nell'indicare cosa è rimasto uguale» — quella che abbatte A-0) confronta
il braccio A contro un braccio B che marca il set sbagliato. Il verdetto resta leggibile e diventa
falso.

### Il punto di rottura

Non si vede in nessun test. Le due unità producono SVG plausibili, i token sono gli stessi
(AD-26:548-550), l'estetica è identica. La divergenza compare **solo** nel confronto fra bracci, che
è l'unica cosa che Gate A produce, e si presenta come un risultato sperimentale invece che come un
difetto di implementazione. È la forma peggiore: un bug che si legge come dato.

### La forma minima della correzione

Emendare **AD-21** in loco, aggiungendo alle quattro rappresentazioni un quinto canale nominato e
recintato, oppure — se l'owner preferisce non toccare il numero quattro, che è retoricamente
portante — emendare **AD-26** perché dica *dove* vive la codifica, *cosa* la indicizza e *chi* la
scrive. Il minimo indispensabile, in una riga:

> La codifica di braccio è una mappa `entity_id → visual_state` costruita **da `Pₖ`** e prodotta da
> `experiment/`; `render/serialize` la applica e non la calcola. Non esiste alcuna funzione che
> ricavi l'insieme dei preservati dalle classi del disegno.

Va inoltre aggiunta la riga corrispondente alla tabella degli scrittori di **AD-8:229-238** e il
prefisso a `Consistency Conventions:642`.

---

## CV2 — Il test permanente di A-0 è falso per costruzione sui bracci B e C — **critico**

### Il testo

`ARCHITECTURE-SPINE.md:511-513` (AD-23, Rule)

> **Il test è permanente** (famiglie obbligatorie, AD-15): rimosso il `TransformOverlay`, il
> rendering delle entità sottostanti è identico a quello senza trasformazione in corso.

Non c'è alcun qualificatore di braccio. AD-15:340-343 stabilisce che le famiglie obbligatorie sono
verificate da «un controllo che **fallisce se una famiglia manca** (FR-46)», e che «ogni fallimento
sfuggito in produzione diventa fixture o invariante permanente».

### Perché è falso su B e C

Nel braccio B il `TransformOverlay` non porta l'`unchanged-marker`: il marcatore sta sull'entità
(CV1). Rimuovere l'overlay lascia il marcatore. Nel braccio C rimuovere l'overlay lascia
`opacity: .38` sui preservati (`DESIGN.md:184`). In entrambi i casi il rendering **non** è identico
a quello senza trasformazione in corso — ed è corretto che non lo sia: `prd.md:1343-1344` definisce
B e C esattamente come le negazioni controllate di A-0.

Lo spine ha quindi un invariante permanente che **due dei quattro deliverable violano per
progetto**.

### Le due unità

**U1 — `render/` con il test come gate universale.** Legge AD-23:511-513 e AD-15:340-343 e scrive
il test nella famiglia obbligatoria, eseguito su ogni rendering prodotto. Conforme alla lettera.
Conseguenza: i bracci B e C non passano la CI, e l'unica uscita conforme è **non costruirli** —
cioè togliere due dei quattro bracci che `prd.md:1339-1344` impone.

**U2 — `experiment/` con il test ristretto ad A.** Legge `prd.md:1343-1344` («B — come A più una
codifica leggera unchanged»; «C — resto attenuato») e conclude che il test vale solo sul braccio A.
Conforme allo spirito. Conseguenza: **nessun documento dice che il test è ristretto**, quindi nessun
documento dice cosa lo tenga acceso su A. Un domani il braccio A acquisisce un tocco di
`unchanged-marker` «solo per leggibilità» e il test resta verde, perché è stato ristretto una volta
e nessuno sa più a cosa.

### Il punto di rottura

Un'unica frase deve fare due lavori incompatibili: **essere l'invariante che protegge A-0** ed
**essere falsa sui bracci che esistono per falsificare A-0**. Finché resta senza qualificatore, o
uccide i bracci o si spegne, e in entrambi i casi lo fa senza che nessuno l'abbia deciso.

Va notato che lo spine ha anche **indebolito** la formulazione del PRD: `prd.md:587-589` dice
«identico **byte per byte**», AD-23:512-513 dice solo «identico». Con SM-20 (`prd.md:1558-1560`,
determinismo del rendering) l'identità byte per byte è misurabile; «identico» senza qualificatore
ammette una lettura per-entità, una per-bounding-box e una per-DOM. Tre unità, tre test.

### La forma minima della correzione

Emendare **AD-23** in loco perché il test diventi **differenziale e dichiarato per braccio**:

> Il test vale sull'**encoding del braccio A**: rimosso il `TransformOverlay`, il rendering delle
> entità preservate è identico **byte per byte** a quello senza trasformazione in corso. Sui bracci
> B e C lo stesso test **deve fallire**: sono le negazioni dichiarate di A-0 e un loro passaggio è
> il difetto, non la conformità.

Un test che deve fallire su B e C è più forte di un test ristretto ad A: verifica che l'encoding di
braccio esista davvero e non sia stato implementato come no-op.

---

## CV3 — R-Visual-1 non è implicata dall'ordine dei layer, e nessuno stadio la esegue — **critico**

Questo è il rilievo che risponde alla domanda 3, ed è il più serio dei sette perché riguarda il
difetto **da cui la regola è nata**.

### Primo: l'ordine dei layer non implica la non-occlusione. La produce.

`ARCHITECTURE-SPINE.md:506-508` (AD-23, *Prevents*)

> che un'annotazione di trasformazione occluda un'entità semantica preservata

`ARCHITECTURE-SPINE.md:509-511` (AD-23, Rule)

> ordine fisso `0` sfondo · `1` regione di trasformazione · `2` fili · `3` componenti ·
> `4` **nodi ed etichette semantiche** · `5` enfasi sul cambiato · `6` annotazioni di boundary ·
> `7` interazione · `8` debug

La scala è crescente e in SVG si dipinge in quest'ordine: **6 sta sopra 4**. Le annotazioni di
boundary sono, per costruzione, **sopra** i nodi e le etichette semantiche.

Il difetto originale era un altro: `prd.md:611-613` e `DESIGN.md:392-394` raccontano che il primo
mock dipingeva **l'alone del sottografo** sopra le etichette di `A` e `B`. L'alone è la *regione di
trasformazione*, oggi al layer 1 — **sotto** il 4. Per quel difetto la scala è la cura giusta.

Ma le entità che il difetto ha colpito, `A` e `B`, sono esattamente quelle che
`prd.md:1272-1274` definisce **preservate e insieme boundary** — cioè quelle che ricevono
l'annotazione del layer 6. La scala sposta l'alone sotto le etichette e lascia
`boundary-anchor` sopra. **R-Visual-1 riguarda proprio il caso che l'ordine dei layer non copre.**

Che oggi non occluda dipende da una scelta di stile e non da una regola: `DESIGN.md:171-177` dà a
`boundary-anchor` `fill: 'none'` e `size: '9px'`. Nessuna riga dello spine impone né il fill
trasparente né un limite di dimensione.

**Le due unità.** U1 rende `boundary-anchor` come anello vuoto di 9 px (`DESIGN.md:174-175`) —
nessuna occlusione. U2 lo rende come pastiglia piena con la lettera del terminale, che è una scelta
di rendering perfettamente ragionevole e che al layer 6 **copre l'etichetta `A`**. Entrambe
rispettano AD-23:509-511 alla lettera. La seconda riproduce il difetto del 15 agosto sullo stesso
elemento, con l'invariante attivo e verde.

### Secondo: la regola ha tre case e nessun proprietario

Cercando **chi** esegue il controllo, lo spine risponde tre volte, in modo diverso:

| Dove | Cosa dice | Riga |
|---|---|---|
| AD-19 | `overlay_occlusion` — R-Visual-1 violata — emessa da **`render/roundtrip`** | `:408` |
| AD-5 | gli **otto** controlli di `publish()`: 1-5, incidenza, round-trip, `TruthfulnessGate` | `:185-190` |
| AD-23 | «Il test è **permanente** (famiglie obbligatorie, AD-15)» | `:511-512` |

`overlay_occlusion` è una **causa di rifiuto a runtime** con un emettitore dichiarato, e **non
compare fra gli otto controlli di `publish()`**. AD-5:190 chiude con «Otto controlli, ogni nodo, un
solo punto di codice»: nove non ce ne sono. AD-23 la colloca invece fra le famiglie di test, cioè
in CI.

È **letteralmente la stessa forma di difetto che AD-32 è stato scritto per chiudere**
(`:616-618`): «due gate definiti e uno solo collegato… un'unità conforme a entrambi costruisce il
gate e non lo attraversa mai». Qui il gate non è nemmeno costruito: c'è la causa di rifiuto, c'è
l'emettitore, non c'è lo stadio che la solleva.

### Terzo: non esiste un predicato di occlusione

AD-31:604-609 fa esattamente il lavoro giusto per l'incidenza geometrica: «entro tolleranza
dichiarata», «due terminali distinti non coincidenti», «nessun modello è coinvolto — è geometria di
segmenti». Per l'occlusione non esiste l'equivalente. «Occlude» non è definito: sovrapposizione di
bounding box? di path? con quale soglia di alpha? un'annotazione al 15 % di opacità occlude?

Senza predicato, **la risposta alla domanda «serve un occhio umano?» è: sì, oggi serve**, perché
l'unico controllo automatico esistente — l'indice di layer — è quello che *causa* la
sovrapposizione invece di impedirla.

### La forma minima della correzione

Tre righe, tutte dentro AD esistenti:

1. **AD-23**, dopo la scala dei layer, un predicato sullo stesso modello di AD-31:604-609 — la
   geometria resa di un'annotazione dei layer 5-6 non interseca la bounding box resa di
   un'entità semantica preservata dei layer 3-4 oltre una tolleranza dichiarata; nessun modello è
   coinvolto. E la conseguenza che oggi manca: **l'ordine dei layer è necessario e non
   sufficiente.**
2. **AD-5:185-190**, aggiungere `overlay_occlusion` come **nono** controllo, oppure — se l'owner
   decide che è controllo di CI e non di pubblicazione — togliere la causa da AD-19:408 e dire
   dove vive. Le due scritture attuali non possono coesistere: una causa di `Refusal` che nessun
   percorso solleva è un tipo morto, e il tipo morto è il modo in cui la regola scompare in
   silenzio.
3. **AD-23**, nominare `render/roundtrip` come proprietario, coerentemente con AD-19:408, o
   correggere AD-19.

> Nota a margine, non un rilievo: `epics.md` non contiene alcuna occorrenza di `R-Visual`,
> `overlay`, `LayoutIR`, `VCER` o «braccio» (verificato con `grep`; 60 citazioni di `AD-` e nessuna
> a `AD-21…AD-33`). La copertura a valle è già trattata da `review-veridicita.md` V5 e non la
> ripeto: la annoto solo perché significa che nessuna storia oggi **possiede** il controllo di CV3.

---

## CV4 — Il `LayoutIR` del braccio 0: quattro affermazioni, tre incompatibili — **alto**

### Il testo, nei quattro punti in cui compare

| # | Riga | Cosa afferma |
|---|---|---|
| 1 | `:540` — **titolo di AD-26** | «I quattro bracci sono modalità di rendering **di un solo `LayoutIR`**» |
| 2 | `:546-547` — Rule di AD-26 | «A, B, C condividono `LayoutIR`… **Il braccio 0 è l'unico che rigenera il layout**» |
| 3 | `:232` — tabella di AD-8 | «`LayoutIR` → scrittore unico **`render/layout`**» |
| 4 | `:240-242` — nota di AD-8 | «È un artefatto **di `experiment/`**… Senza questa riga il braccio 0 e `render/layout` sarebbero due scrittori legittimi della stessa entità» |
| 5 | `:859-861` — Deferred | «produrre **quattro bracci dallo stesso `LayoutIR`** (AD-26)»… «resta differito solo **l'algoritmo di piazzamento del braccio 0**» |

Il titolo (1) è falso per il braccio 0 e la Rule (2) lo dice due righe sotto. Il Deferred (5) ripete
il titolo e nello stesso elenco puntato afferma che il braccio 0 ha un algoritmo di piazzamento
proprio, differito. La tabella (3) dice che l'unico scrittore del `LayoutIR` è `render/layout`; la
nota (4), quindici righe più in basso nello stesso AD, dice che quello del braccio 0 è artefatto di
`experiment/` e motiva la riga proprio con «sarebbero **due scrittori** legittimi».

### Le due unità

**U1 — `render/layout` in modalità from-scratch.** Legge AD-8:232 («scrittore unico
`render/layout`») e `prd.md:489-490` (FR-47: «**stesso renderer**, stessi vincoli estetici, stesso
`CircuitIR(Cₖ₊₁)`, senza accesso a `Layout(Cₖ)`»). Implementa il braccio 0 come **secondo punto di
ingresso dello stesso motore**, che non riceve il layout precedente. Conforme, e coerente con FR-47.

**U2 — `experiment/` con motore proprio.** Legge AD-8:240-242 («artefatto di `experiment/`, con
identità propria e prefisso proprio») e il Deferred:861 («l'algoritmo di piazzamento del braccio 0
va nominato e congelato»), e conclude che il braccio 0 ha **un proprio algoritmo**, dentro
`experiment/`. Conforme, e coerente con le due righe che ha letto.

### La forma divergente

U2 viola FR-47 senza violare alcun AD. «Stesso renderer, stessi vincoli estetici» diventa «due
renderer che condividono i token». Il confronto 0 ↔ A misura allora **due variabili insieme** —
conoscenza del layout precedente *e* algoritmo di piazzamento — che è esattamente il difetto che
AD-26:543-545 dichiara di prevenire per i bracci B e C, lasciato aperto sul braccio 0.

E poiché è il braccio 0 a definire il denominatore del kill criterion, un braccio 0 con motore
proprio può essere involontariamente peggiore — `prd.md:1341` chiede un «ri-layout indipendente
vero, **non costruito per perdere**» — e nessun controllo lo rileverebbe: sembrerebbe una vittoria
del braccio A.

### La forma minima della correzione

Tre emendamenti in loco, nessun AD nuovo:

- **AD-26:540** — il titolo dica il vero: *«tre bracci sono modalità di rendering di un solo
  `LayoutIR`; il quarto è il ri-layout indipendente»*. I titoli degli AD sono la parte che viene
  citata a valle.
- **AD-8:240-242** — separare **chi calcola** da **chi possiede**: il layout del braccio 0 è
  **calcolato da `render/layout`** attraverso un ingresso che non riceve `Layout(Cₖ)`, ed è
  **posseduto da `experiment/`** come artefatto con prefisso proprio, mai in `ProofSession`. Così
  la tabella :232 resta vera e FR-47 («stesso renderer») resta soddisfatta.
- **Deferred:859** — allineare la formula, e restringere il differito a «i parametri di piazzamento
  del braccio 0», non «l'algoritmo»: un algoritmo differito è un secondo renderer che entra dalla
  porta di servizio.

---

## CV5 — «Il vincolo è nel tipo» è falsificato da AD-21 nello stesso documento — **alto**

### Il testo

`ARCHITECTURE-SPINE.md:547-548` (AD-26)

> **non riceve `Layout(Cₖ)` nella propria firma** — il vincolo è nel tipo, non nella buona fede
> del chiamante.

`ARCHITECTURE-SPINE.md:469-471` (AD-21)

> **Non è un errore di compilazione.** Lo stack è Python senza type checker: la frase «un adapter
> importato dal dominio è un errore di compilazione» del paradigma è **falsa**, ed è il controllo
> `ast` di `check_boundaries.py` a essere l'unica difesa reale.

AD-21 ha smontato la stessa figura retorica dodici righe più su di dove AD-26 la riusa. Con
`Stack:664` (Python 3.12+) e senza type checker nell'elenco, «il vincolo è nel tipo» non è una
proprietà del sistema: è una convenzione.

### Perché conta, e non è pedanteria

`review-avversario.md:635-636` ha classificato questo punto fra i **falsi positivi**: «Il braccio 0
che riceve `Layout(Cₖ)`. Chiusa nel tipo, non nella buona fede: AD-26 dice… Il vincolo è
verificabile staticamente». Quella classificazione è ragionevole se si legge AD-26 da solo. Non
regge accanto ad AD-21:469-471, che è del medesimo documento e della medesima data. Lo segnalo
esplicitamente perché è l'unico punto in cui contraddico una chiusura già registrata.

E l'assenza non è astratta. **AD-21:462-467 elenca cinque recinti nominati** per
`check_boundaries.py`:

| # | Vietato |
|---|---|
| 1 | `domain/` → fuori da `domain/` |
| 2 | `domain/` → `render/` |
| 3 | `domain/` → `perception/` |
| 4 | `domain/` ∪ `render/` → `adapters/` |
| 5 | fuori da `corpus/` → filesystem del corpus |

**Nessuno dei cinque riguarda il braccio 0.** Non esiste un recinto «l'ingresso del braccio 0 non
riceve e non risolve un `Layout(Cₖ)`». `prd.md:509-510` chiede invece un test esplicito: «un test lo
verifica **sulla firma della funzione**, non sulla buona fede del chiamante».

### Le due unità

**U1** implementa il braccio 0 come funzione `relayout(circuit_ir, tokens) → LayoutIR`. Il vincolo
è visibile e verificabile con `inspect.signature`.

**U2** implementa il braccio 0 come stadio della pipeline, quindi con la firma che AD-1:91 fissa
per ogni stadio: `(CircuitIR, ctx) → …`. `ctx` è un contenitore opaco: il `LayoutIR` precedente vi
arriva come campo, o come lookup per `circuit_id` su un contesto condiviso. **La firma è pulita e
il layout precedente è dentro.** U2 è conforme ad AD-26:547-548 alla lettera — `Layout(Cₖ)` non
compare nella firma — e produce un braccio 0 che ha visto il layout precedente.

Il difetto è che il braccio 0 così costruito è **più continuo del dovuto**, quindi il divario 0 ↔ A
si assottiglia, quindi il kill criterion **uccide un prodotto valido**. È la direzione di errore
peggiore delle due, ed è invisibile: il rendering del braccio 0 sarebbe semplicemente «un po' più
stabile del previsto», che non ha l'aspetto di un bug.

### La forma minima della correzione

- **AD-26:547-548** — sostituire «il vincolo è nel tipo» con ciò che è vero e verificabile: il
  vincolo è un **controllo statico nominato**, e la firma non è sufficiente se lo stadio riceve un
  `ctx`.
- **AD-21:462-467** — aggiungere il **sesto recinto**: nessun percorso di codice del braccio 0
  riceve, importa o risolve un `LayoutIR` di `Cₖ` — né per parametro, né per `ctx`, né per lookup
  su identificatore. È una riga nella tabella dei recinti, cioè lo stesso costo delle altre cinque.
- Se l'owner vuole il vincolo davvero nel tipo, la decisione è di **Stack** (`:663-676`): aggiungere
  un type checker in CI. È una scelta legittima e va scritta lì, non presupposta in un AD.

---

## CV6 — VCER confronta due `LayoutIR` che non hanno entità, identità né regola di ritenzione — **alto**

Questo risponde alla domanda 5. Va detto prima cosa lo spine **ha** chiuso, perché è un progresso
rispetto a `review-invarianti.md` R4, che rilevava che il soggetto della misura era deducibile solo
per via transitiva:

- **Chi calcola:** nominato. `AD-2:120` — «`eval/` misura lo scostamento `p_{k+1} ≈ p_k` a
  posteriori (AD-15)»; `AD-15:336-340` — l'harness calcola ogni metrica di §8 «a ogni esecuzione,
  con o senza soglia fissata… Vale in particolare per **VCER**». Coerente con `prd.md:1541`:
  «Proprietario della misura: l'harness di FR-34, non il renderer».
- **Chi non calcola:** nominato. `AD-22:481-483`, il renderer non propone `preserve`.

Resta scoperto tutto il resto, e sono tre cose distinte.

### Primo: su quale rappresentazione

Lo spine non lo dice mai. `p_k` «vive nel `LayoutIR`» (`AD-18:379`), ma la misura potrebbe essere
presa (a) sul `LayoutIR` deserializzato, (b) sull'SVG semantico serializzato — che AD-10:268-271
eleva a «sorgente unica di ogni altro formato» e che è l'unico artefatto certificato —, oppure
(c) sul `ReconstructedCircuitIR` del round-trip, che però per costruzione **non porta geometria
confrontabile**. Tre unità, tre numeri, per la metrica che decide se il prodotto continua a
esistere.

### Secondo: i due operandi non hanno entità né identificatore

`SM-14` (`prd.md:1531-1534`) definisce VCER come «**quota di `LayoutPatch`** che violano
`p_{k+1}(x) ≈ p_k(x)`…». Il denominatore è il `LayoutPatch`; il predicato è sul `LayoutIR`. Perché
la metrica sia calcolabile serve, per ogni passo, la tripla `(LayoutPatch, LayoutIR_k,
LayoutIR_{k+1})` **congiungibile**. Lo spine non fornisce nessuno dei tre agganci:

| Cosa serve | Cosa dice lo spine |
|---|---|
| un'entità `LayoutIR` persistita per nodo del `ProofGraph` | l'ERD (`:776-789`) non conosce `LayoutIR`, né `PROOF_GRAPH`, né `LAYOUT_PATCH`: ha `IR_VERSION`, `PUBLISHED`, `STEP` della v1 |
| un identificatore per `LayoutIR` e per `LayoutPatch` | `Consistency Conventions:642` elenca i prefissi `ir_`, `sol_`, `var_`, `evt_`. Nessun `lay_`, nessun `patch_` — e nemmeno il «prefisso proprio» che AD-8:241 promette al braccio 0 |
| una regola di ritenzione di `LayoutIR_k` dopo il passo *k+1* | `AD-8:232` nomina lo scrittore e tace sulla ritenzione. `AD-8:233` dice esplicitamente «non persistito» **solo** per `TransformOverlay`, il che per contrasto suggerisce che gli altri lo siano, senza dirlo |
| un contenitore che li porti tutti | `AD-21:452-454`: la `ProofSession` «porta **gli identificatori dei quattro**» — quattro identificatori, cioè **un** `LayoutIR`, non uno per nodo |

### Terzo: la sola regola vicina usa il termine che lo spine dichiara ambiguo

`Consistency Conventions:646` — «La persistenza è append-only **sugli IR**: una correzione produce
una nuova versione, non una sovrascrittura». Se «IR» include il `LayoutIR`, ogni passo produce una
nuova versione e VCER è calcolabile. Ma `Consistency Conventions:651`, due righe sotto, dice:
«**Mai «IR» nudo nel codice nuovo: il termine è ambiguo dalla v2** e sopravvive solo dove
`AD-1…AD-20` lo usavano». La riga 646 è una convenzione della v1: usa il termine che la riga 651
proibisce, e la sua estensione al `LayoutIR` è indecidibile.

### Le due unità

**U1 — `render/layout` append-only.** Legge :646 in senso largo. Ogni passo scrive un nuovo
`LayoutIR` versionato. `eval/` risolve la coppia e calcola VCER.

**U2 — `render/layout` con layout corrente.** Legge :651 («il termine è ambiguo… sopravvive solo
dove `AD-1…AD-20` lo usavano», e AD-8 è nel range) e conclude che :646 vale per il `CircuitIR`. Il
`LayoutIR` è lo stato corrente del disegno: applicare un `LayoutPatch` lo aggiorna in loco — che è
esattamente ciò che AD-2:110-111 descrive, «il renderer produce applicando il `LayoutPatch` al
`LayoutIR` precedente». Conforme, e più naturale della prima lettura.

**Con U2, `p_k` non esiste più nel momento in cui servirebbe misurarlo.** `eval/` può solo
ricostruirlo rieseguendo la derivazione dall'inizio — il che è possibile solo se il rendering è
deterministico, cioè **solo se SM-20 vale già**, che `prd.md:1558-1560` dichiara doversi misurare
«prima di leggere RRC, VCER e SEC». La dipendenza è circolare e non è scritta da nessuna parte.

### La forma minima della correzione

- **AD-8:229-238** — nella riga `LayoutIR`, aggiungere la ritenzione accanto allo scrittore: **un
  `LayoutIR` per nodo del `ProofGraph`, append-only, mai sovrascritto**. È la riga che rende VCER
  calcolabile, e costa quanto le altre sette della tabella.
- **AD-21:452-454** — la `ProofSession` porta gli identificatori dei layout **per nodo**, non un
  identificatore singolo. Resta una proiezione per riferimento: non è il contenitore che AD-21
  vieta.
- **`Consistency Conventions:642`** — i prefissi di `LayoutIR`, `LayoutPatch` e del layout di
  braccio 0 (`experiment/`, promesso in AD-8:241 e mai definito).
- **AD-15:336-343** — una riga che dica **su quale rappresentazione** l'harness calcola lo
  scostamento. Non la tolleranza, che è owner-locked: la rappresentazione, che non lo è.
- L'ERD (`:776-789`) va allineato o dichiarato v1. Un ERD che non conosce l'entità su cui il gate
  decide non è una vista parziale: è una vista di un altro sistema.

---

## CV7 — `FR-47` dice «braccio B» dove intende «braccio 0», e AD-26 corregge in silenzio — **medio**

`prd.md:509-510` (FR-47, *Consequences (testable)*)

> Il **braccio B** non riceve `Layout(Cₖ)` in nessuna forma: un test lo verifica sulla firma della
> funzione, non sulla buona fede del chiamante.

È in contraddizione diretta con `prd.md:495-497`, dieci righe sopra, nello stesso requisito: «**B e
C sono varianti di rendering dello stesso `LayoutIR`**, non pipeline separate… Se B o C richiedessero
un `LayoutIR` diverso, il confronto misurerebbe due cose insieme»; e con `prd.md:1343`, dove B è
«come A, più una codifica leggera unchanged».

`ARCHITECTURE-SPINE.md:547-548` legge la riga nel modo giusto — «Il braccio **0**… non riceve
`Layout(Cₖ)` nella propria firma» — e **non registra la correzione**. Lo spine dichiara `binds:
FR-1..FR-53` (`:14`) e AD-26:542 dichiara `Binds: FR-47`: un'unità che implementa da FR-47, come
prescrive la catena BMAD, costruisce un braccio B senza layout persistente, cioè un secondo braccio
0 con una codifica «unchanged» sopra. Il confronto A ↔ B misurerebbe allora **layout più codifica**
invece che la sola codifica, che è la domanda a cui il braccio B esiste per rispondere
(`prd.md:1343`, «Marcare aiuta o disturba?»).

**Correzione minima:** una riga di nota in **AD-26**, sul modello delle note di emendamento già
presenti nello spine: *«FR-47 §Consequences scrive «braccio B» dove il resto del requisito e §7.0.1
dicono «braccio 0». Lo spine legge «braccio 0»; il refuso del PRD va corretto alla fonte.»* È il
tipo di divergenza che costa una riga adesso e un braccio sperimentale dopo.

---

## Risposte dirette alle sei domande

| # | Domanda | Risposta |
|---|---|---|
| 1 | I quattro bracci sono ottenibili da un solo `LayoutIR`? | **No, e lo spine si contraddice.** Titolo AD-26:540 e Deferred:859 dicono uno solo; Rule AD-26:547 e Deferred:861 dicono che il braccio 0 rigenera; AD-8:232 e AD-8:240-242 danno due scrittori diversi. Vedi **CV4** |
| 2 | «Non compare `Layout(Cₖ)` nella firma» è esprimibile nel tipo? | **No.** Lo stack è Python senza type checker e AD-21:469-471 lo dice esplicitamente per l'analoga affermazione del paradigma. AD-26:548 afferma il contrario e **non lo dichiara come rischio**. Nessuno dei cinque recinti di AD-21:462-467 lo copre; il `ctx` di AD-1:91 è il veicolo della violazione. Vedi **CV5** |
| 3 | R-Visual-1 è verificabile automaticamente? | **Non com'è scritta.** L'ordine dei layer mette le annotazioni di boundary (6) sopra le etichette semantiche (4): è necessario e non sufficiente, e non copre il caso `A`/`B` che ha generato la regola. Manca un predicato di occlusione (AD-31:604-609 ne è il modello). Sul proprietario lo spine dà **tre risposte**: `render/roundtrip` (AD-19:408), assente dagli otto controlli di `publish()` (AD-5:185-190), famiglia di test permanente (AD-23:511-512). Vedi **CV3** |
| 4 | «Togli il `TransformOverlay` e il rendering è identico» è strutturalmente vero? | **No: è solo raccomandato, ed è enunciato in una forma che due bracci su quattro violano per progetto.** AD-23:511-513 lo pone come test, non come proprietà; nulla vieta a `render/layout` di consumare il `boundary` che AD-22:485 gli consegna e di riservargli spazio. Lo spine ha inoltre indebolito «byte per byte» (`prd.md:587`) in «identico». Vedi **CV2** |
| 5 | VCER: chi calcola, su cosa, e chi conserva i due `LayoutIR`? | **Chi calcola è nominato** (`eval/`, AD-2:120 + AD-15:336-340), **su cosa non è detto**, e **chi conserva non esiste**: nessuna entità nell'ERD (`:776-789`), nessun prefisso (`:642`), nessuna regola di ritenzione (AD-8:232), e la `ProofSession` porta un `LayoutIR` solo (AD-21:452-454). Vedi **CV6** |
| 6 | B e C condividono il `LayoutIR` di A? | **Sì, ed è scritto** (AD-26:546). Ma la differenza **non** è puramente di overlay: `unchanged-marker` e `attenuation` modificano il rendering delle entità preservate (`DESIGN.md:183-193`, mock `:88-91`), e quel canale non è nessuna delle quattro rappresentazioni di AD-21:441. Il confronto è pulito sul layout e **non tipizzato** sulla variabile che sta misurando. Vedi **CV1** e **CV2** |

---

## Porte verificate e trovate chiuse

Non sono rilievi. Le elenco perché una lente che non dice cosa ha provato e non è passato non è
verificabile.

- **Il renderer che sceglie `preserve`.** Chiusa due volte e bene: AD-22:481-483 («non espone
  **alcuna funzione** per proporre un `preserve` proprio: lo riceve») e `DESIGN.md:442-445`. La
  chiusura tiene anche sul punto più sottile, `node_mapping`, grazie ad AD-22:494-497 (controllore
  strutturale indipendente dal `Transform` misurato).
- **Il dominio che emette geometria.** Chiusa da AD-18:376-383 («dalla v2 non sa nemmeno cosa sia
  una posizione») e da AD-2:114-120, che spiega perché `LayoutPatch` nomina entità e non coordinate.
  È l'argomentazione migliore del documento.
- **`TransformOverlay` che scrive nel `LayoutIR`.** Chiusa da AD-21:444 («Nessuno scrive in un
  altro») e da AD-8:233, che gli dà scrittore e lo dichiara non persistito.
- **L'esperimento che riceve circuiti percepiti.** Chiusa da AD-24:517-525 e dal diagramma
  `:768-771`: «L'esperimento di Gate A parte da `STRUCT`, mai da `CONF`». Coerente con
  `prd.md:628-630`.
- **Gate A come profilazione di persone.** Chiusa da AD-11:288-300 in modo strutturale e non per
  esenzione: `ParticipantToken` non congiungibile, aggregazione per braccio, cancellazione
  verificata come il TTL di AD-9. Già trattata da `review-avversario.md` C5, che ne chiedeva la
  disambiguazione: la v2 l'ha fatta.
- **Differenza estetica fra bracci.** Vincolata in tre documenti coerenti: AD-26:548-550,
  `DESIGN.md:447-452`, `EXPERIENCE.md:429-430`. Nessuno spazio di divergenza sui token.

---

## Ordine di chiusura, per costo

| Ordine | Chiusura | Costo adesso | Costo dopo |
|---|---|---|---|
| 1 | **CV7** — nota di refuso in AD-26 | una riga | un braccio sperimentale costruito sull'asse sbagliato |
| 2 | **CV4** — titolo AD-26:540, nota AD-8:240-242, Deferred:859 | tre righe | due motori di layout, e un braccio 0 che non è più «lo stesso renderer» |
| 3 | **CV5** — sesto recinto in AD-21:462-467 | una riga di tabella | un braccio 0 troppo continuo, e un kill criterion che uccide un prodotto valido |
| 4 | **CV2** — qualificatore di braccio in AD-23:511-513 | due righe | o niente bracci B e C, o un invariante spento in silenzio |
| 5 | **CV3** — predicato di occlusione e nono controllo | un paragrafo, sul modello di AD-31 | il difetto del 15 agosto che si ripresenta sullo stesso elemento, con l'invariante verde |
| 6 | **CV6** — ritenzione e identità del `LayoutIR` | una riga in AD-8, una in AD-21, due prefissi | VCER non calcolabile, e Gate A senza ingresso — AD-15:339 lo chiama «un gate senza ingresso non è un gate» |
| 7 | **CV1** — tipizzare la codifica di braccio | un emendamento ad AD-21 o AD-26 | i bracci B e C marcano un insieme diverso da `Pₖ`, e il difetto si legge come risultato sperimentale |

L'ordine è per costo crescente, non per gravità: CV1 e CV3 sono i due critici e stanno in fondo
perché costano un emendamento vero. Se se ne chiude uno solo, **chiudere CV3**: è l'unico in cui il
difetto già accaduto una volta può riaccadere identico, sullo stesso elemento, con tutti i controlli
verdi.
