"""Story 1.3 — il `ProofGraph`, proprietario del riferimento al `LayoutIR`.

AD-8 v2.1: *«Il proprietario del riferimento e' **il nodo**, non la sessione»*.
AD-29: nodi = stati circuitali, archi = `Transform`, diramazione e ricongiungimento
supportati dallo schema fin da subito.
"""

from __future__ import annotations

import pytest

from kirchhoff.domain.identity import conia
from kirchhoff.domain.proof import ProofEdge, ProofGraph, ProofNode

ENTROPIA = bytes(range(10))


def _ir(n: int) -> str:
    return conia("ir", n, ENTROPIA)


def _lay(n: int) -> str:
    return conia("lay", n, ENTROPIA)


def _patch(nome: str) -> str:
    """Un `patch_` coniato come lo conia il registro: un ULID, uno per passo.

    L'istante e' derivato dal nome — deterministico, senza stato condiviso fra i
    test — cosi' che nomi distinti diano passi distinti e riusare un nome scriva
    «lo stesso passo» dove un test lo vuole.
    """
    return conia("patch", int.from_bytes(nome.encode(), "big"), ENTROPIA)


def _catena(quanti: int) -> ProofGraph:
    """Una derivazione lineare di `quanti` passi, con `quanti + 1` stati."""
    grafo = ProofGraph().con_stato_iniziale(ProofNode(_ir(0), _lay(0)))
    for k in range(1, quanti + 1):
        grafo = grafo.con_passo(
            ProofNode(_ir(k), _lay(k)),
            ProofEdge(_ir(k - 1), _ir(k), "serie", _patch(f"p{k}")))
    return grafo


# --- ProofNode ---------------------------------------------------------------

def test_un_nodo_porta_due_identificatori_e_nessuna_struttura():
    """AD-21 ammette il riferimento per identificatore e vieta il contenimento."""
    assert tuple(ProofNode.__slots__) == ("identifier", "layout")


def test_un_nodo_e_uno_stato_circuitale_quindi_ha_un_prefisso_ir():
    with pytest.raises(ValueError, match="atteso il prefisso 'ir_'"):
        ProofNode(_lay(1), _lay(2))


def test_un_nodo_rifiuta_un_layout_che_non_e_un_layout():
    with pytest.raises(ValueError, match="atteso il prefisso 'lay_'"):
        ProofNode(_ir(1), _patch("x"))


# --- ProofEdge ---------------------------------------------------------------

def test_un_arco_porta_il_patch_che_rende_congiungibile_la_tripla_di_cv6():
    arco = ProofEdge(_ir(0), _ir(1), "serie", _patch("p"))
    assert arco.patch.startswith("patch_")


def test_un_arco_rifiuta_un_operazione_fuori_dal_catalogo():
    """Gli archi sono `Transform` (AD-29), e le Trasformazioni sono quelle."""
    with pytest.raises(ValueError, match="fuori dal catalogo chiuso"):
        ProofEdge(_ir(0), _ir(1), "fusione_di_componenti", _patch("p"))


def test_un_arco_rifiuta_un_identificatore_di_patch_di_un_altro_genere():
    with pytest.raises(ValueError, match="atteso il prefisso 'patch_'"):
        ProofEdge(_ir(0), _ir(1), "serie", _lay(3))


@pytest.mark.parametrize("capo", ["source", "target"])
def test_un_arco_rifiuta_un_capo_che_non_e_uno_stato_circuitale(capo):
    campi = {"source": _ir(0), "target": _ir(1)}
    campi[capo] = _lay(9)
    with pytest.raises(ValueError, match="atteso il prefisso 'ir_'"):
        ProofEdge(operation="serie", patch=_patch("p"), **campi)


def test_un_arco_su_se_stesso_darebbe_a_vcer_due_operandi_uguali():
    with pytest.raises(ValueError, match="arco su se stesso"):
        ProofEdge(_ir(0), _ir(0), "serie", _patch("p"))


# --- ProofGraph: le guardie --------------------------------------------------

def test_un_grafo_vuoto_e_costruibile():
    """La derivazione comincia da nessuno stato, non da uno stato fittizio."""
    assert ProofGraph().nodes == () == ProofGraph().edges


@pytest.mark.parametrize("campo,atteso", [("nodes", "ProofNode"), ("edges", "ProofEdge")])
def test_un_grafo_rifiuta_membri_del_tipo_sbagliato(campo, atteso):
    with pytest.raises(TypeError, match=f"invece di {atteso}"):
        ProofGraph(**{campo: ("non un membro",)})  # type: ignore[arg-type]


