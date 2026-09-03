"""`kirchhoff` — il comando che rende usabile il prodotto.

Legge una netlist e la consegna a `resolve`. Non risolve da sé: lo spine è
l'unico ingresso, e il CLI è un adattatore di processo.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
from fractions import Fraction

from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve


def _decimale(f: Fraction, cifre: int = 4) -> str:
    """Il valore leggibile ACCANTO a quello esatto, mai al suo posto."""
    return f"{float(f):.{cifre}g}"


def _chromium() -> pathlib.Path | None:
    import os
    import shutil
    # 1. capability esplicita via env var
    env = os.environ.get("KIRCHHOFF_CHROMIUM")
    if env:
        p = pathlib.Path(env)
        if p.is_file():
            return p
    # 2. PATH (chromium, google-chrome, chromium-browser)
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome-headless-shell"):
        found = shutil.which(name)
        if found:
            return pathlib.Path(found)
    # 3. playwright cache cross-platform
    candidates = [
        pathlib.Path.home() / "Library/Caches/ms-playwright",  # macOS
        pathlib.Path.home() / ".cache/ms-playwright",  # Linux
        pathlib.Path.home() / "AppData/Local/ms-playwright",  # Windows
    ]
    for base in candidates:
        if not base.is_dir():
            continue
        for d in sorted(base.glob("chromium*"), reverse=True):
            for p in d.rglob("chrome-headless-shell"):
                if p.is_file():
                    return p
            for p in d.rglob("chrome"):
                if p.is_file():
                    return p
    return None


def in_pdf(svg: str, dove: pathlib.Path) -> None:
    """Stampa l'SVG in PDF con un browser già installato (capability esterna)."""
    chrome = _chromium()
    if chrome is None:
        raise RuntimeError(
            "nessun chromium trovato per il PDF. Imposta KIRCHHOFF_CHROMIUM=/percorso/chrome "
            "oppure installa con `npx playwright install chromium-headless-shell`. "
            "Il core resta SVG-only: il PDF è capability opzionale.")
    html = dove.with_suffix(".stampa.html")
    html.write_text(
        f'<!doctype html><style>@page{{margin:12mm}}'
        f'body{{margin:0;display:flex;justify-content:center}}'
        f'svg{{width:100%;height:auto}}</style><body>{svg}',
        encoding="utf-8")
    try:
        subprocess.run(
            [str(chrome), "--headless", "--disable-gpu", "--no-sandbox",
             f"--print-to-pdf={dove}", "--no-pdf-header-footer",
             f"file://{html.resolve()}"],
            check=True, capture_output=True, timeout=60)
    finally:
        html.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(
        prog="kirchhoff",
        description="Risolve un circuito, lo verifica e lo disegna.")
    a.add_argument("netlist", type=pathlib.Path, help="il circuito, una riga per bipolo")
    a.add_argument("--svg", type=pathlib.Path, help="dove scrivere il disegno")
    a.add_argument("--pdf", type=pathlib.Path, help="dove scrivere il PDF")
    n = a.parse_args(argv)

    if not n.netlist.is_file():
        print(f"{n.netlist}: non esiste", file=sys.stderr)
        return 66
    try:
        circuito = leggi(n.netlist.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"netlist: {e}", file=sys.stderr)
        return 65

    esito = resolve(circuito)
    if isinstance(esito, Refusal):
        print(f"RIFIUTATO — {esito}", file=sys.stderr)
        return 3
    if isinstance(esito, Failure):
        print(f"GUASTO — {esito}", file=sys.stderr)
        return 70
    if not isinstance(esito, Solved):
        print(f"GUASTO — esito inatteso {type(esito)!r}", file=sys.stderr)
        return 70

    print(f"{len(circuito.components)} bipoli · {len(circuito.nodes)} nodi · "
          f"solver {esito.solver} · verificato da {' e '.join(esito.verifiche)}\n")
    largo = max(len(c.id) for c in circuito.components)
    for c in sorted(circuito.components, key=lambda c: c.id):
        v = esito.soluzione.get(c.id, {})
        tensione, corrente = v.get("voltage"), v.get("current")
        if tensione is None or not isinstance(tensione, Fraction):
            continue
        print(f"  {c.id:<{largo}}  V = {str(tensione):>10}  = {_decimale(tensione):>9} V"
              f"   I = {str(corrente):>10}  = {_decimale(corrente):>9} A")

    if circuito.requests:
        print()
        for r in circuito.requests:
            v = esito.soluzione.get(r.target, {}).get(r.quantity)
            if v is None:
                print(
                    f"GUASTO — Solved senza {r.quantity} di {r.target}: "
                    "lo spine non doveva pubblicare",
                    file=sys.stderr)
                return 70
            extra = f"  ({_decimale(v)})" if isinstance(v, Fraction) else ""
            print(f"  chiesto: {r.quantity} di {r.target} = {v}{extra}")

    if n.svg:
        if not esito.svg:
            print("  disegno NON scritto: il circuito non è una maglia sola "
                  "e l'autolayout generale non è sul percorso", file=sys.stderr)
        else:
            n.svg.write_text(esito.svg, encoding="utf-8")
            print(f"\n  disegno: {n.svg}")
    if n.pdf:
        if not esito.svg:
            print("  pdf NON scritto: manca il disegno certificato", file=sys.stderr)
            return 70
        try:
            in_pdf(esito.svg, n.pdf)
            print(f"  pdf:     {n.pdf}")
        except (RuntimeError, subprocess.SubprocessError) as e:
            print(f"  pdf NON scritto: {e}", file=sys.stderr)
            return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
