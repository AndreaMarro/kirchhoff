# Review — lente: superficie MCP

**Oggetto:** `ARCHITECTURE-SPINE.md` v2, 975 righe, `AD-1…AD-35`, `updated: 2026-08-15`
**Contro:** `prd.md` (FR-20, FR-21, FR-45, FR-48, FR-49, §15), `EXPERIENCE.md`
**Revisioni precedenti lette:** `review-avversario`, `review-confini`, `review-continuita-visuale`,
`review-invarianti`, `review-privacy-percezione`, `review-testabilita`, `review-veridicita`.
Nessuno dei rilievi qui sotto ripete un titolo già rientrato; dove tocco un'area già battuta
(C8, V4, T15) lo dico esplicitamente e dichiaro cosa è cambiato.
**Web verificato il 15 agosto 2026.** Fonti in fondo.

---

## Verdetto in una riga

Quello che la Spine **assume** su MCP è tecnicamente corretto e supportato oggi — ogni fatto di
protocollo in AD-16 regge alla verifica — ma la superficie che quei fatti dovrebbero governare,
`ProofReplay`, **non compare in nessuna delle 975 righe**: MCP è l'unico dei tre adapter la cui
specifica comportamentale vive interamente fuori dall'architettura, e le quattro regole che la
toccano (AD-6, AD-16, AD-27, AD-33) si incontrano in punti dove il protocollo, dal `2026-07-28`,
ha tolto proprio il meccanismo su cui contavano.

---

## Verifica sul web — ciò che la Spine assume è supportato oggi

Rispondo per primo alla domanda 6, perché se la risposta fosse «no» tutto il resto sarebbe
secondario.

**È supportato.** MCP Apps è **Final dal 26 gennaio 2026**, non una bozza. Ogni affermazione
tecnica di `ARCHITECTURE-SPINE.md:355-363` risulta esatta:

| Affermazione della Spine | Riga | Esito |
|---|---|---|
| schema risorsa `ui://` | 356 | ✅ confermato |
| `mimeType` **deve** essere `text/html;profile=mcp-app` | 356 | ✅ confermato |
| associazione al tool via `_meta.ui.resourceUri` | 357 | ✅ confermato — il formato piatto `_meta["ui/resourceUri"]` è deprecato e sarà rimosso prima della GA |
| JSON-RPC 2.0 su postMessage | 357-358 | ✅ confermato — dialetto proprio con prefisso `ui/`, trasporto postMessage |
| *«Tools MUST return meaningful content array even when UI is available»* | 360-361 | ✅ citazione verbatim corretta |
| fonte `ext-apps`, `specification/2026-01-26/apps.mdx` | 363 | ✅ esiste, è la revisione Final |
| `SDK MCP Python`, revisione protocollo `2026-07-28` | 770 | ✅ è la revisione stabile corrente del core |

**Host che rendono MCP Apps oggi:** Claude e Claude Desktop, VS Code GitHub Copilot, Microsoft 365
Copilot, Goose, Postman, MCPJam, Archestra.AI.

**Falso positivo verificato e scartato:** la coesistenza di `2026-01-26` (riga 363) e `2026-07-28`
(riga 770) **non è un'incoerenza**. Sono due artefatti distinti — l'estensione Apps e il core del
protocollo — con calendari indipendenti. Nessun rilievo.

**Il `[ASSUMPTION]` del PRD è risolvibile in positivo.** `prd.md:541-542` chiede di confermare i
riferimenti «prima che una data o una garanzia di runtime diventi un impegno di progetto». Sono
confermati. Il presupposto va sbloccato, non rimosso.

**Ma tre fatti del `2026-07-28` la Spine non registra, e sono quelli che mordono:**

1. **Le sessioni di protocollo non esistono più.** Rimossi `Mcp-Session-Id` e l'handshake
   `initialize`/`notifications/initialized`. Il changelog prescrive testualmente: *«Servers that
   need cross-call state use explicit, server-minted handles passed as ordinary tool arguments»*
   (SEP-2567). → rilievo **M4**.
