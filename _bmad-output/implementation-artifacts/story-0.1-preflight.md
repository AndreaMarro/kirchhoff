# Story 0.1 — Preflight del runtime BMAD e del Loop Kirchhoff v3

**Data:** 2026-08-24 · **Natura:** diagnostica, nessuna correzione applicata
**Regola osservata:** «Non partire sistemando `_bmad/`. Prima stabilisci con prove quale dei tre stati descrive realmente il progetto.»

Ogni riga sotto è una misura eseguita, non una lettura di documentazione. Dove la
prova manca, è scritto che manca.

---

## D1 — Quale dei tre stati descrive `_bmad/`

### VERDETTO: `MISSING_RUNTIME_HELPERS`

Non `BROKEN_PARTIAL_INSTALL`: nulla di ciò che esiste è rotto o incoerente.
Non `INTENTIONAL_RENDERED_INSTALL`: il render **non** sostituisce il renderer.

### Prove

**P1 — Inventario.** `_bmad/` contiene esattamente tre cose:
`config.toml`, `custom/bmad-build.toml`, `render/bmad-build/…`.
Assenti: `scripts/`, `bmm/`, `core/`.

**P2 — Il formato di config del progetto è quello GIUSTO.** Il resolver ufficiale
del plugin, eseguito contro questo progetto, esce **0** e restituisce i valori
corretti (`user_name: Andrea`, `project_name: Kirchhoff`,
`communication_language: Italian`, i tre path di `bmm`):

    uv run <plugin>/src/scripts/resolve_config.py --project-root <kirchhoff>
    → exit 0

**P2-bis — L'incoerenza è DENTRO v6.11.0, non nel progetto.** Nel plugin
convivono due convenzioni: `bmad-spec`, `bmad-architecture`, `bmad-customize`,
`bmad-help` citano `config.toml`; `bmad-prd`, `bmad-ux`, `bmad-product-brief`,
`bmad-sprint-planning`, `bmad-prfaq` citano `_bmad/bmm/config.yaml`. Il file che
il resolver legge davvero è `config.toml`. **Le cinque skill che chiedono
`config.yaml` hanno documentazione stantia; il progetto no.** Questa è una
rettifica di una diagnosi precedente che dava per mancante `bmm/config.yaml`.

**P3 — 41 file di skill invocano `{project-root}/_bmad/scripts/resolve_customization.py`.**
Tutte e 41 hanno un fallback documentato («If the script fails, resolve the
`workflow` block yourself by reading these three files…»). Per questo i passi 1–3
della catena BMAD hanno funzionato: **degradati, non sani.**

**P4 — `bmad-build` è l'unica senza fallback.** `bmad-build/SKILL.md` in tutto
consiste di un comando e due bullet:

    uv run --no-cache "{project-root}/_bmad/scripts/render_skill.py" …
    - On success, read and follow the one absolute `workflow.md` …
    - On failure (including `uv` being unavailable), report the command output
      and HALT. Do not run any workflow source directly.

**P5 — Esecuzione del comando esatto di `SKILL.md:9`:**

    → EXIT=2
    error: Failed to spawn: <kirchhoff>/_bmad/scripts/render_skill.py
      Caused by: No such file or directory (os error 2)

**P6 — Controprova, stesso renderer dal path del plugin:**

    → EXIT=0
    stdout: read and follow …/_bmad/render/bmad-build/kirchhoff-d07b09e6efac/149e1b7f45bfdc0ec5d0/workflow.md

Il renderer funziona. Semplicemente non è dove le skill lo cercano.

### Conseguenza operativa

**La Fase 4 BMAD (`bmad-build`) è oggi hard-bloccata.** Non degrada: si ferma.
Il contratto della skill vieta esplicitamente di eseguire il workflow sorgente
come ripiego.

---

## D2 — Un implementatore a contesto fresco riceve davvero i fatti di `AGENTS.md`?

### VERDETTO: il meccanismo FUNZIONA; la consegna OGGI NON AVVIENE.

Sono due strati distinti e vanno tenuti separati.

**Strato A — il meccanismo di customizzazione: PROVATO FUNZIONANTE.**

Il render fresco generato in P6 contiene, a `workflow.md:50`:

    ### Step 2: Load Persistent Facts
    - file:{project-root}/**/project-context.md
    - file:{project-root}/AGENTS.md

Diff contro il render del 13 agosto: `> 50:- file:{project-root}/AGENTS.md`.
Unica differenza. L'override in `_bmad/custom/bmad-build.toml` è entrato.

**Il render non è mai riusato a vuoto.** L'hash di generazione è derivato dal
contenuto: `3efdf204dcef6f9d7d15` (13 ago) → `149e1b7f45bfdc0ec5d0` (oggi). Un
render stantio non viene silenziosamente riutilizzato: cambia directory.

**Strato B — la consegna: NON AVVIENE.**

`bmad-build` esce 2 e si ferma **prima** dello Step 2. Nessun implementatore
viene mai lanciato. La domanda «riceve i fatti?» oggi non si pone: non nasce.

