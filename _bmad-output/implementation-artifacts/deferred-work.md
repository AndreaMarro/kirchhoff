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
  status: **CHIUSA il 25/08/2026 dalla Story 1.1**, e sostituita dalla voce qui sotto.
  summary: `identity_violation` non è più senza produttore: `check_transform` la emette, ed è
    raggiungibile anche dal motore (misurato sostituendo `_nuovo_id` con una funzione che riusa
    l'identificatore del primo consumato: `serie` e `parallelo` restituiscono entrambe
    `Refusal(identity_violation, R1)`).
  evidence: La voce affermava che la causa «resta dichiarata in `Cause` e senza alcun produttore
    in tutto `src/`», e dal 25/08/2026 è falsa. I tre docstring che affermavano un'emissione che
    non avveniva sono stati aggiornati con la storia. Ciò che resta aperto non è più l'assenza di
    un produttore ma la **semantica** di ciò che viene emesso: vedi la voce successiva.

- source_spec: `spec-1-1-l-identita-preservata-dev-essere-giustificata-non-dichiarata.md`
    (Story 1.1, 25/08/2026) — **decisione da portare al proprietario**
  summary: La semantica emessa di `identity_violation` non è quella che AD-19 le assegna, e la
    forma che AD-22 v2.1 dichiara rappresentabile è ora rifiutata. Due clausole owner-locked sono
    contraddette dal codice.
  evidence: Tre fatti misurati, non dedotti.
    (1) AD-19 (`ARCHITECTURE-SPINE.md:435`) definisce la causa come `id_{k+1}(x) ≠ id_k(x)` per un
    `x ∈ Pₖ`; il codice la emette per `x ∉ Pₖ` presente in entrambi i circuiti. Dopo il ritiro di
    `node_mapping` la definizione dello spine è vuota per costruzione, quindi la causa è stata
    **riusata** con un significato nuovo invece che rimossa.
    (2) AD-22 v2.1 (`:555-558`) dice che la `R1` dell'istruttoria R2-A «è una rimozione più una
    creazione, e come tale deve comparire nel `Delta`» e che «**nessuna causa nuova serve** …
    ⇒ `preserve_nonmaximal`». Il codice rifiuta quella forma con `identity_violation`, prima e
    indipendentemente da ciò che il produttore dichiara.
    (3) La conseguenza si estende oltre il caso R2-A: una fusione di nodi che sposti i terminali di
    un componente **sopravvissuto** è ora rifiutata. Misurato su `{R1(n1,0), R2(n2,0)} →
    {R1(n1,0), R2(n1,0)}` — il caso di `tests/test_delta.py::test_una_preservata_PUO_essere_uscita`
    — che restituisce `Refusal(identity_violation, R2)`. Nessuna delle due riduzioni del catalogo
    la produce, quindi nulla è rotto oggi.
    La Story autorizzava il **rifiuto** («viene rifiutata, e il rifiuto nomina l'entità e la
    trasformazione»), non la scelta della causa né la riscrittura tacita di due clausole dello
    spine. Le due uscite possibili: (A) emendare AD-19 perché `identity_violation` significhi
    «identificatore presente in entrambi che non nomina la stessa entità», e AD-22 v2.1 perché il
    nome riusato sia rifiutato e non rappresentabile; (B) emettere `preserve_nonmaximal`, come
    AD-22 v2.1 dice, e lasciare `identity_violation` senza produttore. La (B) costa il rifiuto
    indipendente dalla dichiarazione, che è il punto della storia: un `preserve` onesto che non
    rivendica `R1` non produrrebbe alcuna causa. È una modifica dello spine in entrambi i casi, e
    lo spine è del proprietario.

- source_spec: `spec-1-1-l-identita-preservata-dev-essere-giustificata-non-dichiarata.md`
    (Story 1.1, 25/08/2026)
  summary: Per i **nodi** il controllo d'identità è vuoto per costruzione: un nodo che sopravvive
    per nome entra sempre in `Pₖ`, qualunque sia la sua incidenza.
  evidence: `check._divergenze` assegna `frozenset()` a ogni nodo sopravvissuto, perché in questo
    IR un nodo **è** il proprio nome e la sua incidenza non è un suo campo ma una proprietà
    derivata dai terminali dei componenti. Un produttore che consumasse il nodo `b` e ne creasse
    uno nuovo con incidenza completamente diversa, chiamandolo ancora `b`, otterrebbe `b ∈ Pₖ`:
    misurato su `{R1(a,b), R2(b,0)} → {R3(a,b), R4(b,0), R5(b,0)}`, dove `b` passa da grado 2 a
    grado 3 e nessun componente sopravvive. Ciò che rivela il riuso **indirettamente** è che i
    componenti attorno cambiano terminali, e quelli il confronto li vede. Il limite è ora
    dichiarato nel docstring di `_divergenze` e **pinnato** da
    `test_per_i_nodi_il_controllo_e_vuoto_per_costruzione`, che diventerebbe rosso se il contratto
    cambiasse. Definire l'identità di un nodo per incidenza è una decisione di contratto — nessun
    documento oggi dice che cosa sia l'identità di un nodo — non un effetto collaterale di un
    modulo. AC1 parla di «entità», e i nodi lo sono: è la ragione per cui la voce è qui e non
    chiusa in silenzio.

