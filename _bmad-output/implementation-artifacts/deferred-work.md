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

- source_spec: Story 1.2 — residui della passata fresca (26/08/2026)
  summary: Due LOW restano aperti dopo la promozione di 1.2, più la disallineatura del ledger che
    entrambe le revisioni hanno segnalato.
  evidence: (1) `_verifica_dormienti` non impone `dormienti ⊆ PRIMITIVES`: un nome dormiente
    inventato non farebbe protestare nulla. (2) Il docstring di `primitives.py:20` — «entrambi i
    registri sono stati aggiornati con l'esito» — ha un antecedente ambiguo che fa sembrare falso
    un claim vero. (3) **`sprint-status.yaml` non registra né 1.1 né 1.2**: le voci `1-1-…` e
    `1-2-…` presenti appartengono alla numerazione v1, già dichiarata stale. Le due storie
    implementate più di recente sono invisibili nel tracker. Il loop non ne dipende — avanza
    leggendo gli artefatti di implementazione, non il ledger — ma chiunque legga il tracker vede
    uno stato falso. Allinearlo tocca 46 chiavi ed è una decisione, non una patch.

- source_spec: `spec-1-4-serializzatore-svg-semantico-deterministico-su-una-fixture-a.md`
    (Story 1.4, 26/08/2026) — **risposta alla domanda di accettazione differita a 1.4**
  summary: `reroute_scope` non è stato deciso, e 1.4 non lo richiede: la voce sopra chiedeva di
    fermarsi con `ARCHITECTURE_CONFLICT` **se** arrivare a 1.4 avesse richiesto la decisione.
    Non l'ha richiesta. La domanda resta aperta e va portata alla Story 1.7.
  evidence: Misurato sul codice, non dedotto. Questa storia non consuma alcun `LayoutPatch` —
    `applica` non esiste, ed è dichiarata contratto della Story 1.7 in
    `render/layout/__init__.py` — quindi non reinstrada nulla di preesistente: `_percorso`
    calcola ogni filo da zero a ogni `render`, e due `render` sullo stesso `LayoutIR` danno gli
    stessi byte proprio perché non c'è stato da conservare fra l'uno e l'altro. I fili non sono
    entità: `EntityKind` è `Literal["component", "node"]` (`domain/transform/delta.py:67`), non
    hanno posizione nel `LayoutIR` e non compaiono in alcun `preserve`. Ne segue che nessuna
    delle quattro letture candidate — componenti, nodi, branch/edge renderizzabili, altro —
    cambia un byte di ciò che 1.4 emette, e sceglierne una qui l'avrebbe chiusa per inerzia
    senza che alcun test potesse vederla sbagliata. **Dove morde davvero:** FR-38 usa
    `reroute_scope` come vincolo normativo — *«il numero di elementi con coordinate cambiate è
    limitato allo `reroute_scope` dichiarato»* — e quel conto esiste solo dentro l'applicatore
    di patch. È lì che la decisione serve, ed è lì che va presa.

- source_spec: `spec-1-4-serializzatore-svg-semantico-deterministico-su-una-fixture-a.md`
    (Story 1.4, 26/08/2026)
  summary: Quale dei due nomi di un componente lo studente debba **leggere** sul disegno —
    `Component.id` o `Component.symbolic` — non è deciso da nessuna autorità.
  evidence: I due esistono e differiscono: in `reference-set/dev/dc-00001.json` valgono `E1` ed
    `E_1`. Il disegno mostra l'`id`, come già faceva, e la scelta non è stata presa qui: nessun
    documento dice quale dei due sia il nome che il testo dell'esercizio usa, e deciderlo in un
    serializzatore significherebbe fissare in un modulo una convenzione di notazione che FR-16
    assegna al Profilo curricolare. Ciò che è stato chiuso è la **perdita**: `symbolic` esce ora
    in `data-component-symbolic`, perché AD-10 fa di questo SVG la sorgente unica di ogni altro
    formato e un nome che non entra nei byte non è più recuperabile a valle. La decisione tocca
    D2 — il primo Profilo curricolare reale — e va presa con quella.

