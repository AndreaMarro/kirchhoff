# Stato corrente

## Legenda

- Le sezioni storiche restano per tracciabilita' e sono marcate STORICO.
- Lo stato corrente sta in "Proof Demo 0.1"; in caso di contraddizione,
  la sezione corrente prevale sulle sezioni storiche.

## Certificato (STORICO)

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

## P1-L (STORICO: merged su `main` via PR #9, `de6bb6c`)

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
- STORICO: il debito registry (supply di `ir_` senza legame oggetto↔identificatore)
  e' chiuso sul branch prodotto da `pipeline/state_registry.py`
  (`CircuitStateRegistry` canonico, `componi_registro` da soli dati pubblici
  della run) con semantica `proof_node` = stato consumato (G1).
- P1-L e' merged su `main` via PR #9 (`de6bb6c`): non piu' candidate.

## Certificazione CI P1-J (STORICO)

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

## Proof Demo / O0 governance

Stato corrente post-merge (O0, vedi decisione
`2026-09-03-proofsession-backend-closure.md`):

- H2.5 / PR #8 e' merged in `main` tramite merge commit
  `26bc00b0ca2ae2d04a53bc0cab6ece87deb03663`. O0 / PR #10 e' il gate
  corrente su `work/proof-demo-o0-governance`.
- `CertifiedDidacticRun` resta l'autorita' didattica; `ProofSession`
  (`domain/proof/session.py`, schema `proof-session.v0.2`) e' la proiezione
  prodotto per riferimento: niente `Any`/dict, niente solve downstream.
- Chiusura backend `CLOSED` (ex `VERIFIED` v0.1): Claim resta `VERIFIED`
  elettrico, Product Verified riservato (K-0/AD-5, H5). Tre nomi distinti.
- Session identity: genere `sess_` (writer unico il compositore).
  Versioni solo autorevoli (`planner_schema_version`, `curriculum_profile`,
  `document_profile` chiuso `student-pdf.v0.1`); provenance strutturata
  (`producer`, `source_sha` dichiarato, `detail`).
- Pubblicazione: live lega ogni ref alla run viva (`is` come sanity check di
  composizione, soluzione per valore); durevole valida senza run e senza
  `is`. D1: 3/80 A raggiungibile senza run. Rotture -> `Failure`;
  `Refusal` a monte non si compone (propagazione al confine di prodotto).
- Schema v0.2: prima le trasformazioni, poi l'analitica ancorata allo stato
  finale. ProofGraph/layout/view: differiti con contratto esplicito (H5).
- CoV: session.py 100% linee/rami; proof_session.py 100% linee/rami;
  globale >= 95%; domain 100%; boundaries PASS.
- Discrepanza metriche chiusa: locale 1732 vs remoto 1730+2 skip = due skip
  condizionali d'ambiente (path plugin BMAD, chromium solo-macOS), nessuna
  differenza di sorgente (decisione O0 §3).
- Aperti registrati: integrita' H3; verita' semantica visuale singola
  (`componi` riesegue `transform`, H5); `__post_init__` da scomporre (45
  stmt); fixture triplicate; contesto AGENTS gestito stale (repo PUBLIC non
  privato, sette prefissi); D2-D8; wire canonico; manifest.
- H2.75 / PR #11 (`work/proof-demo-application-boundary`) e' stacked sopra
  O0 e resta DRAFT. `Product Verified` resta riservato ai gate prodotto
  successivi, inclusa la chiusura visuale H5. L'unica via applicativa e'
  `pipeline/proof_run.run_proof_session`
  (IR, Request) -> `ProofSessionClosure` (sessione CLOSED + registro
  trattenuto): Refusal propagato identico, registro canonico via
  `componi_registro`, sessione via compositore (che valida live, una sola
  volta). Nome `publish` rifiutato: AD-5 lo riserva al gate finale.
  Orologio iniettato (ClockPort), entropia chiamabile iniettata (niente
  EntropyPort), supply state-id dimostrata (componenti+1), evidenze
  possedute dal confine. D1 3/80 A, ponte ok. `GLOBAL_PRODUCT_ENTRYPOINT_
  RECONCILIATION = OPEN` (`resolve` resta l'ingresso dichiarato).

## P1-K (STORICO)

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
- STORICO: il legame CircuitIR object ↔ proof_node e' chiuso sul branch
  prodotto (vedi P1-L sopra): `CircuitStateRegistry` + `proof_node` = stato
  consumato (G1). Non piu' debito residuo.
- No external CAS or new runtime dependency.
- Certification evidence is recorded in GitHub Actions / git history,
  rather than embedding a self-invalidating branch SHA here.
