"""Compatibilita' di prodotto: `resolve` proietta la radice canonica.

La radice applicativa canonica e' `run_proof_session`
(`kirchhoff.pipeline.proof_run`): unica via verso la chiusura di backend.
Per ogni (IR, Request) orchestra esattamente una volta e certifica
esattamente una volta. Questo modulo non pianifica, non risolve, non
certifica, non trasforma, non disegna circuiti da semantica propria:
per ogni domanda dell'IR delega alla radice e ne proietta le chiusure in
`Solved`, la struttura di presentazione del CLI storico.

Ambito onesto (R3): si pubblica solo cio' che il percorso certificato
certifica. Fasori, sorgenti controllate, transitori e IR senza domande
diventano `Refusal`, mai valori pubblicati da un secondo motore: un
secondo motore non esiste piu'.

Le risposte sono chiaveate sulla domanda ORIGINALE: quando la lineage P1-J
retargetta (p.es. `current R1` -> `current R1R2eq`), la catena certifica
che la grandezza finale risponde alla domanda iniziale, ed e' sotto la
chiave iniziale che la risposta si legge. La chiave finale e' registrata
accanto come fatto letteralmente certificato dalla sessione.
"""

from __future__ import annotations

import dataclasses
import os
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from kirchhoff.domain.ir import IR
from kirchhoff.domain.proof.session import DOCUMENT_PROFILE
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.proof_run import ProofSessionClosure, run_proof_session
from kirchhoff.render.layout import LayoutIR
from kirchhoff.render.serialize import FORME, render

#: Il solutore che `Solved.solver` dichiara: un solo percorso certificato.
SOLVER = "didactic"

#: Attestazioni di presentazione: vocabolario distinto per statuti distinti.
#: Il Claim elettrico e' VERIFIED, la sessione di backend e' CLOSED; il nome
#: "Product Verified" resta riservato e non compare qui (H5).
VERIFICHE = ("Claim elettrico: VERIFIED", "Sessione backend: CLOSED")

#: Dettaglio di provenienza dichiarato da questo adattatore (il produttore
#: resta il compositore autorevole, la revisione e' risolta qui sotto).
_DETAIL = (
    "resolve: proiezione Solved da chiusure certificate "
    "della radice canonica run_proof_session"
)


@dataclasses.dataclass(frozen=True, slots=True)
class Solved:
    circuito: IR
    soluzione: dict
    verifiche: tuple[str, ...]
    solver: str
    layout: LayoutIR | None = None
    svg: str | None = None


Risolto = Solved


class _OrologioSistema:
    """Orologio di default dell'adattatore: la radice resta iniettabile."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def renderer_supports(ir: IR) -> bool:
    """Il renderer dichiara i tipi che sa disegnare in `FORME`. Nient'altro."""
    return all(c.type in FORME for c in ir.components)


def _source_sha(dichiarato: str | None) -> str | Failure:
    """La revisione produttrice: dichiarata, d'ambiente o dal checkout.

    Il dominio non tocca Git e una regex non e' un'autorita' (D-H2.5-4):
    questo adattatore lega il campo ai metadati reali quando puo'
    (override esplicito, poi `KIRCHHOFF_SOURCE_SHA`, poi `git rev-parse`
    sul checkout che contiene questo file) e dichiara il limite quando
    non puo'. La forma resta validata dal compositore a valle.
    """
    if dichiarato is not None:
        return dichiarato
    env = os.environ.get("KIRCHHOFF_SOURCE_SHA")
    if env:
        return env
    try:
        radice = Path(__file__).resolve().parents[3]
        completato = subprocess.run(
            ["git", "-C", str(radice), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10)
        return completato.stdout.strip()
    except Exception as exc:
        return Failure(
            "resolve",
            "revisione produttrice non determinabile: "
            f"{exc!r} (passare source_sha=... o KIRCHHOFF_SOURCE_SHA)")


def _rifiuto_senza_domande(circuito: IR) -> Refusal:
    if circuito.components:
        return Refusal(
            "unsolvable", circuito.components[0].id, "component",
            "l'IR non contiene domande: il percorso certificato risponde "
            "a una domanda esplicita («? <grandezza> <componente>»), "
            "non pubblica mappe di valori.")
    return Refusal(
        "unsolvable", "circuito", "operation",
        "l'IR non contiene domande ne' componenti: niente da certificare.")


def _disegna(ir: IR, layout: LayoutIR | None) -> tuple[LayoutIR | None, str | None] | Failure:
    from kirchhoff.pipeline.risolvi import NotASingleMeshError, layout_a_maglia

    if layout is None:
        try:
            disegno = layout_a_maglia(ir)
        except NotASingleMeshError:
            return None, None
        except Exception as e:
            return Failure("layout", f"{type(e).__name__}: {e}")
    else:
        disegno = layout

    if not renderer_supports(ir):
        return disegno, None

    try:
        return disegno, render(ir, disegno)
    except Exception as e:
        return Failure("render", f"{type(e).__name__}: {e}")


def resolve(
    circuito: IR,
    layout: LayoutIR | None = None,
    *,
    source_sha: str | None = None,
) -> Solved | Refusal | Failure:
    """Compatibilita': delega ogni domanda alla radice canonica e proietta."""
    try:
        return _esegui(circuito, layout, source_sha)
    except Exception as e:
        return Failure("resolve", f"{type(e).__name__}: {e}")


def _esegui(
    circuito: IR,
    layout: LayoutIR | None,
    source_sha: str | None,
) -> Solved | Refusal | Failure:
    if not isinstance(circuito, IR):
        return Failure(
            "resolve", f"ingresso {type(circuito).__name__} invece di IR")
    try:
        ingresso = validate(circuito)
    except Exception as e:
        return Failure("validate", f"{type(e).__name__}: {e}")
    if isinstance(ingresso, Refusal):
        return ingresso
    if not isinstance(ingresso, Validated):
        return Failure("validate", f"esito inatteso: {type(ingresso)!r}")
    if not circuito.requests:
        return _rifiuto_senza_domande(circuito)

    sha = _source_sha(source_sha)
    if isinstance(sha, Failure):
        return sha

    soluzione: dict = {}
    for domanda in circuito.requests:
        esito = run_proof_session(
            circuito, domanda,
            clock=_OrologioSistema(),
            entropy=lambda: secrets.token_bytes(10),
            document_profile=DOCUMENT_PROFILE,
            source_sha=sha,
            detail=_DETAIL)
        if isinstance(esito, Refusal):
            return esito
        if isinstance(esito, Failure):
            return esito
        if not isinstance(esito, ProofSessionClosure):
            return Failure(
                "resolve", f"esito inatteso: {type(esito)!r}")
        finale = esito.session.final_request
        importo = esito.session.final_solution.value.amount
        soluzione.setdefault(domanda.target, {})[domanda.quantity] = importo
        if (finale.target, finale.quantity) != (domanda.target, domanda.quantity):
            soluzione.setdefault(finale.target, {})[finale.quantity] = importo

    disegno = _disegna(circuito, layout)
    if isinstance(disegno, Failure):
        return disegno
    lay, svg = disegno
    return Solved(circuito=circuito, soluzione=soluzione, verifiche=VERIFICHE,
                  solver=SOLVER, layout=lay, svg=svg)


def risolvi(
    circuito: IR,
    layout: LayoutIR | None = None,
    *,
    source_sha: str | None = None,
) -> Solved | Refusal | Failure:
    return resolve(circuito, layout, source_sha=source_sha)
