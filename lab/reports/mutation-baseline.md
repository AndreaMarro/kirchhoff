# Mutation baseline — P1-M0

Targeted modules: `didactic/observation.py`, `didactic/orchestrate.py`,
`truthfulness.py`, `verify.py`. Mutmut 3.4.0 was run twice: first on CPython
3.13, then isolated on CPython 3.12 with the relevant test selection and copied
`src/`/`lab/` support paths.

The run is **inconclusive**. CPython 3.13 produced 1,116 `segfault` outcomes
and 55 `no tests`; the CPython 3.12 attempt reproduces the mutant-process
segfault class after valid instrumentation collection. These are runner failures,
not killed mutants, and must not be counted as coverage or as zero survivors.

| Status | Count | Classification |
|---|---:|---|
| generated | 1,171 | raw mutmut baseline |
| killed | 0 valid | none established |
| survived | 0 valid | none established |
| no tests | 55 | test-selection/mutmut mapping debt |
| segfault | 1,116 | runner infrastructure failure |
| high semantic survivors | **unknown** | gate not passed |

No semantic survivor can be classified equivalent/harmless/low/high without a
valid executing mutant. Required follow-up before P1-M: freeze a compatible
mutation runner (or justified alternative), verify a known mutant is killed,
then classify every surviving mutation affecting refusal/success, Request
lineage, exact comparison, Claim issuance, trace canonicity or resolved quantity.
The requested **HIGH semantic survivors = 0** gate is therefore **NO-GO**.