def test_due_nodi_con_lo_stesso_stato_circuitale_sono_un_nodo_riscritto():
    with pytest.raises(ValueError, match="stato circuitale ripetuto"):
        ProofGraph((ProofNode(_ir(0), _lay(0)), ProofNode(_ir(0), _lay(1))))


def test_due_nodi_non_possono_condividere_lo_stesso_stato_visuale():
    """E' la meta' strutturale della ritenzione: il registro impedisce di
    sovrascrivere un layout, questa guardia impedisce di riusarlo."""
    with pytest.raises(ValueError, match="stato visuale condiviso"):
        ProofGraph((ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(0))))


@pytest.mark.parametrize("capo", ["source", "target"])
def test_un_arco_non_puo_nominare_un_nodo_che_non_esiste(capo):
    campi = {"source": _ir(0), "target": _ir(1)}
    campi[capo] = _ir(9)
    with pytest.raises(ValueError, match="non e' un nodo di questo grafo"):
        ProofGraph((ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1))),
                   (ProofEdge(operation="serie", patch=_patch("p"), **campi),))


def test_un_grafo_senza_nodi_ma_con_un_arco_lo_dice():
    with pytest.raises(ValueError, match="Nodi: nessuno"):
        ProofGraph((), (ProofEdge(_ir(0), _ir(1), "serie", _patch("p")),))


def test_lo_stesso_passo_dichiarato_due_volte_conta_due_volte_in_vcer():
    arco = ProofEdge(_ir(0), _ir(1), "serie", _patch("p"))
    with pytest.raises(ValueError, match="arco ripetuto"):
        ProofGraph((ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1))),
                   (arco, arco))


def test_due_passi_diversi_fra_gli_stessi_stati_sono_ammessi():
    """Ricongiungimento: AD-29 lo vuole supportato dallo schema fin da subito,
    anche se l'MVP non lo produce."""
    grafo = ProofGraph(
        (ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1))),
        (ProofEdge(_ir(0), _ir(1), "serie", _patch("p")),
         ProofEdge(_ir(0), _ir(1), "parallelo", _patch("q"))))
    assert len(grafo.transizioni()) == 2


def test_una_diramazione_e_ammessa():
    grafo = _catena(1).con_passo(
        ProofNode(_ir(2), _lay(2)),
        ProofEdge(_ir(0), _ir(2), "parallelo", _patch("q")))
    assert grafo.nodo_di(_lay(2)) == _ir(2)


def test_uno_stato_che_discende_da_se_stesso_e_un_ciclo():
    with pytest.raises(ValueError, match="ha un ciclo"):
        ProofGraph(
            (ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1))),
            (ProofEdge(_ir(0), _ir(1), "serie", _patch("p")),
             ProofEdge(_ir(1), _ir(0), "parallelo", _patch("q"))))


def test_il_ciclo_e_nominato_e_non_solo_annunciato():
    """Una diagnosi che non nomina l'elemento coinvolto non e' utilizzabile."""
    with pytest.raises(ValueError, match=_ir(1)):
        ProofGraph(
            (ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1)),
             ProofNode(_ir(2), _lay(2))),
            (ProofEdge(_ir(0), _ir(1), "serie", _patch("a")),
             ProofEdge(_ir(1), _ir(2), "serie", _patch("b")),
             ProofEdge(_ir(2), _ir(1), "parallelo", _patch("c"))))


# --- ProofGraph: le due direzioni --------------------------------------------

def test_la_relazione_si_interroga_da_nodo_a_layout():
    assert _catena(2).layout_di(_ir(1)) == _lay(1)


def test_la_relazione_si_interroga_da_layout_a_nodo():
    assert _catena(2).nodo_di(_lay(1)) == _ir(1)


def test_le_due_direzioni_sono_l_una_l_inversa_dell_altra():
    grafo = _catena(2)
    for nodo in grafo.nodes:
        assert grafo.nodo_di(grafo.layout_di(nodo.identifier)) == nodo.identifier


def test_chiedere_il_layout_di_un_nodo_inesistente_elenca_i_nodi():
    with pytest.raises(KeyError, match="non e' un nodo di questo grafo"):
        _catena(1).layout_di(_ir(9))


def test_chiedere_il_nodo_di_un_layout_inesistente_elenca_i_layout():
    with pytest.raises(KeyError, match="non e' il layout di alcun nodo"):
        _catena(1).nodo_di(_lay(9))


@pytest.mark.parametrize("interrogazione", ["layout_di", "nodo_di"])
def test_su_un_grafo_vuoto_le_due_direzioni_dicono_nessuno(interrogazione):
    with pytest.raises(KeyError, match="nessuno"):
        getattr(ProofGraph(), interrogazione)(_ir(0))


# --- ProofGraph: append-only --------------------------------------------------

