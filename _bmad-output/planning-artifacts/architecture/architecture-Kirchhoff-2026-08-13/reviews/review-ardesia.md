# Review — lente: integrazione Ardesia / LessonOS

**Oggetto:** `ARCHITECTURE-SPINE.md` (974 righe, AD-1…AD-35, agg. 15 ago 2026 09:11), con
`prd.md` (1898 righe) come contratto di riferimento.
**Fuoco:** AD-28, letto contro AD-27, AD-8, AD-11, AD-16, AD-20, AD-33 e §6 del PRD.
**Vincolo rispettato:** non ho ispezionato Ardesia né LessonOS. Ogni rilievo è documentale.
**Nota:** ho letto i titoli delle sette review già rientrate e non ripeto i loro rilievi. Dove il
mio confina con uno già scritto, lo dichiaro e dico dove diverge.

---

## Verdetto

AD-28 protegge la direzione giusta con la frase giusta e **non nomina nessun meccanismo**: la sola
lettura è una dichiarazione, l'unico enforcement che lo Spine cita altrove (permessi DB, AD-8:218)
non può raggiungere un sistema che non parla col database di Kirchhoff, e la dipendenza che il PRD
**impone** — `prd.md:480`, il plugin consuma ToolHost, Simulation Plugin e LessonOS — corre nel
verso opposto a quello che AD-28 e AD-27 sorvegliano, dove nessun port, nessun recinto e nessun
contratto versionato la guardano.

Un rilievo di contesto che cambia la lettura di tutti gli altri: `review-veridicita.md:357` elenca
«Ardesia / LessonOS come seconda autorità» fra le **porte verificate e trovate chiuse**, motivando
con «chiusa da AD-28: sola lettura». La porta è chiusa in prosa. Non è chiusa da niente che
fallisca.

| # | Rilievo | Sev. | Domanda |
|---|---|---|---|
| A1 | «Sola lettura» dichiarata; il meccanismo di AD-8 è inapplicabile al soggetto di AD-28 | 🔴 | 1 |
| A2 | La dipendenza va verso l'interno, è imposta da FR-45, e nessun port la media | 🔴 | 2 |
| A3 | Il confine non è un contratto versionato, e la `ProofSession` è per riferimento | 🟠 | 5 |
| A4 | Sulla superficie Ardesia nessuno dice chi emette `subject_id`; §6 lo pretende e nessun AD lo impone | 🟠 | 3, 6 |
| A5 | `ProofCertificates` attraversa il confine e non è definito né posseduto; AD-33 vale ma parla un'altra lingua | 🟠 | 4 |
| A6 | AD-28 vieta di certificare il `CircuitIR`; il quarto controllo certifica una `Solution` | 🟡 | 2, 4 |
| A7 | AD-28 non contraddice nessun Non-Goal, ma il suo soggetto non è in nessun gate | 🟡 | 6 |

---

## A1 — «Sola lettura» è dichiarata, e il solo meccanismo che lo Spine possiede non arriva 🔴

### Dove

- `ARCHITECTURE-SPINE.md:623-627` — la Rule di AD-28, per intero. Elenca cosa Ardesia consuma e
  dichiara che ToolHost, Simulation Plugin, LessonOS e la memoria di Ardesia «non producono, non
  modificano e non certificano `CircuitIR`». **Nessun verbo di enforcement, nessun tipo, nessun
  test, nessun permesso.**
- `ARCHITECTURE-SPINE.md:218-219` — AD-8: «Enforcement a livello di permessi DB, non di
  convenzione.» È l'unico meccanismo di sola scrittura che lo Spine nomina.
- `ARCHITECTURE-SPINE.md:229-238` — la tabella dei proprietari. `ProofSession` (`:237`) è
  «`domain/proof`, come proiezione di sola lettura verso gli adapter». `Claim` (`:235`) è
  `domain/truthfulness`. **`ProofCertificates` non è in tabella** (vedi A5).
- `ARCHITECTURE-SPINE.md:467-473` — i cinque recinti di `check_boundaries.py`;
  `ARCHITECTURE-SPINE.md:599-603` — il sesto.

### Cosa può divergere

