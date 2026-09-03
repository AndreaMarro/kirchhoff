# manualintegrate pattern — P1-M0

SymPy's manual-integration architecture separates an information object, rules,
substeps, an ordered rule application and final evaluation. The conceptual map
for a future Kirchhoff layer is:

| manualintegrate | possible Kirchhoff analogue |
|---|---|
| `IntegralInfo` | `CircuitIR + Request` |
| rule applicability | `StrategyCandidate` + `ObservationEffect` |
| substeps | certified transforms / analytical steps |
| ordered rules | explicit deterministic policy stack |
| final evaluation | existing planner/executor/TruthfulnessGate |

The recommended P1-M abstraction, if an owner approves after a stronger corpus,
is a bounded deterministic **rule tree / lexicographic policy stack**. A weighted
flat `StrategyScore` is not justified: it would encode unowned pedagogical
preferences, lacks a frozen oracle, and hides ties. SymPy is not a production
dependency; this is architecture study only. Source:
[SymPy integration documentation](https://docs.sympy.org/latest/modules/integrals/integrals.html).
