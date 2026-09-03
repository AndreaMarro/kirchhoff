# Mutation evidence — P1-M0

## Historical mutmut diagnostic (not certification)

Mutmut 3.4.0 was run twice against the P1-M0 target set. CPython 3.13 produced
1,116 `segfault` outcomes and 55 `no tests`; a CPython 3.12 attempt reproduced
the mutant-process segfault class after valid instrumentation collection.

| Status | Count | Classification |
|---|---:|---|
| generated | 1,171 | historical raw mutmut baseline |
| killed / survived | 0 valid | none established |
| no tests | 55 | test-selection/mutmut mapping debt |
| segfault | 1,116 | runner infrastructure failure |

Those are runner failures, not killed mutants and not evidence of zero survivors.
Mutmut is therefore **HOLD / SECONDARY DIAGNOSTIC**. Its report is retained rather
than rewritten as a success.

## Cosmic Ray 8.7.0 primary runner

Cosmic Ray is pinned only in the `research` extra. It uses one persistent SQLite
session per target module, an unmutated `baseline`, `init`, `exec`, `dump` and
`cr-report`; session DBs, text reports, JSON classifications, configuration and
summary are Actions artifacts rather than tracked source files.

The controlled smoke subject has a deliberately dangerous equality predicate.
The local smoke baseline passed; Cosmic Ray generated seven comparison mutants.
The known `== → !=` mutant was **killed** by
`tests/test_cosmic_ray_smoke.py`. The complete smoke outcome was five killed,
two survived, zero incompetent, zero timeout and zero skipped. The two survivors
are retained as survivors; the smoke proves runner execution and reporting, not
complete mutation adequacy.

Target sessions are configured separately for:

1. `didactic/observation.py`
2. `didactic/orchestrate.py`
3. `truthfulness.py`
4. `verify.py`

They run focused deterministic pytest selections with `-x`. The sole operator
filter excludes `core/ReplaceBinaryOperator_BitOr_*`: in these four modules all
`|` occurrences are PEP 604 type annotations, not runtime P1-M0 behavior. All
comparison, conditional, refusal, lineage, claim and exact-value mutations remain
in scope. The generated classification labels every executed mutant; the gate
requires `HIGH semantic survivors == 0` and
`unexplained HIGH-location incompetent == 0` before the manual `mutation.yml`
workflow can be a successful closure artifact.

At this point the smoke is valid, but P1-M0 remains **NO-GO** until the fresh
four-module run on the final SHA is executed, classified and dispatched through
GitHub Actions.
