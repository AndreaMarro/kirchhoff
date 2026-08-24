---
title: 'Audit dei cinque recinti di AD-21 v2'
type: 'audit'
created: '2026-08-24'
baseline_commit: 'c22a7be'
---

# I cinque recinti richiesti

AD-21 v2, tabella «I recinti, per nome»:

| # | Freccia vietata | Ordinato da |
|---|---|---|
| 1 | `domain/` → qualunque cosa fuori da `domain/` | AD-1, paradigma |
| 2 | `domain/` → `render/` | AD-18, AD-21 |
| 3 | `domain/` → `perception/` | AD-24 |
| 4 | `domain/` ∪ `render/` → `adapters/` | AD-27 |
| 5 | qualunque cosa fuori da `corpus/` → il filesystem del corpus | AD-25 |
| **6** | **braccio 0 → `LayoutIR` di `Cₖ`** (parametro, `ctx` o lookup) | **CV5, aggiunto il 24/08/2026** |

> **Correzione del 24/08/2026.** AD-21 ne elenca cinque, ma CV5 di `review-continuita-visuale.md`
> ne richiede un sesto e ne spiega il costo: un braccio 0 che abbia visto il layout precedente e'
> «piu' continuo del dovuto», il divario 0 ↔ A si assottiglia e **il kill criterion uccide un
> prodotto valido**. Vedi `matrice-impatto-cv1-cv6-su-delta.md`.

# Cosa è implementato davvero

`scripts/check_boundaries.py` dichiara `RECINTO = "domain"` e scandisce **solo** `src/kirchhoff/domain/`.
`_fuori_dal_recinto` respinge ogni import del progetto che non stia sotto `domain/`.

Ne segue una lettura più precisa del «uno su cinque» scritto in AD-21:

| # | Stato | Perché |
|---|---|---|
| 1 | ✅ **implementato e testato** | `test_confini.py`, 10 test, incluso il caso «radice sbagliata non dichiara tutto pulito» |
| 2 | ✅ **coperto per implicazione** | `render/` è fuori da `domain/`, quindi il recinto 1 lo vieta già |
| 3 | ✅ **coperto per implicazione** | idem per `perception/` (che peraltro non esiste ancora come pacchetto) |
| 4 | ⚠️ **metà** | la metà `domain/ → adapters/` è coperta dal recinto 1. La metà **`render/ → adapters/` non è controllata**: lo script non scandisce `render/` |
| 5 | ❌ **assente** | nessun controllo sull'accesso al filesystem del corpus. `corpus/` non esiste ancora |

Il gate resta onesto — non dichiara di controllare ciò che non controlla — ma AD-21 v2 pretende
cinque frecce e il codice ne verifica una sorgente sola.

# Impatto sul percorso in esecuzione

| Storia | Pacchetti toccati | Recinto che li protegge | Sbloccata? |
|---|---|---|---|
| **2.4** validazione elettrica | `domain/validate`, `domain/refusal` | recinto 1, implementato e testato | ✅ sì |
| **2.6** catalogo Trasformazioni | `domain/transform`, `domain/transform/check` | recinto 1, implementato e testato | ✅ sì |
| *prima trasformazione fino al renderer* | `render/layout`, `render/` | **recinto 4 metà mancante** | ⚠️ chiudere il recinto 4 prima di scrivere `render/` |

Conclusione: **2.4 e 2.6 vivono entrambe dentro l'unico recinto già verificato.** I recinti mancanti
mordono quando nasce `render/` — cioè al passo «una trasformazione end-to-end fino al rendering»,
non prima.

# Story 2.1 — `done` rispetto a v1, non a v2

La Storia 2.1 «struttura del progetto con confini di dipendenza verificati» è `done`, ed **era
legittimamente done rispetto al contratto v1**, che chiedeva un recinto. AD-21 v2 alza l'asticella a
cinque. Il vocabolario di stato di BMAD (`backlog · ready-for-dev · in-progress · review · done`)
non ha uno stato «riaperta da un emendamento».

Scelta: **non si riscrive la storia.** `2.1` resta `done` — cancellarlo perderebbe l'evidenza che il
lavoro fu fatto e superò i suoi criteri. Il debito nasce come **storia distinta di superamento**,
`2-1b-recinti-ad-21-v2`, in `backlog`, che nomina la 2.1 come predecessore.
