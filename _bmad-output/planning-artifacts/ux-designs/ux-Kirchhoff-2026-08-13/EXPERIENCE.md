---
name: Kirchhoff
version: 3
description: "Come si comporta Kirchhoff: architettura dell'informazione, stati, interazioni, accessibilita', flussi. L'identita' visiva vive in DESIGN.md."
status: draft
created: 2026-08-13
updated: 2026-08-15
supersedes: "EXPERIENCE v2 (13 ago 2026) — prodotto centrato sull'Anteprima di ricostruzione da foto"
design: ./DESIGN.md
sources:
  - ../../prds/prd-Kirchhoff-2026-08-13/prd.md
  - ../../briefs/brief-Kirchhoff-2026-08-13/brief.md
  - ../../briefs/brief-Kirchhoff-2026-08-13/addendum.md
---

> `DESIGN.md` e `EXPERIENCE.md` sono contratti **pari grado**: il primo possiede *come appare*,
> il secondo *come si comporta*. In caso di conflitto con un mock, un wireframe o un import,
> vincono le spine. I riferimenti `{path.to.token}` puntano al frontmatter di `DESIGN.md`.

## Foundation

> ## Cosa cambia in v3, e perché
>
> La v2 aveva un centro: **l'Anteprima di ricostruzione**, il confronto fra la foto dello studente e
> l'IR ricostruito, e le riceveva il budget di design più alto. In v3 quel centro **non esiste
> nell'MVP**: l'ingresso è strutturato e non c'è nessuna foto da confrontare. Il nuovo centro è
> **il passo** — cosa cambia, cosa resta, l'equazione, la prova — e il nuovo artefatto d'uscita è
> un **`ProofGraph` percorribile**, non una pagina di risposta.
>
> Non è una revoca dell'Anteprima: torna intatta a Gate C, che ora corre in parallelo. È uno
> spostamento del baricentro, e quindi del budget di design.
>
> **Quello che non cambia**, ed è la maggior parte del documento: la voce, la regola *Non
> certificata ≠ Guasto*, il pavimento di accessibilità, il badge che si apre sulla prova, i vincoli
> della superficie assistente. Reggono meglio in v3 di quanto reggessero in v2.

**L'unità di esperienza non è una schermata: è la `ProofSession`.**

Il kernel produce `CircuitIR` + `LayoutIR` + `ProofGraph` + `ProofCertificates` + capacità di
interazione (PRD FR-48). **Nessuna superficie la possiede**; ogni superficie la presenta con la
densità che può permettersi. Progettare prima la sessione e poi gli adapter è ciò che impedisce il
fork che FR-45 vieta.

| Adapter | Densità | Cosa può fare |
|---|---|---|
| **PWA** | piena, schermo intero | Tutto: `proofgraph-rail` sempre visibile, `beforeafter-toggle`, ispezione di ogni elemento |
| **`ProofReplay`** — superficie MCP compatta | ridotta, larghezza imprevedibile | Prima/dopo, selezione di un elemento, certificato, navigazione nel grafo. Nient'altro |
| **Ardesia** (successivo) | piena, canvas ricco | La stessa `ProofSession` montata nativamente, senza duplicare kernel, auth, shell o simulatore |

**La `ProofSession` deve funzionare senza MCP Apps.** Il supporto varia fra host e OpenAI Apps SDK
e MCP Apps non sono la stessa runtime (PRD FR-48). Il degrado a superficie non interattiva — passi
come immagini semantiche più il testo strutturato — è un **percorso previsto e progettato**, non un
guasto. Una `ProofSession` che esiste solo dove l'iframe interattivo funziona è un prodotto con una
dipendenza che non controlliamo.

**Le superfici di Gate A sono un sottoinsieme.** L'MVP che deve emettere il verdetto non ha
account, pagamenti, cronologia né editor: ha il caricamento di un esercizio strutturato, la
sessione, e il protocollo A/B. Il resto di questo documento descrive **il prodotto**; la sezione
*Superfici di Gate A* dice quali di esse esistono prima del verdetto.

**Form-factor: tre superfici, un solo motore di esperienza.**

| Superficie | Chi | Contesto d'uso | Vincolo dominante |
|---|---|---|---|
| **Web PWA, mobile-first** | Solve (B2C) | Telefono in mano, di notte, sotto scadenza | Latenza percepita e leggibilità dei disegni a 360 px |
| **Pannello assistente** | Solve dentro un assistente | Dentro una conversazione di terzi | Sandbox: niente stato locale, niente cookie |
| **Studio, desktop** | Studio (B2B) | Scrivania, sessione lunga, lavoro ripetitivo | Densità e operazioni in blocco |

Nessun sistema di UI di terze parti: i componenti sono propri, perché i due elementi centrali —
l'Anteprima con l'ancoraggio di provenienza e il pannello dei residui — non esistono in nessuna
libreria. Il resto (campi, pulsanti, dialoghi) segue convenzioni di piattaforma senza
personalizzazione.

**Il paradosso da progettare, non da nascondere:** l'utente arriva in emergenza e vuole una
risposta subito, ma il prodotto gli chiede di confermare la ricostruzione prima di risolvere.
Quel passo non è attrito da minimizzare fino a farlo sparire — è il momento in cui nasce la
fiducia, ed è la sorveglianza umana richiesta dalla conformità. Va reso **veloce**, non
**opzionale**: un solo tocco quando non c'è nulla da correggere.

