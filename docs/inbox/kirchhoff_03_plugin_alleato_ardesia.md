# Kirchhoff come plugin alleato di Ardesia

**Working component ID:** `io.ardesia.circuit-reasoning`  
**Working product name:** Kirchhoff  
**Data:** 14 agosto 2026  
**Stato:** product/architecture proposal  
**Metodo:** BMAD correct-course + plugin contract + readiness gate

---

# 0. Executive verdict

Kirchhoff non dovrebbe essere “assorbito” da Ardesia e non dovrebbe nemmeno crescere come prodotto completamente separato che duplica simulatore, lavagna, memoria e infrastruttura.

La forma più forte è una relazione **alleata**:

```text
                    KIRCHHOFF
      Verified Visual Reasoning Engine
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Web/PWA          MCP         Ardesia adapter
                                         │
                                         ▼
                          io.ardesia.circuit-reasoning
                                         │
                 ┌───────────────────────┼───────────────────┐
                 ▼                       ▼                   ▼
        io.ardesia.simulation         LessonOS           ToolHost/Board
```

**Kirchhoff resta un kernel/prodotto vendibile autonomamente.**  
**Ardesia ottiene una capability di reasoning circuitale di qualità molto superiore.**  
**Kirchhoff ottiene lavagna, penna, memoria, simulatori e composizione multi-plugin senza ricostruirli.**

Questo è esattamente il tipo di confine che il canon Ardesia sta già cercando di imporre a ELABTutor: il guest possiede il proprio valore di dominio e cede shell, auth, memoria e altre responsabilità al Core/Host.

---

# 1. Cosa possiede Kirchhoff

Kirchhoff possiede esclusivamente la logica necessaria a trasformare un problema circuitale in un **ProofGraph visuale verificato**.

Ownership:

- `CircuitIR` logico/schematico quando necessario al reasoning;
- `LayoutIR` e `LayoutPatch` per la continuità visuale della derivazione;
- `ProofGraph`;
- `TransformCatalog`;
- transform applicability;
- transform proof obligations;
- Verification Engine specifico della derivazione;
- visual round-trip verification della rappresentazione schematic reasoning;
- StudentTrace semantic interpretation;
- hint/explanation policy;
- CurriculumProfile / NotationProfile per circuit theory;
- certificate/provenance del proof;
- eval/harness/failure corpus del reasoning circuitale.

Kirchhoff **non possiede**:

- auth Ardesia;
- board shell;
- LessonOS database;
- simulator fisico/breadboard general-purpose;
- generic plugin lifecycle;
- global reporting;
- global billing dentro Ardesia;
- ELABTutor didactic pack data;
- raw LLM provider SDK dentro il domain.

---

# 2. Cosa possiede Ardesia

Ardesia Host/Core continua a possedere:

- identity/account/tenant;
- ToolHost;
- plugin install/enable/disable;
- capability grants;
- board objects e persistence;
- pen/whiteboard primitives;
- LessonOS event log/materialization;
- cross-plugin coordination;
- provenance boundary generale;
- global export/session/project context;
- host-level network/storage/LLM capabilities;
- safety/kill-switch.

Kirchhoff non deve diventare una seconda Ardesia dentro un post-it.

---

# 3. Cosa possiede `io.ardesia.simulation`

Il Simulation Plugin è un alleato distinto e deve restare owner di:

- breadboard/circuit physical scene;
- component registry;
- wires e pin geometry;
- simulator canvas;
- electrical provider dispatch per simulation;
- instruments/probes;
- runtime/AVR/SPICE provider boundary;
- placement/occupancy validation;
- simulation diagnostics.

Il canon Ardesia già stabilisce questa direzione. Kirchhoff non deve importare il vecchio CircuitSolver/renderer dal subtree ELABTutor creando un nuovo secondo simulatore.

---

# 4. Perché reasoning e simulation sono due plugin diversi

Sembrano simili, ma risolvono problemi differenti.

## Simulation

Domanda:

> “Cosa succede elettricamente in questa scena/questo montaggio?”

State:

- parts;
- pins;
- wires;
- physical/board geometry;
- provider state;
- instruments.

