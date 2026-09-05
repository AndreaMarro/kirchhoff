# Decision record — ProofSession: occurrence identity vs contenuto semantico

Data: 2026-09-04. Sessione H0, branch `work/proof-demo-0.1`, base `main@de6bb6c`.

## Tensione

`domain/identity` conia ULID veri (48 bit di istante + 80 di casualita' fresca a
ogni conio) e vieta identificatori che *sembrano* ULID senza esserlo. La
specifica Student Vertical Slice (invariante 8) chiede JSON canonico byte-stabile
ripetendo la stessa richiesta a versioni pinnate.

## Alternative scartate

1. `session_id` come hash del contenuto. Scartata: le convenzioni dicono ULID e
   un hash non e' un ULID (ordinamento per impronta invece che per tempo,
   successione plausibile e falsa — stesso argomento con cui `identity` ritiro'
   il conio da impronta).
2. Nuovo genere `sess_` in `IdentityKind`. Scartata in H1: il vocabolario e'
   chiuso e toccarlo e' una modifica delle Consistency Conventions, non di
   questo gate. Il modello accetta `session_id` come stringa opaca non vuota;
   il conio ULID resta al confine applicativo (H2), dove vivono orologio ed
   entropia iniettati.
3. Byte-identical fra due *nuove* occurrence. Contraddittoria con ULID freschi:
   documentata come non-requisito (vedi sotto), non implementata.

## Decisione

- **Occurrence identity:** due esecuzioni dello stesso problema hanno
  `session_id` (e `state_refs`) diversi. Mai uguaglianza byte-fra-occurrence.
- **Semantic content identity:** stesso input normalizzato + stesse versioni
  pinnate + stesso profilo => stessi contenuti semantici, stesso piano, stessi
  risultati matematici, stessi semantic hash (H3). Gli hash coprono il
  contenuto semantico, mai gli ULID di occurrence.
- **Replay identity:** `serialize(sessione_congelata)` e' byte-identical a se
  stessa; `deserialize(serialize(s)) == s`.
- **Niente hash dentro il modello H1:** conservare un content-hash dentro il
  contenuto stesso che l'hash copre e' circolare. H1 non ha campi hash; H3
  aggiunge serializer + hash esterni al modello.

## Collocazione (nessun conflitto con AD-8 / spec 6.2)

La spec 6.2 assegna pubblicazione e significato a `domain/proof`: il modello
vive in `domain/proof/session.py` e importa solo `domain/` (nessun
`render/`, nessun `pipeline/`). Il compositore applicativo (H2) vivra' in
`pipeline/` e proiettera' `CertifiedDidacticRun` + `CircuitStateRegistry` nel
modello, senza risolvere, ripianificare o ricertificare nulla.

## Portata H1 (rinvii dichiarati, non debito nascosto)

- `AnalyticalProofStep` porta riferimenti (`state_ref`, `derivation_before`,
  `derivation_after`), non equazioni per valore: non esiste ancora un registro
  delle derivazioni e inventarne uno e' decisione da spine (cfr.
  deferred-work §9). H2 decidera' se portare `ExactEquation` per valore
  (precedente: `VisualStep.risultato`) o restare per riferimento.
- `final_claim: Claim` e' portato per valore: e' un certificato congelato, non
  una struttura mutabile (stesso precedente).
- `publication_status` accetta solo `VERIFIED` in questo schema: Refusal e
  Failure viaggiano su canali separati (orchestratore / compositore), mai come
  sessioni mezze verificate.

## Falsificabilita'

`tests/test_proof_session.py`: ogni guardia del modello ha un test che l'ha
vista sollevare; CoV 100% linee / 100% rami sul modulo.