## Information Architecture

Le superfici, e la journey che ci atterra:

```
ProofSession (PWA) — il centro del prodotto in v3
├── Scelta esercizio (raccolta controllata)  ← KF-0 inizio · MVP
├── Sessione di prova                        ← KF-0 · LA superficie centrale · MVP
│   ├── Passo corrente                       ← KF-0 · sei campi, disegno incluso
│   │   ├── Prima ↔ Dopo                     ← KF-0 climax
│   │   ├── Provenienza di un elemento       ← KF-0 · «R34 da cosa deriva?»
│   │   └── «Perché posso farlo?»            ← KF-0 · terminali, precondizioni, formula, certificato
│   ├── ProofGraph rail                      ← KF-0 · sempre visibile, percorribile avanti e indietro
│   └── Pannello dei residui                 ← aperto dal badge (prova della soluzione)
├── Non certificata                          ← KF-3 · superficie propria, non un errore · MVP
├── Export SVG/PDF con provenienza           ← MVP (art. 50, non retrofittabile)
└── Protocollo A/B di Gate A                 ← KF-A · superficie di ricerca, non di prodotto · MVP

Solve completo (PWA) — dopo Gate A, e in parallelo su Gate C
├── Ingresso / carica foto                   ← UJ-1 inizio · Gate C
│   └── Selezione esercizio                  ← UJ-1 edge case (foto con 2 esercizi)
├── Anteprima di ricostruzione               ← UJ-1, UJ-7 · Gate C · centro del percorso foto
│   ├── Domanda mirata (0–2 giri)            ← UJ-2
│   └── Editor del circuito                  ← UJ-2 edge case · fuori Gate A per decisione owner
├── Modalità Studio                          ← UJ-4 · Gate B
├── Cronologia
└── Account · Crediti · Dati e consensi      ← nessun incasso prima del verdetto

Studio (desktop)
├── Banco esercizi                         ← UJ-5
├── Sorgente → Generazione varianti        ← UJ-5
│   └── Vincoli di generazione
├── Rassegna varianti + Fogli soluzione    ← UJ-5
├── Profili curricolari                    ← UJ-6
└── Tenant · posti · export

Pubblico
├── Landing                                ← UJ-6 ingresso
├── Pagine esercizi (Varianti proprie)
├── Come funziona la verifica              ← UJ-6 · pagina tecnica, non marketing
├── Policy di uso accademico               ← UJ-6
└── Programma docenti                      ← UJ-6 climax
```

**Chiusura delle superfici.** Ogni bisogno dichiarato nel PRD atterra su una superficie, e ogni
superficie è raggiunta da almeno una journey. Due note di chiusura:

- **"Non certificata" è una superficie, non uno stato d'errore di un'altra.** Ha un proprio
  indirizzo, è condivisibile, e sopravvive al ricaricamento. Se fosse un banner sopra la
  Soluzione, il prodotto starebbe dicendo "ecco la soluzione, ma…" — che è esattamente ciò che
  non fa.
- **Il pannello dei residui non è una pagina.** Vive dentro la Soluzione, aperto dal badge. È la
  prova a portata di tocco; spostarlo altrove lo renderebbe un documento da cercare.
- **v3: non esiste una superficie «Soluzione».** C'era in v2 e portava «passi + disegni» come suo
  contenuto. In v3 la sessione **è** il prodotto e il risultato numerico è l'ultimo nodo del
  `ProofGraph`, non una pagina che lo riassume. Una schermata «ecco la risposta, e sotto i
  passaggi» rimetterebbe i disegni nel ruolo di allegato, che è la categoria da cui il prodotto
  esce.
- **Il `proofgraph-rail` non è una barra di avanzamento.** Un avanzamento si guarda mentre si
  aspetta; il rail si **usa** — avanti, indietro, salta a un passo, torna. Se durante il test A/B
  gli studenti non lo toccano mai, il rail ha fallito e va riprogettato, non spiegato meglio.

**Superfici di Gate A.** Prima del verdetto esistono solo: scelta esercizio, sessione di prova, Non
certificata, export, protocollo A/B. **Non esistono**: account, Crediti, pagamenti, cronologia,
editor, Studio, superfici pubbliche. Ogni superficie costruita prima del verdetto è lavoro a
rischio di essere buttato (PRD §7.0), e questa lista è il modo in cui la UX dichiara di averlo
capito.

## Voice and Tone

Il registro è quello di un tecnico competente che non promette più di quanto può dimostrare.
Diretto, non brusco. Mai entusiasta.

**Regole di microcopy:**

1. **Il sistema dice cosa ha fatto, non quanto è bravo.** "Ho letto R8 come 30 Ω" — non "Ho
   identificato con successo tutti i componenti".
2. **L'incertezza si dichiara in prima persona e con l'oggetto preciso.** "Non sono sicuro del
   valore di R8" — non "Rilevata possibile ambiguità".
3. **Il Rifiuto non si scusa e non allarma.** "Non riesco a certificare questa soluzione: i due
   metodi divergono sul ramo C–GND. Non ti mostro un numero di cui non posso rispondere." La
   frase finale è la promessa del prodotto, ripetuta nel momento in cui costa qualcosa dirla.
4. **Mai "purtroppo", mai "ops", mai punti esclamativi.**
5. **I numeri non si arrotondano nel testo** se non sono arrotondati nel calcolo. Il testo cita
   il risultato, non lo riformula.
