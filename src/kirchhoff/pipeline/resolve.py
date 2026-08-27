"""L'unico ingresso ammesso al prodotto: validate → dispatch → solve → verify → publish."""

from __future__ import annotations

import dataclasses
from typing import Callable

from kirchhoff.domain import mna
from kirchhoff.domain.exact import SingularSystemError
from kirchhoff.domain.independent_dc import TableauSingularError, solve_dc_tableau
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import controlli_eseguiti, verify
from kirchhoff.pipeline.failure import Failure
from kirchhoff.render.layout import LayoutIR
from kirchhoff.render.serialize import FORME, render

DC_TYPES = frozenset({"resistor", "voltage_source_dc", "current_source_dc"})
PHASOR_TYPES = frozenset({
    "resistor", "capacitor", "inductor", "voltage_source_ac",
})
REATTIVI = frozenset({"capacitor", "inductor"})

SUPPORTED_DOMAINS = frozenset({
    "dc", "dc_resistive", "ac_sinusoidal", "three_phase", "transient",
})
DC_DOMAINS = frozenset({"dc", "dc_resistive"})
PHASOR_DOMAINS = frozenset({"ac_sinusoidal", "three_phase"})

QUANTITIES_BY_SOLVER: dict[str, frozenset[str]] = {
    "dc": frozenset({"voltage", "current"}),
    "phasor": frozenset({"voltage", "current"}),
}

ATTESTAZIONE_PERCORSI = "accordo fra percorsi indipendenti"
GRANDEZZE_CONFRONTO = ("voltage", "current")


@dataclasses.dataclass(frozen=True, slots=True)
class Solved:
    circuito: IR
    soluzione: dict
    verifiche: tuple[str, ...]
    solver: str
    layout: LayoutIR | None = None
    svg: str | None = None


Risolto = Solved


def renderer_supports(ir: IR) -> bool:
    """Il renderer dichiara i tipi che sa disegnare in `FORME`. Nient'altro."""
    return all(c.type in FORME for c in ir.components)


def _tipi(ir: IR) -> frozenset[str]:
    return frozenset(c.type for c in ir.components)


def _primo(ir: IR, ammessi: frozenset[str]):
    return next(c for c in ir.components if c.type not in ammessi)


def _rifiuto_richieste(ir: IR, solver: str, soluzione: dict | None = None) -> Refusal | None:
    ammesse = QUANTITIES_BY_SOLVER[solver]
    for r in ir.requests:
        if r.quantity not in ammesse:
            return Refusal(
                "unsolvable", r.id, "request",
                f"la richiesta {r.id} chiede {r.quantity} di {r.target}: "
                f"il percorso {solver} produce solo "
                f"{', '.join(sorted(ammesse))}.")
        if soluzione is None:
            continue
        valore = soluzione.get(r.target, {}).get(r.quantity)
        if valore is None:
            return Refusal(
                "unsolvable", r.id, "request",
                f"la richiesta {r.id} chiede {r.quantity} di {r.target} "
                "ma il solutore non l'ha prodotta.")
    return None


def _confronta_percorsi(sol_a: dict, sol_b: dict) -> Refusal | None:
    """Confronto esatto fra Percorso A e Percorso B. Nessuna tolleranza."""
    ids_a, ids_b = set(sol_a), set(sol_b)
    if ids_a != ids_b:
        solo_a = sorted(ids_a - ids_b)
        solo_b = sorted(ids_b - ids_a)
        if solo_a:
            cid = solo_a[0]
            return Refusal(
                "path_disagreement", cid, "component",
                f"{cid}: presente nel percorso A, assente nel percorso B.")
        cid = solo_b[0]
        return Refusal(
            "path_disagreement", cid, "component",
            f"{cid}: presente nel percorso B, assente nel percorso A.")

    for cid in sorted(ids_a):
        qa, qb = sol_a[cid], sol_b[cid]
        for q in GRANDEZZE_CONFRONTO:
            if q not in qa:
                return Refusal(
                    "path_disagreement", cid, "component",
                    f"{cid}:\n{q}:\npercorso A = assente\npercorso B = {qb.get(q, 'assente')}")
            if q not in qb:
                return Refusal(
                    "path_disagreement", cid, "component",
                    f"{cid}:\n{q}:\npercorso A = {qa[q]}\npercorso B = assente")
            if qa[q] != qb[q]:
                return Refusal(
                    "path_disagreement", cid, "component",
                    f"{cid}:\n{q}:\npercorso A = {qa[q]}\npercorso B = {qb[q]}")
    return None


