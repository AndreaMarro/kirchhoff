# Strategy policy comparison — P1-M0

Corpus: 200 bounded public DC cases (50 each of series, parallel,
current-source and floating-source value families) plus 30 named deliberate
probes. Every policy is deterministic and lab-only; every terminal value was
certified by the existing core. `current` reproduces the planner's first
admissible candidate exactly.

`peripheral_work` is deliberately conservative: a selected transform that does
not touch the target **and** does not reduce either current nodal-unknown count
or current analytical equation count. This measures wasted local structural
work; it does not call a pedagogically explanatory identity step a defect.

| Policy | Generated divergence from current | Mean / median transforms | Peripheral | Identity | Retarget | Mean final unknowns | Mean analytical actions | Refusal | Stable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current | 0/200 | 0.25 / 0 | 0 | 0 | 50 | 1.25 | 3.25 | 0 | yes |
| target-first | 0 first-step choices on generated corpus | 0.25 / 0 | 0 | 0 | 50 | 1.25 | 3.25 | 0 | yes |
| complexity | 0 first-step choices on generated corpus | 0.25 / 0 | 0 | 0 | 50 | 1.25 | 3.25 | 0 | yes |
| lexicographic | 0 first-step choices on generated corpus | 0.25 / 0 | 0 | 0 | 50 | 1.25 | 3.25 | 0 | yes |

The 30 probes yield 43 transforms: 12 conservative-peripheral, 26 identity and
17 retarget; all 30 finish VERIFIED. One probe (`series-periphery`) changes
the first choice under target-first/lexicographic, from `serie(R1,R2)` to
`serie(R2,R3)`. It is a useful falsification example, not sufficient evidence
that either policy is pedagogically better.

Answers to the strategy questions: the generated corpus observes 0% peripheral
work and 0% identity-before-target behaviour, but its four topology families
are too repetitive to generalize; target distance has no predictive result yet;
component reduction does not prove equation reduction; probe-level examples do
show component reduction without a locally lower equation count. SPQR has no
measured rigidity feature yet. **StrategyScore is not justified.**

Recommended P1-M, only after owner approval: broaden a frozen, topology-diverse
corpus and define pedagogical labels; then evaluate a bounded rule tree or
lexicographic stack, never unowned weighted sums.
