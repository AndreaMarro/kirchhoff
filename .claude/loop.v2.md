# Loop di costruzione — Kirchhoff (v2)

Completa la fase *ship* **una storia per iterazione**, attraverso BMAD, fino a esaurire il backlog.
Il piano è scritto e validato: **non ripianificare, esegui.**

La v1 di questo file ha prodotto Epic 1 e la Story 2.1 in ~1h40m, con 159 test e copertura piena.
La sua retrospettiva ha però trovato due difetti nel *processo*, non nel codice. **Questa versione
esiste per correggerli.** Sono le sezioni marcate 🔧.

## Condizione di uscita

Quando `_bmad-output/implementation-artifacts/sprint-status.yaml` non ha più storie in `backlog`,
`ready-for-dev`, `in-progress` o `review`: `ScheduleWakeup(stop: true)` e riepilogo.
Fermati anche, sempre con `stop: true`, in ogni caso di **arresto duro**.

---

## Il ciclo di ogni iterazione

### 1. Orientati — `bmad-sprint-planning`, azione `status`

`sprint-status.yaml` è la verità: il contesto viene compattato fra iterazioni, ciò che non è su
disco è perso. Prendi la **prima** storia non completata in ordine di epica e numero.

Leggi anche `action_items` nello stesso file: la retrospettiva di Epic 1 ne ha lasciati aperti, e
alcuni sono indirizzati proprio a te.

### 2. Costruisci — `bmad-build`

Portagli il contesto minimo: la storia e i suoi criteri da `epics.md`; gli `AD-n` citati, dallo
spine; il blocco **D1–D12** di `docs/00-fonte-piano-kirchhoff.md`. **Non caricare il PRD intero.**

**Test per primi.** Un test per blocco `Given/When/Then`. I criteri **negativi** sono i più
importanti: gate non aggirabile, nessun valore inventato, nessun punteggio persistito, nessun
doppio addebito, nessuna perdita di isolamento fra tenant.

🔧 **Prima di passare oltre, scrivi nella spec della storia la mappa `criterio di accettazione →
test che lo copre`.** Una riga per criterio, col nome del test. Un criterio senza riga è un criterio
non implementato — non entra in `review`. *(azione 3 della retrospettiva di Epic 1)*

### 3. 🔧 Rivedi in un contesto che non ha scritto il codice

**Questo è il difetto che la v1 ha prodotto e che qui va chiuso.** Nella prima esecuzione entrambe
le storie di Epic 1 sono state riviste dallo stesso contesto che le aveva scritte — precisamente la
condizione che uno strato di revisione esiste per rompere.

Non rivedere il tuo lavoro da solo. **Delega a sottoagenti con contesto pulito**, in parallelo:

- **`ecc:python-reviewer`** — idiomi, tipi, sicurezza, correttezza
- **`ecc:silent-failure-hunter`** — errori inghiottiti, fallback silenziosi, propagazione mancante.
  È la lente tematicamente esatta: il prodotto esiste per impedire il fallimento silenzioso, e
  sarebbe assurdo che il codice che lo impedisce ne contenesse.
- **`ecc:type-design-analyzer`** — solo quando la storia introduce tipi di dominio nuovi

Passa a ciascuno: il diff della storia, i criteri di accettazione, gli `AD-n` che vincolano.
**Non passare il tuo ragionamento** — se sanno come hai pensato, smettono di essere indipendenti.

Poi `bmad-code-review` sul diff, come strato di metodo BMAD sopra i sottoagenti.

Risolvi i rilievi. Quelli che decidi di non correggere vanno scritti nel riepilogo **con il
motivo**, non lasciati cadere.

### 4. Se la storia tocca l'interfaccia — `ui-ux-pro-max`

Vale per Epic 3 (3.5, 3.6, 3.7, 3.8), Epic 4 e Epic 7.

- **`ui-ux-pro-max:design-system`** sulla Story 3.5, che è la fondazione: token, scala tipografica,
  componenti base. Tutto ciò che viene dopo eredita da lì.
- **`ui-ux-pro-max:ui-styling`** sui componenti singoli (badge, pannello residui, question-card).
- **`ui-ux-pro-max:design`** sulle schermate intere (Anteprima, Non certificata).

**`DESIGN.md` e `EXPERIENCE.md` restano il contratto e vincono sempre.** `ui-ux-pro-max` esegue
dentro quei vincoli, non li rinegozia. In particolare non tocca: il Rifiuto non è rosso; lo stato
non è mai portato dal solo colore; cifre tabulari ovunque; nessuna animazione celebrativa.

Verifica di accessibilità obbligatoria su ogni storia di interfaccia: la schermata resta
interpretabile **in scala di grigi**, il percorso è completabile da **tastiera**, ogni disegno ha
un'**alternativa testuale topologica**.

### 5. Verifica

