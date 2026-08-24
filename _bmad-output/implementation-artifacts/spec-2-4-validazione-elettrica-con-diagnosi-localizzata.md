---
title: 'Storia 2.4 — Validazione elettrica con diagnosi localizzata'
type: 'feature'
created: '2026-08-24'
baseline_commit: 'c22a7be'
review_loop_iteration: 0
context: ['FR-4', 'AD-13', 'AD-19']
status: 'done'
---

## Intent

**Problem:** non esiste alcun gate fra l'IR e la risoluzione. Un IR con un nodo scollegato, un ramo
aperto o una maglia di soli generatori arriva al solver, che produce una matrice singolare e un
messaggio come «nessun pivot utilizzabile alla riga 3» — vero e inutilizzabile. FR-4 chiede che il
fallimento **nomini l'elemento coinvolto** e che la diagnosi sia riusabile come testo di una Domanda
mirata senza riscrittura manuale.

**Approach:** una batteria di controlli deterministici puri su `domain/`, in ordine fisso, che
restituisce un `Validated` oppure un `Refusal`. `Refusal` nasce qui come tipo di dominio: **non è
un'eccezione** (AD-13 lo tiene su tipo e canale diversi da `Failure`), la sua `cause` viene da
un'enumerazione chiusa e il payload porta sempre `subject` (AD-19).

Terza categoria oltre a promosso/rifiutato: il **sospetto**, che non blocca. Un valore resistivo
fuori dalle serie E12/E24 in un esercizio manoscritto è quasi sempre un errore di lettura, ma «quasi
sempre» non è «sempre»: bloccare sarebbe arroganza, tacere complicità. Diventa Ambiguità residua.

## Boundaries & Constraints

**Always:**
- `domain/validate` e `domain/refusal` restano dentro il recinto 1 di AD-21, l'unico oggi verificato.
- Puri: nessuna I/O, nessun orologio, nessuna casualità.
- Ordine dei controlli fisso; il primo che fallisce vince; l'esito è deterministico.
- Ogni `Refusal` nomina un nodo, un componente o una richiesta.

**Never:**
- Diagnosticare il **procedimento dello studente**. Quello confronterà `StudentSolutionIR` con il
  dominio verificato ed è un livello superiore: infilarlo qui sporcherebbe il confine.
- Sollevare `Refusal` come eccezione.
- Bloccare su un sospetto.

## I/O & Edge-Case Matrix

| Scenario | Esito | Soggetto |
|---|---|---|
| grafo non connesso | `Refusal(topology)` | il nodo isolato |
| nodo di grado 1 | `Refusal(topology)` | il nodo, con il ramo nominato in diagnosi |
| maglia di soli generatori di tensione | `Refusal(topology)` | il componente che la chiude |
| nodo di soli generatori di corrente con somma ≠ 0 | `Refusal(topology)` | il nodo |
| nodo di soli generatori di corrente con somma = 0 | **promosso** | — |
| unità incoerente col tipo | `Refusal(units)` | il componente |
| grandezza richiesta su componente inesistente | `Refusal(unsolvable)` | la richiesta |
| resistore fuori E12/E24, sorgente immagine | promosso **con sospetto** | il componente |
| resistore fuori E12/E24, sorgente netlist | promosso, nessun sospetto | — |
| IR valido | `Validated` | — |

## Code Map

- `src/kirchhoff/domain/refusal.py` — `Refusal`, `Cause`, `SubjectKind`, guardie del costruttore.
- `src/kirchhoff/domain/validate.py` — `validate`, `Validated`, `Suspicion`, i sei controlli.
- `tests/test_validate.py` — 27 test.

## Mappa criterio di accettazione → test

| Criterio | Test |
|---|---|
| grafo non connesso, grado 1, maglia di generatori, taglio di correnti, unità, richiesta inesistente → `Refusal` con causa chiusa e `subject` | `TestTopologia` (4 test), `TestUnita::test_il_gate_ha_comunque_il_proprio_controllo`, `TestGrandezzeRichieste::test_il_controllo_del_gate_scatta_su_un_ir_costruito_di_lato` |
| nessun IR raggiunge lo stato confermato senza superare la validazione | `TestPromozione::test_un_ir_valido_e_promosso` (unico ramo che restituisce `Validated`) |
| valore fuori E12/E24 in manoscritto segnalato senza bloccare, disponibile a valle | `TestSospetti` (3 test) + `TestSerieSottoLaDecade` (2) |
| IR valido promosso, **nessun falso positivo sul gold set di sviluppo** | `TestNessunFalsoPositivo::test_l_intero_split_dev_e_promosso` — 36 casi, zero rifiuti |
| enumerazione chiusa e soggetto obbligatorio | `TestRefusalSiDifende` (4 test) |

## Verification

```
uv run --with pytest --with pytest-cov python -m pytest tests
  → 218 passed · Total coverage 100.00%

uv run python scripts/check_domain_coverage.py     → exit 0 · "domain/ al 100%"
uv run python scripts/check_boundaries.py          → exit 0
uv run kirchhoff-eval report --root reference-set --split dev
  → {"ok": true, "total": 36, "VSR": 1.0, "SER": 0.0}
```

## Aperto, dichiarato

- Il taglio di soli generatori di corrente è controllato **sul singolo nodo**, non nel caso
  generale a più nodi. Il caso generale richiede l'enumerazione dei tagli ed è sproporzionato qui.
- Il controllo dei **segni**, citato nel glossario del PRD, non è implementato: la Storia 2.4 non lo
  elenca fra i propri criteri e non ho voluto inventarne la semantica.
