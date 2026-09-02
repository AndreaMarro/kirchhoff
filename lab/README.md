# P1-M0 research laboratory

`lab/` is an evidence-producing boundary, not a second circuit engine.
Everything here may challenge Kirchhoff, produce a reference rendering, or
measure a candidate policy.  Nothing here may mint a `Claim`, grant
`VERIFIED`, decide `RequestLineage`, or be imported by `src/kirchhoff/domain/`.

## Reproducibility

```bash
uv sync --extra research
uv run --extra research --with pytest --with pytest-cov python -m pytest tests/test_lab_oracles.py --no-cov
```

The pinned research stack is Lcapy 1.26, NetworkX 3.6.1, Schemdraw 0.23 and
mutmut 3.4.0.  Hypothesis 6.167.0 is a normal development dependency.  The
ngspice adapter calls an already-installed `ngspice` executable directly; its
float tolerance belongs only to this laboratory.

## Layout

- `fixtures/`: bounded hand-authored and generated DC cases; never holdout data.
- `oracles/`: non-authoritative Lcapy and ngspice adapters.
- `graph/`: a lossless NetworkX incidence view.
- `strategy/`: corpus and offline policy experiments.
- `rendering/`: reference renderer measurements and SVG artifacts.
- `reports/`: immutable-enough checkpoint evidence, including unsupported or
  held experiments.

The adapter convention is explicit: a two-terminal component is directed from
its first IR terminal to its second.  A component voltage is `V(first) -
V(second)` and a component current is positive from first to second.  Every
adapter mapping has a test before it appears in a bulk corpus.

## Non-goals

This checkpoint does not alter `pianifica`, execution, orchestration,
truthfulness, `Claim`, or `Request` semantics.  It does not add
`StrategyScore`, external runtime authority, a solver fallback, a dataset, or
a frontend.  A result that disagrees with Kirchhoff is triage input, never a
silent replacement of its exact result.