I sei recinti sono tutti frecce di import fra pacchetti Python di Kirchhoff. Nessuno dei sei nomina
`adapters/ardesia`, e nessuno può nominare LessonOS, che non è un pacchetto Python di Kirchhoff.
I permessi DB di AD-8 vincolano i principal che si connettono al database di Kirchhoff: Ardesia non
è uno di quelli. **Il meccanismo esiste, ma il soggetto di AD-28 è fuori dal suo raggio d'azione per
costruzione.**

Resta una superficie che nessuna delle due difese copre: `adapters/ardesia` **è** codice di
Kirchhoff e può legittimamente chiamare l'applicazione — è ciò che fa un adapter in ingresso, e
`ARCHITECTURE-SPINE.md:81-82` lo autorizza («`adapters` implementa `ports` e non è mai importato se
non dalla composizione radice» vincola l'import *verso* l'adapter, non le chiamate *dall'*adapter).
Nessuno dei sei recinti vieta `adapters/ardesia → domain/ingest`, che AD-8 (`:231`) dichiara
scrittore unico del `CircuitIR`. Quindi: LessonOS non scrive un `CircuitIR`, ma può farne scrivere
uno, quando vuole, quante volte vuole. AD-28 non distingue «l'host non possiede la verità» da «l'host
non ne innesca la produzione», e sono due proprietà diverse — la seconda è quella che decide chi
detiene il ciclo di vita (vedi A3).

**Nota di delimitazione.** `review-privacy-percezione.md:434-440` ha già rilevato che AD-28 vincola
una direzione sola e non dice cosa l'host *trattenga*. Quel rilievo riguarda il contenuto; questo
riguarda il meccanismo. Non si sovrappongono e nessuno dei due chiude l'altro.

### Forma minima della correzione

Dentro AD-28, senza nuovi AD:

- **nominare il meccanismo.** Le tre cose che attraversano il confine escono da un tipo che non ha
  metodi di scrittura, e la sola porta d'ingresso di Ardesia verso Kirchhoff è un'operazione
  enumerata nella stessa Rule. Un elenco chiuso di operazioni, come AD-19 fa per le cause di
  rifiuto;
- **una riga nella tabella dei recinti** (`:467-473`): `adapters/ardesia ↛` i moduli scrittori di
  AD-8. È l'unica difesa che oggi fallisce davvero (`:474-478` lo dice di sé: «Non è un errore di
  compilazione»);
- **dire esplicitamente se l'host può innescare `ingest`**, e con quale conseguenza sulla proprietà
  del circuito risultante.

---

## A2 — Il verso della dipendenza è verso l'interno, è imposto dal PRD, e nessun port lo media 🔴

### Dove

- `prd.md:480-481` (FR-45) — «Dentro Ardesia il plugin consuma ToolHost, Simulation Plugin e
  LessonOS **senza duplicare** auth, shell, dashboard, memoria o simulatore.» È una *Consequence
  (testable)*, cioè un requisito, non un'ipotesi.
- `ARCHITECTURE-SPINE.md:611-615` (AD-27, Rule) — «nessun modulo **del kernel** importa codice
  specifico di una superficie; un test di architettura fallisce sulla dipendenza inversa.»
- `ARCHITECTURE-SPINE.md:929-932` — la nota di nomenclatura: «non esiste un pacchetto `kernel/`. Il
  *Visual Proof Kernel* è `domain/` + `render/`».
- `ARCHITECTURE-SPINE.md:63` e `:911-914` — l'elenco unico dei port: `ModelPort`, `BlobPort`,
  `LedgerPort`, `ClockPort`, `SpicePort`, `ObservationPort`.

### Cosa può divergere

Messe insieme, le tre righe dicono che AD-27 protegge `domain/` e `render/` e **nient'altro**.
`adapters/ardesia`, `pipeline/` e `api/` possono importare codice di Ardesia senza violare alcuna
regola — e FR-45 li obbliga a farlo. La domanda dell'incarico («Kirchhoff importa qualcosa da
Ardesia/LessonOS?») ha quindi risposta **sì, per requisito**, e AD-27 non è violato: è semplicemente
muto sul lato dove la dipendenza esiste.

