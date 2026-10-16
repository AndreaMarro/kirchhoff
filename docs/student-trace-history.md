# Tentativi e correzioni nel quaderno

Il quaderno portabile versione3 conserva il procedimento corrente e una
cronologia ordinata dei controlli completati. Correggere o riprendere un
tentativo crea una nuova bozza; non cambia i passi conservati. Solo una risposta
interpretabile e ancora riferita alla richiesta attuale aggiunge un controllo.
Errori di rete, rifiuti HTTP, risposte obsolete e circuiti diversi non appendono.

`StudentTrace` resta l'autorità semantica. La cronologia è un contenitore
applicativo di input: non introduce un secondo solver, una memoria della
persona, un punteggio o una nuova definizione di Verified.

## Trasporto

`kirchhoff-portable-session.v3` aggiunge `traceHistory` richiesto, anche vuoto.
Ogni record contiene soltanto `steps`, `circuitFingerprint` e `engineRevision`.
I passi conservano testo, operazione, due riferimenti, valore dichiarato e stato
di lettura. Le diagnosi non sono salvate come prove. La revisione Git originale
è provenienza dichiarata dal file: un hash non autentica autore o consenso.

Limiti:32 controlli,32 passi per controllo,2.500.000 byte UTF8 per l'intera
cronologia JSON compatta; valgono inoltre i limiti dei passi e del quaderno.
Non si eliminano controlli per far spazio. I quaderni v1/v2 restano leggibili con
cronologia vuota; un downgrade che dichiara controlli viene respinto. La fonte
portabile introdotta in v2 resta supportata. Un inventario di passi illegittimo,
un altro circuito o diagnosi importate sono rifiutati prima della riapertura.

All'apertura, l'app ricalcola la soluzione e ogni tentativo usando l'API reale.
Solo dopo il successo dell'intero percorso sostituisce la lezione corrente.
Tutte le risposte devono appartenere alla stessa revisione del motore della
nuova soluzione. Le revisioni originarie rimangono provenance; gli esiti sono
quelli appena ricalcolati. Un guasto mantiene il quaderno precedente.

La cronologia in memoria richiede **Salva quaderno** per conservarsi sul
dispositivo. Il file include contenuti della lavagna e fonti come già dichiarato
all'utente. Non c'è un salvataggio automatico né un profilo persistito dal server.

## Materiale

Un PDF con tentativi passa dall'API anche per gli esempi del catalogo. Backend
assente o rifiuto non causano un fallback al documento statico senza storia.
Il server valida tutti i record, poi richiama il diagnostico canonico sui passi;
un esito esterno non viene stampato come prova. La revisione dell'ultimo
controllo ricalcolato deve coincidere con quella del motore che genera il PDF.

Il documento conserva domanda, soluzione e disegni esistenti, aggiungendo in
ordine tentativi originali, operandi, lettura e diagnosi ricalcolata. Le bozze non
controllate restano nel quaderno: l'omissione è dichiarata in UI e nel PDF.
Il font PDF base non copre ogni scrittura: i frammenti non visualizzabili sono
segnalati con un'omissione visibile, mantenendo l'originale completo nel quaderno.
Non si sostituisce il significato dei caratteri con ipotesi. `pypdf` è una
dipendenza dev bloccata per estrarre il testo nelle prove, non una dipendenza
runtime del motore o dell'export.

## Prove

Fixture sintetica condivisa Python/TypeScript:
`web/tests/fixtures/student-history.json`:12V,R1=1kohm,R2=2kohm;
riferimento errato → calcolo errato → 8V corretto → lettura non sicura.

- `tests/test_student_history.py`: PDF letto con parser reale, operandi e
  diagnosi, paginazione32 passi, omissione glifi, limiti/record/identità,
  HTTP reale, motore cambiato e diagnosi esterne respinte.
- `web/tests/trace-history.test.ts` e `trace-check.test.ts`: quaderno v3 e
  legacy, record e downgrade, risposte incoerenti, copia immutabile, byte UTF8.
- `web/tests-e2e/student-history-live.spec.ts`: API e browser reali, nuovo
  contesto, ripresa senza mutare la storia, PDF del catalogo, rete/rifiuto/stale.
  Le due viewport sono una prova di portabilità locale, non collaborazione
  remota né un pilot umano.

I run e gli SHA esatti stanno nel registro operativo `deferred-work.md`.
