"""P0-B: la KCL scritta dal passo vive anche nel DerivationState successivo."""
from __future__ import annotations

import pytest

from kirchhoff.domain.didactic import (
    DerivationState,
    applica_passo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.analytical import _kcl_al_nodo
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PONTE


NODO = "nodo-prova"


def _fino_alle_incognite():
    ir = leggi(PONTE)
    d0 = stato_iniziale(NODO)
    _, d1 = applica_passo("choose_reference", ir, d0)
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    return ir, d2


def test_kcl_persiste_nello_stato_successivo():
    ir, prima = _fino_alle_incognite()
    assert prima.equations == ()
    snap = prima.equations
    passo, dopo = applica_passo("write_kcl", ir, prima)
    assert len(passo.equations) == 1
    assert dopo.equations == passo.equations
    assert passo.equations[0] is dopo.equations[-1]
    assert prima.equations == snap == ()


def test_kcl_si_accumula_alle_equazioni_precedenti():
    ir, d2 = _fino_alle_incognite()
    precedente = _kcl_al_nodo(ir, "b")
    con_eq = DerivationState(
        identifier=d2.identifier,
        proof_node=d2.proof_node,
        reference_node=d2.reference_node,
        variables=d2.variables,
        assumptions=d2.assumptions,
        equations=(precedente,),
    )
    passo, dopo = applica_passo("write_kcl", ir, con_eq)
    nuova = passo.equations[0]
    assert dopo.equations == (precedente, nuova)
    assert nuova.focus != precedente.focus
    assert con_eq.equations == (precedente,)


def test_kcl_duplicata_e_rifiutata():
    ir, d2 = _fino_alle_incognite()
    passo, d3 = applica_passo("write_kcl", ir, d2)
    with pytest.raises(ValueError, match="duplicate"):
        applica_passo("write_kcl", ir, d3)
    eq = passo.equations[0]
    with pytest.raises(ValueError, match="duplicate"):
        DerivationState(
            identifier="Dx",
            proof_node=NODO,
            reference_node=d2.reference_node,
            variables=d2.variables,
            equations=(eq, eq),
        )


def test_kcl_deterministica():
    ir, d2 = _fino_alle_incognite()
    p1, s1 = applica_passo("write_kcl", ir, d2)
    p2, s2 = applica_passo("write_kcl", ir, d2)
    assert p1 == p2
    assert s1 == s2
    assert s1.equations[0] == s2.equations[0]
