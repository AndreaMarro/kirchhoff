"""Percorso B — tableau di ramo esatto per circuiti DC resistivi.

Incognite: tensione e corrente di ogni ramo, non i potenziali nodali.
Equazioni: KCL sui nodi non di riferimento, KVL sulle maglie fondamentali
di un albero ricoprente costruito dal grafo, leggi costitutive.

Il kernel lineare è un'eliminazione gaussiana propria su Fraction.
Questo modulo non importa MNA, non importa il kernel lineare di A, non
riusa i residui KCL/KVL del modulo verify.
"""

from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.ir import IR, REFERENCE_NODE, Component

ZERO = Fraction(0)
ONE = Fraction(1)

DC_TABLEAU_TYPES = frozenset({"resistor", "voltage_source_dc", "current_source_dc"})


class TableauSingularError(ValueError):
    """Il sistema del tableau è matematicamente singolare."""


class TableauBuildError(RuntimeError):
    """Il tableau non si può costruire: bug interno o topologia inattesa."""


def _q(x: object) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int) and not isinstance(x, bool):
        return Fraction(x)
    raise TypeError(
        f"il tableau DC accetta solo Fraction (o int): ricevuto {type(x).__name__}"
    )


def solve_tableau_linear(a: list[list], b: list) -> list[Fraction]:
    """Eliminazione gaussiana esatta con scambio righe e sostituzione all'indietro.

    Non è Gauss-Jordan. Non è il kernel lineare del Percorso A.
    """
    n = len(b)
    if n != len(a) or any(len(row) != n for row in a):
        raise TableauBuildError("matrice e termine noto di dimensioni incompatibili")
    if n == 0:
        return []

    m = [[_q(a[i][j]) for j in range(n)] + [_q(b[i])] for i in range(n)]

    for col in range(n):
        pivot = next((r for r in range(col, n) if m[r][col] != 0), None)
        if pivot is None:
            raise TableauSingularError(f"sistema del tableau singolare alla colonna {col}")
        if pivot != col:
            m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        for r in range(col + 1, n):
            if m[r][col] != 0:
                f = m[r][col] / p
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[col])]

    x = [ZERO] * n
    for i in range(n - 1, -1, -1):
        if m[i][i] == 0:  # pragma: no cover - già intercettato in avanti
            raise TableauSingularError(f"sistema del tableau singolare alla colonna {i}")
        s = m[i][n]
        for j in range(i + 1, n):
            s -= m[i][j] * x[j]
        x[i] = s / m[i][i]
    return x


def _vicini(ir: IR) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {n: [] for n in ir.nodes}
    for c in ir.components:
        a, b = c.terminals
        out[a].append((b, c.id))
        out[b].append((a, c.id))
    for n in out:
        out[n].sort(key=lambda x: (x[1], x[0]))
    return out


def _albero_ricoprente(ir: IR) -> tuple[dict[str, tuple[str, str] | None], frozenset[str]]:
    """BFS dal riferimento. parent[nodo] = (padre, id_ramo) oppure None."""
    vicini = _vicini(ir)
    parent: dict[str, tuple[str, str] | None] = {REFERENCE_NODE: None}
    usati: set[str] = set()
    coda = [REFERENCE_NODE]
    while coda:
        qui = coda.pop(0)
        for altro, cid in vicini[qui]:
            if cid in usati or altro in parent:
                continue
            usati.add(cid)
            parent[altro] = (qui, cid)
            coda.append(altro)
    usati_nodi = {t for c in ir.components for t in c.terminals}
    mancanti = sorted(n for n in usati_nodi if n not in parent)
    if mancanti:
        raise TableauBuildError(
            f"albero ricoprente incompleto: nodi non raggiunti {', '.join(mancanti)}"
        )
    return parent, frozenset(usati)


def _segno_percorrenza(c: Component, partenza: str, arrivo: str) -> Fraction:
    t0, t1 = c.terminals
    if partenza == t0 and arrivo == t1:
        return ONE
    if partenza == t1 and arrivo == t0:
        return -ONE
    raise TableauBuildError(
        f"{c.id}: percorrenza {partenza}→{arrivo} non coincide con i terminali {c.terminals}"
    )


def _verso_radice(
    parent: dict[str, tuple[str, str] | None], nodo: str
) -> list[tuple[str, str, str]]:
    """Lista (qui, padre, cid) da nodo verso il riferimento."""
    passi: list[tuple[str, str, str]] = []
    qui = nodo
    while parent[qui] is not None:
        padre, cid = parent[qui]
        passi.append((qui, padre, cid))
        qui = padre
    return passi


