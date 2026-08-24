# Story 0.1 — Parte II: remediation e prova runtime

**Data:** 2026-08-24 · **Precede:** `story-0.1-preflight.md` (diagnostica, non modificata)

La Parte I ha classificato lo stato come `MISSING_RUNTIME_HELPERS` e provato che
`bmad-build` usciva 2 e si fermava. Questa parte lo rimedia e prova il runtime.

---

## 1. Search-before-build: BMAD offre materializzazione ufficiale?

**Risposta: NO, non granulare.**

`tools/installer/bmad-cli.js` espone esattamente tre comandi: `install`,
`status`, `uninstall`. Non esiste un comando che materializzi solo
`_bmad/scripts/`.

Ma il **meccanismo** ufficiale è leggibile e riproducibile —
`tools/installer/core/installer.js:661-681`, metodo `_installSharedScripts`:

    const srcScriptsDir = path.join(paths.srcDir, 'src', 'scripts');
    await fs.remove(paths.scriptsDir);
    await fs.ensureDir(paths.scriptsDir);
    const isInstallable = (srcPath) => {
      const base = path.basename(srcPath);
      return base !== 'tests' && base !== '__pycache__'
          && base !== '.pytest_cache' && !base.endsWith('.pyc');
    };
    await fs.copy(srcScriptsDir, paths.scriptsDir, { overwrite: true, filter: isInstallable });

Il vendoring qui applicato **replica esattamente questo filtro**. Non è un fork
della procedura: è la stessa operazione, eseguita in modo stretto.

### Diagnosi affinata a causa singola

`_installSharedScripts` semina **tre** cose, e mancavano tutte e tre:

| Cosa | Stato prima |
|---|---|
| `_bmad/scripts/` | assente |
| `_bmad/custom/.gitignore` (`*.user.toml`) | assente |
| `_bmad/render/.gitignore` (`*` + `!.gitignore`) | assente |

**Il difetto non era diffuso: era un solo metodo dell'installer mai eseguito.**

---

## 2. Vendoring — 5 file, byte-identical

| File | SHA256 (16) | Modo upstream | Modo locale | Match |
|---|---|---|---|---|
| `config_utils.py` | `48afe2bc18a29201` | 644 | 644 | YES |
| `memlog.py` | `3b00f82ca33dc422` | 644 | 644 | YES |
| `render_skill.py` | `8496d0d8b449d64c` | 644 | 644 | YES |
| `resolve_config.py` | `fc78866fd42862d4` | 644 | 644 | YES |
| `resolve_customization.py` | `9b5124e0b781823a` | 755 | 755 | YES |

Hash completi e policy in `_bmad/scripts.pin.json`. `cp -p` ha preservato anche
i metadati: il bit di esecuzione su `resolve_customization.py` è intatto.

### Chiusura provata, non assunta

Le skill BMAD invocano per nome **quattro** script:
`memlog.py`, `render_skill.py`, `resolve_config.py`, `resolve_customization.py`.
`config_utils.py` non è invocato da nessuna skill: è importato dagli altri tre.
**4 invocati + 1 dipendenza transitiva = 5 = l'intero contenuto di `src/scripts/`
al netto di `tests/`.** La copia è la chiusura, non un campione.

### Testimone indipendente della provenienza

`render_skill.py` locale ha SHA256
`8496d0d8b449d64c21b42a9aab3b13fc8a813a430c0695ffd84ad75bb1da7942`, che coincide
con il campo `renderer_sha256` **inciso nel manifest del render del 13 agosto**,
prodotto mesi prima di questa story e da un processo che non la conosceva.
L'artefatto preesistente del progetto testimonia che l'helper vendorato è lo
stesso che ha renderizzato questo progetto.

**Limite dichiarato:** la verifica è contro la cache locale del plugin ufficiale,
non contro un tarball npm firmato o un tag git. Il testimone riduce, non elimina,
questa esposizione. Registrato in `scripts.pin.json` sotto `known_limitation`.

---

## 3. Prova runtime

### `bmad-build` render: PASS

Comando esatto di `bmad-build/SKILL.md:9`, con l'helper vendorato:

    → EXIT=0
    stdout: read and follow …/_bmad/render/bmad-build/kirchhoff-d07b09e6efac/149e1b7f45bfdc0ec5d0/workflow.md

### Render deterministico: PROVATO

La directory di controprova era stata spostata fuori dal repo **prima** di
eseguire il comando vero. Il comando vero l'ha rigenerata, e `diff -r` fra le
due dà **identità completa**. Il render è cache riproducibile, non evidence: la
decisione di non versionarlo è corretta e ora è applicata dal `.gitignore`
upstream.

### `AGENTS.md` nei persistent facts: PRESENTE

`workflow.md:50` → `- file:{project-root}/AGENTS.md`

### Implementatore a contesto fresco: INVOCABILE ed EFFICACE

Processo `claude -p` separato — `claude-sonnet-5`, effort `low`, tools
`Read Glob Grep`, budget 1 USD — nessun contesto conversazionale. Gli è stato
dato lo Step 2 renderizzato e quattro domande i cui fatti stanno **solo** in
`AGENTS.md`. Risposte testuali:

