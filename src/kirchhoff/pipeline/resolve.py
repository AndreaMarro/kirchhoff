"""L'unico ingresso ammesso al prodotto: validate → dispatch → solve → verify → publish.

Finché le parti si componevano da sole — `validate` in un modulo, `solve_dc`
chiamato di punto in bianco, KCL e Tellegen dopo, il layout che solleva —
il repository conteneva un solutore e il prodotto non lo attraversava.
Questo modulo è lo spine applicativo. Chiunque risolva un circuito passa di qui.

Esiti, tre, e non si mischiano (AD-13):

- `Solved` — numeri certificati. Il disegno è accessorio: c'è se il layout
  c'è, manca se il circuito non è una maglia sola. I numeri non dipendono
  dal disegno.
- `Refusal` — il dominio ha detto no, con soggetto e diagnosi.
- `Failure` — qualcosa di non previsto è esploso. Non è un circuito illecito.
"""

from __future__ import annotations

import dataclasses
from typing import Callable

from kirchhoff.domain import mna
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import verify
from kirchhoff.pipeline.failure import Failure
from kirchhoff.render.layout import LayoutIR
from kirchhoff.render.serialize import render

DC_TYPES = frozenset({"resistor", "voltage_source_dc", "current_source_dc"})
PHASOR_TYPES = frozenset({
    "resistor", "capacitor", "inductor", "voltage_source_ac",
})
REATTIVI = frozenset({"capacitor", "inductor"})

VERIFICHE = (
    "legge dei nodi",
    "legge delle maglie",
    "bilancio di potenza",
    "sanità fisica",
)


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


def _disegna(ir: IR, layout: LayoutIR | None) -> tuple[LayoutIR | None, str | None]:
    from kirchhoff.pipeline.risolvi import layout_a_maglia

    try:
        disegno = layout if layout is not None else layout_a_maglia(ir)
    except ValueError:
        return None, None
    try:
        return disegno, render(ir, disegno)
    except ValueError:
        return disegno, None


def resolve(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    """validate → dispatch → solver → verify → publish. Unico ingresso."""
    try:
        return _esegui(circuito, layout)
    except Exception as e:
        return Failure("resolve", f"{type(e).__name__}: {e}")


def _esegui(circuito: IR, layout: LayoutIR | None) -> Solved | Refusal | Failure:
    ingresso = validate(circuito)
    if isinstance(ingresso, Refusal):
        return ingresso
    if not isinstance(ingresso, Validated):
        return Failure("validate", f"esito inatteso: {type(ingresso)!r}")

    scelto = _dispatch(ingresso.ir)
    if isinstance(scelto, Refusal):
        return scelto
    nome, solutore = scelto

    try:
        soluzione = solutore(ingresso.ir)
    except (ValueError, ZeroDivisionError, KeyError) as e:
        return Refusal(
            "unsolvable", ingresso.ir.components[0].id, "component",
            f"il sistema non è risolvibile: {e}")

    rifiuto = verify(ingresso.ir, soluzione)
    if rifiuto is not None:
        return rifiuto

    disegno, svg = _disegna(ingresso.ir, layout)
    return Solved(circuito=ingresso.ir, soluzione=soluzione, verifiche=VERIFICHE,
                  solver=nome, layout=disegno, svg=svg)


def risolvi(circuito: IR, layout: LayoutIR | None = None) -> Solved | Refusal | Failure:
    """Alias pubblico storico. Non esiste un secondo percorso."""
    return resolve(circuito, layout)