def _percorso_albero(
    ir: IR,
    parent: dict[str, tuple[str, str] | None],
    start: str,
    end: str,
) -> list[tuple[str, Fraction]]:
    """(id_ramo, segno) per andare da start a end sull'albero."""
    if start == end:
        return []
    su_start = _verso_radice(parent, start)
    su_end = _verso_radice(parent, end)
    antenati_end = {end}
    for qui, padre, _cid in su_end:
        antenati_end.add(padre)

    verso_lca: list[tuple[str, str, str]] = []
    qui = start
    if qui in antenati_end:
        lca = qui
    else:
        lca = None
        for qui, padre, cid in su_start:
            verso_lca.append((qui, padre, cid))
            if padre in antenati_end:
                lca = padre
                break
        if lca is None:
            raise TableauBuildError(f"nessun antenato comune fra {start} e {end}")

    da_lca: list[tuple[str, str, str]] = []
    if end != lca:
        for qui, padre, cid in su_end:
            da_lca.append((qui, padre, cid))
            if padre == lca:
                break
        da_lca.reverse()

    passi: list[tuple[str, Fraction]] = []
    for qui, padre, cid in verso_lca:
        passi.append((cid, _segno_percorrenza(ir.component(cid), qui, padre)))
    for qui, padre, cid in da_lca:
        passi.append((cid, _segno_percorrenza(ir.component(cid), padre, qui)))
    return passi


def _costitutiva(c: Component, i_v: int, i_i: int, row: list[Fraction], known: list[Fraction]) -> None:
    if c.type == "resistor":
        row[i_v] = ONE
        row[i_i] = -c.value.amount
        known[0] = ZERO
        return
    if c.type == "voltage_source_dc":
        row[i_v] = ONE
        known[0] = c.value.amount
        return
    if c.type == "current_source_dc":
        row[i_i] = ONE
        known[0] = c.value.amount
        return
    raise ValueError(f"{c.id}: {c.type} non ammesso nel tableau DC resistivo")


def solve_dc_tableau(ir: IR) -> dict[str, dict[str, Fraction]]:
    """Risolve il tableau di ramo. Restituisce tensione e corrente per componente."""
    rami = list(ir.components)
    m = len(rami)
    if m == 0:
        raise TableauBuildError("tableau senza rami")
    for c in rami:
        if c.type not in DC_TABLEAU_TYPES:
            raise ValueError(f"{c.id}: {c.type} non ammesso nel tableau DC resistivo")

    parent, rami_albero = _albero_ricoprente(ir)
    corde = [c for c in rami if c.id not in rami_albero]
    nodi_kcl = [n for n in ir.nodes if n != REFERENCE_NODE and n in parent]

    n_eq = len(nodi_kcl) + len(corde) + m
    n_inc = 2 * m
    if n_eq != n_inc:  # pragma: no cover - invariante del costruttore
        raise TableauBuildError(
            f"tableau non quadrato: {n_eq} equazioni, {n_inc} incognite"
        )

    idx = {c.id: i for i, c in enumerate(rami)}

    def col_v(cid: str) -> int:
        return idx[cid]

    def col_i(cid: str) -> int:
        return m + idx[cid]

    a = [[ZERO] * n_inc for _ in range(n_eq)]
    b = [ZERO] * n_eq
    r = 0

    for nodo in nodi_kcl:
        for c in rami:
            t0, t1 = c.terminals
            if t0 == nodo:
                a[r][col_i(c.id)] -= ONE
            elif t1 == nodo:
                a[r][col_i(c.id)] += ONE
        r += 1

    for corda in corde:
        t0, t1 = corda.terminals
        a[r][col_v(corda.id)] += ONE
        for cid, segno in _percorso_albero(ir, parent, t1, t0):
            a[r][col_v(cid)] += segno
        r += 1

    for c in rami:
        known = [ZERO]
        _costitutiva(c, col_v(c.id), col_i(c.id), a[r], known)
        b[r] = known[0]
        r += 1

    if r != n_eq:  # pragma: no cover - invariante del costruttore
        raise TableauBuildError(f"righe scritte {r}, attese {n_eq}")

    x = solve_tableau_linear(a, b)
    out: dict[str, dict[str, Fraction]] = {}
    for c in rami:
        i = idx[c.id]
        out[c.id] = {"voltage": x[i], "current": x[m + i]}
    return out
