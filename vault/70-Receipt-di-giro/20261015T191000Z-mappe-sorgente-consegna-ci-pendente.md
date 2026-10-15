---
storia: mappe-sorgente-consegna-ci-pendente
istante: 20261015T191000Z
sha: 25702c19c553aa7b2dc7bcee8a73a8fb74739a97
ramo: codex/source-map-boundary-ci-20261015
esito: differito
tipo: receipt-di-giro
---

# Giro 20261015T191000Z — mappe-sorgente-consegna-ci-pendente

> Questa nota registra MISURE, non giudizi. Un giudizio di modello che
> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha
> verificato.

## Misure agli oracoli

| grandezza | valore |
|---|---|
| `test_passati` | 363 |
| `test_falliti` | 0 |
| `recinti` | PASS |
| `verde` | False |

## Esito: differito

## Revisioni

- Review separata del sorgente: APPROVE_SOURCE_FOR_LOCAL_COMMIT_AND_DRAFT_CI_ONLY; non è ancora gate finale su candidate SHA.

## Archi

- [[00-INDICE]]

## Ambito e prove

Base main e1375fb; HEAD di osservazione 25702c1. Otto casi:6 RED di rifiuto e2 sani PASS prima del lock, poi8 GREEN. Build, confini e923fileHTTP PASS; npm audit exit1, debito residuo esplicito. CI del candidato e integrazione PENDING. Nessun terzo full browser locale. Vedere `docs/ops/CONSEGNA-2026-10-15.md` e `docs/web-source-map-boundary.md`. Il precedente esito differito resta storico.