> 1. Kirchhoff è il motore; CircuitCheck è il prodotto.
> 2. `uv run --with pytest --with pytest-cov python -m pytest tests`. L'invocazione apparentemente ovvia `uv run python -m pytest` esce 1 con «No module named pytest».
> 3. `reference-set/holdout/` — perché leggerlo durante lo sviluppo invalida ogni misura successiva.
> 4. Kirchhoff non importa un simulatore, una memoria studente o una shell applicativa.

**Quattro su quattro, esatte.** La seconda è il canary più forte: quel caveat è
un difetto misurato che non esiste in nessun'altra fonte del repo, stringa
d'errore compresa.

### Revisore fresco: INVOCABILE

Secondo processo `claude -p` — **`claude-fable-5`**, effort `high` — che ha
ricevuto il diff e il contesto ma **non** il ragionamento dell'implementatore.
Exit 0, dodici rilievi. Questo prova simultaneamente tre cose: il revisore è
invocabile, il routing su un modello diverso funziona, e il confine di processo
è reale.

---

## 4. Rilievi del revisore — verificati, non accettati

| # | Rilievo | Esito | Prova |
|---|---|---|---|
| Baseline di pin non committata | **CONFERMATO** | risolto: `_bmad/scripts.pin.json` |
| Nessun record di versione BMAD nel progetto | **CONFERMATO** | `config.toml` non contiene versione; risolto dal pin file |
| Provenienza verso cache locale, non upstream firmato | **CONFERMATO** | registrato come `known_limitation` |
| Drift check inesistente | **CONFERMATO — differito a 0.2** | è `doctor`, per decisione dell'owner |
| Skew skill↔helper non protetto da hash | **CONFERMATO — rischio reale** | le skill stanno nel plugin, gli helper nel repo; `doctor` deve confrontare anche la versione del plugin, non solo gli hash |
| Procedura di vendoring non riproducibile | **CONFERMATO — differito a 0.2** | il filtro è documentato qui; lo script appartiene a `doctor`/upgrade |
| Solo 5 file: chiusura non verificata | **REFUTATO** | 4 invocati + 1 import = intero `src/scripts/` |
| Bit di esecuzione non preservati | **REFUTATO** | `cp -p`; 755 su `resolve_customization.py` verificato identico |
| Runtime Python non pinnato | **REFUTATO** | PEP-723 inline: `requires-python = ">=3.11"`, applicato da `uv run` |
| Render stale potrebbe essere riusato | **REFUTATO** | hash derivato dal contenuto: `3efdf204…` → `149e1b7f…`. Un render stale vive a un path diverso e non viene mai selezionato |
| Non tutti gli helper esercitati | **CONFERMATO, poi chiuso** | `memlog.py --help` → exit 0. Tutti e cinque ora esercitati |
| Rimedio non committato | **CONFERMATO** | chiuso da questo commit |

---

## 5. Difetto collaterale scoperto (fuori scope di 0.1)

Lo stderr del processo fresco ha rivelato che **cinque regole `Write(...)` in
`.claude/settings.json` sono inefficaci**. Il CLI stesso lo dice:

    Permission allow rule (.claude/settings.json):
    Write(//…/src/**) is not matched by file permission checks —
    only Edit(path) rules are. Use Edit(//…/src/**) instead.

Righe interessate: 20, 21, 22, 23, 32 — coprono `src/`, `tests/`, `scripts/`,
`_bmad-output/` e un documento. Il progetto crede di aver concesso scrittura su
quelle aree; la concessione non ha effetto. Non toccato in questa story:
modificare i permessi non è remediation del runtime BMAD.

---

## 6. Definition of Done

| Criterio | Stato |
|---|---|
| BMAD runtime classification | `MISSING_RUNTIME_HELPERS` → **REMEDIATED** |
| runtime helpers: official, version pinned, hash verified | **SI** — 5/5 byte-identical, `scripts.pin.json` |
| bmad-build render | **PASS** — exit 0 |
| AGENTS.md persistent facts | **PRESENT** e **EFFECTIVE IN FRESH CONTEXT** — 4/4 canary |
| fresh implementer | **INVOCABLE** |
| fresh reviewer | **INVOCABLE** — modello diverso, confine di processo reale |
| ScheduleWakeup | **INVOCABLE** — presente anche in `claude -p` |
| holdout | **UNTOUCHED** — 0 modifiche, deny attivo a `settings.json:31` |
| BMAD state | **COHERENT** — entrambi i resolver exit 0, ledger intatto |
| product code | **UNCHANGED** — 0 modifiche in `src/` e `tests/` |
| test | **245 passati, exit 0, coverage 100%** |

**Story 0.1 = DONE · R1 runtime effectiveness = CLOSED**

---

## 7. Aperto, e a chi appartiene

- **drift check** (`doctor`): confronti versione dichiarata, hash locali,
  **e versione del plugin installato** — quest'ultima non è opzionale, è
  l'unica difesa contro lo skew skill↔helper. → Story 0.2
- **script di vendoring riproducibile** per un bump deliberato → Story 0.2
- **render vecchio `3efdf204…` committato** (13 file tracciati): upstream lo
  escluderebbe. Il `.gitignore` ora impedisce nuove aggiunte ma non lo
  untrackka. Decisione dell'owner.
- **regole `Write(...)` inefficaci** in `.claude/settings.json` → decisione
  dell'owner
