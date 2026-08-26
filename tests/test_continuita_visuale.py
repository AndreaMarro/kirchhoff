"""Story 1.3 — i criteri di accettazione, su una derivazione vera di due passi.

> **Given** una derivazione di due passi
> **When** si chiede lo stato visuale del passo `k` dopo che `k+1` e' stato prodotto
> **Then** `LayoutIR_k` e' ancora recuperabile e non e' stato sovrascritto
> **And** `LayoutIR` e `LayoutPatch` hanno un identificatore proprio secondo le convenzioni
> **And** la relazione fra nodo della derivazione e layout e' interrogabile in entrambe le direzioni.

I passi sono prodotti da `transform`, non simulati: e' l'unica maniera di sapere che
il `LayoutPatch` che finisce sull'arco e' quello che la Trasformazione ha davvero
emesso.
"""

from __future__ import annotations

from fractions import Fraction
from typing import NamedTuple

import pytest

from kirchhoff.domain.identity import conia, genere_di
from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.proof import ProofEdge, ProofGraph, ProofNode
from kirchhoff.domain.transform import EntityRef, LayoutPatch, transform
from kirchhoff.render.layout import (
    LayoutIR,
    LayoutStore,
    PatchStore,
    Placement,
    operandi_di_vcer,
)

F = Fraction
ENTROPIA = bytes(range(10))


def _r(cid: str, a: str, b: str, ohm: int) -> Component:
    return Component.of(cid, "resistor", (a, b), F(ohm), cid)


#: `R1 — R2 — R3` in serie fra `a` e `0`, alimentati da `V1`. Due riduzioni in
#: serie di fila: la prima fonde `R1` e `R2`, la seconda l'equivalente con `R3`.
TRE_IN_SERIE = IR(
    "1.0.0", "dc_resistive", "netlist", ("0", "a", "b", "c"),
    (Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
     _r("R1", "a", "b", 10), _r("R2", "b", "c", 20), _r("R3", "c", "0", 30)),
    ())


def _entita_di(ir: IR) -> tuple[EntityRef, ...]:
    """Le entita' che un circuito espone a chi lo disegna: nodi e componenti."""
    return (*(EntityRef("node", n) for n in sorted(ir.nodes)),
            *(EntityRef("component", c.id)
              for c in sorted(ir.components, key=lambda c: c.id)))


def _piazzamento_di_prova(ir: IR, istante: int) -> LayoutIR:
    """Uno stato visuale per `ir`, deterministico. **Non e' un renderer.**

    La Story 1.3 dichiara non-goal il renderer: qui serve solo un `LayoutIR` che
    nomini le entita' di quel circuito, perche' cio' che si misura e' la ritenzione
    e la relazione, non il piazzamento. Le coordinate sono una progressione: chi
    scrivera' 1.4 non ha nessuna ragione di guardarle.
    """
    return LayoutIR.nuovo(
        tuple(Placement(e, F(i), F(0)) for i, e in enumerate(_entita_di(ir))),
        istante=istante, casualita=ENTROPIA)


class Derivazione(NamedTuple):
    """Tutto cio' che la derivazione ha prodotto, senza scartare gli oggetti.

    `circuiti` e' qui perche' senza di esso nessun test puo' dire che il nodo `k`
    denoti davvero `Cₖ`: una permutazione degli `ir_` fra i nodi passerebbe una
    suite che guarda solo gli identificatori.
    """

    grafo: ProofGraph
    layout: LayoutStore
    patch: PatchStore
    circuiti: tuple[IR, ...]
    stati: tuple[str, ...]
    patch_id: tuple[str, ...]


