"""Percorso A — analisi nodale modificata, aritmetica esatta.

Un solo assemblaggio serve tre domini, perche' cambia solo cosa vale
un'ammettenza: un numero razionale in continua, un elemento di Q(zeta_12) in
regime sinusoidale, una funzione razionale valutata in `s` nel dominio di
Laplace. La topologia, i segni e le equazioni sono gli stessi.

Nessun float compare mai: il risultato e' esatto, quindi un disaccordo con un
altro percorso e' un bug e non rumore.

Puro: nessuna I/O, nessuna casualita', nessun orologio (AD-2, AD-17).
"""

from __future__ import annotations

from fractions import Fraction

from .exact import ONE, Cyc12, J, solve_linear, zeta_pow
from .ir import IR, REFERENCE_NODE, Component

ZERO = Fraction(0)

#: Convenzione delle correnti: la corrente entra dal primo terminale ed esce dal
#: secondo (convenzione degli utilizzatori); la tensione e' v(terminals[0]) -
#: v(terminals[1]). Vale per ogni componente, sorgenti incluse: cosi' la somma
#: delle potenze e' zero per identita' di Tellegen, e un residuo diverso da zero
#: e' sempre un errore di segno.


def _classify_dc(c: Component) -> tuple[str, Fraction]:
    if c.type == "resistor":
        return "Y", Fraction(1) / c.value.amount
    if c.type == "voltage_source_dc":
        return "E", c.value.amount
    if c.type == "current_source_dc":
        return "I", c.value.amount
    if c.type == "voltage_controlled_voltage_source":
        return "VCVS", c.value.amount
    if c.type == "voltage_controlled_current_source":
        return "VCCS", c.value.amount
    raise ValueError(f"{c.id}: {c.type} non ammesso in analisi in continua")


def _classify_phasor(omega: Fraction, c: Component) -> tuple[str, Cyc12]:
    if c.type == "resistor":
        return "Y", Cyc12.of(Fraction(1) / c.value.amount)
    if c.type == "inductor":
        return "Y", ONE / (J * Cyc12.of(omega * c.value.amount))
    if c.type == "capacitor":
        return "Y", J * Cyc12.of(omega * c.value.amount)
    if c.type == "voltage_source_ac":
        return "E", Cyc12.of(c.value.amount) * zeta_pow(c.phase_steps)
    raise ValueError(f"{c.id}: {c.type} non ammesso in regime sinusoidale")


def _classify_natural(s: Fraction, c: Component) -> tuple[str, Fraction]:
    """Rete a sorgenti spente, impedenze valutate in `s`. Serve alle frequenze naturali."""
    if c.type == "resistor":
        return "Y", Fraction(1) / c.value.amount
    if c.type == "inductor":
        return "Y", Fraction(1) / (s * c.value.amount)
    if c.type == "capacitor":
        return "Y", s * c.value.amount
    if c.type == "voltage_source_dc":
        return "E", ZERO          # sorgente di tensione spenta: un corto circuito
    if c.type == "current_source_dc":
        return "I", ZERO          # sorgente di corrente spenta: un circuito aperto
    raise ValueError(f"{c.id}: {c.type} non ammesso nel dominio di Laplace")


