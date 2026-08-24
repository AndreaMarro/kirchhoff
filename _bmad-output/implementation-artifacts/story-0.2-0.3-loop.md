# Story 0.2 e 0.3 — il Loop Kirchhoff v3, costruito a mano

**Data:** 2026-08-24 · **Costruzione:** manuale, per decisione del proprietario
**Precede:** `story-0.1-preflight.md`, `story-0.1-remediation.md`

> «Il loop non deve auto-costruire la propria infrastruttura fondamentale.»

Il router lo applica meccanicamente, non per promessa: una storia dell'Epic 0
riceve classe `MANUALE` e non e' instradabile. Se il loop la incontrasse,
inciderebbe un FERMO invece di eseguirla.

---

## L'architettura decisa: kernel Ardesia + facciata Kirchhoff

Nessuna delle due alternative pure. Sotto, la topologia provata da Ardesia in
381 iterazioni, con script separati. Sopra, una riga di comando ergonomica che
**non possiede una seconda macchina a stati**: dispaccia e restituisce il
codice di uscita senza reinterpretarlo.

    kirchhoff-loop
          ├─ doctor   → precondizioni.sh (diagnostico) + controlli di runtime
          ├─ status   → stato.sh
          ├─ dry-run  → precondizioni.sh --avvio + router.py
          ├─ run      → kirchhoff-loop.sh
          └─ resume   → ispezione del rientro, poi kirchhoff-loop.sh

La macchina a stati vera e' il filesystem piu' git. Nessuno stato vive in una
memoria di sessione.

### I file

| File | Ruolo |
|---|---|
| `ops/loop/kirchhoff-loop` | la facciata: dispatch puro |
| `ops/loop/precondizioni.sh` | sette cancelli fail-closed, due modi |
| `ops/loop/router.py` | classe di rischio → piano. Puro, deterministico |
| `ops/loop/stato.sh` | sola lettura, ricostruisce da disco e git |
| `ops/loop/verifica.sh` | l'oracolo deterministico, zero token |
| `ops/loop/ratchet.py` | le metriche non regrediscono |
| `ops/loop/fermo.sh` | l'arresto che richiede una persona |
| `ops/loop/kirchhoff-loop.sh` | lo scheduler seriale |
| `ops/loop/iterazione.md` | il prompt dell'implementatore |
| `ops/loop/stato/` | stato di lavoro — **mai** in git |
| `ops/loop/giornale/` | evidenza append-only — **sempre** in git |

---

## I cinque meccanismi copiati, e il sesto adattato

| # | Meccanismo | Come e' realizzato |
|---|---|---|
| 1 | **Precondizioni fail-closed** | sette cancelli. `--avvio` aggiunge quello sull'albero pulito, che vale solo prima di un giro. In diagnosi si riportano tutti e si esce col codice del primo fallito: morire al primo dice meno di quanto il sistema sa |
| 2 | **Watchdog** | `TERM` → dieci secondi di grazia → `KILL`, su ogni invocazione di modello. Il segnale di stop viene da fuori dall'agente |
| 3 | **Ratchet su copia** | `ratchet.py` aggiorna il metro quando passa; lo scheduler misura contro `.ratchet-candidato.json`. Un candidato non puo' abbassare la baseline e poi dichiarare di averla raggiunta |
| 4 | **Giornale append-only** | un file per iterazione, mai riscritto. Inciso via `trap` su **ogni** uscita, non solo su quella felice: un giro che muore e' esattamente quello di cui serve la traccia |
| 5 | **FERMO** | otto cause, elenco **chiuso**. Una causa fuori elenco significa che il loop ha incontrato l'imprevisto, ed e' essa stessa ragione per chiamare una persona. Lo scioglimento e' deliberato e conservato |
| 6 | **Routing dei modelli** | **ADATTATO, non copiato.** Ardesia gira incondizionatamente a `--model claude-opus-5 --effort max` (`ardesia-loop.sh:594-595`). Qui il livello segue il rischio |

---

## Il router

R0 Sonnet 5 high · R1 Opus 5 xhigh + revisione Opus high · R2 Opus 5 max +
Blind Hunter Fable 5 max + ri-revisione · R3 due analisi indipendenti e il
proprietario.

Tre regole incise nel file perche' non dipendano dalla memoria di un modello:

1. **Il revisore non vede il ragionamento dell'implementatore.** Garantito dal
   confine di processo — un `claude -p` separato — non dalla buona volonta'.
2. **Chi trova un rilievo non lo corregge.** Il revisore Fable non e' mai il
   riparatore.