def test_estendere_restituisce_un_grafo_nuovo_e_non_tocca_il_precedente():
    prima = _catena(1)
    dopo = prima.con_passo(ProofNode(_ir(2), _lay(2)),
                           ProofEdge(_ir(1), _ir(2), "serie", _patch("p2")))
    assert len(prima.nodes) == 2
    assert len(dopo.nodes) == 3


def test_un_passo_deve_arrivare_allo_stato_che_aggiunge():
    with pytest.raises(ValueError, match="un passo porta allo stato che aggiunge"):
        _catena(1).con_passo(
            ProofNode(_ir(2), _lay(2)),
            ProofEdge(_ir(0), _ir(1), "serie", _patch("p")))


def test_non_esiste_un_modo_di_sostituire_il_layout_di_un_nodo():
    """Non e' un'omissione: e' la forma che AD-8 v2.1 impone."""
    assert not [nome for nome in dir(ProofGraph)
                if nome.startswith(("sostituisci", "aggiorna", "set_"))]


def test_riusare_uno_stato_visuale_gia_legato_e_rifiutato_anche_estendendo():
    with pytest.raises(ValueError, match="stato visuale condiviso"):
        _catena(1).con_passo(
            ProofNode(_ir(2), _lay(0)),
            ProofEdge(_ir(1), _ir(2), "serie", _patch("p2")))


def test_lo_stato_iniziale_non_ha_un_arco_fittizio():
    """Dargliene uno dichiarerebbe un passo che nessun `Certificate` attesta."""
    grafo = ProofGraph().con_stato_iniziale(ProofNode(_ir(0), _lay(0)))
    assert grafo.edges == ()


def test_piu_radici_sono_ammesse():
    grafo = _catena(1).con_stato_iniziale(ProofNode(_ir(7), _lay(7)))
    assert grafo.layout_di(_ir(7)) == _lay(7)


# --- ProofGraph: la tripla di CV6 --------------------------------------------

def test_transizioni_da_la_tripla_patch_layout_layout_per_ogni_passo():
    """*«per ogni passo, la tripla `(LayoutPatch, LayoutIR_k, LayoutIR_{k+1})`
    congiungibile»* — CV6, secondo rilievo."""
    assert _catena(2).transizioni() == (
        (_patch("p1"), _lay(0), _lay(1)),
        (_patch("p2"), _lay(1), _lay(2)),
    )


def test_un_grafo_senza_passi_non_ha_transizioni():
    assert ProofGraph().con_stato_iniziale(
        ProofNode(_ir(0), _lay(0))).transizioni() == ()


# --- ProofGraph: cio' che il costruttore deve congelare -----------------------

def test_i_nodi_e_gli_archi_si_congelano_in_tuple():
    """Una lista passata al costruttore resta condivisa col chiamante: le guardie
    passerebbero sul contenuto di allora e non su quello di poi."""
    nodi = [ProofNode(_ir(0), _lay(0))]
    grafo = ProofGraph(nodi, [])
    assert isinstance(grafo.nodes, tuple) and isinstance(grafo.edges, tuple)
    assert hash(grafo) is not None


def test_un_append_esterno_non_aggiunge_un_nodo_al_grafo():
    """Il difetto che il congelamento chiude: dopo l'`append` il grafo conterrebbe
    due nodi sullo stesso `lay_` — cio' che la guardia sui layout condivisi vieta —
    e `nodo_di` smetterebbe di essere una funzione."""
    nodi = [ProofNode(_ir(0), _lay(0))]
    grafo = ProofGraph(nodi, [])

    nodi.append(ProofNode(_ir(1), _lay(0)))

    assert len(grafo.nodes) == 1
    assert grafo.nodo_di(_lay(0)) == _ir(0)


def test_due_archi_non_possono_portare_lo_stesso_patch():
    """SM-14 conta i `LayoutPatch` che violano la continuita': se due archi ne
    condividessero uno, un'evidenza «`patch_X` viola VCER» non saprebbe a quale
    passo riferirsi e il denominatore conterebbe un contenuto invece di un passo."""
    nodi = (ProofNode(_ir(0), _lay(0)), ProofNode(_ir(1), _lay(1)),
            ProofNode(_ir(2), _lay(2)))
    condiviso = _patch("z")

    with pytest.raises(ValueError, match="condiviso da piu' archi"):
        ProofGraph(nodi, (ProofEdge(_ir(0), _ir(1), "serie", condiviso),
                          ProofEdge(_ir(1), _ir(2), "serie", condiviso)))


def test_due_passi_con_patch_distinte_si_costruiscono():
    """Il confine sta sul `patch_`, non sul contenuto: due passi consecutivi con la
    stessa forma sono legittimi, e il registro conia loro due nomi."""
    assert len(_catena(2).transizioni()) == 2
