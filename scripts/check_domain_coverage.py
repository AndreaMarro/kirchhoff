#!/usr/bin/env python3
"""Copertura globale senza regressioni e `domain/` al 100%.

Il dominio e' puro — nessuna I/O, nessun orologio, nessuna casualita'. Un ramo
non coperto li' dentro o e' morto o e' un test mancante: in entrambi i casi si
sistema, non si tollera. Il resto del codice vive sotto la soglia globale.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FLOOR = {"src/kirchhoff/domain/": 100.0}
BASELINE = Path(__file__).resolve().parents[1] / "docs/quality/coverage-baseline.json"


def _conteggi(covered: object, total: object) -> tuple[int, int]:
    if (type(covered) is not int or type(total) is not int
            or total < 0 or not 0 <= covered <= total):
        raise ValueError("Conteggi di copertura non validi.")
    return covered, total


def _totali(summary: dict) -> tuple[int, int]:
    lines, statements = _conteggi(summary.get("covered_lines"), summary.get("num_statements"))
    branches, all_branches = _conteggi(summary.get("covered_branches"), summary.get("num_branches"))
    return lines + branches, statements + all_branches


def _globale(data: dict, baseline: dict) -> str:
    if data.get("meta", {}).get("branch_coverage") is not True:
        raise ValueError("Serve un report con copertura dei rami abilitata.")
    if baseline.get("schema") != "kirchhoff-coverage-baseline.v1":
        raise ValueError("Schema della baseline di copertura non valido.")
    previous, previous_total = _conteggi(baseline.get("covered"), baseline.get("total"))
    covered, total = _totali(data.get("totals", {}))
    if total == 0 or previous_total == 0:
        raise ValueError("Report o baseline di copertura vuoti.")
    if covered * 100 < 95 * total:
        raise ValueError("Copertura globale inferiore al minimo del 95%.")
    # Confronto razionale: una percentuale arrotondata non può nascondere un calo.
    if covered * previous_total < previous * total:
        raise ValueError(f"Copertura globale in regressione: {100 * covered / total:.6f}% "
                         f"< baseline {100 * previous / previous_total:.6f}%.")
    return f"Copertura globale {100 * covered / total:.6f}%: minimo e baseline rispettati."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    args = parser.parse_args()
    try:
        data = json.loads(Path("coverage.json").read_text())
        baseline = json.loads(args.baseline.read_text())
        global_status = _globale(data, baseline)
        files = data["files"]
        if not isinstance(files, dict) or not any(name.startswith(tuple(FLOOR)) for name in files):
            raise ValueError("Il report non contiene file del dominio.")
        bad = []
        for name, f in files.items():
            if name.startswith(tuple(FLOOR)):
                covered, total = _totali(f["summary"])
                if covered != total or f.get("missing_lines") or f.get("missing_branches"):
                    bad.append(f"{name}: dominio non completamente coperto — "
                               f"righe scoperte {f.get('missing_lines', [])} · "
                               f"rami scoperti {f.get('missing_branches', [])}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"GATE COPERTURA RIFIUTATO: {exc}")
        return 1
    if bad:
        print("SOGLIA DIFFERENZIALE VIOLATA")
        for b in bad:
            print(" ", b)
        return 1
    print(global_status)
    print("domain/ al 100%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
