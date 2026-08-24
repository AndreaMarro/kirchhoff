# Loop di costruzione — Kirchhoff

Completa la fase *ship* di Kirchhoff **una storia per iterazione**, attraverso BMAD, fino a
esaurire il backlog. Il piano è già scritto e validato: **non ripianificare, esegui.**

## Condizione di uscita

Quando `_bmad-output/implementation-artifacts/sprint-status.yaml` non contiene più storie in
`backlog`, `ready-for-dev`, `in-progress` o `review`, il lavoro è finito: chiama
`ScheduleWakeup(stop: true)` e riepiloga cosa è stato costruito.

Fermati anche — sempre con `stop: true` e spiegando perché — in ogni caso di **arresto duro**.

---

## Il ciclo BMAD di ogni iterazione

BMAD è il metodo, non un accessorio. Ogni iterazione attraversa le sue skill nell'ordine previsto
dalla fase *ship*. Non scrivere codice fuori da questo ciclo.

### 1. Orientati — `bmad-sprint-planning`, azione `status`

Invoca `bmad-sprint-planning` con intento **status** per ottenere conteggi, rischi, voci aperte e
azione successiva raccomandata. È il modo previsto per sapere dove sei; `sprint-status.yaml` è la
verità, non il tuo ricordo — il contesto viene compattato fra un'iterazione e l'altra e tutto ciò
che non è su disco è perso.

Prendi la **prima** storia non completata in ordine di epica e numero. Non saltare avanti: le
storie dentro un'epica sono ordinate perché ognuna si appoggia solo alle precedenti.

### 2. Costruisci — `bmad-build`

Invoca `bmad-build` sulla storia scelta. È il ciclo ufficiale di Fase 4: chiarisce l'intento,
pianifica, implementa, rivede, presenta. Lascia che sia lui a guidare l'implementazione.

Portagli il contesto minimo e preciso:

- la storia e i suoi criteri di accettazione, da `_bmad-output/planning-artifacts/epics.md`;
- gli `AD-n` che la storia cita, da
  `_bmad-output/planning-artifacts/architecture/*/ARCHITECTURE-SPINE.md`;
- se tocca interfaccia: `ux-designs/*/EXPERIENCE.md` e `DESIGN.md`;
- il blocco **D1–D12** in testa a `docs/00-fonte-piano-kirchhoff.md`.

**Non caricare il PRD intero.** I criteri di accettazione sono autoportanti; il PRD serve solo se
un criterio è ambiguo.

**Test per primi.** Un test per blocco `Given/When/Then`, che fallisce prima di scrivere il
codice. I criteri **negativi** sono i più importanti e vanno sempre testati: che il gate non si
aggiri, che un valore illeggibile non venga inventato, che nessun punteggio sia persistito, che
non ci sia doppio addebito, che un tenant non veda l'altro. Un criterio negativo senza test non è
implementato.

### 3. Rivedi — `bmad-code-review`

Dopo `bmad-build`, invoca `bmad-code-review` sul diff della storia. È uno strato in più oltre alla
revisione interna di Build, ed è quello che intercetta ciò che chi ha appena scritto il codice non
vede.

Risolvi i rilievi prima di chiudere la storia. Un rilievo che decidi di non correggere va scritto
nel riepilogo dell'iterazione con il motivo — non lasciato cadere.

### 4. Verifica

```bash
uv run --with pytest --with pytest-cov python -m pytest
uv run --with pytest --with pytest-cov python -m pytest --cov-report=json -q
uv run python scripts/check_domain_coverage.py
uv run kirchhoff-eval build --n 60 --out reference-set
uv run kirchhoff-eval report --root reference-set --split dev
```

Una storia è **fatta** quando, tutte insieme:

- ogni criterio di accettazione ha un test che passa;
- l'intera suite è verde, non solo i test nuovi;
- **la copertura globale resta ≥ 95%** (fallisce da sola: `--cov-fail-under=95` è in
  `pyproject.toml`);
- **`domain/` resta al 100%, righe e rami** — `scripts/check_domain_coverage.py` esce 0;
- l'eval non è peggiorato, **e in particolare SER non sale, mai**;
- nessun modulo sotto `domain/` importa `adapters/` o `ports/`.

Se la storia tocca estrazione, validazione, Trasformazioni o Piano didattico, l'eval è
obbligatorio prima di chiudere (NFR-10).

### 5. Chiudi l'epica — `bmad-retrospective`

Quando l'**ultima** storia di un'epica passa a `done`, invoca `bmad-retrospective` prima di
iniziare l'epica successiva. Le voci d'azione che produce finiscono in `sprint-status.yaml` e vanno
lette all'iterazione dopo.

Se l'epica ha prodotto codice con superficie API o interfaccia, invoca anche
`bmad-qa-generate-e2e-tests` sulla parte implementata.

### 6. Registra e passa oltre

Aggiorna lo stato **con lo script, mai a mano**:

```bash
uv run /Users/andreamarro/.claude/plugins/cache/bmad-method/bmad-method-analyze-plan-build/6.11.0/src/bmm-skills/plan/bmad-sprint-planning/scripts/sprint_plan.py generate \
  --epic-file _bmad-output/planning-artifacts/epics.md \
  --status-file _bmad-output/implementation-artifacts/sprint-status.yaml \
  --stories-dir _bmad-output/implementation-artifacts \
  --project "Kirchhoff" --date "<MM-DD-YYYY HH:MM>" \
  --set <chiave-storia>=done
```

