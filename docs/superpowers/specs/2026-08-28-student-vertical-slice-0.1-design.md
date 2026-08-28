# Student Vertical Slice 0.1 — Design Specification

**Status:** approved direction, implementation pending

**Date:** 2026-08-28

**Owner gate:** Andrea approved the session-first approach and explicitly dissolved the active FERMO

**Source baseline:** `origin/main` at `723f870462d7d52cbd4de7d9d0d2fa771d0a080d`

**Working branch:** `work/student-vertical-slice-0.1`

## 1. Purpose

Deliver one real, end-to-end student experience that accepts a supported circuit problem and produces a verified, navigable solution session with:

- exact circuit and mathematical state owned by the Python core;
- a deterministic didactic plan;
- circuit-transform and analytical steps;
- semantic SVG and continuity-preserving animation;
- a usable responsive React application;
- an editorial, multipage PDF derived from the same session;
- visual, end-to-end, deterministic, and corpus-based verification.

The milestone is a vertical slice, not a claim that the entire university curriculum is covered. Unsupported inputs must produce typed `Refusal`, never invented output or a UI-only approximation.

## 2. Measured baseline

The design starts from the current repository rather than the stale public narrative:

- `1070` Python tests pass; domain coverage is `100%`; global coverage is `99.28%`.
- Boundary checks and the BMAD chain are green.
- The structured development evaluation publishes `36/36` cases with VSR `1.0` and SER `0.0`; this is not an image-extraction result.
- Exact DC and phasor solving, independent DC Tableau path B, verification, refusals/failures, circuit transformations, deltas, layout patches, semantic SVG, overlays, and `VisualStep` already exist.
- `ProofSession`, a didactic planner, analytical steps, a product HTTP boundary, the student web application, general layout, semantic animation, and an editorial PDF pipeline do not yet exist.
- Current automatic layout only covers `layout_a_maglia`; valid multi-mesh cases can solve without layout or SVG.
- Current PDF support prints one SVG and depends on a local Playwright cache path; it is not a deterministic document pipeline.
- The transform vocabulary has sixteen immutable v1 values, while only a small certified subset is executable.

These facts are the baseline for acceptance. Documentation claims that contradict fresh tests, code, or owner-locked decisions are not treated as implementation truth.

## 3. Product outcome

A student can submit a supported structured circuit exercise, receive a stable session URL, inspect the original problem, follow a deterministic sequence of exact circuit and analytical steps, play or scrub a semantic transition, open the evidence behind “verified,” and export a multipage solution PDF whose circuits, equations, labels, and final answer agree with the interactive session.

The first release must handle a deliberately bounded but nontrivial DC corpus, including bridge or multi-mesh topology and at least one controlled-source case through a systematic analytical fallback. It must also preserve the currently certified local reductions where they improve the explanation.

## 4. Non-goals

- No free-form image recognition in this slice.
- No LLM chooses methods, equations, or explanations.
- No browser-side solving, topology inference, or reconstruction of missing semantic state.
- No runtime plugin mechanism for adding mathematical techniques.
- No fake curriculum certification. The initial technical profile is not represented as a complete real-university profile while decision D2 remains open.
- No broad platform, collaboration, account, billing, or content-management layer.
- No replacement of exact core models with a second frontend model.

## 5. Architectural invariants

1. **One semantic source of truth.** `CircuitIR`, exact solver results, proof artifacts, layout artifacts, and verification artifacts are produced by the Python core and referenced by stable IDs.
2. **Projection by reference.** A `ProofSession` contains immutable identifiers and presentation metadata, not mutable copies of circuits, layouts, solver results, or proof graphs.
3. **No re-solving downstream.** HTTP adapters, React, animation, and PDF rendering consume a frozen session projection. They may format but may not infer or solve.
4. **Topology and presentation remain separate.** `CircuitIR` contains circuit meaning. `LayoutIR` contains geometry. A transform yields a semantic `Delta` plus a continuity-preserving `LayoutPatch`.
5. **Verification remains explicit.** A solution is publishable only when the existing verification contract passes. The UI badge links to real checks and certificates.
6. **Refusal and failure remain distinct.** Unsupported capability is a typed refusal; an invariant violation or unexpected defect is a typed failure.
7. **Persistent IDs survive.** Entity identity is stable across steps unless the semantic delta explicitly creates, merges, substitutes, or removes an entity.
8. **Determinism is observable.** Repeating the same request against the same pinned versions yields byte-stable canonical JSON and stable semantic SVG, subject only to explicitly normalized document metadata.
9. **The holdout stays protected.** Implementation and ordinary verification never inspect `reference-set/holdout`.
10. **No silent fallback.** Every fallback is a named, machine-readable planner decision with applicability evidence.

## 6. Core session model