```bash
uv run --with pytest --with pytest-cov python -m pytest
uv run --with pytest --with pytest-cov python -m pytest --cov-report=json -q
uv run python scripts/check_domain_coverage.py
uv run python scripts/check_boundaries.py
uv run kirchhoff-eval build --n 60 --out reference-set
uv run kirchhoff-eval report --root reference-set --split dev
```

Una storia è **fatta** quando, tutte insieme:

- ogni criterio ha un test che passa, e la mappa criterio → test è nella spec;
- l'intera suite è verde;
- 🔧 **la copertura globale non scende rispetto all'iterazione precedente.** Non basta restare sopra
  il 95%: dopo Epic 1 il progetto è al 100% righe e rami, e quello è il nuovo pavimento. Una
  copertura che scende è una regressione, anche se il gate numerico passa;
- `check_domain_coverage.py` esce 0 — `domain/` al 100%, righe **e** rami;
- `check_boundaries.py` esce 0;
- l'eval non peggiora, **e SER non sale, mai**.

Leggi gli exit code senza pipe: `cmd > file 2>&1; echo $?`. Dopo una pipe `$?` è l'exit di `tail`,
non del comando che ti interessa.

### 6. Chiudi l'epica — `bmad-retrospective`

Quando l'ultima storia di un'epica passa a `done`. Le azioni che produce finiscono in
`sprint-status.yaml` e vanno lette all'iterazione dopo. Se l'epica ha prodotto superficie API o
interfaccia, anche `bmad-qa-generate-e2e-tests`.

### 7. Registra

Aggiorna **con lo script, mai a mano**:

```bash
uv run /Users/andreamarro/.claude/plugins/cache/bmad-method/bmad-method-analyze-plan-build/6.11.0/src/bmm-skills/plan/bmad-sprint-planning/scripts/sprint_plan.py generate \
  --epic-file _bmad-output/planning-artifacts/epics.md \
  --status-file _bmad-output/implementation-artifacts/sprint-status.yaml \
  --stories-dir _bmad-output/implementation-artifacts \
  --project "Kirchhoff" --date "<MM-DD-YYYY HH:MM>" \
  --set <chiave-storia>=done
```

Riepilogo in una riga: storia, test aggiunti, copertura globale e `domain/`, VSR, SER, rilievi dei
revisori indipendenti non corretti.

Poi `ScheduleWakeup`: `delaySeconds: 60`, `noop: false`, `reason` che nomina la storia successiva.

---

## 🔧 Azioni aperte dalla retrospettiva di Epic 1

Indirizzate a te. Applicale quando arrivi alla storia indicata, senza aspettare che qualcuno te lo
ricordi.

| Alla storia | Cosa fare |
|---|---|
| **2.5** | Riconcilia l'ambito prima di iniziare: `solve_phasor` e `mna_matrix_at` **esistono già** in `domain/mna.py`. Non riscriverli; restringi la storia a ciò che manca. |
| **2.7** | Il quinto controllo (sanità fisica) oggi non copre regime sinusoidale e trifase. Estendilo lì. |
| **2.11** | Allarga le grandezze richieste dei casi di transitorio a costante di tempo e radici caratteristiche, quando il motore sa produrle. |
| **ovunque** | Traduci in gate eseguibili i vincoli D1–D12 che toccano il codice e non ne hanno ancora uno. Un vincolo senza gate è una raccomandazione. |

---

## Story 1.3 — la metà fotografica, in dettaglio

È la prima in coda e ha caratteristiche che nessun'altra ha.

**Dataset, entrambi verificati alla fonte, entrambi utilizzabili commercialmente:**