3. **Il modello propone, il sistema certifica.** Nessun passo chiude su
   un'affermazione: chiude su `verifica.sh`, o non chiude.

Classificazione dichiarativa e ispezionabile. Default conservativo su R1:
sbagliare verso l'alto costa token, sbagliare verso il basso costa correttezza.

---

## Difetti trovati dal collaudo, non dall'ispezione

Nessuno di questi si vedeva leggendo il codice.

1. **Il giornale bloccava il cambio di ramo.** Il file veniva scritto
   nell'albero tracciato; git rifiuta il checkout con un file modificato non
   committato, e il loop restava appeso sul ramo dell'iterazione. Corretto
   spostando la scrittura in `stato/` (ignorato) e incidendo in `giornale/`
   alla fine, via `trap`.

2. **Il loop si autobloccava al secondo giro.** Il giornale dell'iterazione *n*
   sporcava l'albero che il cancello dell'iterazione *n+1* pretende pulito.

3. **`claude -p` sarebbe nato senza compito.** Il prompt era passato solo via
   `--append-system-prompt`, senza prompt utente. Trovato ispezionando
   l'invocazione **prima** di pagarla.

4. **Nulla bloccava la promozione sui rilievi dell'ultima revisione.** Il piano
   finiva, il ratchet era verde, il ramo veniva fuso — e i rilievi non sono
   giudicabili da nessun cancello deterministico. Un verdetto di modello non
   puo' aprire un merge: sarebbe il modello che certifica se stesso. Ora la
   promozione richiede `--promuovi`, e la sua attivazione sara' il gesto con
   cui il proprietario dichiara conclusa la fase di collaudo.

5. **Percorso del plugin sbagliato in `doctor`.** Emerso perche' il cancello e'
   fallito chiuso invece di dichiarare un falso PASS.

6. **Conteggio dei test gonfiato** (258 invece di 245): contava i punti su
   tutto il file, e la tabella di copertura ne e' piena.

7. **L'emettitore di metriche falliva in silenzio.** `true`/`false` non sono
   letterali Python: `SyntaxError`, stdout vuoto, exit 0. Un emettitore che
   fallisce zitto e' peggio di uno che non c'e'.

---

## Il gate di readiness, eseguito fra 0.1 e 0.2

`validate` → `valid: true`, nessun problema, nessun rischio.

**Verdetto: CONCERNS, compatibile con Epic 0.**

Il `generate --dry-run` mostra che rigenerare il ledger scarterebbe **46
orfani, di cui 5 `done`**: `epics.md` v2 ha rinumerato le storie e le vecchie
chiavi non esistono piu'. Il ledger porta anche commenti inline con provenienza
— per esempio la distinzione fra il contratto v1 di AD-21 e i cinque recinti
della v2 — che una rigenerazione perderebbe.

Non e' un problema meccanico: la mappatura vecchio→nuovo delle cinque storie
fatte e' giudizio di prodotto. **Non rigenerato.** Le storie `0-1`, `0-2`, `0-3`
compaiono fra le `new_entries` e non toccano nessuna chiave contesa, quindi
l'Epic 0 procede senza dipendere da quella decisione.

Rilievo minore: `epics.md` contiene `## Epic List` due volte (righe 346 e 348).

---

## Aperto

- **Sincronizzazione del ledger** con `epics.md` v2: mappare le cinque storie
  `done` sulle chiavi nuove, o dichiararle ri-ambitate. Decisione del proprietario.
- **Script di vendoring riproducibile** per un bump deliberato di BMAD.
- **Regole `Write(...)` inefficaci** in `.claude/settings.json` (righe 20-23, 32).
- **Render vecchio `3efdf204…` committato**: upstream lo escluderebbe.
- **Skew skill↔helper**: il `doctor` confronta gia' versione dichiarata e
  installata e lo dice quando divergono, ma un confronto di hash non vedra' mai
  un cambio di contratto dentro le skill del plugin.

---

# Collaudo progressivo

Gradini, nell'ordine chiesto dal proprietario.

| # | Gradino | Esito |
|---|---|---|
| 1 | `doctor` | verde: 7 cancelli, BMAD 6.11.0 MATCH, render PASS, `AGENTS.md` presente |
| 2 | `status` | completo: repo, runtime, ledger, giornale, ratchet, prossimo giro |
| 3 | `dry-run` | classe R2 corretta, sei passi con modelli e livelli, **zero token** |
| 4 | `run --prova` | scheletro intero: sei passi, oracolo reale due volte, ratchet verde, **zero token** |
| 5 | `resume` con ramo orfano | rileva l'ambiguita' e **fallisce chiuso** con istruzioni azionabili |
| 6 | iterazione vera, tentativo 1 | **fallita**: `Exceeded USD budget (4)`. Parametro mio, non meccanismo |
| 7 | iterazione vera, tentativo 2 | **completata**, sei passi su sei, 67 minuti |

