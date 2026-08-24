"""E2E della riga di comando: attraverso il confine di processo.

`test_cli.py` chiama `main()` dentro il processo di pytest. È il test giusto per la
logica, ma non tocca mai ciò che tocca l'utente: caricamento del modulo, parsing
degli argomenti al confine del sistema operativo, e codice d'uscita propagato al
guscio. Un errore d'importazione a livello di modulo, o un `sys.exit` che perde il
proprio valore, passerebbero interamente inosservati.

Qui si lancia un processo vero e si guarda cosa ne esce.
"""

import json
import subprocess
import sys
from pathlib import Path

MODULO = "kirchhoff.eval.cli"


def esegui(*argv: str) -> tuple[int, dict]:
    p = subprocess.run([sys.executable, "-m", MODULO, *argv],
                       capture_output=True, text=True, timeout=300)
    return p.returncode, json.loads(p.stdout)


def test_e2e_costruzione_e_rapporto(tmp_path: Path):
    out = str(tmp_path / "rs")

    code, d = esegui("build", "--n", "8", "--out", out, "--split", "0.5")
    assert code == 0
    assert d["ok"] is True and d["generati"] == 8
    assert set(d["per_classe"]) == {"dc_resistive", "transient",
                                    "ac_sinusoidal", "three_phase"}

    code, d = esegui("report", "--root", out, "--split", "dev")
    assert code == 0
    assert d["VSR"] == 1.0 and d["SER"] == 0.0
    assert "NON l'estrazione" in d["coverage"]


def test_e2e_la_parte_trattenuta_fa_uscire_con_due(tmp_path: Path):
    """Il codice d'uscita è ciò che vede uno script di integrazione continua."""
    out = str(tmp_path / "rs")
    # servono almeno due casi per classe: con uno solo il taglio a meta' per eccesso
    # lo manda tutto in sviluppo e la parte trattenuta resta vuota
    code, d = esegui("build", "--n", "8", "--out", out, "--split", "0.5")
    assert code == 0 and d["split"]["holdout"] > 0

    code, d = esegui("report", "--root", out, "--split", "holdout")
    assert code == 2
    assert d["ok"] is False and "trattenuta" in d["errore"]
    assert set(d) == {"ok", "errore"}

    code, d = esegui("report", "--root", out, "--split", "holdout", "--allow-holdout")
    assert code == 0 and d["total"] > 0


def test_e2e_argomento_sconosciuto_non_produce_json(tmp_path: Path):
    """Argparse fallisce al confine, con uscita 2 e niente su stdout."""
    p = subprocess.run([sys.executable, "-m", MODULO, "misura-tutto"],
                       capture_output=True, text=True, timeout=300)
    assert p.returncode == 2
    assert p.stdout == ""
    assert "invalid choice" in p.stderr or "argument" in p.stderr
