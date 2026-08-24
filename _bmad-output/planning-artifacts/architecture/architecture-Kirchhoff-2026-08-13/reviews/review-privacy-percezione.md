---
name: 'review-privacy-percezione'
lens: 'privacy · licenze · confine della percezione'
target: 'ARCHITECTURE-SPINE.md v2 (872 righe, 33 AD, updated 2026-08-15)'
date: '2026-08-15'
status: 'rilievi aperti'
non_ripete:
  - reviews/review-avversario.md
  - reviews/review-invarianti.md
  - reviews/review-confini.md
  - reviews/review-veridicita.md
---

# Review privacy, licenze e confine della percezione — Spine v2

## Verdetto

Il confine **tecnico** della percezione è chiuso bene — `PerceptionCandidate`, promozione con esito
di fallimento proprio, recinto `domain/ ↛ perception/` — ma il confine **giuridico** che gli sta
sotto è dichiarato e non costruito: il fail-closed di `UNKNOWN` copre due dei cinque usi che il
registro stesso enumera, l'assenza di registro non ha default, «l'agente propone ma non promuove»
non ha meccanismo, e le due popolazioni di persone reali che il piano tocca — i partecipanti di
Gate A e gli studenti di ripetizioni che donano le foto dell'held-out — non hanno né titolare del
consenso, né legame con l'interessato, né prova di cancellazione, mentre `StudentTrace` e
`source_provenance` non hanno affatto proprietario.

## Metodo e stato dei file

Letti per intero o per sezione, sul disco, il 15 agosto:

| File | Stato al momento della lettura |
|---|---|
| `ARCHITECTURE-SPINE.md` | 872 righe, `version: 2`, `updated: '2026-08-15'`, AD-1…AD-33 |
| `prds/prd-Kirchhoff-2026-08-13/prd.md` | 1898 righe, FR-1…FR-53 |
| `docs/01-fonti-esterne.md` | 149 righe, ricerca licenze del 13 agosto |
| `scripts/check_boundaries.py` | 4222 byte, controllo `ast` sugli import |
| `src/kirchhoff/eval/reference_set.py` | split dev/holdout, guardia `allow_holdout` |
| `reference-set/{dev,holdout}/*.json` | 60 casi già sul disco |

Le quattro review rientrate sono state lette per **non ripetere**: dove un mio rilievo confina con
uno loro, lo dichiaro e cito la riga (in particolare `review-avversario.md:418-478` su AD-11 e
`review-avversario.md:482-532` su evidenza e TTL).

**Legenda severità.** 🔴 difetto strutturale che due unità conformi possono realizzare in modi
divergenti, o dato personale che può uscire · 🟠 difetto strutturale con impatto differito ·
🟡 lacuna che va colmata prima del codice ma non produce divergenza.

---

## P1 — `UNKNOWN` è fail-closed su due usi; il registro ne enumera cinque, e `eval/` è nel *Binds* 🔴

### Il testo

`ARCHITECTURE-SPINE.md:534-535` — «Stato in `ALLOWED · RESTRICTED · REVIEW_REQUIRED · PROHIBITED ·
UNKNOWN`; **`UNKNOWN` è fail-closed per addestramento e ridistribuzione** — assenza di licenza nota
non è permesso d'uso.»

`prd.md:1142` — `allowed_uses: evaluation | training | fine_tuning | publication | demo`.

`ARCHITECTURE-SPINE.md:529` — *Binds:* `corpus/`, **`eval/`**, `perception/`, FR-51, FR-34.

### Cosa può sfuggire

Il fail-closed nomina `addestramento` e `ridistribuzione`. Restano fuori, per lettura letterale,
`evaluation`, `publication` e `demo`. Un'immagine prelevata dal web con licenza non accertata è
quindi **legittimamente usabile**:

- nel gold set e nell'harness — che è `evaluation`, ed è esattamente l'unità che AD-25 dichiara di
  vincolare (`:529`), governata da AD-15 (`:328-343`) e da FR-34;
- nella scheda di sistema pubblica (`prd.md:1703`) e nelle pagine pubbliche che AD-10 elenca fra i
  suoi artefatti (`:256`) — che è `publication`;
- in una demo commerciale — che è `demo`.

Il difetto non è che qualcuno bari: è che **due unità conformi divergono**. `corpus/`, che legge la
Rule, serve l'asset perché l'uso richiesto non è fra i due vietati. `eval/`, che legge il *Binds*,
assume di essere protetto perché AD-25 lo nomina. Nessuna delle due sbaglia.

Secondo mancante, che rende il primo non rimediabile a valle: **nessuna riga impone al chiamante di
dichiarare l'uso**. `allowed_uses` è un campo del `SourceAsset` (`prd.md:1142`) e non esiste alcun
punto in cui l'uso richiesto venga confrontato con esso. Senza l'uso dichiarato, la lista è un
commento.