@pytest.fixture
def derivazione() -> Derivazione:
    """La derivazione di due passi, con i tre stati visuali e le due patch ritenuti."""
    layout, patch = LayoutStore(), PatchStore()
    circuiti = [TRE_IN_SERIE]
    emesse: list[LayoutPatch] = []

    esito = transform(TRE_IN_SERIE, "serie", "R1", "R2")
    circuiti.append(esito[0])
    emesse.append(esito[1].layout_patch)

    esito = transform(circuiti[-1], "serie", "R1R2eq", "R3")
    circuiti.append(esito[0])
    emesse.append(esito[1].layout_patch)

    # Un `LayoutIR` per stato circuitale, depositato al momento in cui lo stato
    # nasce; una `LayoutPatch` per passo, depositata al momento del passo. Gli
    # istanti sono iniettati: un test che non puo' fermare l'orologio non puo'
    # verificare l'ordinamento dei ULID. L'entropia e' costante e va bene solo
    # perche' qui gli istanti sono distinti per costruzione.
    stati_visuali = [_piazzamento_di_prova(ir, 1_000 * (k + 1))
                     for k, ir in enumerate(circuiti)]
    for uno in stati_visuali:
        layout.deposita(uno)
    patch_id = [patch.deposita(una, istante=1_500 * (k + 1), casualita=ENTROPIA)
                for k, una in enumerate(emesse)]

    stati = [conia("ir", 1_000 * (k + 1), ENTROPIA) for k in range(len(circuiti))]
    grafo = ProofGraph().con_stato_iniziale(
        ProofNode(stati[0], stati_visuali[0].identifier))
    for k in (1, 2):
        grafo = grafo.con_passo(
            ProofNode(stati[k], stati_visuali[k].identifier),
            ProofEdge(stati[k - 1], stati[k], "serie", patch_id[k - 1]))

    return Derivazione(grafo, layout, patch, tuple(circuiti), tuple(stati),
                       tuple(patch_id))


# --- Then: `LayoutIR_k` e' ancora recuperabile e non e' stato sovrascritto ----

def test_lo_stato_visuale_del_passo_k_sopravvive_al_passo_successivo(derivazione):
    """CV6, nella sua forma piu' corta: *«Con U2, `p_k` non esiste piu' nel momento
    in cui servirebbe misurarlo»*. Qui esiste."""
    d = derivazione
    intermedio = d.grafo.nodes[1].identifier

    p_k = d.layout.risolvi(d.grafo.layout_di(intermedio))

    # Lo stato intermedio: `R1` e `R2` fusi, il nodo `b` che li univa sparito, `R3`
    # ancora al proprio posto. E' esattamente cio' che il secondo passo cancella.
    assert p_k.entita() == {EntityRef("node", n) for n in ("0", "a", "c")} | {
        EntityRef("component", c) for c in ("V1", "R1R2eq", "R3")}


def test_i_piazzamenti_del_passo_k_sono_quelli_di_prima_non_solo_le_entita(derivazione):
    """AC1 alla lettera: *«non e' stato sovrascritto»*. Un registro che riscrivesse
    le coordinate lasciando intatti `lay_` ed entita' e' il caso di CV6 — `p_k`
    esiste ma non e' piu' quello di prima — e ogni altro test qui lo accetterebbe."""
    d = derivazione
    for k, ir in enumerate(d.circuiti):
        recuperato = d.layout.risolvi(d.grafo.layout_di(d.stati[k]))
        # `sorted` perche' `LayoutIR` canonicalizza l'ordine dei piazzamenti; le
        # coordinate restano quelle che `_piazzamento_di_prova` aveva assegnato, ed
        # e' su quelle che il confronto morde.
        assert recuperato.placements == tuple(sorted(
            Placement(e, F(i), F(0)) for i, e in enumerate(_entita_di(ir))))


def test_ogni_nodo_denota_il_proprio_circuito_e_non_un_altro(derivazione):
    """Senza questo, una permutazione degli `ir_` fra i nodi passerebbe la suite:
    il grafo resterebbe coerente e nessuno saprebbe che il nodo `k` ha smesso di
    essere lo stato visuale di `Cₖ`."""
    d = derivazione
    for k, ir in enumerate(d.circuiti):
        stato_visuale = d.layout.risolvi(d.grafo.layout_di(d.stati[k]))
        assert stato_visuale.entita() == frozenset(_entita_di(ir))
    # I tre circuiti hanno entita' diverse a due a due, quindi il controllo sopra
    # distingue davvero: se fossero uguali passerebbe per ogni permutazione.
    insiemi = [frozenset(_entita_di(ir)) for ir in d.circuiti]
    assert len({tuple(sorted(map(str, i))) for i in insiemi}) == len(insiemi)


def test_i_tre_stati_visuali_sono_tre_e_nessuno_ha_sovrascritto_gli_altri(derivazione):
    d = derivazione
    stati_visuali = [n.layout for n in d.grafo.nodes]

    assert len(set(stati_visuali)) == 3 == len(d.layout)
    assert all(d.layout.risolvi(uno).identifier == uno for uno in stati_visuali)


