---
title: Kirchhoff
version: 3
status: draft
created: 2026-08-13
updated: 2026-08-15
supersedes: "PRD v2 (13 ago 2026) — categoria «risolutore verificato»"
upstream: "docs/02-costituzione-kirchhoff.md (owner-locked) · briefs/brief-Kirchhoff-2026-08-13/brief.md v3 + addendum.md §H · docs/inbox/kirchhoff_01_piano_master_v3.md §25.1"
---

# PRD: Kirchhoff
*`[ASSUMPTION: "Kirchhoff" è un titolo di lavoro; la verifica del marchio su TMview/UIBM non è
stata fatta.]`*

## 0. Document Purpose

Questo PRD è per il fondatore-PM e per i workflow a valle: `bmad-ux`, `bmad-architecture`,
`bmad-create-epics-and-stories`. È ancorato al Glossario (§4): FR, UJ e SM usano quei termini
alla lettera, e un sinonimo introdotto altrove è una violazione di disciplina, non uno stile.
Le feature sono raggruppate con gli FR annidati e numerati globalmente (`FR-n`), così i
riferimenti restano stabili anche se le feature vengono riorganizzate. Le assunzioni sono
taggate inline `[ASSUMPTION]` e indicizzate in §17.

Costruisce su quattro input già esistenti e **non li duplica**:

- `docs/02-costituzione-kirchhoff.md` — **owner-locked**. Le cinque leggi K-0…K-5 e i nove confini
  che un agente non può spostare. Viene **prima** di questo PRD: un requisito che la contraddice è
  in errore, non in evoluzione.
- `planning-artifacts/briefs/brief-Kirchhoff-2026-08-13/brief.md` **v3** — perché il prodotto
  esiste, per chi, e quali confini non si attraversano.
- `.../brief-Kirchhoff-2026-08-13/addendum.md` — alternative scartate (§A), vincoli tecnici
  (§B), compliance (§C), economia (§D), gate di validazione (§E), go-to-market (§F), e **§H, il
  delta v3**: cosa il correct-course supera (H.1), cosa conserva (H.2), i conflitti (H.3), i
  vincoli nuovi che questo PRD doveva recepire (H.4).
- `docs/inbox/kirchhoff_01_piano_master_v3.md` — il piano master v3, sorgente del cambio di
  categoria. **Sostituisce `docs/00-fonte-piano-kirchhoff.md`** come upstream: quello resta il
  piano v2, storico, e non va più letto come corrente.

Le scelte tecnologiche (protocollo, solver, provider, hosting) **non stanno qui**: stanno
nell'addendum del brief e nel documento di architettura. Questo PRD dice *cosa il sistema deve
fare* e *cosa non deve mai fare*.

---

## 1. Vision

> **Cambio di categoria, v3.** Il PRD v2 vendeva la *risposta verificata*. Questa versione vende
> **la derivazione disegnata**. La verifica non è retrocessa — resta il gate costituzionale K-1,
> e nessuno stato riceve `Verified` da un modello — ma smette di essere la proposta di valore,
> perché un prodotto che verifica senza disegnare niente soddisfaceva il PRD v2 alla lettera.
> Origine del cambio: piano master §0, addendum §H.1.

Kirchhoff è un **Verified Visual Reasoning Engine**: dato un circuito, produce la catena
*circuito → trasformazione → circuito ridisegnato → equazione*, e la ripete finché il problema è
chiuso. Ogni stato pubblicato è verificabile a macchina.

Il bene scarso non è il numero finale — quello è gratis ovunque, e lo sarà sempre di più. È la
**continuità visuale della derivazione**: quando due resistenze in serie diventano una, tutto il
resto del circuito **resta dove stava**. Il disegno non illustra il ragionamento: *è* il
ragionamento (K-0). Un passo senza disegno non è un passo — è una riga di calcolo, e va fusa con
la precedente.

Questo è ciò che un modello generalista non può fare, e la ragione è strutturale, non
temporanea: sa produrre un'immagine plausibile di un circuito, non sa garantire che quell'immagine
sia **lo stesso grafo** di quello di partenza, meno la trasformazione dichiarata. Kirchhoff lo
garantisce riparsando il proprio disegno e confrontando i grafi.

Lo stesso kernel serve due prodotti e tre superfici. **Solve** (B2C, a crediti) dà allo studente
la derivazione disegnata nel formalismo del suo corso; **Studio** (B2B) dà a tutor, centri e
docenti un generatore di varianti d'esame con soluzioni garantite. Le superfici sono Web/API, MCP
e MCP Apps, e Ardesia — **tre adapter, un kernel**, nessun fork «Kirchhoff per Ardesia» (§23 del
piano, addendum §H.4).

## 2. Why Now

Il timing è portante su tre assi indipendenti, e tutti e tre scadono.

**La finestra si sta chiudendo, non aprendo.** I modelli di visione frontier migliorano di
trimestre in trimestre sul riconoscimento di schemi circuitali. Fra 12–24 mesi "leggere il
circuito dalla foto" non sarà più differenziante. La conseguenza non è "sbrigati a costruire il
lettore": è **costruire fin dall'inizio il livello che resta di valore quando il lettore diventa
gratis** — continuità visuale certificata, verifica, profilo curricolare, generazione B2B.

> **Correzione v3 su questo elenco.** Il PRD v2 contava **la sequenza didattica** fra i
> differenziatori. Non lo è: *iCircuits/autoCircuits* del Politecnico di Torino è precedente
> rilevante, e «circuiti come nodi, metodi come archi» non è proprietario. Resta **requisito di
> prodotto** — il piano didattico e il Catalogo chiuso restano negli FR — ma esce dalla lista dei
> moat. Origine: piano master §2.1, addendum §H.1. Vedi §27.12: una collaborazione o licenza con
> quel precedente è decisione aperta, da valutare senza assumere disponibilità o diritti.

**Cosa resta da dimostrare, detto con precisione.** *Thevenin* si posiziona su `scan → recognize →
solve → learn`, promettendo soluzione completa da fotografia e diagrammi ridisegnati quando servono;
*AskSia* offre foto o testo, metodo scelto automaticamente, passi numerati, diagrammi generati,
tutor laterale e una forma di self-check. Le percentuali di accuratezza che entrambi pubblicano sono
**claim commerciali dei fornitori, non benchmark indipendenti**, e non vanno usate come riferimento.
Sommato al precedente iCircuits, ne segue che *«mostriamo più circuiti durante la soluzione»* non è
un moat. La tesi di Kirchhoff è più stretta e più falsificabile:

> **non che sa ridisegnare un circuito, ma che sa mantenere la continuità semantica e spaziale fra
> due stati circuitali verificati.**

**Perché la scommessa ha una base tecnica.** Due lavori indicano dove i sistemi generalisti
cedono, e sono esattamente i due punti su cui poggia l'architettura «modello propone, kernel
strutturato certifica»: **CircuitReason-1k** — anche i migliori sistemi multimodali degradano sui
problemi circuitali a ragionamento lungo, con errori di *topology-to-target binding*, di convenzioni
fisiche e di propagazione delle quantità; **NetlistBench** — anche su rappresentazioni **già
strutturate** gli LLM mostrano *structure-preservation failures* al crescere della lunghezza delle
modifiche. Il secondo è il più rilevante per noi: dice che passare al netlist non risolve da solo il
problema che `LayoutPatch` e il round-trip esistono per chiudere.
`[ASSUMPTION: i due riferimenti di ricerca e i due riferimenti commerciali sono stati forniti
dall'owner il 15 agosto e non verificati in prima persona. Vanno confermati prima che una di queste
righe finisca in materiale pubblico o in una tabella comparativa.]`

> 🟠 **`[NOTE FOR PM]` Il calendario di questa sezione e §7.0 non sono riconciliati.** Qui la
> finestra dice «motore ad agosto–settembre, beta a ottobre, spinta piena a dicembre–gennaio».
> §7.0 descrive un MVP **senza utenti, senza ricavi e senza scadenza**, il cui esito può essere
> «si ferma». Le due cose possono convivere solo se Gate A ha un **tetto di tempo o di sforzo**:
> senza, questa è la forma del «sesto progetto al 60%» che l'addendum §G nomina come rischio
> governante. Vedi §16 Q11.

**L'obbligo di trasparenza è già in vigore.** L'art. 50 dell'AI Act si applica dal 2 agosto
2026, e il rinvio del Digital Omnibus riguarda l'Allegato III, non lui. La finestra di grazia al
2 dicembre 2026 per la marcatura vale solo per sistemi già sul mercato al 2 agosto 2026: un
prodotto nuovo non ne beneficia. Progettare disclosure e marcatura adesso costa mezza giornata;
ritrofittarle dopo è una riprogettazione del formato di export.

**La domanda è stagionale e la prossima onda è a gennaio.** Il B2C ha senso solo se arriva
*prima* di una sessione d'esame. Da agosto 2026 la finestra è: motore ad agosto–settembre, beta
a ottobre, spinta piena a dicembre–gennaio. Un lancio a novembre o a metà agosto non trova
domanda. `[ASSUMPTION: questa sequenza presuppone dedizione parziale — il fondatore mantiene
l'attività di ripetizioni, che finanzia lo sviluppo, fornisce il gold set e i primi utenti, ed è
il primo cliente Studio. A tempo pieno il sequenziamento cambierebbe.]`

## 3. Target User

### 3.1 Jobs To Be Done

- **Funzionale.** "Devo consegnare otto esercizi corretti entro dopodomani, e devo poter
  ricopiare il procedimento — non solo il risultato."
- **Funzionale.** "Devo capire *perché* si usa Millman qui e Thévenin lì, perché all'orale me lo
  chiedono."
- **Emotivo.** "Non voglio scoprire all'esame che la fonte su cui ho studiato sbagliava."
- **Sociale.** "Voglio essere quello che nel gruppo del corso porta la soluzione giusta."
- **Funzionale (B2B).** "Devo preparare la simulazione d'esame di venerdì con valori diversi per
  ogni studente, e non ho quattro ore."
- **Sociale (B2B).** "Se do ai miei studenti un foglio soluzione sbagliato, perdo credibilità."
- **Del costruttore.** "Uso io per primo Studio ogni settimana per le ripetizioni. Se non
  risolve un mio problema reale, non risolve quello di nessuno."

### 3.2 Non-Users (v1)

- **Studenti sotto i 18 anni.** L'età minima v1 è 18 con dichiarazione al signup.
  `[ASSUMPTION: il target di lancio è universitario; l'estensione a 14–17 richiede informativa
  in linguaggio semplificato ex art. 4 L.132/2025 ed è rimandata a v2.]`
- **Chi studia elettronica non lineare** (diodi, BJT, MOS in regione attiva). Fuori scope,
  dichiarato pubblicamente.
- **Istituzioni che vogliono valutare studenti.** Non è un limite tecnico: è un confine
  permanente (§6).
- **Chi vuole un chatbot generalista.** Non c'è chat libera.

### 3.3 Key User Journeys

> 🟠 **`[NOTE FOR PM]` Le UJ qui sotto raccontano il prodotto v2 e nessuna copre l'MVP.**
> UJ-1…UJ-7 descrivono sessioni che cominciano con una fotografia; l'MVP della v3 ha ingresso
> strutturato e i requisiti del kernel (FR-37…FR-43, FR-45, FR-46) non sono realizzati da nessuna
> journey. **Non le riscrivo qui**: una user journey si cattura dall'utente, non si autorizza da un
> PRD. È il primo lavoro del passo 4 (UX) — serve che tu racconti una sessione vera sul kernel:
> chi è, cosa fa, in che ordine, dove finisce. Fino ad allora ogni «Realizza UJ-n» dentro un FR
> dell'MVP va letto come un riferimento a una journey che descrive un ingresso diverso.

- **UJ-1. Marco fotografa alle 23:40 e ha la soluzione certificata prima di mezzanotte.**
  Marco, terzo anno di Ingegneria Energetica, esame di Elettrotecnica fra due giorni, sta
  copiando gli appunti di un compagno. Entra da mobile web, non autenticato, primo contatto.
  Scatta la foto storta di un esercizio manoscritto — rete resistiva con generatore e otto
  resistori. Il sistema mostra in pochi secondi l'**Anteprima di ricostruzione**: il circuito
  ridisegnato accanto alla sua foto, ogni componente evidenziato sopra la propria posizione
  originale. Marco riconosce il suo circuito e conferma con un click. La **Soluzione consegnata**
  arriva col **Badge Verificata**, i passaggi con il circuito ridisegnato a ogni riduzione, e il
  valore chiesto in fondo. Resta con la soluzione, due Crediti di prova rimasti, e la sensazione
  precisa che il sistema abbia *letto* il suo foglio.
  **Edge case:** se la foto contiene due esercizi, il sistema chiede quale prima di procedere —
  non ne sceglie uno né li fonde.

- **UJ-2. Giulia risolve l'ambiguità su R8 senza uscire dal flusso.**
  Giulia ha fotografato un esercizio dove la cifra di R8 è mangiata da un'ombra. Autenticata,
  pacchetto da 40. Dopo l'estrazione il sistema non è d'accordo con se stesso su quel componente
  e pone **una Domanda mirata**: la foto ritagliata e ingrandita su R8, due opzioni — 20 Ω o
  30 Ω — più "altro valore". Giulia guarda il suo foglio, sceglie 30 Ω. Il sistema riprende da
  dove era, mostra l'Anteprima con la correzione applicata e la provenienza della scelta
  registrata, e prosegue. Una sola domanda, nessuna ripartenza, nessun Credito consumato due
  volte.
  **Edge case:** se dopo due giri restano ambiguità, il sistema non fa un terzo giro: apre
  l'editor del circuito e la lascia sistemare a mano.

- **UJ-3. Il sistema rifiuta di certificare, e questo è il momento in cui Marco decide se
  fidarsi.**
  Stesso Marco, esercizio diverso: un transitorio con due commutazioni. L'estrazione passa la
  Validazione elettrica, la risoluzione gira, ma i due percorsi non concordano entro tolleranza.
  Invece della soluzione, Marco vede un messaggio esplicito: *"Non riesco a certificare questa
  soluzione. I due metodi indipendenti divergono sul ramo C–GND. Non ti mostro un numero di cui
  non posso rispondere."* Con: cosa può fare (aprire l'editor, correggere la topologia, o
  segnalare), **nessun Credito addebitato**, e la ricostruzione comunque scaricabile. Marco non
  ottiene quello che voleva — ma ottiene la ragione per tornare.

- **UJ-4. Sara studia in modalità Studio a tre settimane dall'esame.**
  Sara, seconda ripetizione dell'esame, ha capito che copiare i risultati non le è servito. Piano
  Anno Accademico. Carica un esercizio e sceglie la modalità Studio: il sistema mostra il primo
  passaggio, poi si ferma e le chiede quale Trasformazione applicherebbe adesso. Sara sbaglia
  (dice "serie"), il sistema le mostra perché quei due resistori non sono in serie — condividono
  un nodo con un terzo ramo — e solo allora rivela il passaggio corretto. Arriva in fondo avendo
  scoperto ogni passo dopo averci provato.

- **UJ-5. Davide prepara dodici simulazioni diverse in venti minuti.**
  Davide, tutor privato, dodici studenti alla stessa simulazione d'esame di venerdì, e il
  problema di sempre: se il testo è identico se lo passano. Piano Tutor. Carica un esercizio dal
  suo archivio LaTeX, imposta 12 Varianti, vincola i valori alla serie E24 e il risultato a
  restare in un intervallo leggibile. Ottiene dodici testi con valori diversi, dodici soluzioni
  complete verificate con i disegni, e dodici **Fogli soluzione** separati con checksum. Esporta
  in PDF per la stampa e nel formato della sua piattaforma di e-learning. Il LaTeX compila al
  primo colpo nel suo ambiente.

