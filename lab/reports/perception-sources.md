# Perception sources and datasets — P1-M0

| Source | Purpose / evidence | License and product use | Verdict |
|---|---|---|---|
| AITEE | 831 circuit images, 11 labels; later perception evaluation | Apache-2.0 stated upstream; verify provenance before any corpus ingestion | HOLD, no vendoring/training |
| CircuitReason-1K | recent circuit-reasoning methodology | code/data license not verified | HOLD, methodology only; no copying |
| CircuitPile / CircuitHub | potential circuit corpus | commercial-training terms/provenance unresolved | REJECT pending exact licence |
| Razavi-bench | analog reasoning benchmark | code Apache-2.0, benchmark content research/non-commercial | HOLD, local methodology only |

No model training, large dataset vendoring, or perception runtime was started.
The first landing slice should show a manual circuit entry/import path and
inspectable verified trace before making any photo-recognition claim. Sources:
[AITEE](https://github.com/CKnievel/aitee-dataset),
[CircuitReason-1K](https://arxiv.org/abs/2608.09374), and
[Razavi-bench](https://github.com/Arcadia-1/razavi-bench).
