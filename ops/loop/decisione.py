#!/usr/bin/env python3
"""Una decisione presa dal loop per delega, e cio' che la rende reversibile.

**Perche' esiste.** Il 26/08/2026 il proprietario ha delegato al loop le decisioni
aperte del vault e quelle architetturali. Fino a quel giorno il confine era
l'opposto — «registra invece di correggere» — e quel confine aveva un motivo: tre
volte in un giorno ha impedito che una questione aperta venisse chiusa per inerzia,
cioe' da un agente che sceglieva senza sapere di star scegliendo.

La delega toglie il divieto. **Non toglie il motivo.** Una decisione presa e non
scritta e' indistinguibile dall'inerzia che il confine fermava: nessuno sa che una
scelta e' stata fatta, quindi nessuno puo' contestarla. Questo strumento esiste
perche' la differenza fra «decidere» e «lasciar accadere» sia leggibile.

**Cosa una nota deve portare, e perche' proprio questo.**

- la MISURA che la sostiene, eseguita — non un ragionamento;
- le ALTERNATIVE scartate, con il motivo, perche' una decisione senza alternative
  scritte e' un fatto compiuto travestito;
- COSA LA RIBALTEREBBE. E' il campo che rende la delega sicura: una decisione che
  non dichiara come si smonta non e' delegabile, e' definitiva.

**Cio' che il loop NON decide** resta in `vault/10-Costituzione/Confini
owner-locked.md`: la definizione di `Verified`, le soglie di qualita', l'holdout,
gli invarianti di privacy, il confine AI Act, la costituzione stessa. Incontrarne
uno non e' un caso da decidere: e' un conflitto di piano, e la costituzione
prescrive di fermarsi e segnalare.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

QUI = pathlib.Path(__file__).resolve().parent
REPO = QUI.parent.parent
DEST = REPO / "vault" / "20-Decisioni-prese"
LOCK = REPO / "vault" / "10-Costituzione" / "Confini owner-locked.md"


def _sha() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def scrivi(titolo: str, istante: str, decisione: str, misura: str,
           alternative: list[str], ribalta: str, questione: str | None) -> pathlib.Path:
    DEST.mkdir(parents=True, exist_ok=True)
    chiave = "".join(c if c.isalnum() or c in "- " else "" for c in titolo)[:70].strip()
    dest = DEST / f"{istante}-{chiave.replace(' ', '-')}.md"
    righe = [
        "---",
        f"istante: {istante}",
        f"sha: {_sha()}",
        "tipo: decisione-presa",
        "decisore: loop (per delega del 26/08/2026)",
        *( [f"questione: {questione}"] if questione else [] ),
        "---",
        "",
        f"# {titolo}",
        "",
        "> Decisione presa dal loop **per delega**, non dal proprietario. E'",
        "> reversibile: la sezione «Cosa la ribalterebbe» dice come.",
        "",
        "## La decisione",
        "",
        decisione.strip(),
        "",
        "## La misura che la sostiene",
        "",
        "Eseguita, non ragionata:",
        "",
        misura.strip(),
        "",
        "## Alternative scartate",
        "",
    ]
    righe += [f"- {a}" for a in alternative] or ["- (nessuna registrata)"]
    righe += [
        "",
        "## Cosa la ribalterebbe",
        "",
        ribalta.strip(),
        "",
        "## Archi",
        "",
        "- [[Decisioni aperte]]",
        "- [[00-INDICE]]",
    ]
    dest.write_text("\n".join(righe) + "\n", encoding="utf-8")
    return dest


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--titolo", required=True)
    a.add_argument("--istante", required=True)
    a.add_argument("--decisione", required=True)
    a.add_argument("--misura", required=True, help="cosa hai ESEGUITO per sostenerla")
    a.add_argument("--alternativa", action="append", default=[])
    a.add_argument("--ribalta", required=True, help="cosa la farebbe cambiare idea")
    a.add_argument("--questione", default=None, help="es. D4")
    n = a.parse_args()

    if not n.misura.strip():
        print("una decisione senza misura non e' delegata, e' inventata", file=sys.stderr)
        return 64
    if not n.ribalta.strip():
        print("una decisione che non dichiara come si smonta non e' delegabile: "
              f"e' definitiva. Vedi {LOCK.relative_to(REPO)}", file=sys.stderr)
        return 64
    print(scrivi(n.titolo, n.istante, n.decisione, n.misura,
                 n.alternativa, n.ribalta, n.questione))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