6. **Le domande sono chiuse quando possono esserlo.** "R8: 20 Ω o 30 Ω?" — non "Puoi verificare
   il valore di R8?".
7. **La dichiarazione d'uso dell'IA è in italiano piano**, non in gergo normativo: *"Kirchhoff
   usa intelligenza artificiale per leggere il circuito. I calcoli sono verificati
   automaticamente."*

**Vocabolario vincolato.** I termini del Glossario del PRD sono anche i termini dell'interfaccia:
*Anteprima*, *Verificata*, *Non certificata*, *residui*, *passo*, *Variante*, *Foglio soluzione*,
*Credito*. Nessun sinonimo in UI — "controllo" per "verifica", o "esercizio" per "Variante",
rompono la corrispondenza fra ciò che l'utente legge e ciò che la documentazione spiega.

**Parole vietate:** "magia", "istantaneo", "perfetto", "garantito al 100%", "IA avanzata",
"potenziato dall'IA". L'ultima coppia perché non differenzia; le altre perché sono affermazioni
che il prodotto non può dimostrare.

## Component Patterns

Comportamento; l'aspetto è in `DESIGN.md.Components`.

### Il kernel — v3

**Passo.** Sei campi, sempre gli stessi, sempre nello stesso ordine: `BEFORE · ACTION · AFTER ·
EQUATION · CERTIFICATE · PROVENANCE` (PRD FR-39). L'ordine di **comparsa** però non è l'ordine dei
campi: prima si accende il sottografo interessato sul circuito, poi arriva l'azione, poi
l'equazione accanto al sottografo, poi il certificato. **Nessun passo si apre con un paragrafo.**
Un passo a cui manca `CERTIFICATE` non è un passo incompleto da mostrare con un avviso: non è un
passo, e non compare.

**La gerarchia della comprensione.** `Circuito > trasformazione > equazione > certificato`. **Non**
`circuito → una barra laterale che spiega cosa è successo`. La barra serve all'ispezione
approfondita, mai alla comprensione di base: **se il passaggio si capisce solo leggendo la barra
laterale, il kernel visuale ha fallito**, e nessun miglioramento del testo lo ripara. È il criterio
con cui si giudica ogni mock prima di portarlo a un partecipante.

**Prima ↔ Dopo.** Due stati, commutabili all'infinito, senza costo e senza conferma. La
commutazione è `{motion.instant}` perché serve al confronto ripetuto, non alla scoperta: un
utente che preme cinque volte sta capendo, non sbagliando. Nel passaggio, ciò che appartiene a
`preserve` **non si muove**; ciò che cambia si trasforma sul posto. Un elemento conservato che si
sposta anche di poco è un difetto di prodotto, non di rendering — è precisamente la cosa che
Gate A misura.

**Provenienza di un elemento.** Toccando `R34` il sistema mostra da quali elementi deriva;
toccando `A` o `B`, la continuità del nodo attraverso il passo. In v2 questa interazione puntava
all'**immagine sorgente**; in v3 punta al **passo precedente**. Stessa primitiva — *mostra da dove
viene* — su un referente diverso. Quando Gate C arriva, entrambi i referenti coesistono e
l'interazione non si sdoppia.

**«Perché posso farlo?».** Risponde con quattro cose e solo quelle: terminali coinvolti,
precondizioni della Trasformazione, formula, certificato. **Non genera una spiegazione**: ogni
elemento della risposta è un campo del passo già calcolato. È la differenza fra un tutor che
argomenta e un sistema che mostra le proprie carte, ed è verificabile — un testo che non
corrisponde a un campo è un difetto (PRD FR-13, FR-49).

**`ProofGraph` rail.** Sempre visibile, percorribile avanti e indietro, con il nodo corrente
marcato. Supporta diramazione e ricongiungimento fin da subito, anche se l'MVP con tre
trasformazioni produce catene quasi lineari: la struttura è quella che sarà, non quella che basta
oggi (PRD FR-40).

**`ProofReplay`** — la stessa sessione dentro un host conversazionale. Porta prima/dopo, selezione
di un elemento, certificato, navigazione. **Non porta**: rail espanso, ispezione multipla,
export. Il criterio non è «cosa ci sta», è **cosa resta comprensibile a 320 px di larghezza**.
Tutto ciò che non ci sta rimanda alla PWA con un collegamento, mai con una versione degradata che
finge di essere completa.

### Il percorso foto — Gate C, in parallelo

**Anteprima di ricostruzione.** Due viste in confronto: immagine sorgente e ricostruzione.
Toccando un componente in una vista si accende il `provenance-anchor` nell'altra — il legame è
bidirezionale, perché l'utente può partire da entrambi i lati ("cos'è questo nel mio foglio?" e
"da dove viene questo valore?"). Un solo controllo primario: **Confermo**. Il secondario,
**Correggi**, apre l'editor. Nessun terzo controllo.

**Badge di stato.** Toccabile su entrambi gli stati. Su *Verificata* apre il pannello dei
residui; su *Non certificata* apre la diagnosi. Un badge che non si apre sarebbe
un'affermazione — quello che il prodotto vende è la possibilità di controllare.

**Pannello dei residui.** Cinque righe, sempre le stesse cinque, sempre nello stesso ordine:
KCL, KVL, potenza, accordo fra metodi, coerenza fisica. Ogni riga: nome del controllo, valore del
residuo in cifre tabulari, esito. Ordine costante e non riordinabile: la ripetizione è ciò che
rende il pannello leggibile a colpo d'occhio dalla seconda volta in poi.

