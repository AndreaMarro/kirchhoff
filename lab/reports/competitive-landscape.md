# Competitive landscape — P1-M0

[CircuitsU](https://www.circuitsu.com/Home) publicly advertises free circuit
tutoring with random problems, answer checking and detailed solutions across
DC/AC/transient analysis, nodal/mesh, superposition, source transformations,
Thevenin/Norton and other topics. That breadth makes the claim “step-by-step
circuit solving alone is a moat” untenable.

| Dimension | Public competitive baseline | Kirchhoff P1-M0 position |
|---|---|---|
| Input | guided exercises / service interface | circuit IR and arbitrary supported netlist |
| Steps | worked steps and feedback | inspectable certified transform/derivation trace |
| Verification | public UX claims; internal method not inspectable here | exact MNA + independent tableau + TruthfulnessGate |
| Query preservation | not evidenced publicly | P1-J observable contract and explicit lineage |
| Visual redraw | public educational interface | renderer remains an open research item |
| Personalization | tutoring workflow | no student model in this checkpoint |

The credible prospective differentiation is not a generic solver: arbitrary
user circuit ingestion, query-aware observable preservation, exact deterministic
certification, proof provenance, redraw after each certified step and an
exportable worked artifact. It is still weak until rendering, input UX and
pedagogical policy are demonstrated. No proprietary exercises were scraped.

The first landing-page vertical slice should therefore lead with “enter a small
DC circuit → choose a requested observable → inspect certified steps and final
exact result”; it should not imply photo recognition, broad AC coverage or a
personalized tutor before evidence exists.
