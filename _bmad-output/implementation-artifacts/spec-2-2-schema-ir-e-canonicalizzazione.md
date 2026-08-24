---
title: 'Storia 2.2 — Schema IR e canonicalizzazione'
type: 'feature'
created: '2026-08-13'
status: 'in-progress'
baseline_commit: 'NO_VCS'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** L'IR porta oggi un numero nudo: `Component.value` è una `Fraction` senza unità, quindi
nulla distingue 10 ohm da 10 farad e nulla impedisce a uno stadio a valle di leggere una capacità
come una resistenza. `ir_version` è `"1.0"`, che non è una versione semantica. Non esiste
provenienza: quando la sorgente sarà un'immagine, nessuno saprà da quale porzione un valore è stato
letto, e la conferma dell'utente non avrà nulla da ancorare. E due IR che descrivono lo stesso
circuito con i componenti elencati in ordine diverso risultano diversi, quindi non sono
confrontabili.

**Approach:** Portare l'unità dentro il tipo, non accanto: una grandezza fisica è una coppia
magnitudine + unità, e l'unità dev'essere quella che il tipo di componente impone. Aggiungere la
provenienza come area normalizzata della sorgente, obbligatoria quando la sorgente è un'immagine e
assente altrove. Rendere `ir_version` semantica e verificata. E dare all'IR una forma canonica che
ordina ciò che è arbitrario — l'elenco dei componenti, l'elenco dei nodi, e i terminali dei bipoli
simmetrici — lasciando intatto ciò che non lo è, cioè l'orientamento di una sorgente.

## Boundaries & Constraints

**Always:**
- Nessun numero nudo nell'IR: ogni valore di componente è magnitudine più unità.
- L'unità è imposta dal tipo: un resistore in farad è respinto dallo schema, non corretto.
- Unità SI internamente; la conversione è cosa del rendering.
- La canonicalizzazione è pura e idempotente: applicarla due volte dà lo stesso risultato.
- I terminali di una sorgente non si riordinano mai: l'ordine è la polarità.
- `domain/ir` diventa il pacchetto previsto dallo spine, non un modulo accanto.
- Aritmetica esatta: la magnitudine resta `Fraction`, la provenienza è in coordinate normalizzate
  esatte.

**Ask First:**
- Estendere la canonicalizzazione all'isomorfismo di grafo, cioè al caso in cui anche i **nomi** dei
  nodi differiscono: il criterio parla di ordine, e il rietichettamento canonico è un problema
  diverso e molto più costoso.

**Never:**
- Un'unità dedotta a runtime da chi legge: se non è nell'IR, non c'è.
- Provenienza inventata per una sorgente che non è un'immagine.
- Riordino dei terminali di un generatore.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Componente ben formato | resistore con 10 ohm | accettato, magnitudine e unità leggibili | — |
| Valore numerico nudo | `Fraction(10)` al posto della grandezza | respinto dallo schema | errore di tipo che nomina il componente |
| Unità incoerente col tipo | condensatore con unità ohm | respinto | il messaggio dice tipo, unità trovata e unità attesa |
| Versione non semantica | `ir_version = "1.0"` | respinta | il messaggio mostra la forma attesa |
| Sorgente immagine senza provenienza | IR con `source_kind` immagine e un componente senza area | respinto nominando il componente | — |
| Provenienza su sorgente non fotografica | IR da netlist con area di provenienza | respinto | una provenienza inventata è peggio di nessuna |
| Area fuori dai limiti | riquadro con lato nullo o oltre il bordo | respinto | — |
| Ordine diverso, stesso circuito | due IR con componenti e nodi elencati in ordine diverso | stessa forma canonica, confronto identico | — |
| Bipolo simmetrico rovesciato | resistore `(A,B)` contro `(B,A)` | stessa forma canonica | — |
| Sorgente rovesciata | generatore `(A,0)` contro `(0,A)` | forme canoniche **diverse** | l'ordine dei terminali è la polarità |
| Canonicalizzazione ripetuta | forma canonica ricanonicalizzata | identica a sé stessa | — |

