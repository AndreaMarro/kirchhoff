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

## P1-L candidate

- P1-L aggiunge l'orchestrazione deterministica di replan: il planner sceglie un
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
- P1-L e' merged su `main` via PR #9 (`de6bb6c`): non piu' candidate. Il debito
  registry sopra e' chiuso sul branch prodotto da `pipeline/state_registry.py`
  (`CircuitStateRegistry` canonico, `componi_registro` da soli dati pubblici
  della run) con semantica `proof_node` = stato consumato (G1).

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

## Proof Demo 0.1 (branch `work/proof-demo-0.1`, PR #8 DRAFT)

Stato verificato il 2026-09-04 (locale == remoto prima di ogni gate):

- Base: `main@de6bb6c` (merge PR #9 P1-L). Il branch e' allineato a `main`
  (`behind = 0` dopo merge `--no-ff`).
- `CertifiedDidacticRun` resta l'autorita' didattica; `ProofSession`
  (`domain/proof/session.py`, schema `proof-session.v0.1`) e' la proiezione
  prodotto per riferimento: niente `Any`/dict, niente solve downstream.
- Session identity: genere `sess_` (estensione Consistency-Conventions,
  D-H1.5-1). Versioni solo autorevoli (`planner_schema_version`,
  `curriculum_profile`, `document_profile`); provenance strutturata
  (`producer`, `source_sha` SHA-40, `detail`).
- Pubblicazione: `pipeline/proof_session.validate_publication` lega ogni ref
  alla run autorevole viva (stati via registry, effect/lineage/Claim per
  identita' `is`, derivazioni per uguaglianza). Forged-but-equal non pubblica.
  Rotture -> `Failure`, mai `Refusal`.
- Schema v0.1: prima le trasformazioni, poi l'analitica ancorata allo stato
  finale. ProofGraph/layout/view: differiti con contratto esplicito (niente
  `lay_` nel percorso didattico; traccia visuale H5).
- CoV: session.py 100% linee/rami; proof_session.py 100% linee/rami;
  globale >= 95%; domain 100%; boundaries PASS.
- H2 chiuso: `pipeline/proof_session.compose_proof_session` proietta run +
  registro in sessione pubblicata (stessi oggetti certificati, niente
  ricalcolo; E2E D1 con 3/80 A e Claim autorevole; ponte a zero
  trasformazioni composto). Rotture -> `Failure`; `Refusal` a monte resta
  `Refusal`.
- Non ancora chiusi: serializzazione canonica (H3), corpus D1-D8 (H4, solo D1
  e ponte esercitati finora), product-proof CI, mutation mirata, review
  indipendente. PR #8 resta DRAFT; PR #7 resta research, non toccata.

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
