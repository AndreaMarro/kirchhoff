"""kirchhoff-eval — costruisce l'insieme di riferimento e produce le metriche."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import metrics, reference_set

COVERAGE = (
    "PARZIALE — insieme di riferimento STRUTTURATO, quattro classi di dominio "
    "(dc_resistive, transient, ac_sinusoidal, three_phase). "
    "VSR e SER coprono la catena a valle dell'IR (solver, Trasformazioni, Verifica) "
    "e NON l'estrazione da immagine, dove nasce quasi tutto l'errore silenzioso. "
    "Non leggere questi numeri come SER complessivo."
)


def cmd_build(a: argparse.Namespace) -> int:
    cases, rejected = reference_set.build(a.n, seed0=a.seed, depth=a.depth)
    counts = reference_set.write(cases, Path(a.out), split=a.split)
    per_classe: dict[str, int] = {}
    for c in cases:
        per_classe[c.domain_class] = per_classe.get(c.domain_class, 0) + 1
    print(json.dumps({
        "ok": True, "generati": len(cases), "scartati_in_verifica": len(rejected),
        "per_classe": per_classe, "split": counts, "out": str(a.out), "coverage": COVERAGE,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    allow = a.allow_holdout or os.environ.get(reference_set.HOLDOUT_ENV) == "1"
    try:
        cases = reference_set.load(Path(a.root), a.split, allow_holdout=allow)
    except reference_set.HoldoutAccessError as e:
        print(json.dumps({"ok": False, "errore": str(e)}, indent=2, ensure_ascii=False))
        return 2
    if not cases:
        print(json.dumps({"ok": False, "errore": f"nessun caso in {a.root}/{a.split}"},
                         indent=2, ensure_ascii=False))
        return 2
    rep = metrics.run(cases, metrics.reference_solver, COVERAGE)
    print(json.dumps({"ok": True, "split": a.split, **rep.as_dict()},
                     indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kirchhoff-eval")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="costruisce l'insieme di riferimento verificato")
    b.add_argument("--n", type=int, default=60)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--depth", type=int, default=3)
    b.add_argument("--split", type=float, default=0.6)
    b.add_argument("--out", default="reference-set")
    b.set_defaults(fn=cmd_build)

    r = sub.add_parser("report", help="misura VSR/SER/QPS/TTV")
    r.add_argument("--root", default="reference-set")
    r.add_argument("--split", choices=("dev", "holdout"), default="dev")
    r.add_argument("--allow-holdout", action="store_true")
    r.set_defaults(fn=cmd_report)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