</frozen-after-approval>

## Code Map

- `src/kirchhoff/domain/ir.py` — da convertire nel pacchetto `domain/ir/` previsto dall'albero
  dello spine. Contiene `Component`, `Request`, `IR`, `ComponentType`, `Quantity`, `POSITIVE_VALUED`
  e la validazione in `__post_init__`.
- `src/kirchhoff/domain/mna.py` — legge `c.value` in `_classify_dc`, `_classify_phasor`,
  `_classify_natural`: ogni lettura diventa lettura della magnitudine.
- `src/kirchhoff/domain/transient.py` — `_substitute` costruisce componenti sostitutivi a valore
  zero: devono nascere con l'unità del tipo che assumono.
- `src/kirchhoff/eval/generator*.py` — tutte le costruzioni di `Component`.
- `src/kirchhoff/eval/reference_set.py` — `to_json`/`from_json` serializzano `value` come frazione
  nuda: devono portare unità, provenienza e origine della sorgente.
- `tests/` — ogni costruzione diretta di `Component` va aggiornata.

## Tasks & Acceptance

**Execution:**
- [ ] `src/kirchhoff/domain/ir/schema.py` — `Magnitude` (magnitudine + unità), `Provenance` (area
  normalizzata), unità attesa per tipo, `source_kind` sull'IR, versione semantica, e la validazione
  che rende impossibile ognuna delle righe negative della matrice.
- [ ] `src/kirchhoff/domain/ir/canonical.py` — forma canonica pura e idempotente.
- [ ] `src/kirchhoff/domain/ir/__init__.py` — riesporta lo schema e la canonicalizzazione.
- [ ] `src/kirchhoff/domain/mna.py`, `transient.py` — leggere la magnitudine invece del numero nudo.
- [ ] `src/kirchhoff/eval/` — generatori e serializzazione allineati al nuovo schema.
- [ ] `tests/test_ir_schema.py`, `tests/test_ir_canonical.py` — una riga della matrice per test.

**Mappa criterio di accettazione → test**

| Criterio | Test |
|---|---|
| `ir_version` semantica | `test_ir_schema.py::test_versione_semantica_richiesta` |
| magnitudine, unità e forma simbolica su ogni componente | `test_ir_schema.py::test_ogni_componente_porta_magnitudine_unita_e_forma_simbolica` |
| provenienza quando la sorgente è un'immagine | `test_ir_schema.py::test_sorgente_immagine_esige_provenienza`, `::test_provenienza_su_sorgente_non_fotografica_respinta` |
| valore numerico senza unità respinto | `test_ir_schema.py::test_valore_nudo_respinto`, `::test_unita_incoerente_col_tipo_respinta` |
| stessa forma canonica per ordini diversi | `test_ir_canonical.py::test_ordine_diverso_stessa_forma_canonica` |
| confronto fra i due identico | `test_ir_canonical.py::test_il_confronto_dopo_la_canonicalizzazione_e_identico` |

**Acceptance Criteria:**
- Dato un IR con un valore privo di unità, quando lo si costruisce, allora lo schema lo respinge
  nominando il componente.
- Dati due IR che descrivono lo stesso circuito con componenti e nodi in ordine diverso, quando si
  canonicalizzano, allora risultano identici.
- Dato un generatore con i terminali invertiti, quando si canonicalizza, allora **non** risulta
  identico all'originale.

## Verification

**Commands:**
- `uv run --with pytest --with pytest-cov python -m pytest` — verde, copertura ≥ 95%.
- `uv run python scripts/check_domain_coverage.py` · `uv run python scripts/check_boundaries.py`
- `uv run kirchhoff-eval build --n 60 --out reference-set` e `report` — SER non sale.
