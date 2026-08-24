# Audit del delta v3 — il PRD ha davvero recepito §H?

Oggetto: `prds/prd-Kirchhoff-2026-08-13/prd.md` (v3, 1.221 righe, 43 FR, 7 UJ, 22 SM).
Contratto di riferimento: `briefs/brief-Kirchhoff-2026-08-13/addendum.md` §H (H.1 superato,
H.2 conservato, H.3 conflitti, H.4 vincoli nuovi).
Metodo: per ogni riga di H.1 si cerca dove il PRD **asserisce ancora** la posizione superata; per
ogni voce di H.4 si cerca il **requisito testabile**, non la menzione; per ogni voce di H.2 si
verifica che non sia sparita o annacquata.

## Verdetto in una riga

Il delta è stato recepito **dove è stato scritto codice nuovo** (§1, §2, §5.0, §7, §8 primarie) e
**non è stato recepito dove nessuno ha riaperto il file** (§4 glossario, §9, §13, §14, §16, §17, e
tutte le Description da §5.1 in poi). Il risultato è un documento che cambia categoria nelle
sezioni riscritte e la contraddice in quelle ereditate.

Conteggi: **A — 12 residui v2** su 6 righe di H.1 (2 righe pulite). **B — 3 vincoli H.4 assenti,
1 parziale, 4 assorbiti.** **C — 2 conservati indeboliti, 2 caduti, 1 nominale.**
**Inconsistenze — 10.**

---

# A. H.1 — ciò che doveva sparire è ancora lì

### Riga 1 — «Vision centrata su risposta verificata» → superata

**A1 · §5.3, Description — CRITICO**
> «Il cuore del prodotto e la sola ragione per pagarlo.» (riga 489)

Detto della *Risoluzione e Verifica*. È letteralmente la proposta di valore v2 che H.1 riga 1
ritira. §1 dice che la verifica «smette di essere la proposta di valore»; §5.3 dice che è l'unica
ragione per pagare. Le due frasi non possono stare nello stesso documento.

**A2 · §6 Non-Goals — ALTO**
> «cancellerebbe la promessa di verificabilità, che è l'unica ragione per pagare.» (riga 839)

Stesso errore in una sezione normativa: il confine «non diventiamo un chatbot» è motivato con la
proposta di valore superata invece che con la continuità visuale. §6 non è stato toccato dal
correct-course.

**A3 · §5.10, Description — MEDIO**
> «SER, VSR, QPS e TTV non sono reportistica: sono il meccanismo che tiene in piedi la promessa
> commerciale.» (riga 797)

La promessa commerciale v3 è la derivazione disegnata, e le metriche che la reggono sono VVDR,
VCER, TVR, VDR — nessuna delle quali compare qui.

### Riga 2 — «`SolutionTrace` lineare come unico modello» → `ProofGraph`

**A4 · §4 Glossario — ALTO**
> «**Piano didattico** — la **sequenza ordinata** di Trasformazioni scelta per arrivare alla
> grandezza richiesta.» (riga 246)

Il glossario è normativo per dichiarazione propria (§0: «FR, UJ e SM usano quei termini alla
lettera»). Definisce ancora la derivazione come sequenza ordinata mentre FR-40 la impone come DAG
con branch e join. `ProofGraph` **non compare nel glossario** (0 occorrenze fra le 27 voci).

**A5 · §1 e §5.4 — MEDIO**
> «produce la **catena** circuito → trasformazione → circuito ridisegnato → equazione» (riga 53);
> «la **catena** di Trasformazioni con i disegni intermedi è il prodotto» (riga 541)

Framing lineare residuo. Meno grave di A4 perché è prosa, ma è la stessa immagine mentale che H.1
dichiara insufficiente per sovrapposizione, Thévenin su sottoproblemi e transitori.

### Riga 3 — «la sequenza didattica come terzo moat» → **PULITA**

§2 riga 84–89 contiene la correzione esplicita, cita il precedente iCircuits/autoCircuits, e
declassa la sequenza a requisito di prodotto. Nessun residuo altrove ("moat"/"differenziatore" non
compaiono in altre posizioni). Nessun rilievo.

