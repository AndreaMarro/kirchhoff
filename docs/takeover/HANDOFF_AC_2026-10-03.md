# Kirchhoff / CircuitCheck — lezione AC e MCP App portabile

Data: 2026-10-03. Mandato complessivo **TARGET_INCOMPLETE**; ACAT-07 resta
**PARTIAL**, come ACAT-09 per la potenza ora servita, con `product_verified=false`. Le 21 famiglie restano nella
matrice di copertura. Questa ricevuta non attesta parità con AutoCircuits
né accettazione del corpus privato di esami.

## Comportamento disponibile

`create_lesson` serve una richiesta di tensione, corrente o potenza complessa su circuiti RLC
con sorgenti sinusoidali indipendenti V/I. HTTP, MCP e pagina studente usano
lo stesso ingresso. La lezione presenta convenzioni, sorgenti, impedenze,
relazioni dei rami, KCL, valori risolti e ritorno alla domanda originale.

MNA e tableau di ramo indipendente devono concordare esattamente su ogni
tensione e corrente, anche nei rami non richiesti. Vengono controllate le
leggi costitutive, KCL, KVL e l'identità di Tellegen. La risposta espone
componenti razionali nella base ciclotomica, forma rettangolare esatta e
approssimazione decimale. Il contratto è:

```text
electrical_claim = PHASOR_PATHS_CROSSCHECKED
backend = PHASOR_RESIDUALS_CHECKED
lesson = phasor-all-branches-crosscheck
product_verified = false
```

La tupla sopra riguarda tensioni e correnti. La richiesta di potenza ha
la tupla distinta `PHASOR_POWER_CROSSCHECKED` / `PHASOR_RESIDUALS_AND_POWER_CHECKED`
/ `phasor-power-all-branches-crosscheck`, documentata in
[HANDOFF_POWER_2026-10-03.md](HANDOFF_POWER_2026-10-03.md).
Questo percorso non crea un Claim `VERIFIED` e non chiude una ProofSession
AC certificata. Il contratto e la UI conservano questa distinzione.

La direttiva opzionale `@amplitude rms|peak|unspecified`, posta dopo `@ac`
e prima dei componenti, dichiara una scala comune a tutti i fasori e al
risultato. La lezione conserva il valore in `conventions.amplitude`, il
quaderno nella netlist e il PDF nelle spiegazioni. L'assenza della direttiva
resta `unspecified`. Dichiarazioni duplicate, valori sconosciuti, direttive
in continua o dopo i componenti vengono rifiutate. Nessuna conversione
numerica o deduzione dalle immagini viene introdotta. La richiesta
`? power <componente>` richiede RMS o picco espliciti e serve S, P e Q
in convenzione passiva; con fasori di picco applica il fattore 1/2.

Le capabilities mantengono l'alias `ac_scope.amplitude='unspecified'` per
compatibilità e aggiungono `amplitude_default` e `amplitude_conventions`.
La convenzione rimane un dato esplicito della lezione: non modifica l'IR
elettrico del kernel, che risolve sulla scala fornita.

La review indipendente ha rilevato una cancellazione nella precedente
conversione a 24 cifre: un risultato esatto non nullo poteva essere mostrato
come zero. La correzione racchiude `sqrt(3)` fra razionali, somma gli estremi
in aritmetica esatta e raddoppia la precisione finché entrambi arrotondano
alle stesse otto cifre significative. Il campo
`answer.phasor.decimal_precision` registra le precisioni utilizzate.

Il metodo «Fasori» funziona nella pagina studente. PDF, salvataggio e
riapertura del quaderno sono esercitati dal browser. La bobina conserva le
curve Bézier anche nel PDF; fase delle sorgenti ed equazioni restano
leggibili. SPICE, CircuitikZ e diagnosi del procedimento sono disabilitati
per questa lezione AC perché quei percorsi prodotto restano DC.

## Avvio e circuito riproducibile

