#!/usr/bin/env python3
"""Soglia differenziale: `domain/` deve stare al 100%.

Il dominio e' puro — nessuna I/O, nessun orologio, nessuna casualita'. Un ramo
non coperto li' dentro o e' morto o e' un test mancante: in entrambi i casi si
sistema, non si tollera. Il resto del codice vive sotto la soglia globale.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FLOOR = {"src/kirchhoff/domain/": 100.0}


def main() -> int:
    data = json.loads(Path("coverage.json").read_text())
    bad = []
    for name, f in data["files"].items():
        for prefix, floor in FLOOR.items():
            if name.startswith(prefix):
                pct = f["summary"]["percent_covered"]
                if pct < floor:
                    bad.append(
                        f"{name}: {pct:.1f}% < {floor}% — "
                        f"righe scoperte {f['missing_lines']} · "
                        f"rami scoperti {f.get('missing_branches', [])}"
                    )
    if bad:
        print("SOGLIA DIFFERENZIALE VIOLATA")
        for b in bad:
            print(" ", b)
        return 1
    print("domain/ al 100%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