2. **La negoziazione dell'estensione è per richiesta.** MCP Apps è **opzionale**, identificata
   `io.modelcontextprotocol/ui`, negoziata via il campo `extensions` di `ClientCapabilities`; senza
   handshake, le capacità viaggiano in `_meta` (`io.modelcontextprotocol/clientCapabilities`) a ogni
   richiesta. → rilievo **M2**.
3. **`resources/read` porta obbligatoriamente `ttlMs` e `cacheScope`** (SEP-2549): la risorsa
   `ui://` è **cacheable dal client** per una durata che dichiariamo noi. → rilievo **M5**.

**Due assenze nella specifica Apps, rilevanti qui:** non definisce **alcun meccanismo di stato**
fra render o fra turni (le viste ricevono `ui/notifications/tool-input` e
`ui/notifications/tool-result`, e vengono smontate da `ui/resource-teardown`); e non dichiara
**alcun limite di dimensione** su risorsa o payload. Il vincolo dei 320 px di `EXPERIENCE.md:225`
è quindi una scelta di prodotto nostra, non un tetto imposto dal protocollo — e non ha nessun
corrispettivo nella Spine.

---

## M1 🔴 — `ProofReplay` non esiste nella Spine, e il suo contratto contraddice AD-33

**File:riga.** `ARCHITECTURE-SPINE.md` — **zero occorrenze** di `ProofReplay` o `replay` in 975
righe (verificato con `grep -ci`). Contro: `EXPERIENCE.md:47` e `:223-227`;
`prd.md:528-529` (FR-48).

Le tre superfici hanno statuti asimmetrici. La PWA e Ardesia sono coperte: la prima da tutto il
documento, la seconda da un AD dedicato (AD-28, `:617-627`) che ne fissa il verso — «consuma
evidenze, non possiede la verità circuitale». La superficie MCP ha AD-16, che ne fissa il
**protocollo** (mimeType, `_meta`, `content`/`structuredContent`), e nient'altro. Il suo
**comportamento** — cosa porta, cosa non porta, con quale criterio — sta solo in `EXPERIENCE.md:47`:

> «Prima/dopo, selezione di un elemento, **certificato**, navigazione nel grafo. Nient'altro»

e in `:224-225`: «**Non porta**: rail espanso, ispezione multipla, export».

**Cosa può divergere.** «Certificato» (UX, PRD FR-48) e «**residui** ispezionabili» (AD-33,
`:684-685`) non sono lo stesso oggetto. Il pannello dei residui è definito in `EXPERIENCE.md:241-244`
come cinque righe fisse — KCL, KVL, potenza, accordo, coerenza fisica — con il valore in cifre;
`ProofCertificates` è una componente distinta della `ProofSession` (`prd.md:523-524`, elencata
separatamente). Un'unità che costruisce `ProofReplay` **dalla sola `EXPERIENCE.md`** porta il
certificato, non porta i residui, e ha esaurito la propria lista. Un'unità che lo costruisce dalla
Spine applica AD-33 e non porta il Badge. **Le due sono entrambe conformi e producono la stessa
superficie con e senza il Badge.**

Peggio nella direzione opposta: se `ProofReplay` porta il certificato e **non** i residui, e
qualcuno rende comunque il Badge — che è la lettura naturale, perché il certificato *sembra* la
prova — si ottiene esattamente il «meglio di niente» che AD-33 esiste per vietare, **senza violare
una sola parola di AD-33**, perché AD-33 non sa che questa superficie esiste con questo nome.

**Forma minima della correzione.** Una riga in AD-33 o in AD-16 che nomini la superficie e leghi i
due termini: *«`ProofReplay` è la superficie MCP della `ProofSession`. Il "certificato" di
`EXPERIENCE.md:47` include i cinque residui nella forma di `EXPERIENCE.md:241-244`: non è un oggetto
alternativo alla prova, è il suo veicolo compatto. Ciò che `ProofReplay` non porta rimanda alla PWA
e non porta il Badge.»* Nessun AD nuovo.

---

## M2 🔴 — Il ramo a tre vie di AD-33 non ha un ingresso: nessuno legge la capacità dell'host