Dalla radice del repository, con le dipendenze già presenti:

```sh
cd web
npm run build
cd ..
.venv/bin/python scripts/serve_student.py --port 43921
```

Aprire `http://127.0.0.1:43921`, scegliere «Il tuo circuito» → «Testo del
circuito», incollare e premere «Risolvi e spiega»:

```text
@ac 100 rad/s
@amplitude rms
V1 a 0 10 volt 30deg
R1 a b 3 ohm
L1 b c 1/25 henry
C1 c 0 1/100 farad
? current R1
```

La corrente orientata `a → b` vale
`(5/6 + 5/6*sqrt(3)) + j*(5/6 - 5/6*sqrt(3)) A`, circa
`2.2767090 - j*0.61004234 A`, in valori efficaci dichiarati. Questo è un circuito di verifica dichiarato,
non un quesito attribuito al materiale privato.

Con l'SDK MCP già disponibile:

```sh
.venv/bin/python -m kirchhoff.api.mcp_server
```

La wheel e la sdist includono l'HTML completo della MCP App. Un manifest
lega bundle, template, sorgenti e lockfile ai rispettivi hash; una build
con bundle assente o obsoleto viene rifiutata. Il runtime installato legge
le risorse del package senza cercare `web/` o Git. Nel checkout non
compilato, gli strumenti MCP core restano disponibili e la risorsa UI
mostra l'istruzione di compilazione.

Il test di packaging costruisce offline, installa soltanto la wheel locale
in una directory temporanea e invoca il server installato. Lo SHA zero
usato dal test è una **fixture congelata**, non una revisione di release.
Nessuna wheel di release è stata pubblicata da questo lavoro.

## Evidenze e comandi

Misure della verifica di questa unità:

| Controllo | Esito |
| --- | --- |
| Suite Python completa con potenza AC | 2.257 test passati, 75,12 s |
| Copertura complessiva | 97,71%, soglia invariata 95% |
| Dominio e confini di import | 100% linee/rami; confini rispettati |
| Suite web | 109 test passati |
| Build standalone e MCP App | Passata |
| Browser standalone AC e potenza RMS/picco | 6 passati; PDF e quaderno ricalcolato dopo reload |
| MCP App con host locale di prova | 4 passati; AC e potenza di picco su desktop/mobile |
| Cataloghi DC rigenerati | 18 JSON: soltanto `source_sha` e `lesson_build`; nessun PDF cambiato |

L'oracolo copre 20 reti AC generate con risposta nota per costruzione,
serie e parallelo con fasi e orientazioni diverse, e un ponte con due nodi
incogniti e due sorgenti verificato mediante KCL manuale e regola di Cramer.
Le prove negative includono singolarità, domande fuori ambito, componenti
mancanti, risultato incompleto o non esatto, disaccordi su rami non
richiesti e due percorsi concordi ma fisicamente errati.
Una regressione attraversa il servizio con tre sorgenti quasi compensanti:
KCL impone `Vx=(q-sqrt(3))/4`, con `q` troncato a 30, 90 e 210 cifre.
Il risultato decimale conserva il valore negativo non nullo e coincide
con un oracolo Decimal a precisione maggiore.
I test dell'ampiezza esercitano i tre valori ammessi, default invariato,
errori di ordine e duplicazione, rifiuti HTTP/MCP e conservazione nel PDF.
Il quaderno rifiuta una convenzione modificata senza aggiornare il digest.

```sh
.venv/bin/python -m pytest tests
.venv/bin/python scripts/check_domain_coverage.py
.venv/bin/python scripts/check_boundaries.py
git diff --check
cd web
npm test
npm run build
KIRCHHOFF_LIVE_BASE_URL=http://127.0.0.1:43921 ./node_modules/.bin/playwright test tests-e2e/student-ac-live.spec.ts
```

