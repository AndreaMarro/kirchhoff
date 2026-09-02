# Graph features — P1-M0

`GraphView` represents each electrical node as `node:<id>` and each component as
`component:<id>`, with two incidence edges per two-terminal component.  This
avoids the lossy shortcut of placing components directly as edges in a simple
NetworkX graph: parallel `R1`/`R2` remain two graph entities.

The 100-case cross-check asserts the same component count, electrical node
count, connected-region count and native cycle rank (`E - V + regions`) between
Kirchhoff IR and the NetworkX view. Result: **100/100 agreement, 0
disagreements**. Lcapy 1.26 exposes symbolic circuit analysis, not a matching
public topology/`CircuitGraph` API for this subset, so it was deliberately not
misrepresented as a third graph oracle.

Measured lab-only descriptors are: articulation electrical nodes, bridge
components (remove-component connectivity test), cycle rank, biconnected
membership, target-to-action distance, target touch, and before/after component,
node, unknown, equation and simple-supernode deltas.  The production
`CircuitFeatures` keeps only Kirchhoff-native definitions and imports no
NetworkX.

Verdict: retain NetworkX as **ADOPT_NOW laboratory tooling**, but do not promote
biconnected or target-distance facts into a strategy invariant until the corpus
has materially more diverse topologies.
