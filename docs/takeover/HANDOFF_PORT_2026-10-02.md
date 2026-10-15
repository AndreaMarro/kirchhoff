# Kirchhoff / CircuitCheck — handoff del checkpoint di porta DC

Data: 2026-10-02. Stato complessivo del mandato V2: **TARGET_INCOMPLETE**.
Questo documento registra il comportamento verificato e i limiti, senza
interpretare una sottoprova come certificazione della domanda originale.

## Repository e checkpoint

- Kirchhoff: branch `codex/kirchhoff-takeover-20261002`, PR pubblica
  [#17](https://github.com/AndreaMarro/kirchhoff/pull/17), base
  `release/proof-workbench-beta-0.3-rc1`. Nessun merge.
- Ardesia: branch `codex/circuitcheck-vertical-20261002`,
  [PR privata #259](https://github.com/AndreaMarro/ardesia/pull/259),
  base `muse/postlesson-export-integrity-20260922`. Il codice di Ardesia
  resta nel suo repository privato. La preview Vercel della PR è stata
  autorizzata e i controlli del checkpoint precedente sono verdi; la
  navigazione interattiva richiede ancora l'accesso al relativo account.
- Il corpus degli esami, le foto e i PDF prodotti da quelle foto sono locali
  e fuori da Git. Il report `06_REPORT_RICEVUTO_2026-10-02.txt` fino alla
  sezione H non è stato trovato nelle posizioni disponibili; questo manca
  come prova documentale, non come codice da ricostruire.

## Risultato servito di questo checkpoint

La netlist può chiedere `? resistance a 0`. La domanda usa due nodi reali,
senza creare un componente fittizio. `create_lesson` e quindi l'HTTP locale
e il tool MCP costruiscono due sottoprove canoniche: porta aperta con 0 A e
sorgenti originali attive; poi sorgenti indipendenti spente e corrente di
prova da 1 A. I valori sono confrontati esattamente con il kernel di porta,
che usa MNA, tableau di ramo indipendente e verifica dei residui. La lezione
ritorna ai morsetti originali, offre cinque passaggi, e produce un PDF.

La verifica emessa è `PORT_SUBPROOFS_CROSSCHECKED`, con
`product_verified=false`. Ogni sottocircuito generato ha una chiusura
canonica; la trasformazione dalla domanda sui morsetti originali alle due
sonde non ha ancora una lineage canonica certificata. L'adattatore storico
`resolve`, che proietta solo claim su componenti, rifiuta esplicitamente la
nuova richiesta di porta. Non attribuire alla domanda originale il claim
`VERIFIED` delle sottoprove.

Le esportazioni CircuitikZ e SPICE conservano la domanda sui due morsetti.
L'interfaccia studente espone il nome «Corrente di prova» e la richiesta
resta disponibile anche con «Percorso consigliato». Il prompt opzionale di
riconoscimento foto conosce la sintassi della domanda di porta; nessun
provider esterno è stato invocato per la foto privata.

## Evidenza locale sull'esame reale

La fonte privata è un quesito reale del corpus locale. I suoi byte, la
trascrizione e gli hash restano nella ricevuta locale fuori Git.
La trascrizione passiva era stata verificata manualmente, senza la sorgente
di prova usata nel precedente esperimento. Il percorso locale
`/api/source` → `/api/confirm` → `/api/solve` → `/api/pdf` ha restituito
un valore esatto coincidente con l'oracolo privato, cinque passaggi e un
PDF A4 di sei pagine. Una modifica della
netlist dopo la conferma ha ricevuto HTTP 422. PDF locale:
`private-corpus-20261002/exam-2021-q2-port-lesson.pdf`, fuori da Git.
La prima pagina e il passaggio della corrente di prova sono stati aperti
e ispezionati visivamente. Non sono stati inviati byte privati a GitHub,
Vercel o provider di visione.

Il risultato coincide con l'oracolo di sviluppo indipendente, ma non
certifica una chiave ufficiale dell'esame. La foto non è stata trascritta
automaticamente: la conferma umana riguarda la trascrizione manuale.

## Verifiche e limiti di completamento

I test discriminanti coprono tipizzazione, orientazione, spegnimento delle
sorgenti, differenza fra sottoprova e claim originale, mutazione della
sonda di prova, rifiuto dei casi non supportati, PDF ed esportazioni. La
suite Python completa è passata, con copertura globale **97,65%**;
`domain/` ha linee e rami al **100%** e il gate dei confini di import è
passato. L'interfaccia ha passato **94/94** test e ha compilato sia la
versione standalone sia l'MCP App.

La matrice `coverage-2026-10-02.json` mantiene ACAT-01 in **PARTIAL**:
il sottoinsieme DC di porta ha una prova positiva, ma non equivale alle
21 famiglie complete. AC, transitori, due porte, riconoscimento fotografico
dal provider, lavagna completa, diagnosi di tutti i metodi alternativi,
review indipendente e accettazione Ardesia nella preview restano aperti.

Comandi di verifica sul checkout del branch:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_domain_coverage.py
.venv/bin/python scripts/check_boundaries.py
cd web && npm test && npm run typecheck && npm run build
```

Il lavoro successivo, quando si riprende il mandato, è strutturare la
lineage originale → sonde nel proof/session canonico e verificare ogni
equazione e stato grafico della derivazione di porta. La foto reale richiede
un provider configurato e autorizzazione specifica per inviare i byte;
l'accesso alla preview Ardesia è necessario per la verifica interattiva.