def _assemble(ir: IR, kinds: list[tuple[Component, str, object]], zero):
    """Costruisce (matrice, termine noto, indice dei nodi, indice delle sorgenti)."""
    unknown_nodes = [n for n in ir.nodes if n != REFERENCE_NODE]
    idx = {n: i for i, n in enumerate(unknown_nodes)}
    sources = [c for c, kind, _ in kinds if kind in ("E", "VCVS")]
    src_idx = {c.id: len(unknown_nodes) + i for i, c in enumerate(sources)}
    size = len(unknown_nodes) + len(sources)

    a = [[zero] * size for _ in range(size)]
    b = [zero] * size

    for c, kind, val in kinds:
        p, q = c.terminals
        if kind == "Y":
            for x, y in ((p, q), (q, p)):
                if x in idx:
                    a[idx[x]][idx[x]] += val
                    if y in idx:
                        a[idx[x]][idx[y]] -= val
        elif kind == "E":
            k = src_idx[c.id]
            if p in idx:
                a[idx[p]][k] += 1
                a[k][idx[p]] += 1
            if q in idx:
                a[idx[q]][k] -= 1
                a[k][idx[q]] -= 1
            b[k] = val
        elif kind == "VCVS":
            k = src_idx[c.id]
            if c.control_nodes is None:
                raise ValueError(f"{c.id}: VCVS senza nodi di controllo")
            cp, cq = c.control_nodes
            if p in idx:
                a[idx[p]][k] += 1
                a[k][idx[p]] += 1
            if q in idx:
                a[idx[q]][k] -= 1
                a[k][idx[q]] -= 1
            if cp in idx:
                a[k][idx[cp]] -= val
            if cq in idx:
                a[k][idx[cq]] += val
        elif kind == "VCCS":
            if c.control_nodes is None:
                raise ValueError(f"{c.id}: VCCS senza nodi di controllo")
            cp, cq = c.control_nodes
            if p in idx:
                if cp in idx:
                    a[idx[p]][idx[cp]] += val
                if cq in idx:
                    a[idx[p]][idx[cq]] -= val
            if q in idx:
                if cp in idx:
                    a[idx[q]][idx[cp]] -= val
                if cq in idx:
                    a[idx[q]][idx[cq]] += val
        else:  # "I": corrente nota, va al termine noto
            if p in idx:
                b[idx[p]] -= val
            if q in idx:
                b[idx[q]] += val
    return a, b, idx, src_idx


def _solve(ir: IR, kinds: list[tuple[Component, str, object]], zero) -> dict[str, dict[str, object]]:
    a, b, idx, src_idx = _assemble(ir, kinds, zero)
    sol = solve_linear(a, b)

    v = {REFERENCE_NODE: zero}
    for n, i in idx.items():
        v[n] = sol[i]

    out: dict[str, dict[str, object]] = {}
    for c, kind, val in kinds:
        p, q = c.terminals
        vd = v[p] - v[q]
        if kind == "Y":
            i_c = vd * val
        elif kind in ("E", "VCVS"):
            i_c = sol[src_idx[c.id]]
        elif kind == "VCCS":
            cp, cq = c.control_nodes
            i_c = val * (v[cp] - v[cq])
        else:
            i_c = val
        out[c.id] = {"voltage": vd, "current": i_c}
    return out


def solve_dc(ir: IR) -> dict[str, dict[str, Fraction]]:
    """Risolve in continua e restituisce, per ogni componente, tensione e corrente."""
    return _solve(ir, [(c, *_classify_dc(c)) for c in ir.components], ZERO)  # type: ignore[return-value]


def solve_phasor(ir: IR) -> dict[str, dict[str, Cyc12]]:
    """Risolve in regime sinusoidale alla pulsazione dell'IR. Fasori esatti."""
    kinds = [(c, *_classify_phasor(ir.omega, c)) for c in ir.components]
    return _solve(ir, kinds, Cyc12.of(0))  # type: ignore[return-value]


def mna_matrix_at(ir: IR, s: Fraction) -> list[list[Fraction]]:
    """Matrice MNA della rete a sorgenti spente, valutata in `s`.

    `s` e' una frequenza naturale della rete esattamente quando questa matrice e'
    singolare: e' la definizione, non una formula ricavata per una topologia
    particolare. Con `s` razionale il determinante resta razionale, quindi il
    controllo e' un confronto a zero esatto.
    """
    kinds = [(c, *_classify_natural(s, c)) for c in ir.components]
    a, _b, _idx, _src = _assemble(ir, kinds, ZERO)
    return a  # type: ignore[return-value]


def kcl_residuals(ir: IR, sol: dict[str, dict]) -> dict[str, object]:
    """Residui KCL per nodo, calcolati sostituendo la soluzione (FR-11)."""
    res: dict[str, object] = {n: ZERO for n in ir.nodes}
    for c in ir.components:
        p, q = c.terminals
        i_c = sol[c.id]["current"]
        res[p] = res[p] - i_c
        res[q] = res[q] + i_c
    return res


def power_balance(ir: IR, sol: dict[str, dict]):
    """Somma algebrica delle potenze. Deve essere esattamente zero."""
    total = ZERO
    for c in ir.components:
        total = total + sol[c.id]["voltage"] * sol[c.id]["current"]
    return total