Il problema non è l'import in sé — un adapter che parla col mondo è il paradigma. Il problema è che
il paradigma di questo Spine ha un solo strumento per il mondo esterno, il *port*
(`ARCHITECTURE-SPINE.md:31-33`: «Tutto ciò che è non deterministico — modelli di visione e
linguaggio, storage, pagamenti, host assistente — sta fuori, dietro *port*»). L'elenco dei port
nomina esplicitamente l'*host assistente* fra le cose da isolare, e poi **non contiene un port per
l'host**. Cinque servizi di Ardesia — auth, shell, dashboard, memoria, simulatore — entrano nel
sistema senza interfaccia dichiarata, senza secondo adapter possibile (che AD-3, `:131-132`,
pretende per i modelli) e senza il confine che rende sostituibile ciò che non controlliamo.

C'è anche un'ambiguità di nome che moltiplica il danno: **due cose diverse si chiamano «adapter
Ardesia»** — il pacchetto `adapters/ardesia` dell'albero sorgente (`:916`) e il *plugin che gira
dentro Ardesia* di `prd.md:480`. Il primo è governato dai recinti; il secondo non è nominato in
nessun punto dello Spine. Due unità che leggono AD-27 e FR-45 costruiscono due cose diverse ed
entrambe sono conformi.

### Forma minima della correzione

- **Una riga in AD-27** che dichiari il verso mancante: ciò che il plugin consuma da Ardesia passa
  da un'interfaccia dichiarata in `ports/` — auth e memoria in primo luogo — oppure è enumerato e
  giustificato caso per caso. Non serve un `ArdesiaPort` monolitico; serve che la lista non sia
  vuota.
- **Una riga di nomenclatura** accanto a `:929-932`, che distingua il pacchetto adapter dal plugin
  ospitato e dica quale dei due i recinti governano.

---

## A3 — Il confine non è un contratto versionato, e la `ProofSession` è una proiezione per riferimento 🟠

### Dove

- `ARCHITECTURE-SPINE.md:353` — il *Binds* di AD-16: «superficie assistente, FR-20, FR-21, §15 del
  PRD». **Solo la superficie assistente.**
- `prd.md:1781-1784` (§15) — «La superficie assistente è consumata da host di terzi: le rotture sono
  osservabili dall'esterno e non si possono ritirare.» Ardesia non compare in §15.
- `ARCHITECTURE-SPINE.md:458-460` (AD-21, emendata) — «`ProofSession` è una **proiezione per
  riferimento** … Ricostruirla significa risolvere gli identificatori, non deserializzare uno
  stato.»
- `ARCHITECTURE-SPINE.md:745` — «La persistenza è append-only sugli IR: una correzione produce una
  nuova versione, non una sovrascrittura.»
- `ARCHITECTURE-SPINE.md:92` — il `CircuitIR` porta `ir_version` semantica;
  `ARCHITECTURE-SPINE.md:880` — l'ER: `CIRCUIT ||--|{ IR_VERSION`.

### Cosa può divergere

Questo è il verso temporale della domanda 5, e ha due facce, entrambe scoperte.

**Prima faccia — nessuna versione del contratto.** AD-28 consegna tre tipi a un sistema separato,
sviluppato e rilasciato su un calendario che Kirchhoff non controlla, e **nessun AD versiona quel
confine**. AD-16 lo fa per MCP, con deprecazione e periodo di sovrapposizione annunciato (`:355`).
L'argomento di §15 — «le rotture sono osservabili dall'esterno e non si possono ritirare» — vale
identico per una `ProofSession` montata dentro LessonOS, e nessuno lo ha applicato lì. Il primo
campo aggiunto a `ProofSession` o a `Claim` rompe o fa divergere l'integrazione senza che alcuna
regola sia stata violata.

**Seconda faccia — l'identificatore non è qualificato.** AD-21 dice che la `ProofSession` porta *gli
identificatori dei quattro*. Non dice **quali** identificatori: quello del circuito o quello della
versione. Con persistenza append-only (`:745`) i due si comportano in modo opposto quando una
correzione arriva dopo la consegna:

- se l'identificatore è logico, Ardesia risolve la stessa `ProofSession` e ottiene **un circuito
  diverso** da quello su cui il Badge è stato emesso — e il Badge, che AD-5 lega a `publish()` di
  uno specifico `ProofGraph`, resta attaccato a una prova che non è più quella;
- se è di versione, la sessione è congelata e la correzione non arriva mai all'host, che continua a
  mostrare un circuito superato.

Sono due comportamenti opposti e **entrambi conformi al testo attuale**. Questa è la risposta alla
domanda «chi decide che quel circuito è *quello* di Kirchhoff»: nessuno, perché l'identità
attraverso il confine non è qualificata sul tempo.