- **UJ-6. La prof.ssa Ferrari verifica lo strumento che i suoi studenti stanno già usando.**
  Ferrari ha visto un PDF con la Marcatura di provenienza Kirchhoff in un elaborato. Va sul sito
  aspettandosi di doverlo vietare. Trova la **policy di uso accademico** in chiaro, la modalità
  Studio come default educativo, e il **programma docenti**: accesso gratuito a Studio con email
  istituzionale, senza obblighi. Prova il generatore di Varianti sul suo tema d'esame dell'anno
  scorso e ottiene sei Varianti verificate. Non scrive il post arrabbiato: chiede se può
  configurare le convenzioni di segno del suo corso.

- **UJ-7. Marco risolve senza uscire dalla conversazione con l'assistente.**
  Marco sta già parlando con un assistente AI. Allega la foto e chiede di risolverla.
  L'assistente chiama Kirchhoff; compare **dentro la conversazione** un pannello con la foto,
  l'Anteprima di ricostruzione e il pulsante di conferma. Marco conferma nel pannello.
  L'assistente riceve anche il riassunto testuale della ricostruzione, quindi *sa* cosa Marco ha
  appena confermato e può ragionarci sopra. La Soluzione consegnata torna in conversazione, con
  il link per collegare un account Kirchhoff e conservare la cronologia.
  **Edge case:** se Marco non ha un account collegato, vale la quota di prova legata alla
  sessione, e il collegamento gli viene proposto — non imposto — alla prima soluzione.

---

## 4. Glossario

I workflow a valle e i lettori devono usare questi termini alla lettera.

- **IR (Rappresentazione Intermedia)** — il grafo elettrico normalizzato: nodi, componenti,
  terminali, valori (numerici *e* simbolici), grandezze richieste, convenzioni, provenienza.
  È il contratto fra tutti gli stadi. Un IR ha esattamente uno stato fra `estratto`,
  `validato`, `confermato`, `risolto`.
- **Pass di estrazione** — una singola lettura indipendente dell'immagine che produce un IR
  candidato. Un'estrazione ne esegue K (K ≥ 3 in produzione).
- **Accordo** — la misura di quanto i Pass di estrazione concordano, per componente e
  complessiva. Deriva dal confronto fra IR candidati. **Non** è una confidence dichiarata da un
  modello.
- **Ambiguità residua** — un elemento dell'IR su cui l'Accordo è basso *e* che sopravvive alla
  Validazione elettrica e alla Ridondanza testuale. Solo l'Ambiguità residua diventa Domanda
  mirata.
- **Validazione elettrica** — la batteria di controlli deterministici sull'IR (connessione, nodo
  di riferimento, grado dei nodi, loop di generatori di tensione, tagli di generatori di
  corrente, segni, unità, serie E12/E24, esistenza delle grandezze richieste). Precede la
  risoluzione.
- **Ridondanza testuale** — i valori estratti dal testo dell'esercizio, tenuti come canale
  separato e usati per confermare o smentire le letture dal disegno.
- **Anteprima di ricostruzione** — la vista che mostra l'IR ricostruito accostato alla foto
  originale, con ogni componente ancorato alla propria area di provenienza. Mostrata **sempre**
  prima della risoluzione.
- **Domanda mirata** — una singola richiesta all'utente su una Ambiguità residua, con il
  ritaglio ingrandito e le alternative osservate. Massimo due giri per esercizio.
- **Percorso A** — risoluzione per analisi nodale modificata, simbolica.
- **Percorso B** — risoluzione per Piano didattico: catena di Trasformazioni.
- **Percorso C** — risoluzione per simulazione numerica esterna. Opzionale, v2.
- **Verifica** — i cinque controlli indipendenti sulla soluzione: residui KCL, residui KVL,
  bilancio di potenza, Accordo fra percorsi, sanità fisica. **Dalla v3 non è l'intera prova:** il
  round-trip visuale (FR-41) è un controllo pari grado, perché il disegno fa parte della prova
  (K-0).
- **Badge Verificata** — il marchio applicato a una Soluzione che ha superato tutti e cinque i
  controlli della Verifica **e il round-trip visuale**, con i residui numerici ispezionabili.
- **Rifiuto di certificazione** — l'esito in cui almeno un controllo della Verifica fallisce.
  Non è un errore di sistema: è un esito previsto, con la propria interfaccia e senza addebito.
- **Trasformazione** — un'operazione pura su IR che produce un nuovo IR più un artefatto di
  disegno (serie, parallelo, partitore, stella↔triangolo, Thévenin, Norton, Millman,
  sovrapposizione, nodale, maglie, impedenza fasoriale, condizioni iniziali, regime permanente,
  costante di tempo).
- **Catalogo trasformazioni** — l'insieme chiuso delle Trasformazioni disponibili. Chiuso
  significa che il sistema non ne inventa di nuove a runtime.
- **Piano didattico** — l'insieme ordinato di Trasformazioni scelto per arrivare alla grandezza
  richiesta. **Dalla v3 la struttura dati non è una lista ma un `ProofGraph`** (FR-40): il termine
  resta per continuità con i requisiti già scritti, la linearità no.
- **Profilo curricolare** — l'insieme di convenzioni di segno, notazione, Trasformazioni ammesse
  e formato d'uscita associato a un corso e a un ateneo. Restringe il Catalogo trasformazioni.
- **Soluzione consegnata** — una Soluzione che ha ottenuto il Badge Verificata ed è stata
  mostrata all'utente. È l'unità di consumo dei Crediti. **Non** è più l'unità della metrica
  nord: dalla v3 la metrica nord è VVDR (SM-3) e la sua unità è la derivazione visuale
  interamente certificata.
- **Credito** — l'unità prepagata consumata da una Soluzione consegnata. Un Rifiuto di
  certificazione non consuma Crediti.
- **Variante** — un esercizio generato da Studio a partire da un esercizio sorgente, con valori
  diversi e stessa struttura simbolica.
- **Foglio soluzione** — il documento separato che accompagna una Variante, con soluzione
  completa e checksum di verifica.
- **Marcatura di provenienza** — l'insieme di marchi leggibili dalla macchina e percepibili
  dall'utente applicati a ogni export, che dichiarano l'origine assistita da IA.
- **SER** — Silent Error Rate: quota di Soluzioni consegnate col Badge Verificata ma
  numericamente sbagliate.
- **VSR** — Verified Solve Rate: quota di esercizi che arrivano a Soluzione consegnata senza
  correzione umana dell'IR.
- **QPS** — Questions Per Solve: Domande mirate medie per Soluzione consegnata.
- **TTV** — Time To Verified: secondi dal caricamento alla Soluzione consegnata.

**Termini della v3 — il kernel.** Introdotti da §5.0; i workflow a valle li usano alla lettera
come i precedenti.

- **`CircuitIR`** — il grafo elettrico. Cosa il circuito *è*. Non contiene posizioni.
- **`LayoutIR`** — la disposizione sul piano. Dove ogni cosa *sta*. Persistente e distinto dal
  `CircuitIR`: sono due rappresentazioni, non due viste della stessa (FR-37).
- **`LayoutPatch`** — la sola operazione ammessa sul `LayoutIR`, con i campi `preserve`, `remove`,
  `create`, `node_mapping`, `reroute_scope`. Valgono `id_{k+1}(x) = id_k(x)` esatto e
  `p_{k+1}(x) ≈ p_k(x)` entro tolleranza owner-locked, per ogni `x ∈ preserve` (FR-38).
- **`ProofGraph`** — la derivazione come grafo con diramazioni e ricongiungimenti, non come lista
  (FR-40).