Il browser è Chromium tramite Playwright già installato; viewport
1440×900 e 390×844. La skill/plugin Browser non era disponibile.
Il flusso standalone è ingresso testo → calcolo → metodo Fasori → ultimo
passaggio → PDF → salva quaderno → riapri e ricalcola. Nessun errore di
pagina o overflow orizzontale è stato rilevato in questo flusso.

Il test MCP usa l'SDK Apps effettivo, handshake `ui/initialize` e
`tools/call` inoltrati al vero server MCP da un **host locale di prova**.
Verifica il risultato, lo schema e la navigazione dei passaggi. Non è
un'accettazione dentro Claude, ChatGPT, Codex o altro host esterno.

Le evidenze locali sono in `/tmp/kirchhoff-ac-evidence/`: `lesson.json`,
`lesson.pdf`, `circuit.kirchhoff` e screenshot `standalone-desktop.png`,
`standalone-mobile.png`, `mcp-desktop.png`, `mcp-mobile.png`. Sono artefatti
temporanei locali, fuori da Git; non contengono fonti private. Gli screenshot
del browser più recenti includono RMS; i precedenti file `lesson.json` e
`lesson.pdf` sono una verifica storica senza direttiva esplicita.
I quattro screenshot RMS sono conservati anche in
`/Users/andreamarro/MATJOURNEY/kirchhoff-ac-rms-evidence-20261003/`.

Una verifica separata ha attraversato il quesito autorizzato 11.17: fonte
locale vista, trascrizione manuale, oracolo KCL con Fraction senza solver,
browser desktop/mobile, PDF di sette pagine e quaderno riaperto dopo reload.
La variante con RMS dichiarato ha artefatti privati distinti dalla precedente
variante unspecified. Le ricevute e i relativi SHA-256 restano in
`/Users/andreamarro/MATJOURNEY/private-corpus-20261002/`, con prefissi
`eserciziario-11-17-browser-receipt` e `eserciziario-11-17-rms-browser-receipt`.
La fonte non è stata inviata a servizi esterni né aggiunta al repository.
`human_confirmation=false` e `product_verified=false` restano espliciti.
Questo caso manuale non misura il riconoscimento di immagini, tutto il corpus,
un host MCP esterno. Una successiva ricevuta privata distinta,
`eserciziario-11-17-ardesia-receipt.json`, registra il percorso Ardesia
con bundle riaperto a browser vuoto, sessione/focus originali conservati e
recap PDF di sette pagine. Restano `human_confirmation=false`,
`teacher_review_recorded=false` e zero chiamate al provider.

## Limiti e prossimo ostacolo implementativo

- Una pulsazione positiva esatta in rad/s e fasi sorgente multiple di 30°;
  nessun ingresso in Hz o multifrequenza.
- Convenzione `exp(+j*omega*t)`; RMS/picco richiede una dichiarazione esplicita
  comune a tutte le sorgenti. Default unspecified; nessuna conversione fra
  scale o forme d'onda istantanee. Potenza complessa, P e Q sono disponibili
  solo con RMS o picco espliciti.
- Una domanda di corrente/tensione/potenza su componente; massimo 32 componenti
  e 24 nodi. Porte AC, due porte, trifase e transitori non sono serviti.
- E/G e operazionali ideali restano kernel-only. Nessun modello di
  saturazione o accettazione di una lezione con quei componenti.
- Nessuna accettazione dell'intero corpus privato, del riconoscimento
  fotografico live, di un host MCP esterno, deploy o autenticazione remota.
- Gli schemi AC generali usano etichette di nodo; non è certificata ogni
  scelta grafica o didattica della lezione.

Il prossimo ostacolo implementativo è rappresentare osservazioni fasoriali,
equazioni e riferimenti al circuito originale nei tipi canonici della
ProofSession, con lineage e controllo indipendente di ogni passaggio.
La definizione di `VERIFIED` e le soglie restano invariate. La successiva
accettazione con trascrizione confermata da un umano e su un host MCP esterno
richiede evidenze separate; non si deduce dai test qui riportati.