**File:riga.** `ARCHITECTURE-SPINE.md:684-688` (AD-33, Rule); `:355-363` (AD-16, Rule);
`:614` (AD-27, «funziona senza MCP Apps»).

AD-33 prescrive tre esiti — ispezionabile · testo strutturato · niente Badge — e AD-16 enumera i
fatti di protocollo **senza mai nominare la negoziazione**. Non esiste nella Spine il nome del
segnale, il punto di codice che lo legge, né il valore di default.

Non è una lacuna teorica: il segnale **esiste ed è obbligatorio**. MCP Apps è un'estensione
opzionale (`io.modelcontextprotocol/ui`) negoziata via il campo `extensions` delle capability, e
dal `2026-07-28` — rimosso l'handshake — le capacità del client arrivano in `_meta` **a ogni
richiesta**. La specifica Apps prevede esplicitamente che il server registri varianti *text-only*
per gli host non supportati. La decisione che AD-33 impone è quindi **realizzabile e per-richiesta**;
semplicemente nessuna riga della Spine dice chi la prende.

**Cosa può divergere.** Un adapter che non trova il segnale nominato sceglie un default. I due
default plausibili sono opposti e nessuno dei due è vietato:
- *«rendo sempre il pannello»* → su un host senza estensione l'utente vede solo `content`, e se
  `content` porta il Badge senza la prova, è la violazione di K-4 che AD-33 esiste per prevenire;
- *«non rendo mai il Badge in conversazione»* → il prodotto perde la superficie che `prd.md` (SM-11)
  chiama il cardine dell'acquisizione, per prudenza, senza che nessuno abbia deciso di perderla.

Il primo è più economico da scrivere ed è quello che si scrive.

**Distinzione da V4** (`review-veridicita`, «Il degrado produce un badge che non si apre»): V4 ha
osservato che **la regola mancava**, e la Spine l'ha aggiunta come AD-33. Il rilievo qui è che la
regola aggiunta **non ha ingresso** — un ramo condizionale la cui condizione nessuno calcola non è
un ramo, è il suo primo caso.

**Forma minima della correzione.** Una riga in AD-33: *«Il ramo è deciso da un unico punto in
`adapters/mcp`, che legge la capacità `io.modelcontextprotocol/ui` dichiarata dall'host per quella
richiesta. In assenza del segnale il default è il ramo più conservativo: nessun Badge, rimando alla
superficie che regge la prova. Un default permissivo non è un'ottimizzazione, è la violazione di
K-4 con un'altra faccia.»*

---

## M3 🔴 — `adapters/` → `domain/` non è recintato: è il fork che FR-45 vieta, da una porta non sorvegliata

**File:riga.** `ARCHITECTURE-SPINE.md:612` (AD-27, Rule); tabella dei recinti `:468-473`;
sesto recinto `:601-603` (AD-26); `:237` (AD-8, riga `ProofSession`).

AD-27 dice: *«nessun modulo del kernel importa codice specifico di una superficie; un test di
architettura fallisce sulla **dipendenza inversa**»*. Il verso vincolato è uno solo. I sei recinti
oggi ordinati sono:

| # | Vietato | Ordinato da |
|---|---|---|
| 1 | `domain/` → fuori da `domain/` | AD-1 |
| 2 | `domain/` → `render/` | AD-18, AD-21 |
| 3 | `domain/` → `perception/` | AD-24 |
| 4 | `domain/` ∪ `render/` → `adapters/` | AD-27 |
| 5 | fuori da `corpus/` → filesystem del corpus | AD-25 |
| 6 | `experiment/arm0` ↛ `LayoutIR` del passo precedente | AD-26 |

**Nessuno vincola `adapters/mcp` → `domain/`.** Verificato: zero occorrenze di un vincolo in quel
verso (`grep -c "adapters/.*→.*domain"` = 0).

AD-8 `:237` dichiara `ProofSession` «proiezione di sola lettura **verso gli adapter**» — cioè il
canale *inteso*. Non dice che sia il canale **unico**, e AD-28 `:623` mostra che non lo è nemmeno
per Ardesia, che consuma «`ProofSession`, `ProofCertificates` e `Claim`» come tre voci separate.

