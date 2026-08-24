---
title: 'Storia 1.1 — Insieme di riferimento strutturato a risposta nota (classi mancanti)'
type: 'feature'
created: '2026-08-13'
status: 'done'
baseline_commit: 'NO_VCS'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** L'insieme di riferimento copre una sola delle quattro classi di dominio in scope
(`dc_resistive`). Transitori RL/RC/RLC, regime sinusoidale e trifase non hanno casi, quindi
l'harness non misura nulla su tre quarti del dominio che il prodotto promette di risolvere; in più,
nessun caso porta la sequenza di Trasformazioni di riferimento che il criterio di accettazione
richiede.

**Approach:** Estendere il dominio con l'aritmetica esatta necessaria alle altre tre classi — un
campo ciclotomico razionale che contiene `j` e `√3`, così che fasori e sfasamenti a 120° restino
esatti — e aggiungere un generatore per classe, ognuno con un oracolo che ricava la stessa risposta
per una via strutturalmente diversa da quella che l'ha prodotta. Ogni caso, incluse le reti DC già
esistenti, porta da qui in avanti la propria sequenza di Trasformazioni di riferimento.

## Boundaries & Constraints

**Always:**
- Aritmetica esatta ovunque nell'oracolo: `Fraction` e il campo ciclotomico costruito su `Fraction`.
  Nessun `float` entra in un valore atteso, in un confronto o in una tolleranza.
- La verifica di un caso non usa la via che l'ha generato. Generatore e oracolo partono da estremi
  opposti: chi costruisce sceglie la risposta e ne deriva i componenti, chi verifica parte dai
  componenti e ricava la risposta.
- Un residuo non nullo è un bug, non rumore: le uguaglianze si controllano a zero esatto.
- `domain/` non importa `adapters/`, `ports/`, `eval/`, `pipeline/`. La casualità della generazione
  vive in `eval/` ed è sempre governata da un seme esplicito.
- Copertura globale ≥ 95%; `domain/` al 100% su righe e rami.
- Il rapporto dell'harness continua a dichiarare che la copertura esclude l'estrazione da immagine.

**Ask First:**
- Abbassare una soglia di copertura, ampliare lo scope oltre le quattro classi di D8, o introdurre
  una dipendenza esterna (SymPy, NumPy, ngspice).
- Trattare come completa la metà fotografica del criterio CGHD: richiede annotazione manuale di
  immagini reali e contraddice la decisione del 13 agosto 2026. Fuori da questa spec.

**Never:**
- Circuiti non lineari, componenti attivi, mutuo accoppiamento: fuori scope per D8.
- Un caso che si verifica da solo riusando la propria formula di costruzione.
- Nomi di Trasformazione inventati caso per caso: l'insieme dei nomi emessi è chiuso e controllato
  da un test.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Generazione per classe | seme intero, classe di dominio | caso con IR, risposta attesa esatta, sequenza di Trasformazioni | seme che produce un caso degenere → scartato e contato, non silenziato |
| Verifica indipendente | caso generato | lista di problemi vuota | disaccordo generatore/oracolo → il caso finisce fra gli scartati con il problema nominato |
| Fasore in regime sinusoidale | IR con R, L, C e sorgente a pulsazione razionale | tensioni e correnti come elementi esatti del campo ciclotomico | pulsazione o valore nullo dove serve un inverso → errore esplicito |
| Trifase equilibrato | sorgente a stella con sfasamenti di 120°, carico equilibrato | correnti di fase uguali in modulo e ruotate di 120° esatti; corrente di neutro nulla | neutro non nullo → problema di verifica, non arrotondamento |
| Transitorio del primo ordine | rete resistiva con un solo elemento di accumulo | costante di tempo, valore iniziale e valore finale esatti | costante di tempo non positiva → problema di verifica |
| Transitorio del secondo ordine | RLC con radici caratteristiche razionali per costruzione | due radici reali negative, esatte | radice che non annulla il polinomio caratteristico assemblato dai componenti → problema |
| Serializzazione | caso con valori razionali e ciclotomici | JSON che rilegge identico, valore per valore | valore di tipo non previsto → errore, mai troncamento a float |

</frozen-after-approval>

## Code Map

- `src/kirchhoff/domain/ir.py` — `Component` (id, type, terminals, value, symbolic), `Request`,
  `IR` con validazione in `__post_init__`. `ComponentType` oggi è `resistor | voltage_source_dc`,
  `Quantity` è `voltage | current`: entrambi vanno allargati. Il valore di un componente è oggi un
  solo `Fraction`, e a un condensatore o a un induttore serve lo stesso campo con significato
  diverso (F, H) — non serve un secondo campo.
