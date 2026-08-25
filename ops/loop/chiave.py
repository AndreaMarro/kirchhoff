#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""chiave.py — LA chiave canonica di una Story, derivata dall'artefatto che la possiede.

Il problema che chiude, misurato il 25/08/2026: il loop ha lavorato su
`2-6-catalogo-delle-trasformazioni`, il ledger conosceva
`2-6-catalogo-delle-trasformazioni-e-percorso-b`, e nell'`epics.md` corrente il
numero `2.6` appartiene a una storia **diversa** — «Guidami», FR-17/KF-4/K-5.
Quattro consumatori, quattro nomi, nessuno derivato dallo stesso posto.

**La regola.** La chiave si deriva programmaticamente da `epics.md`, che e'
l'artefatto BMAD corrente che possiede la Story. Ramo, giornale, router e ledger la
consumano; nessuno la ricostruisce accorciando a mano un titolo.

**La derivazione e' quella di BMAD, non una nostra.** `_slug` riproduce
`sprint_plan.py:133` carattere per carattere, e `chiavi()` riproduce la
composizione di `sprint_plan.py:196`. Una seconda regola che assomiglia alla prima
divergerebbe nel posto dove nessuno guarda (E-62); questa e' verificata contro
l'originale da un test che confronta le due liste.

    chiave.py --elenco              tutte le chiavi correnti, in ordine
    chiave.py --risolvi 1.1         dal numero alla chiave canonica
    chiave.py --verifica <chiave>   esce 0 se la chiave esiste oggi
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

#: L'artefatto che possiede le Story. Non e' configurabile: se cambia, cambia qui,
#: in un posto solo, e tutti i consumatori seguono.
EPICS = Path("_bmad-output/planning-artifacts/epics.md")

#: `### Story 1.2: Titolo` — la stessa forma che `sprint_plan.py` riconosce.
INTESTAZIONE = re.compile(r"^###\s+Story\s+(\d+)\.(\d+[a-z]?)\s*:\s*(.+?)\s*$")


def _slug(text: str, maxlen: int = 60) -> str:
    """Copia fedele di `sprint_plan.py:133`. Non migliorarla: deve coincidere."""
    slug = re.sub(r"[^\w]+", "-", str(text).lower(), flags=re.UNICODE).strip("-")
    slug = slug[:maxlen].strip("-")
    if not slug:
        slug = hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:8]
    return slug


def chiavi(epics: Path | None = None) -> list[tuple[str, str, str]]:
    """`(numero, chiave, titolo)` per ogni Story, nell'ordine del documento."""
    percorso = epics or EPICS
    if not percorso.exists():
        raise SystemExit(f"chiave: {percorso} non esiste: nessuna sorgente da cui derivare.")
    fuori: list[tuple[str, str, str]] = []
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        m = INTESTAZIONE.match(riga)
        if not m:
            continue
        epica, storia, titolo = m.group(1), m.group(2), m.group(3)
        fuori.append((f"{epica}.{storia}", f"{epica}-{storia}-{_slug(titolo)}", titolo))
    return fuori


AUTORITA = re.compile(r"^\*\*Autorit[àa]:?\*\*\s*(.+?)\s*$", re.MULTILINE)


def corpo(chiave_cercata: str, epics: Path | None = None) -> str:
    """Il testo della Story, dalla sua intestazione alla successiva."""
    percorso = epics or EPICS
    righe = percorso.read_text(encoding="utf-8").splitlines()
    dentro, raccolto = False, []
    for riga in righe:
        m = INTESTAZIONE.match(riga)
        if m:
            questa = f"{m.group(1)}-{m.group(2)}-{_slug(m.group(3))}"
            if dentro:
                break
            dentro = questa == chiave_cercata
            if dentro:
                raccolto.append(riga)
            continue
        if dentro:
            raccolto.append(riga)
    return "\n".join(raccolto)


def autorita(chiave_cercata: str, epics: Path | None = None) -> str:
    """La riga **Autorita:** che la Story dichiara. Vuota se non la dichiara.

    E' il segnale che il router deve leggere. Classificare sulla sola chiave
    significa classificare su uno slug di sessanta caratteri: misurato il
    25/08/2026, la Story 1.1 — che dichiara «AD-22 em. · CV1 · CV3 · CV5» ed e'
    architettura-critica — usciva R1, perche' il suo titolo non nomina nessuna di
    quelle autorita'.

    Si legge la riga dichiarata e non tutto il corpo: il corpo cita spesso
    un'autorita' come MOTIVAZIONE — «un Pₖ falsificabile rende il verdetto di Gate A
    leggibile e falso» — e prenderla per un tocco farebbe salire di classe ogni
    storia che spiega perche' esiste.
    """
    m = AUTORITA.search(corpo(chiave_cercata, epics))
    return m.group(1) if m else ""


def risolvi(numero: str, epics: Path | None = None) -> tuple[str, str]:
    """Dal numero — `1.1` o `1-1` — alla chiave canonica e al titolo."""
    normale = numero.replace("-", ".").strip()
    for n, chiave, titolo in chiavi(epics):
        if n == normale:
            return chiave, titolo
    disponibili = ", ".join(n for n, _, _ in chiavi(epics))
    raise SystemExit(f"chiave: nessuna Story {numero!r}. Disponibili: {disponibili}")


def main() -> int:
    p = argparse.ArgumentParser(description="La chiave canonica di una Story.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--elenco", action="store_true")
    g.add_argument("--risolvi", metavar="N.M")
    g.add_argument("--verifica", metavar="CHIAVE")
    g.add_argument("--autorita", metavar="CHIAVE")
    p.add_argument("--epics", type=Path, default=None)
    a = p.parse_args()

    if a.elenco:
        for n, chiave, titolo in chiavi(a.epics):
            print(f"{n:<6} {chiave}")
        return 0

    if a.risolvi:
        chiave, titolo = risolvi(a.risolvi, a.epics)
        print(chiave)
        print(f"# {titolo}", file=sys.stderr)
        return 0

    if a.autorita:
        print(autorita(a.autorita, a.epics))
        return 0

    note = {c for _, c, _ in chiavi(a.epics)}
    if a.verifica in note:
        print(f"{a.verifica}: corrente", file=sys.stderr)
        return 0
    print(f"{a.verifica}: NON e' una chiave corrente di {EPICS}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
