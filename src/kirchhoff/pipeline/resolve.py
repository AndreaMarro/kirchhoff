"""L'unico ingresso ammesso al prodotto: validate → dispatch → solve → verify → publish.

Esiti, tre, e non si mischiano (AD-13):

- `Solved` — numeri certificati. `verifiche` elenca solo i controlli realmente
  eseguiti su quella soluzione. Il disegno è accessorio.
- `Refusal` — il dominio ha detto no, con soggetto e diagnosi.
- `Failure` — guasto interno. `dove` è lo stadio, non un contenitore generico.
"""

from __future__ import annotations

import dataclasses
from typing import Callable

from kirchhoff.domain import mna
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import controlli_eseguiti, verify
from kirchhoff.pipeline.failure import Failure
from kirchhoff.render.layout import LayoutIR
from kirchhoff.render.serialize import render

DC_TYPES = frozenset({"resistor", "voltage_source_dc", "current_source_dc"})
PHASOR_TYPES = frozenset({
    "resistor", "capacitor", "inductor", "voltage_source_ac",
})
REATTIVI = frozenset({"capacitor", "inductor"})


@dataclasses.dataclass(frozen=True, slots=True)
class Solved:
    """Numeri certificati. Il disegno è presente solo se è stato possibile."""

    circuito: IR
    soluzione: dict
    verifiche: tuple[str, ...]
    solver: str
    layout: LayoutIR | None = None
    svg: str | None = None


Risolto = Solved


def _tipi(ir: IR) -> frozenset[str]:
    return frozenset(c.type for c in ir.components)


def _primo(ir: IR, ammessi: frozenset[str]):
    return next(c for c in ir.components if c.type not in ammessi)


def _dispatch(ir: IR) -> tuple[str, Callable[[IR], dict]] | Refusal:
    """Sceglie un solutore già presente nel kernel. Non ne inventa uno."""
    tipi = _tipi(ir)
    dominio = ir.domain

    if dominio in ("ac_sinusoidal", "three_phase"):
        if tipi - PHASOR_TYPES:
            c = _primo(ir, PHASOR_TYPES)
            return Refusal(
                "unsolvable", c.id, "component",
                f"{c.id} è un {c.type}: il percorso fasoriale non lo ammette.")
        # Lo schema rifiuta già un VAC senza ω positiva. Questo ramo copre
        # l'IR sinusoidale senza VAC (R+C, R+L) che lo schema lascia passare:
        # le impedenze reattive non hanno frequenza a cui valutarsi.
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


def _senza_autolayout(exc: BaseException) -> bool:
    return "non formano una maglia sola" in str(exc)


def _disegna(ir: IR, layout: LayoutIR | None) -> tuple[LayoutIR | None, str | None] | Failure:
    from kirchhoff.pipeline.risolvi import layout_a_maglia

    if layout is None:
        try:
            disegno = layout_a_maglia(ir)
        except ValueError as e:
            if _senza_autolayout(e):
                return None, None
            return Failure("layout", f"ValueError: {e}")
        except Exception as e:
            return Failure("layout", f"{type(e).__name__}: {e}")
    else:
        disegno = layout

    try:
        return disegno, render(ir, disegno)
    except Exception as e:
        return Failure("render", f"{type(e).__name__}: {e}")


def _guasto_del_solutore(exc: BaseException) -> bool:
    """True solo per la singolarità che solve_linear dichiara per nome.

    Ogni altro ValueError/KeyError/ZeroDivisionError uscito dal solver è un
    buco del prodotto, non un circuito illecito: validate è già passato.
    """
    return isinstance(exc, ValueError) and "singolare" in str(exc)


def resolve(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    """validate → dispatch → solver → verify → publish. Unico ingresso."""
    try:
        return _esegui(circuito, layout)
    except Exception as e:
        return Failure("resolve", f"{type(e).__name__}: {e}")


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

    try:
        soluzione = solutore(ingresso.ir)
    except Exception as e:
        if _guasto_del_solutore(e):
            return Refusal(
                "unsolvable", ingresso.ir.components[0].id, "component",
                f"il sistema non è risolvibile: {e}")
        return Failure("solver", f"{type(e).__name__}: {e}")

    try:
        rifiuto = verify(ingresso.ir, soluzione)
        attestati = controlli_eseguiti(ingresso.ir, soluzione)
    except Exception as e:
        return Failure("verify", f"{type(e).__name__}: {e}")
    if rifiuto is not None:
        return rifiuto

    disegno = _disegna(ingresso.ir, layout)
    if isinstance(disegno, Failure):
        return disegno
    lay, svg = disegno
    return Solved(circuito=ingresso.ir, soluzione=soluzione, verifiche=attestati,
                  solver=nome, layout=lay, svg=svg)


def risolvi(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    """Alias pubblico storico. Non esiste un secondo percorso."""
    return resolve(circuito, layout)
