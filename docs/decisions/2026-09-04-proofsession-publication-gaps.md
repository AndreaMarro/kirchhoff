# H1.5 — Publication contract gap matrix + closure decisions

Data: 2026-09-04. Branch `work/proof-demo-0.1` (dopo merge `main@de6bb6c`).
Ipotesi di partenza: una `ProofSession` costruibile non e' ancora pubblicabile.
Ogni riga chiude con RESOLVED, DEFERRED WITH EXPLICIT CONTRACT o OUT OF SCOPE.

## Matrice

| # | Concern | Produttore autorevole | Valore/artefatto | Forma di identita' | Store/registro | Rappresentazione in sessione v0.1 | Validatore di pubblicazione | Stato |
|---|---|---|---|---|---|---|---|---|
| 1 | circuito iniziale | orchestrate (`initial_ir`) | IR | state ref `ir_` | CircuitStateRegistry | `initial_state_ref` + `state_refs[0]` | resolve == `run.initial_ir` | RESOLVED |
| 2 | circuito finale operativo | orchestrate (`final_ir`) | IR | state ref `ir_` | registry | `final_state_ref` = `state_refs[-1]` | resolve == `run.final_ir` | RESOLVED |
| 3 | `after` letterale delle transform | transform engine (`execution.after`) | IR intermedio | evidence ref `ir_` (supply del chiamante) | registry via `componi_registro` | NON nominato in v0.1 (nessun ref fantasma) | binding obbligatorio quando distinto dallo stato operativo | DEFERRED WITH EXPLICIT CONTRACT |
| 4 | risultato di transform | transform engine | TransformResult | nessuna (per valore nell'execution) | nessuno (cfr. deferred-work §9) | `operation` + `effect` + `lineage` proiettati | identita' `is` con gli oggetti della run | RESOLVED |
| 5 | proof edge | nessun builder nel percorso prodotto | — | — | — | nessuno | — | DEFERRED (richiede `lay_`+`patch_`, traccia visuale H5) |
| 6 | proof graph | — | — | — | — | nessuno; schema chiuso (kwarg extra = TypeError) | nessun claim di risolvibilita' | DEFERRED WITH EXPLICIT CONTRACT |
| 7 | layout per stato | render/layout (solo curati) | — | — | — | nessuno | — | OUT OF SCOPE backend 0.1 (H5) |
| 8 | layout patch per arco | PatchStore | — | — | — | nessuno | — | OUT OF SCOPE backend 0.1 (H5) |
| 9 | didactic plan | `pianifica` | DidacticPlan | nessuna (senza id) | nessuno | non nominato; la run prova da se' la canonicita' (`_require_canonical_plan`) | run autorevole | DEFERRED (un plan ref richiede identita' dei piani) |
| 10 | derivation state | motore analitico | DerivationState | D-id locali (`D0`…) esplicitamente NON globali | nessuno (in-run, autorevole viva) | `derivation_before/after` come citazioni | catena == passi nodali della run | RESOLVED (via run viva; store durevole differito, stessa ragione di deferred-work §9) |
| 11 | analytical step | execute nodale | AnalyticalStep | D-id locali | nessuno | `kind` + derivation refs | uguaglianza con `final_execution.execution.steps` | RESOLVED |
| 12 | soluzione finale | solve/resolve | ResolvedQuantity | nessuna | nessuno | via `final_request` + subjects del Claim | tie del Claim + E2E H2 (3/80 A) | RESOLVED |
| 13 | Claim finale | truthfulness_gate | Claim | nessuna (senza id proprio) | nessuno | per valore + tie di identita' `is` | `is run.final_execution.claim` | RESOLVED |
| 14 | autorita' del verificatore | costanti truthfulness | VERIFIER_ID/VERSION | — | — | dentro il Claim | tie del Claim (niente secondo controllo) | RESOLVED |
| 15 | source SHA | checkout git (chiamante) | SHA-40 hex | — | — | `provenance.source_sha` | forma 40-hex | RESOLVED |
| 16 | schema version | session.py | costante | — | — | `schema_version` | uguaglianza | RESOLVED |
| 17 | session occurrence ID | compositore (H2) via `conia` | ULID | **`sess_` (nuovo genere, estensione owner-level, vedi sotto)** | — | `session_id` | `verifica(..., "sess")` nel costruttore | RESOLVED |
| 18 | semantic content identity | pins autorevoli | — | — | — | `SessionVersions` ridotta al vero | uguaglianza con l'autorita' | RESOLVED (hash H3) |
| 19 | document profile | dichiarazione del chiamante | token | — | — | `document_profile` non vuoto | forma (dichiarato, onesto) | RESOLVED |

## Decisioni di chiusura

### D-H1.5-1 — Identita' di sessione: nuovo genere `sess_`

`sol_` nel vocabolario chiuso non e' designato per la sessione: nello spine
e' il `Published` scritto da `solve`, entita' che nell'albero corrente non
esiste in quella forma e che comunque non e' la sessione; riusarlo solo
perche' esiste e' l'abuso che il prompt vieta. La proposta `review-avversario`
(`ProofSession: nessuno, e' una proiezione`) nega persino il writer, ma la
spec 6.1 approvata richiede `session_id`: serve un genere reale.
`SESSION_ID_KIND = sess` come estensione Consistency-Conventions con test e
nota di migrazione (il test che pinna i sei generi viene aggiornato
deliberatamente, non indebolito: il test derivato `get_args` resta a guardia
della fonte singola). Fixture opache tipo `sessione-d1-prova-001` restano
valide solo come stringhe qualsiasi: la pubblicazione le respinge.

### D-H1.5-2 — Version pinning: solo autorita', il resto si rimuove

Nessuna release autorevole esiste a runtime per core/planner-impl/catalog/
layout/renderer (`kirchhoff/__init__.py` e' vuoto, nessuna costante nel
codice). I cinque semver di H1 erano inventabili: rimossi dallo schema.
`SessionVersions` v0.1 = `planner_schema_version` (== PLAN_SCHEMA_VERSION),
`curriculum_profile` (== PROFILE), `document_profile` (token dichiarato).
Il modello rifiuta per uguaglianza, non per form
```

...[truncated 2085 chars]