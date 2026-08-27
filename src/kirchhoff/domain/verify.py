"""Verifica indipendente dalla costruzione del sistema (D6, AD-19)."""

from __future__ import annotations

from fractions import Fraction

from .ir import IR, REFERENCE_NODE
from .mna import kcl_residuals, power_balance
from .refusal import Refusal

ZERO = Fraction(0)
PASSIVI = frozenset({"resistor", "capacitor", "inductor"})
PHASOR_DOMAINS = frozenset({"ac_sinusoidal", "three_phase"})


def kvl_residuals(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    vicini: dict[str, list[tuple[str, str]]] = {n: [] for n in ir.nodes}
    for c in ir.components:
        a, b = c.terminals
        vicini[a].append((b, c.id))
        vicini[b].append((a, c.id))

    zero = sol[ir.components[0].id]["voltage"] * 0
    potenziale: dict[str, object] = {REFERENCE_NODE: zero}
    usati: set[str] = set()
    coda = [REFERENCE_NODE]
    while coda:
        qui = coda.pop(0)
        for altro, cid in sorted(vicini[qui], key=lambda x: x[1]):
            if cid in usati or altro in potenziale:
                continue
            usati.add(cid)
            c = ir.component(cid)
            v_ramo = sol[cid]["voltage"]
            if c.terminals[0] == qui:
                potenziale[altro] = potenziale[qui] - v_ramo
            else:
                potenziale[altro] = potenziale[qui] + v_ramo
            coda.append(altro)

    residui: dict[str, object] = {}
    for c in ir.components:
        if c.id in usati:
            continue
        p, q = c.terminals
        if p not in potenziale or q not in potenziale:
            continue
        attesa = potenziale[p] - potenziale[q]
        residui[c.id] = sol[c.id]["voltage"] - attesa
    return residui


def _potenza(sol: dict[str, dict], cid: str):
    return sol[cid]["voltage"] * sol[cid]["current"]


def _sanita_applicabile(ir: IR, sol: dict[str, dict]) -> bool:
    return any(
        c.type in PASSIVI and isinstance(_potenza(sol, c.id), Fraction)
        for c in ir.components
    )


def _sanita(ir: IR, sol: dict[str, dict]) -> Refusal | None:
    for c in sorted(ir.components, key=lambda x: x.id):
        if c.type not in PASSIVI:
            continue
        potenza = _potenza(sol, c.id)
        if isinstance(potenza, Fraction) and potenza < 0:
            return Refusal(
                "sanity", c.id, "component",
                f"{c.id} è un {c.type} ma eroga {potenza} W: un passivo "
                "dissipa, non genera. Il segno della soluzione è falso.")
    return None


def controlli_eseguiti(ir: IR, sol: dict[str, dict]) -> tuple[str, ...]:
    if ir.domain in PHASOR_DOMAINS:
        fatti = ["legge dei nodi", "legge delle maglie", "identità di Tellegen"]
    else:
        fatti = ["legge dei nodi", "legge delle maglie", "bilancio di potenza"]
    if _sanita_applicabile(ir, sol):
        fatti.append("sanità fisica")
    return tuple(fatti)


def verify(ir: IR, sol: dict[str, dict]) -> Refusal | None:
    for nodo, r in sorted(kcl_residuals(ir, sol).items()):
        if r:
            return Refusal(
                "residual", nodo, "node",
                f"al nodo {nodo} la corrente entrante non si annulla: {r}")

    for cid, r in sorted(kvl_residuals(ir, sol).items()):
        if r:
            return Refusal(
                "residual", cid, "component",
                f"sulla maglia chiusa da {cid} la somma delle tensioni "
                f"non si annulla: {r}")

    bilancio = power_balance(ir, sol)
    if bilancio not in (0, None) and bilancio != ZERO:
        nome = ("identità di Tellegen" if ir.domain in PHASOR_DOMAINS
                else "bilancio di potenza")
        return Refusal(
            "residual", ir.components[0].id, "component",
            f"{nome}: erogata e dissipata non pareggiano: scarto {bilancio}")

    return _sanita(ir, sol)