## Circuit Reasoning

Domanda:

> “Come trasformo questo circuito in una derivazione comprensibile e verificata?”

State:

- schematic CircuitIR;
- ProofState;
- Transform;
- LayoutPatch;
- equation;
- evidence;
- certificate;
- student hypothesis.

## Ponte

Quando il reasoning ha bisogno di conferma numerica/fisica può chiamare Simulation/Solver capability tramite un port. Quando Simulation vuole una spiegazione didattica, può invocare Circuit Reasoning.

Nessuno dei due deve inglobare l'altro.

---

# 5. Contratto del plugin Ardesia

Working manifest concept:

```ts
{
  id: "io.ardesia.circuit-reasoning",
  kind: "plugin",
  version: "0.x",
  surfaces: ["board-embed", "panel"],
  capabilities: {
    "board.read": {},
    "board.write": { scope: "own-embed" },
    "graph.query": {},
    "lesson.event.emit": { events: [
      "proof.started",
      "proof.transform.proposed",
      "proof.transform.corrected",
      "proof.completed"
    ]},
    "llm.generate": { mediated: true },
    "simulation.solve": { optional: true }
  }
}
```

I nomi esatti devono essere allineati al contract reale Ardesia; questo è uno schema concettuale, non una dichiarazione che tali capability esistano già con questi nomi.

---

# 6. Surface native inside Ardesia

## 6.1 Proof post-it

Un post-it può contenere:

```text
┌───────────────────────────────────────┐
│ PASSO 4/11                  Verified │
│                                       │
│  BEFORE    → transform →    AFTER    │
│                                       │
│  [diff] [why?] [certificate]         │
│                                       │
│  R34 = R3 || R4                      │
│                                       │
│  [Prova tu il prossimo passo]        │
└───────────────────────────────────────┘
```

## 6.2 Whiteboard mode

Il board Ardesia diventa il canvas esteso:

- cerchiare componenti;
- scrivere equazioni;
- frecce;
- note;
- selezionare nodi;
- trascinare un proof state sulla lavagna;
- affiancare due stati;
- aggiungere Simulation post-it;
- chiedere spiegazione su una selezione.

Kirchhoff interpreta questi gesti attraverso l'adapter e produce `StudentTrace`, senza diventare owner dell'intera lavagna.

---

# 7. LessonOS: il vantaggio che Kirchhoff standalone non ha

In web standalone Kirchhoff può mantenere session history limitata. Dentro Ardesia può collegarsi alla memoria didattica di lungo periodo senza inventare un altro “student model”.

Eventi consigliati:

```text
proof.started
proof.input.confirmed
proof.transform.proposed
proof.transform.accepted
proof.transform.rejected
proof.hint.requested
proof.explanation.expanded
proof.misconception.observed
proof.misconception.corrected
proof.completed
proof.abandoned
```

Payload:

```text
proof_id
state_id
transform_id
concept_refs[]
evidence_refs[]
curriculum_profile
source_artifact_ref
```

LessonOS materializza poi viste/relazioni; Kirchhoff non scrive direttamente il grafo.

---

# 8. Dalla lavagna alla spiegazione su misura

Esempio completo:

1. Lo studente sta osservando `ProofState C4`.
2. Cerchia `R3` e `R4` sulla lavagna.
3. Scrive `R3 + R4`.
4. Ardesia board produce selection/strokes/text anchors.
5. Kirchhoff adapter associa gli anchor agli ID semantici del proof.
6. `StudentTrace` crea una `candidate_transform`.
7. Transform verifier controlla serie/parallelo.
8. Risultato: serie false, parallelo true, shared nodes A/B.
9. Tutor decide se dare domanda socratica, hint o spiegazione esplicita secondo session state.
10. Se l'utente corregge, viene emesso `proof.misconception.corrected` con evidence, non un voto.

Questo è più vicino a un vero tutor perché la risposta è causata da **ciò che lo studente ha fatto sul circuito**, non solo dal testo della chat.

---

# 9. Bidirectional handoff Kirchhoff ↔ Simulation

