# Kirchhoff — potenza complessa AC servita

Data: 2026-10-03. **ACAT-09 PARTIAL**, `product_verified=false`.
La verticale funziona in `create_lesson`, HTTP, MCP, pagina studente e PDF.
Il quaderno conserva la domanda e la convenzione, poi ricalcola alla riapertura.
Le 21 famiglie restano nella matrice; questo risultato non conclude il mandato.

## Ingresso e risposta

La domanda tipizzata è `? power <componente>`. Sono accettati R/L/C e
sorgenti AC indipendenti V/I, una frequenza positiva esatta in rad/s e
fasi sorgente multiple di 30°. Valgono i limiti esistenti di 32 componenti,
24 nodi e una domanda. La convenzione comune `@amplitude rms` oppure
`@amplitude peak` è obbligatoria: default e dichiarazione `unspecified`
producono un rifiuto esplicito. La richiesta in continua viene rifiutata.

La convenzione è passiva: `V=V(first)-V(second)` e I entra nel primo
morsetto. Per RMS, `S=V*conj(I)`; per picco, `S=V*conj(I)/2`.
P positiva indica potenza attiva assorbita, P negativa erogata.
Q positiva indica reattiva assorbita, Q negativa erogata; un L ideale
ha Q positiva, un C ideale Q negativa.

La risposta conserva `answer.exact`, `decimal`, `reference` e `unit='VA'`;
aggiunge `quantity='power'` e `complex_power`, che contiene coefficienti
esatti, `active` in W, `reactive` in var e la precisione decimale adattiva.
Non contiene `answer.phasor`: S è una potenza complessa, non un fasore
sinusoidale di tensione o corrente. Le conventions espongono anche
`power_calculated=true`, `power_sign='passive'`, `power_factor` e
`power_formula` coerenti con RMS/picco.

```text
electrical_claim = PHASOR_POWER_CROSSCHECKED
backend = PHASOR_RESIDUALS_AND_POWER_CHECKED
lesson = phasor-power-all-branches-crosscheck
product_verified = false
```

Il percorso prima controlla tutti i valori di tensione/corrente con MNA,
tableau indipendente, leggi costitutive, KCL, KVL e Tellegen. Riusa poi
`phasor_complex_powers` e confronta ogni potenza con un prodotto separato
dei valori del tableau: `P=Vr*Ir+Vi*Ii`, `Q=Vi*Ir-Vr*Ii`, calcolati con
coppie razionali in Q(sqrt(3)), senza riusare il coniugato del kernel.
Il fattore di scala viene applicato anche in questa seconda via.
Infine richiede il bilancio esatto nullo su tutti i rami, sorgenti incluse.
Un bilancio nullo da solo non basta: la mutazione del coniugato è respinta
anche quando il prodotto errato conserva la somma di Tellegen.

La lezione ha otto passi: cinque per il sistema fasoriale, convenzione e
segni della potenza, tabella/bilancio dei rami e risposta S/P/Q. Disegni,
equazioni e riferimenti provengono dalla stessa lezione servita.

## Circuito pubblico di verifica

Dalla radice del repository eseguire `(cd web && npm run build)`, poi
`.venv/bin/python scripts/serve_student.py --port 43921`.
In «Il tuo circuito» → «Testo del circuito»:

```text
@ac 100 rad/s
@amplitude peak
V1 a 0 10 volt 30deg
R1 a b 3 ohm
L1 b c 1/25 henry
C1 c 0 1/100 farad
? power V1
```

Il generatore eroga `P=-25/3 W`, `Q=-25/3 var`, quindi
`S=(-25/3)+j*(-25/3) VA`. Con gli stessi numeri dichiarati RMS,
le potenze sono doppie: si sta dichiarando un'ampiezza fisica diversa,
non convertendo lo stesso circuito. La rete è un caso di verifica pubblico,
senza materiale privato. Non è stata aggiunta alcuna dipendenza.

## Evidenze finali

Directory locale durevole, fuori da Git:
`/Users/andreamarro/MATJOURNEY/kirchhoff-ac-power-evidence-20261003/`.

| Controllo | Risultato |
| --- | --- |
| Python completo, log `python-tests.log` | 2257 passati, 75,12 s |
| Copertura complessiva | 97,71%; soglia 95% invariata |
| `lesson_ac.py` e `lesson_ac_power.py` | 100% linee e rami |
| Dominio e confini | 100%; controlli passati e log conservati |
| Web, log `web-tests.log` | 109 passati |
| Build, log `web-build.log` | Standalone e MCP App passate |
| Browser, log `browser-tests.log` | 10 passati, 23,7 s |
| PDF | RMS e picco di 9 pagine, tutte controllate visivamente |
| Cataloghi DC | 18 JSON: cambiano solo i due hash di provenienza |

I dieci percorsi browser includono quattro regressioni AC precedenti,
quattro percorsi di potenza RMS/picco su desktop/mobile con rifiuto
unspecified, PDF e quaderno riaperto dopo reload, e due percorsi MCP App
di potenza peak. L'App usa l'SDK effettivo e un **host locale di prova**
che inoltra `tools/call` al server reale: nessuna accettazione di un host
MCP esterno è implicita.

L'audit indipendente conservato in `oracle.py`, `check_product.py` e
`result.json` ha confrontato 504 potenze di 36 reti a ponte RLC da sette
rami, con RMS/picco e 24 inversioni dei riferimenti passivi. Usa Cramer
complesso scritto a mano e medie temporali di prodotti di sinusoidi;
errore numerico scalato massimo 4,07e-15, bilanci esatti tutti nulli.
Sono coperte entrambe le sorgenti in assorbimento ed erogazione.
Le regressioni nel repository usano inoltre formule esatte basate su
|I|²R e |V|²Y, alterazioni di segno/fattore, potenze mancanti o spurie,
tipo non esatto e un bilancio finale corrotto. Nessun oracolo è stato
modificato per fare passare l'implementazione.

```sh
.venv/bin/python -m pytest tests
.venv/bin/python scripts/check_domain_coverage.py
.venv/bin/python scripts/check_boundaries.py
git diff --check
cd web
npm test
npm run build
KIRCHHOFF_LIVE_BASE_URL=http://127.0.0.1:43927 ./node_modules/.bin/playwright test tests-e2e/student-ac-live.spec.ts tests-e2e/student-ac-power-live.spec.ts
```

## Limiti e prossimo passo

La lineage delle osservazioni e dei passaggi AC non è ancora una
ProofSession canonica `VERIFIED`. Il confronto elettrico e il bilancio
non certificano da soli ogni scelta didattica o grafica. E/G, op-amp,
trifase, multifrequenza, potenza apparente scalare |S|, fattore di potenza,
transitori e richieste aggregate restano fuori da questa verticale.
Non sono serviti SPICE/CircuitikZ AC o diagnosi automatica del procedimento AC.
Le ampiezze non vengono dedotte dalle immagini e scale miste non sono convertite.

Prossimo ostacolo implementativo: rappresentare S/P/Q e i vincoli di
ampiezza/segno nei tipi canonici di osservazione e derivazione, mantenendo
il gate `VERIFIED` esistente. Il repository è modificato rispetto a HEAD:
`source_sha` è la base Git, mentre `lesson_build` e gli hash della ricevuta
identificano questa evidenza. Nessuna release, pubblicazione o deploy è stata eseguita.
