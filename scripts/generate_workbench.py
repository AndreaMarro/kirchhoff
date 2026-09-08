"""Genera le viste studente del Proof Workbench da dati veri del kernel.

Ogni esercizio attraversa UNA volta la radice canonica
(`run_proof_session_con_run`, stessa implementazione della via di prodotto:
zero divergenze) con orologio ed entropia FISSI, quindi la rigenerazione e'
byte-identica a `source_sha` normalizzato. Niente fixture scritte a mano,
niente equazioni inventate dal frontend, niente badge hardcoded.

Uso:
    uv run --no-sync python scripts/generate_workbench.py [--out DIR] [--source-sha SHA]

Il drift test (`tests/test_workbench_generation.py`) rigenera in una
directory temporanea e confronta col contenuto versionato.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "src"))

from kirchhoff.domain.proof.session import DOCUMENT_PROFILE  # noqa: E402
from kirchhoff.domain.refusal import Refusal  # noqa: E402
from kirchhoff.pipeline.failure import Failure  # noqa: E402
from kirchhoff.pipeline.netlist import leggi  # noqa: E402
from kirchhoff.pipeline.presentation import (  # noqa: E402
    QuestionView,
    project_closed_session,
    project_failure,
    project_refusal,
    to_json,
)
from kirchhoff.pipeline.proof_run import run_proof_session_con_run  # noqa: E402
from kirchhoff.pipeline.risolvi import layout_a_maglia  # noqa: E402
from kirchhoff.render.layout import LayoutIR, Placement  # noqa: E402
from kirchhoff.domain.transform import EntityRef  # noqa: E402

ISTANTE_FISSO = 1_750_000_000_000
ATTIMO_FISSO = datetime(2026, 9, 7, 12, 0, 0, tzinfo=timezone.utc)
DETAIL = "generate_workbench: proiezione student-session da chiusura certificata"


class _OrologioFermo:
    def now(self) -> datetime:
        return ATTIMO_FISSO


def _entropia_fissa():
    n = 0
    while True:
        n += 1
        yield bytes(((n + j) % 256 for j in range(10)))


@dataclass(frozen=True, slots=True)
class Esercizio:
    id: str
    titolo: str
    netlist: str
    domanda: tuple[str, str, str] | None
    disposizione: str


def _nodo(i: str) -> EntityRef:
    return EntityRef("node", i)


def _comp(i: str) -> EntityRef:
    return EntityRef("component", i)


PIAZZAMENTI_SCALA = (
    Placement(_nodo("b"), F(0), F(0)),
    Placement(_nodo("a"), F(200), F(0)),
    Placement(_nodo("c"), F(400), F(0)),
    Placement(_nodo("0"), F(200), F(240)),
    Placement(_comp("V1"), F(0), F(120)),
    Placement(_comp("R1"), F(100), F(0)),
    Placement(_comp("R2"), F(300), F(0)),
    Placement(_comp("R3"), F(400), F(120)),
)

PIAZZAMENTI_PONTE = (
    Placement(_nodo("0"), F(200), F(20)),
    Placement(_nodo("a"), F(20), F(220)),
    Placement(_nodo("b"), F(380), F(220)),
    Placement(_nodo("c"), F(200), F(160)),
    Placement(_comp("V1"), F(200), F(90)),
    Placement(_comp("R1"), F(110), F(190)),
    Placement(_comp("R2"), F(290), F(190)),
    Placement(_comp("R3"), F(110), F(120)),
    Placement(_comp("R4"), F(290), F(120)),
    Placement(_comp("Rg"), F(200), F(220)),
)

ESERCIZI: tuple[Esercizio, ...] = (
    Esercizio(
        "partitore-d1",
        "Partitore: la corrente di serie (3/80 A)",
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? current R1\n",
        ("q1", "current", "R1"),
        "maglia",
    ),
    Esercizio(
        "scala-due-riduzioni",
        "Scala di tre resistori: due riduzioni in fila",
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a c 220 ohm\nR3 c 0 330 ohm\n"
        "? current R1\n",
        ("q1", "current", "R1"),
        "scala",
    ),
    Esercizio(
        "ponte-nodale",
        "Ponte: via nodale diretta, senza riduzioni",
        "V1 c 0 12 volt\nR1 c a 10 ohm\nR2 c b 20 ohm\n"
        "R3 a 0 30 ohm\nR4 b 0 40 ohm\nRg a b 50 ohm\n? current R4\n",
        ("q1", "current", "R4"),
        "ponte",
    ),
    Esercizio(
        "rifiuto-reattivo",
        "Fuori ambito: il condensatore in continua non si certifica",
        "V1 b 0 12 volt\nR1 b a 100 ohm\nC1 a 0 1/1000 farad\n? voltage R1\n",
        ("q1", "voltage", "R1"),
        "nessuna",
    ),
)


def _source_sha(dichiarato: str | None) -> str:
    if dichiarato:
        return dichiarato
    completato = subprocess.run(
        ["git", "-C", str(RADICE), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=10)
    return completato.stdout.strip()


def _disposizione(nome: str, ir, istante: int, casualita: bytes) -> LayoutIR:
    if nome == "maglia":
        return layout_a_maglia(ir)
    if nome == "scala":
        return LayoutIR.nuovo(PIAZZAMENTI_SCALA, istante=istante, casualita=casualita)
    if nome == "ponte":
        return LayoutIR.nuovo(PIAZZAMENTI_PONTE, istante=istante, casualita=casualita)
    raise ValueError(f"disposizione {nome!r} sconosciuta")


def genera(out: Path, source_sha: str) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    indice = []
    for numero, ex in enumerate(ESERCIZI):
        entropia = _entropia_fissa()
        ir = leggi(ex.netlist)
        if ex.domanda is None:
            raise ValueError(f"esercizio {ex.id} senza domanda")
        qid, quantita, obiettivo = ex.domanda
        richiesta = next(r for r in ir.requests if r.id == qid)
        esito = run_proof_session_con_run(
            ir, richiesta, clock=_OrologioFermo(),
            entropy=lambda: next(entropia),
            document_profile=DOCUMENT_PROFILE, source_sha=source_sha,
            detail=DETAIL)
        if isinstance(esito, Refusal):
            vista = project_refusal(
                esito, QuestionView(qid, quantita, obiettivo),
                source_sha=source_sha, detail=DETAIL)
        elif isinstance(esito, Failure):
            raise SystemExit(f"generazione {ex.id}: guasto {esito}")
        else:
            chiusura, run = esito
            if ex.disposizione == "nessuna":
                raise SystemExit(f"generazione {ex.id}: chiusa senza disposizione")
            vista = project_closed_session(
                chiusura.session, chiusura.registry, run,
                layout_iniziale=_disposizione(
                    ex.disposizione, ir, ISTANTE_FISSO + numero * 1_000,
                    next(entropia)),
                istante=ISTANTE_FISSO + numero * 100_000,
                casualita=next(entropia))
            if isinstance(vista, Failure):
                raise SystemExit(f"proiezione {ex.id}: guasto {vista}")
        (out / f"{ex.id}.json").write_text(to_json(vista) + "\n", encoding="utf-8")
        voce = {"id": ex.id, "titolo": ex.titolo, "outcome": vista.outcome,
                "domanda": {"quantity": quantita, "target": obiettivo}}
        if vista.answer is not None:
            voce["risposta_esatta"] = (
                f"{vista.answer.exact} {vista.answer.unit}")
        if vista.refusal is not None:
            voce["rifiuto"] = {
                "cause": vista.refusal.cause,
                "diagnosis": vista.refusal.diagnosis}
        indice.append(voce)
    (out / "index.json").write_text(
        json.dumps(indice, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return [ex.id for ex in ESERCIZI]


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description="Genera le viste del Proof Workbench.")
    a.add_argument("--out", type=Path, default=RADICE / "web" / "public" / "sessions")
    a.add_argument("--source-sha", default=None)
    n = a.parse_args(argv)
    sha = _source_sha(n.source_sha)
    generati = genera(n.out, sha)
    print(f"sessioni: {', '.join(generati)} -> {n.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