**Cosa può divergere.** Un `adapters/mcp` che importa `domain.proof.ProofGraph` e lo percorre per
costruire il prima/dopo di FR-49 passa **tutti e sei** i recinti. Fatto tre volte — PWA, MCP,
Ardesia — sono tre implementazioni della stessa logica di derivazione, che divergeranno al primo
cambio del `ProofGraph`. È letteralmente il fork che FR-45 (`prd.md:473-486`) vieta, entrato dalla
porta che AD-27 non guarda.

**E c'è un caso peggiore, che tocca l'invariante più protetto.** Per decidere cosa marcare nel
prima/dopo, un adapter con accesso diretto a `ProofGraph` + `TransformResult` può **ricalcolarsi
`Pₖ`**. AD-22 `:486-489` chiude esattamente questa porta su `render/` — *«Il renderer non espone
alcuna funzione per proporre un `preserve` proprio: lo riceve»* — perché chi è misurato non
definisce il proprio riferimento. Riaperta uno strato più in fuori, su una superficie che AD-26 non
copre, produce un `ProofReplay` che evidenzia un insieme di conservati che nessun
`domain/transform/check` ha validato: A-0 mostrato allo studente su un `Pₖ` non certificato.

**Distinzione da R5 di `review-confini`** («un test fallisce sulla dipendenza inversa è una
promessa, tre volte»): R5 riguardava l'**assenza del soggetto** dei recinti, ed è stata chiusa —
i sei recinti ora esistono con nome e file. Il rilievo qui è che **la lista è incompleta nel verso
opposto**, e che il verso mancante è quello che porta al fork.

**Forma minima della correzione.** Un **settimo recinto** in `check_boundaries.py`, dichiarato in
AD-27: *«`adapters/*` → `domain/` è vietato salvo il tipo `ProofSession` e i tipi che essa nomina.
Un adapter che risolve un identificatore lo fa attraverso la proiezione, mai importando lo stadio
che l'ha prodotta. In particolare nessun adapter ricalcola `Pₖ`: lo riceve dal `TransformResult`,
come `render/` (AD-22).»* Nessun AD nuovo, nessuna rinumerazione.

---

## M4 🟠 — La `ProofSession` non ha una maniglia fra chiamate, e il `2026-07-28` ha reso quella l'unica strada

**File:riga.** `ARCHITECTURE-SPINE.md:192-200` (AD-6); `:613-614` (AD-27); `:741` (convenzione
identificatori); `prd.md:544-557` (FR-49).

Il changelog `2026-07-28` è esplicito: rimosse le sessioni di protocollo e `Mcp-Session-Id`, e
*«Servers that need cross-call state use explicit, **server-minted handles passed as ordinary tool
arguments**»*. È esattamente la forma di `resume_ref`, quindi AD-6 è **compatibile**. Il problema è
la **portata**.

AD-6 `:197-198` circoscrive `resume_ref` a *«lo stato di **una conversazione multi-giro**»* — il
flusso di disambiguazione: sospendo su una Domanda mirata, riprendo. È **monouso** e a **TTL 15
minuti**. La `ProofSession` non è una conversazione multi-giro: è un artefatto durevole, che AD-27
`:613-614` vuole «serializzabile e ricostruibile». E `ProofReplay` è per costruzione una superficie
a **molte chiamate**: FR-49 `:548-553` enumera prima/dopo, provenienza di un elemento, «perché posso
farlo?» — tre interrogazioni distinte sullo stesso passo, più la navigazione nel grafo.

**Cosa può divergere.** La Spine offre un solo contenitore fra chiamate. Due letture, entrambe
conformi:
- **(a)** la sessione viaggia in `resume_ref` → muore dopo 15 minuti e **un solo uso**; ogni
  navigazione nel grafo ne brucia uno, e uno studente che torna sul passo 2 dopo aver letto il 3
  trova la sessione consumata;