**Domanda mirata.** Ritaglio ingrandito in cima — l'immagine viene prima della domanda, perché
l'utente decide guardando il proprio foglio, non leggendo. Alternative come scelte grandi e
distinte, campo libero sempre in coda e sempre presente. Una domanda per volta, mai un modulo con
tre ambiguità.

**Passo della soluzione.** Nome della Trasformazione, formula letterale, sostituzione numerica,
disegno risultante. Il disegno non è un allegato: è metà del passo. Se un passo non ha disegno,
non è un passo — è una riga di calcolo e va fusa con quello precedente.

**Editor del circuito.** Non è un CAD. Modifica di ciò che il sistema ha già ricostruito: valori,
tipi, collegamenti, polarità, grandezze richieste. Ogni modifica manuale resta marcata come tale
nell'IR e visibile nell'Anteprima, così l'utente vede cosa ha cambiato lui e cosa ha letto il
sistema.

**Rassegna Varianti (Studio).** Tabella con esito di verifica per riga. Le Varianti scartate
perché non verificate sono **mostrate**, non nascoste: un generatore che consegna 12 su 15 senza
dirlo è un generatore di cui non ci si fida.

## State Patterns

Gli stati che contano, e cosa vede l'utente in ciascuno.

| Stato | Cosa vede | Regola |
|---|---|---|
| **Caricamento** | Progresso a fasi con etichette reali ("normalizzo l'immagine", "leggo il circuito", "controllo la rete", "risolvo", "verifico") | Le etichette sono lo stadio vero, non decorazione. È l'unico modo di rendere accettabili 45 secondi. |
| **Selezione esercizio** | Riquadri sui candidati, scelta esplicita | Il sistema non sceglie mai e non fonde mai (FR-1) |
| **Attesa di conferma** | Anteprima, un tocco | Stato terminale finché l'utente non agisce. Nessun timeout, nessun auto-avanzamento. |
| **Domanda aperta** | `question-card`, giro 1 o 2 di 2 | Il contatore è visibile: sapere che finisce cambia la disponibilità a rispondere. |
| **Degrado all'editor** | Editor precaricato + spiegazione | "Ho ancora dei dubbi che non riesco a chiudere con una domanda. Sistemali direttamente." |
| **Verificata** | Soluzione + `badge-verified` + residui a un tocco | L'unico stato in cui si vedono numeri di risultato |
| **Non certificata** | Superficie propria, diagnosi, opzioni, **nessun numero di risultato** | Non si mostra il risultato "solo per curiosità": mostrarlo annullerebbe il gate |
| **Guasto** | `{colors.fault}`, causa, ritenta | Distinto dal precedente per colore, icona e parole. Un guasto è colpa nostra; una non-certificazione è onestà. |
| **Credito esaurito** | Saldo, opzioni | Mostrato **prima** dell'elaborazione, mai dopo aver fatto lavorare l'utente |
| **Vuoto** | Cronologia vuota, banco vuoto | Un esempio reale caricabile con un tocco, non un'illustrazione |
| **Offline** | Le soluzioni già ottenute restano leggibili | La PWA conserva gli artefatti; l'elaborazione richiede rete e lo dice |

**La regola che governa tutta la tabella:** *Non certificata* e *Guasto* non devono mai
assomigliarsi. Sono le due situazioni in cui l'utente non ottiene ciò che voleva, e sono
opposte nel significato — una è il sistema che funziona, l'altra è il sistema che è rotto. Colore
(`{colors.suspended}` contro `{colors.fault}`), icona e parole devono distinguerle tutte e tre
insieme.

## Interaction Primitives

- **Un tocco per confermare.** Quando non ci sono correzioni, il percorso dall'Anteprima alla
  Soluzione è un solo tocco. È il vincolo che rende sostenibile un passo obbligatorio.
- **Tocco su un valore = mostra da dove viene.** In ogni punto (Anteprima, passo, soluzione),
  toccare una quantità accende il `provenance-anchor` sull'immagine sorgente.
- **Tocco sul badge = mostra la prova.** Sempre disponibile, mai dietro un menu.
- **Massimo due giri di domande.** Il contatore è visibile. Il terzo giro non esiste: si degrada
  all'editor.
- **Nessuna azione distruttiva senza annullamento.** Cancellare un esercizio o una Variante è
  reversibile per la durata della sessione.
- **Nessun auto-avanzamento.** Nessuno stato prosegue da solo dopo un timeout. In modalità Studio
  il passo successivo non si rivela mai da sé.
