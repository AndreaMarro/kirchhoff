# P1-M0 Research Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish an external, reproducible research laboratory and expose only evidence-backed, pure strategy information without changing Kirchhoff's planner or trust semantics.

**Architecture:** `lab/` contains all external adapters, generated fixtures, reports and experimental policies. `src/kirchhoff/domain/didactic/features.py` and `candidates.py` use only existing Kirchhoff types; they never import a laboratory package. Existing `pianifica`, `execute_plan`, `orchestrate_didactic_run`, and `certify_execution` remain behavioral oracles.

**Tech Stack:** Python 3.12, uv, pytest/pytest-cov, Hypothesis; research-only NetworkX, Lcapy, Schemdraw, direct `ngspice` subprocess and mutmut.

**Spec:** `/Users/andreamarro/.codex/attachments/d0c8aae0-96c6-4935-ac20-161f12759667/pasted-text.txt`

## Global Constraints

- Base and branch: `98f73f1184f34f50e030372efaa2b7d91e678cce` → `work/p1-m0-research-gpt`.
- `project.dependencies` remains `[]`; external packages are optional dev/research only.
- `src/kirchhoff/domain/` imports no external laboratory package.
- Do not read `reference-set/holdout/`, change planner behavior, or add `StrategyScore`.
- External results challenge only; Kirchhoff alone owns Claim, TruthfulnessGate, Request lineage and CertifiedDidacticRun.
- P1-M0 opens a PR against `work/student-vertical-slice-0.1-phase1` and never merges it.

---

### Task 1: Establish the technology and lab boundary

**Files:**
- Create: `docs/07-technology-register.md`
- Create: `docs/08-strategy-research.md`
- Create: `lab/README.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Produces pinned `dev` and `research` optional groups and an explicit source/license/verdict table.
- Prohibits runtime import of every research package.

- [x] Add the failing import-boundary test before modifying `pyproject.toml`.
- [x] Add `hypothesis` to the `dev` group; isolate NetworkX/Lcapy/Schemdraw/mutmut in `research`.
- [x] Record the web/GitHub evidence, licensing confidence, maintenance risk and recommended experiment for each serious candidate.
- [x] Run `uv lock`, the boundary test, and the full core suite.
- [ ] Commit only this coherent setup family after fresh verification.

### Task 2: Implement generative invariant attacks

**Files:**
- Create: `tests/strategies.py`
- Create: `tests/test_hypothesis_didactic.py`
- Create: `tests/test_hypothesis_stateful.py`
- Create: `lab/reports/mutation-baseline.md`

**Interfaces:**
- `bounded_dc_cases()` returns only valid bounded DC `IR`/`Request` pairs assembled with existing factories.
- Rule-based state transitions use `pianifica`, `execute_plan`, P1-J lineage and P1-K certification as real oracles.

- [x] Write properties that fail before the helper exists, then implement the smallest reusable strategies.
- [x] Verify deterministic P1-J/P1-K/P1-L replay and state-supply invariants with a genuine `RuleBasedStateMachine`.
- [x] Run a targeted mutmut baseline and record the invalid runner outcome without classifying it as a pass.
- [x] Run property and full test suites; commit after evidence is fresh.

### Task 3: Build external adapters and topology view

**Files:**
- Create: `lab/oracles/lcapy_adapter.py`
- Create: `lab/oracles/ngspice_adapter.py`
- Create: `lab/graph/graph_view.py`
- Create: `lab/fixtures/adapter-mapping.json`
- Create: `lab/reports/differential-oracles.md`
- Create: `lab/reports/graph-features.md`

**Interfaces:**
- Each adapter converts an `IR` to a non-authoritative result or an explicit unsupported reason.
- `GraphView.from_ir(ir)` returns a bipartite incidence graph that retains every component identity.

- [x] Write mapping-fixture tests before adapter code, covering polarity, current orientation, ground and floating voltage sources.
- [x] Build direct subprocess ngspice decks and carefully normalized Lcapy comparisons without floats in core values.
- [x] Generate 200 compatible cases per oracle and 100 graph cross-check cases; preserve each triage outcome.
- [x] Run all lab tests and record the experimental family.

### Task 4: Measure strategy and renderer alternatives

**Files:**
- Create: `lab/strategy/corpus.py`
- Create: `lab/strategy/policies.py`
- Create: `lab/rendering/benchmark.py`
- Create: `lab/reports/strategy-policy-comparison.md`
- Create: `lab/reports/spqr-spike.md`
- Create: `lab/reports/renderer-baseline.md`

**Interfaces:**
- Corpus rows identify provenance, request, current plan, candidates, trace and ambiguity.
- Policies accept a candidate tuple and return a deterministic choice without calling production planner mutation.

- [x] Write corpus-count and planner-unchanged tests first.
- [x] Generate 200 supported DC cases and at least 30 named deliberate probes, all outside holdout.
- [x] Compare current, target-first, complexity and lexicographic policies; classify SPQR as HOLD because no safe mapping was established.
- [x] Render 12 circuits through Schemdraw and retain SVG artifacts; document that comparative layout metrics remain unavailable.
- [x] Run report generators and record research outputs.

### Task 5: Add pure features and current candidate enumeration

**Files:**
- Create: `src/kirchhoff/domain/didactic/features.py`
- Create: `src/kirchhoff/domain/didactic/candidates.py`
- Modify: `src/kirchhoff/domain/didactic/__init__.py`
- Create: `tests/test_didactic_features.py`
- Create: `tests/test_didactic_candidates.py`

**Interfaces:**
- `extract_circuit_features(ir, request) -> CircuitFeatures`
- `enumerate_strategy_candidates(ir, request) -> tuple[StrategyCandidate, ...]`
- Transform candidates reuse `observation_effect`; nodal candidates exist only when the current plan supports nodal analysis.

- [x] Write a failing behavioral test for each public pure function and watch it fail.
- [x] Implement only fields independently defined by the lab; add no ranking/score or future technique.
- [x] Add static AST/import boundary tests and P1-L equality regression fixtures.
- [x] Run focused then full suite with coverage; commit after green evidence.

### Task 6: Close evidence and publish a reviewable candidate

**Files:**
- Create: `.github/workflows/research-lab.yml`
- Create: `lab/reports/centaur-comparison.md`
- Create: `lab/reports/manualintegrate-pattern.md`
- Create: `lab/reports/competitive-landscape.md`
- Create: `lab/reports/perception-sources.md`
- Modify: `docs/current-state.md`

**Interfaces:**
- Core CI remains lean; research CI has a separately pinned scientific stack.
- Documentation answers every P1-M0 research question and labels evidence versus unresolved issues.

- [x] Update the P1-L status wording only after its immutable baseline regression passes.
- [x] Run core and research commands, inspect raw logs, and re-read the branch/diff.
- [ ] Push the blocked candidate only after a final reviewer-oriented commit; create a draft PR and append a capability receipt.

## Self-review

- Every requested experiment has a durable report or an explicit unavailable/HOLD result.
- No task grants external authority or crosses `domain/` dependency boundaries.
- The only production interfaces are features and candidate enumeration; none ranks or changes `pianifica`.
- The final protocol requires evidence for all counts, not coverage alone.