**Osservazione collaterale, decisiva.** `project-context.md` esiste in
**0** copie in tutto il repo. Il glob di default spedito da BMAD risolve a
**niente**. Quindi:

- il render del 13 agosto, se fosse stato usato, avrebbe consegnato **zero fatti**;
- `AGENTS.md` non è ridondante rispetto a `project-context.md`: **è l'unica
  superficie di fatti viva.** La decisione di scriverlo era necessaria.

`AGENTS.md` contiene 12 occorrenze dei termini canary (Kirchhoff, CircuitCheck,
StudentTrace, holdout).

### Stato di R1

- **R1 artifact: CLOSED** (confermato: l'override è corretto ed efficace nel render)
- **R1 runtime effectiveness: BLOCKED**, non `PENDING`. La causa non è la
  customizzazione — è l'assenza del renderer. Cambia il rimedio.

---

## D3 — Matrice di capacità contro il loop Ardesia REALMENTE usato

### Il loop reale

`~/ARDESIA-KNOWLEDGE/ops/loop/ardesia-loop.sh` — 55.532 byte, eseguibile,
modificato 19 ago 18:21. Il `giornale/` è stato scritto **oggi alle 21:30**
(ora locale); 381 iterazioni registrate. Le ricevute in `91-Auto-Receipts/`
sono ferme al 2 agosto: sono la **generazione precedente**, non questa.

### RETTIFICA — l'interfaccia che ho scritto in `.claude/loop.md` non è quella di Ardesia

`ardesia-loop.sh` accetta **tre** argomenti e nient'altro:

    --ore N | --iterazioni N | --prova        (argomento ignoto → exit 64)

**Non esiste** una superficie `doctor / status / dry-run / run / resume`.
Quella quintupla è **mia invenzione**, non un prestito da Ardesia. `--prova` è
l'analogo del dry-run (forza `ITERAZIONI=1`). Le altre funzioni non sono
sottocomandi: sono **script separati** — `stato.sh`, `perpetuo.sh`,
`precondizioni.sh`, `cov.sh`, `verifica-semantica.sh`, `receipt-vista.py`,
`flotta.py`, `compiti.py`, `convergenza.py`.

Va deciso esplicitamente se Kirchhoff copia la forma di Ardesia (script
separati) o adotta la quintupla. **Non è una differenza cosmetica**: la
quintupla implica uno stato condiviso fra verbi che Ardesia non ha.

### I quattro meccanismi dichiarati in testa al file, tutti verificati nel corpo

| # | Meccanismo | Dove | Kirchhoff |
|---|-----------|------|-----------|
| 1 | **PRECONDIZIONI** — fail-closed prima di spendere token | `precondizioni.sh`, riga 383; exit 12 osservato oggi | ASSENTE |
| 2 | **WATCHDOG** — l'iterazione che non finisce è uccisa, non attesa | righe 607-608: `kill -TERM` → `sleep 10` → `kill -KILL` | ASSENTE |
| 3 | **RATCHET** — le metriche non regrediscono | `stato/ratchet.json`, riga 168; misurato su una **copia** (righe 724-731) perché `ratchet.py` aggiorna il file quando passa | ASSENTE |
| 4 | **GIORNALE** — append-only, un file per iterazione | `giornale/`, 381 file | ASSENTE |

Meccanismo quinto, non dichiarato in testa ma presente e attivo:

| 5 | **FERMO** — arresto che richiede una persona | `stato/FERMO-SERVE-ANDREA.txt` | ASSENTE |

### Stato persistente su disco (Ardesia)

    stato/loop-state.json         34 KB
    stato/ratchet.json            .ratchet-candidato.json
    stato/convergenza.json        compiti-tentati.json
    stato/refutazioni/            refutazioni-aperte.txt
    stato/FERMO-SERVE-ANDREA.txt

### Kirchhoff: cosa esiste

`.claude/loop.md` (31.646 byte) + `loop.v1.md` + `loop.v2.md`. **Prosa.**
Eseguibili in `.claude/`: **zero**. Nessuna directory `ops/`. Nessuno stato.

**Il divario non è di funzionalità: è totale.** Kirchhoff ha la dottrina
scritta e nessun meccanismo.

### Nota di stato: il loop Ardesia è FERMO in questo momento

    OROLOGIO FERMO
    causa:      il prodotto ha 4 file non committati (erano 0)
    iterazione: 3
    quando:     2026-08-22T01:10:10Z
    Serve una persona.

E l'ultima iterazione registrata (oggi, 19:30:25Z) mostra il cancello che tiene:

    precondizioni exit 12.
    FERMO gia' presente: il rilancio muore qui, a costo zero.

Il giornale cresce (ogni tentativo è inciso), lo stato è fermo dal 22 agosto.
**Il meccanismo funziona esattamente come progettato** — ed è la prova più
forte che il fail-closed vale la pena di essere copiato.

---

## D4 — Invocabilità, etichettata

| Capacità | Etichetta | Prova |
|---|---|---|
| `bmad-build` | **NON invocabile — PROVED NOW** | exit 2, `No such file or directory`; `SKILL.md` impone HALT |
| Blind Hunter | **PROVED BY 0.2** | è un `review_layer` dentro `step-04-review` di `bmad-build`: transitivamente bloccato. Il suo testo risolve correttamente nel manifest (non è quello il difetto) |
| `ScheduleWakeup` | **esiste — PROVED NOW; ma è il meccanismo SBAGLIATO** | presente nella superficie runtime. Ardesia **non lo usa**: usa `while` + `sleep $PAUSA` in shell + `perpetuo.sh`. Per un loop eseguibile da riga di comando, la cadenza sta nella shell, non nell'agente |
| Persistenza di stato | **PROVED NOW in Ardesia · ASSENTE in Kirchhoff → PROVED BY 0.2** | `stato/*.json` + `giornale/` vs. nulla |

---

## D5 — MODEL CAPABILITY PRE-FLIGHT

### Superficie CLI misurata (`claude --help`)

| Flag | Valori | Esito |
|---|---|---|
| `--model` | alias (`fable`, `opus`, `sonnet`) **o** nome pieno (`claude-fable-5`) | DISPONIBILE |
| `--effort` | **`low, medium, high, xhigh, max`** | DISPONIBILE — cinque livelli, esattamente quelli del router |
| `--fallback-model` | modello | DISPONIBILE |
| `--agents` | JSON che definisce agenti custom | DISPONIBILE |
| `--max-budget-usd` | soglia in dollari | DISPONIBILE |
| `--disallowed-tools` | elenco strumenti | DISPONIBILE |

### Prova di esercizio reale — non solo di esistenza

`ardesia-loop.sh:593-602`, in produzione da 381 iterazioni:

    ARDESIA_ITERAZIONE=1 claude -p \
        --model claude-opus-5 \
        --effort max \
        --dangerously-skip-permissions \
        --disallowed-tools Workflow \
        --add-dir "$PRODOTTO" \
        --max-budget-usd "$BUDGET" \
        --setting-sources project,local \
        "${FLAG_PLUGIN[@]}" \
        --output-format stream-json --verbose

### Verdetto per il routing Sonnet 5 → Opus 5 → Fable 5

**PERMESSO, con una riserva precisa.**

| Elemento del router | Stato | Come |
|---|---|---|
| Scelta del modello per classe di rischio | **PROVED NOW** | `--model` per invocazione; R0→`claude-sonnet-5`, R1/R2→`claude-opus-5`, revisore→`claude-fable-5` |
| Livello di sforzo per classe | **PROVED NOW** | `--effort {high,xhigh,max}`, tutti e cinque i livelli accettati |
| Contesto fresco per il revisore | **PROVED NOW** | `claude -p` separato = processo nuovo. La regola «il revisore non vede il ragionamento dell'implementatore» è garantita dal confine di processo, non dalla buona volontà del modello |
| Fallback | **PROVED NOW** | `--fallback-model` |
| Tetto di costo | **PROVED NOW** | `--max-budget-usd` (Ardesia: 25) |
| **Revisore con modello diverso DENTRO una sola invocazione** | **PROVED BY 0.3** | due strade: `--agents <json>`, oppure una invocazione `claude -p` per revisore. Non misurato qui |

**Riserva — la strada `Workflow` è preclusa dal precedente.** Ardesia passa
`--disallowed-tools Workflow`: il loop **vieta** lo strumento Workflow dentro
l'iterazione. Se Kirchhoff v3 vuole revisori avversari paralleli, deve
ottenerli da `--agents`/subagenti o da invocazioni separate — **non** da
Workflow, salvo decisione esplicita di divergere da Ardesia.

### D-4 confermato alla sorgente

`docs/04-ricerca-token-e-automiglioramento.md` §2.4 registrava: *«Il loop gira
tutto a `--effort max`. Non applicato.»* — misurato allora sul comportamento.
**Ora è verificato alla riga sorgente**: `ardesia-loop.sh:595` recita
`--effort max` incondizionatamente, per ogni iterazione, senza ramo. Il difetto
non è dedotto: è letterale. La topologia risk-routed è la sua chiusura.

---

## Effetto collaterale da dichiarare

La controprova P6 ha **creato** la directory
`_bmad/render/bmad-build/kirchhoff-d07b09e6efac/149e1b7f45bfdc0ec5d0/`.
È benigna — `bmad-build` genera queste directory da sé a ogni invocazione — ma è
una scrittura nel repo fatta da una story diagnostica. Va tenuta (è la prova di
D2) o rimossa; è una decisione, non un automatismo.

---

## Cosa NON è stato fatto, deliberatamente

- Nessuna installazione, copia o link di `_bmad/scripts/`.
- Nessuna esecuzione di `npx bmad-method install`.
- Nessuna modifica a `.claude/loop.md`, a `bmad-chain-status.json`, alla tabella FASE 1.
- Nessuna lettura di `reference-set/holdout/`.
- Nessuna Story di prodotto usata come cavia.