- source_spec: `spec-1-4-serializzatore-svg-semantico-deterministico-su-una-fixture-a.md`
    (Story 1.4, 26/08/2026)
  summary: `DESIGN.md` non ha un token per lo spessore di tratto **dello schema**, e il renderer
    ne ha dovuto dichiarare uno.
  evidence: I quattro componenti di `DESIGN.md` che dichiarano uno `strokeWidth` —
    `provenance-anchor` (2px), `subgraph-highlight` (2px), `boundary-anchor` (1.4px),
    `unchanged-marker` (1px) — sono tutti **overlay**: annotano il disegno, non lo sono. Il
    circuito stesso non ha un token. `svg.py` dichiara `TRATTO = 3/2` e lo emette come
    `stroke-width` sulla radice più la proprietà `--kf-tratto` nel foglio di stile, così che un
    braccio possa ridefinirlo senza toccare il renderer (AD-26). Resta che il valore è stato
    scelto qui e non in `DESIGN.md`, che è dove i token vivono: il numero è dichiarato e
    sostituibile, ma la riga di `DESIGN.md` manca e la deve scrivere chi possiede il documento.
    Nota di coerenza: `boundary-anchor` è dichiarato *«deliberatamente più discreto»* del segnale
    sul delta, e a 1.4px contro 1.5 lo è appena — la relazione fra i due spessori è un'altra cosa
    che solo il proprietario di `DESIGN.md` può fissare.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: La scala dei layer di AD-23 **non ha una riga per l'equazione**, che UX-DR10 e
    `EXPERIENCE.md` richiedono entrambi accanto al sottografo. Il renderer la emette al `6` e lo
    dichiara; la riga la deve scrivere chi possiede lo spine.
  evidence: I nove livelli sono `0` sfondo · `1` regione di trasformazione · `2` fili · `3`
    componenti · `4` nodi ed etichette semantiche · `5` enfasi sul cambiato · `6` annotazioni di
    boundary · `7` interazione · `8` debug, e AD-23 aggiunge *«il renderer non compone layer fuori
    da questa scala»*. Nessuno dei nove nomina l'equazione: il `6` dice «di boundary», il `5` dice
    «sul cambiato», e l'equazione non è né l'una né l'altra — è un'annotazione **ancorata** al
    sottografo. `render/overlay/schema.py` sceglie il `6` insieme alle altre annotazioni ancorate
    del passo e lo scrive come assunzione dichiarata, non come se AD-23 lo prescrivesse. È la
    stessa forma dell'assunzione che la Story 1.3 ha dichiarato per il `PatchStore`, che AD-8 non
    nomina. Va ratificata, non ereditata per inerzia.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **AD-23 em. e `DESIGN.md` collidono sul `boundary-anchor`**, e l'uscita di oggi viola
    il predicato di non-occlusione così com'è scritto. Non è una svista del renderer: è un
    conflitto fra due autorità, e la regola di collisione della costituzione dice che si segnala,
    non si sceglie.
  evidence: AD-23 em. chiede che *«nessun riquadro di livello ≥ 5 intersechi il riquadro di
    un'entità di livello 4 appartenente a `Pₖ`»*. `DESIGN.md:177` dichiara il `boundary-anchor`
    *«un segno **sovrapposto**»* al nodo, e *«togliendolo, il nodo torna identico»* — un segno
    sovrapposto interseca per definizione ciò su cui sta. Questa storia è la prima che emette
    entrambi. Misurato sull'uscita corrente, entrambi i fotogrammi: l'ancora del nodo `0` occupa
    `[95.5,104.5]×[155.5,164.5]` e interseca due riquadri di livello 4 del nodo `0`, che è in
    `preserve` — il pallino della giunzione `[97,103]×[157,163]` e il simbolo di massa
    `[93,107]×[160,176]`; l'ancora del nodo `b` interseca il pallino di `b`. Tre intersezioni, e
    il predicato come scritto le vieta tutte e tre.
    Ciò che questa storia ha potuto chiudere è la metà che non dipende dalla collisione, e l'ha
    chiusa come **test permanente** invece che come prosa
    (`test_nessuna_annotazione_occlude_un_preservato_salvo_l_ancora_sul_proprio_nodo`, per
    fotogramma): nessuna annotazione tocca l'**etichetta** di un preservato — che è l'aneddoto da
    cui AD-23 nasce — e l'unica intersezione ammessa è quella di un'ancora con la geometria del
    nodo su cui è centrata. Il conteggio è fissato a 3: se scendesse a zero il test starebbe
    misurando un'uscita senza ancore invece di un predicato soddisfatto.
    **Rettifica di una voce precedente di questa stessa storia.** La prima stesura attribuiva ad
    AD-26 l'incalcolabilità del predicato dentro `render/`, sostenendo che il `TransformOverlay`
    non poteva portare `preserve`. Era sbagliato: `preserve` è un membro di `TransformResult`
    esattamente come `boundary`, e portarlo è una **copia**, non il ricalcolo di `Pₖ` che AD-26
    chiama velenoso — quello sarebbe dedurlo dai due circuiti o da «tutto ciò che l'overlay non
    nomina». AD-26 em. enumera del resto i ruoli come `preservato · cambiato · confine`: sono tre.
    L'overlay ora porta il terzo, il predicato **è** calcolabile, e ciò che resta aperto è solo la
    collisione fra le due autorità. Resta a 1.6 il canale d'emissione: AD-23 vuole
    `overlay_occlusion` da `render/roundtrip`, che non esiste ancora.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **Un nodo consumato non ha un segnale dichiarato in `DESIGN.md`.** Il renderer gliene
    dava uno preso in prestito; ora non gliene dà nessuno, ed è una riga che manca alla tabella.
  evidence: `subgraph-highlight` porta la nota *«Marca **SOLO i componenti** che cambiano»*, e la
    sequenza di `DESIGN.md:430-432` distribuisce i segnali per genere: i componenti che cambiano
    ricevono l'evidenziazione, i nodi di boundary il `boundary-anchor`. La tabella dei segnali
    (`:382-384`) ha tre righe — il delta, i preservati-e-boundary, i preservati — e **nessuna** per
    un nodo che la riduzione assorbe. `serie` ne assorbe uno: sulla fixture della storia
    `overlay.cambiato` contiene `node:a`. La prima stesura gli dava il segnale dei componenti; era
    una decisione del renderer, e misurata produceva il difetto esatto dell'aneddoto di AD-23 — il
    riquadro finiva a `x=208`, l'etichetta del nodo `a` comincia a `x=208`, tratto 2 centrato sul
    bordo, cioè evidenziazione sopra il primo tratto del nome. Oggi il nodo consumato non riceve
    nulla e il test `test_il_sottografo_marca_solo_i_componenti` lo tiene chiuso. Che sia il
    trattamento **giusto** non è deciso da nessuno: lo studente vede sparire un nodo senza che
    niente lo abbia acceso. La riga la scrive chi possiede `DESIGN.md`.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: Due quantità di `equation-anchor` non hanno un token dietro: il **fondo** del riquadro
    e lo **spessore della linea di collegamento**. Sono dichiarate nel modulo, non copiate.
  evidence: `DESIGN.md:206-212` dà a `equation-anchor` `background: '{colors.surface-raised}'` e
    `border: '1px solid {colors.rule-hairline}'`. Il bordo ora è `1` ed è il token (la prima
    stesura emetteva `1.4`, che è lo spessore del `boundary-anchor` — *«deliberatamente più
    discreto del segnale sul delta»* — e legava due quantità che i token tengono separate;
    `test_il_bordo_dell_equazione_e_quello_del_token` lo tiene chiuso). Il **fondo** no: la tinta
    dei token non è emessa da `svg.py` — `TINTA` spiega perché, e D4 è aperta — quindi il riquadro
    esce `fill="none"`. È una dichiarazione, non una copia, e la ragione per cui è quella e non
    un'altra è che un riquadro pieno di `currentColor` coprirebbe ciò che ha dietro. Lo
    **spessore della linea di collegamento** non ha token affatto: `equation-anchor` la chiede
    (*«collegata da una linea»*) e non la quantifica. Vale quanto il bordo del riquadro, che è
    l'unica relazione che i token permettono di affermare. Entrambe stanno accanto a `TRATTO`, già
    registrato dalla Story 1.4 per la stessa ragione: il token manca, non è stato inventato.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **La firma di `render` non sa esprimere i passi 3 e 4 della sequenza di
    `EXPERIENCE.md`**: layer 5 e layer 6 escono da una sola chiamata, e non c'è un fotogramma in
    cui il sottografo è acceso e nessun testo del passo è comparso. La Story 1.8 la incontra per
    prima.
  evidence: `EXPERIENCE.md:466-472` numera tre battute distinte: (3) *«`R3` e `R4` si accendono
    … Non è ancora comparso un solo carattere di testo»*, (4) **PRIMA**, (5) **AZIONE** con
    l'equazione. `render(circuito, layout, overlay)` emette `5` e `6` insieme: non esiste un
    parametro che accenda l'evidenziazione senza l'equazione. Misurato: il fotogramma *Prima*
    porta già `R1R2eq = R1 + R2`, che nomina un'entità che `Cₖ` non contiene, con una linea che vi
    punta. La lettura di UX-DR8 che questa storia ha preso — l'evidenziazione prima di ogni testo
    **del passo**, non di ogni `<text>` del file — resta corretta e verificata
    (`test_il_sottografo_si_accende_prima_di_qualunque_testo_del_passo`), ma la sequenza che la
    giustifica non è producibile da questa firma. Aggiungere un parametro di fase qui avrebbe
    inventato un'API che AD-35 non nomina: la firma dello spine è
    `render(LayoutIR, TransformOverlay, ArmEncoding)`, tre parametri e nessuna fase.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: Il **`certificate-chip`** — terza delle *«tre cose, in ordine di comparsa»* — non ha
    alcuna rappresentazione, e `Certificate` non arriva al renderer.
  evidence: `DESIGN.md:435-440` elenca tre cose in ordine di comparsa: evidenziazione, equazione,
    certificato. Il renderer ne implementa due, e si appoggia proprio a quell'elenco per decidere
    la lettura di UX-DR8. `Certificate` è un membro di `TransformResult`; `TransformOverlay` non lo
    porta e `render/` non lo nomina mai (verificato: zero occorrenze). `EXPERIENCE.md:190-191`:
    *«Un passo a cui manca `CERTIFICATE` … non è un passo, e non compare.»* Nessun AC della Story
    1.7 lo chiede — gli AC visuali sono UX-DR8 e UX-DR10 — quindi non è stato costruito: portarlo
    avrebbe richiesto di decidere che cosa il chip mostra e dove, cioè lavoro di 1.8 fatto qui.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **Gli elementi dei layer 5 e 6 non portano alcun `data-*`**, e nulla dice se il
    round-trip di FR-41 debba ignorarli o rifiutarli. La Story 1.6 li incontra senza una regola.
  evidence: Misurato: nessuno dei cinque elementi emessi — `kf-sottografo`, `kf-confine`,
    `kf-collegamento`, `kf-equazione`, `kf-equazione-testo` — porta un attributo `data-*`, mentre
    ogni elemento dei layer 2–4 ne porta. FR-41 riparsa le annotazioni per ricostruire il
    `CircuitIR`: un elemento senza annotazioni è invisibile a quel parser, il che è probabilmente
    corretto — l'overlay non è il circuito — ma non è **scritto** da nessuna parte, e la storia che
    lo scriverà (1.6) precede questa nel backlog e non è fatta. Conseguenza già visibile qui: il
    test del predicato di AD-23 deve attribuire le etichette del layer 4 alle proprie entità
    leggendo le strutture (`_scritte_del_simbolo`, `_scritte_del_nodo`) invece dei byte, perché dal
    solo SVG un'etichetta non è attribuibile.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **`<title>` e `<desc>` sono byte-identici con e senza overlay**: chi legge con un
    lettore di schermo non sente la trasformazione, sente due volte lo stesso circuito.
  evidence: Misurato e fissato in `test_l_alternativa_testuale_non_cambia_con_l_overlay`. UX-DR25
    e FR-15 danno all'alternativa testuale la topologia, e la topologia dei due fotogrammi è
    davvero diversa — quindi *Prima* e *Dopo* differiscono, ma solo per la frase di topologia: né
    l'evidenziazione, né il confine, né l'equazione compaiono in forma testuale. K-0 dice che un
    passo senza disegno non è un passo; per chi il disegno non lo vede, il passo oggi non ha una
    forma. Non è un criterio di questa storia e non è stato costruito; è una misura, non
    un'impressione.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: **FR-53 «identico byte per byte» ha due letture, e la seconda tocca D4**, che è aperta
    e blocca Gate A. La storia ha implementato e verificato la prima, e ha misurato la seconda.
  evidence: FR-53, seconda *Consequence (testable)*: *«Rimuovendo l'overlay, il rendering delle
    entità sottostanti è identico byte per byte a quello senza trasformazione in corso»*; AD-23 em.
    la qualifica *«nei bracci 0 e A»* e FR-46 la rende obbligatoria. La famiglia ora esiste —
    `test_rimosso_l_overlay_il_layer_delle_entita_e_identico`, sei casi: layer `2`, `3`, `4` per
    entrambi i fotogrammi, confrontati sui **byte emessi** e non su un sottoalbero riserializzato.
    La seconda lettura — «il rendering» come ciò che finisce a schermo — non è soddisfatta e non
    può esserlo da sola: l'equazione **deve** stare fuori dal disegno (UX-DR10), quindi la
    `viewBox` cresce necessariamente. Misurato sul fotogramma *Dopo*: da `-24 -28.8 279 216.8`
    senza overlay a `-24 -28.8 493.4 216.8` con overlay,
    stessa origine e stessa altezza, larghezza maggiore; e l'`<svg>` non porta `width`/`height`,
    quindi scala col contenitore (UX-DR27) e ogni entità preservata si rimpicciolisce. Quale
    lettura governi non è deciso da nessuna autorità, e deciderlo nel renderer chiuderebbe per
    inerzia **D4**, *«renderer stack web vs PDF»*. La misura è fissata in
    `test_l_overlay_allarga_la_viewbox_e_questo_e_dichiarato` perché chi decide D4 la trovi.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: `annota` ammette un caso — una fusione che **atterra su un'entità preservata** — che il
    renderer non saprebbe disegnare sul fotogramma successivo. Non è raggiungibile dal Catalogo di
    oggi, ed è misurato.
  evidence: `annota` calcola `cambiato = (consumed | produced) - preserve`, e sottrae `preserve` e
    non `boundary` perché *«una fusione può atterrare su un'entità preservata»* — `check_delta` lo
    ammette (`check.py:292-293`). Per un prodotto simile `cambiato = delta.consumed`, tutto in
    `patch.remove`, quindi assente da `LayoutIR_{k+1}`: `_verifica_l_ordine_dell_overlay`
    solleverebbe sul fotogramma *Dopo*, e K-0 dice che un passo senza disegno non è un passo — un
    passo legittimo per il dominio avrebbe un *Dopo* non disegnabile. Misurato sul Catalogo
    corrente: `implemented()` è `{serie, parallelo}` e le due riduzioni passano dallo stesso
    percorso, che pone `create=(prodotto,)` con `prodotto` coniato da `engine._nuovo_id` — un nome
    nuovo, quindi mai in `preserve`. Il caso **non è raggiungibile oggi**. Che cosa il fotogramma
    successivo debba accendere quando il punto d'atterraggio è preservato è una domanda per chi
    apre il Catalogo, e la risposta userà il ruolo `preservato` che l'overlay ora porta.