### 6.1 `ProofSession`

`ProofSession` is the immutable product-level projection of one completed request. Its minimum contract is:

- `session_id` and schema version;
- pinned core, planner, catalog, layout, renderer, and document profile versions;
- input request and normalized `CircuitIR` references;
- final solution and verification references;
- `ProofGraph` reference;
- ordered `DidacticPlan` reference;
- ordered step references;
- initial and final view references;
- optional animation and document artifact references;
- typed publication status, refusal, or failure;
- deterministic provenance and content hashes.

The session is written only after all required referenced objects exist. Publication validates referential integrity, version compatibility, verification state, and final-view equivalence.

### 6.2 Stores and ownership

The current architecture lacks a durable register for transform products and reconstructible visual steps. This milestone adds minimal append-only repositories for the artifacts that a session references:

- circuit states;
- solver and verification results;
- transform results and proof graphs;
- derivation states and didactic steps;
- layouts, overlays, and composed views;
- frozen sessions and document artifacts.

The domain/proof layer owns proof meaning and session publication. Render owns layout, overlay, and view artifacts. Adapters may serialize IDs but do not own these models. In-memory implementations are acceptable for deterministic unit tests; the slice's real application requires a repository implementation with atomic publication and content-addressed integrity. Selecting the storage engine is an implementation-plan decision and may not change the domain contracts.

Because this closes known deferred architectural gaps, implementation begins with a BMAD correct-course/architecture update rather than silently changing owner-locked decisions.

## 7. Proof topology and didactic timeline

`ProofGraph` keeps its established meaning:

- nodes are exact circuit states;
- edges are certified circuit transformations;
- each proof node references the layout appropriate to that circuit state;
- graph navigation supports branches without imposing a presentation order.

The new `DidacticPlan` supplies the presentation order and can interleave two step types:

### 7.1 `CircuitTransformStep`

A `CircuitTransformStep` references a proof edge and includes:

- before/after circuit, proof-node, layout, and composed-view IDs;
- certified transform result;
- semantic delta and layout patch;
- affected-entity set and overlays;
- exact equation or identity used;
- concise justification and verification reference;
- semantic animation phases.

It never re-executes the transform to reconstruct “after.”

### 7.2 `AnalyticalStep`

An `AnalyticalStep` advances exact mathematical reasoning without pretending that the circuit topology changed. It attaches to one proof node and references:

- before/after immutable `DerivationState` IDs;
- the unchanged circuit and proof-node ID;
- equations introduced, substituted, eliminated, or solved;
- variable bindings to circuit entities;
- semantic overlays and focused entities;
- exact justification and verification evidence;
- before/after composed-view IDs when visual emphasis changes.

`DerivationState` is deliberately small: exact variables, equations, assumptions, and bindings. It is not a second solver IR. It records verified mathematical state produced by the core.

This split avoids illegal self-loop transforms and preserves the existing owner-locked definition of `ProofGraph`.

## 8. Versioned didactic catalog

The existing `TransformationKind` v1 enum remains immutable. It continues to name topological or electrical transformations already recognized by the proof engine.

The milestone introduces a separate, static `DidacticTechniqueKind` schema for techniques such as nodal analysis, mesh analysis, supernode, supermesh, superposition, source transformation, Thévenin, Norton, Millman, controlled-source equations, transformer/two-port treatment, and Laplace/transient methods.

“Closed” means closed per schema version and pinned profile:

- a session pins `catalog_schema_version`, `catalog_release`, and `curriculum_profile`;
- a release contains a finite compile-time vocabulary and certified applicability rules;
- a profile selects an ordered subset and pedagogical preferences;
- runtime data may not invent a technique;
- adding vocabulary requires a new schema version, implementation, tests, migration rules, and owner review;
- a technique may be listed but not advertised as supported until its executable certificate path is green.

The first slice uses a technical profile, provisionally `student-dc-v0.1`. It is explicitly not the final real-university profile governed by D2.

## 9. Deterministic didactic planner

The planner is a pure, versioned core service. Its inputs are the validated request, `CircuitIR`, requested quantities, supported-technique registry, and pinned curriculum profile. Its output is a `DidacticPlan` plus a machine-readable decision trace.

### 9.1 Planning stages

1. Classify topology, sources, domain, unknowns, requested quantities, and applicable certified techniques.
2. Generate only executable candidate actions.
3. Reject candidates whose preconditions or certificate paths cannot be proven.
4. Search a finite state space using a stable lexicographic cost.
5. Execute and verify the selected plan in the core.
6. Freeze proof, derivation, visual, and verification artifacts into the session.

### 9.2 Stable cost order

Candidates are ordered by:

