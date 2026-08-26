#!/usr/bin/env python3
"""Il contesto che l'implementatore riceve dal vault, oltre alla Story.

**Perche'.** Fino a ieri il loop passava la chiave e la classe, e l'implementatore
doveva indovinare che `epics.md` esistesse. Corretto quello, resta il secondo
buco: la Story dice cosa costruire, ma NON dice quali decisioni sono gia' state
prese, quali sono aperte, e cosa i giri precedenti hanno imparato. Quella roba
vive nel vault, e finora nessuno gliela dava.

**Cosa entra, e perche' proprio questo.**

- `10-Costituzione` — i vincoli K-0..K-5. Non negoziabili: un'implementazione che
  li ignora e' sbagliata anche se verde.
- `30-Decisioni-aperte` — cio' che NON e' deciso. Serve piu' del deciso: un
  implementatore che inventa una semantica su una questione aperta la chiude di
  fatto, senza che nessuno l'abbia scelto.
- `50-Lezioni-loop` — cosa e' gia' costato caro.
- Le note che nominano questa storia.

**Cosa NON entra, e viene detto.** Il contesto ha un tetto: oltre una certa
misura smette di essere contesto e diventa rumore che scaccia la Story. Quando
qualcosa resta fuori, questo strumento lo DICHIARA — un taglio silenzioso si
legge come «non c'era altro», che e' una bugia.
"""
from __future__ import annotations

import argparse
import pathlib
import re

QUI = pathlib.Path(__file__).resolve().parent
VAULT = QUI.parent.parent / "vault"

#: Cartelle sempre incluse, nell'ordine in cui contano.
SEMPRE = ("10-Costituzione", "30-Decisioni-aperte", "50-Lezioni-loop")

#: Tetto in caratteri. Oltre, il contesto scaccia la Story invece di sostenerla.
TETTO = 60_000


def _numero(chiave: str) -> str:
    """`1-4-serializzatore-...` -> `1.4`, per trovare le note che la nominano."""
    m = re.match(r"(\d+)-(\d+)-", chiave)
    return f"{m.group(1)}.{m.group(2)}" if m else ""


def raccogli(chiave: str) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """(incluse, escluse-per-tetto), nell'ordine di priorita'."""
    viste: set[pathlib.Path] = set()
    candidate: list[pathlib.Path] = []

    for cartella in SEMPRE:
        d = VAULT / cartella
        if d.is_dir():
            for f in sorted(d.rglob("*.md")):
                if f not in viste:
                    viste.add(f)
                    candidate.append(f)

    num = _numero(chiave)
    if num:
        for f in sorted(VAULT.rglob("*.md")):
            if f in viste or ".obsidian" in f.parts:
                continue
            t = f.read_text(encoding="utf-8", errors="replace")
            if num in t or chiave in t:
                viste.add(f)
                candidate.append(f)

    incluse, escluse, peso = [], [], 0
    for f in candidate:
        n = len(f.read_text(encoding="utf-8", errors="replace"))
        if peso + n > TETTO:
            escluse.append(f)
        else:
            incluse.append(f)
            peso += n
    return incluse, escluse


def rendi(chiave: str) -> str:
    incluse, escluse = raccogli(chiave)
    fuori = [
        "## Il sapere gia' acquisito su questo prodotto",
        "",
        "Le note che seguono vengono dal vault del progetto. **Non sono**",
        "suggerimenti: la costituzione vincola, le decisioni aperte non vanno",
        "chiuse per inerzia, e le lezioni sono cose gia' costate care.",
        "",
        "Se una decisione qui e' dichiarata APERTA, implementare una semantica che",
        "la chiude di fatto e' un errore anche se i test passano: registra",
        "`DEFERRED` con la misura e prosegui.",
        "",
    ]
    for f in incluse:
        fuori += [f"### {f.relative_to(VAULT)}", "",
                  f.read_text(encoding="utf-8", errors="replace").strip(), ""]

    if escluse:
        fuori += [
            "### Note NON incluse, per tetto di contesto",
            "",
            f"Il tetto e' {TETTO} caratteri. Queste {len(escluse)} note esistono e",
            "sono leggibili nel vault, ma non sono state incollate qui:",
            "",
        ]
        fuori += [f"- `{f.relative_to(VAULT)}`" for f in escluse] + [""]
    return "\n".join(fuori)


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--storia", required=True)
    a.add_argument("--elenco", action="store_true", help="solo i percorsi")
    n = a.parse_args()
    if n.elenco:
        inc, esc = raccogli(n.storia)
        for f in inc:
            print(f"incluso  {f.relative_to(VAULT)}")
        for f in esc:
            print(f"ESCLUSO  {f.relative_to(VAULT)}")
        return 0
    print(rendi(n.storia))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
