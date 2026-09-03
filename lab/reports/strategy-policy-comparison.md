# Strategy policy comparison — P1-M0

This is an offline comparison only: no result feeds `pianifica`. The corpus is
200 public, bounded, topology-diverse DC circuits plus 30 deliberately named
probes. Every terminal result was certified by the unchanged core.

The generated corpus contains 200 distinct value-independent topology
fingerprints. Its family distribution is 129 nested series-parallel depth-3,
55 nested series-parallel depth-2, 13 pure series/parallel across depths 1–3,
and 3 single-resistor depth-2 cases. The 30 named probes contain 27 distinct
fingerprints. The three declared repetitions deliberately revisit the same
topology under a distinct observation question: probes 00/06, 01/07 and 02/05.

`peripheral_work` is conservative: a selected transform that does not touch the
target and does not reduce the current nodal-unknown count or analytical
equation count. It is a structural fact, not a verdict on pedagogical value.
`directly_nodal` means that nodal analysis was the **first** selected technique,
not merely the terminal technique after reductions. `full-run divergence`
compares the complete technique/operation/operand trace to `current`.

## Generated corpus (200 cases)

| Policy | First-step / full divergence | Direct nodal | Mean / median transforms | Peripheral | Identity | Retarget | Mean final unknowns | Mean analytical actions | Refusal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current | 0 / 0 | 3 | 6.64 / 6 | 417 | 1,071 | 257 | 1.87 | 3.87 | 0 |
| complexity | 0 / 136 | 3 | 6.64 / 6 | 417 | 1,071 | 257 | 1.87 | 3.87 | 0 |
| direct-nodal | 197 / 197 | 200 | 0 / 0 | 0 | 0 | 0 | 5.14 | 7.14 | 0 |
| target-first | 197 / 197 | 200 | 0 / 0 | 0 | 0 | 0 | 5.14 | 7.14 | 0 |
| lexicographic | 197 / 197 | 200 | 0 / 0 | 0 | 0 | 0 | 5.14 | 7.14 | 0 |

`complexity` agrees on every first step yet diverges in 136 complete traces;
equal immediate complexity facts do not establish an identical multi-step
policy. It also has the same aggregate counts as `current`, so this experiment
does not justify changing the frozen production preference.

## Deliberate probes (30 cases)

| Policy | First-step / full divergence | Direct nodal | Mean / median transforms | Peripheral | Identity | Retarget | Mean final unknowns | Mean analytical actions | Refusal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current | 0 / 0 | 3 | 3.80 / 2 | 29 | 82 | 32 | 1.47 | 3.47 | 0 |
| complexity | 0 / 10 | 3 | 3.80 / 2 | 29 | 82 | 32 | 1.47 | 3.47 | 0 |
| direct-nodal | 27 / 27 | 30 | 0 / 0 | 0 | 0 | 0 | 3.37 | 5.37 | 0 |
| target-first | 27 / 27 | 30 | 0 / 0 | 0 | 0 | 0 | 3.37 | 5.37 | 0 |
| lexicographic | 27 / 27 | 30 | 0 / 0 | 0 | 0 | 0 | 3.37 | 5.37 | 0 |

All 230 corpus/probe inputs under each of the five policies (1,150 runs) ended
with a core `VERIFIED` claim and zero refusals. The extreme nodal, target-first
and lexicographic baselines choose
nodal immediately under their declared tuples, yielding fewer transforms but
more final unknowns and analytical actions. This is evidence against claiming
an automatic simplification benefit from either extreme.

## Decision

The data record observable trade-offs, not pedagogical labels or owner-selected
preference. `StrategyScore`, weighted ranking, learning, search and production
planner changes remain unjustified. Any P1-M proposal requires owner-approved
pedagogical criteria and a fresh decision gate; P1-M0 closes with the planner
unchanged.
