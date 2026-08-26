"""Story 1.3 — le cinque condizioni che rendono la tripla di CV6 davvero congiunta.

`test_continuita_visuale.py` verifica che la giunzione riesca su una derivazione
vera. Qui si verifica che **fallisca** dove deve: tre risoluzioni indipendenti
riescono anche quando la tripla non significa nulla, e una metrica calcolata su
operandi incoerenti e' peggio di una metrica assente.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.identity import conia
from kirchhoff.domain.proof import ProofEdge, ProofGraph, ProofNode
from kirchhoff.domain.transform import EntityRef, LayoutPatch
from kirchhoff.render.layout import (
    LayoutIR,
    LayoutStore,
    PatchStore,
    Placement,
    operandi_di_vcer,
)

F = Fraction
C = lambda i: EntityRef("component", i)      # noqa: E731

ENTROPIA = bytes(range(10))


def _monta(patch: LayoutPatch, prima: tuple[EntityRef, ...],
           dopo: tuple[EntityRef, ...]):
    """Un passo solo: due stati visuali, una patch, e i tre registri che li tengono.

    Restituisce `(grafo, layout, registro_patch)`, gia' depositati. Le coordinate
    non contano: cio' che si misura qui e' quali entita' sono piazzate.
    """
    layout, registro = LayoutStore(), PatchStore()
    uno = LayoutIR.nuovo(tuple(Placement(e, F(i), F(0)) for i, e in enumerate(prima)),
                         istante=1_000, casualita=ENTROPIA)
    due = LayoutIR.nuovo(tuple(Placement(e, F(i), F(0)) for i, e in enumerate(dopo)),
                         istante=2_000, casualita=ENTROPIA)
    layout.deposita(uno)
    layout.deposita(due)
    identificatore = registro.deposita(patch, istante=1_500, casualita=ENTROPIA)

    sorgente, bersaglio = conia("ir", 1, ENTROPIA), conia("ir", 2, ENTROPIA)
    grafo = ProofGraph(
        (ProofNode(sorgente, uno.identifier), ProofNode(bersaglio, due.identifier)),
        (ProofEdge(sorgente, bersaglio, "serie", identificatore),))
    return grafo, layout, registro


def test_una_tripla_coerente_si_congiunge():
    patch = LayoutPatch((C("R3"),), (C("R1"), C("R2")), (C("Req"),), (C("Req"),))
    grafo, layout, registro = _monta(
        patch, (C("R1"), C("R2"), C("R3")), (C("Req"), C("R3")))

    operandi = operandi_di_vcer(grafo, layout, registro)

    assert len(operandi) == 1
    assert operandi[0].patch is patch
    assert operandi[0].dominio() == (C("R3"),)
    assert operandi[0].prima.posizione(C("R3")).x == F(2)
    assert operandi[0].dopo.posizione(C("R3")).x == F(1)


def test_un_grafo_senza_passi_da_nessun_operando():
    layout, registro = LayoutStore(), PatchStore()
    uno = LayoutIR.nuovo((Placement(C("R1"), F(0), F(0)),), istante=1,
                         casualita=ENTROPIA)
    layout.deposita(uno)
    grafo = ProofGraph().con_stato_iniziale(
        ProofNode(conia("ir", 1, ENTROPIA), uno.identifier))
    assert operandi_di_vcer(grafo, layout, registro) == ()


# --- le cinque condizioni, ciascuna vista fallire ----------------------------

def test_un_nodo_che_nomina_un_layout_mai_depositato_solleva():
    """L'integrita' referenziale che mancava: la relazione era interrogabile e non
    risolvibile, e `layout_di` restituiva un nome che nessun registro conosce."""
    grafo, layout, registro = _monta(
        LayoutPatch((C("R1"),), (), (), (C("R1"),)), (C("R1"),), (C("R1"),))
    orfano = ProofGraph(
        (ProofNode(conia("ir", 5, ENTROPIA), conia("lay", 5, ENTROPIA)),), ())

    with pytest.raises(KeyError, match="non e' depositato"):
        operandi_di_vcer(orfano, layout, registro)


def test_un_arco_che_nomina_una_patch_mai_depositata_solleva():
    grafo, layout, registro = _monta(
        LayoutPatch((C("R1"),), (), (), (C("R1"),)), (C("R1"),), (C("R1"),))
    arco = grafo.edges[0]
    storto = ProofGraph(grafo.nodes, (ProofEdge(
        arco.source, arco.target, arco.operation, conia("patch", 9, ENTROPIA)),))

    with pytest.raises(KeyError, match="manca `preserve`"):
        operandi_di_vcer(storto, layout, registro)


def test_preservare_un_entita_non_piazzata_nel_primo_stato_solleva():
    """`p_k(x)` non e' definita, quindi `p_{k+1}(x) ≈ p_k(x)` non ha due operandi:
    SM-14 misurerebbe un `KeyError` invece della continuita' visuale."""
    grafo, layout, registro = _monta(
        LayoutPatch((C("R9"),), (), (), (C("R9"),)), (C("R1"),), (C("R9"),))

    with pytest.raises(ValueError, match="in `preserve` ma non piazzata"):
        operandi_di_vcer(grafo, layout, registro)


