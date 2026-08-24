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
