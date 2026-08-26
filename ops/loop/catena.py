#!/usr/bin/env python3
"""La catena delle storie: quale viene dopo quale.

L'ordine e' DATO in `catena.txt`, non derivato. Sceglierlo con un'euristica
— «la prima non fatta» — produrrebbe 1.5, che il proprietario ha
deliberatamente rimandato: la priorita' e' arrivare al browser, non completare
l'epica in ordine.

Traduce i numeri della catena in chiavi canoniche passando da `chiave.py`, cosi'
la catena non diventa una seconda fonte dei nomi.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import unicodedata

QUI = pathlib.Path(__file__).resolve().parent


def catena() -> list[str]:
    """I numeri della catena, nell'ordine, senza commenti ne' righe vuote."""
    testo = (QUI / "catena.txt").read_text(encoding="utf-8")
    return [r.strip() for r in testo.splitlines()
            if r.strip() and not r.lstrip().startswith("#")]


def risolvi(numero: str) -> str:
    """Il numero diventa chiave canonica passando da chiave.py: una fonte sola."""
    r = subprocess.run([sys.executable, str(QUI / "chiave.py"), "--risolvi", numero],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _piatto(t: str) -> str:
    """La chiave senza accenti, per confrontarla con i nomi dei file.

    **Serve perche' la chiave e il file NON si scrivono uguale.** La chiave dice
    `1-1-l-identità-...` con l'accento; l'artefatto su disco si chiama
    `spec-1-1-l-identita-...` senza. Un confronto letterale dice «non fatta» di una
    storia promossa, e il loop la rifarebbe.

    E' lo stesso difetto che questo prodotto passa la vita a cacciare — una cosa,
    due nomi — e la cura e' la stessa: una regola sola, in un posto solo, invece di
    due scritture che si assomigliano.
    """
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def fatta(chiave: str) -> bool:
    """Vero se l'artefatto di implementazione della storia esiste gia'.

    Confronta la chiave INTERA, non il prefisso: `spec-1-2-script-di-valutazione`
    e' una storia della v1, e farla collidere con la 1.2 della v2 sarebbe
    precisamente l'errore che il ledger disallineato gia' commette.
    """
    art = QUI.parent.parent / "_bmad-output" / "implementation-artifacts"
    if not art.is_dir():
        return False
    atteso = _piatto(f"spec-{chiave}.md")
    return any(_piatto(f.name) == atteso for f in art.glob("spec-*.md"))


def dopo(chiave_corrente: str) -> str:
    """La chiave della storia successiva, o stringa vuota se la catena e' finita."""
    coppie = [(n, risolvi(n)) for n in catena()]
    for i, (_, k) in enumerate(coppie):
        if k == chiave_corrente:
            return coppie[i + 1][1] if i + 1 < len(coppie) else ""
    # La corrente non e' in catena (per esempio 1.1, che la precede): la prossima
    # e' la prima della catena che non sia gia' su main.
    for _, k in coppie:
        if k and not fatta(k):
            return k
    return ""


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--dopo", metavar="CHIAVE")
    a.add_argument("--elenco", action="store_true")
    a.add_argument("--fatta", metavar="CHIAVE")
    n = a.parse_args()
    if n.elenco:
        for num in catena():
            print(f"{num:6} {risolvi(num)}")
        return 0
    if n.fatta:
        return 0 if fatta(n.fatta) else 1

    if n.dopo:
        k = dopo(n.dopo)
        if not k:
            return 1
        print(k)
        return 0
    a.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