def test_preservare_un_entita_non_piazzata_nel_secondo_stato_solleva():
    grafo, layout, registro = _monta(
        LayoutPatch((C("R1"),), (), (), (C("R1"),)), (C("R1"),), (C("R9"),))

    with pytest.raises(ValueError, match="in `preserve` ma non piazzata"):
        operandi_di_vcer(grafo, layout, registro)


def test_rimuovere_un_entita_che_non_c_era_solleva():
    grafo, layout, registro = _monta(
        LayoutPatch((), (C("R9"),), (), (C("R9"),)), (C("R1"),), (C("R2"),))

    with pytest.raises(ValueError, match="in `remove` ma non piazzata"):
        operandi_di_vcer(grafo, layout, registro)


def test_creare_un_entita_che_non_compare_dopo_solleva():
    grafo, layout, registro = _monta(
        LayoutPatch((), (), (C("R9"),), (C("R9"),)), (C("R1"),), (C("R2"),))

    with pytest.raises(ValueError, match="in `create` ma non piazzata"):
        operandi_di_vcer(grafo, layout, registro)


def test_la_giunzione_rifiuta_cio_che_non_e_un_grafo():
    with pytest.raises(TypeError, match="invece di ProofGraph"):
        operandi_di_vcer("ir_" + "0" * 26, LayoutStore(),  # type: ignore[arg-type]
                         PatchStore())


def test_la_giunzione_non_giudica_la_continuita():
    """Non-goal dichiarato: la tolleranza del `≈` e' owner-locked, e chi calcola la
    metrica e' `eval/` (AD-15).

    Qui l'entita' preservata **si sposta** da `x=0` a `x=99`: e' esattamente cio' che
    VCER conterebbe come violazione, e la giunzione lo lascia passare restituendo i
    due operandi. Se un giorno sollevasse, `eval/` non avrebbe piu' da misurare i
    passi che violano la continuita' — li avrebbe gia' persi.
    """
    layout, registro = LayoutStore(), PatchStore()
    prima = LayoutIR(conia("lay", 1, ENTROPIA), (Placement(C("R1"), F(0), F(0)),))
    dopo = LayoutIR(conia("lay", 2, ENTROPIA), (Placement(C("R1"), F(99), F(0)),))
    layout.deposita(prima)
    layout.deposita(dopo)
    identificatore = registro.deposita(
        LayoutPatch((C("R1"),), (), (), (C("R1"),)), istante=1, casualita=ENTROPIA)
    sorgente, bersaglio = conia("ir", 1, ENTROPIA), conia("ir", 2, ENTROPIA)
    grafo = ProofGraph(
        (ProofNode(sorgente, prima.identifier), ProofNode(bersaglio, dopo.identifier)),
        (ProofEdge(sorgente, bersaglio, "serie", identificatore),))

    operandi = operandi_di_vcer(grafo, layout, registro)

    assert operandi[0].prima.posizione(C("R1")).x == F(0)
    assert operandi[0].dopo.posizione(C("R1")).x == F(99)
