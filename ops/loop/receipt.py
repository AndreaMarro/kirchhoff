#!/usr/bin/env python3
"""La receipt di un giro: cosa e' stato costruito, verificato, differito.

**Perche' esiste.** Il giornale del loop e' un log: cronologico, verboso, e
nessuno lo rilegge. La receipt e' il contrario — una nota sola, nel vault, che
dice cosa quel giro ha lasciato al prodotto e con quale prova. E' il
`91-Auto-Receipts` di ARDESIA, e la ragione e' la stessa: un giro che non lascia
traccia interrogabile e' un giro che il giro dopo non puo' usare.

**Cosa NON fa.** Non giudica. Registra misure — numero di test, copertura, esito
delle revisioni, chiave della storia, SHA — e le lascia parlare. Un giudizio di
modello in una receipt diventerebbe, tre giri dopo, un fatto che nessuno ha
verificato.

Ogni receipt dichiara lo SHA su cui e' stata scritta. Una receipt che non dice a
quale revisione si riferisce e' una frase senza soggetto.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

QUI = pathlib.Path(__file__).resolve().parent
REPO = QUI.parent.parent
RECEIPT_DIR = REPO / "vault" / "70-Receipt-di-giro"


def _git(*a: str) -> str:
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def scrivi(storia: str, istante: str, metriche: dict, esito: str,
           revisioni: list[str] | None = None) -> pathlib.Path:
    """Incide la receipt e restituisce il percorso.

    `istante` arriva da fuori — dallo scheduler, che lo ha gia' inciso nel nome
    del ramo. Prenderlo qui da `datetime.now()` produrrebbe due istanti diversi
    per lo stesso giro, ed e' esattamente la classe di difetto che questo
    progetto passa la vita a togliere.
    """
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    sha = _git("rev-parse", "HEAD")
    ramo = _git("rev-parse", "--abbrev-ref", "HEAD")
    dest = RECEIPT_DIR / f"{istante}-{storia[:60]}.md"

    righe = [
        "---",
        f"storia: {storia}",
        f"istante: {istante}",
        f"sha: {sha}",
        f"ramo: {ramo}",
        f"esito: {esito}",
        "tipo: receipt-di-giro",
        "---",
        "",
        f"# Giro {istante} — {storia}",
        "",
        "> Questa nota registra MISURE, non giudizi. Un giudizio di modello che",
        "> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha",
        "> verificato.",
        "",
        "## Misure agli oracoli",
        "",
        "| grandezza | valore |",
        "|---|---|",
    ]
    for k in ("test_passati", "test_falliti", "copertura", "recinti", "dominio", "verde"):
        if k in metriche:
            righe.append(f"| `{k}` | {metriche[k]} |")
    righe += ["", f"## Esito: {esito}", ""]

    if revisioni:
        righe += ["## Revisioni", ""]
        righe += [f"- {r}" for r in revisioni] + [""]

    righe += [
        "## Archi",
        "",
        f"- [[00-INDICE]]",
    ]
    dest.write_text("\n".join(righe) + "\n", encoding="utf-8")
    return dest


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--storia", required=True)
    a.add_argument("--istante", required=True)
    a.add_argument("--metriche", default="{}", help="JSON dell'oracolo")
    a.add_argument("--esito", required=True,
                   choices=["promosso", "verde-non-promosso", "fallito", "differito"])
    a.add_argument("--revisione", action="append", default=[])
    n = a.parse_args()
    try:
        m = json.loads(n.metriche)
    except json.JSONDecodeError:
        print("metriche non sono JSON valido", file=sys.stderr)
        return 64
    print(scrivi(n.storia, n.istante, m, n.esito, n.revisione))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
