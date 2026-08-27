"""Verifica indipendente dalla costruzione del sistema (D6, AD-19).

1. residui KCL per nodo — sostituzione della soluzione, non riassemblaggio MNA;
2. residui KVL per maglia fondamentale — albero ricoprente + corde;
3. bilancio di potenza in DC, identità di Tellegen in AC — stesso Σ V I, nomi diversi;
4. sanità fisica — un passivo non eroga, e solo dove la potenza è un razionale.
5. leggi costitutive delle sorgenti controllate, se presenti.

L'accordo fra Percorso A e Percorso B DC è un gate dello spine, in `resolve`,
prima di questi controlli. Questo modulo non costruisce il secondo percorso.

Puro: nessuna I/O, nessun orologio, nessuna casualità.
"""

from __future__ import annotations

from fractions import Fraction

from .ir import IR, REFERENCE_NODE
from .ir.schema import CONTROLLED_SOURCE_TYPES
from .mna import kcl_residuals, power_balance
from .refusal import Refusal

ZERO = Fraction(0)
PASSIVI = frozenset({"resistor", "capacitor", "inductor"})
PHASOR_DOMAINS = frozenset({"ac_sinusoidal", "three_phase"})

ATTESTAZIONE_COSTITUTIVE = "leggi costitutive delle sorgenti controllate"


def kvl_residuals(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    """Residuo di tensione su ogni maglia fondamentale."""
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


def _potenziali_da_soluzione(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    """Potenziali ricostruiti dalle tensioni di ramo pubblicate, non da MNA."""
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
    return potenziale


def _vcontrol_pubblicato(ir: IR, sol: dict[str, dict], cp: str, cq: str):
    if cp == cq:
        return sol[ir.components[0].id]["voltage"] * 0
    pot = _potenziali_da_soluzione(ir, sol)
    if cp not in pot or cq not in pot:
        raise KeyError(f"nodo di controllo non raggiungibile: {cp},{cq}")
    return pot[cp] - pot[cq]


def constitutive_residuals(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    """Residuo della legge di ogni sorgente controllata, dalla soluzione pubblicata."""
    residui: dict[str, object] = {}
    for c in ir.components:
        if c.type not in CONTROLLED_SOURCE_TYPES:
            continue
        if c.control_nodes is None:
            continue
        cp, cq = c.control_nodes
        vctrl = _vcontrol_pubblicato(ir, sol, cp, cq)
        if c.type == "voltage_controlled_voltage_source":
            residui[c.id] = sol[c.id]["voltage"] - c.value.amount * vctrl
        else:
            residui[c.id] = sol[c.id]["current"] - c.value.amount * vctrl
    return residui


def _potenza(sol: dict[str, dict], cid: str):
    return sol[cid]["voltage"] * sol[cid]["current"]


def _sanita_applicabile(ir: IR, sol: dict[str, dict]) -> bool:
    """Vero solo se almeno un passivo ha potenza razionale da ispezionare."""
    return any(
        c.type in PASSIVI and isinstance(_potenza(sol, c.id), Fraction)
        for c in ir.components
    )


def _sanita(ir: IR, sol: dict[str, dict]) -> Refusal | None:
    """Un passivo che eroga viola la convenzione degli utilizzatori, o il segno."""
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


def _nome_tellegen(ir: IR) -> str:
    if ir.domain in PHASOR_DOMAINS:
        return "identità di Tellegen"
    return "bilancio di potenza"


def _ha_controllate(ir: IR) -> bool:
    return any(c.type in CONTROLLED_SOURCE_TYPES for c in ir.components)


def controlli_eseguiti(ir: IR, sol: dict[str, dict]) -> tuple[str, ...]:
    """I controlli che verify ha davvero applicato a questa soluzione.

    KCL, KVL e ΣVI girano su Fraction e su Cyc12. In DC ΣVI è un bilancio
    di potenza. In regime fasoriale è l'identità di Tellegen, non S = V I*.
    La sanità razionale gira solo se esiste un passivo la cui potenza è
    una Fraction: in regime fasoriale non si attesta.
    """
    fatti = ["legge dei nodi", "legge delle maglie", _nome_tellegen(ir)]
    if _ha_controllate(ir):
        fatti.append(ATTESTAZIONE_COSTITUTIVE)
    if _sanita_applicabile(ir, sol):
        fatti.append("sanità fisica")
    return tuple(fatti)


def _rifiuta_scarto_potenza(ir: IR, bilancio) -> Refusal | None:
    """None se ΣVI si annulla; altrimenti Refusal tipizzato sul bilancio."""
    if bilancio in (0, None) or bilancio == ZERO:
        return None
    nome = _nome_tellegen(ir)
    return Refusal(
        "residual", ir.components[0].id, "component",
        f"{nome}: scarto {bilancio}")


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

    for cid, r in sorted(constitutive_residuals(ir, sol).items()):
        if r:
            return Refusal(
                "residual", cid, "component",
                f"{cid}: la legge costitutiva della sorgente controllata "
                f"non si annulla: {r}")

    return _rifiuta_scarto_potenza(ir, power_balance(ir, sol)) or _sanita(ir, sol)
