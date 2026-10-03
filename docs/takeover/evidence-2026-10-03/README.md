# Public technical evidence — 2026-10-03

These are original, independently frozen generated circuit corpora and auditors,
plus their recorded results. They contain no private exercise scans or credentials.

- AC port: 71 cases; 62 solved comparisons, 6 conservative refusals and 3 invalid
  input exceptions. The raw library runner remains failing for those exceptions;
  the separate actual HTTP check confirms all three return 422.
- Laplace kernel: 80 cases, 70 solved / 3 refusals / 7 typed errors; 420 complex
  samples, 104 exact analytic identities, 5 pole checks, 3 rejected mutations.
- Additional Laplace served lesson: frozen five-mesh checker failed integrity
  before HTTP; see its execution note. No accepted result for that audit.

Historical runner paths may refer to the original local checkout or staging.
Use their CLI path arguments for reproduction; never overwrite frozen files.
Large raw response streams and private corpus outputs remain local.
Current product test commands and limitations are in the parent delivery report.

Published log copies have trailing whitespace normalized for Git; raw logs remain in the local evidence archive. Frozen oracle, criteria and expected files are byte-identical.
