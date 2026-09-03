# Boundary checker — keep custom

## Spike

Custom: `scripts/check_boundaries.py` — 114 LOC, stdlib-only (`ast`, `pathlib`), gestisce `import X`, `from X import`, `from .. import`, `from kirchhoff import pipeline` → `kirchhoff.pipeline`.

Standard candidati:
- `import-linter` — richiede `setup.cfg` + `importlinter` contract, dipendenza extra, config dichiarativa
- `tach` — Rust binary, `tach.toml`, `tach check`, più pesante, richiede `tach install`

## Comparazione

| Criterio | Custom | import-linter | tach |
|---|---|---|---|
| LOC config | 0 | ~15 | ~10 |
| Install | stdlib | `pip install import-linter` | `cargo`/`pip` |
| Tempo | <0.1s | ~0.3s | ~0.2s |
| Cattura `from ..adapters import x` | sì (aritmetica su `level`) | sì (se configurato) | sì |
| Cattura `import kirchhoff.adapters as a` | sì | sì | parziale |
| Manutenzione | bassa | media (contract) | media |

## Decisione

**KEEP_CUSTOM** — custom è più piccolo, stdlib, già cattura casi reali (`domain/` non importa `pipeline`, `adapters`, `ports`), testato da `tests/test_confini.py`, nessuna dipendenza. Valutare migrazione solo se cresce complessità a >200 LOC o servono layer multipli.

Spike effimero eseguito: `uv run --with import-linter import-linter --help` → richiede contract; non installato permanentemente.