1. certificate validity and capability support;
2. ability to reach every requested quantity;
3. profile method preference;
4. number of conceptual steps;
5. exact equation complexity;
6. visual clutter and estimated local layout movement;
7. stable technique and entity-ID tie-breakers.

Weights, tie-breakers, and applicability rules are versioned fixtures, not learned preferences.

### 9.3 Initial strategy

The slice first applies currently certified local reductions when they reduce explanation cost. If no certified reduction path completes the request, it uses a systematic exact nodal formulation for supported DC circuits, including the necessary controlled-source equations. Bridge and multi-mesh circuits therefore do not depend on reducibility.

Other listed techniques remain catalog entries with explicit unsupported capability state until their complete execution and certification paths exist. The planner must refuse rather than route through an unimplemented label.

## 10. General deterministic autolayout

The general layout engine lives in `render/layout`. It creates the initial `LayoutIR` for arbitrary supported graphs; later proof steps still use the existing patch/apply path for continuity.

### 10.1 Initial layout pipeline

1. Normalize traversal using stable node and entity IDs.
2. Identify terminals, articulation structure, parallel branches, cycles, and source/measurement anchors.
3. Assign deterministic ranks along the dominant energy-flow axis.
4. Allocate parallel lanes and cycle bands with stable ordering.
5. Place symbols on a fixed grid with orientation rules.
6. Route orthogonal wires between typed ports.
7. Measure symbol and label bounds.
8. Resolve collisions using bounded deterministic local moves.
9. Validate geometric invariants and derive a stable view box.

### 10.2 Hard invariants

- no wire crosses an unrelated node or symbol terminal;
- connected terminals share exact endpoints;
- symbols and primary labels do not overlap;
- entity placement is unique and finite;
- the same input produces the same serialized layout;
- the circuit fits the target viewport without horizontal page overflow;
- validation failure is typed and never silently replaced by an unordered drawing.

### 10.3 Continuity after transforms

For a proof edge, unchanged entities retain position and orientation where valid. Created or substituted entities occupy the affected region. Removed entities leave through semantic animation. Rerouting is local to the impacted region unless a hard invariant forces a wider deterministic repair, which is recorded in the patch.

The corpus includes series, parallel, mixed ladder, bridge, two meshes, current source, voltage source, controlled source, supernode-shaped topology, asymmetric labels, and a refusal case.

## 11. Product boundary and React application

A thin HTTP adapter exposes frozen sessions and artifacts. The exact framework and version are selected during the dependency gate using official documentation; the adapter remains replaceable and contains no domain logic.

Minimum operations:

- submit a supported structured problem;
- obtain publication/refusal/failure state;
- fetch a session projection and referenced immutable artifacts;
- fetch semantic SVG/animation payloads;
- export or fetch the derived PDF.

The React/TypeScript application renders the approved student workflow:

- problem and circuit context;
- ordered step navigation plus proof-graph access;
- equation, justification, and affected-entity detail;
- play, pause, previous/next, and scrub controls;
- a real verification evidence panel;
- PDF export;
- responsive layouts at `360`, `390`, `768`, and `1440` CSS pixels;
- keyboard operation, focus visibility, semantic headings, and reduced-motion support.

The client keeps only interaction state: selected step, playback phase, disclosure state, and viewport preferences. It does not hold an editable semantic circuit model.

## 12. Semantic animation

Animation consumes stable entity IDs, semantic roles, `Delta`, `LayoutPatch`, overlays, and before/after composed views. It does not interpolate arbitrary SVG path strings or infer meaning from DOM order.

Each step compiles to deterministic phases:

1. settle on the verified before view;
2. focus affected entities;
3. introduce the exact relation or analytical action;
4. dim or retire removed semantic entities;
5. move unchanged and retained entities according to the patch;
6. introduce created or substituted entities;
7. settle on the verified after view and equation state.

Reduced motion collapses spatial interpolation while retaining focus, explanation, and exact final state. End-of-animation equivalence is checked against the referenced after view, not a screenshot heuristic.

## 13. Editorial PDF pipeline

The document path is:

`ProofSession -> SolutionDocumentIR -> deterministic HTML/CSS -> PDF`

`SolutionDocumentIR` references the same circuit views, equations, justifications, verification evidence, and final answer used by the web application. It defines document order and pagination semantics but never solves or reconstructs proof data.

The initial editorial template includes:

- cover/problem summary;
- given values and requested quantities;
- one or more reasoning sections with circuit figures and exact equations;
- final answer with units;
- compact verification appendix and provenance.

The implementation must use a project-pinned browser runtime in local and Linux CI, never a hard-coded home-directory cache. Metadata, timestamps, font set, page size, margins, and locale are pinned or normalized. PDF acceptance checks page count, extractable text, embedded/vector figure presence, absence of clipping, and semantic agreement with the session. Byte identity is required only after the selected normalization path proves portable; until then, canonical `SolutionDocumentIR`, HTML, and extracted semantic checks are the deterministic contract.