Nota di attenuazione onesta: `prd.md:1161-1162` fissa già i vincoli accertati (CGHD e Digitize-HCD
usabili; Image2Net/Fiore no), e `docs/01-fonti-esterne.md:108-109` esclude Fiore per la clausola NC
e JUHCCR-v1 per licenza non verificata. La disciplina di oggi è buona. Il rilievo è che la regola
scritta non la sostiene.

### Forma minima della correzione

**Emendare AD-25**, nessun AD nuovo:

- il fail-closed vale per **ogni uso non esplicitamente presente in `allowed_uses`**, non per due usi
  nominati;
- ogni lettura da `corpus/` porta un `use` dichiarato; `corpus/` rifiuta quando `use ∉ allowed_uses`
  o quando lo stato è `UNKNOWN`/`PROHIBITED`. La causa esiste già: `source_unlicensed`
  (`ARCHITECTURE-SPINE.md:412`), che oggi però nomina solo lo stato e non l'uso — va estesa al
  `subject` «(asset, uso richiesto)».

---

## P2 — L'assenza di `SourceAsset` non ha default sicuro, e sul disco c'è già il materiale che lo prova 🔴

### Il testo

`ARCHITECTURE-SPINE.md:533` — «il registro **precede** l'ingestione, non la segue.»
`prd.md:1132` — «entra nel corpus **solo** attraverso un `SourceAsset` registrato e versionato.»
`ARCHITECTURE-SPINE.md:412` — l'unica causa di rifiuto disponibile è `source_unlicensed`, definita
come «`SourceAsset` in `UNKNOWN` o `PROHIBITED`».

### Cosa può sfuggire

Le tre righe insieme coprono l'asset **registrato in uno stato cattivo**. Non coprono l'asset
**senza riga di registro**: un artefatto non registrato non ha stato, quindi non è in `UNKNOWN`,
quindi la sola causa legale non lo nomina. Il fail-closed è definito su un **valore**; l'assenza non
è un valore. La lettura naturale di un'unità conforme diventa «non è registrato, dunque la regola
non lo riguarda» — che è l'inversione esatta della promessa.

Non è ipotetico. Sul disco, oggi:

- `/Users/andreamarro/MATJOURNEY/kirchhoff/reference-set/dev/*.json` e `.../holdout/*.json` — 60 casi
  già presenti; le chiavi sono `case_id`, `domain_class`, `transformations`, `ir`, `expected`, e
  **nessun campo di licenza o di provenienza al livello del caso**;
- `grep -rl "SourceAsset\|corpus\|license" src/ tests/ scripts/` → **zero occorrenze**. Il registro
  che «precede l'ingestione» non esiste, e il materiale è già ingerito.