- source_spec: `spec-1-1-l-identita-preservata-dev-essere-giustificata-non-dichiarata.md`
    (Story 1.1, 25/08/2026) — **decisione da portare al proprietario**
  summary: `type` è dichiarabile mutabile: una voce del Catalogo potrebbe licenziare un
    condensatore che diventa resistore «restando la stessa entità». Nessuna guardia lo vieta.
  evidence: La scelta di non vietarlo è deliberata e scritta in `catalog.py`: AD-22 v2.1 porta come
    esempio *illustrativo* proprio questo caso — «la disattivazione di un generatore indipendente
    **potrebbe** essere una di queste — stessa entità, stato cambiato» — e un generatore
    disattivato modellato come corto circuito **è** un cambio di `type`. Vietarlo in un modulo
    deciderebbe in anticipo una questione che lo spine lascia aperta al vocabolario delle primitive
    strutturali. **Aggiornamento del 26/08/2026 (Story 1.2): quel vocabolario ora esiste —
    `domain/transform/primitives.py`, cinque riscritture chiuse — e continua a non decidere la
    questione.** Nessuna delle cinque nomina la soppressione di un generatore, e l'assenza è
    deliberata per la stessa ragione registrata qui: darle un nome sceglierebbe in un modulo la
    lettura «sostituzione strutturale con identità nuova». La decisione resta al proprietario, e
    la premessa su cui poggia è ora questa, non più «il vocabolario non esiste». Il posto dove
    dichiarare il caso nuovo è `test_la_soppressione_di_un_generatore_non_e_nel_vocabolario`, che
    pinna l'insieme per intero e diventa rosso il giorno in cui una sesta riscrittura compare.
    La licenza resta quindi **esprimibile e non esercitata**:
    nessuna voce di `_MUTABILI` la concede, e
    `test_il_tipo_resta_licenziabile_e_non_e_licenziato_da_nessuno` diventerebbe rosso il giorno in
    cui una la concedesse. Se il proprietario decide che il cambio di tipo non è mai identità
    conservata, la riga da aggiungere è una guardia in `_verifica_dichiarazione`.

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

- source_spec: `spec-1-1-l-identita-preservata-dev-essere-giustificata-non-dichiarata.md`
    (Story 1.1, 25/08/2026)
  summary: La Story 1.1 «L'identità preservata dev'essere giustificata, non dichiarata» non ha una
    riga in `development_status` di `sprint-status.yaml`.
  evidence: Lo scheduler l'ha selezionata da `epics.md`, dove vive, ma il tracker non la conosce:
    la sola `1-1-*` presente è `1-1-insieme-di-riferimento-strutturato-a-risposta-nota: done`, che è
    l'altra Story 1.1. Non l'ho aggiunta io perché lo stato di una storia sotto revisione lo scrive
    la promozione del loop, in un commit separato («Promozione: … (nessuna Story corrente marcata
    done)»), e un implementatore che scrive lo stato della propria storia è la forma di
    autocertificazione che questa storia esiste per chiudere. Va aggiunta con lo stato che il loop
    decide, non con quello che l'implementatore vorrebbe.

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

- source_spec: `ramo loop/iter-20260824T211636Z` — residui della sesta tornata di Blind Hunter
  summary: Tre MEDIUM e quattro LOW restano aperti sul contratto di dominio, tutti su superfici
    che il motore interno non raggiunge. Il ramo è stato promosso con 0 CRITICAL e 0 HIGH.
  evidence: (1) `check_boundary` condanna con diagnosi fattualmente falsa qualunque componente nel
    boundary — `_terminali` produce solo nodi, quindi «non adiacente» descrive un difetto diverso
    da quello reale, che è «non è un nodo»; il tipo ammette componenti e la terza condizione è
    imposta strutturalmente senza essere dichiarata. (2) `attributes_of` è una seconda definizione
    parziale del confronto d'identità, esportata, e il suo docstring non dice che i terminali vanno
    orientati. (3) Il docstring di `CONTROLLI` promette «nell'ordine in cui girano» un ordine che
    non è quello di esecuzione — l'attestato è vero nel contenuto e falso nella pretesa d'ordine.
    (4) `CatalogOpening` accetta campi di soli spazi, l'incompletezza che il suo stesso docstring
    dichiara di rifiutare. (5) `transform(ir, "parallelo", "R1", "R1")` — stesso componente due
    volte — sfugge alle porte tipizzate e muore in `_ordinate` con una diagnosi che non nomina né
    l'operazione né l'argomento. Nessuno di questi è raggiungibile dal motore, che è l'unico
    produttore reale; tutti lo sono dalla porta pubblica che la decisione owner del 25/08 conserva.

- source_spec: Story 1.1 — residui della ri-revisione a contesto fresco (26/08/2026)
  summary: Un MEDIUM e due LOW restano aperti dopo la promozione di 1.1. Nessuno tocca la
    correttezza del contratto; tutti e tre sono discrepanze fra ciò che il codice dichiara e ciò
    che fa.
  evidence: (1) La diagnosi di `attestazione_infondata` afferma una causa che il controllo non
    conosce, ed è falsa se il vero motivo è un altro. (2) Il commento del motore dichiara un
    conteggio misurabile e sbagliato: `_divergenze` gira sette volte, non il numero scritto.
    (3) Il criterio enunciato per l'elenco `CONTROLLI` è contraddetto dalla voce `boundary` due
    righe sotto — lo stesso rilievo già emerso nella sesta tornata manuale, che sopravvive.