## Caso A — reasoning → simulation

Durante un transitorio:

- Kirchhoff crea gli stati 0⁻, 0⁺, ∞, circuito visto dall'elemento;
- può chiedere a una provider capability di verificare quantità o simulare la risposta;
- apre un Simulation post-it con la scena corrispondente.

## Caso B — simulation → reasoning

Uno studente monta un circuito e vede una tensione inattesa.

Simulation produce una scena/netlist validata. Kirchhoff può creare:

- schematic abstraction;
- percorso di analisi;
- spiegazione della corrente/tensione;
- proof step legato ai nodi reali della scena.

## Regola

Il passaggio tra i due avviene tramite **typed scene/netlist contracts**, non screenshot quando esiste stato strutturato.

---

# 10. ELABTutor come terzo alleato

Il rapporto ideale diventa:

```text
ELABTutor Pack
     │ didactic content / lesson path
     ▼
io.ardesia.simulation ──────── physical interactive scene
     │
     └─────────────┐
                   ▼
io.ardesia.circuit-reasoning ─ explanation/proof when needed
                   │
                   ▼
                LessonOS
```

ELABTutor può chiedere:

> “mostra perché questi due LED/resistori si comportano così”

senza possedere né solver generale né reasoning engine.

Kirchhoff non deve conoscere i volumi/manuali ELAB salvo metadata/curriculum forniti dal pack.

---

# 11. Shared IDs e provenance

Perché l'ecosistema funzioni servono identity bridges stabili.

Esempio:

```text
SimulationScene component id: sim:R3
ProofGraph component id: proof:R3
Source image region: src:region18
LessonOS evidence ref: evidence:...
```

Un mapping esplicito permette:

- click su R3 nel proof → highlight R3 nella simulation;
- click sul valore → mostra source crop;
- LessonOS event → link al proof e alla source;
- export → provenance completa.

Mai affidarsi alla posizione visuale per identificare semanticamente un componente.

---

# 12. Plugin as product ally, not internal fork

Il repository commerciale/standalone di Kirchhoff può avere il proprio release lifecycle.

L'integrazione Ardesia deve usare una boundary stabile:

```text
@kirchhoff/core        private/shared kernel
@kirchhoff/contracts   versioned schemas
ardesia-adapter        plugin integration
mcp-adapter            external integration
web-adapter            standalone product
```

La scelta esatta mono-repo/multi-repo va presa in base alla governance reale, ma il principio è **one kernel, multiple adapters**.

---

# 13. Cosa riutilizzare già da Ardesia

Dal repository e dai canon consultati emergono asset che riducono fortemente il lavoro:

- ToolHost lifecycle e capability thinking;
- board embed surface;
- `renderEmbeddable()` pattern;
- SimulationScene e mutation validation;
- LessonOS append-only events/materialized graph;
- provenance orientation;
- plugin/pack decoupling lessons apprese da ELABTutor;
- kill-switch/security boundary;
- iPad/board interaction foundation.

Kirchhoff dovrebbe **consumare** questi asset invece di riscriverli.

---

# 14. Cosa Kirchhoff può restituire ad Ardesia

La relazione deve essere simmetrica. Kirchhoff può migliorare Ardesia in aree che oggi non sono necessariamente mature:

1. `ProofGraph` come pattern generale per ragionamenti visuali.
2. `LayoutPatch` e visual continuity engine.
3. Truthfulness Gate e evidence-backed claims.
4. Visual round-trip verifier.
5. StudentTrace semantic interpretation.
6. Harness metamorfici per grafi/disegni.
7. MCP Apps adapter pattern riutilizzabile.
8. Cross-host → Ardesia continuation.
9. Curriculum/notation rendering separato dal domain truth.

Questi possono diventare primitive riusabili oltre i circuiti.

---

# 15. L'orizzontalità giusta per Ardesia

Kirchhoff non deve iniziare come “Reasoning for all STEM”.

Ma il kernel dovrebbe evitare concetti inutilmente specifici quando l'astrazione è reale:

```text
State
Transform
Layout
Evidence
Certificate
StudentTrace
```

