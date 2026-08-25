# Lavoro rinviato

Voci raccolte durante la fase *ship*. Ognuna è reale e non risolvibile dentro la storia che l'ha
fatta emergere. Nessuna viene lasciata cadere in silenzio.

- source_spec: `spec-1-1-insieme-di-riferimento-strutturato-a-risposta-nota.md`
  summary: La metà fotografica della Story 1.1 — almeno 30 immagini CGHD con IR e risultato
    annotati a mano — non è stata realizzata, e la storia è stata chiusa sulla sola metà
    strutturata.
  evidence: Il criterio richiede annotazione manuale di fotografie reali. Contraddice la decisione
    dell'utente del 13 agosto 2026 ("saltiamo la parte foto reali"), recepita nello
    `sprint-change-proposal-2026-08-13.md`, che ha rimosso raccolta e annotazione fotografica da
    Epic 1; il criterio è però rimasto scritto in `epics.md`. È un conflitto di piano fra due
    artefatti, non un problema di codice: si risolve con `bmad-correct-course` e una decisione
    umana, non implementandolo. Finché resta aperto, SER è cieco sull'estrazione da immagine —
    esattamente il tratto dove nasce quasi tutto l'errore silenzioso, come già dichiarato nella
    proposta di cambio.

- source_spec: `spec-1-1-insieme-di-riferimento-strutturato-a-risposta-nota.md`
  summary: Il controllo di sanità fisica (D6, quinto controllo) non è applicato alle classi in
    regime sinusoidale e trifase.
  evidence: L'oracolo verifica KCL e bilancio delle potenze, che in regime sinusoidale valgono per
    identità di Tellegen sul prodotto `v·i`, non sulla potenza fisica `v·conj(i)`. Nessun controllo
    esclude oggi un passivo con potenza attiva negativa in alternata. Il controllo appartiene alla
    Story 2.7 (Verifica a cinque controlli); qui manca solo l'anticipo, e va ripreso lì.

- source_spec: `spec-1-1-insieme-di-riferimento-strutturato-a-risposta-nota.md`
  summary: La costante di tempo e le radici caratteristiche stanno nella risposta attesa dei casi
    di transitorio ma non fra le grandezze richieste, quindi VSR e SER non le misurano.
  evidence: Nessun risolutore le produce ancora: il sistema sotto test dell'harness è un
    riferimento minimo, non il prodotto (AD-15), e inventare una capacità che non esiste sarebbe
    peggio che dichiararla assente. I valori sono comunque presenti e verificati a ogni
    costruzione. Story 2.11 deve allargare le richieste quando il motore di Epic 2 sa rispondere.

- source_spec: Story `2-6-catalogo-delle-trasformazioni` (rilievo di revisione, 25/08/2026)
  summary: `partitore_di_tensione` è la terza applicabile dell'MVP (FR-43) e non ha
    implementazione: chi la chiede riceve «applicabile ma senza implementazione».
  evidence: Non è un corpo da scrivere, è una decisione di dominio che manca. Le due
    riduzioni implementate producono un `Cₖ₊₁` con una topologia diversa, e il
    `TransformResult` lo esige: AD-22 vuole ogni campo non-vuoto, `Delta` vuole almeno
    una derivazione, e una derivazione vuole almeno un'entità in ingresso. Una
    **ripartizione** — il catalogo stesso separa le due famiglie in `catalog.py` — non
    consuma né produce entità: ricava la tensione su un ramo di una serie già
    esistente. Quale sia il suo contenuto strutturale (nessuna derivazione? la serie
    percorsa a ritroso, `{Req} → {R1, R2}`? un settimo membro del risultato?) non è
    scritto in nessun documento di autorità: né AD-2 em., né AD-22 em., né FR-43, che
    ne parlano solo come nome. Sceglierlo dentro questa storia significherebbe fissare
    nel codice un modello che nessuno ha deciso, e AD-22 dice che il discriminante lo
    dichiara il Catalogo, mai chi implementa. Serve la decisione del proprietario su
    cosa sia il prodotto strutturale di una ripartizione; l'implementazione è mezza
    giornata dopo.

- source_spec: Story `2-6-catalogo-delle-trasformazioni` (terzo blocco di criteri)
  summary: Il Percorso B — sequenza di Trasformazioni fino alla grandezza richiesta,
    confrontata col Percorso A entro 1e-9 simbolica / 1e-6 numerica (FR-10) — e i
    segnaposto legati allo scope del nodo del `ProofGraph` (FR-13, AD-4 em.) non
    esistono.
  evidence: Bloccati da prerequisiti che non sono stati costruiti, non da lavoro
    mancante in questa storia. Il confronto ha bisogno del **Percorso A**, che è la
    Story 2.5 (`2-5-percorso-a-analisi-nodale-modificata-simbolica: backlog`): un
    braccio del confronto non esiste, e misurare l'accordo con sé stessi non è un
    controllo indipendente — è l'autocertificazione che AD-22 chiude altrove. I
    segnaposto hanno bisogno del `ProofGraph` (nessun nodo a cui legare uno scope) e
    di `render/serialize`, a cui AD-19 assegna `placeholder_unbound`: emetterlo da
    `domain/transform` sarebbe una modifica dello spine. Questa storia chiude i primi
    due blocchi di criteri; il terzo si riapre quando 2.5 è fatta e il `ProofGraph`
    esiste.

