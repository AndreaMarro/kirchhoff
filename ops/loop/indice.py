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


def costruisci() -> pathlib.Path:
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
    INDICE.write_text("\n".join(righe) + "\n", encoding="utf-8")
    return INDICE


def _ultima_revisione_delle_note() -> str:
    """La revisione piu' recente che ha toccato una NOTA — non l'indice stesso.

    Confrontare con `HEAD` sembrava giusto e non lo era: l'indice viene costruito
    PRIMA del commit che lo contiene, quindi dichiara sempre la revisione
    precedente, e un controllo su `HEAD` lo trova stantio un istante dopo essere
    stato scritto. Misurato il 26/08/2026 su due giri di fila.

    La domanda giusta non e' «l'indice dichiara HEAD?» ma «e' cambiata una nota
    dopo che l'indice e' stato scritto?». Un commit che tocca solo codice non
    invecchia una vista del vault, e dirlo stantio insegnerebbe a ignorarlo.

    L'indice e' ESCLUSO dalla domanda: senza l'esclusione il commit che lo
    contiene conterebbe come «vault toccato» e l'indice invecchierebbe se stesso.
    Una vista non e' una nota.
    """
    r = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "vault",
         f":(exclude){INDICE.relative_to(REPO)}"],
        cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _e_antenato(a: str, b: str) -> bool:
    """Vero se `a` e' un antenato di `b`, o coincide."""
    if not a or not b:
        return False
    if a == b:
        return True
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                          cwd=REPO, capture_output=True).returncode == 0


def verifica() -> int:
    """Zero se nessuna nota e' cambiata dopo la revisione che l'indice dichiara."""
    if not INDICE.exists():
        print("indice assente: costruiscilo con `indice.py --costruisci`", file=sys.stderr)
        return 1
    dichiarato = _campo(INDICE.read_text(encoding="utf-8"), "sha")
    if not dichiarato:
        print("l'indice non dichiara alcuna revisione: ricostruiscilo", file=sys.stderr)
        return 1

    note = _ultima_revisione_delle_note()
    if note and dichiarato != note and _e_antenato(dichiarato, note):
        print(f"indice stantio: dichiara {dichiarato[:12]}, ma una nota e' cambiata "
              f"dopo, in {note[:12]}", file=sys.stderr)
        return 1
    print(f"indice corrente: nessuna nota cambiata dopo {dichiarato[:12]}")
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