- source_spec: Story `1-7-la-prima-trasformazione-pedagogica-fino-al-disegno` (26/08/2026)
  summary: L'equivalente nasce nel **baricentro** dei suoi ascendenti, che non appartiene al
    percorso fra i suoi due morsetti: i fili escono a gomito. È una conseguenza misurata della
    scelta dichiarata, non un difetto contro un'autorità — ma nessuna autorità la ratifica.
  evidence: Misurato sul fotogramma *Dopo*: `R1R2eq` è disegnato in `(150,40)`, il baricentro
    esatto di `R1(100,0)` e `R2(200,80)`; i suoi morsetti stanno su `b(0,0)` e `0(100,160)`, e i
    fili emessi sono `150,16 150,0 0,0` e `150,64 150,160 100,160` — due gomiti attorno a un
    simbolo posato a un'ascissa dove non sta nessuno dei suoi due nodi. La scelta è quella che
    risponde alla domanda della storia (*«quelle due sono diventate questa»*: l'equivalente compare
    dove stavano le due, ed è verificato sul disegno da
    `test_l_equivalente_e_disegnato_dentro_l_ingombro_delle_due_che_sostituisce`), e l'alternativa
    — posarlo sul percorso `b–0` — sarebbe autolayout, non-goal dichiarato. `EXPERIENCE.md:470`
    dice *«`R3` e `R4` diventano `R34`, sempre fra `A` e `B`»*, e topologicamente lo è. Se il
    gomito sia accettabile davanti a uno studente è una domanda di Gate A, e la risposta appartiene
    a chi possiede `DESIGN.md` e all'instradatore dei fili di `render/serialize/geometry.py`, non a
    `applica`.
