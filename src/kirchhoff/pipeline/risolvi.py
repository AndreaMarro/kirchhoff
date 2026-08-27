"""Disposizione a una maglia e alias dello spine.

Il percorso di prodotto vive in `resolve`. Questo modulo tiene ciò che è
disegno — `layout_a_maglia` — e i nomi storici `risolvi` / `Risolto`, perché
non esiste un secondo modo di risolvere.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction

from kirchhoff.domain import mna
from kirchhoff.domain.ir import IR
from kirchhoff.domain.identity import conia
from kirchhoff.domain.transform import EntityRef
from kirchhoff.pipeline.resolve import Solved, risolvi as _risolvi
from kirchhoff.render.layout import LayoutIR, Placement

PASSO = Fraction(200)
Risolto = Solved


def _giro(circuito: IR) -> list[str] | None:
    """L'ordine dei nodi lungo l'unica maglia, o None se maglia non è."""
    vicini: dict[str, list[tuple[str, str]]] = {n: [] for n in circuito.nodes}
    for c in circuito.components:
        a, b = c.terminals
        vicini[a].append((b, c.id))
        vicini[b].append((a, c.id))
    if any(len(v) != 2 for v in vicini.values()):
        return None

    giro, visti = [mna.REFERENCE_NODE], set()
    corrente = mna.REFERENCE_NODE
    while len(visti) < len(circuito.components):
        passi = [(n, cid) for n, cid in vicini[corrente] if cid not in visti]
        if not passi:
            return None
        prossimo, cid = passi[0]
        visti.add(cid)
        if prossimo != mna.REFERENCE_NODE:
            giro.append(prossimo)
        corrente = prossimo
    return giro if len(giro) == len(circuito.nodes) else None


def layout_a_maglia(circuito: IR) -> LayoutIR:
    """Dispone un circuito a UNA maglia, e rifiuta gli altri.

    Non è autolayout e non finge di esserlo. Un circuito che non è a una
    maglia solleva: chi pubblica i numeri è `resolve`, che tratta questa
    eccezione come «niente disegno», non come crash del prodotto.
    """
    giro = _giro(circuito)
    if giro is None:
        raise ValueError(
            f"{len(circuito.components)} bipoli su {len(circuito.nodes)} nodi non "
            "formano una maglia sola: questa disposizione farebbe passare fili "
            "attraverso nodi che non toccano, e il renderer la rifiuterebbe. "
            "L'autolayout generale è un non-goal dichiarato: passa un LayoutIR "
            "costruito a mano.")

    n = len(giro)
    if n == 2:
        posti = [(Fraction(0), Fraction(0)), (Fraction(0), PASSO)]
    elif n == 3:
        posti = [(PASSO / 2, PASSO), (Fraction(0), Fraction(0)), (PASSO, Fraction(0))]
    else:
        lato = (n + 3) // 4
        perimetro = ([(PASSO * i, Fraction(0)) for i in range(lato + 1)]
                     + [(PASSO * lato, PASSO * i) for i in range(1, lato + 1)]
                     + [(PASSO * (lato - i), PASSO * lato) for i in range(1, lato + 1)]
                     + [(Fraction(0), PASSO * (lato - i)) for i in range(1, lato)])
        posti = perimetro[:n]

    dove = {nodo: posti[i] for i, nodo in enumerate(giro)}
    piazzamenti = [Placement(EntityRef("node", nodo), *dove[nodo]) for nodo in sorted(giro)]
    per_coppia: dict[frozenset[str], list] = {}
    for c in sorted(circuito.components, key=lambda c: c.id):
        per_coppia.setdefault(frozenset(c.terminals), []).append(c)

    for coppia, gruppo in sorted(per_coppia.items(), key=lambda kv: sorted(kv[0])):
        for k, c in enumerate(gruppo):
            (x1, y1), (x2, y2) = dove[c.terminals[0]], dove[c.terminals[1]]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if len(gruppo) > 1:
                mx += PASSO * (k - Fraction(len(gruppo) - 1, 2))
            piazzamenti.append(Placement(EntityRef("component", c.id), mx, my))

    impronta = hashlib.blake2b(
        "|".join(f"{p.entity.kind}:{p.entity.id}@{p.x},{p.y}" for p in piazzamenti)
        .encode("utf-8"), digest_size=16).digest()
    return LayoutIR(
        identifier=conia("lay", int.from_bytes(impronta[:6], "big"), impronta[6:16]),
        placements=tuple(piazzamenti))


def risolvi(circuito: IR, layout: LayoutIR | None = None):
    """Unico ingresso: delega a `resolve`. Non risolve da sé."""
    return _risolvi(circuito, layout)