- **(b)** si conia una **seconda maniglia** non dichiarata → un secondo meccanismo di stato senza
  proprietario, senza regola di firma, senza TTL e **senza legame al `subject_id`** — che è
  precisamente la vulnerabilità che il *Prevents* di AD-6 `:199-200` nomina: *«Un `resume_ref` non
  firmato o non legato al soggetto è un IDOR sugli esercizi altrui.»*

La (b) è quella che si scrive, perché la (a) è visibilmente inutilizzabile. E la (b) reintroduce
l'IDOR che AD-6 chiude, su una maniglia che AD-6 non sa di dover proteggere.

**Distinzione da C8 di `review-avversario`:** C8 riguardava l'`InteractionState`, cioè lo **stato di
vista** (quale elemento è selezionato). La sua chiusura è arrivata a metà: AD-8 `:238` e AD-21 `:461`
ora assegnano `InteractionState` al **client** e lo escludono dalla `ProofSession`, ma AD-16 `:362`
dice ancora, non emendata, *«Il pannello non conserva stato locale»* — tre righe della stessa Spine
che dicono cose opposte sulla stessa superficie. Il rilievo **qui** è diverso e di grado maggiore:
non lo stato di vista, ma **la maniglia della sessione stessa**, che è stato di dominio e che
nessuna delle tre righe copre.

**Nota su T15** (`review-testabilita`, «il registro dei prefissi copre quattro entità su una
dozzina»): il fatto che `ProofSession` non abbia prefisso ULID a `:741` è già rilevato lì e non lo
ripeto. La conseguenza **specifica di MCP** — che senza identificatore non esiste l'argomento di
tool che il protocollo prescrive come unico veicolo di stato — non lo è.

**Forma minima della correzione.** Una riga in AD-6 che separi le due maniglie: *«`resume_ref`
resta la continuazione **monouso** di un flusso sospeso. La ripresa di una `ProofSession` è una
maniglia distinta — `session_ref` — **rileggibile**, legata al `subject_id` e firmata con la stessa
regola, con TTL proprio. Le due non si sostituiscono: la prima riprende un'operazione, la seconda
risolve una proiezione.»* Più una riga in `:741` per il prefisso.

---

## M5 🟠 — «Contratto versionato» non dice chi versiona, con che regola, né cosa accade a una `ProofSession` precedente

**File:riga.** `ARCHITECTURE-SPINE.md:355` (AD-16, Rule, prima riga); `prd.md:1795-1796` (§15);
`ARCHITECTURE-SPINE.md:92` (AD-1, `ir_version`).

Le due fonti dicono la stessa mezza frase e si fermano lì:

- Spine `:355` — «versione dichiarata; deprecazione con periodo di sovrapposizione annunciato».
- PRD `:1795` — «Versionamento e deprecazione dichiarati, con un periodo di sovrapposizione
  annunciato prima di qualunque rottura».

Mancano tre cose, e la terza è quella che si paga:

1. **Chi versiona.** AD-8 assegna uno scrittore unico a ogni entità; il contratto non è un'entità e
   non ha proprietario. Nessun modulo lo possiede.
2. **Cosa conta come rottura.** Aggiungere un campo a `structuredContent` rompe? Cambiare l'HTML
   della risorsa `ui://` rompe? Cambiare la forma della `ProofSession` rompe? Senza regola, due
   adapter divergono al primo cambio — che è precisamente la domanda dell'incarico.
3. **Cosa accade a una `ProofSession` creata sotto una versione precedente.** Nessuna riga lo dice.
   E qui il difetto è strutturale: **solo `CircuitIR` porta una versione** (`ir_version`, AD-1
   `:92`). `LayoutIR`, `ProofGraph`, `ProofCertificates` e la `ProofSession` stessa — cioè
   **l'intero payload che questa superficie trasporta** — non ne portano nessuna. AD-27 `:613` la
   vuole «serializzabile»: un formato di filo senza versione.

**E MCP rende il contratto due artefatti con vite indipendenti, non uno.** Dal `2026-07-28`,
`resources/read` **deve** restituire `ttlMs` e `cacheScope` (SEP-2549): la risorsa `ui://` — il
bundle HTML della vista — è **cacheable dal client per una durata che dichiariamo noi**, mentre le
risposte di tool restano fresche a ogni chiamata.

