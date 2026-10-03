# Versione studente del 13 settembre 2026

Andrea ha autorizzato in questa sessione lo sviluppo diretto con Codex, in eccezione al requisito del Loop. Base: `5ff9bd6`, comprensiva delle correzioni P1A/P1B. Branch locale: `codex/student-product-20260913`. Nessuna modifica ai confini owner-locked, al catalogo dei certificati o alle soglie.

## Prodotto utilizzabile

La pagina principale apre l'esperienza studente, con un circuito alla volta, frecce avanti/indietro, spiegazione sotto il disegno, ritorno all'originale, modalità ingrandita e PDF vettoriale scaricabile. Il vecchio Proof Workbench rimane disponibile come strumento tecnico tramite `?view=proof`.

Il backend accetta circuiti nuovi; il catalogo non è una simulazione del backend. I quattro esercizi distribuiti e tutti i loro percorsi sono generati dalla stessa funzione usata per i circuiti dell'utente. La lavagna permette di posare R/V/I e fili su nodi espliciti, anche tramite trascinamento. La trascrizione mantiene orientazioni e valori esatti. Il collegamento dei fili è testato anche nei punti intermedi.

Le foto possono essere caricate o trascinate, confrontate localmente e ricostruite nella lavagna o nell'editor. È presente un adattatore OpenAI per la trascrizione automatica: non è stato chiamato su un'API reale in questa sessione, perché chiave e modello non sono configurati. La conferma dei dati rimane obbligatoria dopo il riconoscimento. Il disegno libero a mano non viene riconosciuto senza un adattatore visivo: la lavagna incorporata usa componenti e fili.

## Metodi effettivi e limiti

| Metodo | Ambito implementato |
|---|---|
| Partitori di tensione/corrente | Rami resistivi riconosciuti, valori SI esatti, ritorno ai componenti originali |
| Millman | Rami a due morsetti con resistenze, sorgenti indipendenti, segni e rami a tensione imposta |
| V+R → Norton | Rami riconosciuti con sorgenti di tensione e resistenza finita in serie; ogni conversione ha un disegno |
| Thévenin | Sottorete a due morsetti con carico resistivo separabile; tensione a vuoto, resistenza vista e ricollegamento |
| Sovrapposizione | Sorgenti indipendenti in reti a due morsetti; corto/aperto disegnati, contributi con segno e ricomposizione |
| Semplificazioni con sorgenti ideali | Rami resistivi in parallelo a V ideale e dettagli in serie a I ideale, solo quando la domanda non richiede le grandezze interne |
| Stella → triangolo | Ponte resistivo classico; osservazione esterna alla stella, riduzioni parallele e recupero sull'originale |
| Analisi nodale | Percorso del nucleo già esistente, con spiegazioni delle equazioni effettivamente eseguite |

Non è coperta tutta AutoCircuits: AC, transitori, quadripoli, sorgenti dipendenti nell'esperienza didattica, triangolo→stella generale e trasformazioni arbitrarie restano da sviluppare. Per topologie DC non riconosciute dal layout connesso si usano etichette di rete esplicite, evitando collegamenti grafici inventati. Gli schemi con molti rami possono richiedere scorrimento orizzontale. Il limite dell'API è 32 componenti / 24 nodi / una domanda alla volta.

## Una sola catena del risultato

`Input confermato → IR esistente → run_proof_session_con_run → chiusura verificata → create_lesson → web/PDF`.

Le derivazioni didattiche usano aritmetica razionale. Ogni risposta viene confrontata esattamente con il risultato del nucleo prima dell'esposizione. I nuovi passaggi **non sono presentati come nuovi Certificate** del catalogo, né come Product Verified. Il codice non apre il catalogo e non ridefinisce Verified. La proiezione nuova ha schema `circuit-lesson.v1`, un campo `lesson_build` calcolato sui byte dei quattro moduli e la revisione del nucleo. La vecchia proiezione `StudentSessionView` rimane al confine degli strumenti di verifica.

Il frontend non risolve circuiti e non inventa equazioni. Il PDF legge gli stessi SVG e le stesse spiegazioni della lezione. L'exporter è autonomo: supporta soltanto il vocabolario SVG generato dal nostro renderer. Nel PDF il font standard traslittera alcuni simboli, per esempio Ω in `ohm`; non si altera il valore. La foto originale non viene incorporata automaticamente nel PDF: vi compare lo schema ricostruito.

