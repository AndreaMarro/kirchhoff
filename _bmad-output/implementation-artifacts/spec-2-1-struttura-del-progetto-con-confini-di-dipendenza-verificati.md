---
title: 'Storia 2.1 — Struttura del progetto con confini di dipendenza verificati'
type: 'feature'
created: '2026-08-13'
status: 'done'
baseline_commit: 'NO_VCS'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** La regola di dipendenza dello spine — `domain/` non importa nulla del progetto fuori
da sé — oggi è verificata a mano, con un `grep` che il loop esegue perché se lo ricorda. Un `grep`
non vede `import kirchhoff.adapters as x`, non vede `from kirchhoff import ports`, e soprattutto non
gira quando nessuno lo lancia. Parallelamente non esiste alcuna configurazione: nessun punto in cui
un valore d'ambiente sbagliato fermi l'avvio invece di essere assorbito.

**Approach:** Due gate eseguibili. Il primo legge l'albero sintattico di ogni modulo sotto `domain/`
e nomina file, riga e import quando qualcuno esce dal recinto — la sintassi, non una stringa. Il
secondo valida la configurazione contro uno schema esplicito e rifiuta l'avvio nominando la
variabile e il motivo, e ne approfitta per rendere eseguibili tre vincoli che finora vivevano solo
nella prosa: `K ≥ 3` passi di estrazione, immagini cancellate entro 72 ore, dati in Unione Europea.

## Boundaries & Constraints

**Always:**
- Il controllo dei confini analizza l'albero sintattico, non il testo: `import a.b as c`,
  `from a import b` e le forme relative sono tutte viste.
- Un fallimento nomina il file, la riga e l'import: un controllo che dice solo "fallito" costringe
  a rifare da capo l'indagine che ha già fatto.
- La configurazione non ha valori di ripiego silenziosi per ciò che è obbligatorio. Un valore
  assente o fuori dominio ferma l'avvio.
- `K ≥ 3` è un limite imposto dal codice, non una raccomandazione (AD-12, D4).
- Le sette directory dello spine esistono e sono pacchetti importabili.

**Ask First:**
- Riorganizzare `domain/` nei sotto-pacchetti dello spine (`ir/`, `validate/`, `transform/`,
  `solve/`, `verify/`): li creano le storie che li abitano, non questa.
- Aggiungere una variabile di configurazione che non discenda da una decisione già scritta.

**Never:**
- Un controllo dei confini basato su espressioni regolari.
- Un valore di configurazione obbligatorio con un default che permette di partire comunque.
- Adapter concreti: `ports/` definisce interfacce, e questa storia non ne implementa nessuna.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Albero pulito | `domain/` che importa solo sé stesso e la libreria standard | il controllo esce 0 e non nomina nulla | — |
| Import verso `adapters/` o `ports/` | un modulo sotto `domain/` con `from ..ports.clock import ClockPort` | uscita diversa da zero, con file, riga e import nominati | il messaggio identifica il punto esatto |
| Import assoluto travestito | `import kirchhoff.adapters as a` dentro `domain/` | rilevato come il caso relativo | — |
| Configurazione valida | tutte le variabili presenti e nel dominio | oggetto di configurazione congelato | — |
| Variabile obbligatoria assente | ambiente senza `KIRCHHOFF_ENV` | l'avvio fallisce nominando la variabile | mai un valore di ripiego |
| Passi di estrazione sotto tre | `KIRCHHOFF_EXTRACTION_PASSES=2` | l'avvio fallisce citando il limite | l'ambiguità si misura su almeno tre pass, o non si misura |
| Vita delle immagini oltre 72 ore | `KIRCHHOFF_IMAGE_TTL_HOURS=96` | l'avvio fallisce | il termine è un obbligo, non una preferenza |
| Regione fuori dall'Unione Europea | `KIRCHHOFF_DATA_REGION=us-east-1` | l'avvio fallisce nominando la regione | — |
| Valore non numerico dove serve un intero | `KIRCHHOFF_EXTRACTION_PASSES=tre` | l'avvio fallisce dicendo cosa si aspettava | — |

