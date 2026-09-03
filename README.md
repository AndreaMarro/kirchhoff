# Kirchhoff

Risolutore di circuiti **verificato**: ogni risposta supera cinque controlli indipendenti prima di essere mostrata (accordo A/B, KCL, KVL, bilancio ΣVI/Tellegen, sanità).

```bash
uv pip install -e .
kirchhoff examples/series/netlist.txt --svg /tmp/series.svg
# 3 bipoli · solver dc · verificato da legge dei nodi e legge delle maglie e bilancio di potenza e sanità fisica e accordo fra percorsi indipendenti
```

## Stato attuale (empirico, non roadmap)

P1-L certificato a `98f73f`; P1-M0 localmente consolidato (4-config HIGH 0, domain 100, boundaries green) in branch `work/p1-m0-research-gpt` — non ancora mergiato. `main` è indietro.

| Capability | Stato | Evidenza | Entry point | Test |
|---|---|---|---|---|
| DC resistive sorgenti indipendenti | **CERTIFIED** | `1640 passed`, `verify HIGH 0` | `kirchhoff examples/series/netlist.txt` | `tests/test_verify.py`, `test_il_prodotto_funziona.py` |
| DC sorgenti controllate VCVS/VCCS | **CERTIFIED** | 60 casi VCVS/VCCS, A/B 0 mismatch | `E1 C 0 A 0 2` in netlist | `tests/test_controlled_sources.py:455` |
| Trasformazioni didattiche serie/parallelo | **CERTIFIED** | `CertifiedDidacticRun`, `VisualStep` | `src/kirchhoff/domain/didactic/orchestrate.py` | `tests/test_didactic_orchestrate.py` |
| Nodo diretto (fallback) | **CERTIFIED** | `NodalExecution` | `pipeline/resolve.py:resolve` | `tests/test_truthfulness_nodal.py` |
| SVG deterministico (maglia singola) | **CERTIFIED** | `layout_a_maglia` | `--svg` | `tests/test_il_prodotto_funziona.py:36` |
| PDF | **OPTIONAL** | capability esterna `KIRCHHOFF_CHROMIUM` | `--pdf` | `test_il_pdf_assente_lo_DICE` |
| AC sinusoidale / trifase / transient | **IMPLEMENTED, non VERIFIED per marketing** | `Cyc12` in `Q(ζ12)` passa challenge SymPy effimera (`scripts/research/cyc12_challenge.py` PASS) ma claim `VERIFIED` bloccato fino a oracolo esterno stabile | `src/kirchhoff/domain/exact.py` | `tests/test_controlled_sources.py` + `eval` 36 dev |
| Photo/OCR, autolayout generale | **UNSUPPORTED** | — | — | — |

## Quick start (60s)

```bash
uv pip install -e .
kirchhoff examples/series/netlist.txt --svg /tmp/series.svg   # maglia singola → SVG deterministico
kirchhoff examples/parallel/netlist.txt                       # non-maglia → solve ok, svg non scritto (limite dichiarato)
kirchhoff examples/ladder/netlist.txt --svg /tmp/ladder.svg
kirchhoff examples/bridge/netlist.txt                         # ponte → solve ok, layout manuale richiesto per visual
uv run --with pytest python -m pytest tests -q                # 1640 passed, domain 100, boundaries green
```

5 circuiti curati in `examples/`: `series` (corrente), `parallel` (tensione), `ladder` (multi-step), `bridge` (non riducibile), `nodal` (diretto). Ogni netlist è una riga per bipolo (`R1 b a 100 ohm`).

## Uso

```bash
kirchhoff <netlist> [--svg out.svg] [--pdf out.pdf]
kirchhoff-eval build --n 60 --out /tmp/ref && kirchhoff-eval report --root /tmp/ref --split dev
```

Holdout non leggibile senza `KIRCHHOFF_ALLOW_HOLDOUT=1` o `--allow-holdout` (invalida misura se usato in dev).

## Gate

```bash
uv run python scripts/check_domain_coverage.py   # domain/ al 100%
uv run python scripts/check_boundaries.py        # domain/ non importa fuori da sé (AST)
uv run --with pytest --with pytest-cov python -m pytest   # globale >=95%
```

## PDF — capability esterna, non core

Core è **SVG-only**. PDF è opzionale e richiede Chromium:

```bash
KIRCHHOFF_CHROMIUM=/percorso/chrome kirchhoff examples/series/netlist.txt --pdf /tmp/out.pdf
# oppure
npx playwright install chromium-headless-shell
kirchhoff examples/series/netlist.txt --pdf /tmp/out.pdf
```

Senza capability: `exit 70` con `pdf NON scritto: nessun chromium trovato…` (cross-platform: macOS `~/Library/Caches/ms-playwright`, Linux `~/.cache/ms-playwright`, Windows `%LOCALAPPDATA%/ms-playwright`, + `PATH`).

## Verifica oracolo

Chi genera e chi verifica non condividono implementazione:

| Classe | Costruzione | Verifica |
|---|---|---|
| `dc_resistive` | albero serie/parallelo → tensioni foglie | MNA sull'IR appiattito |
| `ac_sinusoidal` | impedenze `Cyc12` | MNA fasoriale |
| `three_phase` | monofase + rotazione 120° | MNA intera rete |
| `transient` | radici → componenti | MNA singolare in radici |

Aritmetica esatta `Fraction` + `Q(ζ12)` (`src/kirchhoff/domain/exact.py:17-101`, `ζ^12=1`, `√3^2=3`). Challenge indipendente: `uv run --with sympy python scripts/research/cyc12_challenge.py` → **PASS** (14 identità, `det` e `solve_linear` vs SymPy).

## Limitazioni note

- Autolayout solo maglia singola (`layout_a_maglia` grado 2). Circuiti non-maglia risolvono ma non disegnano (serve `LayoutIR` manuale).
- AC/trifase/transient `IMPLEMENTED` ma marketing `VERIFIED` bloccato fino a oracolo esterno pesante (SymPy challenge è solo sanity, non proof).
- Dipendenze: core `dependencies=[]`, PDF è `KIRCHHOFF_CHROMIUM` esterno, research (`sympy`, `lcapy`, `ngspice`, `schemdraw`) solo `pip install -e ".[research]"`.

## Sviluppo

```bash
uv run python scripts/check_boundaries.py
uv run python scripts/check_domain_coverage.py
uv run --with pytest --with pytest-cov python -m pytest
uv run --with sympy python scripts/research/cyc12_challenge.py
```

## Attribuzioni

Il materiale esterno usato e le sue licenze sono in `docs/01-fonti-esterne.md`.