def test_i_due_operandi_di_vcer_si_risolvono_senza_rieseguire_la_derivazione(derivazione):
    """*«`eval/` risolve la coppia `(LayoutIR_k, LayoutIR_{k+1})` dai due nodi
    adiacenti senza rieseguire nulla»* — AD-8 v2.1. E' la riga che rompe la
    dipendenza circolare con SM-20."""
    d = derivazione

    for _, lay_k, lay_successivo in d.grafo.transizioni():
        prima, dopo = d.layout.risolvi(lay_k), d.layout.risolvi(lay_successivo)
        assert prima.identifier != dopo.identifier
        assert prima.entita() != dopo.entita()


def test_un_secondo_deposito_sullo_stesso_layout_e_rifiutato(derivazione):
    """La ritenzione non e' una proprieta' del `LayoutIR`: e' una proprieta' del
    posto in cui sta, e va imposta li'."""
    d = derivazione
    esistente = d.layout.risolvi(d.grafo.nodes[0].layout)

    with pytest.raises(ValueError, match="append-only e mai sovrascritto"):
        d.layout.deposita(esistente)


# --- And: identificatori propri, secondo le convenzioni ----------------------

def test_ogni_stato_visuale_ha_un_identificatore_lay(derivazione):
    assert all(genere_di(n.layout) == "lay" for n in derivazione.grafo.nodes)


def test_ogni_patch_del_passo_ha_un_identificatore_patch(derivazione):
    assert [genere_di(p) for p in derivazione.patch_id] == ["patch", "patch"]


def test_i_due_passi_hanno_patch_distinte(derivazione):
    """Il denominatore di VCER conta i `LayoutPatch`: due passi che ne
    condividessero uno conterebbero una volta sola."""
    assert len(set(derivazione.patch_id)) == 2


def test_i_due_identificatori_sono_ulid_e_ordinano_per_istante(derivazione):
    """Le convenzioni dicono «ULID» per entrambi i generi, e un ULID porta dentro
    l'istante: i tre stati e le due patch sono nati in quest'ordine."""
    d = derivazione
    stati_visuali = [n.layout for n in d.grafo.nodes]
    assert stati_visuali == sorted(stati_visuali)
    assert list(d.patch_id) == sorted(d.patch_id)


def test_la_tripla_di_cv6_e_congiungibile(derivazione):
    """*«perche' la metrica sia calcolabile serve, per ogni passo, la tripla
    `(LayoutPatch, LayoutIR_k, LayoutIR_{k+1})` congiungibile»*."""
    d = derivazione

    triple = d.grafo.transizioni()

    assert tuple(p for p, _, _ in triple) == d.patch_id
    for identificatore, lay_k, lay_successivo in triple:
        assert genere_di(identificatore) == "patch"
        assert identificatore in d.patch
        assert {lay_k, lay_successivo} <= set(d.layout.identificatori())


def test_gli_operandi_di_vcer_si_risolvono_tutti_e_tre(derivazione):
    """Il «so that» della storia: *«VCER sia calcolabile»*. Calcolabile vuol dire
    che `p_k(x)` e `p_{k+1}(x)` esistono per ogni `x ∈ Pₖ`, e `Pₖ` e' `preserve`."""
    d = derivazione

    operandi = operandi_di_vcer(d.grafo, d.layout, d.patch)

    assert [o.patch_id for o in operandi] == list(d.patch_id)
    for passo in operandi:
        assert passo.dominio()
        for x in passo.dominio():
            assert passo.prima.posizione(x) is not None
            assert passo.dopo.posizione(x) is not None


# --- And: la relazione e' interrogabile in entrambe le direzioni --------------

def test_da_ogni_nodo_si_arriva_al_suo_layout_e_viceversa(derivazione):
    grafo = derivazione.grafo
    for nodo in grafo.nodes:
        assert grafo.nodo_di(grafo.layout_di(nodo.identifier)) == nodo.identifier


def test_dal_layout_intermedio_si_risale_al_passo_che_lo_ha_prodotto(derivazione):
    """La direzione che serve a chi legge un'evidenza: da un `lay_` citato in un
    rapporto, tornare allo stato circuitale di cui e' lo stato visuale, e da li'
    al passo — cioe' alla patch che SM-14 conterebbe."""
    d = derivazione
    intermedio = d.grafo.nodes[1]

    stato = d.grafo.nodo_di(intermedio.layout)

    entrante = [a for a in d.grafo.edges if a.target == stato]
    assert [a.patch for a in entrante] == [d.patch_id[0]]
    assert d.patch.risolvi(entrante[0].patch) is not None
