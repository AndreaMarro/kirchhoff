# P1-M0 strategy research protocol

P1-M0 is an evidence checkpoint before any change to the didactic planner.  It
does **not** introduce a score, weights, a learned chooser, graph search, a
solver fallback, or a new transformation.  The current `pianifica` output is
an immutable comparison baseline.

## Questions and measurements

The corpus records 200 topology-diverse generated supported DC circuits and 30
named deliberate probes. Each row carries provenance, topology fingerprint,
IR/request, executable transforms, P1-J observation effect, pure features,
current plan, P1-L trace, final certification, and an ambiguity flag. No
holdout data is read.

`peripheral_work` is measured conservatively: a chosen transform is peripheral
only when it does not touch the requested component and does not reduce the
current nodal-unknown or analytical-equation count. The report keeps the facts
separately, so a pedagogically useful identity-preserving simplification is not
silently labelled a defect.

Five offline deterministic policies consume the same candidate tuple:

1. current: exactly reproduces `pianifica` via explicit plan/action identity;
2. direct-nodal: chooses executable nodal analysis, otherwise a deterministic
   admissible transform; it is an extreme baseline, not a recommendation;
3. target-first: target relevance and current analytical facts, without a
   transform-before-nodal discriminator;
4. complexity: resulting equation/unknown/component facts before a deterministic
   tie-break;
5. lexicographic: admissibility, target relevance, complexity, structural
   simplification, canonical tie-break.

They are lab functions only.  Neither the policy result nor any external graph
feature changes `pianifica`.

## Production boundary allowed after evidence

Only two pure, immutable descriptions may cross into the domain:

- `CircuitFeatures`, computed with Kirchhoff-native topology and capabilities;
- `StrategyCandidate`, enumerating only currently executable certified
  transformations plus currently executable nodal analysis, independently of
  whichever candidate the frozen planner currently chooses.

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
and negative results. An unsupported external result is recorded as such; it is
not discarded or converted into a Kirchhoff failure. The P1-M0 feature/candidate
contract fails closed for non-DC, non-voltage/current, malformed Request and
non-didactic component inputs; it does not silently advertise AC/transient
strategy choices.
