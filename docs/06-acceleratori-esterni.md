# Acceleratori esterni: confini e ruoli

Questo documento registra opzioni di sviluppo e verifica. Nessuna di esse e' una
dipendenza runtime di Kirchhoff o una fonte di verita' del prodotto.

| Strumento | Ruolo eventuale | Confine non negoziabile |
|---|---|---|
| Lcapy | Oracolo esterno per test e sviluppo | Non decide la verita' del prodotto. |
| egglog | Acceleratore opzionale di equality saturation per ExprIR | Non e' un solver di verita' per CircuitIR. |
| Centaur | Ispirazione architetturale per semantica query-aware | Nessun codice copiato; licenza trattata in modo conservativo. |
| NetworkX | GraphView effimera futura | Non entra nel dominio o nel runtime del prodotto. |
| Schemdraw | Renderer secondario o fixture sintetiche | Non sostituisce il renderer semantico. |
| PySpice | Oracolo GPL esterno, solo con isolamento di processo e decisione di licenza | Non e' una dipendenza del prodotto. |
| Progetti vision | Adapter di percezione | CandidateCircuitIR passa sempre validazione Kirchhoff e conferma utente. |

## Decisione di riproducibilita'

**Si mantiene il modello attuale.** `pyproject.toml` dichiara nessuna dipendenza
runtime; gli strumenti di test sono optional development dependencies e la CI
installa `.[dev]`. Non viene aggiunto un lockfile o un package manager alternativo
in questo checkpoint: P1-J non introduce nuove dipendenze e non giustifica una
migrazione di packaging.
