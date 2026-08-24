#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""router.py — dalla storia alla classe di rischio, dalla classe al piano.

Puro e deterministico: nessuna chiamata a modello, nessun orologio, nessuna
rete. Stesso input, stessi byte in uscita. E' la stessa regola che AD-35 impone
al renderer, applicata qui perche' un router non riproducibile renderebbe non
riproducibile ogni giro.

Il router NON decide se lavorare: decide COME, se si lavora. La decisione di
lavorare sta nelle precondizioni.

CLASSI (topologia congelata dall'owner il 24/08/2026)

  R0 ROUTINE            Sonnet 5 high, verifica deterministica.
  R1 NORMAL             Opus 5 xhigh implementa, verifica, revisione fresca
                        Opus 5 high, correzioni, verifica.
  R2 CRITICAL           Opus 5 max implementa, verifica, PROCESSO NUOVO con
                        Fable 5 max come Blind Hunter, correzioni fatte da
                        Opus, verifica, nuova revisione Fable.
  R3 CHAIN-TOP          Opus 5 max e Fable 5 max analizzano in modo
                        indipendente, si confrontano, e se non convergono
                        decide il proprietario.

  MANUALE               L'Epic 0 non e' instradabile. Il loop non costruisce la
                        propria infrastruttura fondamentale: se lo facesse, un
                        difetto del loop si autocertificherebbe.

REGOLE INVIOLABILI, incise qui perche' non dipendano dalla memoria del modello

  1. Il revisore non vede mai il ragionamento dell'implementatore. Garantito dal
     confine di processo (`claude -p` separato), non dalla buona volonta'.
  2. Chi trova un rilievo non lo corregge. Il revisore Fable non e' mai il
     riparatore: le correzioni le fa Opus.
  3. Il modello propone, il sistema certifica. Nessun passo si chiude su
     un'affermazione del modello, solo su un oracolo deterministico.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- la topologia -------------------------------------------------------------
# Ardesia gira incondizionatamente a --model claude-opus-5 --effort max
# (ardesia-loop.sh:594-595). E' la capacita' da ADATTARE, non da copiare: qui
# il livello segue il rischio invece di essere costante.

IMPLEMENTA = "implementa"
VERIFICA = "verifica"
REVISIONA = "revisiona"
RIPARA = "ripara"
ANALIZZA = "analizza"
CONFRONTA = "confronta"

CLASSI: dict[str, dict] = {
    "R0": {
        "nome": "ROUTINE",
        "quando": "lavoro meccanico o documentale, nessun contratto toccato",
        "piano": [
            {"passo": IMPLEMENTA, "modello": "claude-sonnet-5", "effort": "high", "processo": "nuovo"},
            {"passo": VERIFICA, "modello": None, "effort": None, "processo": "locale"},
        ],
    },
    "R1": {
        "nome": "NORMAL",
        "quando": "codice di prodotto che non tocca contratti bloccati",
        "piano": [
            {"passo": IMPLEMENTA, "modello": "claude-opus-5", "effort": "xhigh", "processo": "nuovo"},
            {"passo": VERIFICA, "modello": None, "effort": None, "processo": "locale"},
            {"passo": REVISIONA, "modello": "claude-opus-5", "effort": "high", "processo": "nuovo"},
            {"passo": RIPARA, "modello": "claude-opus-5", "effort": "xhigh", "processo": "contesto implementatore"},
            {"passo": VERIFICA, "modello": None, "effort": None, "processo": "locale"},
        ],
    },
    "R2": {
        "nome": "CRITICAL",
        "quando": "tocca un contratto architetturale, un recinto, il renderer o il grafo di prova",
        "piano": [
            {"passo": IMPLEMENTA, "modello": "claude-opus-5", "effort": "max", "processo": "nuovo"},
            {"passo": VERIFICA, "modello": None, "effort": None, "processo": "locale"},
            {"passo": REVISIONA, "modello": "claude-fable-5", "effort": "max", "processo": "nuovo", "ruolo": "Blind Hunter"},
            {"passo": RIPARA, "modello": "claude-opus-5", "effort": "max", "processo": "contesto implementatore"},
            {"passo": VERIFICA, "modello": None, "effort": None, "processo": "locale"},
            {"passo": REVISIONA, "modello": "claude-fable-5", "effort": "max", "processo": "nuovo", "ruolo": "ri-revisione"},
        ],
    },
    "R3": {
        "nome": "CHAIN-TOP",
        "quando": "decisione di proprieta': costituzione, gate, criteri di uccisione, holdout",
        "piano": [
            {"passo": ANALIZZA, "modello": "claude-opus-5", "effort": "max", "processo": "nuovo"},
            {"passo": ANALIZZA, "modello": "claude-fable-5", "effort": "max", "processo": "nuovo"},
            {"passo": CONFRONTA, "modello": None, "effort": None, "processo": "locale"},
        ],
        "se_non_converge": "proprietario",
    },
}

# --- classificazione ----------------------------------------------------------
# Dichiarativa e ispezionabile. Un router che "capisce" la storia sarebbe un
# modello dentro il router: non riproducibile, e quindi inammissibile.

SUPERFICI_R3 = (
    "costituzione", "K-0", "K-1", "K-2", "K-3", "K-4", "K-5",
    "gate a", "gate-a", "criterio di uccisione", "kill criterion",
    "holdout", "ARCHITECTURE-SPINE", "recinto", "recinti",
)

SUPERFICI_R2 = (
    "AD-2", "AD-8", "AD-10", "AD-19", "AD-21", "AD-22", "AD-29", "AD-31", "AD-35",
    "transform", "trasformazion", "delta", "preserve", "proofgraph", "grafo di prova",
    "render", "layoutir", "svg", "publish", "certificate", "certificato",
)

SUPERFICI_R0 = (
    "documenta", "evidence", "ricevut", "rinomin", "sposta", "refactor meccanico",
)


def classifica(chiave: str, testo: str, forzata: str | None) -> tuple[str, str]:
    """Ritorna (classe, motivo). Nessuna euristica nascosta: ogni ramo e' esplicito."""
    if forzata:
        f = forzata.upper()
        if f not in CLASSI and f != "MANUALE":
            raise SystemExit(f"classe forzata sconosciuta: {forzata}")
        return f, "forzata da riga di comando"

    # L'Epic 0 e' l'infrastruttura del loop. Non instradabile, per decisione
    # dell'owner: un loop che costruisce se stesso autocertifica i propri difetti.
    if re.match(r"^(epic-)?0[-.]", chiave):
        return "MANUALE", "Epic 0: infrastruttura del loop, si costruisce a mano"

    basso = (chiave + " " + testo).lower()

    for s in SUPERFICI_R3:
        if s.lower() in basso:
            return "R3", f"tocca una superficie di proprieta': «{s}»"
    for s in SUPERFICI_R2:
        if s.lower() in basso:
            return "R2", f"tocca un contratto architetturale: «{s}»"
    for s in SUPERFICI_R0:
        if s.lower() in basso:
            return "R0", f"lavoro meccanico o documentale: «{s}»"

    # Default conservativo: chi non si riconosce vale come codice di prodotto.
    # Sbagliare verso l'alto costa token; sbagliare verso il basso costa
    # correttezza, ed e' l'errore che non vogliamo.
    return "R1", "nessuna superficie speciale riconosciuta: default conservativo"


def main() -> int:
    p = argparse.ArgumentParser(description="Instrada una storia sulla sua classe di rischio.")
    p.add_argument("--storia", required=True, help="chiave della storia, es. 2-6-catalogo-...")
    p.add_argument("--testo", default="", help="titolo o intento, usato per la classificazione")
    p.add_argument("--classe", default=None, help="forza una classe (R0|R1|R2|R3|MANUALE)")
    p.add_argument("--json", action="store_true", help="emette JSON invece del riassunto leggibile")
    a = p.parse_args()

    classe, motivo = classifica(a.storia, a.testo, a.classe)

    if classe == "MANUALE":
        out = {
            "storia": a.storia, "classe": "MANUALE", "motivo": motivo,
            "instradabile": False, "piano": [],
        }
    else:
        c = CLASSI[classe]
        out = {
            "storia": a.storia, "classe": classe, "nome": c["nome"],
            "motivo": motivo, "quando": c["quando"], "instradabile": True,
            "piano": c["piano"],
        }
        if "se_non_converge" in c:
            out["se_non_converge"] = c["se_non_converge"]

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(f"storia  : {out['storia']}")
    print(f"classe  : {out['classe']}" + (f" — {out['nome']}" if out.get("nome") else ""))
    print(f"motivo  : {out['motivo']}")
    if not out["instradabile"]:
        print("piano   : nessuno. Questa storia si esegue a mano.")
        return 0
    print("piano   :")
    for i, s in enumerate(out["piano"], 1):
        m = s["modello"] or "—"
        e = s["effort"] or "—"
        ruolo = f"  [{s['ruolo']}]" if s.get("ruolo") else ""
        print(f"   {i}. {s['passo']:<11} {m:<18} effort {e:<6} processo: {s['processo']}{ruolo}")
    if out.get("se_non_converge"):
        print(f"   → se non converge: {out['se_non_converge']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
