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
    """Vero se il lavoro della storia e' gia' dentro `main`.

    **Il segnale e' il ramo fuso, non un artefatto.** La prima versione guardava se
    esisteva `spec-<chiave>.md`, e dipendeva percio' da una scelta
    dell'implementatore: il giro della 1.1 quell'artefatto lo aveva scritto, quello
    della 1.2 no — e il pannello annunciava di voler rifare una storia appena
    promossa. Un criterio di completamento non puo' poggiare su un'abitudine.

    Un ramo `loop/iter-<istante>-<chiave>` dentro `git branch --merged main` e'
    invece il fatto: quel lavoro E' su main, perche' e' li' che il merge lo ha
    messo. Non c'e' un secondo registro da tenere allineato — la stessa ragione per
    cui il dominio deriva `CAUSES` da `Cause` invece di scriverlo due volte.

    Il confronto e' per PREFISSO perche' lo scheduler tronca il nome del ramo a 90
    caratteri: `...non-dichiarat` ha perso la sua ultima lettera. Ed e' senza
    accenti, perche' i due nomi non si scrivono uguale.
    """
    r = subprocess.run(["git", "branch", "--merged", "main"],
                       cwd=QUI.parent.parent, capture_output=True, text=True)
    if r.returncode != 0:
        return False
    atteso = _piatto(chiave)
    for riga in r.stdout.splitlines():
        nome = riga.strip().lstrip("* ").strip()
        if not nome.startswith("loop/iter-"):
            continue
        # `loop/iter-<istante>-<chiave-troncata>` -> la parte dopo l'istante
        resto = nome[len("loop/iter-"):]
        _, _, coda = resto.partition("-")
        if coda and atteso.startswith(_piatto(coda)):
            return True
    return False


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