**Nota di delimitazione.** `review-confini.md:34-63` (R1) ha argomentato che la `ProofSession`
doveva essere *per valore*; lo Spine ha risposto il 15 agosto rendendola *per riferimento*
(`:453-461`). R1 è chiuso. Questo rilievo è il costo non pagato di quella risposta, su un confine
che R1 non esaminava: fra due sistemi, «risolvere un identificatore» è una chiamata di rete nel
tempo, non un lookup.

### Forma minima della correzione

- **Estendere il *Binds* di AD-16** a `adapters/ardesia`, oppure una riga in AD-28 che dichiari il
  confine verso Ardesia contratto versionato con le stesse regole di deprecazione. Preferibile la
  prima: AD-16 possiede già la disciplina.
- **Una riga in AD-21** che qualifichi gli identificatori portati dalla `ProofSession`: versione o
  logico, e cosa accade a una `ProofSession` già consegnata quando l'IR referenziato riceve una
  nuova versione.

---

## A4 — Sulla superficie Ardesia nessuno dice chi emette `subject_id`, e §6 lo pretende senza AD 🟠

### Dove

- `ARCHITECTURE-SPINE.md:436-439` (AD-20, Rule) — «ogni richiesta porta un `subject_id` opaco.»
  Dice come si **usa** (firma, quota, ledger, idempotenza) e **non dice chi lo emette** né come sia
  derivato su una superficie che non ha un login Kirchhoff.
- `prd.md:480-481` (FR-45) — il plugin consuma ToolHost «senza duplicare **auth**».
- `prd.md:1189-1190` (§6, Non-Goals) — «**Non siamo il sistema di record dentro un assistente di
  terzi:** l'anagrafica resta l'account Kirchhoff.»
- `ARCHITECTURE-SPINE.md:291-294` (AD-11) — il `ParticipantToken` «non è congiungibile con
  `subject_id`, account, email o tenant: non esiste tabella, vista o percorso di codice che li metta
  in relazione, e **un test di contratto lo verifica**».

### Cosa può divergere

Le due frasi si guardano e non si toccano. §6 dichiara un Non-Goal sull'anagrafica; FR-45 impone di
non duplicare l'auth; **nessun AD media fra i due.** Se l'auth non è duplicata, l'identità sulla
superficie Ardesia nasce in Ardesia, e `subject_id` diventa una funzione di un identificatore emesso
altrove. AD-20 non lo vieta né lo autorizza: non ne parla. Il Non-Goal più esplicito di §6
sull'identità è quindi l'unico dei nove **senza un AD che lo regga**, mentre il primo — «Non
valutiamo persone» — ne ha uno intero (AD-11) e il *Binds* di AD-11 cita §6 alla lettera
(`:275-276`).

Sul `ParticipantToken` la conseguenza è precisa e non è quella già rilevata. AD-11 enumera quattro
cose con cui il token non è congiungibile, tutte interne a Kirchhoff, e affida la garanzia a **un
test di contratto** — cioè a un controllo che gira dentro Kirchhoff e vede le tabelle di Kirchhoff.
Se una sessione di Gate A si svolge in un contesto in cui l'host sa chi è seduto davanti allo
schermo e quando, la congiunzione «persona ↔ token» esiste, si compone per timestamp, e **si trova
interamente fuori dal raggio del test**. AD-11 non lo può impedire perché AD-11 non nomina gli
identificatori dell'host: dice `subject_id`, account, email, tenant. Lo Spine, inoltre, non dice
**su quale superficie** Gate A si esegua — `experiment/` esiste (`:910`), il braccio è «un parametro
di rendering, mai una variante di build o un ramo» (`:753`), ma nessuna riga limita l'esecuzione
dell'esperimento alla PWA.

Lo stesso vale per `StudentTrace` in ingresso da un host che conosce lo studente per nome; su
**cosa** contenga, quanto viva e chi lo legga rimando a `review-privacy-percezione.md:401-459` (P7),
che l'ha già coperto — qui il punto aggiuntivo è che **l'identificatore con cui arriva** non è
nominato da AD-20 né da AD-24 (`ARCHITECTURE-SPINE.md:553-554` è l'unica riga sull'entità, e parla
solo di forma semantica contro immagine).

### Forma minima della correzione