</frozen-after-approval>

## Code Map

- `src/kirchhoff/` — le sette directory dello spine esistono già come pacchetti
  (`domain/`, `ports/`, `adapters/`, `pipeline/`, `api/`, `render/`, `eval/`); `ports/`,
  `adapters/`, `api/`, `pipeline/`, `render/` hanno `__init__.py` vuoti.
- `src/kirchhoff/domain/` — `exact.py`, `ir.py`, `mna.py`, `transient.py`: oggi importano solo la
  libreria standard e sé stessi. Sono l'insieme che il controllo deve dichiarare pulito.
- `scripts/check_domain_coverage.py` — il modello del gate già esistente: script autonomo, uscita
  diversa da zero, messaggio che nomina la causa. Il nuovo controllo lo affianca.
- `docs/00-fonte-piano-kirchhoff.md` — D4 (K ≥ 3 pass), D10 e FR-30 (72 ore), NFR-14 (dati in UE):
  le tre soglie che la configurazione rende eseguibili.

## Tasks & Acceptance

**Execution:**
- [x] `src/kirchhoff/ports/clock.py` — definire `ClockPort` come protocollo (AD-17: un solo
  orologio, iniettato). Serve anche a dare al controllo dei confini qualcosa di vero da proteggere.
- [x] `src/kirchhoff/config.py` — schema esplicito, lettura dall'ambiente, oggetto congelato;
  `ConfigError` che nomina variabile e motivo. Le tre soglie di D4, FR-30 e NFR-14 diventano
  condizioni di avvio.
- [x] `scripts/check_boundaries.py` — analisi dell'albero sintattico di ogni modulo sotto
  `domain/`, risoluzione degli import relativi e assoluti, uscita diversa da zero con file, riga e
  import.
- [x] `tests/test_config.py`, `tests/test_confini.py` — una riga della matrice per test, incluso il
  caso positivo su cui il controllo deve tacere.

**Mappa criterio di accettazione → test** (voce d'azione 3 della retrospettiva di Epic 1):

| Criterio | Test |
|---|---|
| ogni directory dello spine esiste ed è un pacchetto inizializzato | `test_confini.py::test_le_sette_directory_dello_spine_sono_pacchetti` |
| la configurazione valida all'avvio con schema | `test_config.py::test_configurazione_valida` |
| una configurazione non valida impedisce l'avvio invece di degradare in silenzio | `test_config.py::test_variabile_obbligatoria_assente`, `::test_intero_malformato`, `::test_meno_di_tre_pass_rifiutati`, `::test_ttl_oltre_settantadue_ore_rifiutato`, `::test_regione_fuori_unione_europea_rifiutata` |
| un modulo sotto `domain/` che importa `adapters/` o `ports/` fa fallire il controllo | `test_confini.py::test_import_relativo_verso_ports_rilevato`, `::test_import_assoluto_verso_adapters_rilevato` |
| il controllo nomina file e import | `test_confini.py::test_il_messaggio_nomina_file_riga_e_import` |
| il fallimento blocca la fusione | `test_confini.py::test_il_dominio_reale_e_pulito` (il controllo gira nella suite: un'infrazione fa fallire i test) |

**Acceptance Criteria:**
- Dato l'albero sorgente attuale, quando il controllo dei confini gira, allora esce 0 e la suite
  resta verde.
- Dato un modulo sotto `domain/` che importa `ports/` o `adapters/` in una qualunque forma
  sintattica, quando il controllo gira, allora esce diverso da zero e il messaggio contiene il file,
  la riga e l'import.
- Data una configurazione con meno di tre passi di estrazione, quando si tenta l'avvio, allora
  fallisce citando il limite invece di procedere con due.

## Verification

**Commands:**
- `uv run --with pytest --with pytest-cov python -m pytest` — atteso: verde, copertura ≥ 95%.
- `uv run python scripts/check_domain_coverage.py` — atteso: uscita 0.
- `uv run python scripts/check_boundaries.py` — atteso: uscita 0, nessuna violazione.
