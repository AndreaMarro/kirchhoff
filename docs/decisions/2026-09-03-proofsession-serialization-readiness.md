# H2.5 — Durable authority + serialization readiness (correct-course)

Data: 2026-09-03. Branch `work/proof-demo-0.1`, base `main@de6bb6c`.
Gate: H2.5 CHIUDE la leggibilita' durevole; H3 (serializer canonico) inizia
solo dopo chiusura remota di questo gate.

## 1. Problema

H1.5/H2 chiamavano `PROOFSESSION_CANONICAL = 1/1` una proiezione la cui
autorita' moriva col processo:

- `validate_publication` legava effetto, lineage e Claim alla run viva con
  l'identita' Python (`is`): dopo serialize -> exit -> deserialize la copia
  `==` ma non `is` veniva respinta ("l'effetto del passo 0 non e' l'oggetto
  certificato della run", provato con `copy.deepcopy` prima del fix);
- la sessione non portava la soluzione finale: il Claim cita soggetti ed
  evidenze ma non il valore; `Fraction(3, 80) ampere` viveva solo in
  `run.final_execution.execution.resolved`, irraggiungibile senza run viva;
- `session_id` coniato dal chiamante mentre `identity.py` dichiarava writer
  il compositore; `source_sha` di forma senza autorita'; `document_profile`
  qualsiasi stringa non vuota; `VERIFIED` di backend indistinguibile dal
  badge prodotto owner-locked; `sess_` solo nel codice contro sei prefissi
  nello spine.

Scoreboard corretto (misura, non premio):

```text
PROOFSESSION_MODEL                    1/1
IN_MEMORY_PUBLICATION_VALIDATION      1/1
IN_MEMORY_COMPOSER                    1/1

DURABLE_PROOFSESSION_AUTHORITY        1/1  (chiuso qui)
REPLAY_SAFE_PUBLICATION               1/1  (chiuso qui, via durevole)
CANONICAL_PROOFSESSION                PARTIAL (resta H3: wire + hash)
```

## 2. Matrice di riconciliazione §6.1 / spine / codice

| Concern | Student Vertical Slice §6.1 | Spine / AD | Codice v0.1+H2.5 | Decisione gap | H3 puo' procedere? |
|---|---|---|---|---|---|
| session_id + schema | richiesti | Consistency Conventions (ULID con prefisso) | `sess_` + `proof-session.v0.1` | RICONCILIATO (D-H2.5-6, emendamento in loco) | si' |
| version pins | core/planner/catalog/layout/renderer/profilo | — | solo pin reali: `planner_schema_version`, `curriculum_profile`, `document_profile` chiuso (D-H1.5-2, D-H2.5-3) | RICONCILIATO: semver inventati rimossi, resto inesistente a runtime | si' |
| input request + IR refs | richiesti | AD-21 proiezione per riferimento | `original_request` + `state_refs` via `CircuitStateRegistry` | RICONCILIATO | si' |
| final solution ref | richiesto | — | `final_solution: ResolvedQuantity` per valore (D-H2.5-2) | RICONCILIATO IN CODICE | si' |
| verification ref | richiesto | AD-32 TruthfulnessGate | `final_claim` per valore + pin verificatore nel modello | RICONCILIATO IN CODICE | si' |
| ProofGraph ref | richiesto | AD-29 nodi=stati | assente, schema chiuso | DIFFERITO ESPLICITO (H5) | si', senza Pretendere chiusura visuale |
| DidacticPlan ref | richiesto | §9 planner | assente; canonicita' provata dalla run (`_require_canonical_plan`) | DIFFERITO (identita' dei piani inesistente) | si' |
| derivation refs | (§7.2, D-id) | — | citazioni `D0..` + catena ancorata al Claim (D-H2.5-2) | RICONCILIATO (store durevole differito, cfr. deferred-work §9) | si' |
| view/layout refs | richiesti | AD-8/AD-21: un `lay_` per nodo | assenti | OUT OF SCOPE backend 0.1 (H5) | si' |
| animation/document refs | opzionali | — | assenti / solo profilo | DIFFERITO (H5/H-documento) | si' |
| publication state | tipizzato | AD-5 gate unico, AD-13 Refusal/Failure | `VERIFIED` backend-scoped (D-H2.5-7) | COLLISIONE owner documentata, via conservativa | si', con scoping nel wire contract |
| provenance | deterministica | — | producer + `source_sha` dichiarato + detail (D-H2.5-4) | RICONCILIATO (confine dichiarato) | si' |
| content hash | richiesti | — | assenti (circolari dentro il modello) | H3 fuori dal modello | H3 li calcola |

## 3. Decisioni

### D-H2.5-1 — Autorita' durevole: uguaglianza + registro, `is` solo a composizione

`validate_publication` resta il gate di composizione (tie `is` come sanity
check in-process). `validate_persisted_publication(sessione, registro)`
valida senza run e senza `is`: tipi, produttore autorevole, risoluzione di
ogni state ref. La coerenza interna non si ricontrolla (E-65: il costruttore
la garantisce a ogni costruzione; un ricontrollo avrebbe rami irraggiungibili
e violerebbe il 100% di branch). Il durevole prova coerenza della chiusura,
non corrispondenza a una run dimenticata: dopo la persistenza la fiducia sta
nella catena di integrita' (H3), non nella RAM.
Alternative scartate: cache globale di oggetti / pickle / interning (vietati
dal gate); rebuild della verita' via re-solve nel validatore (violerebbe
"il serializer non risolve", anticipato qui).