- **Una riga in AD-20** che dichiari chi emette `subject_id` su una superficie ospitata, e se sia
  una fusione esplicita di soggetti come già previsto per FR-21 (`:438-439`) o un soggetto distinto.
  Questo è anche ciò che dà un meccanismo al Non-Goal di `prd.md:1189`.
- **Una riga in AD-11** che estenda la non-congiungibilità agli identificatori emessi dall'host, e
  che dichiari su quale superficie Gate A può essere eseguito. Se la risposta è «solo PWA», è una
  riga; se è «anche in aula dentro un host», il test di contratto va sostituito da un vincolo di
  raccolta, perché un test interno non può vedere quella join.

---

## A5 — `ProofCertificates` attraversa il confine e non esiste; AD-33 vale, ma nomina altre cose 🟠

### Dove

- `ARCHITECTURE-SPINE.md:623-624` (AD-28) — le tre cose che attraversano: `ProofSession`,
  `ProofCertificates`, `Claim`.
- `ProofCertificates` compare in tutto lo Spine **due volte**: `:454` (dentro la composizione della
  `ProofSession`) e `:623`. Non è in AD-8 (`:229-238`), non è nell'albero sorgente (`:893-922`), non
  ha prefisso nel registro degli identificatori (`:741`), non ha causa di rifiuto in AD-19
  (`:406-418`).
- `ARCHITECTURE-SPINE.md:680` (AD-33, *Binds*) — «`adapters/`, superficie assistente, degrado non
  interattivo, AD-16, AD-27, K-4».
- `ARCHITECTURE-SPINE.md:684-688` (AD-33, Rule) — «il Badge Verificata e i **residui ispezionabili**
  viaggiano insieme o non viaggiano».

### Cosa può divergere

**Alla domanda diretta — AD-33 vale su questo confine?** Sì. Il suo *Binds* dice `adapters/` senza
qualificatori, e `adapters/ardesia` è sotto `adapters/` (`:916`). Non è una regola delle sole
superfici di prodotto. Questa porta è chiusa.

Ma è chiusa in un vocabolario che non tocca quello di AD-28. AD-28 autorizza il transito di tre
tipi e **il Badge non è uno dei tre**; AD-33 governa il Badge e i «residui ispezionabili», e
*residuo* nello Spine è un'altra cosa ancora — una causa di rifiuto di `domain/verify` (`:409`) e un
prodotto di `verify/` (`:900`). Nessuna riga dice che `ProofCertificates` siano i residui
ispezionabili, né che il Badge viaggi dentro la `ProofSession`.

Ne segue una divergenza concreta: due unità che implementano l'adapter Ardesia, una leggendo AD-28 e
l'altra AD-33, spediscono payload diversi, ed entrambe sono conformi. Peggio, l'unità che legge solo
AD-28 spedisce `ProofCertificates` — un tipo che dovrà inventare, perché nessun documento lo
definisce e AD-8 non gli assegna uno scrittore. Un tipo inventato nell'adapter è esattamente il fork
che AD-27 esiste per prevenire (`:609`), ottenuto senza importare nulla.

### Forma minima della correzione

- **Riga in AD-8** per `ProofCertificates`, con scrittore unico — plausibilmente `domain/proof`
  insieme al `ProofGraph`, o `domain/verify` che li produce; la scelta è dell'owner, l'assenza no.
- **Una frase in AD-28** che leghi i due vocabolari: cosa attraversa il confine è la `ProofSession`
  con i suoi certificati, **e il Badge vi appartiene alle condizioni di AD-33** — o non attraversa.
  Due parole di rinvio, e il confine smette di avere due descrizioni.

---

## A6 — AD-28 vieta di certificare il `CircuitIR`; il quarto controllo di `publish()` certifica una `Solution` 🟡

### Dove

- `ARCHITECTURE-SPINE.md:624-625` (AD-28) — «ToolHost, Simulation Plugin, LessonOS e la memoria di
  Ardesia non producono, non modificano e non certificano **`CircuitIR`**.»
- `ARCHITECTURE-SPINE.md:185` — i controlli 1-5 di `publish()`: «KCL · KVL · bilancio di potenza ·
  **accordo fra percorsi** · sanità fisica».
- `ARCHITECTURE-SPINE.md:954-956` (Deferred) — «Percorso C (ngspice) … Lo spine ne prevede il port
  (`SpicePort`) perché AD-5 confronta *n* percorsi, non due.»
