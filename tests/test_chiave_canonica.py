"""La chiave canonica di una Story si deriva, e coincide con quella di BMAD.

Il difetto che questi test impediscono e' stato misurato il 25/08/2026: il loop ha
lavorato su `2-6-catalogo-delle-trasformazioni`, il ledger conosceva
`2-6-catalogo-delle-trasformazioni-e-percorso-b`, e nell'`epics.md` corrente il
numero `2.6` appartiene a una storia **diversa**. Quattro consumatori, quattro
nomi, nessuno derivato dallo stesso posto.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops" / "loop"))
import chiave as C  # noqa: E402

RADICE = Path(__file__).resolve().parents[1]
EPICS = RADICE / "_bmad-output" / "planning-artifacts" / "epics.md"
PIN = RADICE / "_bmad" / "scripts.pin.json"
STORIA = re.compile(r"^\d+-\d+[a-z]?-")


def _sprint_plan() -> Path | None:
    """Lo script BMAD che possiede la derivazione originale, se raggiungibile."""
    if not PIN.exists():
        return None
    sorgente = Path(json.loads(PIN.read_text())["source_path"])   # <plugin>/src/scripts
    s = sorgente.parent / "bmm-skills" / "plan" / "bmad-sprint-planning" / "scripts" / "sprint_plan.py"
    return s if s.exists() else None


def test_ogni_storia_dell_epics_ha_una_chiave():
    trovate = C.chiavi(EPICS)
    assert trovate, "nessuna Story riconosciuta in epics.md"
    numeri = [n for n, _, _ in trovate]
    assert len(numeri) == len(set(numeri)), f"numeri duplicati: {numeri}"


def test_la_chiave_e_derivata_e_non_inventata():
    """Il numero da solo non basta: la chiave porta anche il titolo corrente."""
    chiave, titolo = C.risolvi("1.2", EPICS)
    assert chiave.startswith("1-2-")
    assert C._slug(titolo) in chiave


def test_un_numero_inesistente_non_produce_una_chiave_plausibile():
    """Fallire chiuso: meglio nessuna chiave che una inventata."""
    with pytest.raises(SystemExit) as scoppio:
        C.risolvi("99.9", EPICS)
    assert "nessuna Story" in str(scoppio.value)


def test_la_derivazione_coincide_con_quella_di_bmad():
    """**L'invariante che conta.** Una regola che *assomiglia* a quella di BMAD
    divergerebbe nel posto dove nessuno guarda (E-62). Qui si confrontano le due
    liste, non le due implementazioni.
    """
    script = _sprint_plan()
    if script is None:
        pytest.skip("sprint_plan.py non raggiungibile: equivalenza non verificabile qui")

    esito = subprocess.run(
        ["uv", "run", str(script), "generate", "--dry-run",
         "--epic-file", str(EPICS),
         "--status-file", str(RADICE / "_bmad-output/implementation-artifacts/sprint-status.yaml"),
         "--stories-dir", str(RADICE / "_bmad-output/implementation-artifacts"),
         "--project", "Kirchhoff", "--date", "01-01-2026 00:00"],
        capture_output=True, text=True, cwd=RADICE,
    )
    assert esito.returncode == 0, esito.stderr[:400]
    da_bmad = sorted(k for k in json.loads(esito.stdout)["new_entries"] if STORIA.match(k))
    da_noi = sorted(k for _, k, _ in C.chiavi(EPICS))
    assert da_bmad == da_noi, (
        "la derivazione locale non riproduce quella di BMAD:\n"
        f"  solo BMAD: {sorted(set(da_bmad) - set(da_noi))}\n"
        f"  solo noi : {sorted(set(da_noi) - set(da_bmad))}")
