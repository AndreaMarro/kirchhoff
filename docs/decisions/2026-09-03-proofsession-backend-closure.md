# O0 — Backend closure CLOSED, schema v0.2, governance convergence

Data: 2026-09-03. Branch O0: `work/proof-demo-o0-governance` da `aff2409`.
Carve-out owner: sessione O0 con workflow diretto autorizzato (AGENTS.md
prescrive Loop Kirchhoff v3; il loop esiste in `ops/loop/`, non invocato qui
per decisione owner esplicita — registrare, non scegliere in silenzio).

## 1. Decisione semantica (una sola)

```text
Claim.status VERIFIED      = il claim elettrico passa il gate P1-K (invariato)
ProofSession backend       = CLOSED (chiusura pubblicazione backend, ex VERIFIED)
Product Verified           = RISERVATO (badge owner-locked, richiede H5 visuale)
Schema                     = proof-session.v0.2 (v0.1 rifiutato come input)
```

Perche': `VERIFIED` a livello sessione suggeriva il badge prodotto definito
dal piano master ("solo quando tutti i gate passano", incl. round-trip
visuale K-0/AD-5). Tre concetti, tre nomi: confusione meccanicamente
impossibile (`Literal["CLOSED"]` vs `Literal["VERIFIED"]` su tipi diversi).

## 2. Matrice delle autorita'