### Riga 4 — «North star soluzioni verificate a settimana» → VVDR

**A6 · §4 Glossario — ALTO**
> «**Soluzione consegnata** — … È l'unità di consumo dei Crediti e **l'unità della metrica nord**.»
> (righe 250–251)

Contraddizione frontale con SM-3 («VVDR ⭐ Metrica nord, v3»). Il glossario continua a nominare
metrica nord un'unità che si può massimizzare senza disegnare nulla — esattamente il difetto per cui
la north star è stata sostituita. Peggiora perché i Crediti sono fuori MVP (§7.2).

### Riga 5 — «Foto nella prima versione» → scende a Gate C

**A7 · §16 Open Questions, punto 8 — CRITICO**
> «i modelli frontier sono ritenuti insufficienti su questo compito e **l'ingresso da foto resta
> nell'MVP**. Vedi §7 e `sprint-change-proposal-2026-08-13.md`.» (righe 1206–1209)

Il PRD afferma qui l'esatto contrario di §7.2 («Ingresso da foto e tutta la percezione — spostati a
Gate C»), e rinvia a §7 come conferma. È la decisione del 13 agosto sopravvissuta al proprio
superamento del 15. Un lettore a valle che apre §16 costruisce l'MVP sbagliato.

**A8 · §14 Platform — MEDIO**
> «**Web progressiva, mobile-first**, con **accesso alla fotocamera**.» (riga 1161)

Il contratto di piattaforma continua a richiedere la fotocamera come capacità v1. §14 non è stato
riscritto: non nomina né il kernel, né i tre adapter, né Ardesia.

**A9 · §9 Cross-Cutting NFRs — MEDIO**
> «Budget di latenza end-to-end. **Dal caricamento** alla Soluzione consegnata, < 45 s» (riga 1031);
> «**Mobile-first.** Il flusso B2C si completa su schermo telefono» (riga 1042)

Gli NFR trasversali sono scritti sul flusso caricamento-foto/B2C, che l'MVP non contiene. Nessun NFR
copre il kernel (determinismo del rendering, costo di ri-layout, latenza per passo).

### Riga 6 — «gold set fotografico come gate che precede il prodotto» → è il gate di Gate C

**A10 · §8 SM-1, nota «Punto cieco in chiusura» — ALTO**
> «La **Story 1.3** aggiunge la metà fotografica da dataset a licenza aperta verificata … Resta
> cieca finché 1.3 non è `done`.» (righe 950–954)

Rimette il gold set fotografico dentro il primo epico, cioè prima del prodotto, che è precisamente
ciò che H.1 riga 6 sposta a Gate C. Doppio problema: la nota è datata «13 agosto, sera» e cita un ID
di storia della decomposizione v2, ora rescopata.

### Riga 7 — «Backlog B2C-pesante» → ruoli economici separati

**A11 · §13 Monetization — MEDIO**
> «**B2C a Crediti prepagati**, mai abbonamento mensile … Struttura: una prova gratuita limitata con
> filigrana; due pacchetti di Crediti; un pass a tempo …» (righe 1116–1119)

§13 non è stata toccata dal correct-course: presenta il B2C come il modello di ricavo e non enuncia
mai la separazione v3 (B2C = acquisizione e dati, B2B = ricavo). L'unica traccia della separazione è
in §7.2 («Studio … resta il motore di ricavo»), che è un elenco di esclusioni, non la sezione
monetizzazione.

**A12 · §3.3 Key User Journeys — MEDIO**
Sette UJ, sei B2C, cinque con la foto, tutte a Crediti. La §5 lo ammette
(«`[NOTE FOR PM]` Le UJ-1…UJ-7 raccontano sessioni **con la foto**», riga 274) ma §3.3 resta
invariata e senza marcatura di gate. Vedi anche I2: nessuna UJ descrive l'MVP.

### Riga 8 — «Truthfulness Enforcer come skill esterna» → **PULITA**

FR-42 lo supera con il tipo `Claim` e conseguenze testabili («un ambiente senza skill installate
produce gli stessi verdetti»), e cita l'origine. Nessun residuo. Nessun rilievo.

