"""Verifica indipendente dalla costruzione del sistema (D6, AD-19).

Tre controlli oggi, due ancora senza secondo motore:

1. residui KCL per nodo — sostituzione della soluzione, non riassemblaggio MNA;
2. residui KVL per maglia fondamentale — albero ricoprente + corde, assente
   dall'assemblaggio nodale;
3. bilancio di potenza — Tellegen, cattura i segni che KCL/KVL lasciano passare;
4. sanità fisica — un passivo non eroga.

L'accordo fra percorsi (D6.4) resta fuori: non esiste un Percorso B sul prodotto.
Aggiungerlo qui senza il secondo motore sarebbe una seconda lettura dello stesso
numero, e questo prodotto tratta quella figura come un controllo che non può
fallire.

Puro: nessuna I/O, nessun orologio, nessuna casualità.
"""

from __future__ import annotations

from fractions import Fraction

from .ir import IR, REFERENCE_NODE
from .mna import kcl_residuals, power_balance
from .refusal import Refusal

ZERO = Fraction(0)


def kvl_residuals(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    """Residuo di tensione su ogni maglia fondamentale.

    L'albero parte dal nodo di riferimento e propaga i potenziali dai rami
    dell'albero. Ogni bipolo che non entra nell'albero è una corda: il suo
    residuo è V_dichiarata − (v_p − v_q), dove v è il potenziale ricostruito
    sull'albero. L'assemblaggio MNA non costruisce queste maglie: se un
    potenziale nodale e una tensione di ramo divergono, è qui che si vede.
    """
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
            # V = v(term0) − v(term1). qui è un estremo già noto.
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


def _sanita(ir: IR, sol: dict[str, dict]) -> Refusal | None:
    """Un passivo che eroga viola la convenzione degli utilizzatori, o il segno."""
    for c in sorted(ir.components, key=lambda x: x.id):
        if c.type not in ("resistor", "capacitor", "inductor"):
            continue
        potenza = sol[c.id]["voltage"] * sol[c.id]["current"]
        if isinstance(potenza, Fraction) and potenza < 0:
            return Refusal(
                "sanity", c.id, "component",
                f"{c.id} è un {c.type} ma eroga {potenza} W: un passivo "
                "dissipa, non genera. Il segno della soluzione è falso.")
    return None


def verify(ir: IR, sol: dict[str, dict]) -> Refusal | None:
    """Il primo controllo che fallisce vince. None se la soluzione regge."""
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
        return Refusal(
            "residual", ir.components[0].id, "component",
            f"erogata e dissipata non pareggiano: scarto {bilancio}")

    return _sanita(ir, sol)