## Avvio e build

Dal repository, con le dipendenze Python e web del progetto già disponibili:

```sh
uv run --no-sync python scripts/serve_student.py --export
npm --prefix web run build
uv run --no-sync python scripts/serve_student.py --port 43921
```

Aprire `http://127.0.0.1:43921/`. Durante questa sessione `web/node_modules` è un collegamento locale alle dipendenze già installate nel worktree P1A; non è parte della patch e non è stato aggiunto un pacchetto npm. Per un checkout nuovo si usano le dipendenze già dichiarate e il lockfile del repository.

Il server lega solo localhost, limita origine, dimensioni e percorsi, non salva le richieste e non scrive log con contenuti utente. L'eventuale foto viene inviata a OpenAI solo su esplicita azione nell'interfaccia. Per abilitare la trascrizione occorrono `OPENAI_API_KEY` e `KIRCHHOFF_VISION_MODEL` nell'ambiente del server, mai nel frontend o nel repository. L'adattatore usa Responses API, `store=false` e conferma manuale prima del calcolo. Non sono state fatte installazioni, spese o chiamate visive remote.

La pubblicazione dei file statici da sola rende disponibili gli esercizi distribuiti, ma non risolve input nuovi: serve anche un backend ospitato. Il server localhost è un candidato di sviluppo; prima dell'esposizione pubblica servono la scelta dell'hosting, limiti di utilizzo, gestione delle chiavi e verifica della configurazione. Nessun deploy è stato effettuato.

## Validazione

- Suite Python completa: 1896 test passati; copertura complessiva circa 98,7%, dominio 100%.
- Suite web: 68 test passati, inclusi cinque nuovi test sulla connettività della lavagna; typecheck e build passati.
- 30 varianti del circuito Millman confrontate con una formula indipendente, incluse inversioni; 12 varianti di ponte e diverse osservazioni confrontate con il nucleo.
- Test HTTP su circuito nuovo (valori differenti dal catalogo), download PDF, errori, origine e attraversamento dei percorsi.
- Rifiuti: componenti non supportati, topologie non applicabili al metodo, richieste interne alla stella, input invalido e discordanza fra derivazione e nucleo.
- Verifica browser: cambio esercizio/metodo, frecce, ritorno all'originale, circuito costruito sulla lavagna e risolto (6 V), modalità ingrandita e mobile. PDF controllati visivamente con Poppler. Suite E2E storica completa non rieseguita; il Workbench tecnico è conservato.

I due fallimenti iniziali della baseline erano dovuti all'assenza del dataset ignorato nel nuovo worktree. È stato collegato soltanto `reference-set/dev`; nessuna lettura dell'holdout e nessun abbassamento dei test.

## Integrazione del sito personale

Nel branch locale del sito la pagina Metodo torna a un unico riquadro interattivo, con link alla stessa app a schermo intero; le tre illustrazioni statiche della precedente proposta sono state rimosse. La presentazione generale del tuo insegnamento resta prima dell'esempio di elettrotecnica. In sviluppo si usa il server localhost; in produzione il collegamento rimane quello GitHub Pages finché non viene pubblicata la nuova versione, oppure si può impostare `KIRCHHOFF_APP_URL`.

Prossimi interventi sostanziali: convalida visiva su foto reali con API configurata; pubblicazione frontend/backend; estensione di dominio con oracoli indipendenti alle famiglie AC e transitorie. Queste capacità non sono date per concluse dal numero di test o dalla qualità dell'interfaccia.

## Revisione di design e didattica R2

Il percorso ora ha un indice laterale con titoli espliciti, un solo schema centrale, confronto facoltativo con il passaggio precedente e zoom dal 100 al 200%. Su mobile lo schema scorre nel proprio riquadro: pagina e viewport restano di 390 px nella prova eseguita. La modalità ingrandita trattiene il focus e si chiude con Escape. L’indirizzo conserva esercizio distribuito, metodo, passaggio e vista originale anche dopo la ricarica; i circuiti personali non vengono serializzati nell’URL o salvati automaticamente.

La direzione visiva usa titoli serif, testo operativo sans serif, carta chiara e un solo accento blu. La scaletta è navigazione dello stesso circuito, non una sequenza di diapositive nella pagina. Le formule hanno un’area distinta dalla spiegazione. I titoli del percorso nodale sono tradotti in linguaggio studente.

