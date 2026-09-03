# Stato corrente

## Certificato

- P0 fino a P1-I sono certificati sul baseline storico
  `231c95355336bc983ec14ca5422baaf88f936244`.
- P1-J e' certificato e merged nello storico che precede il baseline P1-K.
- P1-J implementa `ObservationContract`, `ObservationEffect`,
  `RequestLineageStep`, la funzione autorevole `observation_effect` e la
  funzione autorevole `validate_observation_lineage`.
- La preservazione semantica supportata e':
  - `series` + `current` -> `retarget`;
  - `series` + `voltage` -> `blocked`;
  - `parallel` + `voltage` -> `retarget`;
  - `parallel` + `current` -> `blocked`;
  - target non toccato -> `identity`.
- P1-K e' certificato e merged nel baseline
  `770e529fbd6d379b342b3d04ef126b20f1ea62e3`.

## P1-L certified and merged

- P1-L e' merged nel baseline certificato
  `98f73f1184f34f50e030372efaa2b7d91e678cce`. Aggiunge l'orchestrazione deterministica di replan: il planner sceglie un
  piano al singolo stato, ogni trasformazione resta l'esecuzione di un solo piano
  fornito, e l'orchestratore ripianifica soltanto dopo il suo esito certificato.
- La lineage autorevole della Request resta P1-J: id e quantity non cambiano, e
  soltanto il target puo' essere retargettato dall'effetto osservativo certificato.
- Il solo Claim numerico finale resta il `resolved_quantity` verificato dal
  `TruthfulnessGate` P1-K; l'orchestrazione espone una trace, non crea un Claim
  composto o propagato.
- Non e' dichiarata alcuna ottimalita' didattica globale, non esiste uno
  `StrategyScore`, ne' ricerca di strategie, CAS esterni o dipendenze runtime
  esterne.
- CircuitIR object ↔ state-id registry resta debito residuo: P1-L riceve dal
  chiamante una supply ordinata esplicita di identificatori `ir_` distinti, senza
  coniare o registrare una falsa associazione oggetto↔identificatore. Solo il
  prefisso consumato entra nella trace; il chiamante puo' fornire un limite
  superiore strutturale.
- La prova di certificazione P1-L resta CI/storia Git, non lo SHA di un branch
  candidato. P1-M0 puo' soltanto misurarne il comportamento e non lo modifica.

## P1-M0 candidate

- P1-M0 e' un laboratorio di ricerca in branch: esterni, grafi e renderer possono
  contestare o misurare, ma non possono emettere Claim, VERIFIED o lineage.
- Espone solo `CircuitFeatures` e `StrategyCandidate` puri e descrittivi; non
  introduce `StrategyScore`, ranking di produzione o dipendenze runtime.

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

## P1-K

- P1-J is the certified historical baseline.
- P1-K owns the resolved_quantity Claim and TruthfulnessGate.
- A VERIFIED final nodal DC Claim requires:
  - exact MNA
  - independent exact tableau
  - full A/B comparison on every branch voltage/current
  - Fraction-only values
  - verify()
  - exact didactic-vs-oracle agreement
  - correct unit
- TransformExecution remains intermediate.
- AnalyticalStep remains inspectable evidence, not an independently
  certified semantic Claim.
- CircuitIR object ↔ proof_node binding remains residual debt.
- No external CAS or new runtime dependency.
- Certification evidence is recorded in GitHub Actions / git history,
  rather than embedding a self-invalidating branch SHA here.