- `src/kirchhoff/domain/mna.py` — `_solve_exact` (Gauss con pivot parziale su `Fraction`, righe
  19-34) è già un solutore di campo: si generalizza a qualunque scalare che sappia `+ - * /`
  parametrizzando zero e uno. `solve_dc` (37-85) assembla nodi e sorgenti di tensione; `kcl_residuals`
  (88-96) e `power_balance` (99-104) sono i controlli riusati dall'oracolo.
- `src/kirchhoff/eval/generator.py` — generatore DC ad albero serie/parallelo: `Leaf/Series/Parallel`,
  `equivalent`, `propagate`, `_flatten`, `generate_case`. Il modello da imitare per la classe
  sinusoidale, dove l'albero è identico ma i valori sono impedenze complesse.
- `src/kirchhoff/eval/reference_set.py` — `Case` (senza sequenza di Trasformazioni, da aggiungere),
  `verify_independently` (43-61) è oggi specifico del DC, `build` (64-79) genera una sola classe,
  `to_json`/`from_json` (82-110) serializzano solo `Fraction`, `write`/`load` gestiscono lo split e
  il divieto di lettura della parte trattenuta — quest'ultimo non va toccato.
- `src/kirchhoff/eval/metrics.py` — `reference_solver` (104-120) chiama `solve_dc` per ogni caso:
  con quattro classi deve smistare, o le nuove classi risulterebbero tutte irrisolvibili e SER
  perderebbe significato.
- `src/kirchhoff/eval/cli.py` — `COVERAGE` (13-18) nomina `dc_resistive` e va aggiornata alle
  quattro classi senza perdere la dichiarazione di cecità sull'estrazione; `cmd_build` distribuisce
  la generazione.
- `tests/test_domain.py`, `test_reference_set.py`, `test_percorsi_di_errore.py`, `test_cli.py` —
  suddivisione esistente dei test, da rispettare.
- `scripts/check_domain_coverage.py` — impone 100% righe e rami su `domain/`; legge `coverage.json`.
- `_bmad-output/implementation-artifacts/epic-1-context.md` — vincoli d'epica.

## Tasks & Acceptance

**Execution:**
- [x] `src/kirchhoff/domain/exact.py` — nuovo. Elemento del campo ciclotomico `Q(ζ₁₂)` come quattro
  `Fraction` sulla base `(1, ζ, ζ², ζ³)`, con `ζ⁴ = ζ² − 1`. Somma, prodotto, inverso (per soluzione
  del sistema lineare di moltiplicazione), coniugio, potenza intera, uguaglianza, immersione dei
  razionali. Serve perché `j = ζ³` e `√3 = 2ζ − ζ³` vivono entrambi qui: fasori e rotazioni di 120°
  restano esatti senza mai toccare un float.
- [x] `src/kirchhoff/domain/ir.py` — allargare `ComponentType` a condensatore, induttore, sorgente
  di corrente continua e sorgente sinusoidale; allargare `Quantity` con le grandezze che le nuove
  classi richiedono (costante di tempo, valore iniziale, valore finale, radici caratteristiche);
  estendere la validazione ai nuovi tipi (capacità e induttanza strettamente positive).
- [x] `src/kirchhoff/domain/mna.py` — parametrizzare l'eliminazione di Gauss sullo scalare;
  aggiungere il contributo delle sorgenti di corrente; aggiungere la risoluzione in regime
  sinusoidale a pulsazione razionale, con le ammettenze costruite sul campo ciclotomico.
- [x] `src/kirchhoff/domain/transient.py` — nuovo. Oracolo dei transitori: resistenza equivalente
  vista dall'elemento di accumulo per iniezione di una sorgente di prova risolta con MNA, costante
  di tempo, valore iniziale e finale dal circuito equivalente a `t=0⁺` e a `t→∞`, e polinomio
  caratteristico assemblato dai componenti per il secondo ordine.
- [x] `src/kirchhoff/eval/generator_ac.py` — nuovo. Rete serie/parallelo di R, L, C con sorgente
  sinusoidale; risposta per costruzione propagando il fasore sull'albero.
- [x] `src/kirchhoff/eval/generator_transient.py` — nuovo. Primo ordine RL/RC e secondo ordine RLC
  con radici caratteristiche razionali scelte per prime e componenti derivati da esse.
- [x] `src/kirchhoff/eval/generator_three_phase.py` — nuovo. Sorgente trifase equilibrata a stella e
  carico equilibrato a stella o a triangolo; risposta per costruzione dalla simmetria.