I circuiti implementano:

```text
CircuitState
CircuitTransform
CircuitVerifier
```

Un giorno Ardesia potrebbe avere:

```text
ControlDiagramReasoning
FreeBodyDiagramReasoning
SignalFlowReasoning
```

che riusano parti del framework senza fingere che tutti i domini siano uguali.

---

# 16. Product packaging

## Standalone

**Kirchhoff Solve** — B2C.  
**Kirchhoff Studio** — tutor/docenti/centri.

## Ardesia

**Circuit Reasoning Plugin** — capability nativa disponibile ai pack e agli utenti Ardesia.

Possibile entitlement model:

- alcune capacità incluse in Ardesia tiers;
- advanced proofs/volume via Kirchhoff entitlement/account linking;
- B2B licensing separabile.

La decisione commerciale va presa più avanti; l'architettura deve evitare hard-code.

---

# 17. MCP triangulation

Il plugin crea un triangolo strategico:

```text
                Kirchhoff Core
              /                \
             /                  \
      Ardesia native         MCP Apps
          │                      │
  board + LessonOS         ChatGPT/Claude
             \                  /
              \                /
               same proof IDs
```

Un esercizio iniziato in un host esterno può continuare in Ardesia. Uno proof creato sulla lavagna può essere riaperto in una conversazione esterna tramite ID/permissions.

Questo rende Ardesia più aperta senza sacrificare il suo workspace.

---

# 18. Privacy/compliance boundary

Dentro Ardesia:

- LessonOS conserva soltanto gli eventi/evidence necessari;
- raw image retention resta responsabilità della capability/input pipeline secondo policy;
- plugin non persiste profili valutativi paralleli;
- tenant isolation è host-enforced;
- cross-host MCP non riceve automaticamente l'intera memoria LessonOS.

Dati inviati a model providers passano da ModelPort/policy host, con routing conforme al deployment/tenant.

---

# 19. Failure modes da prevenire

## FM1 — Kirchhoff importa il simulator

Risultato: due scene graph, due solver, drift.  
**Gate:** dependency lint.

## FM2 — Kirchhoff costruisce memoria studente propria dentro Ardesia

Risultato: conflitto LessonOS e compliance.  
**Gate:** plugin storage schema limitato a own operational state; learning events via host.

## FM3 — Ardesia modifica direttamente ProofGraph internals

Risultato: kernel non più portabile.  
**Gate:** contracts package + adapter only.

## FM4 — MCP-specific concepts entrano nel domain

Risultato: lock-in distribution.  
**Gate:** domain dependency rule.

## FM5 — Visual scene e proof scene divergono

Risultato: click/highlight errati.  
**Gate:** ID mapping + integration fixtures.

## FM6 — Tutor LLM può bypassare verifier

Risultato: spiegazione apparentemente autorevole ma falsa.  
**Gate:** no domain mutation/Verified from ModelPort.

---

# 20. BMAD plan per creare il plugin

## Phase 0 — Decision/constitution

Registrare:

- plugin ownership;
- non-duplication invariants;
- K-0…K-5;
- Simulation boundary;
- LessonOS boundary;
- MCP/web/native adapter strategy.

## Phase 1 — Product Brief

Definire due clienti:

- standalone student/tutor;
- Ardesia user/pack consuming a capability.

Non confonderli: stessa tecnologia, journey diversa.

## Phase 2 — PRD

FR dedicati a:

- ProofGraph;
- layout continuity;
- interactive board integration;
- simulation handoff;
- LessonOS events;
- embed lifecycle;
- provenance;
- cross-surface resume.

## Phase 3 — UX Pro

Progettare:

- proof post-it;
- board selection/highlighting;
- “prova tu” flow;
- simulation side-by-side;
- mobile/native differences;
- pen interaction.

## Phase 4 — Architecture

Produrre:

- contract schemas;
- adapter ports;
- package boundaries;
- dependency gates;
- event mapping;
- ID/provenance mapping;
- threat model.

## Phase 5 — Epics

Non partire da “integra tutto”. Vertical slices.

## Phase 6 — Readiness

Gate:

