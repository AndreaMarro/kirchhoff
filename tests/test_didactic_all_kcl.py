"""P1-C: coverage completa delle KCL ordinarie sulle unknown dello slice."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DidacticPlan,
    applica_passo,
    nodi_kcl_ordinarie,
    pianifica,
    scrivi_kcl_al_nodo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.capabilities import (
    _nodi_incogniti,
    nodale_disponibile,
)
from kirchhoff.domain.didactic.kinds import ANALYTICAL_KINDS
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR, Request
from kirchhoff.domain.ir.canonical import canonicalize
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve

from test_percorso_b import CORRENTE, PARTITORE, PONTE

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str, quantity: str = "current", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _due_unknown():
    """unknown a,b; known c; reference 0. Irriducibile nello slice certificato."""
    return _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "c"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("b", "0"), F(5), "R3"),
        Component.of("R4", "resistor", ("a", "0"), F(4), "R4"),
        Component.of("R5", "resistor", ("b", "c"), F(7), "R5"),
    ))


def _tre_unknown():
    """unknown a,b,d; known c; reference 0."""
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
    _, d1 = applica_passo("choose_reference", ir, d0)
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    return d2


def _kcl_pianificate(azioni) -> tuple[str, ...]:
    return tuple(a.operands[0] for a in azioni if a.kind == "write_kcl")


def _unknown_dello_stato(stato) -> tuple[str, ...]:
    return tuple(v.node for v in stato.variables if v.role == "unknown")


@pytest.mark.parametrize("fabbrica, attesi", (
    (_due_unknown, ("a", "b")),
    (_tre_unknown, ("a", "b", "d")),
    (lambda: leggi(PONTE), ("a", "b")),
))
def test_nodale_disponibile_implica_unknown_uguale_kcl_ordinarie(fabbrica, attesi):
    ir = fabbrica()
    assert nodale_disponibile(ir, "current")
    assert nodale_disponibile(ir, "voltage")
    d2 = _fino_alle_incognite(ir)
    unknown = _unknown_dello_stato(d2)
    ordinarie = nodi_kcl_ordinarie(ir)
    pianificati = _kcl_pianificate(_azioni_nodali(ir))
    assert unknown == ordinarie == pianificati == attesi
    assert unknown == tuple(sorted(unknown))
    assert len(pianificati) == len(set(pianificati))


def test_due_unknown_piano_due_write_kcl():
    ir = _due_unknown()
    piano = pianifica(ir, _req("R4"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "nodal_analysis"
    assert [a.kind for a in piano.actions] == [
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_kcl",
    ]
    assert _kcl_pianificate(piano.actions) == ("a", "b")


def test_tre_unknown_piano_tre_write_kcl_non_solo_la_prima():
    ir = _tre_unknown()
    piano = pianifica(ir, _req("R4"))
    assert piano.technique == "nodal_analysis"
    kcl = _kcl_pianificate(piano.actions)
    assert kcl == ("a", "b", "d")
    assert kcl != (nodi_kcl_ordinarie(ir)[0],)
    assert [a.kind for a in piano.actions].count("write_kcl") == 3


def test_nodo_noto_e_riferimento_senza_kcl():
    ir = _due_unknown()
    d2 = _fino_alle_incognite(ir)
    ruoli = {v.node: v.role for v in d2.variables}
    assert ruoli["c"] == "known_from_source"
    assert ruoli[REFERENCE_NODE] == "reference"
    kcl = _kcl_pianificate(pianifica(ir, _req("R3")).actions)
    assert "c" not in kcl
    assert REFERENCE_NODE not in kcl
    assert kcl == ("a", "b")


def test_ordine_indipendente_dall_ordine_dei_componenti():
    base = _tre_unknown()
    invertito = _ir(base.nodes[::-1], tuple(reversed(base.components)))
    assert tuple(c.id for c in invertito.components) != tuple(c.id for c in base.components)
    assert nodi_kcl_ordinarie(base) == nodi_kcl_ordinarie(invertito) == ("a", "b", "d")
    assert _kcl_pianificate(_azioni_nodali(base)) == _kcl_pianificate(_azioni_nodali(invertito))
    assert canonicalize(base).nodes == canonicalize(invertito).nodes


def test_esecuzione_sequenziale_manuale_e_catena():
    ir = _tre_unknown()
    piano = pianifica(ir, _req("R5"))
    d0 = stato_iniziale(NODO)
    _, d1 = applica_passo("choose_reference", ir, d0)
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    assert d2.equations == ()
    snap_d2 = d2.equations

    stati = [d2]
    passi = []
    stato = d2
    for azione in piano.actions:
        if azione.kind != "write_kcl":
            continue
        passo, stato = scrivi_kcl_al_nodo(ir, stato, azione.operands[0])
        passi.append(passo)
        stati.append(stato)

    unknown = _unknown_dello_stato(d2)
    assert tuple(eq.focus for eq in stato.equations) == unknown == ("a", "b", "d")
    assert len(stato.equations) == 3
    assert [p.focused_entities for p in passi] == [("a",), ("b",), ("d",)]
    assert [p.equations[0].focus for p in passi] == list(unknown)
    assert [p.derivation_before for p in passi] == ["D2", "D3", "D4"]
    assert [p.derivation_after for p in passi] == ["D3", "D4", "D5"]
    for i in range(len(passi) - 1):
        assert passi[i].derivation_after == passi[i + 1].derivation_before
    assert d2.equations == snap_d2 == ()
    assert stati[1].equations == (passi[0].equations[0],)
    assert stati[2].equations == (passi[0].equations[0], passi[1].equations[0])
    assert stati[3].equations == tuple(p.equations[0] for p in passi)
    assert stati[1].identifier == "D3"
    assert len(stati[1].equations) == 1


def test_nodo_isolato_non_e_sistema_nodale_completo():
    ir = _ir(("0", "a", "c", "z"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("R1", "resistor", ("a", "c"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(4), "R2"),
    ))
    assert _nodi_incogniti(ir) == ("a", "z")
    assert nodi_kcl_ordinarie(ir) == ("a",)
    assert not nodale_disponibile(ir, "voltage")
    assert _kcl_pianificate(_azioni_nodali(ir)) == ("a",)


def test_generatore_di_corrente_resta_fuori():
    ir = leggi(CORRENTE)
    kernel = resolve(IR(
        "1.0.0", "dc", "netlist", ir.nodes, ir.components,
        (_req("R1", "voltage"),),
    ))
    assert isinstance(kernel, Solved)
    assert not nodale_disponibile(ir, "voltage")
    assert not nodale_disponibile(ir, "current")
    assert isinstance(pianifica(ir, _req("R1", "voltage")), Refusal)


def test_sorgente_di_tensione_flottante_resta_fuori():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert isinstance(resolve(IR(
        "1.0.0", "dc", "netlist", ir.nodes, ir.components,
        (_req("R1", "voltage"),),
    )), Solved)
    assert not nodale_disponibile(ir, "voltage")
    assert nodi_kcl_ordinarie(ir) == ()
    assert isinstance(pianifica(ir, _req("R1", "voltage")), Refusal)


def test_vcvs_e_vccs_restano_fuori():
    vcvs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "E1", "voltage_controlled_voltage_source", ("C", "0"),
            F(2), "E1", control_nodes=("A", "0"),
        ),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    vccs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "G1", "voltage_controlled_current_source", ("C", "0"),
            F(1), "G1", control_nodes=("A", "0"),
        ),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    assert not nodale_disponibile(vcvs, "voltage")
    assert not nodale_disponibile(vccs, "voltage")
    assert isinstance(pianifica(vcvs, _req("R3", "voltage")), Refusal)
    assert isinstance(pianifica(vccs, _req("R3", "voltage")), Refusal)


def test_percorso_trasformazione_certificata_invariato():
    piano = pianifica(leggi(PARTITORE), _req("R2", "current"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "certified_transform_path"
    assert piano.actions[0].kind == "serie"
    assert all(a.kind != "write_kcl" for a in piano.actions)


def test_vocabolario_analitico_invariato():
    assert ANALYTICAL_KINDS == frozenset({
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
    })
    assert "write_all_kcl" not in ANALYTICAL_KINDS