- **CGHD** — `cc-by-4.0` (verificata dall'API Zenodo, record 14042961). 3.173 immagini, 32
  disegnatori, bounding box PASCAL VOC, netlist ASC per una parte. `cghd-zenodo-14.zip`,
  4.375.895.985 byte.
- **Digitize-HCD** — `CC BY 4.0` (verificata sulla pagina Mendeley Data, versione 2). 1.277
  immagini, oltre 150 volontari, 17 classi, **posizioni dei terminali** — che a CGHD mancano e che
  sono l'informazione da cui si ricostruisce la connettività.

**Esclusi, e non vanno riaperti:** Image2Net `CC BY-NC-ND`, Fiore `CC BY-NC-SA`, JUHCCR-v1
(licenza non verificata). La clausola NC è incompatibile con un prodotto a pagamento.

**Vincoli propri della storia:**

- L'attribuzione CC-BY è un **obbligo di licenza**: un controllo automatico deve fallire se manca
  negli artefatti che usano i dataset. Il testo esatto è in `docs/01-fonti-esterne.md`.
- Almeno **30 immagini** annotate a mano con IR e risultato, da **almeno 10 disegnatori diversi** —
  altrimenti stai misurando la calligrafia di una persona sola.
- Il rapporto deve riportare VSR e SER **separati** per metà strutturata e metà fotografica.
  Mediarli nasconde esattamente il numero che interessa.
- Implementa **NED** (distanza di edit fra grafi normalizzata su dispositivi + net + porte) accanto
  a SER. La formula è pubblicata e adottabile; il dataset di Image2Net no. Riferimento contro cui
  misurarsi: 80,77% di successo, 0,116 di NED medio.
- Il download è grande. Se la rete non è disponibile o lo spazio non basta, **fermati e dillo** —
  non ripiegare su un campione inventato.

---

## Quando qualcosa non funziona — `superpowers:systematic-debugging`

**Al primo test che fallisce e non si sistema con la correzione ovvia.** Non tentare la seconda
ipotesi a caso: in un loop il tentativo casuale si moltiplica per il numero di iterazioni.

Vale anche per: un test che passa da solo e fallisce nella suite; una copertura che scende senza
aver tolto test; **un residuo di Verifica non nullo** dove l'aritmetica è esatta — lì un residuo
diverso da zero è *sempre* un bug; SER che sale dopo una modifica innocua.

Scrivi la causa radice nel riepilogo. Una causa trovata e non scritta viene ritrovata da capo tre
iterazioni dopo.

---

## Vincoli che non si negoziano mai

Da D1–D12 e dagli AD. Codice che li viola è sbagliato anche se i test passano.

1. **Nessun numero mostrato all'utente esce da un modello linguistico** (D5, AD-4). Segnaposto
   `[[q1.value]]`; il renderer sostituisce dai valori calcolati.
2. **Gate di pubblicazione in un solo punto, nessun bypass** (AD-5). Solo `publish()` produce
   `Published`. Nessun flag lo disattiva, nemmeno in test.
3. **`domain/` non importa nulla del progetto** (paradigma ports-and-adapters).
4. **Trasformazioni pure** (AD-2): niente I/O, orologio, casualità.
5. **Nessun tipo associa una misura di rendimento a una persona** (D9, AD-11).
6. **`Refusal` e `Failure`: tipi e canali distinti** (AD-13).
7. **Aritmetica dell'oracolo esatta**, `Fraction`, mai float.
8. **Niente confidence auto-dichiarate** (D4): l'ambiguità è disaccordo fra K ≥ 3 pass, e `K ≥ 3` è
   imposto dal codice (AD-12).
9. **`subject_id` ovunque, mai `user_id`** (AD-20): l'utente anonimo esiste ed è il primo che ogni
   persona attraversa.
10. **Superficie assistente, norma verificata** (AD-16, spec `ext-apps` 2026-01-26): `ui://` per la
    risorsa; `mimeType` **deve** essere `text/html;profile=mcp-app`; associazione via
    `_meta.ui.resourceUri`; JSON-RPC 2.0 su postMessage. Ogni risposta di tool con UI porta **due
    campi distinti**: `content` (testo per il modello e per host senza UI) e `structuredContent`
    (dati per il rendering). *«Tools MUST return meaningful content array even when UI is available»*.

---

## Arresto duro — fermati e chiedi

`ScheduleWakeup(stop: true)` e spiega, quando:

- **La storia dipende da una decisione aperta.** In `implementation-readiness.md`: profilo
  curricolare (C1, blocca 2.9), ambiente LaTeX (C2, blocca 4.4), formato e-learning (C3, blocca 4.4
  e 6.4), soglia di uso equo (C4, blocca 5.4). **Non inventarle.** Salta a una storia che non ne
  dipende e segnalalo; se non ce n'è, fermati.
- **SER sale**, o **la copertura scende**, e `systematic-debugging` non ha trovato la causa.
- **Gli stessi test falliscono dopo un'indagine sistematica completa.** Riporta cosa hai escluso.
- **Un criterio richiede di violare un vincolo.** È un conflitto di piano: `bmad-correct-course`,
  non codice.
- **Due artefatti di piano si contraddicono.** È già successo una volta. Non scegliere tu quale ha
  ragione: fermati e nominali entrambi.
- **Servono chiave, account o servizio esterno** non configurati.
- **Un revisore indipendente solleva un rilievo che non sai risolvere** senza cambiare un `AD`.

---

## Cosa non fare

- Non ripianificare, non riscrivere epiche o PRD, non aggiungere storie.
- Non più di una storia per iterazione.
- Non rivedere il proprio codice da soli — è il difetto che questa versione esiste per correggere.
- Non toccare `docs/00-fonte-piano-kirchhoff.md`.
- Non abbassare una soglia di copertura per far passare una storia.
- Non pubblicare, push, pagare, registrare account.
- Non usare materiale con licenza non commerciale. Fonti e licenze in `docs/01-fonti-esterne.md`.

---

## Contesto in una riga

Kirchhoff vende **la certezza che il numero è giusto**: ogni soluzione supera cinque controlli
indipendenti prima di essere mostrata, e quando non li supera il sistema lo dice invece di
pubblicare. Se una scelta di implementazione indebolisce quella promessa, è la scelta sbagliata
anche quando è la più comoda.