- [x] `src/kirchhoff/eval/reference_set.py` — aggiungere la sequenza di Trasformazioni a `Case`,
  smistare la verifica indipendente per classe, generare le quattro classi, serializzare anche i
  valori ciclotomici in modo che rileggano identici.
- [x] `src/kirchhoff/eval/metrics.py` — smistare `reference_solver` per classe di dominio.
- [x] `src/kirchhoff/eval/cli.py` — aggiornare la nota di copertura alle quattro classi mantenendo
  la dichiarazione sull'estrazione; distribuire `--n` fra le classi.
- [x] `tests/` — un test per ogni riga della matrice I/O, più i criteri negativi: che un oracolo non
  possa coincidere col proprio generatore, che un valore ciclotomico non degradi a float nel giro di
  serializzazione, che nessun nome di Trasformazione esca dall'insieme chiuso, che la parte
  trattenuta resti illeggibile.

**Acceptance Criteria:**
- Dato l'insieme di riferimento prodotto, quando se ne leggono le classi di dominio, allora
  compaiono tutte e quattro le classi in scope e ogni caso porta IR, risposta attesa e sequenza di
  Trasformazioni di riferimento.
- Dato un caso qualsiasi dell'insieme, quando lo si verifica, allora la verifica non riusa la
  formula che l'ha generato e il disaccordo ammesso è zero esatto.
- Dato un caso trifase equilibrato, quando si sommano le tre correnti di fase, allora la somma è
  esattamente nulla — la corrente di neutro è zero per struttura, non per arrotondamento.
- Dato un caso del secondo ordine, quando si sostituiscono le radici nel polinomio caratteristico
  assemblato dai componenti, allora il risultato è esattamente nullo.
- Data la suite completa, quando gira, allora è verde, la copertura globale resta ≥ 95% e `domain/`
  resta al 100% su righe e rami.
- Dato l'harness, quando produce il rapporto sulla parte di sviluppo, allora SER non è salito
  rispetto alla misura precedente (0.0) e la nota di copertura dichiara ancora il limite
  sull'estrazione.

## Design Notes

**Perché `Q(ζ₁₂)` e non un complesso su `Fraction`.** Un complesso razionale basta al regime
sinusoidale, ma non al trifase: `e^{j120°} = −1/2 + j√3/2` porta `√3`, che razionale non è. Il campo
ciclotomico di ordine 12 è la più piccola estensione che contiene insieme `j` e `√3`, ha grado 4 su
`Q`, e la sua aritmetica è quattro razionali con una riduzione modulo `x⁴ − x² + 1`. Tutto resta
esatto, l'uguaglianza è confronto di coefficienti, e le rotazioni di 30° in 30° sono potenze di `ζ`.

**Perché le radici prima dei componenti.** Un RLC generato scegliendo `R, L, C` a caso ha radici
irrazionali quasi sempre. Scegliendo invece due radici razionali negative `s₁, s₂` e derivando
`R/L = −(s₁+s₂)`, `1/(LC) = s₁s₂`, il caso resta esatto e l'oracolo può ancora arrivarci per la via
opposta: assembla il polinomio caratteristico dai componenti e verifica che le radici lo annullino.

**Indipendenza dell'oracolo, per classe.** DC: albero → MNA. Sinusoidale: propagazione del fasore
sull'albero → MNA complessa. Trifase: simmetria → MNA sui quattro nodi, che della simmetria non sa
nulla. Transitorio: costruzione → circuito equivalente resistivo a `t=0⁺` e `t→∞` risolto con MNA,
resistenza di Thévenin per iniezione di prova.

## Verification

**Commands:**
- `uv run --with pytest --with pytest-cov python -m pytest` — atteso: verde, copertura ≥ 95%.
- `uv run --with pytest --with pytest-cov python -m pytest --cov-report=json -q` — atteso: verde,
  produce `coverage.json`.
- `uv run python scripts/check_domain_coverage.py` — atteso: uscita 0, `domain/` al 100%.
- `uv run kirchhoff-eval build --n 60 --out reference-set` — atteso: quattro classi presenti, zero
  scartati o scartati contati esplicitamente.
- `uv run kirchhoff-eval report --root reference-set --split dev` — atteso: `VSR` 1.0, `SER` 0.0,
  nota di copertura che nomina le quattro classi e dichiara l'esclusione dell'estrazione.
- `grep -rn "from \.\.adapters\|from \.\.ports\|import adapters\|import ports" src/kirchhoff/domain/`
  — atteso: nessun risultato.
