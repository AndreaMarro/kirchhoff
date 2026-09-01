# Stato corrente

## Certificato

- P0 fino a P1-I sono certificati sul baseline storico
  `231c95355336bc983ec14ca5422baaf88f936244`.
- P1-J e' certificato come candidato allo SHA
  `3d83fbc81bae03c11258de0b63d5b505e8b86208`.
- P1-J implementa `ObservationContract`, `ObservationEffect`,
  `RequestLineageStep`, la funzione autorevole `observation_effect` e la
  funzione autorevole `validate_observation_lineage`.
- La preservazione semantica supportata e':
  - `series` + `current` -> `retarget`;
  - `series` + `voltage` -> `blocked`;
  - `parallel` + `voltage` -> `retarget`;
  - `parallel` + `current` -> `blocked`;
  - target non toccato -> `identity`.
- Non sono previsti replan automatici, CAS esterni o dipendenze runtime esterne.

## Certificazione CI P1-J

- Push GitHub Actions `33508516707` e Pull Request GitHub Actions `33508521991`
  verdi.
- Risultato certificato: 1401 passed, 2 skipped, copertura globale 99.34%,
  copertura domain 100%, reference-set 60 / 0 e boundaries CI verdi.

## Futuro

- Oracoli esterni per test e sviluppo, non per la verita' del prodotto.
- Estensione di Observation/ProtectedEntities oltre corrente e tensione.
- Punteggio e ricerca di strategie multi-passo, soltanto con un contratto dedicato.
- Adapter di percezione con validazione e conferma utente.
- Percorsi di prodotto AC e transitori.