- **Passo** — l'unità della derivazione, con i sei campi obbligatori `BEFORE · ACTION · AFTER ·
  EQUATION · CERTIFICATE · PROVENANCE` (FR-39).
- **Round-trip visuale** — SVG semantico → riparsa → `ReconstructedCircuitIR` →
  canonicalizzazione → confronto esatto di grafi. È il controllo primario della topologia e non
  coinvolge alcun VLM (FR-41).
- **`Claim`** — il tipo su cui opera il gate di veridicità proprietario (FR-42).
- **Metriche v3** — VVDR, NED, TVR, VCER, SEC, RRC, VDR: definizioni in §8, **con i significati
  del piano master §27**. Le soglie sono owner-locked.

---

## 5. Features

> **Ordine di lettura, v3.** §5.0 è il kernel ed è il grosso dell'MVP, ma **non coincide con
> l'MVP**: la tabella di §7.1 è la sola lista autorevole di cosa sta dentro, e vi compaiono anche
> FR-1 ristretto ai formati strutturati, FR-4, FR-11, FR-12, FR-13, FR-18, FR-19, FR-34, FR-35 e
> FR-46, che vivono in altre sottosezioni. **FR-9, l'editor, non c'è più**: uscito da Gate A il
> 15 agosto. Il resto resta valido come requisito di prodotto
> ma è allocato ai gate successivi: §5.1 percezione → Gate C, Studio → Gate E/F, tutor e lavagna
> → Gate B. **Un FR assente da §7.1 è fuori MVP**, comunque sia scritto qui.
> `[NOTE FOR PM]` Le UJ-1…UJ-7 raccontano sessioni **con la foto**. Vanno rimappate sul kernel a
> ingresso strutturato nel passo 4 della catena (`bmad-ux`): non le riscrivo qui perché le UJ si
> catturano dall'utente, non si autorizzano da un PRD.

### 5.0 Visual Proof Kernel

**Description.** Dato un `CircuitIR` valido, il kernel produce una derivazione come sequenza di
stati visuali certificati: a ogni passo applica una trasformazione del Catalogo, emette un
`LayoutPatch` che **conserva** ciò che non è cambiato, ridisegna, e dimostra che il circuito
ridisegnato è lo stesso grafo meno la trasformazione dichiarata. È il blocco che realizza K-0 e
l'unico oggetto del kill criterion di Gate A.

**Functional Requirements:**

#### FR-37: Rappresentazione doppia e persistente
Il sistema mantiene `CircuitIR` — la verità elettrica — e `LayoutIR` — la verità visuale — come
strutture **distinte e entrambe persistenti**.

**Consequences (testable):**
- Il renderer **non** re-inferisce il circuito dal layout: una modifica al solo `LayoutIR` non
  cambia alcun risultato elettrico, e un test lo verifica su un caso in cui il layout è alterato
  a mano.
- Il sistema **non** ricalcola il layout globale a ogni passo: dopo una trasformazione locale, il
  numero di elementi con coordinate cambiate è limitato allo `reroute_scope` dichiarato.
- `CircuitIR` e `LayoutIR` sono serializzabili e ricaricabili senza perdita: round-trip
  serializza → deserializza → confronto esatto.

#### FR-38: La trasformazione è un `LayoutPatch` con invariante di conservazione
Ogni trasformazione emette un `LayoutPatch` con i campi `preserve`, `remove`, `create`,
`node_mapping`, `reroute_scope`. **Il patch non è composto dal renderer: deriva dal `Transform`**,
che espone `preserve_entities`, `remove_entities`, `create_entities`, `preserve_nodes`,
`node_mapping`, `changed_edges`, `boundary`. In forma compatta:
**`Transform ⇒ PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate`.**

**Consequences (testable):**
- **`id_{k+1}(x) = id_k(x)` per ogni `x ∈ preserve`, senza eccezioni.** L'identità non ha
  tolleranza: un elemento conservato che cambia identificatore è un difetto, sempre.
- **`p_{k+1}(x) ≈ p_k(x)` e `θ_{k+1}(x) = θ_k(x)`, salvo necessità geometriche dimostrabili.**
  Ogni scostamento è **misurato e penalizzato da SM-14 (VCER)**, mai assolto come libertà del
  renderer. Un renderer che sposta per comodità paga; uno che sposta per evitare una collisione
  paga meno, ma paga.
  > **Correzione del 15 agosto.** Qui c'era `p_{k+1}(x) = p_k(x)`, uguaglianza esatta. Era troppo
  > forte: responsive, zoom, viewport, anti-aliasing ed evitamento di collisioni producono
  > differenze minime e legittime, e un invariante che il rendering reale viola sempre smette di
  > essere un gate. L'invariante corretto è **semantico-spaziale**, non pixel-perfect.
- Ordine relativo, appartenenza ai nodi e ruolo circuitale degli elementi preservati sono
  invariati. Sono le proprietà che l'utente usa per ritrovarsi, e non ammettono scostamento.
- **Il renderer non decide cosa «sembra invariato».** `preserve` gli arriva calcolato (FR-47); non
  ha una funzione per proporne uno proprio.
- Un `LayoutPatch` che dichiara in `preserve` un elemento assente in `p_k` è rifiutato in
  validazione, non ignorato.
- `node_mapping` è totale sui nodi sopravvissuti: nessun nodo del circuito risultante è privo di
  origine dichiarata.

**Notes:** Realizza **A-0** (§7.0.1). Se A-0 cade a Gate A, cade la giustificazione di questo
requisito ma **non il requisito**: i campi del `Transform` restano necessari per calcolare
qualunque delta, marcato o no.

#### FR-39: Grammatica obbligatoria del passo
Ogni passo della derivazione porta, come **schema dati**, i sei campi
`BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE · PROVENANCE`.

**Consequences (testable):**
- Un passo privo di uno dei sei campi non è pubblicabile: il gate lo rifiuta.
- Un passo il cui `BEFORE` non coincide con l'`AFTER` del passo precedente è rifiutato (continuità
  della catena).
- `CERTIFICATE` referenzia `verifier_id` e versione, coerentemente col tipo `Claim` di K-2.
- La grammatica è **indipendente dalla presentazione**: un cambio di tema o di renderer non altera
  nessuno dei sei campi.

#### FR-40: La derivazione è un `ProofGraph`, non una lista
Il sistema rappresenta la derivazione come grafo diretto aciclico con branch e join.

**Consequences (testable):**
- Sovrapposizione, Thévenin su sottoproblemi e transitori sono rappresentabili **senza** cambiare
  lo schema — verificato con un caso di test che apre due branch e li richiude.
- Ogni nodo del `ProofGraph` è uno stato visuale certificato; un nodo senza disegno è un errore di
  schema, non uno stile (K-0).
- `[ASSUMPTION: l'MVP con tre trasformazioni produce grafi quasi lineari. Il ProofGraph entra
  comunque adesso perché cambiarlo dopo è una migrazione di dati, non un refactor.]`

#### FR-41: Il round-trip visuale è il controllo primario della topologia
Il sistema esporta SVG **semantico** con `data-component-id` e `data-terminal-*`, lo riparsa in un
`ReconstructedCircuitIR`, lo canonicalizza, e lo confronta **esattamente** col `CircuitIR` atteso.

**Consequences (testable):**
- Il confronto è di grafi, non di pixel e non di stringhe.
- **Nessun VLM partecipa alla certificazione della topologia.** La QA percettiva esiste, è
  separata, e non concede `Verified` (K-1).
- Un disegno che non supera il round-trip **non viene pubblicato**: produce Rifiuto tipizzato, non
  un avviso.
- Il fallimento alimenta SM-16 (RRC) — la correttezza del round-trip di rendering. La validità
  della Trasformazione che ha prodotto quel disegno è misurata a parte, da SM-13 (TVR).

#### FR-42: Il gate di veridicità è componente proprietaria, non skill esterna
Il gate che decide `Verified` è codice versionato del prodotto, con il tipo `Claim`
(`claim_type`, `state_id`, `subject_ids`, `evidence_ids`, `verifier_id` + versione, `status`).

**Consequences (testable):**
- Nessun elemento della trusted computing base dipende dalla presenza di una skill esterna: un
  ambiente senza skill installate produce gli stessi verdetti.
- Ogni `Claim` pubblicato ha `evidence_ids` non vuoto e un `verifier_id` risolvibile a una versione.
- La versione del verificatore compare nella prova ispezionabile (K-4).
- Origine: piano master §19, addendum §H.1 — supera l'uso del Truthfulness Enforcer come skill.

#### FR-43: Catalogo chiuso, e la sua condizione di apertura
L'MVP supporta **esattamente tre** trasformazioni: serie, parallelo, partitore di tensione.

**Consequences (testable):**
- Una trasformazione non nel Catalogo non è applicabile: il sistema rifiuta invece di improvvisare.
- Il numero di trasformazioni supportate è misurato da SM-C5 e **resta a tre** finché il kill
  criterion di Gate A non è superato.
- L'espansione del Catalogo richiede la decisione registrata che il kill criterion è passato — non
  è una scelta di implementazione. **La registrazione contiene almeno:** la misura di VCER e SM-18
  sui due bracci del confronto, il corpus su cui è stata presa, chi ha deciso e la data. Una
  registrazione priva di uno di questi campi non apre il Catalogo.

#### FR-44: `StudentTrace` è ingresso semantico, non immagine
Quando il sistema controlla una derivazione **prodotta dallo studente**, la riceve come struttura
semantica — passi, equazioni, grandezze dichiarate — e non come fotografia del quaderno.

**Consequences (testable):**
- Il verifier non accetta un'immagine come `StudentTrace`: l'eventuale conversione avviene prima ed
  è un altro stadio, con il proprio esito di fallimento.
- Un `StudentTrace` è confrontabile col `ProofGraph` di riferimento passo per passo, non solo sul
  risultato finale.
- **Fuori dall'MVP di Gate A, richiesto dalla prima release rivolta allo studente.** Il Visual
  Proof Kernel si prova senza: Visual Slice 0 non ha bisogno di un procedimento da correggere. Ma
  la prima cosa che CircuitCheck pubblica **è** la correzione del procedimento, e senza questo
  requisito sarebbe un risolutore visuale — non il prodotto.
  *Provenienza:* fino al 24 agosto 2026 questa riga diceva «Fuori MVP — Gate B (tutor
  interattivo)». La riprioritizzazione è del 24 agosto ed è registrata in
  `sprint-change-proposal-2026-08-24.md`; il tutor interattivo e la lavagna restano a Gate B.
  Scritto qui perché l'addendum §H.4 lo impone come vincolo del verifier, e il verifier si
  costruisce adesso: accettare immagini dopo costerebbe una riscrittura del confine.

**Notes:** Origine: addendum §H.4, piano master §7.2.

#### FR-45: Un kernel, tre adapter — nessun fork
Il kernel è autonomo e non conosce la superficie che lo chiama. Le superfici sono tre: Web/API,
MCP e MCP Apps, Ardesia.

**Consequences (testable):**
- Nessun modulo del kernel importa codice specifico di una superficie; la dipendenza va in una
  direzione sola e un test di architettura fallisce se si inverte.
- Dentro Ardesia il plugin consuma ToolHost, Simulation Plugin e LessonOS **senza duplicare**
  auth, shell, dashboard, memoria o simulatore.
- **Non esiste un ramo «Kirchhoff per Ardesia».** Una funzionalità che esiste in una superficie
  sola sta nell'adapter, mai nel kernel.

**Notes:** Origine: addendum §H.4, piano master §23. Era un vincolo v3 senza requisito: citato una
volta in §1 e assente da §14 e §15. Un fork non si scopre alla fine, si previene con un test.

#### FR-47: I quattro bracci di Gate A, dallo stesso passaggio
Il sistema produce, per **lo stesso identico passaggio**, quattro rendering: **0** baseline globale
equa — stesso renderer, stessi vincoli estetici, stesso `CircuitIR(Cₖ₊₁)`, **senza accesso a**
`Layout(Cₖ)`; **A** layout persistente con segnale solo sul delta; **B** come A più codifica
leggera «unchanged» sui preservati; **C** come A più attenuazione del resto.

**Consequences aggiuntive (testable):**
- **B e C sono varianti di rendering dello stesso `LayoutIR`**, non pipeline separate: si ottengono
  cambiando la codifica visiva, mai il layout. Se B o C richiedessero un `LayoutIR` diverso, il
  confronto misurerebbe due cose insieme.
- I bracci sono **selezionabili a runtime** e l'assegnazione è controbilanciata fra partecipanti,
  registrata per sessione.
- Il braccio 0 e il braccio A sono deliverable dell'MVP; B e C sono modalità di rendering.
- **Il braccio A non usa attenuazione del resto, marcatori sugli invarianti, né evidenziazioni di
  regione estese.** Un grande fondo colorato dietro il sottografo è una **versione morbida di C**:
  trasforma visivamente un'area larga dello schema, e contaminerebbe proprio il confronto A↔C.
  L'enfasi del braccio A è **locale al delta** — i componenti che cambiano, più l'eventuale overlay
  di boundary (FR-53). Se si vuole misurare l'effetto della regione evidenziata, diventa una
  variabile sperimentale dichiarata, non un dettaglio di stile.

**Consequences (testable):**
- Il braccio B non riceve `Layout(Cₖ)` in nessuna forma: un test lo verifica sulla firma della
  funzione, non sulla buona fede del chiamante.
- I due bracci condividono renderer e vincoli. Una differenza di qualità estetica fra i bracci è un
  difetto dell'esperimento, non un risultato.
- **Il `preserve set` è calcolato dal sistema, non dichiarato dal produttore del patch:**
  `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` dopo `node_mapping` / `entity_mapping`. Un `LayoutPatch` che
  dichiara `preserve` più piccolo di `Pₖ` è **non conforme**, non efficiente.
- Su ogni elemento di `Pₖ` si misurano spostamento normalizzato, cambio di orientamento, inversione
  dell'ordine relativo e rerouting non richiesto, per entrambi i bracci.

**Notes:** Senza questo requisito il kill criterion di §7.0.1 confronta una cosa con niente. È la
ragione per cui la baseline è un deliverable dell'MVP e non un lavoro successivo.

#### FR-48: `ProofSession` è indipendente dalla superficie
Il kernel produce una **`ProofSession`** — `CircuitIR` + `LayoutIR` + `ProofGraph` +
`ProofCertificates` + capacità di interazione — che nessuna superficie possiede.

**Consequences (testable):**
- La `ProofSession` è serializzabile e ricostruibile senza il codice di alcuna superficie.
- **Almeno due adapter la presentano**: la PWA a schermo intero, e una superficie MCP compatta
  (`ProofReplay`) con prima/dopo, selezione dell'elemento, certificato e navigazione nel
  `ProofGraph`. Ardesia monta la stessa `ProofSession` in seguito, senza duplicare il kernel
  (FR-45).
- **La `ProofSession` funziona senza MCP Apps.** L'estensione aumenta il prodotto e non è l'unico
  modo di farlo funzionare: il supporto varia fra host, e OpenAI Apps SDK e MCP Apps non sono oggi
  la stessa runtime. Un degrado a superficie non interattiva è un percorso previsto, non un guasto.
- Dentro un host conversazionale la conversazione resta il contesto linguistico e **Kirchhoff resta
  l'autorità sul circuito**: nessun valore o topologia proviene dal turno di chat (FR-13).

**Notes:** Origine: sessione owner del 15 agosto. Riferimenti forniti dall'owner: specifica MCP
`2026-07-28` (core stateless + estensioni, fra cui MCP Apps; UI distribuita dal server e resa dal
client in iframe sandboxed, azioni che rientrano nel protocollo) e OpenAI Apps SDK.
`[ASSUMPTION: i due riferimenti sono stati forniti dall'owner e non verificati in prima persona.
Vanno confermati prima che una data o una garanzia di runtime diventi un impegno di progetto.]`

#### FR-49: Ispezione del passaggio, ancorata allo stato
A ogni passo lo studente può interrogare la derivazione senza uscire dal circuito.

**Consequences (testable):**
- Un controllo **Prima ↔ Dopo** commuta fra `Cₖ` e `Cₖ₊₁` conservando la posizione dell'occhio.
- Selezionando un elemento derivato — per esempio `R34` — il sistema mostra **da quali elementi
  deriva**; selezionando un nodo, ne mostra la continuità attraverso il passo.
- Alla domanda «perché posso farlo?» il sistema risponde con **terminali, precondizioni, formula e
  certificato** della trasformazione. **Non genera una spiegazione libera scollegata dallo stato:**
  ogni elemento della risposta è un campo del passo (FR-39), non prosa prodotta al momento.
- L'evidenziazione precede la spiegazione: la parte interessata è marcata **nel circuito** prima che
  compaia qualunque testo.

**Notes:** Origine: journey primaria dell'owner, 15 agosto, punti 3-7.

#### FR-50: Quattro classi di stato visivo, e una sola è vincolata
Il sistema tiene distinti **stato semantico di trasformazione**, **stato di interazione**, **stato
di accessibilità** e **stato di ispezione/debug**. Sono canali separati, non livelli di uno stesso
canale.

**Consequences (testable):**
- **Solo lo stato semantico di trasformazione è vincolato da A-0**: non può usare gli elementi
  preservati come supporto grafico. Le altre tre classi possono cambiare l'aspetto di qualunque
  elemento, incluso un invariante.
- Selezione, hover, focus, ispezione del certificato, alto contrasto, modalità diagnostica e la
  richiesta esplicita *«mostrami cosa è rimasto uguale»* sono **stati dell'interfaccia**, non
  codifica della trasformazione. Nessuno di essi viola A-0.
- Pan e zoom dell'intera viewport non appartengono a nessuna delle quattro: trasformano la vista,
  non il circuito.
- Le classi sono **componibili senza ambiguità**: un elemento selezionato dentro un sottografo in
  trasformazione mostra entrambi i trattamenti, e un test verifica che nessuno dei due cancelli
  l'altro.

**Notes:** Origine: correzione owner del 15 agosto. Senza questa separazione, A-0 sarebbe
inapplicabile — vieterebbe anche l'hover su una resistenza conservata, che è assurdo.

#### FR-53: `TransformOverlay` è un layer separato, e non occlude mai un'entità preservata
Il boundary e l'enfasi della trasformazione vivono in un **`TransformOverlay`** distinto dal
`LayoutIR`. L'overlay è ancorato geometricamente alle entità, **non le modifica**.

**Consequences (testable):**
- **`CircuitIR ≠ LayoutIR ≠ TransformOverlay ≠ InteractionState`**: quattro tipi, quattro cicli di
  vita. Un test di architettura fallisce se uno scrive nell'altro.
- **Rimuovendo l'overlay, il rendering delle entità sottostanti è identico byte per byte a quello
  senza trasformazione in corso.** È il test che distingue `style = blue` da `style = unchanged +
  overlay`, ed è automatizzabile.
- **R-Visual-1 — un'annotazione di trasformazione non occlude mai un'entità semantica preservata.**
  L'ordine dei layer è deterministico e verificato:

  | # | Layer |
  |---|---|
  | 0 | canvas / sfondo |
  | 1 | sfondo della regione di trasformazione |
  | 2 | fili |
  | 3 | componenti |
  | 4 | **nodi ed etichette semantiche** |
  | 5 | enfasi sulle entità cambiate |
  | 6 | annotazioni di boundary |
  | 7 | stato di interazione |
  | 8 | ispezione / debug |

- Il test di R-Visual-1 è **permanente**, non una verifica una tantum: rientra fra le famiglie
  obbligatorie di FR-46, dove ogni fallimento sfuggito diventa invariante.
- `Transform` espone, oltre ai campi di FR-38, il proprio **`boundary`**: le entità attraverso cui
  l'equivalenza è affermata. Un boundary vuoto è rifiutato — un'equivalenza senza terminali non è
  un'affermazione verificabile.

**Notes:** Origine: correzione owner del 15 agosto, nata da un difetto vero. **Il primo mock di A-0
dipingeva l'alone del sottografo sopra le etichette dei nodi `A` e `B`** — cioè cancellava
visivamente i due elementi preservati più importanti del passo. L'owner ha chiesto di trasformare
quel bug in invariante del renderer invece che in aneddoto: è esattamente il meccanismo
*fallimento sfuggito → invariante permanente* che il loop deve accumulare.

#### FR-52: Il confine del kernel è `CircuitIR`, e la percezione sta fuori
Nessun percorso di percezione produce direttamente un `CircuitIR` fidato. Produce un
**`PerceptionCandidate<CircuitIR>`** con `confidence`, `ambiguities[]`, `evidence_refs[]`,
`source_provenance`.

**Consequences (testable):**
- Un `PerceptionCandidate` diventa `CircuitIR` fidato **solo** dopo conferma e Validazione
  elettrica. La conversione è un passaggio esplicito con un proprio esito di fallimento, non un
  cast.
- **Il kernel non importa nulla dalla pipeline di percezione**: la dipendenza va in una direzione
  sola e un test di architettura fallisce se si inverte (coerente con FR-45).
- L'esperimento di §7.0.1 riceve `CircuitIR` **fidati**, mai candidati. Un circuito letto male
  confonderebbe il partecipante per ragioni che non riguardano la continuità del disegno, e il
  verdetto smetterebbe di essere interpretabile.
- `source_provenance` di ogni candidato punta a un `SourceAsset` registrato (FR-51). Un candidato
  senza provenienza registrata non entra nel corpus.

**Notes:** Origine: decisione owner del 15 agosto. È il confine che permette al percorso foto di
avanzare **in parallelo** a Gate A senza contaminarlo. Ha effetto sulla Spine adesso, anche se la
UX della foto resta a Gate C.

### 5.1 Ingestione e ricostruzione del circuito

**Description.** L'utente fornisce un esercizio come foto, come LaTeX, o costruendolo
nell'editor. Il sistema normalizza l'immagine, esegue K Pass di estrazione deliberatamente
diversi fra loro, canonicalizza ogni risultato in IR, e misura l'Accordo. Estrae in parallelo la
Ridondanza testuale. Passa l'IR consensuale alla Validazione elettrica, il cui esito o promuove
l'IR o produce una diagnosi localizzata. Realizza UJ-1, UJ-5.

**Functional Requirements:**

#### FR-1: Ingestione multi-formato
Un utente può fornire un esercizio come immagine (foto o scansione), come sorgente LaTeX, o come
netlist. Realizza UJ-1, UJ-5.

**Consequences (testable):**
- Il sistema accetta JPEG, PNG, HEIC e PDF a pagina singola fino a 20 MB.
- Un'immagine che contiene più di un esercizio produce una richiesta di selezione prima di
  qualunque estrazione; il sistema non ne sceglie uno d'ufficio e non fonde due circuiti.
- Un input non interpretabile come esercizio produce un messaggio che dice cosa manca, non un
  fallimento generico.

#### FR-2: Estrazione multi-pass con misura dell'Accordo
Il sistema esegue almeno tre Pass di estrazione indipendenti e produce un Accordo per componente
e complessivo. Realizza UJ-1, UJ-2.

**Consequences (testable):**
- I Pass differiscono per almeno due assi fra: modello impiegato, preprocessing dell'immagine,
  inquadratura del prompt.
- L'Accordo è calcolato confrontando gli IR canonicalizzati, mai leggendo un campo di confidence
  emesso da un modello.
- Ogni componente dell'IR porta la propria area di provenienza sull'immagine sorgente.
- Un valore non leggibile è emesso come assente con le alternative osservate, mai come valore
  plausibile inventato.

**Out of Scope:**
- Riconoscimento di componenti non lineari (§6).

#### FR-3: Ridondanza testuale come secondo canale
Il sistema estrae i valori presenti nel testo dell'esercizio separatamente da quelli letti nel
disegno, e li usa per confermare o smentire.

**Consequences (testable):**
- I valori testuali sono conservati in un campo distinto e non fusi con le letture dal disegno.
- Una lettura dal disegno con Accordo basso, confermata dal testo, non genera Domanda mirata.
- Un disaccordo fra testo e disegno genera sempre una Domanda mirata, qualunque sia l'Accordo.

#### FR-4: Validazione elettrica come gate
Il sistema esegue la Validazione elettrica su ogni IR candidato prima di consentire la
risoluzione, e in caso di fallimento produce una diagnosi che localizza il problema.

**Consequences (testable):**
- Nessun IR raggiunge lo stato `confermato` senza aver superato la Validazione elettrica.
- Un fallimento nomina l'elemento coinvolto (nodo, ramo, componente), non solo la regola violata.
- La diagnosi è utilizzabile come testo di una Domanda mirata senza riscrittura manuale.

#### FR-5: Anteprima di ricostruzione, sempre
Il sistema mostra l'Anteprima di ricostruzione prima di ogni risoluzione, anche quando non
esiste Ambiguità residua, e richiede una conferma esplicita. Realizza UJ-1, UJ-7.

**Consequences (testable):**
- Nessuna Soluzione è calcolata prima della conferma dell'utente sull'Anteprima.
- Ogni componente dell'Anteprima è visivamente ancorato alla propria area di provenienza
  sull'immagine sorgente.
- La conferma è una singola azione quando non ci sono correzioni da fare.
- L'Anteprima è utilizzabile da tastiera e con screen reader.

**Feature-specific NFRs:**
- L'Anteprima compare entro 5 secondi dal caricamento per un'immagine fino a 5 MP.

### 5.2 Disambiguazione guidata

**Description.** Ciò che sopravvive ad Accordo, Validazione elettrica e Ridondanza testuale
diventa Ambiguità residua, e solo allora l'utente viene disturbato — con il ritaglio ingrandito e
le alternative realmente osservate. Il flusso è a più giri: il sistema sospende, l'utente
risponde, il sistema riprende dallo stesso punto. Realizza UJ-2, UJ-7.

**Functional Requirements:**

#### FR-6: Domanda mirata su Ambiguità residua
Il sistema pone una Domanda mirata per ciascuna Ambiguità residua, mostrando il ritaglio
ingrandito e le alternative osservate. Realizza UJ-2.

**Consequences (testable):**
- Ogni Domanda mirata mostra la porzione di immagine da cui nasce l'ambiguità.
- Le alternative offerte sono quelle osservate nei Pass, più sempre un'opzione di inserimento
  libero.
- Nessuna Domanda mirata è posta per un elemento che ha superato Accordo, Validazione elettrica e
  Ridondanza testuale.

#### FR-7: Tetto di due giri e degrado all'editor
Il sistema pone al massimo due giri di Domande mirate per esercizio; oltre, apre l'editor del
circuito. Realizza UJ-2.

**Consequences (testable):**
- Un terzo giro non è mai posto: al suo posto compare l'editor con l'IR corrente precaricato.
- Il degrado all'editor preserva tutte le risposte già date.

#### FR-8: Ripresa senza perdita e senza doppio addebito
Il sistema riprende l'elaborazione dal punto di sospensione, e la stessa ripresa non consuma
Crediti più di una volta. Realizza UJ-2, UJ-7.

**Consequences (testable):**
- Una ripresa ripetuta con lo stesso riferimento di sospensione produce lo stesso risultato e un
  solo addebito.
- Un riferimento di sospensione scaduto produce un messaggio che offre di ripartire, non un
  errore opaco.
- Un riferimento di sospensione non può essere usato per accedere all'esercizio di un altro
  utente.

#### FR-9: Editor del circuito
Un utente può modificare direttamente nodi, componenti, valori, polarità e grandezze richieste di
un IR. Realizza UJ-2, UJ-6.

**Consequences (testable):**
- Ogni modifica manuale è registrata nell'IR come tale, distinta da una lettura automatica.
- La Validazione elettrica gira di nuovo dopo ogni modifica e segnala l'esito prima che l'utente
  possa risolvere.

### 5.3 Risoluzione e Verifica

**Description.** Il gate che rende onesto tutto il resto. Ogni esercizio è risolto per almeno due
percorsi indipendenti, e la soluzione supera cinque controlli prima di essere mostrata. L'esito
negativo è un esito di prima classe, con la propria interfaccia. Realizza UJ-1, UJ-3.

> **Correzione v3.** Fino alla v2 questa sezione si apriva con «il cuore del prodotto e la sola
> ragione per pagarlo». Non lo è più: §1 ha ritirato quella proposta di valore. La verifica resta
> il gate non negoziabile di K-1 — nessuna certificazione senza — ma **ciò che si vende è la
> derivazione disegnata**, e la verifica è la condizione perché sia credibile, non il prodotto.

**Functional Requirements:**

#### FR-10: Risoluzione a percorsi indipendenti
Il sistema risolve ogni esercizio confermato tramite Percorso A e Percorso B, e ne confronta i
risultati. Realizza UJ-1.

**Consequences (testable):**
- Entrambi i percorsi producono un risultato, o la soluzione non è pubblicabile.
- Il confronto avviene su tutte le grandezze richieste, non solo sulla prima.
- Una discordanza fra percorsi impedisce la pubblicazione ed è registrata come evento diagnostico
  interno con l'IR allegato.

#### FR-11: Verifica a cinque controlli come gate di pubblicazione
Il sistema applica la Verifica a ogni soluzione e pubblica solo ciò che la supera interamente.
Realizza UJ-1, UJ-3.

**Consequences (testable):**
- I cinque controlli sono calcolati sostituendo la soluzione ottenuta, non ri-derivandola.
- Il Badge Verificata è applicato **se e solo se tutti e cinque passano _e_ il round-trip visuale
  di FR-41 è superato.** I cinque controlli sono necessari e non sufficienti: dalla v3 il disegno
  fa parte della prova (K-0), quindi la condizione del Badge lo include invece di delegarlo a un
  altro requisito che blocca la pubblicazione più a valle.
- I residui numerici di ciascun controllo sono ispezionabili dall'utente.
- Nessun percorso di codice consente di mostrare una soluzione priva di Badge Verificata come se
  lo avesse.

#### FR-12: Rifiuto di certificazione come esito progettato
Quando la Verifica fallisce, il sistema comunica il fallimento e la sua localizzazione, non mostra
il risultato, e non addebita Crediti. Realizza UJ-3.

**Consequences (testable):**
- Il messaggio nomina il controllo fallito e l'elemento coinvolto.
- Nessun Credito è consumato.
- L'utente può aprire l'editor, segnalare il caso, o scaricare la ricostruzione.
- L'evento è registrato con l'IR per l'analisi di qualità.

**Notes:** `[NOTE FOR PM]` Il tasso di Rifiuto è una metrica di salute, non un difetto da
azzerare. Esiste un livello oltre il quale il prodotto è percepito come inaffidabile a
prescindere dalla correttezza, ma **quel livello è soglia di lancio e quindi owner-locked**
(§16 Q0): questo PRD non lo fissa. Vedi SM-C1.

#### FR-13: Nessun valore generato da modello linguistico
Ogni valore numerico mostrato all'utente proviene da un motore di calcolo deterministico.

**Consequences (testable):**
- Nessun numero presentato all'utente ha come unica origine un'uscita di modello linguistico.
- I testi generati che contengono numeri li riprendono dal risultato calcolato, e la coerenza fra
  i due è verificata prima della pubblicazione.

### 5.4 Spiegazione didattica e rendering

**Description.** Il numero è commodity; la catena di Trasformazioni con i disegni intermedi è il
prodotto. Il Piano didattico è proposto entro un Catalogo chiuso, eseguito deterministicamente, e
verificato. Il Profilo curricolare restringe cosa è ammesso. Realizza UJ-1, UJ-4, UJ-6.

**Functional Requirements:**

#### FR-14: Piano didattico da Catalogo chiuso
Il sistema produce un Piano didattico scegliendo solo Trasformazioni del Catalogo, lo esegue
deterministicamente, e verifica che porti alla grandezza richiesta. Realizza UJ-1, UJ-4.

**Consequences (testable):**
- Una Trasformazione fuori Catalogo non è eseguibile.
- Un Piano che non converge o non è applicabile fa ripiegare il sistema sul piano canonico
  nodale, senza intervento manuale.
- Il risultato ottenuto per Piano didattico coincide con quello del Percorso A entro tolleranza,
  o la soluzione non è pubblicabile.

#### FR-15: Disegno del circuito a ogni passo
Ogni passo del Piano didattico produce il disegno del circuito nel suo stato dopo la
Trasformazione. Realizza UJ-1, UJ-4.

**Consequences (testable):**
- Ogni passo mostrato ha un disegno associato.
- A 360 px di larghezza di viewport il disegno resta interamente visibile senza scorrimento
  orizzontale della pagina, e le etichette dei componenti restano leggibili a non meno di 11 px
  effettivi.
- Ogni disegno ha un'alternativa testuale che descrive la topologia risultante.

#### FR-16: Profilo curricolare
Un utente o un tenant può associare un esercizio a un Profilo curricolare che restringe le
Trasformazioni ammesse e fissa convenzioni e notazione. Realizza UJ-4, UJ-6.

**Consequences (testable):**
- Una Trasformazione esclusa dal Profilo non compare in nessun Piano didattico prodotto sotto
  quel Profilo.
- Le convenzioni di segno del Profilo sono applicate coerentemente a soluzione, disegni e testo.
- In assenza di Profilo il sistema usa un profilo predefinito dichiarato, non un comportamento
  implicito.

#### FR-17: Modalità Studio a rivelazione progressiva
Un utente può percorrere la soluzione un passo alla volta, con una domanda di comprensione prima
di ogni rivelazione. Realizza UJ-4.

**Consequences (testable):**
- Il passo successivo non è visibile prima che l'utente abbia risposto o esplicitamente saltato.
- Una risposta errata produce una spiegazione del perché prima di rivelare il passo.
- Nessuna risposta dell'utente in modalità Studio è registrata come punteggio, voto o misura di
  rendimento attribuita a una persona (§6).

### 5.5 Export e provenienza

**Description.** Ogni artefatto che lascia il prodotto porta la Marcatura di provenienza. È un
obbligo normativo, ed è anche il meccanismo che rende visibile l'uso disonesto e quindi
difendibile il prodotto davanti ai docenti. Realizza UJ-1, UJ-5, UJ-6.

**Functional Requirements:**

#### FR-18: Export multiformato
Un utente può esportare una Soluzione consegnata o una Variante in PDF, LaTeX, SVG e — per
Studio — nei formati di importazione delle piattaforme di e-learning. Realizza UJ-1, UJ-5.

**Consequences (testable):**
- Il LaTeX prodotto compila senza intervento manuale nell'ambiente di riferimento documentato.
- Il PDF conserva i disegni come grafica vettoriale.
- Un export fallito dichiara la causa e non produce un file parziale.

#### FR-19: Marcatura di provenienza su ogni artefatto
Ogni artefatto esportato porta una marcatura leggibile dalla macchina e una percepibile
dall'utente. Realizza UJ-6.

**Consequences (testable):**
- Ogni export contiene metadati che dichiarano l'origine assistita da IA, la versione del
  sistema, il momento di generazione e un riferimento verificabile all'IR.
- Ogni export contiene un elemento visibile che dichiara la stessa cosa in linguaggio naturale.
- La marcatura sopravvive alle operazioni ordinarie sul formato (copia, stampa su PDF).
- Nessun percorso del prodotto produce un artefatto esportabile privo di marcatura.

### 5.6 Superficie assistente

**Description.** Kirchhoff è raggiungibile dall'interno degli assistenti che l'utente già usa, con
il pannello di conferma reso in conversazione. È un canale di acquisizione, non il sistema di
record: l'account Kirchhoff resta l'anagrafica. Realizza UJ-7.

**Functional Requirements:**

#### FR-20: Superficie assistente con conferma in conversazione
Un utente può eseguire il flusso completo — ingestione, conferma dell'Anteprima, risposta alle
Domande mirate, Soluzione consegnata — dall'interno di un assistente compatibile. Realizza UJ-7.

**Consequences (testable):**
- L'Anteprima di ricostruzione e le Domande mirate sono utilizzabili nel pannello in
  conversazione.
- Ogni risposta di tool con UI porta **due campi distinti**: una rappresentazione testuale per il
  contesto del modello e per gli host senza UI, e i dati strutturati per il rendering. Il primo è
  obbligatorio anche quando la UI è disponibile — senza, l'assistente non vede cosa l'utente ha
  confermato.
- Il flusso funziona senza che il pannello possa conservare stato locale fra un giro e l'altro.
- Le stesse regole di FR-5, FR-7, FR-11 e FR-12 valgono identiche su questa superficie.

#### FR-21: Collegamento dell'account dalla superficie assistente
Un utente che arriva da un assistente può collegare un account Kirchhoff e conservare cronologia e
Crediti. Realizza UJ-7.

**Consequences (testable):**
- Il collegamento è proposto dopo la prima Soluzione consegnata, non prima.
- Un utente non collegato opera entro una quota di prova legata alla sessione.
- Dopo il collegamento la cronologia prodotta nella sessione resta accessibile.

### 5.7 Studio — generazione di Varianti

**Description.** Il prodotto B2B, e il generatore del corpus pubblico. Riusa la soluzione
simbolica dell'esercizio sorgente per produrre Varianti nuove nei valori e identiche nella
struttura. Realizza UJ-5, UJ-6.

**Functional Requirements:**

#### FR-22: Generazione di Varianti verificate
Un utente Studio può generare N Varianti da un esercizio sorgente, ognuna con soluzione completa e
Badge Verificata. Realizza UJ-5.

**Consequences (testable):**
- Ogni Variante consegnata ha superato la Verifica, esattamente come una Soluzione consegnata.
- Una Variante che non supera la Verifica non è consegnata e non è conteggiata verso N; l'utente è
  informato di quante ne sono state scartate.
- Le Varianti generate dallo stesso sorgente differiscono nei valori e coincidono nella struttura
  simbolica.

#### FR-23: Vincoli di generazione
Un utente Studio può vincolare la generazione: serie di valori ammessa, intervalli, e proprietà
del risultato. Realizza UJ-5.

**Consequences (testable):**
- Una Variante che viola un vincolo dichiarato non è consegnata.
- Un insieme di vincoli insoddisfacibile è segnalato come tale, invece di produrre meno Varianti
  in silenzio.

#### FR-24: Fogli soluzione separati e verificabili
Ogni Variante è accompagnata da un Foglio soluzione separato con un checksum di verifica.
Realizza UJ-5.

**Consequences (testable):**
- Il Foglio soluzione è un artefatto distinto dal testo dell'esercizio ed è esportabile
  separatamente.
- Il checksum consente di verificare che Foglio soluzione e Variante appartengano alla stessa
  generazione.

#### FR-25: Banco esercizi del tenant
Un utente Studio può conservare, etichettare e ritrovare i propri esercizi e le proprie Varianti.
Realizza UJ-5, UJ-6.

**Consequences (testable):**
- Il contenuto di un tenant non è accessibile ad altri tenant.
- Gli esercizi sono etichettabili almeno per corso, ateneo, argomento e difficoltà.

### 5.8 Account, Crediti e fatturazione

**Description.** Il consumo è per Soluzione consegnata, mai per tentativo. Il B2C compra Crediti
prepagati; il B2B sottoscrive posti.

**Functional Requirements:**

#### FR-26: Consumo per Soluzione consegnata
Il sistema consuma Crediti solo alla consegna di una Soluzione con Badge Verificata.

**Consequences (testable):**
- Un Rifiuto di certificazione non consuma Crediti.
- Un errore di sistema non consuma Crediti.
- Una ripresa dopo Domanda mirata non consuma Crediti aggiuntivi.
- Il saldo residuo è visibile prima di iniziare un'elaborazione.

#### FR-27: Acquisto di Crediti e piani
Un utente può acquistare pacchetti di Crediti o un piano a tempo; un tenant può sottoscrivere
posti Studio.

**Consequences (testable):**
- I prezzi mostrati al consumatore includono le imposte applicabili.
- La ricevuta o fattura è disponibile per ogni acquisto.
- Un piano a tempo dichiara il proprio limite di uso equo prima dell'acquisto.

#### FR-28: Registrazione con dichiarazione di età
Un utente dichiara di avere l'età minima al momento della registrazione.

**Consequences (testable):**
- La registrazione non si completa senza la dichiarazione.
- Esiste una procedura documentata di rimozione per account non conformi.

### 5.9 Trasparenza e controllo dei dati

**Description.** Gli obblighi di trasparenza sono requisiti funzionali del prodotto, non una
pagina legale. Stanno qui perché devono essere implementati, testati, e non regredire.

**Functional Requirements:**

#### FR-36: Quota per soggetto anonimo

Il sistema applica una quota di prova al `subject_id` anonimo, senza richiedere un account.
Realizza UJ-7, UJ-1.

**Consequences (testable):**
- La quota è contata **per soggetto**, non per mese di calendario: un utente in conversazione non
  ha un account su cui contare un ciclo mensile.
- La prima Soluzione consegnata è sempre completa — badge, residui, passaggi, disegni. Il valore
  atterra per intero almeno una volta prima di qualunque limite.
- Esaurita la quota, la superficie non mostra un modale di pagamento: mostra il collegamento al
  dominio proprio, dove avviene l'acquisto.
- Un soggetto anonimo che ricrea la sessione per azzerare la quota viene rilevato.
- Alla fusione dei soggetti (FR-21) la quota consumata segue il soggetto, non si azzera.

#### FR-29: Dichiarazione d'uso dell'IA al primo contatto
Il sistema dichiara di usare intelligenza artificiale al primo punto di contatto, su ogni
superficie. Realizza UJ-1, UJ-7.

**Consequences (testable):**
- La dichiarazione è visibile senza interazione, prima di qualunque caricamento.
- È presente sulla superficie web e sulla superficie assistente.
- Non è assolta dalla sola presenza nei termini di servizio.

#### FR-30: Cancellazione automatica delle immagini
Il sistema cancella l'immagine sorgente entro **72 ore** dall'estrazione dell'IR.

**Consequences (testable):**
- Nessuna immagine sorgente sopravvive oltre 72 ore dall'estrazione, verificato da un controllo
  automatico che fallisce se ne trova una.
- L'IR e la Soluzione restano disponibili dopo la cancellazione dell'immagine.
- Il periodo effettivo è dichiarato all'utente e nell'informativa, e coincide con quello
  applicato.

**Notes:** 72 h è il **limite superiore, mai estendibile** — è il confine owner-locked, e il
requisito è testabile così com'è: il controllo automatico cerca immagini più vecchie di 72 h e
fallisce se ne trova. **Il periodo effettivo dentro la finestra 24–72 h resta decisione aperta
§16.4 e questo PRD non lo fissa.** La stesura precedente diceva «fissato qui»: chiudeva una
decisione che §16.4 dichiara aperta, e il documento teneva tre stati per lo stesso numero.

#### FR-31: Offuscamento delle regioni personali
Il sistema offre di offuscare le regioni testuali non circuitali prima di trasmettere l'immagine a
un fornitore esterno.

**Consequences (testable):**
- L'offuscamento avviene prima della trasmissione a qualunque fornitore esterno.
- L'utente è avvisato al caricamento di non includere dati identificativi.

#### FR-32: Consenso esplicito all'uso dei contenuti per il miglioramento
Il sistema usa i contenuti caricati per migliorare i propri modelli solo con consenso esplicito,
disattivato di default.

**Consequences (testable):**
- L'impostazione predefinita è "non usare".
- La revoca è possibile e ha effetto sugli usi successivi.
- Lo stato del consenso è ispezionabile dall'utente.

#### FR-33: Esercizio dei diritti dell'interessato
Un utente può ottenere accesso, portabilità e cancellazione dei propri dati.

**Consequences (testable):**
- Le richieste sono evase entro il termine di legge.
- La cancellazione dell'account rimuove IR e Soluzioni entro il termine dichiarato.

### 5.10 Misurazione della qualità

**Description.** Le metriche di §8 non sono reportistica: sono il meccanismo che tiene in piedi la
promessa commerciale. Il gold set e l'eval harness sono parte del prodotto. Dalla v3 questo vale
in particolare per **VCER**, che è la metrica su cui §7 decide se il prodotto continua a esistere:
una metrica che decide un gate e che nessun requisito impone di calcolare non è un gate.

**Functional Requirements:**

#### FR-34: Eval harness sul gold set
Il sistema misura **tutte le metriche di §8** su un insieme di riferimento annotato, in modo
riproducibile: SER, VSR, QPS, TTV e le nove metriche v3 — NED, TVR, VCER, SEC, RRC, VDR, SM-18,
SM-19, SM-20.

**Consequences (testable):**
- L'esecuzione produce **ogni** metrica di §8 più una ripartizione degli errori per tipo. Una
  metrica di §8 che l'harness non calcola è un difetto dell'harness, non una metrica facoltativa.
- **VCER è calcolata a ogni esecuzione**, con o senza soglia fissata. La soglia è owner-locked;
  il numero no. Senza questa riga il kill criterion di §7 non ha un ingresso.
- L'insieme di riferimento è diviso in una parte di sviluppo e una parte trattenuta; la parte
  trattenuta non è consultabile durante lo sviluppo.
- L'eval gira su ogni modifica che tocchi estrazione, Validazione elettrica, Trasformazioni o
  Piano didattico.
- Ogni rapporto prodotto dichiara esplicitamente la propria copertura, così che una misura parziale
  non venga letta come complessiva.

**Notes:** `[NOTE FOR PM]` **Limite di copertura dal 13 agosto 2026.** L'insieme di riferimento è
**strutturato**, non fotografico: copre la catena a valle dell'IR — solver, Trasformazioni, Verifica
— e **non** l'estrazione da immagine. Chiuderlo richiede un insieme fotografico anche piccolo
(30–40 immagini bastano a distinguere un SER dell'1% da uno del 10%; **non** bastano a sostenere
un claim di SER molto basso — piano master §8.3, e SM-1 punta sotto lo 0,5%).

#### FR-35: Segnalazione di errore dall'utente
Un utente può segnalare che una Soluzione consegnata è sbagliata, dall'artefatto stesso.

**Consequences (testable):**
- La segnalazione allega automaticamente l'IR e l'identificativo della soluzione.
- Le segnalazioni sono conteggiate per mille Soluzioni consegnate come indicatore anticipatore di
  SER.

#### FR-46: Famiglie di test obbligatorie, e il fallimento sfuggito diventa invariante
La suite comprende **tutte** queste famiglie: unit, integration, property-based, metamorfiche,
mutation testing, golden `ProofGraph`, visual round-trip.

**Consequences (testable):**
- L'assenza di una famiglia è un difetto della suite, non una scelta di stile: un controllo
  elenca le famiglie presenti e fallisce se ne manca una.
- **Ogni fallimento sfuggito in produzione diventa una fixture o un invariante permanente** prima
  che il difetto sia dichiarato chiuso. Un difetto chiuso senza il test che lo cattura non è chiuso.
- I golden `ProofGraph` sono versionati: un cambio di golden è una modifica esplicita e revisionata,
  non un aggiornamento automatico che assorbe la regressione.

**Notes:** Origine: addendum §H.4, piano master §21. Era un vincolo v3 senza requisito — zero
occorrenze nel PRD prima del 15 agosto.

#### FR-51: Registro di provenienza e licenza — oggetto versionato, non foglio amministrativo
Ogni artefatto acquisito dall'esterno — immagine, annotazione, circuito, netlist, testo, benchmark
— entra nel corpus **solo** attraverso un `SourceAsset` registrato e versionato.

```
SourceAsset:
  source_id · origin_url · provider · retrieved_at · artifact_hash
  asset_type: image | annotation | circuit | netlist | text | benchmark
  license:    identifier · version · license_url · commercial_use ·
              derivative_use · redistribution · attribution_required
  provenance: original_author · dataset · dataset_version · source_record
  consent:    required · status · scope
  allowed_uses: evaluation | training | fine_tuning | publication | demo
  restrictions: []
  evidence:   license_snapshot_hash · evidence_ref
