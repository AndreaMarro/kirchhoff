# Proof Demo 0.1 — branch ledger (SESSION 1 start)

BASE_SHA: 98f73f1184f34f50e030372efaa2b7d91e678cce
BASE_BRANCH: work/student-vertical-slice-0.1-phase1
NEW_BRANCH: work/proof-demo-0.1
REMOTE_MAIN: 723f870462d7d52cbd4de7d9d0d2fa771d0a080d
MIXED_P1M: 16eb00ee4550e7ff2205578dbf43251d594b28e3 (NOT used as base; PR #7 stays untouched)

## Forensics (refreshed 2026-09-03, not trusted blindly)
- LOCAL_HEAD (pre-branch): 16eb00ee4550e7ff2205578dbf43251d594b28e3
- REMOTE_MAIN: 723f870462d7d52cbd4de7d9d0d2fa771d0a080d (matches spec)
- REMOTE_P1L: 98f73f1184f34f50e030372efaa2b7d91e678cce (matches spec)
- REMOTE_P1M: 16eb00ee4550e7ff2205578dbf43251d594b28e3 (matches spec, no STOP)
- DIRTY: clean
- AHEAD/BEHIND local vs origin/work/p1-m0-research-gpt: 0/0
- PR #7: DRAFT, base=work/student-vertical-slice-0.1-phase1, head=work/p1-m0-research-gpt, 15 commits, 97 files (stale body, MERGE NO-GO — left untouched)

## Product dependency check on base
Present on 98f73f1:
- src/kirchhoff/domain/didactic/{planner,capabilities,observation,orchestrate,analytical,derivation,execute,solve,request,plan,kinds}.py
- src/kirchhoff/domain/{ir,transform/engine,truthfulness,verify,validate,refusal}.py
- src/kirchhoff/pipeline/netlist.py (leggi)
Absent (by design, NOT ported blindly):
- lab/ (research-only; must never enter product branch)
- src/kirchhoff/domain/didactic/{candidates,features,nodal_plan,strategy_scope}.py (P1-M0 strategy research; RESEARCH_ONLY for now)
- src/kirchhoff/pipeline/didactic_session.py (provisional composer; REIMPLEMENT as ProofSession later)
- tests/test_didactic_nodal_plan.py (BROKEN: imports lab.strategy.corpus -> networkx; do not port)
- examples/ curated netlists/sessions (will be regenerated from canonical registry in SESSION 5)

## Classification of mixed commits (not cherry-picked)
- 7784fc0 feat(product): curated DC examples... -> MIXED (product fragments + research oracles); REIMPLEMENT selectively, do not cherry-pick
- 16eb00e test(didactic): close DC matrix... -> MIXED + BROKEN boundary (lab import in core test); do not cherry-pick
- 0a05cee, bacc406, 59a595d, d859ea1, 8f3e8f6, 0123e1e, 0a38e41, 8de4c52 -> RESEARCH_ONLY (lab/, tests/test_lab_*)
- 46746c6, 04b1139, b85c4fc, 1aa7747, 111e56b -> REIMPLEMENT (provisional DidacticSession; known before==after, Any, dict-copy issues)

## Session 1 gate
- CORE_CI_GREEN: pending verification on this branch (expected GREEN: no lab imports in tests/)
- RESEARCH_CI_GREEN: N/A on product branch (no lab/); research stays on work/p1-m0-research-gpt
- Next: run local CoV (pip install -e ".[dev]", pytest, check_domain_coverage, check_boundaries), push, open draft PR, record Actions.