**Cosa può divergere.** Una vista di versione *N*, ancora in cache presso l'host, che riceve
`structuredContent` di versione *N+1*. È uno stato **legale a livello di protocollo**, raggiungibile
senza che nessuno abbia sbagliato, e la Spine non lo contempla: il «periodo di sovrapposizione
annunciato» di `:355` è pensato per host che aggiornano il proprio codice, non per una cache che
tiene ferma metà del contratto. Il fallimento tipico è muto — la vista rende un campo che non c'è
più, o ignora uno nuovo, e mostra una `ProofSession` incompleta **con il Badge**, perché il Badge
sta nel payload fresco e la prova nel bundle vecchio.

**Forma minima della correzione.** Tre righe in AD-16, nessun AD nuovo:
- *«Il contratto ha un proprietario dichiarato: `api/assistant`. La versione è un campo della
  risposta, non una nota di rilascio.»*
- *«Regola di compatibilità: additiva entro la stessa major — un campo nuovo in `structuredContent`
  non è una rottura, la rimozione o il cambio di significato di un campo esistente lo è. La
  `ProofSession` porta la propria versione, come `CircuitIR` porta `ir_version`.»*
- *«La risorsa `ui://` e la risposta di tool sono versionate **insieme**: la vista dichiara la
  versione che sa leggere, e una risposta di versione diversa non è resa — degrada al ramo testuale
  di AD-33. Il `ttlMs` della risorsa non può eccedere il periodo di sovrapposizione annunciato.»*

---

## M6 🟠 — La «forma testuale strutturata» non è specificata, e l'unico veicolo che ha consegna i nostri numeri a un modello che AD-4 non governa

**File:riga.** `ARCHITECTURE-SPINE.md:685-686` (AD-33); `:359-360` (AD-16); `:134-141` (AD-4);
`:130-132` (AD-3); `prd.md:910-913` (FR-20); `EXPERIENCE.md:241-244`.

**Prima metà — il formato non c'è.** AD-33 `:685-686` prescrive *«l'artefatto porta i residui in
forma testuale strutturata»* e nessuna sezione della Spine definisce quella forma. Le uniche
convenzioni di forma esistenti sono `{code, message, subject}` per gli errori (`:744`) e la
partizione `content` / `structuredContent` di AD-16. Il formato è quindi **lasciato all'adapter** —
la risposta alla domanda 5. Con tre adapter e un degrado «previsto e progettato» (AD-27 `:614`),
sono tre forme diverse della stessa prova, e nessun test può verificare che «i residui ci sono»
perché non esiste la forma rispetto a cui verificarlo.

**Seconda metà, e vale di più.** L'unico veicolo che quella forma può usare è `content`. E `content`
è definito, in due documenti, come la rappresentazione **per il modello**:

- Spine `:359` — «`content` — rappresentazione testuale **per il contesto del modello** e per gli
  host senza UI»;
- PRD `:910-911` (FR-20) — «una rappresentazione testuale **per il contesto del modello** e per gli
  host senza UI».

Quindi i cinque residui — che sono **numeri**, `EXPERIENCE.md:241-244`: «valore del residuo in cifre
tabulari» — entrano nel contesto del modello dell'host, e il modello dell'host li riformula nella
propria risposta all'utente. È esattamente ciò che AD-4 `:136-137` chiama *«l'errore silenzioso più
costoso del prodotto — un testo che riformula, arrotonda o inventa un valore che il solver aveva
calcolato correttamente»*.

**Ma la Rule di AD-4 non lo raggiunge.** AD-4 `:139-141` vincola «il generatore di testo», che nella
Spine è `ModelPort.narrate` (AD-3 `:130-132`): un modello **nostro**, dietro **nostra** porta, che
riceve e restituisce segnaposto. Il modello dell'host non sta dietro alcun port — il paradigma
`:32` lo elenca fra le cose non deterministiche «dietro *port*», ma nessun port lo rappresenta, e
AD-16 gli consegna `content` per progetto. **AD-4 protegge ogni numero su tutte le nostre superfici
e nessuno sull'unica superficie dove un modello di terzi li legge.**