- source_spec: `spec-2-6-catalogo-delle-trasformazioni.md` (riparazione P1-6, 25/08/2026)
  summary: `_senza` porta `source_kind` a `generated` su ogni `Cₖ₊₁`, e la distinzione fra un
    circuito letto da netlist e uno letto da fotografia sparisce per sempre a valle del primo
    passo di riduzione.
  evidence: La decisione è argomentata nel docstring di `_senza` ed è corretta rispetto allo
    schema — `Cₖ₊₁` non è stato letto da nessuna parte, è stato calcolato — ma nessun documento
    di autorità la registra. La conseguenza non è locale: `domain/validate` emette il sospetto
    E12/E24 sui resistori fuori serie **solo** quando `source_kind == "image"`, quindi dopo una
    riduzione quel sospetto non nasce più, anche su un circuito che viene da una fotografia.
    Se la distinzione debba sopravvivere alla riduzione — per esempio con un campo che ricorda
    l'origine della catena — è una decisione di contratto, non di implementazione.

- source_spec: `spec-2-6-catalogo-delle-trasformazioni.md` (riparazione P1-6, 25/08/2026)
  summary: La provenienza fotografica dei componenti sopravvissuti viene azzerata su `Cₖ₊₁`.
  evidence: Segue dalla decisione precedente: lo schema vieta un'area di provenienza su una
    sorgente che non è un'immagine. Il docstring sostiene che non è una perdita perché
    «l'ancoraggio vive su `C₀`, dove la conferma dell'utente avviene, e il `Delta` tiene il filo
    fra i due». È vero per i componenti, ed è verificato. Ma la risalita a `C₀` attraverso una
    catena di più passi non è né implementata né testata: `Delta` è per passo, e nessun oggetto
    tiene oggi la catena. FR-40 (ancoraggio di provenienza) ne dipende.

- source_spec: `spec-2-6-catalogo-delle-trasformazioni.md` (riparazione P1-6, 25/08/2026)
  summary: Una `Request` il cui bersaglio viene consumato resta su `Cₖ` e non viaggia su `Cₖ₊₁`.
  evidence: La decisione è giusta e ben argomentata — ridirigere la richiesta sull'equivalente
    cambierebbe di nascosto la domanda dell'utente, perché la tensione ai capi di `R1` non è
    quella ai capi di `R1+R2`. Ma il docstring affermava che «non si perde: `what_happened_to` la
    ritrova», e questo è impreciso: il `Delta` ritrova il **componente** `R1`, non la **richiesta**
    `q1`, il cui identificatore e la cui grandezza vivono solo su `Cₖ`. La ricostruzione presuppone
    quindi che chi risale conservi `Cₖ`, e nessun test lo dimostra. Precisato nel docstring;
    chi debba conservare la catena dei circuiti resta una decisione aperta.

- source_spec: `escalation-cause-v2-irraggiungibili.md` (decisione owner del 25/08/2026, uscita B)
  summary: `identity_violation` resta dichiarata in `Cause` e senza alcun produttore in tutto
    `src/`, dopo che il ritiro di `node_mapping` (AD-22 v2.2) ha reso l'uguaglianza degli
    identificatori su `Pₖ` vera per costruzione.
  evidence: Rimuoverla dall'enumerazione tocca la tabella di AD-19, che è spine: è una decisione
    architetturale, non un effetto collaterale di una patch. Fino ad allora tre docstring
    affermano un'emissione che non avviene — `check.py` in testa al modulo, `refusal.py` nella
    motivazione dell'aggiunta, e la riga della tabella. La causa non è dannosa: è una superficie
    dichiarata e irraggiungibile, che il prossimo lettore cercherà di produrre senza riuscirci.

- source_spec: `escalation-cause-v2-irraggiungibili.md` (decisione owner del 25/08/2026, uscita B)
  summary: L'uscita A — le Trasformazioni **dichiarano** `preserve` invece di farselo derivare —
    resta possibile e non è stata implementata.
  evidence: Oggi `transform()` è l'unico produttore reale del contratto e `check_transform` ha un
    solo consumatore in produzione: pagare 16 dichiarazioni duplicate costruirebbe un meccanismo
    per un produttore esterno che non esiste. La pipeline di percezione dovrà produrre una
    rappresentazione semantica **da confermare**, e il renderer deve **consumare** `LayoutPatch`,
    non diventare un secondo produttore della verità trasformativa. Se un vero produttore
    dichiarativo comparirà, servirà una decisione architetturale esplicita — e con essa il
    `Certificate` potrà tornare ad attestare la massimalità, perché a quel punto sarà verificata.

- source_spec: `spec-2-6` → **Story 1.4** (differimento esplicito, 25/08/2026)
  summary: L'unità semantica di `reroute_scope` non è decisa. Domanda di accettazione per 1.4:
    *«Qual è l'unità semantica contenuta in `reroute_scope`: componenti, nodi, branch/edge
    renderizzabili, o altro?»*
  evidence: Il docstring lo definiva «l'insieme dei rami la cui instradatura è libera» mentre il
    motore vi scrive il componente creato più i **nodi** del boundary: nemmeno il produttore
    interno rispettava la semantica dichiarata. La descrizione è stata resa fedele al fatto invece
    di continuare a contraddirlo, e `check_patch` verifica ciò che è verificabile senza la
    risposta — nessun fantasma, insieme non vuoto. È un blocker reale di 1.4 perché FR-38 lo usa
    come vincolo **normativo** del renderer. Se arrivare a 1.4 richiedesse questa decisione prima,
    il loop deve fermarsi con `ARCHITECTURE_CONFLICT` invece di indovinare.
