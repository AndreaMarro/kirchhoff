#!/usr/bin/env python3
"""L'indice del vault: DERIVATO, e che dichiara da quale revisione viene.

**La regola che rende utile un indice e' anche quella che lo rende innocuo.**
ARDESIA la scrive cosi': «WikiLLM e' solo un indice derivato e deve dichiarare lo
stesso HEAD». Un indice che non dice da dove viene diventa, appena il repository
avanza, una seconda verita' che nessuno sa essere vecchia — ed e' la stessa
ragione per cui il dominio deriva `CAUSES` da `Cause` invece di scriverlo due
volte.

Qui la dichiarazione e' esplicita e verificabile: `--verifica` esce diverso da
zero quando l'indice e' stato costruito su una revisione che non e' piu' quella
corrente. Un cancello puo' quindi rifiutarsi di fidarsene, invece di leggerlo e
credergli.

L'indice non riassume e non giudica: elenca. Titolo, tipo, e i wikilink che ogni
nota dichiara. Cio' che serve per NAVIGARE al fatto, mai per sostituirlo.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

QUI = pathlib.Path(__file__).resolve().parent
REPO = QUI.parent.parent
VAULT = REPO / "vault"
INDICE = VAULT / "90-Indice-derivato.md"

_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_LINK = re.compile(r"\[\[([^\]|#]+)")


def head() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _campo(testo: str, nome: str) -> str:
    m = _FRONT.match(testo)
    if not m:
        return ""
    for riga in m.group(1).splitlines():
        chiave, _, valore = riga.partition(":")
        if chiave.strip() == nome:
            return valore.strip()
    return ""


def note() -> list[tuple[pathlib.Path, str, str, list[str]]]:
    """Ogni nota: percorso, titolo, tipo, wikilink dichiarati."""
    fuori = []
    for f in sorted(VAULT.rglob("*.md")):
        if f == INDICE or ".obsidian" in f.parts or ".trash" in f.parts:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        titolo = next((r[2:].strip() for r in t.splitlines() if r.startswith("# ")),
                      f.stem)
        fuori.append((f.relative_to(VAULT), titolo, _campo(t, "tipo"),
                      sorted(set(_LINK.findall(t)))))
    return fuori


def _rendi() -> str:
    """Il testo dell'indice, senza scriverlo."""
    h = head()
    n = note()
    righe = [
        "---",
        f"sha: {h}",
        "tipo: indice-derivato",
        "---",
        "",
        "# Indice derivato del vault",
        "",
        "> **Non modificare a mano.** Questo file e' costruito da",
        "> `ops/loop/indice.py` e non e' una fonte: e' una vista. Se contraddice",
        "> una nota, ha torto lui — e `--verifica` lo dice, invece di lasciartelo",
        "> scoprire.",
        "",
        f"Costruito sulla revisione `{h}`.",
        f"{len(n)} note.",
        "",
    ]
    per_cartella: dict[str, list] = {}
    for rel, titolo, tipo, link in n:
        per_cartella.setdefault(str(rel.parent) if rel.parent != pathlib.Path(".")
                                else "(radice)", []).append((rel, titolo, tipo, link))
    for cartella in sorted(per_cartella):
        righe += [f"## {cartella}", ""]
        for rel, titolo, tipo, link in per_cartella[cartella]:
            marca = f" · `{tipo}`" if tipo else ""
            archi = f" → {', '.join('[[' + x + ']]' for x in link[:4])}" if link else ""
            righe.append(f"- [[{rel.stem}]] — {titolo}{marca}{archi}")
        righe.append("")
    return "\n".join(righe) + "\n"


def costruisci() -> pathlib.Path:
    INDICE.write_text(_rendi(), encoding="utf-8")
    return INDICE


def _corpo(testo: str) -> str:
    """L'indice senza la riga della revisione: cio' che deve coincidere."""
    return "\n".join(r for r in testo.splitlines()
                     if not r.startswith(("sha:", "Costruito sulla revisione")))


def verifica() -> int:
    """Zero se ricostruire l'indice non lo cambierebbe.

    **Terza forma di questo controllo, e la prima che regge.** Le prime due
    confrontavano revisioni git, e sono cadute sullo stesso scoglio da due lati:
    l'indice viene costruito PRIMA del commit che lo contiene, quindi dichiara
    sempre la revisione precedente. Confrontandolo con `HEAD` si dichiarava
    stantio un istante dopo essere stato scritto; escludendo se stesso restava il
    caso — normale — in cui una nota e l'indice entrano nello stesso commit, e
    l'indice risultava di nuovo indietro di uno.

    Il difetto non era nel confronto ma nella domanda. «Da quale revisione viene?»
    e' una domanda sull'ordine degli eventi, e l'ordine qui e' intrinsecamente
    ambiguo. «Ricostruirlo lo cambierebbe?» e' una domanda sul CONTENUTO, ha una
    risposta sola, e non dipende da quando qualcuno ha committato.

    La riga della revisione resta nel file: dice a un lettore umano da dove viene
    quella vista. Semplicemente non e' piu' cio' su cui si decide.
    """
    if not INDICE.exists():
        print("indice assente: costruiscilo con `indice.py --costruisci`", file=sys.stderr)
        return 1

    depositato = INDICE.read_text(encoding="utf-8")
    atteso = _rendi()
    if _corpo(depositato) != _corpo(atteso):
        d, a = _corpo(depositato).splitlines(), _corpo(atteso).splitlines()
        print(f"indice stantio: ricostruirlo lo cambierebbe "
              f"({len(d)} righe depositate, {len(a)} attese). "
              "Ricostruiscilo con `indice.py --costruisci`.", file=sys.stderr)
        for riga in [r for r in a if r not in d][:3]:
            print(f"  manca: {riga[:96]}", file=sys.stderr)
        return 1
    print(f"indice corrente: {len(note())} note, ricostruirlo non lo cambierebbe")
    return 0


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--costruisci", action="store_true")
    g.add_argument("--verifica", action="store_true")
    n = a.parse_args()
    if n.costruisci:
        print(costruisci())
        return 0
    return verifica()


if __name__ == "__main__":
    raise SystemExit(main())
