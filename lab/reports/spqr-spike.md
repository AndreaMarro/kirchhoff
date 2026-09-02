# SPQR spike — P1-M0

`imacat/spqrtree` is Apache-2.0 but alpha/young. The time-boxed P1-M0 result is
**HOLD**: no dependency was installed and no production representation was
introduced. The available public API and documentation do not establish a
stable, lossless mapping from Kirchhoff's typed two-terminal IR (including
parallel elements, sources and a requested observable) to an SPQR graph and
back.

The proposed probe set remains useful for a future isolated spike: series
ladder, parallel structure, ladder, bridge, mostly-rigid circuit, peripheral
reduction, and target inside/outside a rigid core. Potential descriptors are
`rigid_core_size`, `target_in_rigid_core`, distance to rigid region, serial and
parallel region counts. None are measured facts yet, and none enter the domain.

Recommendation: retry only after a frozen adapter mapping and test oracle are
defined; otherwise topology semantics can be lost while appearing more
sophisticated. Source: [spqrtree upstream](https://github.com/imacat/spqrtree).