| Concetto | Autorita' dichiarata | Owner nel codice | Significato corrente | Conflitto? | Azione O0 |
|---|---|---|---|---|---|
| K-0 | costituzione §K-0 (owner-locked) | `docs/02-costituzione-kirchhoff.md:24` | disegno parte della prova | no | invariato |
| AD-5 | spine:167 (8 controlli/nodo, round-trip dentro `publish`) | architettura | gate unico pubblicazione | no | invariato, H5 aperto |
| AD-13 | spine:336 | `domain/refusal.py`, `pipeline/failure.py` | Refusal esito dominio / Failure guasto | no | tassonomia test-pinned |
| AD-17 | spine:390 | `ports/clock.py`, `identity.conia` | orologio/entropia iniettati | no | invariato |
| AD-21 | spine:466 | boundaries gate | 4 rappresentazioni, sessione per riferimento | no | invariato |
| ProofSession schema | questo doc + `domain/proof/session.py` | `domain/proof` | v0.2, chiusura CLOSED | era sovraccarico | migrato qui |
| Claim.status | `domain/truthfulness.py` ClaimStatus | `domain/truthfulness` | VERIFIED elettrico | no | invariato |
| PublicationStatus | `domain/proof/session.py` | `domain/proof` | CLOSED backend | era VERIFIED | migrato qui |
| TruthfulnessGate | `domain/truthfulness.py:139` | dominio | MNA+tableau+compare+verify+oracolo+unita' | no | invariato |
| CertifiedDidacticRun | `domain/didactic/orchestrate.py:28` | dominio | autorita' didattica | no | invariato |
| CircuitStateRegistry | `pipeline/state_registry.py:94` | pipeline | legami canonici ir_ | no | invariato |
| render/step/compose.py | AD-10/AD-22 | `render/step` | `componi` chiama `transform()` riga 77 | SI (doppia autorita') | REGISTRATO, non fixato (H5) |

## 3. Discrepanza metriche 1732 vs 1730 (causa radice, alta confidenza)

Osservazione: locale 1732 passed/99.55%, remoto 1730+2 skipped/99.44%,
stesso SHA `aff2409`, domain 100% entrambi.
Ipotesi scartate: versioni dipendenze (env A replica CI: pytest 9.1.1,
pytest-cov 7.1.0, coverage 7.16.0 → 1732 passed), collection (1732 nodi
identici A/B), ordine/invocazione.
Causa: due skip condizionali d'ambiente, provati per meccanismo +
falsificazione (`HOME` svuotata → skip esatto remoto):
- `test_la_derivazione_coincide_con_quella_di_bmad`: `_sprint_plan()` risolve
  `/Users/andreamarro/.claude/plugins/cache/...` (macchina sviluppatore),
  inesistente sui runner → skip;
- `test_il_pdf_esce_davvero_se_il_browser_c_e`: `_chromium()` cerca solo
  `~/Library/Caches/ms-playwright` (layout macOS) → mai su linux → skip.
Delta copertura 99.55→99.44 = due corpi test non eseguiti. Nessuna differenza
di sorgente. Residuo: lookup chromium solo-macOS = wart P2 portabilita'
(non O0, non H3).

## 4. Ambienti misurati

| | Env A (pip, semantica CI) | Env B (uv.lock frozen) | Remoto linux |
|---|---|---|---|
| python | 3.12.13 | 3.12.12 | 3.12.14 |
| pytest / coverage | 9.1.1 / 7.16.0 | 9.1.1 / 7.15.4 | 9.1.1 / 7.16.0 |
| collected | 1732 | 1732 identici | 1732 (1730+2) |
| esito | 1732 passed, 99.55% | 1732 passed, 99.55% | 1730+2 skip, 99.44% |
| domain/boundaries | 100% / PASS | 100% / PASS | 100% / PASS |

CI migrabile a lock frozen: PROVATO (commit 2).

## 5. Gerarchia delle fonti (anti-drift)

```text
costituzione owner-locked / AD  (autorita')
  ↓
codice eseguibile + test        (verita' corrente)
  ↓
docs/current-state.md           (descrizione corrente)
  ↓
receipt PR / evidenza storica   (cosa accadde, non cosa esiste)
```

Prosa PR = coordinamento, non autorita'. Messaggi commit = evidenza, non
database di copertura. Output CI = autorevole per cio' che quella run misuro'.
Distinzioni: consistenza strutturale != integrita' != autenticita' storica;
CI verification != self-review != AI review != independent review.

## 6. Stato review

CI verification: push+PR verdi su SHA esatto. Self-review: audit avversariale
de6bb6c...aff2409 (nessun P0 oltre i noti registrati). AI review: CodeRabbit
skipped (draft) = NON ESEGUITA. Independent review: NESSUNA sottomessa =
NOT SATISFIED. Nessun merge in questa sessione.

## 7. Debiti registrati (non fixati qui)

- `VISUAL_SINGLE_SEMANTIC_TRUTH = OPEN`: `render/step/compose.py:77`
  `componi` riesegue `transform()` invece di proiettare TransformExecution
  certificata. Target H5: TransformExecution → proiezione → patch/overlay/SVG.
- Application service mancante: nessuna radice prodotto possiede
  orchestrate→Refusal→registro→clock/entropia→build metadata→compose→live
  validation restituendo `ProofSession | Refusal | Failure`. Proposta minima
  (next gate): `pipeline/publish.py::publish_didactic_session(ir, request,
  *, state_ids, instant_ms, entropy, document_profile, source_sha, detail)`
  pura rispetto I/O (clock/entropia/metadati iniettati), mai render/serialize.
- `ProofSession.__post_init__`: 45 statement, 51 nodi di branch. Proposta next:
  singolo gate pubblico + validatori puri (`_validate_identity`, `_versions`,
  `_provenance`, `_requests`, `_state_chain`, `_steps`, `_lineage`,
  `_analytical_chain`, `_final_solution`, `_final_claim`), zero cambio semantico.
- Fixture testuali triplicate (`_kwargs_d1` in 3 file + ponte sintetico in 2):
  convergere dopo il refactor sopra, non prima.
- Contesto generato stale (AGENTS.md blocco gestito, NO edit a mano, NO path
  di rigenerazione trovato): dichiara repo "privato" (e' PUBLIC) e sei
  prefissi (sono sette). Debito di freschezza registrato.
- PR #8 body stale (numeri H2, date 2026-09-04 errate — commit tutti 2026-09-03,
  "Refusal stays Refusal" fuorviante): aggiornato in coda a O0.
- D2-D8, wire canonico, manifest integrita': aperti, fuori scope O0.

## 8. Falsificabilita' O0

`tests/test_proof_durable_authority.py::test_o0_*` (7): VERIFIED respinto,
v0.1 respinto, Claim VERIFIED invariato, compose emette CLOSED, D1 3/80 A +
Claim VERIFIED + CLOSED, ponte CLOSED live+durevole, tassonomia invariata.
Ogni discriminante osservato fallire (RED) prima del fix, tranne la
tassonomia (caratterizzazione intenzionale).