**Cosa può divergere.** Due adapter conformi: uno mette i residui in `structuredContent` (resi dalla
vista, mai narrati) e in `content` mette solo un riferimento non parafrasabile; l'altro li mette in
`content` in prosa, perché AD-33 dice «forma testuale» e `content` è il campo testuale. Il secondo
produce una superficie dove l'assistente dice «il residuo KCL è circa zero» — arrotondato, in
prosa, sotto Badge Verificata. Nessuna regola è stata violata.

**Distinzione da V3** (`review-veridicita`, «la cifra non è inventata, ma può essere quella
sbagliata»): V3 riguarda l'ancoraggio dei segnaposto **dentro il nostro renderer**, ed è stata
chiusa nell'emendamento di AD-4 `:143-153`. Qui il modello non è il nostro e i segnaposto non
esistono: il numero esce già risolto.

**Forma minima della correzione.** Due righe:
- in **AD-33**, la forma: *«"Forma testuale strutturata" significa: i cinque residui nell'ordine
  fisso di `EXPERIENCE.md`, ciascuno con nome del controllo, valore, unità ed esito, più l'esito
  del round-trip e `verifier_id` + versione. È la stessa forma su ogni adapter, ed è verificata da
  un test di contratto.»*
- in **AD-4**, l'estensione del confine: *«I valori calcolati escono verso un modello che non è
  dietro `ModelPort` — il modello dell'host assistente — solo in `structuredContent`, reso dalla
  vista. In `content` compaiono come blocco citabile e non riformulabile, con l'istruzione esplicita
  che i numeri non vanno riespressi. AD-4 vale su ogni modello che legge un nostro numero, non solo
  sul nostro.»*

---

## Risposte dirette alle sei domande

1. **`ProofReplay` su superficie compatta.** La Spine **non dice** cosa può portare e cosa no: la
   parola non vi compare (M1). AD-33 **non rende impossibile** il Badge su MCP — la specifica Apps
   impone l'array `content` *anche* quando la UI è disponibile, quindi il secondo ramo («residui in
   forma testuale strutturata») ha sempre un veicolo e il terzo ramo («non porta il Badge») è di
   fatto irraggiungibile su MCP. **È realizzabile.** Ciò che manca non è la possibilità, è
   l'ingresso del ramo (M2) e la forma del contenuto (M6).
2. **Contratto versionato.** Nessuno lo versiona, non c'è regola di compatibilità, e una
   `ProofSession` di versione precedente non ha trattamento — anche perché è l'unica delle
   rappresentazioni trasportate a non portare una versione (M5). Con `ttlMs` obbligatorio su
   `resources/read`, il contratto è due artefatti con vite indipendenti.
3. **Dipendenza a senso unico.** Il verso opposto **non è vincolato**: nessuno dei sei recinti
   copre `adapters/` → `domain/` (M3). Un `adapters/mcp` che legge `ProofGraph` direttamente è
   conforme, e nel caso peggiore si ricalcola `Pₖ`, riaprendo su un altro strato
   l'autocertificazione che AD-22 chiude su `render/`.
4. **Stato.** `resume_ref` **non copre questo caso**: è circoscritto alla conversazione multi-giro,
   è monouso e a TTL 15 minuti, mentre `ProofReplay` è a molte chiamate per costruzione. Il
   `2026-07-28` ha reso le maniglie coniate dal server l'**unico** meccanismo di stato fra chiamate,
   e la `ProofSession` non ne ha una (M4).
5. **Il degrado.** Il formato **è lasciato all'adapter** — nessuna sezione lo definisce — e il campo
   che dovrebbe portarlo è per definizione il canale del modello dell'host, che AD-4 non governa
   (M6).
6. **Web.** Supportato. Vedi la sezione di verifica e le fonti.

---

## Porte verificate e trovate chiuse

