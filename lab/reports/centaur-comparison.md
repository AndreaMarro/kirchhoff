# Centaur comparison — P1-M0

Centaur's useful conceptual pattern is query-aware rewriting: protect the
structure being queried while simplifying surrounding topology. Kirchhoff is
already stronger where it matters for product truth: `ObservationContract`
specifies the observable, `ObservationEffect` fail-closes it, `RequestLineage`
makes a permitted retarget explicit, and `TruthfulnessGate` alone issues the
final verified Claim.

Useful future idea: a reviewable *protected observable* annotation may make the
same intent visible earlier in candidate generation. It must remain derived from
the existing Request/observation contract, not a parallel truth table. Suggested
future transformations are only already-certifiable structural transforms with
explicit observation behavior; no Centaur algorithm is imported.

The upstream repository did not expose a license in the fresh check. Therefore
the legal result is **NO CODE COPYING** and the P1-M0 recommendation is **HOLD**.
Source: [Centaur toolkit](https://github.com/centaur-toolkit/centaur).