Thévenin distingue ora tensione a vuoto (generatori accesi), resistenza vista (generatori indipendenti spenti, carico ancora staccato), ricollegamento e ritorno all’originale. Ogni operazione ha uno schema e sostituzioni numeriche esplicite. Test dedicati verificano corto delle sorgenti V, apertura delle sorgenti I, carico rimosso e Rth nulla con generatore V ideale ai morsetti.

Il PDF include una prima pagina con originale, domanda e indice effettivo, poi distingue ragionamento e calcolo a ogni passo. Sono stati verificati tutti i 18 PDF tramite estrazione del testo e ispezionate le pagine di apertura e resistenza di Thévenin. La suite finale R2 passa con 1898 test Python (98,70%, dominio 100%) e 68 web; build e confini passano. Screenshot, log e note sono conservati in `../kirchhoff-study-20260913/design-r2/`. Nessuna verifica completa WCAG o prova con studenti reali è implicata da questi controlli. Il perimetro scientifico e i limiti di pubblicazione/API restano quelli dichiarati sopra.


## Riuso della lavagna e importazione R3

“Il tuo circuito” offre adesso anche **Lavagna libera**, basata su Excalidraw 0.18.1 già installato e usato in MAESTRO-Studio. Si disegna con penna, forme e testo, oppure si inserisce un’immagine; “Usa questo disegno” esporta localmente una foto e riporta al controllo della trascrizione. “Salva disegno” conserva un file `.excalidraw` modificabile. La lavagna resta in memoria quando si chiude il pannello; ricaricare la pagina richiede di riaprire il file salvato. Anche il testo in corso resta invariato alla riapertura del pannello.

Il codice `imageToDataURL` riusa il caricatore di MAESTRO-Studio. PNG/JPEG/WebP fino a 20 MB sono decodificati e, quando serve, ridotti localmente entro il limite del servizio di riconoscimento. Un file immagine corrotto viene rifiutato. La prova browser usa uno screenshot JPEG locale con padding oltre 2 MB, esplicitamente un fixture di test; non è una convalida OCR su foto reali. Non sono state eseguite chiamate API.

La lavagna è un’applicazione opzionale isolata in un iframe, caricata soltanto alla prima apertura. Non modifica le dipendenze npm del frontend principale. Il bundle distribuito include font locali e licenze, con CSP che limita rete e asset alla stessa origine. Lo scambio verifica origine, finestra mittente, tipo e dimensioni; immagini SVG e URL remoti vengono respinti. La compilazione riusa gli strumenti già installati, senza `npm install`:

```sh
python3 scripts/build_student_board.py --donor /percorso/whiteboard-studio/studio
npm --prefix web run build
```

I sorgenti stanno in `companion-board/`; l’output pronto in `web/public/board/` è circa 22 MB, in gran parte font e moduli opzionali di Excalidraw. La schermata ordinaria conserva un bundle JS di circa 247 kB non compresso. `build-manifest.json` registra versione, commit donor e SHA-256; `THIRD-PARTY-NOTICES.txt` raccoglie conservativamente le licenze trovate nell’installazione donor, comprese dipendenze non necessariamente distribuite. La licenza Excalidraw proviene dal tag ufficiale v0.18.1. I collegamenti locali `node_modules` non fanno parte del commit.

Controlli R3: suite Python completa PASS (1898 casi, copertura 98,70%, dominio 100%), 77 test web PASS, typecheck di entrambe le applicazioni e build PASS. Browser: disegno manuale, esportazione con valori leggibili, recupero scena, recupero trascrizione, preparazione immagine oltre 2 MB, rifiuto immagine corrotta, nessun errore console nella prova. Restano i limiti scientifici e OCR già dichiarati: Excalidraw è lo strumento di disegno, non un riconoscitore di circuiti. La copertura completa di AutoCircuits resta da implementare e validare. Nessun deploy, reset credito o spesa effettuato.

### Ingresso dagli appunti

Nel pannello circuito si può anche incollare una foto con Cmd/Ctrl+V. Si riusa lo stesso controllo e preparazione dei file; l’incolla normale del testo continua a funzionare. Entrambi i percorsi sono stati provati nel browser reale. Suite web: 77 PASS; typecheck/build PASS. Nessun nuovo riconoscitore o servizio introdotto.