## 14. Verification strategy

All fixtures represent executable circuits or explicit refusals; none are fake demo records.

### 14.1 Core

- contract tests for each new immutable model and repository;
- referential-integrity and publication tests;
- planner golden cases and permutation/metamorphic determinism;
- analytical-step exactness and unit consistency;
- proof/session round-trip and content-hash tests;
- general-layout invariants and regression corpus;
- full existing test, boundary, domain-coverage, and BMAD gates.

### 14.2 Product and visuals

- HTTP contract tests covering publication, refusal, and failure;
- React unit/component tests for navigation and accessibility;
- Playwright end-to-end tests at all target widths;
- visual baselines for representative session steps and PDF pages;
- semantic animation tests for phase order, reduced motion, and exact final state;
- Linux CI smoke test for browser and PDF generation;
- mobile checks for clipping and horizontal overflow.

Visual screenshots supplement semantic assertions; they do not replace exact model checks.

## 15. Delivery slices through Loop Kirchhoff v3

Every implementation slice is selected and closed through the repository loop, follows test-first development, and is small enough to verify and roll back independently.

1. **Architecture reconciliation.** Correct-course documents and locked decision updates for session ownership, reconstructible artifacts, analytical timeline, and versioned catalog semantics.
2. **Session spine.** Artifact repositories, `DerivationState`, step contracts, `DidacticPlan`, `ProofSession`, publication validation, and golden serialization.
3. **Planner vertical.** Certified reduction planning plus exact nodal fallback for the first bounded DC corpus, with decision traces and refusals.
4. **General layout.** Initial layout pipeline, invariant validator, corpus, and continuity integration.
5. **HTTP product boundary.** Real submit/read/artifact/export operations backed by the session spine.
6. **Student web application.** Responsive shell, real session navigation, proof/evidence views, and accessible interaction state.
7. **Semantic motion.** Phase compiler, player, reduced-motion path, and final-state equivalence.
8. **Document pipeline.** `SolutionDocumentIR`, editorial template, deterministic browser setup, multipage PDF, and Linux smoke coverage.
9. **Integrated quality closure.** End-to-end corpus, visual baselines, cross-artifact semantic equality, docs reconciliation, and final evaluation report.

No slice may claim completion by substituting hard-coded session JSON, screenshots, or browser-only calculations for missing core behavior.

## 16. Dependency policy

No dependency is added merely for convenience. Before each proposed dependency:

- confirm the capability is not already present;
- consult current official documentation;
- pin a compatible version;
- record license, security, runtime, CI, and determinism impact;
- obtain owner approval where policy requires it;
- keep domain models independent of the framework.

The first plan should prefer the standard library and the already present Playwright runtime where practical. Dependency installation, cloud deployment, and external publication remain separately approval-gated.

## 17. Risks and controls

- **Architectural duplication:** blocked by ID references, ownership tests, and adapter boundary checks.
- **Planner labels without execution:** blocked by executable-candidate generation and certificate gates.
- **Layout instability:** controlled by stable traversal, exact grid rules, invariant validation, and metamorphic tests.
- **PDF portability:** controlled by a pinned project runtime, Linux CI, normalized metadata, and semantic checks.
- **Scope explosion:** controlled by the bounded DC profile, typed refusal, and independent loop slices.
- **Stale documentation:** corrected only when fresh code/test evidence exists; historical decisions remain traceable.
- **Frontend semantic drift:** prevented by frozen session artifacts and cross-artifact equality tests.
- **Curriculum overclaim:** prevented by the provisional technical-profile label while D2 remains open.

## 18. Definition of done

The milestone is done only when all of the following are true on the working branch:

- a nontrivial supported DC corpus produces verified `ProofSession` artifacts twice with stable canonical semantics;
- at least one case uses a circuit transformation and at least one uses analytical nodal fallback;
- bridge/multi-mesh and controlled-source coverage is demonstrated or explicitly refused with a documented capability boundary;
- general layout passes collision, connectivity, determinism, and viewport invariants;
- the React application completes the student flow at target desktop and mobile widths using real backend artifacts;
- semantic animation ends exactly at the referenced after state and honors reduced motion;
- the multipage PDF is derived from the same session and passes Linux CI smoke and semantic checks;
- full Python tests, domain coverage, boundaries, BMAD gates, frontend tests, Playwright E2E, and visual checks are green;
- no holdout data, fake fixtures, hidden browser solving, or runtime catalog invention is present;
- README, sprint status, deferred-work records, receipts, and the final evidence report agree with the measured implementation.

Push, pull request creation, deployment, and merge are outside this specification unless separately authorized.