---

# B. H.4 — vincolo o menzione?

| # | Vincolo H.4 | Dove | Esito |
|---|---|---|---|
| 1 | `CircuitIR` / `LayoutIR` distinti | FR-37 | **Assorbito** |
| 2 | `LayoutPatch` + invariante `p_{k+1}(x)=p_k(x)` | FR-38 | **Assorbito** |
| 3 | Grammatica del passo a sei campi | FR-39 | **Assorbito** |
| 4 | Visual round-trip come controllo primario | FR-41 | **Assorbito** |
| 5 | `StudentTrace` input semantico del verifier | — | **ASSENTE** |
| 6 | Tre adapter, un kernel (Web/API · MCP · Ardesia) | §1 prosa | **Solo menzione** |
| 7 | Metriche nuove + VVDR north star | §8, §16 Q0 | **Parziale** |
| 8 | Famiglie di test obbligatorie | — | **ASSENTE** |

**B1–B4 — assorbiti correttamente.** FR-37…FR-39 e FR-41 portano conseguenze falsificabili
(round-trip di serializzazione, rifiuto del patch che dichiara `preserve` su elemento assente,
`node_mapping` totale, confronto di grafi e non di pixel, rifiuto tipizzato invece di avviso).
Nessun rilievo.

**B5 · `StudentTrace` — ASSENTE, ALTO**
Zero occorrenze in 1.221 righe. Il vincolo H.4 «`StudentTrace` come input semantico del verifier,
**non** come immagine» non ha alcuna controparte. L'unico punto in cui lo studente produce qualcosa
è FR-17 (modalità Studio), che dice
> «Il passo successivo non è visibile prima che l'utente abbia risposto o esplicitamente saltato»

senza mai dire *in che forma* la risposta entra nel verificatore. È il vincolo che impedisce a
qualcuno, a valle, di implementare «lo studente fotografa il suo svolgimento»: senza requisito, la
porta resta aperta.

**B6 · Tre adapter, un kernel — SOLO MENZIONE, ALTO**
> «Le superfici sono Web/API, MCP e MCP Apps, e Ardesia — **tre adapter, un kernel**, nessun fork
> «Kirchhoff per Ardesia» (§23 del piano, addendum §H.4).» (§1, righe 70–72)

È l'**unica** occorrenza di "Ardesia" nel PRD, ed è in Vision. Conseguenze mancanti:
nessun FR; §14 Platform elenca solo web + superficie assistente + pagine pubbliche; §15 Public
Surface Contract copre solo la superficie assistente. Il pezzo operativo del vincolo — «dentro
Ardesia il plugin consuma ToolHost, Simulation Plugin e LessonOS **senza duplicare** auth, shell,
dashboard, memoria o simulatore» — non compare in nessuna forma (`ToolHost`, `LessonOS`,
`Simulation Plugin`: 0 occorrenze). Un vincolo anti-fork enunciato solo nella visione non impedisce
il fork.

**B7 · Metriche nuove — PARZIALE**
Definite bene (SM-12…SM-17 + SM-3) e con le soglie correttamente owner-locked (§16 punto 0). Ma la
conseguenza operativa non è stata propagata:

- **ALTO** — FR-34, l'unico requisito di harness:
  > «Il sistema misura **VSR, SER, QPS e TTV** su un insieme di riferimento annotato» (riga 803)

  contro §8 riga 965: «Le sei metriche qui sotto entrano nel PRD perché **l'harness deve calcolarle
  dal primo giorno**». Il PRD chiede una cosa in §8 e ne specifica un'altra nel requisito che la
  implementa. VCER — la metrica del kill criterion — non è richiesta da nessun FR.
- **ALTO** — §9 Osservabilità:
  > «SER, VSR, QPS, TTV, tasso di Rifiuto e correzioni per soluzione sono strumentati in
  > produzione» (riga 1044)

  Nessuna metrica v3 è strumentata. VDR (determinismo del rendering) e VCER sono esattamente ciò che
  si degrada in silenzio senza strumentazione.
