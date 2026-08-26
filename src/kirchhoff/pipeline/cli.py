"""`kirchhoff` — il comando che rende usabile il prodotto.

Legge una netlist, risolve in aritmetica esatta, **verifica prima di disegnare**,
e scrive la risposta, l'SVG e — se richiesto — il PDF.

Il PDF passa da un browser gia' presente sul disco invece che da una libreria
nuova: `cairosvg` e simili reimplementano il rendering SVG, e un secondo motore
di rendering vuol dire due disegni che possono divergere da byte identici. Un
browser e' lo stesso motore che vedra' lo studente.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
from fractions import Fraction

from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.risolvi import Rifiuto, risolvi


def _decimale(f: Fraction, cifre: int = 4) -> str:
    """Il valore leggibile ACCANTO a quello esatto, mai al suo posto."""
    return f"{float(f):.{cifre}g}"


def _chromium() -> pathlib.Path | None:
    base = pathlib.Path.home() / "Library/Caches/ms-playwright"
    if not base.is_dir():
        return None
    for d in sorted(base.glob("chromium_headless_shell-*"), reverse=True):
        for p in d.rglob("chrome-headless-shell"):
            return p
    return None


def in_pdf(svg: str, dove: pathlib.Path) -> None:
    """Stampa l'SVG in PDF con un browser gia' installato.

    Se il browser non c'e', **lo dice e non finge**: un PDF mancante annunciato
    e' un problema, un PDF vuoto scritto in silenzio e' un difetto.
    """
    chrome = _chromium()
    if chrome is None:
        raise RuntimeError(
            "nessun chromium sul disco per stampare il PDF. Installalo con "
            "`npx playwright install chromium-headless-shell`, oppure chiedi il "
            "solo SVG: e' il formato sorgente, il PDF ne e' una copia.")
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

    esito = risolvi(circuito)
    if isinstance(esito, Rifiuto):
        # K-3: il rifiuto e' un output valido, e dice PERCHE'.
        print(f"RIFIUTATO — {esito}", file=sys.stderr)
        return 3

    print(f"{len(circuito.components)} bipoli · {len(circuito.nodes)} nodi · "
          f"verificato da {' e '.join(esito.verifiche)}\n")
    largo = max(len(c.id) for c in circuito.components)
    for c in sorted(circuito.components, key=lambda c: c.id):
        v = esito.soluzione.get(c.id, {})
        tensione, corrente = v.get("voltage"), v.get("current")
        if tensione is None:
            continue
        print(f"  {c.id:<{largo}}  V = {str(tensione):>10}  = {_decimale(tensione):>9} V"
              f"   I = {str(corrente):>10}  = {_decimale(corrente):>9} A")

    if circuito.requests:
        print()
        for r in circuito.requests:
            v = esito.soluzione.get(r.target, {}).get(r.quantity)
            print(f"  chiesto: {r.quantity} di {r.target} = {v}  "
                  f"({_decimale(v)})" if v is not None else
                  f"  chiesto: {r.quantity} di {r.target} — non risolto")

    if n.svg:
        n.svg.write_text(esito.svg, encoding="utf-8")
        print(f"\n  disegno: {n.svg}")
    if n.pdf:
        try:
            in_pdf(esito.svg, n.pdf)
            print(f"  pdf:     {n.pdf}")
        except (RuntimeError, subprocess.SubprocessError) as e:
            print(f"  pdf NON scritto: {e}", file=sys.stderr)
            return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