Chiudi con una riga: quale storia, quanti test aggiunti, copertura globale, copertura `domain/`,
VSR e SER correnti.

Poi `ScheduleWakeup` con `delaySeconds: 60` — non stai aspettando niente di esterno, stai
lavorando — `noop: false`, e `reason` che nomina la storia successiva.

---

## Quando qualcosa non funziona — `superpowers:systematic-debugging`

**Al primo test che fallisce e non si sistema con la correzione ovvia, invoca
`superpowers:systematic-debugging`.** Non tentare la seconda ipotesi a caso: due tentativi
casuali costano più di un'indagine strutturata, e in un loop autonomo il tentativo casuale si
moltiplica per il numero di iterazioni.

Vale anche per:

- un test che passa da solo e fallisce nella suite, o viceversa;
- una copertura che scende senza che tu abbia tolto test;
- un residuo di Verifica non nullo dove l'aritmetica è esatta — lì un residuo diverso da zero è
  **sempre** un bug, mai rumore;
- SER che sale dopo una modifica che sembrava innocua.

Dopo l'indagine, scrivi la causa radice nel riepilogo dell'iterazione. Una causa radice trovata e
non scritta viene ritrovata da capo tre iterazioni dopo.

---

## Vincoli che non si negoziano mai

Vengono da D1–D12 e dagli AD dello spine. Codice che li viola è sbagliato anche se i test passano.

1. **Nessun numero mostrato all'utente esce da un modello linguistico** (D5, AD-4). Il generatore
   di testo produce segnaposto `[[q1.value]]`; il renderer sostituisce dai valori calcolati.
2. **Il gate di pubblicazione ha un solo punto di codice e nessun bypass** (AD-5). Solo
   `publish()` produce `Published`. Nessun flag lo disattiva, nemmeno in test.
3. **`domain/` non importa nulla del progetto** (paradigma ports-and-adapters).
4. **Le Trasformazioni sono pure** (AD-2): niente I/O, niente orologio, niente casualità.
5. **Nessun tipo associa una misura di rendimento a una persona** (D9, AD-11). Se una storia
   sembra chiederlo, hai letto male: fermati.
6. **`Refusal` e `Failure` restano tipi e canali distinti** (AD-13).
7. **L'aritmetica dell'oracolo è esatta**, `Fraction`, mai float.
8. **Niente confidence auto-dichiarate dal modello** (D4): l'ambiguità si misura come disaccordo
   fra K ≥ 3 pass, e `K ≥ 3` è imposto dal codice (AD-12).
9. **`subject_id` ovunque, mai `user_id`** per firma, quota, ledger e idempotenza (AD-20):
   l'utente anonimo esiste ed è il primo che ogni persona attraversa.

---

## Arresto duro — fermati e chiedi, non indovinare

Chiama `ScheduleWakeup(stop: true)` e spiega, quando:

- **La storia dipende da una decisione aperta.** Le quattro sono in
  `_bmad-output/planning-artifacts/implementation-readiness.md`: ateneo e corso del primo Profilo
  curricolare (C1, blocca 2.9), ambiente LaTeX di riferimento (C2, blocca 4.4), formato e-learning
  (C3, blocca 4.4 e 6.4), soglia di uso equo (C4, blocca 5.4). **Non inventarle.** Salta alla
  storia successiva che non dipende da esse e segnalalo; se non ce n'è, fermati.
- **SER sale** rispetto all'iterazione precedente.
- **La copertura scende sotto le soglie** e `systematic-debugging` non ha trovato la causa.
- **Gli stessi test falliscono dopo un'indagine sistematica completa.** Non accanirti: riporta
  dove si rompe e cosa hai escluso.
- **Un criterio di accettazione richiede di violare un vincolo** della sezione precedente. È un
  conflitto di piano: si risolve con `bmad-correct-course`, non nel codice. Fermati e dillo.
- **Una storia richiede una chiave, un account o un servizio esterno** non configurato.

---

## Cosa non fare

- Non ripianificare, non riscrivere epiche o PRD, non aggiungere storie. Se il piano è sbagliato,
  si corregge con `bmad-correct-course` in una sessione dedicata.
- Non implementare più di una storia per iterazione, anche se sembrano piccole.
- Non toccare `docs/00-fonte-piano-kirchhoff.md`: è il riferimento immutabile.
- Non abbassare una soglia di copertura per far passare una storia. La soglia scende solo con una
  decisione esplicita scritta nel riepilogo.
- Non pubblicare, non fare push, non pagare, non registrare account.
- Non usare materiale con licenza non commerciale. Fonti e licenze verificate stanno in
  `docs/01-fonti-esterne.md`; CGHD è CC-BY-4.0 e va attribuito ovunque venga usato.

---

## Contesto in una riga

Kirchhoff risolve circuiti di elettrotecnica e vende **la certezza che il numero è giusto**: ogni
soluzione supera cinque controlli indipendenti prima di essere mostrata, e quando non li supera il
sistema lo dice invece di pubblicare. Se una scelta di implementazione indebolisce quella
promessa, è la scelta sbagliata anche quando è la più comoda.
