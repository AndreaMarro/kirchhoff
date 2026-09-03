# Renderer benchmark — P1-M0

This is a narrow real comparison, not a new autolayout. Six DC single-mesh
circuits (`mesh-02` through `mesh-07`) are rendered with the same component
identities and topology by Kirchhoff and Schemdraw 0.23. Kirchhoff uses
`layout_a_maglia()` for the 2-, 3- and 4-node cases; the longer cases use three
explicit immutable `LayoutIR` fixtures because the product deliberately refuses
to generalise its single-mesh layout when a bend would transit another node.

The benchmark creates rather than tracks SVGs. `run_renderer_benchmark()` writes
12 static SVGs, eight certified VisualStep SVGs and
`renderer-benchmark-manifest.json`; research CI archives them as
`renderer-benchmark-artifacts.zip`.

| Case | Kirchhoff bbox / aspect | Kirchhoff crossings / overlap / intrusion / bends | Schemdraw bbox / aspect | Schemdraw crossings | Comparison status |
|---|---|---|---|---|---|
| mesh-02 | `(-108,0)–(112,200)` / 11/10 | 0 / 0 / 0 / 4 | `(-100,0)–(100,200)` / 1 | 0 | comparable topology/crossing/bbox |
| mesh-03 | `(0,-8)–(200,200)` / 25/26 | 0 / 0 / 0 / 4 | `(0,0)–(200,200)` / 1 | 0 | comparable topology/crossing/bbox |
| mesh-04 | `(-8,-12)–(208,208)` / 54/55 | 0 / 0 / 0 / 0 | `(0,0)–(200,200)` / 1 | 0 | comparable topology/crossing/bbox |
| mesh-05 | `(0,0)–(208,200)` / 26/25 | 0 / 0 / 0 / 8 | `(0,0)–(200,200)` / 1 | 0 | comparable topology/crossing/bbox |
| mesh-06 | `(0,-8)–(200,208)` / 25/27 | 0 / 0 / 0 / 8 | `(0,0)–(200,200)` / 1 | 0 | comparable topology/crossing/bbox |
| mesh-07 | `(0,-8)–(208,248)` / 13/16 | 0 / 0 / 0 / 8 | `(0,0)–(200,240)` / 5/6 | 0 | comparable topology/crossing/bbox |

Kirchhoff's bounding box is scene geometry (bodies, terminals and wires);
Schemdraw's is the frozen topology coordinate frame. This is a reported
definition difference, not a claim that one renderer is more compact.

`component_overlap`, `wire_body_intrusion`, labels and bends are **NOT
COMPARABLE** for Schemdraw: its emitted SVG does not expose stable public
symbol/text geometry. Label collisions are likewise not measured for either
renderer because neither exposes exact font metrics. They are not recorded as
zeroes.

## Certified visual-step continuity

Four actual `componi()` pairs are included: one series, one parallel and two
independent chain-series reductions. Their surviving component counts are 1, 1,
2 and 2 respectively. All have maximum and mean surviving-component Manhattan
displacement `0`; that is the existing `applica()` preservation contract observed
on the emitted before/after paths, not a reference-renderer claim. Schemdraw has
no `VisualStep`, `LayoutPatch` or lineage equivalent, so its step displacement is
**NOT COMPARABLE**.

No renderer is replaced, no ELK/netlistsvg adapter is introduced, and this result
does not establish a pedagogical or product rendering winner.
