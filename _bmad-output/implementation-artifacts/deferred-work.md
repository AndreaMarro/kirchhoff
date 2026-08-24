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