- **MEDIO** — §4 Glossario definisce SER, VSR, QPS, TTV e **nessuna** delle sette nuove, in un
  documento che dichiara (§0) di essere «ancorato al Glossario» e che chiama violazione di disciplina
  un sinonimo introdotto altrove.

**B8 · Famiglie di test obbligatorie — ASSENTE, ALTO**
Zero occorrenze di `property-based`, `metamorfic*`, `mutation`, `golden`, `fixture`, `escaped`. Il
vincolo H.4 («incluse property-based, metamorfiche, mutation testing, golden ProofGraph e visual
round-trip. **Ogni escaped failure diventa fixture o invariante permanente**») ha come unica
controparte §9:
> «**Non-regressione della qualità.** Nessuna modifica che tocchi estrazione, Validazione elettrica,
> Trasformazioni o Piano didattico raggiunge la produzione senza esecuzione dell'eval harness.»
> (righe 1046–1048)

che è un gate di CI su quattro sottosistemi (tre dei quali fuori MVP), non una politica di test. La
regola «escaped failure → invariante permanente» è il meccanismo anti-regressione del kernel: senza,
il visual round-trip resta un controllo runtime senza rete di test dietro.

---

# C. H.2 — ciò che era conservato è ancora conservato?

| Voce H.2 | Stato |
|---|---|
| Solver deterministico | Conservato (FR-13, §9 Determinismo) |
| Aritmetica esatta e oracolo | **Caduto** |
| Harness ed eval | Conservato ma ristretto (vedi B7) |
| Ports-and-adapters | **Caduto** |
| I cinque controlli | Conservato (FR-11, §4) |
| Semantica del rifiuto | Conservato e rafforzato (FR-12 + SM-16 RRC) |
| Disclosure e provenienza | Conservato (FR-19, FR-29, §11) |
| Concetti di entitlement | Conservato nella sostanza, non nel nome |
| Review a contesto pulito · 159 test · 100% | **Assente** (nominale) |
| B1–B3 (MCP, MRTR, MCP Apps) | Conservato (FR-20, §15) |
| B4 (confine dell'LLM) | Conservato e rafforzato (FR-13, FR-41) |
| B5 (tolleranze) | **Indebolito** |
| B6 (campi obbligatori dell'IR) | **Indebolito** |
| B7 (stack) · §C (compliance) | Correttamente fuori / conservato (§11, §12) |

**C1 · B5, le tolleranze numeriche — ALTO**
H.2 conserva esplicitamente «tolleranze **1e-9 simbolico / 1e-6 numerico** e mancata pubblicazione in
caso di discordanza». Il PRD conserva la seconda metà (FR-10: «Una discordanza fra percorsi impedisce
la pubblicazione») e perde la prima: le uniche formulazioni sono
> «i due percorsi non concordano **entro tolleranza**» (riga 160) e «coincide con quello del Percorso
> A **entro tolleranza**» (FR-14, riga 555)

Nessun numero, in nessun punto del documento. Per lo standard che il PRD stesso applica altrove
(«un requisito con una forbice non è testabile», nota FR-30) questi due FR non sono testabili.

**C2 · B6, i campi obbligatori dell'IR — ALTO**
H.2 conserva «provenienza, `symbolic`, `schedule`, `curriculum_profile` **nell'IR**». Il glossario:
> «**IR** — … nodi, componenti, terminali, valori (numerici *e* simbolici), grandezze richieste,
> convenzioni, **provenienza**.» (righe 208–211)

`symbolic` e la provenienza ci sono. **`schedule` non compare mai.** `curriculum_profile` esiste solo
come feature di prodotto (FR-16), mai come campo dell'IR: FR-16 dice che il Profilo «restringe le
Trasformazioni ammesse», non che viaggia nell'IR. Il contratto di dato è più povero di quanto H.2
conservi, e l'architettura a valle erediterà la versione impoverita.

**C3 · «aritmetica esatta e oracolo» — MEDIO**
`aritmetica`, `esatta` (riferita all'aritmetica), `oracolo`: 0 occorrenze. Sopravvive il determinismo
(FR-13, §9) e il confronto **esatto** di grafi (FR-41), che è un'altra cosa. L'oracolo — il
riferimento contro cui si misura la correttezza numerica — non è nominato da nessun requisito, il che
lascia SER senza una definizione operativa di "sbagliato".

**C4 · ports-and-adapters — MEDIO**
0 occorrenze. L'unica traccia architetturale è «tre adapter, un kernel» (§1), che è la conseguenza,
non il vincolo. Difendibile come materia del documento di architettura, ma H.2 lo elenca fra le cose
non ridiscutibili e §0 dichiara questo PRD chain-top verso `bmad-architecture`: se non passa di qui,
passa per nulla.

**C5 · concetti di entitlement — MEDIO**
`entitlement`: 0 occorrenze. La sostanza è però preservata dove conta: FR-26 tiene l'invariante che
H.3.1 chiama «owner-locked» («Un Rifiuto di certificazione non consuma Crediti… Una ripresa dopo
Domanda mirata non consuma Crediti aggiuntivi»), e §15 la ripete come idempotenza. Il rilievo è che
§7.2 esclude «Crediti, pagamenti, posti Studio» dall'MVP **senza qualificare** che i *concetti* di
entitlement restano vincolanti per il kernel: un'esclusione non qualificata è un invito a
implementare il kernel senza il tipo.

**C6 · «processo di review a contesto pulito · 159 test verdi · copertura 100%» — INFORMATIVO**
Assenti. Plausibilmente fuori dal perimetro di un PRD (processo e stato del disco, non requisito),
ma vanno riportati esplicitamente in `bmad-architecture`, altrimenti H.2 li conserva in un documento
che nessun artefatto a valle legge.

---

# Inconsistenze interne create o lasciate dall'aggiornamento

**I1 · Metriche che validano requisiti usciti dallo scope — ALTO**
§7.2 riga 919: «FR-1…FR-9 restano scritti, **fuori MVP**». §8 continua a puntarci:
> SM-2 «Valida FR-2, FR-3, FR-4, FR-14» · SM-5 «Valida FR-2, FR-10, FR-14» ·
> SM-6 «Valida FR-1, FR-5» · SM-8 «Valida FR-2, FR-5, FR-9»

Quattro metriche su dieci secondarie/primarie validano requisiti che l'MVP non implementa, e §8 non
ha alcuna allocazione per gate. Si aggiungono SM-C3 (che parla di Pass di estrazione) e §10.3 («costo
per Soluzione consegnata sotto il 10% del **prezzo effettivo**», con zero incassi in MVP).

**I2 · L'MVP non ha nessuna user journey — ALTO**
Gli unici FR in scope sono FR-37…FR-43 e **nessuno** porta un «Realizza UJ-n» — a differenza di tutti
gli FR fuori scope, che li portano. Tutte e sette le UJ descrivono flussi foto/Crediti. §5 riga 274
lo dichiara e rimanda a `bmad-ux`, il che è corretto come processo, ma nel frattempo il documento che
alimenta UX e storie non contiene un solo scenario del prodotto che chiede di costruire.

**I3 · La superficie assistente non è allocata a nessun gate — MEDIO**
§5.6 (FR-20, FR-21), §13.1, §15 «Public Surface Contract», SM-11 la trattano come viva e cardine
(«🔑 Sotto la tesi MCP-first è la metrica che decide se il canale è un cardine o una perdita»). §7.1
non la include; §7.2 non la esclude. §15 la chiama «contratto pubblico» — con obblighi di
versionamento e deprecazione — per una superficie che nessuna sezione di scope colloca.

**I4 · Vocabolario dei gate incoerente e mai definito — MEDIO**
> §7: «non si prosegue su **B, C, D**» (riga 855) · §7.2: «Studio B2B … **Gate E/F**» (riga 920) ·
> §5: «Studio → Gate E/F, tutor e lavagna → Gate B» (riga 273)

Nel primo elenco Studio starebbe in D, nel secondo in E/F. Il PRD usa Gate A/B/C/D/E/F senza definirli
né in §7 né nel glossario: la sequenza vive solo nel piano master. Un lettore a valle non può
verificare l'allocazione.

**I5 · Indice delle assunzioni incompleto — MEDIO**
§0 riga 22: «Le assunzioni sono taggate inline `[ASSUMPTION]` e **indicizzate in §17**». Tag inline:
6 (righe 12, 100, 123, 333, 889, 1152). Voci in §17: 4. Mancano **entrambe le assunzioni nuove della
v3**:
- FR-40 riga 333 — «l'MVP con tre trasformazioni produce grafi quasi lineari»;
- §7.0 riga 889 — «il kill criterion è valutabile in modo non ambiguo dal confronto fra continuità
  visuale e re-layout completo», che il PRD stesso qualifica come «la condizione perché §7 abbia
  senso».

L'assunzione portante dell'intero MVP non è indicizzata.

**I6 · §13 non recepisce la decisione chiusa di H.3.1 — MEDIO**
H.3.1 (chiusa 15 ago): «mensile scartato · Free, Exam Sprint e crediti prepagati confermati ·
**annuale scontato resta da testare**». §13 riga 1119 elenca «un piano annuale per lo studente
diligente» come struttura decisa, e §16 non contiene la corrispondente domanda aperta. La decisione
è stata recepita per metà: il divieto sì, l'incertezza no.

**I7 · «Le cinque leggi K-0…K-5» — BASSO**
§0 riga 26: da K-0 a K-5 sono sei identificatori, non cinque. Il PRD cita poi K-0, K-1, K-2, K-3, K-4
e mai K-5 in isolamento. Da allineare alla costituzione, che è owner-locked.

**I8 · Definizione divergente del Percorso C — BASSO**
§4: «**Percorso C** — risoluzione per simulazione numerica esterna. Opzionale, v2.» ·
§7.2: «**Percorso C** (terzo motore di **verifica**) — differito.» Percorso di risoluzione o motore
di verifica: il glossario e lo scope non dicono la stessa cosa.

**I9 · SM-3 senza aggancio ai requisiti — BASSO**
«Valida **l'intero §5.0 e §5**.» È l'unica SM che non elenca FR. Per la metrica nord è il legame più
importante del documento.

**I10 · Riferimento a un artefatto a valle rescopato — MEDIO**
SM-1 dipende dalla «Story 1.3» per chiudere il proprio punto cieco, e §16 punto 8 rinvia a
`sprint-change-proposal-2026-08-13.md`. Entrambi appartengono alla decomposizione del 13 agosto, che
il correct-course del 15 ha rescopato (foto → Gate C). Un requisito di misura non dovrebbe dipendere
da un ID di storia, tanto meno da uno che potrebbe non esistere più.

---

## Ordine di riparazione suggerito

1. **A7** (§16 punto 8) e **A6** (§4 metrica nord): contraddizioni frontali, costo di fix ~10 minuti,
   costo di non-fix = MVP sbagliato a valle.
2. **B7/FR-34 + §9**: allineare harness e osservabilità alle sette metriche v3, altrimenti il kill
   criterion di Gate A non è misurabile dal sistema che deve misurarlo.
3. **B5, B6, B8**: tre vincoli H.4 da scrivere come FR (`StudentTrace`; adapter Ardesia senza
   duplicazione; famiglie di test + escaped failure → invariante).
4. **C1, C2**: rimettere i numeri delle tolleranze e i campi `schedule` / `curriculum_profile` nell'IR
   prima che `bmad-architecture` erediti il contratto impoverito.
5. **§4 glossario**: aggiungere `CircuitIR`, `LayoutIR`, `LayoutPatch`, `ProofGraph`,
   `ReconstructedCircuitIR`, `Claim`, `StudentTrace` e le sette metriche; e risolvere la coppia
   sinonimica `IR` / `CircuitIR`, che §0 classifica come violazione di disciplina.
6. **A1, A2, A3, A11, A8, A9**: riscrivere le Description e le sezioni ereditate (§5.3, §6, §5.10,
   §13, §14, §9) sulla proposta di valore v3.
