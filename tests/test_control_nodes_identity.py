"""control_nodes entra nell'identità sostanziale delle sorgenti controllate.

Un identificatore uguale non basta: E1 (A,B) controllata da (C,D) non è
E1 (A,B) controllata da (E,F). Prima della patch, IDENTITY_ATTRIBUTES
ometteva control_nodes e preserve_set() considerava identiche le due.
"""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.ir.schema import Component as SchemaComponent
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import (
    IDENTITY_ATTRIBUTES,
    Boundary,
    EntityRef,
    LayoutPatch,
    attributes_of,
    check_transform,
    preserve_set,
    transform,
)

F = Fraction
C = lambda i: EntityRef("component", i)  # noqa: E731
N = lambda i: EntityRef("node", i)  # noqa: E731


def _dc(comps, nodes=None) -> IR:
    if nodes is None:
        nodes = tuple(sorted({
            t for c in comps
            for t in (*c.terminals, *(c.control_nodes or ()))
        }))
    return IR("1.0.0", "dc", "generated", nodes, comps, ())


def _vcvs(cid, terminals, mu, control):
    return Component.of(
        cid, "voltage_controlled_voltage_source", terminals, mu, cid,
        control_nodes=control,
    )


def _vccs(cid, terminals, g, control):
    return Component.of(
        cid, "voltage_controlled_current_source", terminals, g, cid,
        control_nodes=control,
    )


def _rete_con(controllata: Component) -> IR:
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "B"), F(4), "R_1"),
        Component.of("R2", "resistor", ("B", "0"), F(6), "R_2"),
        controllata,
        Component.of("Rl", "resistor", ("C", "0"), F(5), "R_l"),
    ))


def test_preserve_set_non_confonde_control_nodes_diversi_sulla_stessa_vcvs():
    """Il bug: stesso id/type/terminals/value/symbolic/phase_steps, altro controllo."""
    prima = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    dopo = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "B")))
    assert prima.component("E1").id == dopo.component("E1").id
    assert prima.component("E1").type == dopo.component("E1").type
    assert prima.component("E1").terminals == dopo.component("E1").terminals
    assert prima.component("E1").value == dopo.component("E1").value
    assert prima.component("E1").symbolic == dopo.component("E1").symbolic
    assert prima.component("E1").phase_steps == dopo.component("E1").phase_steps
    assert prima.component("E1").control_nodes != dopo.component("E1").control_nodes
    assert C("E1") not in preserve_set(prima, dopo)


def test_vcvs_identica_e_preservata():
    ir = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    assert C("E1") in preserve_set(ir, ir)


def test_vccs_identica_e_preservata():
    ir = _rete_con(_vccs("G1", ("C", "0"), F(1, 10), ("A", "0")))
    assert C("G1") in preserve_set(ir, ir)


def test_vccs_con_control_nodes_diversi_non_e_preservata():
    prima = _rete_con(_vccs("G1", ("C", "0"), F(1, 10), ("A", "0")))
    dopo = _rete_con(_vccs("G1", ("C", "0"), F(1, 10), ("A", "B")))
    assert C("G1") not in preserve_set(prima, dopo)


def test_resistore_invariato_resta_preservato():
    prima = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    dopo = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "B")))
    assert C("R1") in preserve_set(prima, dopo)
    assert C("V1") in preserve_set(prima, dopo)


def test_serie_con_vcvs_non_coinvolta_la_preserva():
    ir = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    esito = transform(ir, "serie", "R1", "R2")
    assert not isinstance(esito, Refusal)
    _dopo, prodotto = esito
    assert C("E1") in prodotto.preserve
    assert _dopo.component("E1").control_nodes == ("A", "0")


def test_serie_con_vccs_non_coinvolta_la_preserva():
    ir = _rete_con(_vccs("G1", ("C", "0"), F(1, 10), ("A", "B")))
    esito = transform(ir, "serie", "R1", "R2")
    assert not isinstance(esito, Refusal)
    _dopo, prodotto = esito
    assert C("G1") in prodotto.preserve
    assert _dopo.component("G1").control_nodes == ("A", "B")


def test_trasformazione_corrotta_sul_controllo_e_identity_violation():
    prima = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    dopo = _rete_con(_vcvs("E1", ("C", "0"), F(2), ("A", "B")))
    patch = LayoutPatch(
        preserve=(C("V1"), C("R1"), C("R2"), C("E1"), C("Rl"),
                  N("0"), N("A"), N("B"), N("C")),
        remove=(),
        create=(),
        reroute_scope=(N("A"),),
    )
    boundary = Boundary((N("A"), N("0")))
    esito = check_transform(prima, dopo, "serie", patch, boundary)
    assert isinstance(esito, Refusal)
    assert esito.cause == "identity_violation"
    assert esito.subject == "E1"
    assert "control_nodes" in esito.diagnosis


def test_control_nodes_compone_l_identita_e_provenance_no():
    assert "control_nodes" in IDENTITY_ATTRIBUTES
    assert "provenance" not in IDENTITY_ATTRIBUTES
    assert "id" not in IDENTITY_ATTRIBUTES
    nomi = {f.name for f in fields(SchemaComponent)}
    sostanziali = {"type", "terminals", "value", "symbolic", "phase_steps",
                   "control_nodes"}
    assert sostanziali <= nomi
    assert set(IDENTITY_ATTRIBUTES) == sostanziali
    assert "control_nodes" in attributes_of(
        _vcvs("E1", ("C", "0"), F(2), ("A", "0")))
    assert attributes_of(_vcvs("E1", ("C", "0"), F(2), ("A", "0")))["control_nodes"] == ("A", "0")