- no duplicated ownership;
- every FR testable;
- every public contract versioned;
- privacy/security paths;
- fallback/refusal semantics;
- rollback.

## Phase 7 — Ship loop

Story-by-story, acceptance→test map, clean-context review, E2E, retrospectives.

---

# 21. Epiche iniziali proposte

## Epic A — Proof Kernel standalone

Prima/dopo + local LayoutPatch + certificate + roundtrip.

## Epic B — Ardesia contract slice

Plugin monta un ProofReplay statico/structured tramite ToolHost senza duplicare shell.

## Epic C — Board interaction

Selection/strokes → StudentTrace → verify hypothesis.

## Epic D — Simulation bridge

Typed mapping ProofState ↔ SimulationScene/netlist per un caso semplice.

## Epic E — LessonOS continuity

Supported events + evidence refs + resume.

## Epic F — MCP parity slice

Lo stesso proof può essere consumato da MCP App e Ardesia native surface.

## Epic G — Production hardening

Security, tenant, performance, accessibility, upgrade/deprecation.

---

# 22. Acceptance test simbolico del rapporto

Il concetto di “alleato” è riuscito soltanto se questo test passa:

### Given

Uno stesso circuito `proof_123` è aperto in Kirchhoff web, Ardesia e una MCP App.

### When

L'utente seleziona il passo 4 e, in Ardesia, propone una trasformazione sulla lavagna.

### Then

- la trasformazione è verificata dallo stesso kernel;
- Ardesia emette soltanto un evento LessonOS host-approved;
- il Simulation Plugin resta owner della simulation scene;
- il ProofGraph rimane semanticamente identico tra superfici;
- nessun adapter contiene logica scientifica duplicata;
- l'utente può riaprire `proof_123` sul web/MCP con i permessi corretti.

Se per farlo servono tre implementation diverse della trasformazione, l'architettura ha fallito.

---

# 23. Economics of alliance

La relazione riduce costi in entrambe le direzioni.

## Kirchhoff risparmia

- whiteboard engine;
- plugin host;
- simulation stack;
- long-term learning memory;
- board persistence;
- rich iPad UX.

## Ardesia risparmia

- sviluppo di un reasoning engine circuitale da zero;
- visual proof framework;
- circuit transformation catalog/harness;
- standalone distribution experiments;
- MCP circuit surface specifica.

## Rischio

Coupling eccessivo potrebbe rendere Kirchhoff impossibile da vendere autonomamente e Ardesia dipendente da un kernel instabile.

Mitigazione: contracts e adapters versionati, release gates indipendenti.

---

# 24. Decisione finale

La relazione migliore è:

> **Kirchhoff è un prodotto autonomo e contemporaneamente il Circuit Reasoning Plugin di Ardesia.**

Non è una feature sepolta nel core.  
Non è una seconda app monolitica dentro la lavagna.  
Non è un clone del Simulation Plugin.  
Non è un pack didattico.

È una capability scientifica indipendente con una surface nativa Ardesia.

La divisione di responsabilità dovrebbe rimanere leggibile in una frase:

> **Simulation dice che cosa fa il circuito; Kirchhoff mostra e verifica come lo si ragiona; LessonOS conserva l'evidenza didattica; Ardesia orchestra lo spazio di lavoro.**

Questa composizione è più forte della somma dei quattro pezzi e, soprattutto, evita la deriva già osservata storicamente quando un guest/plugin inizia a duplicare shell, auth, AI, memoria, report e simulatore.

---

# 25. Provenienza

Questo documento usa come base:

- fonti incollate su Kirchhoff/GRAFITE storico, PRD, Architecture, UX, Epic, loop e change proposal;
- conversazione sul “circuito come ragionamento” e MCP Apps;
- canon Ardesia `ELAB-AS-PLUGIN-CANON`, `Simulation Plugin v2`, LessonOS dynamic graph e ARDESIA-MAP consultati nella sessione;
- principio BMAD chain-top/readiness/ship-loop già usato nei materiali.

Per il testo integrale delle fonti allegate: `kirchhoff_00_corpus_fonti_integrali.md`.
