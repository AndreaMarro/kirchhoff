# Renderer baseline — P1-M0

Twelve SVG reference artifacts were produced with Schemdraw 0.23 under
`lab/rendering/artifacts/` (112,901 bytes total): series, parallel, local/far
peripheral reduction, simultaneous reductions, target-distance variants,
unknown-count variants, bridge, trivial nodal, multi-step ladder and retarget.
They are deterministic, visual inspection inputs; the test verifies all 12 are
validly emitted.

| Renderer | Cases | What is measured | Result / limitation |
|---|---:|---|---|
| Schemdraw 0.23 | 12 | symbol/label SVG emission | 12/12 artifacts, linear reference strips |
| Kirchhoff renderer | 0 comparable | crossings, overlap, displacement require a concrete LayoutIR/step input adapter | not replaced, **HOLD** |
| ELK/netlistsvg | 0 | automatic layout baseline | research candidate, adapter not justified in P1-M0 |
| Circuitikz | 0 | TeX reference | toolchain spike deferred |

The Schemdraw strips intentionally do not claim to preserve full circuit
topology; therefore crossing, bend, overlap, target-visibility and
step-to-step displacement values are **not measured**, rather than recorded as
fictional zeroes. The controlled finding is that a meaningful renderer
comparison needs a frozen `CircuitIR → LayoutIR/renderer-input` adapter and a
visual metric oracle. No production renderer was replaced.