- **AD-16 e la specifica.** Ogni fatto tecnico regge (tabella in alto). Nessun rilievo.
- **`2026-01-26` vs `2026-07-28`.** Due artefatti distinti, non un'incoerenza.
- **AD-6 e la statelessness del `2026-07-28`.** La forma di `resume_ref` — maniglia coniata dal
  server, passata come argomento — è **esattamente** quella che il changelog prescrive. Compatibile.
  Il rilievo M4 è sulla portata, non sulla forma.
- **AD-28 e il verso verso Ardesia.** «Evidenze in sola lettura» è coerente con il modello di
  ospitalità di MCP: l'host possiede il contesto linguistico, noi il circuito. Nessun rilievo.
- **AD-5 e il gate.** `publish()` sta in `domain/`, e nessuna superficie può aggirarlo perché solo
  `Published` è serializzabile (`:167-168`). L'adapter MCP non apre un varco sul gate.
- **Limiti di dimensione.** Cercati nella specifica Apps: **non ne dichiara**. Il vincolo dei
  320 px di `EXPERIENCE.md:225` è nostro. Non è un rilievo contro la Spine, ma resta un vincolo di
  prodotto che la Spine non registra.

---

## Ordine di chiusura, per costo

| # | Rilievo | Costo | Perché prima |
|---|---|---|---|
| 1 | **M3** — settimo recinto `adapters/ → domain/` | una riga in `check_boundaries.py` | è l'unico che diventa irrecuperabile: tre adapter scritti, tre logiche divergenti, e il fork esiste |
| 2 | **M2** — ingresso del ramo di AD-33 | una riga in AD-33 | il default sbagliato è quello economico, e si scrive al primo commit dell'adapter |
| 3 | **M6** — forma dei residui + estensione di AD-4 | due righe | il formato si congela appena il primo adapter lo serializza |
| 4 | **M1** — `ProofReplay` nominato nella Spine | una riga | chiude il divario fra i due documenti che l'unità legge |
| 5 | **M4** — `session_ref` distinto da `resume_ref` | una riga in AD-6 + un prefisso | l'IDOR entra con la seconda maniglia non dichiarata |
| 6 | **M5** — regola di compatibilità | tre righe in AD-16 | morde al primo cambio, non al primo commit — ma dopo è un contratto pubblico e non si ritira |

Nessuna correzione richiede un AD nuovo. `AD-1…AD-35` restano come sono; sei righe in AD-4, AD-6,
AD-16, AD-27 e AD-33, più un recinto in `check_boundaries.py` e un prefisso in `:741`.

---

## Fonti web (verificate il 15 agosto 2026)

- [MCP Apps — Model Context Protocol](https://modelcontextprotocol.io/extensions/apps/overview) —
  stato, modello di sicurezza a iframe sandboxed, `_meta.ui.resourceUri`, `_meta.ui.csp`,
  `_meta.ui.permissions`, elenco degli host che rendono MCP Apps oggi.
- [`ext-apps/specification/2026-01-26/apps.mdx`](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) —
  revisione Final; `ui://`, `text/html;profile=mcp-app`, *«Tools MUST return meaningful content
  array even when UI is available»*, metodi `ui/*`, `ui/resource-teardown`, identificatore
  `io.modelcontextprotocol/ui`, natura opzionale e negoziata, assenza di limiti di dimensione e di
  meccanismo di stato.
- [Key Changes — MCP `2026-07-28`](https://modelcontextprotocol.io/specification/2026-07-28/changelog) —
  rimozione di `Mcp-Session-Id` e dell'handshake `initialize` (SEP-2567, SEP-2575); *«Servers that
  need cross-call state use explicit, server-minted handles passed as ordinary tool arguments»*;
  MRTR e `resultType: "input_required"` (SEP-2322); `ttlMs` e `cacheScope` obbligatori su
  `resources/read` (SEP-2549); campo `extensions` su `ClientCapabilities`/`ServerCapabilities`.
- [MCP Apps: Extending servers with interactive user interfaces](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/) —
  annuncio dell'estensione.
- [SEP-1865 — MCP Apps](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1865) —
  proposta di origine.
