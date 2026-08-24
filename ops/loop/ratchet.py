#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""ratchet.py — le metriche non regrediscono. Se regrediscono, ci si ferma.

LA TRAPPOLA CHE QUESTO FILE EVITA, e che Ardesia ha pagato per scoprire:
un ratchet che AGGIORNA la baseline mentre misura, misura contro se stesso.
Il candidato passerebbe sempre, perche' il metro si adegua a cio' che deve
misurare. Per questo lo scheduler misura contro una COPIA del metro, e solo
un candidato gia' promosso aggiorna l'originale, con --applica.

L'agente puo' tentare quel che vuole dentro l'iterazione. Non puo' abbassare
la baseline e poi dichiarare di averla raggiunta.

  ratchet.py --metriche m.json --baseline b.json          confronta, non scrive
  ratchet.py --metriche m.json --baseline b.json --applica confronta e promuove
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Come si giudica ogni metrica. Esplicito, perche' un ratchet con regole
# implicite e' un ratchet di cui nessuno conosce la forza.
#   "cresce"   il valore non puo' diminuire
#   "vero"     una volta vero, non puo' tornare falso
#   "zero"     deve restare zero
REGOLE = {
    "test_passati": "cresce",
    "copertura": "cresce",
    "recinti": "vero",
    "dominio": "vero",
    "test_falliti": "zero",
    "verde": "vero",
}


def confronta(candidato: dict, baseline: dict) -> list[str]:
    """Ritorna l'elenco delle regressioni. Vuoto significa: si puo' promuovere."""
    regressioni: list[str] = []
    for chiave, regola in REGOLE.items():
        nuovo = candidato.get(chiave)
        if nuovo is None:
            # Una metrica non misurata NON e' una metrica passata. Ma non e'
            # nemmeno una regressione: e' un buco, e va detto come tale.
            regressioni.append(f"{chiave}: non misurata dal candidato")
            continue

        if regola == "zero":
            if nuovo != 0:
                regressioni.append(f"{chiave}: {nuovo}, deve essere 0")
            continue

        if regola == "vero":
            vecchio = baseline.get(chiave)
            if nuovo is not True and vecchio is True:
                regressioni.append(f"{chiave}: era vero, ora {nuovo}")
            elif nuovo is not True and vecchio is None:
                regressioni.append(f"{chiave}: {nuovo}, senza baseline si pretende vero")
            continue

        if regola == "cresce":
            vecchio = baseline.get(chiave)
            if vecchio is None:
                continue  # prima incisione: qualunque valore fonda la baseline
            if nuovo < vecchio:
                regressioni.append(f"{chiave}: {vecchio} -> {nuovo}")

    return regressioni


def main() -> int:
    p = argparse.ArgumentParser(description="Il ratchet: le metriche non regrediscono.")
    p.add_argument("--metriche", required=True, help="JSON del candidato, da verifica.sh")
    p.add_argument("--baseline", required=True, help="JSON della baseline (o una sua copia)")
    p.add_argument("--applica", action="store_true", help="se passa, promuove il candidato a baseline")
    a = p.parse_args()

    try:
        candidato = json.loads(Path(a.metriche).read_text())
    except Exception as e:
        print(f"ratchet: metriche del candidato illeggibili: {e}", file=sys.stderr)
        return 70

    b = Path(a.baseline)
    if b.exists() and b.read_text().strip():
        try:
            baseline = json.loads(b.read_text())
        except Exception as e:
            print(f"ratchet: baseline illeggibile: {e}", file=sys.stderr)
            return 70
    else:
        baseline = {}

    regressioni = confronta(candidato, baseline)

    if regressioni:
        print("RATCHET: regressione. Il giro non si promuove.", file=sys.stderr)
        for r in regressioni:
            print(f"  - {r}", file=sys.stderr)
        return 1

    if not baseline:
        print("ratchet: prima incisione della baseline.", file=sys.stderr)
    else:
        migliorie = [
            f"{k}: {baseline[k]} -> {candidato[k]}"
            for k in REGOLE
            if k in baseline and k in candidato and candidato[k] != baseline[k]
        ]
        if migliorie:
            print("ratchet: avanzamento — " + "; ".join(migliorie), file=sys.stderr)
        else:
            print("ratchet: nessuna regressione, nessun avanzamento.", file=sys.stderr)

    if a.applica:
        b.parent.mkdir(parents=True, exist_ok=True)
        b.write_text(json.dumps(candidato, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print(f"ratchet: baseline promossa in {b}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