- **Movimento minimo.** Le transizioni servono a mantenere la continuità spaziale (il pannello
  dei residui esce dal badge che l'ha aperto). Nessuna animazione celebrativa. `prefers-reduced-
  motion` rimuove ogni transizione non essenziale.

## Accessibility Floor

Non negoziabile: i clienti istituzionali lo chiedono e il pubblico universitario lo include.
Obiettivo dichiarato **WCAG 2.2 AA** su tutte e tre le superfici, pannello assistente compreso.

- **Ogni disegno di circuito ha un'alternativa testuale** che descrive la topologia risultante —
  non "schema del circuito", ma la struttura ("R1 in serie con il parallelo di R2 e R3, fra il
  nodo A e massa"). È un requisito di prodotto (FR-15), non una cortesia: uno studente
  ipovedente che studia elettrotecnica esiste, e la topologia è l'informazione.
- **L'intero flusso è percorribile da tastiera**, Anteprima ed editor inclusi. L'ordine di
  tabulazione segue l'ordine di lettura; il focus è sempre visibile e non è mai portato dal solo
  colore.
- **Nessuno stato è portato dal solo colore.** Verificata e Non certificata si distinguono per
  icona, etichetta e forma prima che per tinta. Verifica operativa: la schermata resta
  interpretabile in scala di grigi.
- **Contrasto** conforme AA su testo e componenti; le regole sottili di `DESIGN.md` sono
  decorative e non portano informazione.
- **Le formule sono accessibili come matematica**, non come immagini con testo alternativo
  generico.
- **Bersagli di tocco** almeno 44 × 44 px, incluse le alternative nelle Domande mirate.
- **Dimensione minima del testo nei disegni**: `{typography.label-drawing}` a 11 px effettivi.
  Un disegno che scenderebbe sotto va ricomposto, non rimpicciolito.
- **Nessun limite di tempo** su nessuna interazione, salvo la scadenza del riferimento di
  sospensione — che è di sicurezza e produce un messaggio con ripartenza, non una perdita.

## Responsive & Platform

- **< 768 px (default di progetto).** Colonna singola. Disegni interi entro 360 px senza
  scorrimento orizzontale della pagina.
  **v3 — la sessione di prova.** Il circuito prende la maggior parte dell'altezza utile; il
  `proofgraph-rail` si contrae a indicatore e si espande a richiesta; l'`equation-anchor` resta
  **accanto** al sottografo anche qui, riducendo la scala del disegno prima di staccare
  l'equazione. Se l'equazione va sotto, il passo torna a essere «disegno più spiegazione» ed è
  esattamente ciò che il prodotto non è. `[NOTE FOR UX: quale delle tre cede per prima è la
  domanda aperta 7 — questa è l'ipotesi di lavoro, non una decisione presa.]`
  Il controllo *Prima ↔ Dopo* è **pollice-raggiungibile**: si preme molte volte di seguito, e in
  alto a destra sarebbe scomodo esattamente nel momento in cui serve di più.
- **≥ 768 px.** I due stati del passaggio possono stare **affiancati** invece che commutati — ma
  il controllo *Prima ↔ Dopo* **resta**: affiancare mostra la differenza, commutare la fa
  percepire, e sono due modi diversi di capire. Nel protocollo A/B i due bracci sono sempre
  commutati e mai affiancati, per non introdurre un confronto che il prodotto reale non offre.
  **Gate C, quando arriva:** Anteprima a due colonne affiancate, come in v2.
- **Studio.** Solo desktop. Densità maggiore, tabelle, azioni in blocco. Non è una versione
  ristretta della PWA: è un'altra postura di lavoro.
- **Pannello assistente.** Larghezza imprevedibile e generalmente stretta. Progettato per la
  larghezza minima; nessuna dipendenza dall'altezza del contenitore.
- **Modalità scura** pari grado, non secondaria: gran parte dell'uso è notturna.
- **Stampa.** La Soluzione ha un foglio di stile di stampa: molti studenti stampano. Marcatura di
  provenienza inclusa e non rimovibile via CSS.

## Vincoli della superficie assistente

Sezione inventata perché il prodotto porta un concern che nessuna sezione standard nomina: una
superficie di terzi con regole proprie.

- **Nessuno stato locale.** Il pannello non conserva niente fra un giro e l'altro. Tutto ciò che
  serve viaggia nel riferimento di sospensione. Progettare come se il pannello venisse distrutto
  e ricreato a ogni interazione — perché può accadere.
- **L'assistente non vede il pannello.** Ogni risposta che ne alimenta uno porta **anche** un
  riassunto testuale strutturato di ciò che l'utente sta guardando. Senza, l'assistente non sa
  cosa è stato confermato e non può ragionarci. È il vincolo più facile da dimenticare e il più
  visibile quando manca: l'utente conferma, e l'assistente risponde come se non fosse successo
  nulla.
- **Parità funzionale sui gate.** Anteprima obbligatoria, tetto di due giri, gate di verifica e
  Rifiuto valgono identici. Nessuna scorciatoia "perché è dentro una chat".
- **La dichiarazione d'uso dell'IA è presente anche qui**, dentro il pannello.
- **Il collegamento dell'account si propone dopo la prima Soluzione consegnata**, mai prima: un
  invito a registrarsi prima di aver dato valore è la ragione per cui i canali di terzi portano
  uso e non portano clienti.
- **Accessibilità pari** a quella della PWA. La sandbox non è un'attenuante.

## Protocollo A/B di Gate A

Sezione inventata, e l'unica di questo documento che descrive una superficie **di ricerca** invece
che di prodotto. Esiste perché il verdetto che decide se Kirchhoff continua si raccoglie qui, e un
protocollo mal progettato produce un numero che non significa niente. Normativa: PRD §7.0.1.

**Cosa vede il partecipante.** Lo stesso identico passaggio, reso in **quattro** modi. Non gli si
dice quale sia quale, né che uno di essi sia «il nostro». L'ordine è controbilanciato fra
partecipanti e registrato per sessione.

| Braccio | Rendering | Domanda |
|---|---|---|
| **0** | ri-layout globale indipendente, stesso renderer, nessuna conoscenza di `Layout(Cₖ)` | la continuità di posizione serve? |
| **A** | persistente, segnale solo sul delta | **A-0** |
| **B** | persistente + codifica leggera «unchanged» sui preservati | marcare aiuta o disturba? |
| **C** | persistente + attenuazione del resto — il pattern UI comune | il pattern comune fa meglio? |

I quattro stanno su **un asse solo**, non su due incrociati: C presuppone il layout persistente,
perché si può attenuare il resto solo se il resto è ancora lì. Un disegno fattoriale darebbe sei
celle e non finirebbe. **B e C sono varianti di rendering dello stesso `LayoutIR`** — se
richiedessero un layout diverso, il confronto misurerebbe due cose insieme.

**Il disegno è entro-soggetti e controbilanciato**, non a quattro gruppi indipendenti. Ogni
partecipante vede più condizioni, su **circuiti equivalenti ma non identici**, con l'ordine a
quadrato latino:

```
P1: 0 → A → B → C        P3: B → C → 0 → A
P2: A → B → C → 0        P4: C → 0 → A → B
```

Il confronto diventa *«questa persona capisce meglio A o C?»* invece di *«due persone diverse con
capacità diverse»*, e la varianza individuale crolla. Il prezzo è apprendimento e trascinamento fra
condizioni — che è esattamente ciò che i problemi appaiati e il controbilanciamento comprano.
**I quattro bracci moltiplicano i circuiti appaiati, non i partecipanti.**

**Le sei misure**, cinque oggettive e una soggettiva:

| # | Misura | Tipo |
|---|---|---|
| 1 | Tempo per indicare **cosa è cambiato** | tempo |
| 2 | Errori nell'indicare **cosa è rimasto uguale** | errori — **è la misura che parla direttamente ad A-0** |
| 3 | Capacità di **ricostruire `Cₖ`** dopo aver visto `Cₖ₊₁` | errori |
| 4 | Tempo per trovare i **nodi terminali** della trasformazione | tempo |
| 5 | Errori nell'**identità dei componenti** | errori |
| 6 | Preferenza soggettiva | **secondaria**, in coda |

La preferenza si chiede **dopo** le cinque oggettive, mai prima: in testa trasformerebbe un test di
comprensione in un test di gradimento. **Un braccio che vince solo sulla 6 non ha vinto.** Se il
braccio A perde sulla misura 2, A-0 è abbattuta a prescindere dal resto. Alimentano SM-21.

**Regole che tengono in piedi l'esperimento** — violarne una invalida la sessione, non la peggiora:

- **Nessuna differenza estetica fra i bracci.** Stessi token, stesso renderer, stessi vincoli
  (`DESIGN.md.Continuità visuale`). Se A è più bello, non si sta più misurando la continuità.
- **Nessun marchio, nessun colore di prodotto, nessuna parola «Kirchhoff»** nella superficie di
  test.
- **Nessun aiuto, nessun suggerimento, nessun tempo limite.** Un partecipante bloccato è un dato,
  non un problema da risolvere.
- **`preserve` è calcolato dal sistema**, mai dichiarato da chi produce il rendering (PRD FR-47).
  Il compito 2 verifica dal lato umano esattamente ciò che VCER verifica dal lato geometrico: se le
  due misure divergono, la divergenza è il risultato più interessante della sessione.
- **Il fondatore non somministra le proprie sessioni.** È il primo expert evaluator, non l'unico
  campione, e non può essere anche lo sperimentatore sui partecipanti esterni.

**Accessibilità.** Il protocollo eredita il pavimento intero. Un partecipante che usa lettore di
schermo esegue i tre compiti sull'**alternativa testuale della topologia**, che è la forma in cui
la continuità gli arriva: se l'alternativa testuale non rende leggibile cosa è cambiato, il
prodotto ha un difetto che il test grafico non vedrebbe mai.

## Key Flows

> **v3: KF-0 è il flusso primario.** I sette che seguono restano validi e descrivono il prodotto
> completo, ma **cominciano tutti da una foto** e nessuno di essi copre l'MVP. KF-0 è l'unico che
> Gate A deve far funzionare, ed è la journey dettata dall'owner il 15 agosto. KF-1…KF-7 tornano
> centrali quando Gate C atterra.

**KF-0 — Elena segue una riduzione senza perdere il circuito.** *(flusso primario v3 · realizza
FR-37…FR-43, FR-49)*

Elena, secondo anno di Ingegneria, sta preparando Elettrotecnica. Conosce serie, parallelo, Ohm e
partitore. Il suo problema non è la formula: è che quando il libro ridisegna il circuito dopo una
riduzione, **non ritrova più dov'era**. Non fotografa niente e non disegna niente: sceglie un
esercizio da una raccolta controllata.

1. Apre un esercizio strutturato: una rete DC con una sorgente, e `R3` e `R4` in parallelo fra i
   nodi `A` e `B`. Il target è una tensione. Nessun caricamento, nessuna attesa di lettura.
2. **`C₀` occupa quasi tutta la superficie utile.** Elena si costruisce la mappa: dov'è la
   sorgente, dove sono i nodi, dove il ramo che le interessa. Questo momento non è un'introduzione:
   è ciò che rende possibile tutto il resto, e ha un costo in pixel che va pagato.
3. Il sistema individua `R3 ∥ R4 → R34`. **`R3` e `R4` si accendono nel circuito** e i terminali
   `A-B` diventano espliciti. **Al resto non succede niente** — non si attenua, non si spegne, non
   si sposta. Non è ancora comparso un solo carattere di testo.
4. **PRIMA.** Elena guarda. Il resto del circuito è **identico**: il messaggio non è «queste sono le
   cose che non ci interessano», è «il circuito è ancora questo, guarda solo ciò che cambia».
5. **AZIONE.** L'equazione dell'equivalente compare in `equation-anchor` **accanto** al sottografo,
   collegata da una linea. Non sotto il disegno.
6. **DOPO — il climax.** `C₁`. `R3` e `R4` diventano `R34`, sempre fra `A` e `B`. Tutto il resto
   non si è mosso di un pixel. Elena pensa *«quelle due sono diventate questa»* — non *«mi hanno
   mostrato un circuito nuovo»*. **È l'intera scommessa del prodotto, in un istante di mezzo
   secondo.** Se qui pensa la seconda cosa, Gate A ha la sua risposta.
7. Tocca `R34`: vede da cosa deriva. Tocca `A`: vede che è lo stesso `A`. Preme *Prima ↔ Dopo* tre
   volte di fila per fissare il cambiamento. Chiede *«perché posso farlo?»*: terminali,
   precondizione, formula, certificato. Nessuna prosa.
8. **Il certificato non è il numero.** Il passo porta `certificate-chip` perché trasformazione,
   equazione **e rappresentazione grafica** sono state verificate — il rendering è stato riparsato
   e confrontato col `CircuitIR` atteso. Se il round-trip fallisse, Elena vedrebbe un passo marcato
   come errore, mai un passo certificato.
9. Stesso meccanismo per `C₁ → C₂`. Il catalogo resta a tre: serve dimostrare che il meccanismo
   **generalizza oltre un trucco**, non che copre l'elettrotecnica.
10. **Non arriva a una pagina di risposta.** Arriva a `C₀ → T₁ → C₁ → T₂ → C₂`, percorribile avanti
    e indietro. La soluzione è **conseguenza** della catena, non un risultato con i disegni
    allegati.

*La promessa che questo flusso mette alla prova:* **«quando il circuito cambia, riesco a vedere
esattamente cosa è cambiato senza perdere mentalmente il circuito che stavo guardando.»**

**KF-1 — Marco, 23:40, dalla foto alla certezza.** *(realizza UJ-1 · Gate C)*

1. Apre da mobile web, non autenticato. La barra di dichiarazione è già visibile.
2. Scatta la foto storta di un esercizio manoscritto.
3. Il progresso a fasi mostra cosa sta succedendo, con etichette reali.
4. **Anteprima**: la sua foto a sinistra, la ricostruzione a destra. Tocca R3 nella ricostruzione;
   si accende il riquadro sulla sua foto.
5. **Climax** — riconosce il proprio circuito e tocca *Confermo*. È il momento in cui capisce che
   il sistema ha *letto* il suo foglio, non indovinato.
6. La Soluzione arriva con `badge-verified`. Tocca il badge: cinque residui in colonna, tutti
   sotto soglia.
7. Resta con la soluzione, il procedimento ricopiabile, due Crediti di prova.

**KF-2 — Giulia risolve l'ambiguità senza uscire dal flusso.** *(realizza UJ-2)*

1. Carica; il sistema non è d'accordo con se stesso su R8.
2. **`question-card`**, giro 1 di 2: ritaglio ingrandito su R8 in cima, poi "20 Ω" / "30 Ω" /
   campo libero.
3. **Climax** — guarda il proprio foglio, sceglie 30 Ω, e il sistema **riprende da dove era**
   invece di ripartire. La correzione compare nell'Anteprima marcata come sua.
4. Conferma; nessun Credito consumato due volte.

**KF-3 — Il sistema rifiuta, e Marco decide se fidarsi.** *(realizza UJ-3)*

1. Transitorio con due commutazioni. Estrazione e validazione passano.
2. I due percorsi risolutivi divergono oltre tolleranza.
3. **Climax** — invece della soluzione, la superficie *Non certificata*: cosa è fallito (accordo
   fra metodi), dove (ramo C–GND), e la frase che è la promessa del prodotto detta nel momento in
   cui costa: *"Non ti mostro un numero di cui non posso rispondere."*
4. Tre opzioni: aprire l'editor, segnalare, scaricare la ricostruzione. **Nessun Credito
   addebitato**, e lo dice.
5. Marco non ottiene ciò che voleva. Ottiene la ragione per tornare.

**KF-4 — Sara studia invece di copiare.** *(realizza UJ-4)*

1. Carica e sceglie modalità Studio.
2. Primo passo mostrato. Poi il sistema si ferma: "quale Trasformazione applicheresti adesso?"
3. Sara risponde "serie". È sbagliato.
4. **Climax** — prima di rivelare, il sistema le mostra *perché* non sono in serie: i due
   resistori condividono un nodo con un terzo ramo, evidenziato sul disegno.
5. Arriva in fondo avendo scoperto ogni passo dopo averci provato. Nessun punteggio, nessuna
   percentuale, nessun registro: non si valuta nessuno.

**KF-5 — Davide prepara dodici simulazioni in venti minuti.** *(realizza UJ-5)*

1. Studio, desktop. Carica un esercizio dal proprio archivio LaTeX nel banco.
2. Imposta 12 Varianti, vincola i valori alla serie E24 e il risultato a un intervallo leggibile.
3. La rassegna mostra le Varianti generate **e quelle scartate perché non verificate**, con il
   motivo.
4. **Climax** — dodici testi diversi, dodici soluzioni verificate, dodici Fogli soluzione con
   checksum, esportati in un colpo. Il LaTeX compila al primo tentativo.

**KF-6 — La prof.ssa Ferrari passa da censore a distributore.** *(realizza UJ-6)*

1. Arriva dal footer di provenienza su un elaborato, pronta a vietare lo strumento.
2. Trova, in ordine e senza cercarle: la policy di uso accademico, la modalità Studio come default
   educativo, e la pagina "Come funziona la verifica" — tecnica, non promozionale.
3. **Climax** — il programma docenti: accesso gratuito a Studio con email istituzionale, nessun
   obbligo. Genera sei Varianti dal proprio tema d'esame dell'anno scorso e funzionano.
4. Non scrive il post arrabbiato. Chiede come configurare le convenzioni di segno del suo corso —
   e con quella domanda il suo Profilo curricolare entra nel sistema.

**KF-7 — Marco risolve dentro la conversazione.** *(realizza UJ-7)*

1. Sta già parlando con un assistente. Allega la foto e chiede di risolverla.
2. Nel pannello in conversazione compaiono foto, Anteprima e conferma. La dichiarazione d'uso
   dell'IA è presente anche qui.
3. **Climax** — Marco conferma nel pannello, e l'assistente *sa* cosa ha confermato, perché ha
   ricevuto il riassunto testuale strutturato. Può ragionarci sopra invece di proseguire alla
   cieca.
4. La Soluzione verificata torna in conversazione. Solo adesso compare l'invito a collegare un
   account.

---

## Domande aperte (UX)

1. **Rendering delle formule**: composizione matematica vera contro immagini. Vincola
   accessibilità e stampa. `[ASSUMPTION: composizione matematica accessibile — le immagini
   renderebbero le formule inaccessibili e non selezionabili.]`
2. **Progresso a fasi con etichette reali**: rischia di esporre fallimenti intermedi che il
   sistema recupererebbe da solo. Da provare con utenti veri.
3. **Densità della modalità Studio**: quanti passi per schermata prima che la rivelazione
   progressiva diventi frustrante.
4. **Foto con più esercizi**: la selezione deve essere un ritaglio interattivo o un elenco di
   candidati? Dipende dal tasso reale di foto multi-esercizio, che il gold set misurerà.
5. **Mock delle schermate chiave non prodotti** in questa esecuzione (Fast path). Le superfici
   che ne trarrebbero di più in v3: **la sessione di prova a metà passaggio** (è dove si vince o si
   perde Gate A), `ProofReplay` alla larghezza minima, e la superficie del protocollo A/B.

**Aperte in v3 — 15 agosto**

6. ✅ **Chiusa il 15 agosto — è diventata `A-0`, Unmarked Preservation Hypothesis.** Confermata
   dall'owner come regola progettuale madre del kernel e insieme come **ipotesi forte da
   falsificare**, non come legge percettiva dimostrata. Decisione, alla lettera:

   > *A e B sono entità preservate e contemporaneamente boundary della trasformazione. La loro
   > rappresentazione circuitale non viene modificata. Un layer di annotazione separato può
   > indicare i boundary ports senza alterare il visual state dei nodi. Il boundary overlay
   > appartiene alla trasformazione, non all'entità. A-0 rimane quindi intatto.*
   >
   > *Il braccio A non usa dimming del resto del circuito né marcatori sugli invarianti. Anche
   > region highlight estesi devono essere evitati o trattati come variabile sperimentale, perché
   > potrebbero contaminare il confronto con C.*

   Tre cose che avevo sbagliato e che l'owner ha corretto: l'invariante è **semantico-spaziale, non
   pixel-perfect**; **l'attenuazione del resto è revocata dal default**; e la marcatura dei
   terminali non è un'eccezione ad A-0 ma un **layer separato**, che è più rigoroso di entrambe le
   letture che avevo proposto. Normativo in PRD §7.0.1, FR-53 e `DESIGN.md.Continuità visuale`.
7. 🟠 **Densità della sessione a 360 px.** `C₀` deve occupare quasi tutta la superficie utile, il
   `proofgraph-rail` deve restare visibile, l'equazione deve stare accanto al sottografo. Su
   telefono le tre cose competono per lo stesso spazio. Quale cede per prima è una decisione di
   design che non ho preso: probabile che sia il rail, che si contrae a indicatore e si espande a
   richiesta — ma va provato, non deciso a tavolino.
8. 🟠 **`ProofReplay` a 320 px.** Il criterio dichiarato è «cosa resta comprensibile», non «cosa ci
   sta». Serve stabilire la larghezza sotto la quale la superficie compatta **rifiuta** di
   presentarsi e rimanda alla PWA. Un `ProofReplay` illeggibile è peggio di un collegamento.
9. 🟡 **Il rail come oggetto d'uso.** Se durante il test A/B nessuno lo tocca, va riprogettato.
   Serve definire prima cosa conta come «usato», o il dato non sarà interpretabile dopo.
10. 🟡 **Alternativa testuale di un `LayoutPatch`.** Descrivere una topologia è risolto (FR-15);
    descrivere un **cambiamento** fra due topologie, conservando il senso di ciò che è rimasto, non
    lo è. È requisito di accessibilità e insieme ingresso del protocollo A/B per i partecipanti che
    usano lettore di schermo.