- `prd.md:480-481` — il plugin non duplica il **simulatore**.

### Cosa può divergere

AD-28 vieta all'host di certificare un tipo, il `CircuitIR`, e il quarto controllo di `publish()`
non certifica quello: certifica l'accordo fra percorsi di risoluzione, cioè una `Solution`. Con
`SpicePort` esplicitamente previsto e FR-45 che chiede di non duplicare il simulatore, la lettura
che salda le due righe — il Simulation Plugin di Ardesia come adapter di `SpicePort`, terzo percorso
di verifica — **non viola la lettera di AD-28**, perché non tocca il `CircuitIR`. Farebbe però
partecipare un sistema esterno al gate che il prodotto vende.

Non è urgente: Percorso C è differito. È però il momento più economico per chiudere, perché la
chiusura è una parola e il costo di riaprirla dopo è un adapter già scritto.

### Forma minima della correzione

Sostituire in AD-28 il solo `CircuitIR` con l'elenco delle cose che il gate certifica —
`CircuitIR`, `Solution`, `Published`, `Claim` — oppure una riga che dichiari che nessun adapter di
`SpicePort` può essere fornito da una superficie ospite.

---

## A7 — AD-28 non contraddice nessun Non-Goal; il suo soggetto non è però in nessun gate 🟡

### Verifica di §6, riga per riga

Ho confrontato AD-28 (`:617-627`) con i nove Non-Goals di `prd.md:1175-1190`. **Nessuna
contraddizione diretta.** Sette sono ortogonali (chatbot, non lineari, addestramento, temi d'esame,
visione propria, gamification, app native). Due meritano una nota:

- **«Non valutiamo persone»** (`:1175-1180`) — AD-28 non lo contraddice, ma non lo protegge nemmeno
  su questo confine: la sola lettura riguarda il circuito. Coperto da A4 e, per il contenuto, da P7.
- **«Non siamo il sistema di record dentro un assistente di terzi»** (`:1189-1190`) — vedi A4: il
  Non-Goal esiste, l'AD che lo regge no.

**Nessun Non-Goal rende AD-28 privo di oggetto.** Il rischio è di natura diversa e va detto perché
tocca la stabilità della numerazione, che l'incarico dichiara congelata:

- `prd.md:530-531` (FR-48) — «Ardesia monta la stessa `ProofSession` **in seguito**».
- `prd.md:1414` (§7.1, In Scope) — «presentabile da PWA, superficie MCP **e in seguito Ardesia**».
- `prd.md:1436-1484` (§7.2, Out of Scope for MVP) — Ardesia **non compare**.
- `prd.md:1208-1216` — i sette gate A…G. **Nessuno apre Ardesia.**

Ardesia non è né in scope né fuori scope: è «in seguito», senza gate e senza criterio d'uscita. AD-28
vincola quindi un soggetto che nessuna tappa del piano consegna, e sarà letto per la prima volta da
chi lo costruisce, mesi dopo, quando la numerazione AD-1…AD-35 è congelata e l'unica correzione
possibile è un emendamento in loco.

Lo stesso vuoto si vede nella **Capability → Architecture Map** (`ARCHITECTURE-SPINE.md:934-948`):
l'ultima riga è «Misurazione qualità (FR-34, FR-35)». FR-36…FR-53 non hanno riga — fra cui FR-42,
FR-44, FR-45 e FR-48, cioè **tutti e quattro i requisiti che AD-27 e AD-28 dichiarano di vincolare**.
La mappa è l'unico punto del documento che dice a un costruttore *dove vive una cosa*, e per questo
confine non lo dice.

### Forma minima della correzione

- **Una riga in §7.2 del PRD** che collochi l'adapter Ardesia — o fuori MVP con un gate, o dentro un
  gate esistente. «In seguito» non è una posizione.
- **Righe nella Capability Map** per FR-42, FR-44, FR-45, FR-48, con modulo e AD di governo. È
  meccanico e chiude anche il sospetto che la mappa sia rimasta alla v1 come lo era l'albero sorgente
  prima del 15 agosto (`:924-928`).

---

## Risposte dirette alle sei domande

1. **«Sola lettura» è imposta o dichiarata?** Dichiarata. AD-28 (`:623-627`) non nomina permesso,
   tipo né assenza di metodo. AD-8 (`:218-219`) nomina i permessi DB, ma non raggiungono un sistema
   che non parla col nostro database; i sei recinti (`:467-473`, `:599-603`) non nominano
   `adapters/ardesia`. → A1.
