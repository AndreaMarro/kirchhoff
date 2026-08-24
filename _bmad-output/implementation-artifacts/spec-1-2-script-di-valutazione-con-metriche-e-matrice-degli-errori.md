---
title: 'Storia 1.2 — Script di valutazione: riproducibilità dichiarata e matrice degli errori chiusa'
type: 'feature'
created: '2026-08-13'
status: 'done'
baseline_commit: 'NO_VCS'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Il comando produce le quattro metriche e la ripartizione degli errori, ma il criterio
*"stessi input, stesse metriche"* non è soddisfatto e non è testato: il rapporto contiene
`TTV_p90_s`, che misura l'orologio della macchina e cambia a ogni esecuzione. Un rapporto che non
si può confrontare con quello di ieri non regge la discussione sulla qualità che la storia esiste
per rendere possibile. In più la matrice degli errori non è chiusa: un sistema sotto test che
restituisce un tipo d'errore inventato se lo vede accettare in silenzio, e il rapporto cambia forma
senza che nessuno protesti.

**Approach:** Non nascondere il conflitto fra "riproducibile" e "TTV": dichiararlo. Il rapporto
nomina esplicitamente i campi che dipendono dalla macchina, così che tutto il resto sia
confrontabile riga per riga; e la ripartizione degli errori diventa un'enumerazione chiusa che
rifiuta un tipo sconosciuto invece di aggiungerlo.

## Boundaries & Constraints

**Always:**
- Le metriche che portano una decisione — `VSR`, `SER`, `QPS`, tasso di Rifiuto, conteggi e matrice
  degli errori — sono identiche fra due esecuzioni sugli stessi input.
- Il rapporto continua a dichiarare che la copertura esclude l'estrazione da immagine.
- Il divieto di lettura della parte trattenuta resta com'è: non si tocca.
- Copertura globale ≥ 95%; `domain/` al 100% righe e rami.

**Ask First:**
- Togliere `TTV` dal rapporto: è una delle quattro metriche che la storia richiede, e sparirebbe
  una misura di NFR-1.

**Never:**
- Rendere `TTV` finto-deterministico arrotondandolo: un numero stabile che non misura più il tempo
  è peggio di un numero instabile che lo misura.
- Un tipo d'errore fuori dai cinque previsti accettato in silenzio.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Due esecuzioni sullo stesso insieme | stessa radice, stesso split | ogni campo del rapporto identico, tranne quelli dichiarati dipendenti dalla macchina | — |
| Rapporto letto da chi confronta | un rapporto qualsiasi | nomina i campi non riproducibili, così che il confronto sappia cosa saltare | — |
| Sistema sotto test con tipo d'errore inventato | esito non pubblicato con `error_kind` fuori dai cinque | l'harness fallisce nominando il tipo | errore esplicito, mai una chiave nuova nella matrice |
| Richiesta della parte trattenuta in sviluppo | split `holdout` senza autorizzazione | uscita 2, messaggio esplicito | nessuna metrica compare nell'uscita |

</frozen-after-approval>

## Code Map

- `src/kirchhoff/eval/metrics.py` — `ERROR_KINDS` è la tupla dei cinque tipi; `Report.errors` la
  inizializza con `dict.fromkeys`, ma `run()` fa `rep.errors.get(kind, 0) + 1`, che aggiunge una
  chiave nuova invece di rifiutarla. `Report.as_dict()` emette `TTV_p90_s` accanto alle metriche
  deterministiche senza distinguerle.
- `src/kirchhoff/eval/cli.py` — `cmd_report` stampa `{"ok", "split", **rep.as_dict()}`; il ramo di
  Rifiuto della parte trattenuta stampa solo `ok` ed `errore`, e va tenuto così.
- `tests/test_cli.py` — quattro test sulla superficie del comando; manca quello sulla
  riproducibilità, che è il criterio scoperto.

## Tasks & Acceptance

**Execution:**
- [x] `src/kirchhoff/eval/metrics.py` — dichiarare nel rapporto i campi che dipendono dalla
  macchina, e chiudere la matrice degli errori rifiutando un tipo fuori dai cinque.
- [x] `tests/test_cli.py` — un test per ogni riga della matrice I/O: due esecuzioni confrontate
  campo per campo, la dichiarazione dei campi non riproducibili, il tipo d'errore inventato, e
  l'assenza di qualunque metrica quando la parte trattenuta viene rifiutata.

**Acceptance Criteria:**
- Dato lo stesso insieme di riferimento, quando il comando gira due volte, allora tutti i campi del
  rapporto tranne quelli dichiarati dipendenti dalla macchina sono identici.
- Dato un rapporto, quando lo legge chi confronta due misure, allora sa dall'uscita stessa quali
  campi saltare.
- Dato un sistema sotto test che restituisce un tipo d'errore fuori dai cinque, quando l'harness
  gira, allora fallisce nominandolo invece di allargare la matrice.

## Verification

**Commands:**
- `uv run --with pytest --with pytest-cov python -m pytest` — atteso: verde, copertura ≥ 95%.
- `uv run python scripts/check_domain_coverage.py` — atteso: uscita 0.
- `uv run kirchhoff-eval report --root reference-set --split dev` — atteso: `VSR` 1.0, `SER` 0.0,
  campi non riproducibili dichiarati.