def _dispatch(ir: IR) -> tuple[str, Callable[[IR], dict]] | Refusal:
    tipi = _tipi(ir)
    dominio = ir.domain

    if dominio not in SUPPORTED_DOMAINS:
        return Refusal(
            "unsolvable", dominio, "operation",
            f"domain={dominio!r} non è fra i domini supportati "
            f"({', '.join(sorted(SUPPORTED_DOMAINS))}): "
            "non viene interpretato come continua.")

    if dominio in PHASOR_DOMAINS:
        if tipi - PHASOR_TYPES:
            c = _primo(ir, PHASOR_TYPES)
            return Refusal(
                "unsolvable", c.id, "component",
                f"{c.id} è un {c.type}: il percorso fasoriale non lo ammette.")
        if ir.omega <= 0:
            return Refusal(
                "unsolvable", ir.components[0].id, "component",
                "regime sinusoidale senza pulsazione positiva: il percorso "
                "fasoriale non ha una frequenza a cui valutare le impedenze.")
        return "phasor", mna.solve_phasor

    if dominio == "transient":
        c = next((x for x in ir.components if x.type in REATTIVI), ir.components[0])
        return Refusal(
            "unsolvable", c.id, "component",
            "il transitorio ha un oracolo nel kernel, ma non è ancora sul "
            "percorso di pubblicazione: non si certifica uno stato iniziale "
            "senza dire quale rete sostituita è stata verificata.")

    if dominio in DC_DOMAINS:
        if tipi <= DC_TYPES:
            return "dc", mna.solve_dc
        c = _primo(ir, DC_TYPES)
        if c.type in REATTIVI:
            return Refusal(
                "unsolvable", c.id, "component",
                f"{c.id} è un {c.type}: il percorso in continua non lo ammette. "
                "Non viene spento in silenzio (aperto o corto): sarebbe la "
                "soluzione di un circuito diverso da quello dichiarato.")
        return Refusal(
            "unsolvable", c.id, "component",
            f"{c.id} è un {c.type}: nessun percorso del prodotto lo risolve "
            f"con domain={dominio!r}.")

    return Refusal(
        "unsolvable", dominio, "operation",
        f"domain={dominio!r} è nominato ma non ha un percorso di pubblicazione.")


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


def resolve(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    try:
        return _esegui(circuito, layout)
    except Exception as e:
        return Failure("resolve", f"{type(e).__name__}: {e}")


def _oracolo_percorso_b(ir: IR, soluzione_a: dict) -> Refusal | Failure | None:
    """Gate interno: A e B devono concordare esattamente. None se concordano."""
    try:
        soluzione_b = solve_dc_tableau(ir)
    except TableauSingularError as e:
        return Refusal(
            "path_disagreement", ir.components[0].id, "component",
            "percorso A ha una soluzione, percorso B dichiara sistema "
            f"singolare: {e}")
    except Exception as e:
        return Failure("verify", f"{type(e).__name__}: {e}")
    return _confronta_percorsi(soluzione_a, soluzione_b)


def _esegui(circuito: IR, layout: LayoutIR | None) -> Solved | Refusal | Failure:
    try:
        ingresso = validate(circuito)
    except Exception as e:
        return Failure("validate", f"{type(e).__name__}: {e}")
    if isinstance(ingresso, Refusal):
        return ingresso
    if not isinstance(ingresso, Validated):
        return Failure("validate", f"esito inatteso: {type(ingresso)!r}")

    try:
        scelto = _dispatch(ingresso.ir)
    except Exception as e:
        return Failure("dispatch", f"{type(e).__name__}: {e}")
    if isinstance(scelto, Refusal):
        return scelto
    nome, solutore = scelto

    rifiuto = _rifiuto_richieste(ingresso.ir, nome)
    if rifiuto is not None:
        return rifiuto

    try:
        soluzione = solutore(ingresso.ir)
    except SingularSystemError as e:
        return Refusal(
            "unsolvable", ingresso.ir.components[0].id, "component",
            f"il sistema non è risolvibile: {e}")
    except Exception as e:
        return Failure("solver", f"{type(e).__name__}: {e}")

    rifiuto = _rifiuto_richieste(ingresso.ir, nome, soluzione)
    if rifiuto is not None:
        return rifiuto

    if nome == "dc":
        esito_b = _oracolo_percorso_b(ingresso.ir, soluzione)
        if esito_b is not None:
            return esito_b

    try:
        rifiuto = verify(ingresso.ir, soluzione)
        attestati = controlli_eseguiti(ingresso.ir, soluzione)
    except Exception as e:
        return Failure("verify", f"{type(e).__name__}: {e}")
    if rifiuto is not None:
        return rifiuto

    if nome == "dc":
        attestati = (*attestati, ATTESTAZIONE_PERCORSI)

    disegno = _disegna(ingresso.ir, layout)
    if isinstance(disegno, Failure):
        return disegno
    lay, svg = disegno
    return Solved(circuito=ingresso.ir, soluzione=soluzione, verifiche=attestati,
                  solver=nome, layout=lay, svg=svg)


def risolvi(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    return resolve(circuito, layout)