```

**Consequences (testable):**
- Lo stato di un `SourceAsset` è uno fra `ALLOWED · RESTRICTED · REVIEW_REQUIRED · PROHIBITED ·
  UNKNOWN`.
- **`UNKNOWN` è fail-closed per addestramento e ridistribuzione.** *Assenza di licenza nota non è
  permesso d'uso*: un artefatto senza licenza accertata non è materiale libero, è materiale non
  ancora valutato.
- Il registro è **versionato come il codice**, non compilato a fine progetto. Un corpus con un
  registro ricostruito a posteriori non è ripulibile: le prove di licenza si raccolgono al momento
  dell'acquisizione o non esistono più.
- `evidence.license_snapshot_hash` cattura il testo di licenza **al momento del prelievo**. Le
  licenze online cambiano e la pagina di oggi non prova i termini di ieri.
- **Nessun agente può aggiungere materiale al corpus.** Un agente può *proporre* un `SourceAsset` in
  stato `REVIEW_REQUIRED`; la promozione ad `ALLOWED` richiede una decisione umana registrata.
  «Sembra pubblico» non è uno stato.
- Vincoli già accertati da rispettare: CGHD e Digitize-HCD aperti e usabili; **Image2Net/Fiore —
  formula NED adottabile, dataset no** (`docs/01-fonti-esterne.md`, piano master §8.3).

**Notes:** Origine: decisione owner del 15 agosto, attivata dalla scelta di raccogliere «da banche
dati e online». `[NOTE FOR PM]` L'ultima consequence — **il registro come confine non aggirabile
dall'agente** — ha la forma di un confine owner-locked, non di un requisito di prodotto. La
costituzione è owner-locked e questo PRD non la modifica: **se deve stare lì, ce la metti tu.** Qui
resta come requisito, il che la rende vincolante per il codice ma non per un agente che lavori fuori
da questo repo.

---

## 6. Non-Goals (Explicit)

- **Non valutiamo persone.** Kirchhoff non produce voti, punteggi di merito, ranking, dashboard di
  rendimento, né segnalazioni di studenti a rischio. Nessun endpoint restituisce un punteggio
  associato a una persona identificata. È un confine permanente, non un rinvio: è ciò che tiene il
  sistema fuori dall'Allegato III dell'AI Act, e con esso fuori da un regime di conformità
  insostenibile per un fondatore singolo. **Ogni richiesta di cliente in questa direzione va
  rifiutata o riformulata come generazione.**
- **Non diventiamo un chatbot.** Nessuna chat libera generalista: cancellerebbe la promessa di
  verificabilità, che è la condizione perché la derivazione disegnata valga qualcosa (§1).
- **Non copriamo i circuiti non lineari** in v1, ed è dichiarato pubblicamente nella tabella
  comparativa. Dichiarare il limite è ciò che rende credibili le altre righe.
- **Non addestriamo sui contenuti degli utenti** per impostazione predefinita.
- **Non pubblichiamo temi d'esame altrui.** Il corpus pubblico è fatto di Varianti generate da noi.
- **Non costruiamo un modello di visione proprio, né un simulatore da zero, né app native.**
- **Non aggiungiamo community, gamification, badge di gioco o classifiche.**
- **Non siamo il sistema di record dentro un assistente di terzi:** l'anagrafica resta l'account
  Kirchhoff.

## 7. MVP Scope

> 🔑 **Il kill criterion che precede tutto — Gate A.**
> Se la **continuità visuale non è chiaramente migliore di un re-layout completo**, il catalogo
> delle trasformazioni **non si espande** e il prodotto non ha una ragione di esistere nella forma
> descritta da §1. Bastano **serie, parallelo e partitore** per saperlo. Se non regge: ci si ferma
> e lo si segnala — non si prosegue su B, C, D.
>
> Questo callout **sostituisce** quello del PRD v2, che promuoveva a gate la baseline dei modelli
> frontier sul gold set fotografico (>85%). Quel gate **resta obbligatorio ma non è più il primo**:
> è il gate di **Gate C**, dove la foto è stata spostata. Origine: piano master §24, addendum §H.1.
> Il rischio R2 — commoditizzazione del riconoscimento — resta aperto e va monitorato lì.

**I gate, una volta sola.** Il documento li cita per lettera in §7.2, §16 e §5; qui sono definiti.
Sono le tappe del piano master §25, non fasi di progetto inventate qui.

| Gate | Cosa apre | Criterio d'uscita |
|---|---|---|
| **A** | Visual Proof Kernel — **è l'MVP** | il kill criterion di §7.0. Può uccidere l'idea |
| **B** | Tutor interattivo e lavagna | dopo A |
| **C** | Ingresso da foto e percezione | dopo A, con held-out fotografico reale |
| **D** | Catalogo esteso — Millman, Thévenin/Norton, transitori | dopo A, sorvegliato da SM-C5 |
| **E** | Studio B2B — Varianti, Fogli soluzione | dopo A; è il motore di ricavo |
| **F** | Banco del tenant e piano Dipartimento | dopo E |
| **G** | Domini oltre l'elettrotecnica | dopo E |

### 7.0 Perché l'MVP è il solo Visual Proof Kernel

**Decisione owner del 15 agosto 2026**, presa dopo che il presupposto della decisione precedente è
caduto.

Il 13 agosto il peso dell'MVP era stato messo su Solve con una motivazione precisa: *il gold set
nasce dal B2C, le foto reali arrivano dagli studenti*. Il correct-course v3 sposta l'ingresso da
foto a Gate C — «la foto è input rischioso e **non è il collo di bottiglia del valore**» (§8.1).
**Senza foto nell'MVP, quella motivazione non esiste più**, e una decisione che sopravvive al
proprio motivo è drift, non continuità.

La forma nuova è più stretta di entrambe le precedenti:

1. **Gate A può uccidere l'idea.** Ha un kill criterion vero, e finché non è superato ogni cosa
   costruita sopra è lavoro a rischio di essere buttato. Studio, foto, tutor e lavagna poggiano
   tutti sulla stessa promessa: che la derivazione disegnata valga più della risposta.
2. **Serve poco per saperlo.** Tre trasformazioni — serie, parallelo, partitore — bastano a
   misurare la continuità visuale. Non serve il catalogo completo, non serve la percezione, non
   serve un secondo prodotto.
3. **Il kernel è condiviso comunque.** `CircuitIR`, `LayoutIR`, `ProofGraph`, verifica e rifiuto
   servono a Solve e a Studio identici. Costruire prima il kernel non ritarda Studio: lo precede
   per necessità.

**Conseguenza accettata:** nessun ricavo nell'MVP, e nessun canale di acquisizione. L'asset
dell'MVP è **una risposta binaria a una domanda che vale l'intero prodotto**.
**Conseguenza da sorvegliare:** un MVP senza utenti non produce segnale di mercato. Se Gate A
passa, il ribilanciamento verso Solve e Studio va rifatto **subito**, con la sequenza B → E del
piano. `[ASSUMPTION: il kill criterion è valutabile in modo non ambiguo dal confronto fra
continuità visuale e re-layout completo su serie/parallelo/partitore. Se la valutazione risultasse
soggettiva, il gate va reso misurabile prima di eseguirlo — è la condizione perché §7 abbia senso.]`

### 7.0.1 Protocollo di Gate A — decisione owner del 15 agosto 2026

Il reviewer aveva ragione: *«chiaramente migliore»* non è un criterio. Il protocollo qui sotto lo
sostituisce. **È normativo**: il passo 4 progetta la UX dentro questo protocollo, non accanto.

### A-0 — Unmarked Preservation Hypothesis

**Ipotesi progettuale madre del kernel, e ipotesi forte da falsificare.** Non è una legge percettiva
dimostrata: è la scommessa su cui il kernel è costruito, e Gate A esiste anche per abbatterla.
Collegata direttamente a **K-0** — il disegno fa parte della prova.

> Un'entità preservata **non riceve una modifica del proprio visual state per comunicare la
> trasformazione**. Il suo essere invariata è comunicato dal fatto che non le succede nulla. Colore,
> movimento, evidenziazione, comparsa e scomparsa appartengono **esclusivamente al sottografo
> trasformato**.
>
> Se un'entità preservata appartiene **anche** al boundary della trasformazione, il boundary può
> essere rappresentato mediante un **overlay effimero e indipendente**, ancorato geometricamente
> all'entità, **senza modificare il rendering dell'entità sottostante**.

**Preservazione e boundary sono due proprietà diverse, non due letture della stessa.** Per la
riduzione `R3 ∥ R4 → R34` fra i nodi `A` e `B`:

`A, B ∈ Pₖ` — sono nel preserve set

`∂Tₖ = {A, B}` — sono il boundary della trasformazione

Entrambe vere insieme. La conseguenza architetturale è precisa, e non è una sfumatura di stile:

```
✗  Node A: style = blue
✓  Node A: style = unchanged
   TransformOverlay: anchor = A, role = boundary-port