## Il tentativo fallito, e perche' conta

`Error: Exceeded USD budget (4)`. Il meccanismo si e' comportato in ogni parte
come progettato: watchdog non scattato (25 min di soglia contro 10 di corsa),
passo rosso rilevato, **977 righe su 8 file conservate sul ramo**, `main` non
contaminato, giornale inciso dal `trap` anche sull'uscita infelice, nessuna
promozione.

Un tetto troppo stretto non e' prudenza: e' un'iterazione tagliata a meta' che
costa quanto e' spesa e non consegna niente. Il precedente corretto e' del
proprietario — Ardesia usa `BUDGET=25`, alzato deliberatamente il 15/08.

## L'iterazione completata

    21:16:37  implementa   claude-opus-5  effort max   $25   → 25 min
    21:41:49  verifica     oracolo exit 0 — 308 test, copertura 100%
    21:41:49  revisiona    claude-fable-5 effort max   $8    → 10 min  [Blind Hunter]
    21:51:26  ripara       claude-opus-5  effort max   $25   → 23 min
    22:14:30  verifica     oracolo exit 0 — 342 test, copertura 100%
    22:14:30  revisiona    claude-fable-5 effort max   $8    →  9 min  [ri-revisione]
    22:23:25  ratchet: verde
    22:23:25  giro verde, NON promosso: manca --promuovi

Prodotte 1915 righe su 11 file. Baseline del ratchet **ancora a 245**: non
promossa, come progettato.

## Il risultato piu' importante del collaudo

**Gli oracoli erano verdi e il codice era comunque sbagliato.**

342 test passati, copertura 100%, recinti verdi, dominio verde — e la
ri-revisione avversaria su Fable 5 max, in processo fresco, ha prodotto
**quattordici rilievi riprodotti con codice eseguito sul HEAD committato**.
Fra essi:

- `check_delta` ha **zero consumatori in produzione**: il pacchetto contiene il
  proprio controllore di coerenza e non lo esegue mai. Dentro un singolo
  `TransformResult` i due canali raccontano storie diverse per la stessa entita'.
- L'`Equation` e' **tautologica**: `engine.py:213` costruisce
  `Equation(eq.symbolic, f"{a.symbolic} + {b.symbolic}")` — il primo membro e'
  l'espressione dell'equivalente, non il suo identificatore. Il simbolo nuovo
  non compare, l'uguaglianza non lo lega alla formula che lo definisce, e un
  test **pinna la forma difettosa come comportamento atteso**.
- `node_mapping` non ha alcun uso legale: i due versi del ciclo d'identita'
  coprono l'intero spazio delle mappe con sorgente reale.
- `Cause`/`CAUSES` scritti due volte senza test di riconciliazione — lo stesso
  difetto E-62 che per `CATALOG` il repository ha elevato a dottrina.
- La chiave della storia **non esiste** in `sprint-status.yaml`: la voce reale
  e' `2-6-catalogo-delle-trasformazioni-e-percorso-b`. Tre nomi in circolazione.

Verificati in modo indipendente tre rilievi su quattordici, i piu'
consequenziali: tutti e tre confermati.

### Che cosa questo dimostra

1. **L'oracolo deterministico e' necessario e largamente insufficiente.** Un
   giro con 342 test verdi e copertura piena ha prodotto codice che viola il
   controllore del proprio pacchetto.
2. **La revisione avversaria in processo fresco e su modello diverso fa lavoro
   reale**, e non e' cerimonia.
3. **Il cancello `--promuovi` era la decisione giusta, e ora l'evidenza e'
   concreta invece che teorica.** Senza di esso, questo ramo sarebbe stato fuso
   su `main` con il ratchet verde.

Il ramo `loop/iter-20260824T211636Z-2-6-catalogo-delle-trasformazioni` **non e'
stato promosso** e resta per l'ispezione del proprietario.

## Verdetto

Il meccanismo del Loop Kirchhoff v3 e' **provato end-to-end**. Il suo prodotto,
alla prima corsa, **non e' promuovibile** — ed e' esattamente cio' che il loop
doveva riuscire a dire invece di nascondere.

Il passaggio a motore normale di sviluppo resta al proprietario, e il gesto che
lo segna e' l'attivazione di `--promuovi`.
