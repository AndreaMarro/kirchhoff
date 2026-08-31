"""P1-C: una KCL ordinaria distinta per ogni nodo incognito necessario."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.didactic import (
    applica_passo,
    nodi_kcl_ordinarie,
    pianifica,
    scrivi_kcl_al_nodo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.capabilities import nodale_disponibile
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR, Request
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PONTE

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str, quantity: str = "current", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _due_nodi_ordinari():
    """V1 fissa c; a e b restano incogniti e ammettono KCL ordinaria.

    La maglia extra b-c impedisce una riduzione serie su b.
    """
    return _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "c"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("b", "0"), F(5), "R3"),
        Component.of("R4", "resistor", ("a", "0"), F(4), "R4"),
        Component.of("R5", "resistor", ("b", "c"), F(7), "R5"),
    ))


def _tre_nodi_ordinari():
    """V1 fissa c; a, b, d incogniti con soli resistori incidenti.

    I rami extra verso c rendono la rete irriducibile nello slice
    certificato, così `pianifica` deve scegliere l'analisi nodale.
    """
    return _ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "c"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("b", "d"), F(5), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(4), "R4"),
        Component.of("R5", "resistor", ("a", "0"), F(8), "R5"),
        Component.of("R6", "resistor", ("b", "0"), F(6), "R6"),
        Component.of("R7", "resistor", ("d", "c"), F(3), "R7"),
    ))


def _fino_alle_incognite(ir: IR):
    d0 = stato_iniziale(NODO)
    _, d1 = applica_passo("choose_reference", ir, d0, operands=())
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    return d2


def _kcl_del_piano(piano) -> tuple[str, ...]:
    return tuple(
        a.operands[0] for a in piano.actions if a.kind == "write_kcl"
    )


def test_piano_una_write_kcl_per_nodo_ordinario():
    ir = _tre_nodi_ordinari()
    assert nodale_disponibile(ir, "voltage")
    piano = pianifica(ir, _req("R4"))
    assert piano.technique == "nodal_analysis"
    kcl = [a for a in piano.actions if a.kind == "write_kcl"]
    assert [a.kind for a in piano.actions] == [
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_kcl",
        "write_kcl",
    ]
    assert all(a.operands == (nodo,) for a, nodo in zip(kcl, ("a", "b", "d")))
    assert "write_all_kcl" not in [a.kind for a in piano.actions]
    assert all(len(a.operands) == 1 for a in kcl)


def test_invariante_unknown_uguale_piano_uguale_ordinarie():
    for ir in (_due_nodi_ordinari(), _tre_nodi_ordinari(), leggi(PONTE)):
        assert nodale_disponibile(ir, "current")
        d2 = _fino_alle_incognite(ir)
        u = tuple(v.node for v in d2.variables if v.role == "unknown")
        o = nodi_kcl_ordinarie(ir)
        k = tuple(
            a.operands[0]
            for a in _azioni_nodali(ir)
            if a.kind == "write_kcl"
        )
        assert u == k == o
        assert u == tuple(sorted(u))


def test_riferimento_e_noti_non_ricevono_write_kcl():
    ir = _due_nodi_ordinari()
    d2 = _fino_alle_incognite(ir)
    ruoli = {v.node: v.role for v in d2.variables}
    assert ruoli[REFERENCE_NODE] == "reference"
    assert ruoli["c"] == "known_from_source"
    assert ruoli["a"] == "unknown"
    assert ruoli["b"] == "unknown"
    piano = pianifica(ir, _req("R3"))
    nodi_kcl = _kcl_del_piano(piano)
    assert nodi_kcl == ("a", "b")
    assert REFERENCE_NODE not in nodi_kcl
    assert "c" not in nodi_kcl


def test_ponte_due_kcl_distinte_in_ordine_canonico():
    ir = leggi(PONTE)
    piano = pianifica(ir, _req("R4"))
    assert _kcl_del_piano(piano) == nodi_kcl_ordinarie(ir) == ("a", "b")
    write = [a for a in piano.actions if a.kind == "write_kcl"]
    assert write[0].operands == ("a",)
    assert write[1].operands == ("b",)


def test_replay_manuale_del_piano_accumula_le_kcl():
    ir = _tre_nodi_ordinari()
    piano = pianifica(ir, _req("R4"))
    d0 = stato_iniziale(NODO)
    passo_ref, d1 = applica_passo("choose_reference", ir, d0, operands=())
    passo_inc, d2 = applica_passo("define_nodal_unknowns", ir, d1, operands=())
    assert passo_ref.derivation_before == "D0"
    assert passo_ref.derivation_after == d1.identifier == "D1"
    assert passo_inc.derivation_before == "D1"
    assert passo_inc.derivation_after == d2.identifier == "D2"

    stato = d2
    passi = []
    for azione in piano.actions:
        if azione.kind != "write_kcl":
            continue
        nodo = azione.operands[0]
        passo, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
        passi.append(passo)

    unknown = tuple(v.node for v in d2.variables if v.role == "unknown")
    focus = tuple(eq.focus for eq in stato.equations)
    assert focus == unknown == ("a", "b", "d")
    assert len(stato.equations) == len(unknown) == 3
    assert len(set(focus)) == len(focus)
    assert [p.focused_entities for p in passi] == [("a",), ("b",), ("d",)]
    assert [p.derivation_before for p in passi] == ["D2", "D3", "D4"]
    assert [p.derivation_after for p in passi] == ["D3", "D4", "D5"]
    assert stato.identifier == "D5"
    assert stato.equations == tuple(p.equations[0] for p in passi)
    for i, passo in enumerate(passi):
        assert passo.kind == "write_kcl"
        assert passo.equations[0].kind == "kcl"
        assert passo.equations[0].focus == unknown[i]
        assert passo.equations[0] is stato.equations[i]


def test_replay_non_usa_il_wrapper_legacy_per_le_kcl_multiple():
    ir = _due_nodi_ordinari()
    piano = pianifica(ir, _req("R2"))
    stato = _fino_alle_incognite(ir)
    for azione in piano.actions:
        if azione.kind == "write_kcl":
            _, stato = scrivi_kcl_al_nodo(ir, stato, azione.operands[0])
    assert tuple(eq.focus for eq in stato.equations) == ("a", "b")


def test_ordine_delle_equazioni_coincide_col_piano():
    ir = _tre_nodi_ordinari()
    piano = pianifica(ir, _req("R5"))
    stato = _fino_alle_incognite(ir)
    pianificati = _kcl_del_piano(piano)
    for nodo in pianificati:
        _, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
    assert tuple(eq.focus for eq in stato.equations) == pianificati


def test_piano_nodale_deterministico():
    ir = _tre_nodi_ordinari()
    p1 = pianifica(ir, _req("R4"))
    p2 = pianifica(ir, _req("R4"))
    assert p1.canonical_json() == p2.canonical_json()
    assert _kcl_del_piano(p1) == _kcl_del_piano(p2) == ("a", "b", "d")


def test_ogni_unknown_ordinario_ha_esattamente_la_propria_kcl():
    ir = _tre_nodi_ordinari()
    stato = _fino_alle_incognite(ir)
    unknown = [v.node for v in stato.variables if v.role == "unknown"]
    noti = [v.node for v in stato.variables if v.role != "unknown"]
    for nodo in _kcl_del_piano(pianifica(ir, _req("R1"))):
        _, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
    focus = [eq.focus for eq in stato.equations]
    assert sorted(focus) == sorted(unknown)
    assert all(eq.kind == "kcl" for eq in stato.equations)
    assert not set(focus) & set(noti)
    assert set(focus) == set(nodi_kcl_ordinarie(ir))