2. **Kirchhoff importa da Ardesia?** Sì, **per requisito**: `prd.md:480-481`. AD-27 (`:611-615`)
   protegge solo `domain/` e `render/` (`:929-932`) e non è violato — è muto. Nessun port media i
   cinque servizi consumati. → A2.
3. **Chi possiede lo studente?** Lo Spine non dice se `StudentTrace` e `ParticipantToken` siano
   collegabili, perché non dice chi emette l'identità sulla superficie ospitata (AD-20:436-439 tace).
   AD-11 (`:291-294`) affida la non-congiungibilità a un test di contratto interno, che non può
   vedere una join composta fuori. → A4.
4. **Cosa attraversa il confine?** AD-28 autorizza `ProofSession`, `ProofCertificates`, `Claim`. Il
   secondo non è definito né posseduto in nessun punto dello Spine. **AD-33 vale su questo confine**
   — il suo *Binds* dice `adapters/` (`:680`) — ma nomina «Badge e residui ispezionabili», che non
   sono nessuno dei tre. → A5.
5. **Il verso temporale.** Nessuna regola di identità attraverso il confine: la `ProofSession` è per
   riferimento (`:458-460`), la persistenza è append-only (`:745`), e lo Spine non dice se
   l'identificatore portato sia logico o di versione. Il confine, inoltre, non è versionato: AD-16
   copre solo la superficie assistente (`:353`). → A3.
6. **Non-Goals.** AD-28 non ne contraddice nessuno e nessuno lo rende privo di oggetto. Ma
   `prd.md:1189-1190` è l'unico Non-Goal senza AD che lo regga, e il soggetto di AD-28 non compare in
   §7.2 né in alcuno dei sette gate. → A4, A7.

---

## Porte verificate e trovate chiuse

Le registro perché non vengano riaperte da una review successiva.

| Ipotesi | Esito |
|---|---|
| Ardesia certifica un `CircuitIR` | Chiusa da AD-28 (`:624-626`) **in prosa**; il meccanismo manca (A1), il tipo è quello giusto |
| Il `TruthfulnessGate` diventa una skill di Ardesia | Chiusa due volte: AD-28 (`:626`) e AD-30 (`:644-647`), quest'ultimo con proprietà del dominio e versionamento col codice |
| L'esperimento di Gate A parte da un ingresso di Ardesia | Chiusa: `:869-870`, «L'esperimento di Gate A parte da `STRUCT`, mai da `CONF`» |
| Ardesia produce un artefatto esportabile per conto proprio | Chiusa da AD-10 (`:259-271`): unico punto di export, e ogni formato deriva dall'SVG certificato |
| Il Badge viaggia verso una superficie che non regge la prova | Chiusa da AD-33 (`:684-688`), che vincola `adapters/` — con la riserva di vocabolario di A5 |
| `adapters/ardesia` non esiste nell'albero sorgente | Chiusa il 15 agosto (`:916`); il rilievo di `review-avversario.md:648` è superato |
| La `ProofSession` è un aggregato per valore | Chiusa il 15 agosto (`:453-461`); il rilievo R1 di `review-confini.md` è superato — vedi A3 per il costo residuo |

---

## Ordine di chiusura, per costo

1. **A5** — due righe (AD-8 + AD-28). Sblocca un tipo che oggi verrebbe inventato nell'adapter.
2. **A6** — una parola in AD-28. Costo nullo adesso, costo di un adapter dopo.
3. **A7** — righe nella Capability Map e una riga in §7.2 del PRD. Meccanico.
4. **A1** — una riga di recinto in AD-21 più una frase di meccanismo in AD-28. Richiede una
   decisione: se l'host può innescare `ingest`.
5. **A3** — decisione dell'owner su versionamento del confine e qualificazione dell'identificatore.
   Due righe di testo, una decisione vera.
6. **A4** — la più costosa perché è una decisione di prodotto sull'identità, non una riga. È anche
   quella che, non presa, si scoprirà il giorno in cui il primo studente entra da LessonOS.
7. **A2** — richiede di sapere quali dei cinque servizi di Ardesia sono davvero consumati, e non è
   deducibile dai documenti di Kirchhoff.