### D-H2.5-2 — Soluzione e verifica come artefatti distinti, per valore

`final_solution: ResolvedQuantity` portato per valore (precedente:
`final_claim` per valore, `VisualStep.risultato`). Guardie nel modello:
tipo, `derivation_id == final_derivation_id`, coerenza con `final_request`
(id/target/quantity), inclusione nelle `evidence_ids` del Claim. Pin del
verificatore nel modello (`VERIFIER_ID/VERSION` da `truthfulness`): un Claim
forgiato-uguale-con-verificatore-diverso fallisce senza `is`. Derivation
store e TransformEvidenceStore NON costruiti: search-before-build ha trovato
il differimento motivato in deferred-work §9 (un registro nuovo con id nuovo
e' decisione di spine) e il Claim resta l'artefatto di verifica che ancora la
catena D-id. La catena resta citazione in-session, non id globale spacciato
per tale.

### D-H2.5-3 — Profilo documento chiuso

`DOCUMENT_PROFILE = "student-pdf.v0.1"`, autorita' di `domain/proof/session.py`
come `SCHEMA_VERSION`. Alternativa scartata: stringa libera del chiamante
(nascondeva arbitrio dietro "dichiarazione onesta" mentre il documento
prodotto dipende dal profilo). Un secondo profilo = nuova versione di schema.

### D-H2.5-4 — Provenienza: dichiarato, non verificato

`source_sha` = revisione produttrice dichiarata (forma SHA-40), non revisione
di checkout verificata. Il dominio non tocca Git; legare il campo ai metadati
reali di build spetta alla radice di composizione (futura). Fixture sintetiche
ammesse proprio perche' il contratto dice "dichiarato".

### D-H2.5-5 — Writer unico: il compositore conia

Opzione A (compositore conia da istante/entropia iniettati), scartata B
(caller che conia: due verita' su chi e' il writer, doc contro codice).
Firma senza `session_id`; a parita' di ingressi conio riproducibile (replay),
a entropia fresca occurrence nuova. Freschezza entropia = dovere del chiamante.

### D-H2.5-6 — `sess_` ratificato nello spine

`sol_` = Published di `solve`, mai la sessione. Emendamento in loco della riga
Identificatori delle Consistency Conventions (pratica stabilita: dieci AD
emendati in loco). Contesto agente derivato (`AGENTS.md`, blocco gestito da
bmad-project-context) NON toccato a mano: cita ancora sei prefissi, va
rigenerato dal percorso supportato (refresh del blocco).

### D-H2.5-7 — OWNER / SPEC COLLISION: VERIFIED prima di H5

```text
Sorgente: piano master "badge Verified solo quando tutti i gate passano"
  + K-0 (il disegno fa parte della prova) + AD-5 (8 controlli per nodo,
  incluso round-trip visuale).
Comportamento: sessione backend con publication_status VERIFIED senza
  ProofGraph/layout/round-trip.
Conflitto: il token VERIFIED suggerisce il badge prodotto, che richiede H5.
Via conservativa: v0.1 pre-release (PR DRAFT, nulla di pubblico) corregge il
  significato per scoping esplicito — VERIFIED = chiusura di pubblicazione di
  backend — senza toccare la definizione owner-locked del badge. H3 dovra'
  documentare lo scoping nel wire contract; H5 chiude il badge prodotto.
  Nessun nuovo stato pubblico inventato.
Decisione owner richiesta: ratificare lo scoping o imporre la ridenominazione
  del campo prima di H3.
```

Q1: `Claim.status == VERIFIED` e' solo elettrico/dominio (gate P1-K).
Q2: `ProofSession.publication_status` NON significa chiusura visuale in v0.1.
Q3: No, la sessione backend non puo' portare il badge prodotto prima di H5.

### D-H2.5-8 — Refusal al confine, Failure nel compositore

Compositore stretto: Refusal in ingresso = corruzione -> `Failure` (nome test
corretto, era fuorviante). La propagazione "rifiuto resta rifiuto" vive al
confine di prodotto (orchestrare -> restituire senza comporre), provata con
il caso condensatore.

## 4. Impatto migrazione / serializzazione

- Schema resta `proof-session.v0.1` (pre-release, PR DRAFT): aggiunta
  `final_solution` richiesta, `document_profile` chiuso, `source_sha`
  ridefinito come dichiarato, `session_id` non piu' iniettabile. Nessun
  artefatto pubblico esiste: nessuna migrazione.
- H3 riceve: sessione autosufficiente (soluzione + verifica per valore,
  stati via registry), validatore durevole senza `is`, writer unico,
  token chiusi, scoping VERIFIED documentato, manifest di integrita' ancora
  da costruire (hash SHA-256 con domain separator, fuori dal modello).

## 5. Falsificabilita'

`tests/test_proof_durable_authority.py` (A-K + chiusure del durevole):
deepcopy passa durevole/fallisce live; 3/80 A senza run; verifier forgiato
respinto; profilo banana respinto; writer unico (firma + determinismo);
nessun ref visuale; condensatore -> Refusal al confine; ricostruzione fresca
valida solo sul durevole; ponte zero-transform durevole. Moduli critici
(session.py, proof_session.py) 100% linee/rami, BrPart 0.