Nel caso specifico il rischio è basso — quei casi sono generati (`"source_kind": "generated"` nei
componenti dell'IR) — ma è precisamente il precedente che la regola deve poter trattare: il primo
corpus è entrato prima del registro, e nessuna riga dice cosa farne.

### Forma minima della correzione

**Emendare AD-25** con due frasi:

- «**Assenza di `SourceAsset` ≡ `UNKNOWN`.**» Un artefatto senza riga di registro è non usabile per
  ogni uso, con la stessa forza dello stato esplicito.
- Un controllo di inventario in `corpus/` **fallisce** se trova un file senza riga corrispondente —
  stessa forma del controllo TTL di AD-9 (`:250-252`), che lo spine sa già scrivere.

La decisione retroattiva sui 60 casi già presenti (registrarli o rigenerarli) è dell'owner, non
mia: qui va nominata, non presa.

---

## P3 — «Propone ma non promuove» non ha meccanismo: AD-8 dà a `corpus/` un solo scrittore per entrambe le operazioni 🔴

### Il testo

`ARCHITECTURE-SPINE.md:536-538` — «**Un agente può proporre in `REVIEW_REQUIRED`, mai promuovere ad
`ALLOWED`**: la promozione richiede una decisione umana registrata.»

`ARCHITECTURE-SPINE.md:655` (Consistency Conventions) — «Un agente propone in `REVIEW_REQUIRED`, non
promuove; non estende il Catalogo trasformazioni; non tocca soglie né held-out. **Le tre cose sono
controlli, non convenzioni sociali.**»

`ARCHITECTURE-SPINE.md:236` (tabella AD-8) — `SourceAsset` | scrittore unico `corpus/` — «nessun
altro modulo apre un file del corpus».

`ARCHITECTURE-SPINE.md:218-219` — «Enforcement a livello di **permessi DB**, non di convenzione.»

### Cosa può divergere

La convenzione **dichiara** che sono controlli e non ne nomina nessuno. Il solo meccanismo
disponibile è quello di AD-8, e l'unità che AD-8 sa distinguere è il **modulo**, non l'**attore**:
`corpus/` è scrittore unico di `SourceAsset`, quindi ha il permesso di scrittura, quindi ha il
permesso di scrivere `ALLOWED`. Un agente che scriva codice dentro `corpus/`, o che invochi la
funzione di promozione, eredita quel permesso per costruzione. Il confine che AD-25 protegge —
`REVIEW_REQUIRED → ALLOWED`, l'unica transizione irreversibile del corpus — passa dentro il modulo,
dove nessun meccanismo lo vede.

Mancano le tre cose che lo renderebbero meccanico, e lo spine le sa fare altrove:

1. **Nessun tipo separato.** Non esiste un `SourceAssetProposal` distinto da un `SourceAsset`: la
   proposta e il registro sono lo stesso record con un campo diverso.
2. **Nessun ruolo di scrittura separato.** AD-8 assegna un solo scrittore, quindi la granularità
   della difesa è più grossa dell'operazione da difendere.
3. **Nessuna entità «decisione umana».** AD-25 la esige (`:538`) e la tabella di AD-8 (`:230-238`)
   non ha una riga per essa — quindi non ha proprietario, quindi non è scrivibile, quindi non è
   esigibile. È lo stesso difetto che l'emendamento del 15 agosto ad AD-8 chiudeva per sette entità
   (`:225-227`): un'entità senza proprietario rende inapplicabile l'enforcement a permessi.

Il confronto interno rende il difetto evidente: AD-9 (`:250-252`) e AD-11 (`:296-297`) rendono le
proprie garanzie **meccaniche** — «da un controllo che fallisce, non da una procedura». AD-25
consegna la propria transizione più delicata alla buona fede.

Il PRD lo dice già, e non è stato raccolto: `prd.md:1164-1169` — «il registro come confine non
aggirabile dall'agente ha la forma di un confine owner-locked, non di un requisito di prodotto …
resta come requisito, il che la rende vincolante per il codice **ma non per un agente che lavori
fuori da questo repo**».

### Forma minima della correzione

**Emendare AD-25 e la tabella di AD-8**, senza AD nuovo:

- `ALLOWED` è uno stato **derivato**, mai impostabile direttamente: è calcolabile solo dall'esistenza
  di una riga `LicenseDecision { asset, decisore umano, data, evidenza }`;
- `LicenseDecision` entra nella tabella di AD-8 con **scrittore diverso da `corpus/`** — altrimenti
  la separazione è nominale;
- il controllo assume la forma già usata dallo spine: un `SourceAsset` in `ALLOWED` senza
  `LicenseDecision` corrispondente **fa fallire** il controllo di conformità.

---

## P4 — Nessuno stadio guarda cosa c'è dentro un'immagine di corpus, e nessun campo lo registra 🔴

### Il testo

Ricerca testuale sullo spine: **zero occorrenze** di `consens`, `consent`, `personal`,
`identificativ`, `volto`, `matricola`, `offusc`, `FR-31`, `FR-32`, `FR-33`.

`ARCHITECTURE-SPINE.md:844` (Capability → Architecture Map) — l'unica riga che nomina quel gruppo:
«Trasparenza e dati (FR-29…FR-33) | `api/`, `adapters/blob`, `render/` | AD-9, AD-10, AD-11».
Nessuno dei tre AD riguarda l'offuscamento o il consenso: AD-9 è il TTL, AD-10 l'export, AD-11 il
punteggio per persona.

`prd.md:1051-1057` (FR-31) — l'offuscamento avviene «prima di trasmettere l'immagine a un fornitore
esterno», cioè sul **percorso di caricamento utente**, non su quello di acquisizione del corpus.

`prd.md:1669-1671` (§10.2) — «può contenere nome, matricola, grafia e nome del docente, e **nulla di
questo serve al prodotto**.»

### Cosa può sfuggire

Il piano raccoglie immagini «da banche dati e online» (`prd.md:1164`, `prd.md:1446-1449`). Quelle
immagini possono contenere volti, nomi, matricole, intestazioni di compiti e filigrane di editori.
Nello spine non esiste:

- **uno stadio** che lo rilevi o lo escluda — l'unico stadio di minimizzazione previsto (FR-31) sta
  su un altro percorso e non è governato da alcun AD;
- **un campo** che lo registri — lo schema `SourceAsset` (`prd.md:1135-1145`) ha `license`,
  `provenance`, `consent`, `allowed_uses`, `restrictions`, `evidence`, e **nessun campo sul
  contenuto personale** dell'artefatto;
- **una regola di ritenzione** — AD-9 (`:250-252`) impone 72 ore alle sole «immagini sorgente» nel
  bucket; il corpus è un filesystem governato da AD-25, che non ha alcun limite temporale. Le classi
  di dato di `prd.md:1716-1720` non contengono la classe «corpus».

L'esito è preciso: un volto o una matricola entrati nel corpus **restano lì senza scadenza**, dentro
l'unico insieme di dati del progetto che nessuna regola cancella. E non è un'ipotesi remota — CGHD è
fatto di disegni a mano di 32 disegnatori fotografati
(`docs/01-fonti-esterne.md:15`, `:26-28`): la grafia è presente per costruzione, e la licenza CC-BY
governa il diritto d'autore, non la protezione dei dati.

### Chi dovrebbe possederlo

`corpus/`. È il solo modulo autorizzato ad aprire un file del corpus (`ARCHITECTURE-SPINE.md:236`,
`:653`), quindi è l'unico punto in cui uno stadio obbligatorio non è aggirabile per costruzione.

### Forma minima della correzione

Serve un **AD nuovo — AD-34** (AD-1…AD-33 non si rinumerano), oppure un emendamento ad AD-25 che ne
faccia le veci. Il contenuto minimo:

- il `SourceAsset` porta uno stato di **contenuto personale** con lo stesso comportamento della
  licenza: sconosciuto ⇒ non usabile, mai «usabile finché non emerge il contrario»;
- `corpus/` esegue uno **stadio di minimizzazione dichiarato** prima che un asset possa salire sopra
  `REVIEW_REQUIRED`, e l'esito è registrato nell'asset;
- il corpus ha una **classe di dato e un periodo** in §12 del PRD, come ce l'hanno le immagini
  sorgente, la telemetria e i log.

Il periodo e la tecnica di minimizzazione sono decisioni dell'owner: qui va detto che mancano, non
quali siano.

---

## P5 — Le foto degli studenti di ripetizioni: consenso senza titolare, cancellazione senza prova 🔴

### Il testo

`prd.md:1450-1452` — «**L'held-out non viene dalle banche dati.** L'addendum lo fissa: *«Foto
scattate dagli studenti, non scansioni»*. … la parte trattenuta resta raccolta dal vero, dal bacino
delle ripetizioni (§17).»

`prd.md:1386-1390` — «Il fondatore è il primo expert evaluator … Il bacino esiste già ed è quello
delle ripetizioni (§17). `[NOTE FOR PM]` … quegli studenti sono **valutatori**, non clienti».

`prd.md:1141` — `consent: required · status · scope`, sotto-oggetto dello schema `SourceAsset`.

Ricerca testuale sullo spine: **zero occorrenze** di `consenso`/`consent`.

### Cosa può sfuggire

**(a) Il consenso non è fail-closed.** AD-25 (`:533-535`) chiude su `UNKNOWN` **della licenza** e
non nomina mai `consent`. Il sotto-oggetto esiste nel PRD e non è trasportato nello spine. Un
`SourceAsset` con `license = ALLOWED` — la foto è del prodotto, il tutor la considera propria — e
`consent.status` vuoto **passa ogni controllo scritto**. La protezione più forte del registro
protegge la dimensione sbagliata.

**(b) Non esiste il legame con l'interessato.** Lo schema (`prd.md:1135-1145`) non ha un riferimento
al soggetto dei dati. Se uno studente revoca, nessuna interrogazione trova le sue foto: la
cancellazione **non è dimostrabile**. Il confronto interno è impietoso — AD-9 (`:250-252`) e AD-11
(`:296-297`) rendono entrambe la propria cancellazione un controllo che fallisce; AD-25 non ha
nulla di equivalente, pur governando il solo insieme di dati raccolto direttamente da persone
identificabili.

**(c) Il percorso dei diritti non raggiunge questi soggetti.** FR-33 (`prd.md:1068-1073`) è scritto
per «un utente» e il suo meccanismo è la cancellazione dell'account. Un donatore di foto non ha un
account — il PRD lo dice esplicitamente (`:1388`: valutatori, non clienti) — quindi il meccanismo
non lo tocca. Vale identico per i partecipanti di Gate A.

**(d) La relazione è asimmetrica e non è registrata da nessuna parte.** Chi raccoglie è il tutor
degli stessi studenti e il primo valutatore del loro lavoro (`prd.md:1386-1387`, `:1896-1898`). Lo
spine non registra il ruolo di chi raccoglie, né la volontarietà, né la revocabilità. Non tocca a me
dire quale base giuridica serva: dico che **la decisione non è presa e non è nominata**.

**(e) Il confine d'età esiste per gli utenti e non per i donatori.** FR-28 impone la dichiarazione
di età al signup e `prd.md:152-155` fissa 18 anni per gli utenti v1, rimandando la fascia 14-17 a
un'informativa dedicata. Nessuna riga impone un confine equivalente a chi partecipa a Gate A o dona
una foto. Un bacino di ripetizioni non coincide con il target universitario del prodotto.

**(f) La sequenza di conformità è invertita.** `prd.md:1705-1707` colloca il pacchetto documentale
— informativa, registro dei trattamenti, accordi di trattamento, valutazione d'impatto — «**prima
del primo incasso**». Ma l'incasso è fuori dall'MVP per decisione esplicita (`prd.md:1471`: «nessun
incasso su un kernel non ancora provato»), mentre la raccolta di foto e le sessioni di Gate A
avvengono **dentro** l'MVP. Il gate che produce la documentazione sta a valle dell'attività che ne
ha bisogno.

### Forma minima della correzione

**Emendare AD-25**, più un rimando in AD-11:

- **`consent` è fail-closed esattamente come `license`**: `required = true` con `status` non
  accertato ⇒ asset non usabile, per ogni uso;
- il `SourceAsset` porta un **riferimento pseudonimo al soggetto** e un percorso di revoca, e la
  cancellazione è verificata da un controllo che fallisce — la stessa forma di AD-9 e AD-11;
- lo spine nomina il **titolare della raccolta** e il punto in cui il consenso è registrato, o
  dichiara che la decisione è dell'owner e resta aperta.

Il trigger del pacchetto documentale (P5f) è una correzione del **PRD**, non dello spine: va spostato
da «primo incasso» a «prima raccolta di dati da persone fisiche». Lo segnalo qui perché lo spine
eredita l'assenza e non può ripararla da solo.

---

## P6 — `ParticipantToken`: non congiungibile con l'anagrafica, ma il disegno è entro-soggetti 🟠

### Il testo

`ARCHITECTURE-SPINE.md:289` — «`experiment/` misura contro un **`ParticipantToken`** generato **per
sessione sperimentale**.»
`:290-292` — «Il token **non è congiungibile** con `subject_id`, account, email o tenant.»
`:295` — «La reportistica è **aggregata per braccio**. **Nessuna vista rende una riga per persona.**»
`:296-297` — «Il token è **cancellato alla chiusura dell'analisi**.»

`prd.md:1843-1849` (§16 Q9b) — «**Il disegno è entro-soggetti e controbilanciato**, non a quattro
gruppi indipendenti: ogni partecipante vede più condizioni … con l'ordine controbilanciato a
quadrato latino (`P1: 0→A→B→C`, `P2: A→B→C→0`, …). Il confronto diventa *«questa persona capisce
meglio A o C?»*.»

`prd.md:1561-1566` (SM-21) — cinque misure oggettive per lettura.

### Perché «non congiungibile e solo aggregato» non basta

La domanda dell'incarico è quella giusta, e la risposta è no, per quattro ragioni distinte.

**(a) «Per sessione» è ambiguo, e le due letture rompono cose diverse.** Se le quattro condizioni di
un partecipante sono quattro sessioni, i token differiscono e **l'appaiamento su cui il disegno è
costruito è distrutto** — cioè si perde esattamente il vantaggio per cui il disegno entro-soggetti è
stato scelto. Se sono una sessione, il token porta 4 bracci × 5 misure **della stessa persona**:
un profilo di prestazione individuale, pseudonimo e non anonimo. AD-11 non dice quale sia, ed
entrambe le letture sono letterali.

**(b) «Nessuna vista rende una riga per persona» è incompatibile con l'analisi che il protocollo
richiede.** Un test appaiato ha bisogno di righe congiunte per partecipante: è la definizione di
entro-soggetti. O l'analisi avviene fuori dal sistema — non documentata, non vincolata, su un foglio
di calcolo — oppure la vista vietata esiste. Non c'è la terza via.

**(c) La lista dei join vietati non contiene il join che riconduce alla persona.** `:290-292` vieta
`subject_id`, account, email, tenant. Non vieta il `SourceAsset` e il suo record di consenso — e il
PRD dice che **partecipanti e donatori di foto vengono dallo stesso bacino** (`prd.md:1387` e
`prd.md:1452`). Un consenso che nomina lo studente e una sessione sperimentale datata sono
sufficienti a reidentificare, e nessuna delle due parti lo vieta perché ciascuna sorveglia l'altra
metà del confine.

**(d) La cancellazione promette un controllo e non gli dà un orologio.** «Cancellato alla chiusura
dell'analisi» non nomina un evento definito né un termine; §16 Q11 (`prd.md:1859-1863`) dichiara
apertamente che **non esiste un tetto di tempo su Gate A**. AD-9 può promettere un controllo che
fallisce perché ha 72 ore; AD-11 promette lo stesso controllo senza una soglia rispetto a cui
fallire. Il test che l'AD ordina non è scrivibile.

**Confine con `review-avversario.md:418-478` (C5).** Quella review ha rilevato il conflitto sul
**tipo** — `ParticipantReading` vietato da AD-11 — e ha proposto un `reading_id` effimero e non
congiungibile. L'emendamento presente nello spine (`:283-300`) chiude quel punto. Ciò che resta
scoperto è il **disegno sperimentale**, fissato nel PRD lo stesso giorno: un `reading_id` davvero
effimero rende impossibile il quadrato latino. Il rilievo qui è il residuo, non la ripetizione.

### Forma minima della correzione

**Emendare AD-11** in loco:

- dichiarare il token **per partecipante dentro l'esperimento**, e dire a voce alta che il
  collegamento fra le sue letture è **voluto e confinato** — è ciò che il disegno richiede, e
  fingere il contrario produce solo un'esenzione silenziosa;
- aggiungere `SourceAsset` e i record di consenso alla **lista dei join vietati**;
- sostituire «chiusura dell'analisi» con una **data o un evento delimitato**, così che il controllo
  promesso sia scrivibile;
- riformulare `:295` distinguendo **archiviazione** da **pubblicazione**: l'aggregazione è un
  vincolo sull'esito pubblicato, non una descrizione del dato conservato — oggi la riga dice la
  seconda cosa e non è vera.

---

## P7 — `StudentTrace` non ha proprietario, ritenzione né lettore, e produce il tipo che AD-11 vieta 🟠

### Il testo

`ARCHITECTURE-SPINE.md:524-525` — l'unica riga dello spine su `StudentTrace`: «Vale identico per
`StudentTrace` (FR-44): ingresso semantico, mai immagine.»

`ARCHITECTURE-SPINE.md:230-238` — la tabella dei proprietari di AD-8 elenca otto entità.
`StudentTrace` **non c'è**.

`prd.md:458-466` (FR-44) — «passi, equazioni, grandezze dichiarate» … «confrontabile col
`ProofGraph` di riferimento **passo per passo**, non solo sul risultato finale».

`ARCHITECTURE-SPINE.md:279-281` (AD-11) — «non esiste alcun tipo che associi una misura di rendimento
a un identificatore di persona».

### Cosa può sfuggire

Alla domanda «cosa contiene, quanto vive, chi lo legge» lo spine risponde solo alla prima, e per
negazione: non è un'immagine. Le altre due non hanno risposta.

- **Proprietario:** nessuno. AD-8 è stato emendato il 15 agosto proprio perché «sette entità erano
  senza proprietario» (`:225-227`); `StudentTrace` è l'ottava, arrivata dallo stesso giorno via
  AD-24 e non aggiunta alla tabella.
- **Ritenzione:** nessuna. AD-9 copre le immagini sorgente; §12 del PRD (`:1716-1720`) non ha una
  classe per le tracce degli studenti.
- **Lettore:** nessuna restrizione. In particolare, nulla dice se il tutor possa vedere la traccia
  passo-passo di un proprio studente identificato.

E il confronto passo-per-passo di FR-44 (`prd.md:465`) **produce** il tipo che AD-11 vieta: un
profilo di errore per passo, riferito a una persona. AD-11 vieta il tipo nel prodotto; FR-44
costruisce l'ingresso per fabbricarlo, ed è una funzionalità di prodotto (tutor, Gate B).

**Sulla sola lettura di AD-28, che l'incarico chiedeva di verificare: non basta, ed è peggio di
così.** `ARCHITECTURE-SPINE.md:569-573` elenca ciò che Ardesia consuma — `ProofSession`,
`ProofCertificates`, `Claim` — e `StudentTrace` **non è nella lista**, quindi il suo transito non è
governato affatto. Inoltre la regola vincola una direzione sola e non quella che conta qui: dice che
ToolHost, Simulation Plugin, LessonOS e «la memoria di Ardesia» **non producono né certificano
`CircuitIR`**. Protegge la verità circuitale dall'host. Non dice nulla su cosa l'host **trattenga**
di ciò che lo studente ha scritto. La sola lettura protegge il circuito, non lo studente.

FR-44 è fuori MVP (Gate B), ma il PRD stesso spiega perché il confine si scrive adesso
(`prd.md:467-469`): «il verifier si costruisce adesso: accettare immagini dopo costerebbe una
riscrittura del confine». Lo stesso argomento vale per la proprietà e la ritenzione.

### Forma minima della correzione

Senza AD nuovo:

- **riga in AD-8** per `StudentTrace`, con scrittore unico e con la dichiarazione se sia persistito
  o transitorio;
- **riga in AD-11** — l'esito del confronto `StudentTrace ↔ ProofGraph` è transitorio e non
  persistito per persona, oppure la deroga è dichiarata e delimitata come per `experiment/`;
- **riga in AD-28** — elencare `StudentTrace` fra ciò che attraversa l'adapter e dire cosa l'host
  può conservarne. «Sola lettura» va qualificata: non scrive la verità circuitale **e** non trattiene
  la traccia oltre la sessione.

Se il tutor debba o non debba vedere la traccia del proprio studente è una decisione di prodotto con
implicazioni dirette su AD-11: va presa dall'owner, e oggi manca.

---

## P8 — `source_provenance` non ha veicolo fino al `ProofGraph` pubblicato 🟠

### Il testo

`ARCHITECTURE-SPINE.md:521-524` (AD-24) — il candidato porta `source_provenance`; la promozione «passa
per conferma e Validazione elettrica ed è un passaggio esplicito con esito di fallimento proprio,
mai un cast». **Nessuna parola su cosa della provenienza sopravviva alla promozione.**

`ARCHITECTURE-SPINE.md:91-93` (AD-1) — «Nessuno stadio a valle dell'estrazione legge l'immagine
sorgente: **se un dato serve, sta nel `CircuitIR` o non esiste**.»

`ARCHITECTURE-SPINE.md:864-865` (**Deferred**) — «Il seed fissa che l'IR … porta provenienza e forma
simbolica». È l'unico punto dello spine che afferma che l'IR porta la provenienza, ed è nella lista
delle cose **non decise**.

### Cosa può sfuggire

Messe insieme: la provenienza deve stare nel `CircuitIR` per sopravvivere (AD-1), nessun AD dice che
ci stia, e l'unica affermazione che ci stia è differita. Un `PerceptionCandidate` promosso perde la
provenienza senza che nessuna regola sia violata.

A valle il buco si allarga:

- **Il gate non la controlla.** Gli otto controlli di `publish()` (`:183-190`) non includono la
  risolvibilità della provenienza del nodo radice.
- **Il campo che la porterebbe non è nello spine.** FR-39 (`prd.md:399-401`) rende `PROVENANCE` uno
  dei sei campi obbligatori del passo, e SM-15 (`prd.md:1543-1545`) misura che tutti e sei siano
  compilati e non vuoti. Ricerca sullo spine per `provenance`/`provenienza`: righe 258, 522, 750,
  840, 864 — **il campo `PROVENANCE` della grammatica del passo non compare mai**. Il veicolo esiste
  nel PRD e non è stato raccolto.
- **L'export marca l'altra cosa.** AD-10 (`:259-260`) applica la Marcatura di provenienza, che
  FR-19 definisce come «origine assistita da IA, versione del sistema, momento di generazione e un
  riferimento verificabile all'IR» (`prd.md:889-890`). È la provenienza **nostra**, non quella della
  fonte.

Esito: un Badge Verificata su una derivazione nata da una foto, la cui origine non è più
rintracciabile — che è esattamente lo scenario che l'incarico nomina.

**Sul lato licenze c'è il gemello.** `attribution_required` è un campo del `SourceAsset`
(`prd.md:1139`) e CGHD e Digitize-HCD sono entrambe CC-BY con la formula di attribuzione già scritta
(`docs/01-fonti-esterne.md:23`, `:85`). Nessuna riga dello spine porta quell'obbligo dentro
`export()`, che AD-10 dichiara essere **il solo punto** che produce artefatti — cioè il posto giusto,
dove non c'è.

**Confine con `review-avversario.md:482-532` (C6).** Quella review tratta l'evidenza che **evapora**
a 72 ore mentre il `Claim` la esige. Qui la domanda è diversa e complementare: se la provenienza
**viaggia** dal candidato al `ProofGraph` pubblicato e all'artefatto esportato. Le due chiusure sono
compatibili e vanno fatte insieme.

### Forma minima della correzione

Tre emendamenti in loco, nessun AD nuovo:

- **AD-24** — la promozione **trasporta `source_provenance` nel `CircuitIR` fidato** o rifiuta; è la
  sola forma compatibile con AD-1;
- **AD-5** — nono controllo: un nodo il cui riferimento di provenienza non si risolve a un
  `SourceAsset` **non è pubblicabile**. La causa esiste già (`source_unlicensed`, `:412`);
- **AD-10** — `export()` porta l'attribuzione richiesta dal `SourceAsset` della radice **accanto**
  alla marcatura di FR-19, non al posto suo.

E la riga di *Deferred* (`:864-865`) sulla provenienza dell'IR va tolta dai differiti: non è una
scelta interna a un modulo, è il presupposto di tre AD.

---

## P9 — Il quinto recinto non è un fatto di import, e sul disco non ha soggetto 🟡

### Il testo

`ARCHITECTURE-SPINE.md:467` — recinto 5: «qualunque cosa fuori da `corpus/` → **il filesystem del
corpus**», ordinato da AD-25.
`:469-472` — «**Non è un errore di compilazione.** Lo stack è Python senza type checker … ed è il
controllo `ast` di `check_boundaries.py` a essere **l'unica difesa reale**. Estenderlo ai cinque
recinti è la prima storia di Epic 1.»
`:653` — «L'accesso diretto al filesystem del corpus è vietato al di fuori di `corpus/`.»

### Perché il meccanismo nominato non lo può reggere

`scripts/check_boundaries.py` risolve **nomi di modulo** sull'albero sintattico: `PACCHETTO =
"kirchhoff"`, `RECINTO = "domain"`, e le funzioni `_fuori_dal_recinto` / `_moduli_importati`
lavorano su `ast.Import` e `ast.ImportFrom`. I recinti 1-4 sono fatti di **grafo degli import** e
lo strumento li vede. Il recinto 5 è un fatto di **I/O a runtime**: un `open()` o un `Path.read_bytes()`
non è un import e non lascia traccia nel grafo. L'altro meccanismo che lo spine nomina — «permessi
DB» in AD-8 (`:218-219`) — non raggiunge un filesystem. Il quinto recinto è quindi ordinato e privo
di entrambi i meccanismi disponibili, in un elenco che li presenta come omogenei.

Secondo problema, di soggetto: sul disco il gold set sta in
`/Users/andreamarro/MATJOURNEY/kirchhoff/reference-set/{dev,holdout}/`, **fuori** da
`src/kirchhoff/`, e un pacchetto `corpus/` non esiste ancora. Il recinto nomina un percorso che non
c'è e non nomina quello che c'è.

Terzo, ed è quello che tocca la mia lente: AD-15 (`:334-335`) esige che la parte trattenuta stia «in
uno store separato che la pipeline di sviluppo **non può** leggere». L'implementazione è
`src/kirchhoff/eval/reference_set.py:311-315` — un parametro `allow_holdout` con variabile
d'ambiente, nella stessa directory. Una bandiera non è uno store separato. Quando arriverà l'held-out
fotografico, quella directory conterrà **foto di studenti identificabili raccolte con consenso**
(`prd.md:1450-1452`), protette da una variabile d'ambiente.

### Forma minima della correzione

- **AD-21** — dichiarare che il recinto 5 è imposto da un meccanismo **diverso** dagli altri quattro
  (permessi di filesystem, o una API di ingestione che sia l'unico percorso di lettura), nominarlo, e
  nominare il percorso reale;
- **AD-15** — «store separato» significa collocazione separata con credenziali proprie, non una
  bandiera nel processo che deve essere escluso. Vale a maggior ragione quando lo store conterrà
  dati personali.

---

## Cosa ho verificato e risulta chiuso

Elenco esplicito, perché un rilievo mancato e un confine ben chiuso si distinguono solo se il
secondo è dichiarato.

| Confine | Dove | Esito |
|---|---|---|
| `domain/` non conosce `perception/` | AD-24:524, recinto 3 in AD-21:465 | **chiuso**, ed è l'unico dei cinque recinti scrivibile oggi con lo strumento esistente |
| Promozione candidato → `CircuitIR` con esito di fallimento proprio | AD-24:522-524, causa `candidate_unconfirmed` AD-19:411 | **chiuso** — la causa esiste nell'enumerazione |
| L'esperimento di Gate A non riceve candidati percettivi | diagramma :770-771, `prd.md:1440-1443` | **chiuso**, e chiuso bene: la freccia parte da `STRUCT`, non da `CONF` |
| Nessun VLM certifica la topologia | AD-5:174, AD-31:604-609 | **chiuso** (e già trattato in `review-veridicita.md:152-197`) |
| Il token dell'esperimento non entra in API di prodotto, artefatti o `Claim` | AD-11:293-294 | **chiuso** sul percorso di uscita; resta il problema di archiviazione, P6 |
| Log e telemetria senza dati identificativi | Consistency Conventions :648 | **chiuso** come convenzione; non copre il corpus, che non è telemetria |
| Immagini sorgente utente a 72 ore | AD-9:250-252 | **chiuso, e con il meccanismo giusto** — è il modello che AD-25 dovrebbe copiare |

---

## Ordine di risoluzione

Per costo, non per gravità: i primi tre sono righe dentro AD esistenti.

1. **P1 + P2** — due frasi in AD-25: il fail-closed vale per ogni uso non enumerato; l'assenza di
   registro equivale a `UNKNOWN`. Sblocca la sola difesa che il corpus ha.
2. **P8** — tre righe fra AD-24, AD-5 e AD-10, più togliere la provenienza dell'IR dai *Deferred*.
   Va fatto **prima** che il formato del `ProofGraph` sia persistito.
3. **P6** — emendamento in loco ad AD-11. Morde a Gate A, cioè adesso.
4. **P3** — `LicenseDecision` come entità con proprietario proprio. Richiede una riga in AD-8, che è
   la tabella già emendata una volta lo stesso giorno.
5. **P7 + P9** — righe in AD-8, AD-11, AD-28, AD-21, AD-15. Differite ma economiche.
6. **P4 + P5** — le uniche due che richiedono **decisioni dell'owner** prima della scrittura:
   ritenzione e minimizzazione del corpus, titolare e base del consenso, confine d'età per donatori
   e partecipanti, e lo spostamento del trigger del pacchetto documentale da «primo incasso» a
   «prima raccolta». Lo spine può nominare la lacuna oggi; non può colmarla da solo.
