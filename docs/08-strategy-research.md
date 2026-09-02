# P1-M0 strategy research protocol

P1-M0 is an evidence checkpoint before any change to the didactic planner.  It
does **not** introduce a score, weights, a learned chooser, graph search, a
solver fallback, or a new transformation.  The current `pianifica` output is
an immutable comparison baseline.

## Questions and measurements

The corpus records 200 generated supported DC circuits and 30 named,
hand-designed probes.  Each row carries provenance, IR/request, executable
transforms, P1-J observation effect, pure features, current plan, P1-L trace,
final certification, and an ambiguity flag.  No holdout data is read.

`peripheral_work` is measured conservatively: a chosen transform is peripheral
only when it neither touches the requested component, nor decreases its
structural target distance, nor reduces the final nodal unknown/equation count.
The report keeps the three facts separately, so a pedagogically useful
identity-preserving simplification is not silently labelled a defect.

Four offline deterministic policies consume the same candidate tuple:

1. current: first observation-contributing executable transform;
2. target-first: target relevance before canonical order;
3. complexity: greatest predicted equation/unknown reduction before canonical order;
4. lexicographic: admissibility, target relevance, complexity, structural
   simplification, canonical tie-break.

They are lab functions only.  Neither the policy result nor any external graph
feature changes `pianifica`.

## Production boundary allowed after evidence

Only two pure, immutable descriptions may cross into the domain:

- `CircuitFeatures`, computed with Kirchhoff-native topology and capabilities;
- `StrategyCandidate`, enumerating only currently executable certified
  transformations plus currently executable nodal analysis.

They expose facts; they do not rank, select, execute, create claims, or alter
request lineage.  The AST boundary test rejects imports of research packages
from `src/kirchhoff/domain/`.

## Decision criteria

P1-M is an owner decision, not automatic promotion from a benchmark.  A future
model should be a deterministic **lexicographic policy stack or bounded rule
tree**, only if the corpus shows a stable improvement and the owner defines
pedagogical preference.  A weighted `StrategyScore` has no frozen oracle or
owner-selected weights and is therefore not justified by P1-M0 alone.

The remaining research reports contain raw counts, all differential triage,
and negative results.  An unsupported external result is recorded as such; it
is not discarded or converted into a Kirchhoff failure.