```

**Togliendo l'overlay, `A` torna letteralmente allo stesso rendering — perché non era mai
cambiato.** È il test che distingue le due implementazioni, ed è eseguibile.

È anche ciò che rende leggibile la prova: `Tₖ : G[R3, R4; A, B] → G[R34; A, B]` con `A_{k+1} = A_k`
e `B_{k+1} = B_k`. **È proprio il fatto che i terminali restino gli stessi a rendere significativa
l'equivalenza circuitale**, e marcarli come «cambiati» negherebbe l'affermazione che si sta
provando.

| Elemento | Segnale |
|---|---|
| `R3`, `R4` — il delta | forte: sono ciò che cambia |
| `A`, `B` — preservati **e** boundary | solo l'overlay strutturale «l'equivalenza vale vista da qui», più discreto del segnale sul delta |
| `V1`, `R1` — preservati | **nessuno** |

**L'invariante è semantico-spaziale, non pixel-perfect.** «Restano esattamente com'erano» sarebbe
troppo forte: responsive, zoom, viewport, anti-aliasing ed evitamento di collisioni producono
differenze minime e legittime. Per ogni entità preservata `x`:

`id_{k+1}(x) = id_k(x)` — **sempre, senza eccezioni**

`p_{k+1}(x) ≈ p_k(x)` e `θ_{k+1}(x) = θ_k(x)` — **salvo necessità geometriche dimostrabili**

con ordine relativo, appartenenza ai nodi e ruolo circuitale invariati. **Se qualcosa di non
trasformato deve muoversi per ragioni di layout, quel movimento è minimo, misurabile e penalizzato
da VCER** — non reinterpretato come normale libertà del renderer. È la differenza fra un'eccezione
che si paga e un'eccezione che si assolve da sola.

**Quattro classi di stato, e solo la prima è vincolata.** Un elemento invariato **può** cambiare
aspetto: quello che non può è cambiarlo *perché è avvenuta una trasformazione*.

| Classe | Esempi | Vincolata da A-0 |
|---|---|---|
| **Stato semantico di trasformazione** | il delta di `Cₖ → Cₖ₊₁` | **sì — non può usare gli invarianti come supporto grafico** |
| **Stato di interazione** | selezione, hover, focus, ispezione del certificato, «fammi vedere cosa è rimasto uguale» | no |
| **Stato di accessibilità** | alto contrasto, evidenziazione da lettore di schermo | no |
| **Stato di ispezione/debug** | modalità diagnostica, sovrapposizione delle misure | no |

Pan e zoom dell'intera viewport non sono codifica: trasformano la vista, non il circuito.

**Non è solo UX: è un vincolo del dominio.** Se A-0 vale, `LayoutPatch` non può essere *«fammi un
layout che assomigli al precedente»*, e il renderer non decide cosa «sembra invariato». Il `Transform`
deve esporre `preserve_entities`, `remove_entities`, `create_entities`, `preserve_nodes`,
`node_mapping`, `changed_edges`; il patch **deriva** da quelli. Vedi FR-38 e FR-47.

`[ASSUMPTION: A-0 è confermata dall'owner il 15 agosto come regola progettuale, esplicitamente
**non** come legge percettiva dimostrata per Kirchhoff. Resta ipotesi finché Gate A non la conferma
o la abbatte. Vincere «perché sembra più pulita» non basta: deve vincere sulla continuità mentale
del circuito.]`

### I quattro bracci del confronto

Le due specifiche dell'owner stanno su **un asse solo**, non su due incrociati: *conventional-focus*
presuppone il layout persistente, perché si può attenuare il resto solo se il resto è ancora lì. Un
disegno fattoriale darebbe sei celle e non finirebbe.

| Braccio | Cosa rende | A quale domanda risponde |
|---|---|---|
| **0 — baseline globale equa** | Lo **stesso** renderer, gli **stessi** vincoli estetici, lo stesso `CircuitIR(Cₖ₊₁)`, **senza conoscere** `Layout(Cₖ)`. Ri-layout indipendente vero, non costruito per perdere | La continuità di posizione serve? |
| **A — unmarked preservation** | `Layout(Cₖ) + LayoutPatch → Layout(Cₖ₊₁)`; segnale visivo **solo** sul delta | **A-0** |
| **B — marked preservation** | Come A, più una codifica leggera «unchanged» sui sopravvissuti | Marcare aiuta o disturba? |
| **C — conventional focus** | Delta evidenziato, **resto attenuato** — il pattern UI comune | Il pattern comune fa meglio? |

Il braccio 0 e il braccio A sono **deliverable dell'MVP** (FR-47): senza il primo non c'è confronto,
senza il secondo non c'è prodotto. B e C sono varianti di rendering dello stesso `LayoutIR`, non
prodotti separati.

> **Il braccio C è il comportamento che l'owner ha revocato dal default il 15 agosto.** La journey
> del mattino diceva «il resto si attenua»; la correzione del pomeriggio lo toglie, perché attenuare
> i sopravvissuti **è comunque modificarli**, e comunica *«queste sono le cose che non ci
> interessano»* invece di *«il circuito è ancora questo, guarda solo ciò che cambia»*. Il focus deve
> essere **positivo e locale sul delta**, non negativo e globale sul resto. Il design ritirato resta
> come concorrente da battere: è il modo più onesto di trattarlo.

**Il `preserve set` non è scelto dal layout engine.** Deriva deterministicamente dalla
trasformazione:

`Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)`

applicata dopo la `node_mapping` / `entity_mapping` della trasformazione. **Così `preserve = {}` non
può barare prendendo VCER = 0**: l'insieme da conservare è imposto dall'identità degli oggetti, non
dichiarato da chi viene misurato. Chiude il difetto di autocertificazione trovato al gate.

**Misure automatiche**, su ogni elemento obbligatoriamente preservato: spostamento normalizzato,
cambio di orientamento, inversione dell'ordine relativo, rerouting non richiesto, e le altre
discontinuità geometriche. Alimentano VCER (SM-14) e le complementari (SM-18).

**Lettura umana — cieco su quattro bracci.** Allo studente non si dice quale versione è Kirchhoff.
Sei misure, di cui **cinque oggettive e una soggettiva** (SM-21):

| # | Misura | Tipo |
|---|---|---|
| 1 | Tempo per indicare **cosa è cambiato** | tempo |
| 2 | Errori nell'indicare **cosa è rimasto uguale** | errori — la misura più vicina ad A-0 |
| 3 | Capacità di **ricostruire `Cₖ`** dopo aver visto `Cₖ₊₁` | errori |
| 4 | Tempo per trovare i **nodi terminali** della trasformazione | tempo |
| 5 | Errori nell'**identità dei componenti** | errori |
| 6 | Preferenza soggettiva | **secondaria**, raccolta in coda |

La preferenza si chiede **dopo** le cinque misure oggettive, mai prima: in testa trasformerebbe un
test di comprensione in un test di gradimento. **Un braccio che vince solo sulla misura 6 non ha
vinto.**

**Chi decide.** Il fondatore è il primo expert evaluator, **non l'unico campione**: il gate si prova
su studenti reali del target. Il bacino esiste già ed è quello delle ripetizioni (§17).
`[NOTE FOR PM]` §7.0 dice «nessun utente nell'MVP»: quegli studenti sono **valutatori**, non
clienti, e non aprono un canale di acquisizione. La distinzione va tenuta, o §7.0 e questo
protocollo divergono.

**Soglia GO/NO-GO: owner-locked** (§16 Q0), deliberatamente non fissata qui. Il protocollo per
misurarla sta nel PRD; il numero no.

> 🟠 **Resta aperto un solo pezzo: il corpus.** Su quanti circuiti si esegue il confronto, scelti
> come, stratificati dove l'ipotesi prevede una differenza. Un corpus di sole reti resistive
> piccole è dove la baseline B resta quasi stabile per conto suo — cioè dove il gate può uccidere
> un prodotto valido. Vedi §16 Q9.

**La promessa che il gate falsifica**, in una riga:
*«Quando il circuito cambia, riesco a vedere esattamente cosa è cambiato senza perdere mentalmente
il circuito che stavo guardando.»*

### 7.1 In Scope — il Visual Proof Kernel, e nient'altro

**Ogni riga nomina i requisiti che la realizzano.** Un FR che non compare qui non è in MVP, e la
lista degli esclusi in §7.2 è il complemento esatto di questa — non un elenco a parte.

| In MVP | FR |
|---|---|
| **Reti resistive in DC.** Nessun transitorio, nessun regime sinusoidale, nessun trifase | vincolo di dominio, nessun FR |
| **Ingresso strutturato soltanto**: esercizi già strutturati da una raccolta controllata, più import da netlist/fixture come interfaccia tecnica secondaria. **Nessun editor** | **FR-1** limitato ai formati strutturati (il ramo foto è fuori) |
| **Baseline globale equa** — secondo braccio del confronto di Gate A, stesso renderer senza conoscenza del layout precedente | **FR-47** |
| **`ProofSession` indipendente dalla superficie**, presentabile da PWA, superficie MCP e in seguito Ardesia | **FR-48** |
| **Ispezione del passaggio** — Prima↔Dopo, provenienza di un elemento, «perché posso farlo?» | **FR-49** |
| **Validazione elettrica** come gate sull'IR in ingresso | **FR-4** — richiesta da FR-9 e dalla definizione di SM-13 |
| `CircuitIR` e `LayoutIR` **distinti e persistenti**, con canonicalizzazione e confronto di grafi | **FR-37** |
| **Tre trasformazioni**: serie, parallelo, partitore di tensione. Il catalogo non si espande finché il kill criterion non è superato | **FR-43**, sorvegliato da SM-C5 |
| `LayoutPatch` con `preserve / remove / create / node_mapping / reroute_scope`, e gli invarianti `id_{k+1}(x) = id_k(x)` esatto, `p_{k+1}(x) ≈ p_k(x)` entro tolleranza owner-locked | **FR-38** |
| **Grammatica obbligatoria del passo**: `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE · PROVENANCE`. È schema dati, non presentation design | **FR-39**, misurata da SEC |
| `ProofGraph` invece della traccia lineare — anche con tre trasformazioni la struttura dati è a branch e join, perché cambiarla dopo costa una migrazione | **FR-40** |
| **Visual round-trip** come controllo primario: SVG semantico con `data-component-id` e `data-terminal-*` → riparsa → `ReconstructedCircuitIR` → canonicalizzazione → **confronto esatto di grafi**. Nessun VLM nel percorso di certificazione | **FR-41**, misurato da RRC |
| **Verifica a cinque controlli** e **Rifiuto di certificazione** tipizzato | **FR-11**, **FR-12** |
| **Gate di veridicità proprietario** col tipo `Claim` — non una skill esterna (§19, addendum §H.1) | **FR-42** |
| **Nessun valore da modello linguistico** | **FR-13** |
| **Export SVG/PDF con Marcatura di provenienza** — art. 50 AI Act si applica dal 2 agosto 2026 e non si retrofitta | **FR-18** ridotto a SVG/PDF, **FR-19** |
| **Eval harness** con le metriche di §8 e segnalazione errore | **FR-34**, **FR-35** |
| **Famiglie di test obbligatorie**, e ogni fallimento sfuggito diventa invariante permanente | **FR-46** |
| **Un kernel, tre adapter, nessun fork** — vincolo di costruzione, vale dal primo commit | **FR-45** |

> **Decisione owner del 15 agosto: FR-9 esce da Gate A.** L'editor circuitale completo è costoso e
> non risponde alla domanda che Gate A deve falsificare. Per questa fase bastano problemi
> strutturati pre-caricati e, come interfaccia tecnica secondaria, import da netlist/fixture.
> **L'editor torna quando serve a un flusso utente vero**, non prima.

### 7.2 Out of Scope for MVP

- **Ingresso da foto e tutta la percezione** — **Gate C, portato in parallelo a Gate A** per
  decisione owner del 15 agosto. Non entrano nella tabella di §7.1 e **non entrano
  nell'esperimento di §7.0.1**: l'A/B di Gate A riceve `CircuitIR`, mai un'estrazione. Un circuito
  letto male confonde lo studente per ragioni che non riguardano la continuità del disegno, e il
  verdetto non sarebbe più interpretabile. FR-2, FR-3, FR-5, FR-6, FR-7, FR-8 e il ramo fotografico
  di FR-1 sono **lavoro attivo su un binario proprio**, con un proprio criterio d'uscita.

  > **Vincoli che questa scelta attiva** — tutti preesistenti, nessuno nuovo:
  > **(a) Licenze.** CGHD e Digitize-HCD sono aperti; **Image2Net/Fiore no** — la formula NED si
  > adotta, il dataset non si usa (`docs/01-fonti-esterne.md`). Ogni immagine acquisita da banca
  > dati o dal web entra nel **registro licenze e attribuzioni** del piano master §8.3 prima di
  > entrare nel corpus. Un corpus senza registro non è utilizzabile e non si ripulisce a posteriori.
  > **(b) L'held-out non viene dalle banche dati.** L'addendum lo fissa: *«Foto scattate dagli
  > studenti, non scansioni»*. Le banche dati costruiscono lo split di sviluppo; la parte
  > trattenuta resta raccolta dal vero, dal bacino delle ripetizioni (§17).
  > **(c) Il conteggio di FR-34 resta valido.** 30–40 immagini distinguono un SER dell'1% da uno del
  > 10%, non sostengono un claim di SER molto basso. Allargare il corpus con banche dati alza il
  > volume, non chiude da solo il punto cieco di SM-1.

  > **Correzione del 15 agosto.** Qui c'era scritto «FR-1…FR-9 restano scritti, fuori MVP»: un
  > blocco che escludeva anche FR-1 e FR-4, cioè l'ingresso strutturato e la Validazione elettrica
  > — che §7.1 elenca **in** scope dieci righe sopra. Le due sezioni si contraddicevano e §7.1 non
  > nominava un solo FR, quindi la contraddizione non era visibile a chi legge per costruire. Ora
  > §7.1 è una tabella con gli ID e questa riga ne è il complemento esatto.

- **Editor del circuito — FR-9.** Fuori da Gate A per decisione owner del 15 agosto: costoso e non
  necessario a falsificare l'ipotesi del gate. Rientra quando serve a un flusso utente reale.
- **Studio B2B** (Varianti vincolate, Fogli soluzione, banco del tenant) — Gate E/F. Resta il
  motore di ricavo; non precede la prova che il motore vale.
- **Tutor interattivo e lavagna** — Gate B.
- **`StudentTrace` — FR-44.** Fuori dall'MVP di Gate A: il kernel visuale si prova senza. **Non**
  fuori dalla prima release rivolta allo studente, che è la correzione del procedimento e lo
  richiede. Separato dal tutor il 24 agosto 2026: erano nella stessa riga e condividevano un
  «Gate B» che per l'uno significa «dopo» e per l'altro «subito dopo Gate A». Scritto già ora
  perché vincola il confine del verifier che si costruisce adesso.
- **Millman, Thévenin/Norton, transitori, sinusoidale, trifase** — dopo il kill criterion. Sono
  esattamente ciò che «non espandere il catalogo» significa.
- **Crediti, pagamenti, posti Studio** — nessun incasso su un kernel non ancora provato.
- **Percorso C** (terzo motore di verifica) — differito. Alto valore commerciale verso i
  docenti, nessun valore per il primo studente pagante. `[NOTE FOR PM]` È l'argomento di vendita
  più forte verso un dipartimento: rivalutare non appena il canale B2B si apre.
- **Utenti 14–17** — richiede informativa semplificata dedicata. v2.
- **Domini oltre l'elettrotecnica** (Automatica, elettronica digitale, analisi numerica) — v2/v3,
  già previsti nella visione.
- **SSO e piano Dipartimento** — v2; nessun cliente istituzionale prima che il pacchetto
  documentale sia completo.
- **Più Profili curricolari** — v1 ne implementa uno reale; il secondo dimostra la
  generalizzazione ed è la prima cosa dopo il lancio.
- **App native** — permanente (§6).
- **Localizzazione oltre l'italiano** — v2. `[NOTE FOR PM]` La superficie assistente è
  intrinsecamente internazionale: la richiesta arriverà prima del previsto.

---

## 8. Success Metrics

**Primary**

- **SM-1 — SER (Silent Error Rate).** Quota di Soluzioni consegnate con Badge Verificata ma
  numericamente sbagliate, misurata sulla parte trattenuta dell'insieme di riferimento e sulle
  segnalazioni. Target v1 **< 0,5%**, v2 **< 0,1%**. Valida FR-10, FR-11, FR-13.
  *È la metrica bloccante: sopra il 2% e non in discesa, il prodotto si ferma.*
  🟠 **Punto cieco in chiusura (13 agosto 2026, sera).** Con il solo insieme strutturato SER
  misurava la catena a valle dell'IR e **non** l'estrazione. La Story 1.3 aggiunge la metà
  fotografica da dataset a licenza aperta verificata, e il rapporto separa i due numeri invece di
  mediarli. Resta cieca finché 1.3 non è `done`. Un circuito letto male è internamente coerente e supera KCL, KVL e bilancio di potenza
  senza battere ciglio. SER resta bloccante, ma va letta sapendo cosa non vede.
- **SM-2 — VSR (Verified Solve Rate).** Quota di esercizi che arrivano a Soluzione consegnata
  senza correzione umana dell'IR. Target v1 **65%**, v2 **88%**. Valida FR-2, FR-3, FR-4, FR-14.
- **SM-3 — VVDR (Verified Visual Derivation Rate).** ⭐ **Metrica nord, v3.** Derivazioni visuali
  **interamente certificate** / problemi accettati. Valida l'intero §5.0 e §5.
  > **Sostituisce** «Soluzioni consegnate a settimana» del PRD v2. Quella metrica era compatibile
  > con un prodotto che **non disegna nulla**: si poteva massimizzarla consegnando risposte
  > verificate senza un solo stato visuale. Origine: piano master §22, addendum §H.1.

**Metriche nuove della v3 — nominate, soglie non fissate**

Le nove metriche qui sotto entrano nel PRD perché l'harness deve calcolarle dal primo giorno. **Le
soglie di lancio sono decisione aperta §27.6 ed è owner-locked**: un agente che le inventa viola
un confine, e questo PRD deliberatamente non le contiene. FR-34 le impone come uscita obbligatoria
dell'harness.

> **Nomenclatura, 15 agosto 2026 — collisione risolta.** La stesura precedente aveva assegnato a
> `TVR`, `SEC`, `RRC` e `VDR` significati diversi da quelli del piano master (`§27`, righe
> 835-841), mentre §16 Q0 rimandava a §27.6 per le soglie: una soglia fissata sul significato del
> master sarebbe stata applicata a una grandezza diversa, in un'altra unità. **Le quattro sigle
> adottano ora i significati del piano master.** I tre concetti che occupavano quelle sigle
> sopravvivono con un ID proprio e senza acronimo — SM-18, SM-19, SM-20 — perché servono e non
> devono ricollidere.

- **SM-12 — NED (Netlist Edit Distance).** Distanza di edit fra il grafo ricostruito e quello
  vero, normalizzata su dispositivi, net e porte. È la definizione pubblicata da Image2Net —
  adottare la formula è legittimo, il dataset no (`docs/01-fonti-esterne.md`). Misura ciò che SER
  non vede: un circuito letto male è internamente coerente e supera KCL, KVL e bilancio di potenza.
- **SM-13 — TVR (Transformation Validity Rate).** Quota di Trasformazioni applicate il cui `IR`
  risultante supera la Validazione elettrica ed è equivalente all'`IR` di partenza sulle grandezze
  conservate. Misura la correttezza dell'operazione, non del disegno. Valida FR-43, FR-38.
- **SM-14 — VCER (Visual Continuity Error Rate).** Quota di `LayoutPatch` che violano
  **`p_{k+1}(x) ≈ p_k(x)` oltre la tolleranza dichiarata**, oppure `id_{k+1}(x) ≠ id_k(x)`, oppure
  `θ_{k+1}(x) ≠ θ_k(x)`, su almeno un `x ∈ preserve`. **È la metrica del kill criterion.** Valida
  FR-38.
  > **Corretta il 15 agosto — conflitto trovato dal gate della Spine.** Questa riga diceva
  > `p_{k+1}(x) = p_k(x)`, uguaglianza **esatta**, mentre FR-38 era stato emendato lo stesso giorno
  > a `≈` con necessità geometriche ammesse. Due unità che leggessero l'una o l'altra avrebbero
  > prodotto **due numeri diversi per la stessa metrica**, e la metrica è quella su cui Gate A
  > decide se il prodotto continua. `id` e `θ` restano esatti e non hanno tolleranza.
  > 🔴 **La tolleranza numerica su `p` è owner-locked** (§16 Q0) e questo PRD non la fissa: senza,
  > `≈` non è misurabile. **Proprietario della misura: l'harness di FR-34**, non il renderer — chi
  > produce lo scostamento non lo quantifica.
- **SM-15 — SEC (Step Evidence Coverage).** Quota di passi che portano tutti e sei i campi della
  grammatica `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE · PROVENANCE` compilati e non vuoti.
  Un passo con `CERTIFICATE` assente è un passo non provato. Valida FR-39.
- **SM-16 — RRC (Render Roundtrip Correctness).** Quota di rendering il cui SVG semantico,
  riparsato e canonicalizzato, riproduce **esattamente** il `CircuitIR` atteso. Misura la
  correttezza del disegno, non dell'operazione. Valida FR-41.
- **SM-17 — VDR (Visual Derivation completion rate).** Quota di problemi accettati che arrivano a
  una derivazione visuale **completa**, certificata o no. È il denominatore naturale di VVDR: la
  differenza fra VDR e VVDR isola quanto si perde in certificazione anziché in completamento.
- **SM-18 — Costo di ri-layout per passo.** Quanta parte del `LayoutIR` viene riscritta a ogni
  passo. Distingue «continuità» da «ho ridisegnato tutto e sembrava uguale». `[NOTE FOR PM]`
  Il revisore del kill criterion la indica come la grandezza che il criterio di §7 misura davvero,
  più di VCER: VCER dice se l'invariante è violato, SM-18 dice se `preserve` era ambizioso o vuoto.
- **SM-19 — Copertura della causa di Rifiuto.** Quota di Rifiuti che portano una causa
  localizzata e azionabile invece di un rifiuto generico. Vincolata a K-3: il rifiuto è progettato.
- **SM-20 — Determinismo del rendering.** Quota di rendering che, dato lo stesso `LayoutIR`,
  producono SVG identico. Un renderer non deterministico rende RRC non falsificabile, quindi si
  misura prima di leggere RRC, VCER e SEC.
- **SM-21 — Lettura umana di Gate A.** ⭐ **È il secondo braccio del verdetto, accanto a VCER.**
  Misurata sul confronto cieco a quattro bracci di §7.0.1. **Cinque misure oggettive**: tempo per
  indicare cosa è cambiato · errori nell'indicare cosa è rimasto uguale · capacità di ricostruire
  `Cₖ` dopo aver visto `Cₖ₊₁` · tempo per trovare i nodi terminali · errori nell'identità dei
  componenti. **Una soggettiva**, la preferenza, raccolta in coda e **secondaria**. Valida FR-47,
  FR-49, FR-50.
  > La misura 2 — *errori nell'indicare cosa è rimasto uguale* — è quella che parla direttamente ad
  > **A-0**. Se il braccio A perde su questa, l'ipotesi è abbattuta indipendentemente da come vada
  > il resto. **Un braccio che vince solo sulla preferenza non ha vinto.**
  `[NOTE FOR PM]` Serve una regola di precedenza fra SM-14 e SM-21: se la continuità geometrica
  migliora e la comprensione no, il gate cosa risponde? Owner-locked come le soglie (§16 Q10).

**Secondary**

- **SM-4 — QPS (Questions Per Solve).** Domande mirate medie per Soluzione consegnata. Target v1
  **≤ 1,5**, v2 **≤ 0,5**. Valida FR-6, FR-7.
- **SM-5 — TTV (Time To Verified).** Secondi dal caricamento alla Soluzione consegnata, al 90°
  percentile. Target v1 **< 45 s**, v2 **< 25 s**. Valida FR-2, FR-10, FR-14.
- **SM-6 — Attivazione.** Quota di utenti registrati che ottengono una Soluzione consegnata entro
  10 minuti. Target **> 60%**. Valida FR-1, FR-5.
- **SM-7 — Ritorno alla seconda soluzione.** Target **> 70%**. Valida FR-15, FR-11.
- **SM-8 — Correzioni per soluzione.** Modifiche manuali all'IR per Soluzione consegnata.
  Target **< 1,0**. Valida FR-2, FR-5, FR-9.
- **SM-9 — Segnalazioni per mille Soluzioni consegnate.** Indicatore anticipatore di SM-1.
  Valida FR-35.
- **SM-10 — Varianti consegnate per utente Studio al mese.** Misura il valore B2B reale.
  Valida FR-22, FR-23.

- **SM-11 — Conversione conversazione → account.** Quota di utenti che, ottenuta almeno una
  Soluzione consegnata sulla superficie assistente, collegano un account Kirchhoff. Valida FR-21,
  FR-36.
  🔑 **Sotto la tesi MCP-first è la metrica che decide se il canale è un cardine o una perdita.**
  La monetizzazione dentro gli host è chiusa ai servizi digitali: l'incasso avviene solo sul
  dominio proprio, e questo numero misura l'unico ponte che ci arriva. Un canale con uso alto e
  SM-11 bassa porta costo di elaborazione e nessun cliente.

**Counter-metrics (do not optimize)**

> **Le soglie di allarme delle contro-metriche sono owner-locked** (§16 Q0). La stesura precedente
> fissava un tetto ai Rifiuti e un pavimento a QPS: entrambi sono stati **rimossi, non
> sostituiti** — proporre un altro numero sullo stesso confine sarebbe la stessa violazione.
> Restano la direzione e il criterio di lettura, che non sono owner-locked.

- **SM-C1 — Tasso di Rifiuto di certificazione.** Quota di elaborazioni che finiscono in Rifiuto.
  **Non va portato a zero:** il Rifiuto *è* il sistema che funziona, e comprimerlo significa
  ammorbidire il gate. Un tasso in **discesa** mentre SER è stabile o in salita è il segnale
  d'allarme, non il valore assoluto. Controbilancia SM-2 e SM-3.
- **SM-C2 — QPS al ribasso.** Un QPS che scende mentre l'Accordo non migliora significa quasi
  certamente che il sistema ha smesso di chiedere quando dovrebbe. **Se SER e QPS sono in
  conflitto, vince SER.** Controbilancia SM-4.
- **SM-C3 — TTV al ribasso.** Comprimere TTV riducendo il numero di Pass di estrazione degrada la
  misura dell'Accordo, che è la base di tutto il resto. Controbilancia SM-5.
- **SM-C4 — Copertura di dominio.** Allargare i tipi di circuito supportati prima che SER sia
  stabile sotto target moltiplica la superficie di errore silenzioso. Controbilancia SM-3.
- **SM-C5 — Ampiezza del Catalogo, v3.** Numero di trasformazioni supportate **prima** che il kill
  criterion di Gate A sia superato. **Deve restare a tre.** Espandere il catalogo è il modo più
  naturale per far salire VVDR senza aver dimostrato la continuità visuale — cioè per ottimizzare
  la cosa sbagliata. Controbilancia SM-3 e SM-18.
- **SM-C6 — Costo per prova verificata.** Costo di elaborazione diviso derivazioni visuali
  certificate. Una VVDR che sale mentre SM-C6 esplode è un prodotto che non regge il proprio
  prezzo. Origine: piano master §22. Controbilancia SM-3.
- **SM-C7 — Abbandono durante la conferma.** Quota di sessioni che si interrompono su una Domanda
  mirata o sull'Anteprima di ricostruzione. La conferma obbligatoria è ciò che rende onesta la
  catena; se caccia gli utenti, il costo va visto e non nascosto. Origine: piano master §22.
  Controbilancia FR-5, FR-6, FR-7.
- **SM-C9 — Quota di ripiego sul piano nodale.** Quando il Piano didattico non trova una catena di
  Trasformazioni, il sistema ripiega sull'analisi nodale e consegna **un calcolo corretto invece di
  una derivazione disegnata** — con Badge pieno, perché i cinque controlli passano. È il modo più
  silenzioso di far salire VVDR svuotandola: la promessa del prodotto è la derivazione, non il
  numero. **Il ripiego va misurato e dichiarato all'utente, non nascosto dietro un Badge identico.**
  Origine: rilievo del gate della Spine, 15 agosto. Controbilancia SM-3 e SM-17.
- **SM-C8 — Illeggibilità del disegno.** Quota di passi il cui rendering è formalmente corretto e
  praticamente illeggibile — sovrapposizioni, incroci, densità. Il round-trip non la vede: un SVG
  può riprodurre esattamente il grafo ed essere inguardabile. Origine: piano master §22.
  Controbilancia SM-3 e SM-14.

---

## 9. Cross-Cutting NFRs

- **Budget di latenza end-to-end.** Dal caricamento alla Soluzione consegnata, **< 45 s** al 90°
  percentile, domande incluse. Sopra i 60 s l'utente abbandona.
- **Determinismo del calcolo.** A parità di IR confermato, la soluzione e i passaggi sono
  riproducibili.
- **Tracciabilità.** Ogni Soluzione consegnata è ricostruibile a partire dall'IR e dalla versione
  del sistema che l'ha prodotta.
- **Indipendenza dal fornitore di modelli.** Il sistema funziona con almeno due fornitori
  intercambiabili; la caduta di uno degrada la qualità, non la disponibilità.
- **Accessibilità.** Le superfici interattive — Anteprima, Domande mirate, editor, passaggi — sono
  utilizzabili da tastiera e con screen reader, con alternative testuali per ogni disegno. Non
  negoziabile per i clienti istituzionali.
- **Mobile-first.** Il flusso B2C si completa su schermo telefono senza scorrimento orizzontale.
- **Isolamento fra tenant.** Nessun dato di un tenant è raggiungibile da un altro.
- **Osservabilità.** Tutte le metriche di §8 — le quattro storiche più le nove della v3, **VCER
  compresa** — oltre a tasso di Rifiuto e correzioni per soluzione sono
  strumentati in produzione, non solo in eval.
- **Non-regressione della qualità.** Nessuna modifica che tocchi estrazione, Validazione
  elettrica, Trasformazioni o Piano didattico raggiunge la produzione senza esecuzione dell'eval
  harness.

## 10. Constraints and Guardrails

### 10.1 Sicurezza dell'esito
- Il gate di pubblicazione (FR-11) non ha bypass, nemmeno amministrativo.
- In caso di conflitto fra metriche, **SER prevale su QPS, TTV e VSR**, sempre.
- Nessuna soluzione parziale è mostrata come completa.

### 10.2 Privacy
- L'immagine sorgente è il dato più sensibile del sistema: può contenere nome, matricola, grafia e
  nome del docente, e **nulla di questo serve al prodotto**. Conservazione minima (FR-30),
  offuscamento offerto (FR-31), nessun uso per addestramento senza consenso (FR-32).
- I fornitori esterni che ricevono immagini operano senza conservazione dei dati.
- L'elenco dei fornitori che trattano dati degli utenti è pubblico e le modifiche sono notificate
  in anticipo.

### 10.3 Costo
- Il costo di elaborazione per Soluzione consegnata resta sotto il **10% del prezzo effettivo**.
- La strategia a scaglioni (modello economico prima, escalation solo su Accordo basso o
  Validazione elettrica fallita) è consentita **solo se non peggiora SER**.
- **Non si ottimizza il costo dei modelli prima che l'acquisizione sia risolta**: il vincolo
  economico del progetto è il costo di acquisizione, non quello di elaborazione.

### 10.4 Integrità accademica
- La modalità Studio è il default nei contesti educativi.
- Nessuna modalità "solo risposta" è offerta ai tenant istituzionali.
- La policy di uso accademico è pubblica e raggiungibile da ogni pagina.
- La Marcatura di provenienza (FR-19) rende visibile l'uso disonesto: **rendere facile essere
  onesti e visibile essere disonesti**.

## 11. Compliance and Regulatory

Requisiti che il prodotto deve soddisfare per essere immesso sul mercato. Il dettaglio normativo è
nell'addendum del brief, §C.

- **Trasparenza sull'interazione.** Dichiarazione al primo contatto su ogni superficie (FR-29).
- **Marcatura dei contenuti generati.** Leggibile dalla macchina e percepibile dall'utente, su
  ogni artefatto esportabile (FR-19). Nessuna finestra di grazia si applica a un sistema nuovo.
- **Esclusione dall'ambito ad alto rischio.** L'assenza di funzioni valutative (§6) è scritta nei
  termini, imposta tecnicamente, e documentata nella scheda di sistema. **Da riverificare a ogni
  release**, perché la deriva avviene per accumulo di richieste ragionevoli.
- **Alfabetizzazione.** Nota interna su cosa il sistema fa, dove sbaglia, cosa non va mai
  promesso, e chi contattare in caso di incidente. Letta e firmata da chiunque operi il sistema.
- **Scheda di sistema** pubblica: scopo, limiti noti, SER e VSR misurati, sorveglianza umana.
- **Età.** Minimo dichiarato al signup (FR-28) e procedura di rimozione documentata.
- **Pacchetto documentale** completo prima del primo incasso: informativa, termini, cookie,
  registro dei trattamenti, elenco fornitori, accordi di trattamento, policy di uso accademico,
  valutazione d'impatto proporzionata, procedura di violazione dei dati, registro incidenti.

`[NOTE FOR PM]` Il pacchetto documentale è anche un asset commerciale: nessun centro di ripetizioni
serio compra da chi non ha un'informativa. Costo stimato 1.500–4.000 €, da trattare come costo di
lancio.

## 12. Data Governance

- **Residenza.** Dati e artefatti risiedono nell'Unione Europea.
- **Classi di dato e conservazione.** Account (durata del rapporto + 30 giorni) · immagini sorgente
  (24–72 ore, limite superiore owner-locked, valore esatto aperto §16.4) · IR e Soluzioni (durata
  dell'account) · dati di fatturazione (termine di legge) · telemetria pseudonimizzata (14 mesi) ·
  log di sicurezza (6–12 mesi) · contenuti per miglioramento modello (fino a revoca, solo con
  consenso).
  `[ASSUMPTION: i periodi di 30 giorni, 14 mesi e 6–12 mesi non hanno origine in nessun documento a
  monte — né costituzione, né brief, né piano master. Sono proposte di lavoro, non decisioni prese,
  e vanno confermate prima che finiscano nell'informativa.]`
- **Minimizzazione.** Nessun dato identificativo è richiesto oltre a quanto serve per account e
  fatturazione. L'utente è attivamente scoraggiato dal caricare dati identificativi.
- **Verificabilità.** La cancellazione automatica delle immagini è controllata da un test, non
  assunta.

## 13. Monetization

- **B2C a Crediti prepagati**, mai abbonamento mensile: la domanda è stagionale con due picchi e
  mesi morti, e l'abbonamento in questo regime produce rimborsi e disdette.
- Struttura: una prova gratuita limitata con filigrana; due pacchetti di Crediti; un pass a tempo
  come opzione principale nei picchi; un piano annuale per lo studente diligente.
- **B2B ad abbonamento** per posti, con sconto annuale.
- **Docenti gratis** con verifica istituzionale: è investimento in distribuzione, non ricavo.
### 13.1 Dove avviene l'incasso — vincolo di piattaforma, non preferenza

**Il denaro non può atterrare dentro l'assistente.** Verificato alla fonte il 14 agosto 2026:
l'approvazione alla monetizzazione su ChatGPT «is limited to plugins for **physical goods**
purchases», e il percorso supportato — External Checkout — stabilisce che «Payment, billing, taxes,
refunds, and compliance are handled **entirely on your domain**». Il checkout in conversazione è in
beta privata per «select marketplace partners». Su Claude non esiste alcun rail di pagamento nativo.

Kirchhoff vende crediti per un servizio digitale. **La superficie assistente è la porta d'ingresso;
il dominio proprio è la cassa.** FR-21 e FR-36 sono la cerniera fra le due, SM-11 la misura.

### 13.2 Il rail — un fornitore, due configurazioni

| Flusso | Rail | Perché |
|---|---|---|
| **Italia** — B2C domestico, Studio ai tutor italiani | Pipeline Stripe esistente, ricevute in forfettario | Nessuna IVA transfrontaliera, nessun sovrapprezzo |
| **Estero** — tutto ciò che arriva dalla superficie assistente | **Stripe Managed Payments** (merchant of record) | Trasferisce a Stripe la responsabilità fiscale in 75+ paesi |

**Costo verificato** (pagina prezzi Stripe, tariffe SEE): Managed Payments **+3,5%** sopra le
commissioni standard — 1,5% + 0,25 € su carta standard SEE, 2,8% + 0,25 € su premium. Tutto
compreso: **5,0% + 0,25 €** standard, **6,3% + 0,25 €** premium. Il 6,4% che circola online è la
tariffa statunitense.

Sul listino: Pass Sessione 19,90 € → 1,25 € di commissione, **migliore** dei 1,50 € assunti nelle
unit economics. Pacchetto 10 a 4,90 € → 10,1%, contro il 15,2% di un MoR con quota fissa a 0,50 €.
La differenza sta tutta nella componente fissa, e pesa dove il biglietto è piccolo.

**Paddle e Lemon Squeezy escono dal piano.** L'alternativa «Stripe *oppure* MoR» del documento
sorgente §6.4 non esiste più: Stripe offre entrambi.

`[ASSUMPTION: da confermare col commercialista prima del primo incasso estero — con un merchant of
record il cliente diventa Stripe e non lo studente, il che cambia la natura dell'operazione ai fini
del regime forfettario.]`

`[NOTE FOR PM]` Non verificati, riportati solo da fonti terze: Stripe Billing 0,5–0,8% sul
ricorrente e 15 $ per contestazione. Il secondo pesa sul B2B ad abbonamento.

## 14. Platform

- **Web progressiva, mobile-first**, con accesso alla fotocamera. Nessuna app native (§6).
- **Superficie assistente** per gli host compatibili (§5.6).
- **Pagine pubbliche di esercizi** generate da Varianti proprie, indicizzabili: sono
  contemporaneamente contenuto, demo e artefatto legalmente sicuro.

## 15. Public Surface Contract

La superficie assistente è consumata da host di terzi: le rotture sono osservabili dall'esterno e
non si possono ritirare. Va trattata come contratto pubblico.

- **Superficie minima.** Si espone il numero minimo di operazioni che copre il flusso, non il
  massimo possibile: ogni operazione in più è superficie d'attacco e fonte di confusione per il
  modello chiamante.
- **Ogni risposta con pannello porta anche il proprio riassunto testuale strutturato.** Senza,
  l'assistente non sa cosa l'utente sta guardando (FR-20).
- **Nessuno stato conservato lato pannello.** Lo stato viaggia nel riferimento di sospensione.
- **Il riferimento di sospensione è firmato, legato all'utente, a scadenza breve e monouso.** Un
  riferimento indovinabile espone gli esercizi di altri utenti (FR-8).
- **Idempotenza sui Crediti**: la stessa ripresa non addebita due volte (FR-8, FR-26).
- **Versionamento e deprecazione dichiarati**, con un periodo di sovrapposizione annunciato prima
  di qualunque rottura.
- **Accessibilità del pannello** al pari della superficie web.

## 16. Open Questions

0. 🔴 **Soglie di lancio di VVDR, SER, NED, TVR, VCER, SEC, RRC, VDR.** **Owner-locked** (§27.6 del
   piano master, e «soglie di qualità minima» fra i confini della costituzione). Le metriche sono
   definite in §8; i numeri **non stanno in questo PRD e non vanno inferiti a valle**. Un artefatto
   che li propone è in errore, non in evoluzione. Blocca la dichiarazione di superamento di Gate A,
   **non** la sua costruzione. Vale anche per le soglie d'allarme delle contro-metriche SM-C1…SM-C8.

   > **Due correzioni del 15 agosto.** (a) **SER era stata omessa da questo elenco** mentre §27.6
   > del master la contiene alla lettera — «Soglie VVDR/**SER**/RRC di lancio» — e §8 SM-1 ne fissa
   > i target. Il brief e il piano master divergono davvero su questo punto: il brief tratta i
   > numeri di SER come acquisiti, il master li mette sotto lock. **Le due fonti sono nominate qui
   > invece che risolte in silenzio**, e la scelta è dell'owner. Fino ad allora i target di SM-1
   > restano scritti ma non vincolano un gate. (b) Le sigle `TVR`, `SEC`, `RRC`, `VDR` significavano
   > in §8 cose diverse dal master; dal 15 agosto adottano i significati del master, così che questo
   > rimando a §27.6 torni a puntare alle stesse grandezze. Vedi il riquadro in §8.
1. **Ateneo e corso del primo Profilo curricolare.** 🟡 **Declassata il 15 agosto: bloccante di
   Gate C, non blocco di fase.** Il motivo per cui era blocco di fase — «determina come si annota
   il gold set, e il gold set precede tutto» — è caduto con lo spostamento della foto a Gate C.
   Resta da risolvere **prima dell'annotazione**, che ora non precede più l'MVP. Il kernel di §5.0
   non dipende dal Profilo curricolare.
2. **Marchio "Kirchhoff".** Verifica TMview/UIBM non fatta. Blocca dominio e materiali pubblici.
3. **Numero di Pass di estrazione in produzione.** Tre è il punto di partenza; il valore definitivo
   esce dalla misura sul gold set, non da una scelta a priori.
4. **Periodo esatto di conservazione delle immagini** entro la finestra 24–72 h: da fissare
   bilanciando la possibilità di rivedere l'Anteprima e la minimizzazione.
5. **Soglia operativa del limite di uso equo** sul pass a tempo: 150 è un'ipotesi da validare sul
   consumo reale.
6. **Regime IVA definitivo** — da confermare con il commercialista.
7. **Formati e-learning prioritari** per Studio: quale piattaforma serve davvero al primo cliente
   B2B.
8. ~~Se la baseline dei modelli frontier supera l'85% sul gold set…~~ **Chiusa il 13 agosto 2026**
   per decisione dell'utente, senza misura: i modelli frontier sono ritenuti insufficienti su questo
   compito. Vedi `sprint-change-proposal-2026-08-13.md`.

   > **Correzione del 15 agosto.** La riga proseguiva con «e l'ingresso da foto resta nell'MVP»,
   > citando §7 a conferma. **Era in contraddizione diretta con §7.2**, che dalla v3 sposta la foto
   > e tutta la percezione a Gate C. Un lettore a valle che costruisse da §16 costruirebbe l'MVP
   > sbagliato. La decisione del 13 agosto sui modelli frontier resta chiusa e valida — riguardava
   > la baseline, non la collocazione dell'ingresso. **La foto è fuori MVP.**
9. 🟠 **Corpus e campione di Gate A — due incognite, non una.**
   **(a) Circuiti**: su quanti si esegue il confronto, scelti come, stratificati secondo quale
   criterio. Un corpus di sole reti resistive piccole è esattamente dove il braccio 0 resta quasi
   stabile per conto proprio, cioè dove il gate può uccidere un prodotto valido.
   **(b) Partecipanti**: i bracci sono passati da due a quattro il 15 agosto. **Il disegno è
   entro-soggetti e controbilanciato**, non a quattro gruppi indipendenti: ogni partecipante vede
   più condizioni, su circuiti **equivalenti ma non identici**, con l'ordine controbilanciato a
   quadrato latino (`P1: 0→A→B→C`, `P2: A→B→C→0`, `P3: B→C→0→A`, `P4: C→0→A→B`, …). Il confronto
   diventa *«questa persona capisce meglio A o C?»* invece di *«due persone diverse con capacità
   diverse»*, e la varianza individuale crolla. Il prezzo è apprendimento e trascinamento fra
   condizioni, che è precisamente ciò che i problemi appaiati e il controbilanciamento comprano.
   > **Correzione del 15 agosto.** Qui c'era scritto che «i bracci moltiplicano i partecipanti, non
   > i circuiti». **È il contrario:** con un disegno entro-soggetti i quattro bracci moltiplicano i
   > **circuiti appaiati** — ne servono quattro comparabili per partecipante — e il numero di
   > partecipanti **non cresce linearmente** con i bracci. Q9 deve fissare entrambi i numeri, senza
   > assumere quella proporzionalità.

   Blocca l'**esecuzione** di Gate A, non la sua costruzione.
10. 🟡 **Precedenza fra SM-14 e SM-21.** Se la continuità geometrica migliora e la comprensione
    misurata no, quale prevale. Owner-locked come le soglie.
11. 🟠 **Tetto di tempo o di sforzo su Gate A.** §2 fissa una finestra stagionale che scade a
    gennaio; §7.0 descrive un MVP senza ricavi, senza utenti e senza scadenza. Senza un tetto
    dichiarato — settimane, o una data oltre la quale si decide comunque — le due sezioni non
    convivono, ed è la forma esatta del rischio nominato nell'addendum §G. Non è una soglia di
    qualità: è una decisione di sequenziamento, e resta tua.

## 17. Assumptions Index

> **Riconciliato il 15 agosto.** L'indice conteneva 4 voci a fronte di 6 `[ASSUMPTION]` inline.
> Le due mancanti erano quella di FR-40 e — la più pesante — quella di §7.0: **l'assunzione su cui
> poggia l'intero MVP non era elencata fra le cose che potrebbero essere false.** Sotto ci sono
> tutte, più quella nuova di §12.

- **A-0 — 🔴 Unmarked Preservation Hypothesis.** Gli elementi preservati non ricevono codifica
  visuale automatica dell'essere preservati; la continuità è comunicata dall'assenza di
  cambiamento. **Confermata dall'owner il 15 agosto come regola progettuale madre del kernel, e
  contemporaneamente dichiarata ipotesi forte da falsificare** — non legge percettiva dimostrata
  per Kirchhoff. Collegata a K-0. Da essa discendono FR-38 (campi del `Transform`), FR-47 (quattro
  bracci), FR-50 (classi di stato) e l'intera sezione *Continuità visuale* di `DESIGN.md`. Gate A
  la confronta contro un braccio a invarianti marcati e uno conventional-focus; vincere «perché
  sembra più pulita» non basta. Definizione completa in §7.0.1.
- **§7.0 — Il kill criterion è valutabile senza ambiguità.** È l'assunzione portante del documento:
  se il confronto non è eseguibile, l'MVP non ha criterio d'uscita e §7 perde senso. Al gate del
  15 agosto **non reggeva**; il protocollo di **§7.0.1**, deciso dall'owner lo stesso giorno, la
  rende operativa — baseline equa, `preserve set` derivato dalla trasformazione, misure geometriche,
  A/B cieco con tempo ed errori, decisore nominato. **Resta condizionata a §16 Q9**, il corpus.
  Storia del difetto in `review-kill-criterion.md`.
- **FR-40** — L'MVP con tre trasformazioni produce grafi quasi lineari; il `ProofGraph` entra
  comunque adesso perché migrarci dopo costa più di adottarlo subito.
- **§12** — I periodi di conservazione di 30 giorni, 14 mesi e 6–12 mesi non hanno origine a
  monte: sono proposte di lavoro da confermare prima dell'informativa.
- **§3.2** — Il target di lancio è universitario, età minima 18; l'apertura a 14–17 richiede
  informativa semplificata dedicata ed è rimandata a v2.
- **§13** — L'intermediario di pagamento assume gli obblighi IVA UE per il B2C internazionale,
  mentre la componente italiana e il B2B domestico restano sull'infrastruttura esistente. Da
  confermare con il commercialista.
- **Titolo** — "Kirchhoff" è un titolo di lavoro finché la verifica sul marchio non è fatta.
- **Trasversale** — Il fondatore mantiene l'attività di ripetizioni: finanzia lo sviluppo, fornisce
  il gold set e i primi utenti, ed è il primo cliente Studio. Il sequenziamento del piano assume
  dedizione parziale, non a tempo pieno.
