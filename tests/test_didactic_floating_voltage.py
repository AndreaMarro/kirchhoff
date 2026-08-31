"""P1-F: supernodo semplice da voltage_source_dc flottante e vincolo di tensione."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    DidacticPlan,
    ExactEquation,
    LinearTerm,
    SimpleSupernode,
    applica_passo,
    nodi_dei_supernodi_semplici,
    nodi_kcl_ordinarie,
    pianifica,
    scrivi_kcl_al_nodo,
    scrivi_kcl_del_supernodo,
    scrivi_vincolo_tensione,
    stato_iniziale,
    supernodi_semplici,
)
from kirchhoff.domain.didactic.analytical import (
    _kcl_del_supernodo,
    _precondizioni_kcl_supernodo,
    _sorgenti_tensione_flottanti,
    _vincolo_tensione,
)
from kirchhoff.domain.didactic.capabilities import nodale_disponibile
from kirchhoff.domain.didactic.derivation import DerivationState, EQUATION_KINDS
from kirchhoff.domain.didactic.kinds import ANALYTICAL_KINDS
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR, Request
from kirchhoff.domain.mna import solve_dc
from kirchhoff.domain.refusal import Refusal

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _req(target: str, quantity: str = "voltage", rid: str = "q1") -> Request:
    return Request(rid, quantity, target)  # type: ignore[arg-type]


def _flottante(term=("a", "b"), amount=F(5)) -> IR:
    return _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", term, amount, "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))


def _misto() -> IR:
    """unknown a,b in supernodo; unknown d ordinaria; known c; reference 0."""
    return _ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("c", "0"), F(12), "V1"),
        Component.of("V2", "voltage_source_dc", ("a", "b"), F(5), "V2"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
        Component.of("R3", "resistor", ("d", "c"), F(4), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(8), "R4"),
    ))


def _catena() -> IR:
    return _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("b", "c"), F(3), "V2"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "0"), F(10), "R2"),
    ))


def _fino_alle_incognite(ir: IR):
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO))
    _, d2 = applica_passo("define_nodal_unknowns", ir, d1)
    return d2


def _coeff(eq: ExactEquation) -> dict[str, Fraction]:
    return {t.variable.node: t.coefficient for t in eq.terms}


def test_simple_supernode_guardie():
    with pytest.raises(ValueError, match="senza source_id"):
        SimpleSupernode("", "a", "b")
    with pytest.raises(ValueError, match="senza nodi"):
        SimpleSupernode("V1", "", "b")
    with pytest.raises(ValueError, match="senza nodi"):
        SimpleSupernode("V1", "a", "")
    with pytest.raises(ValueError, match="coincidenti"):
        SimpleSupernode("V1", "a", "a")
    with pytest.raises(ValueError, match="riferimento"):
        SimpleSupernode("V1", "a", REFERENCE_NODE)


def test_discovery_supernodo_semplice_e_ordine_terminali():
    diretto = _flottante(("a", "b"), F(5))
    inverso = _flottante(("b", "a"), F(5))
    sn = supernodi_semplici(diretto)
    assert sn == (SimpleSupernode("V1", "a", "b"),)
    assert supernodi_semplici(inverso) == (SimpleSupernode("V1", "b", "a"),)
    assert nodi_dei_supernodi_semplici(diretto) == ("a", "b")
    assert nodi_kcl_ordinarie(diretto) == ()
    assert tuple(c.id for c in _sorgenti_tensione_flottanti(diretto)) == ("V1",)


def test_grounded_non_e_flottante():
    ir = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
    ))
    assert _sorgenti_tensione_flottanti(ir) == ()
    assert supernodi_semplici(ir) == ()
    assert nodi_dei_supernodi_semplici(ir) == ()


def test_vincolo_tensione_convenzione_terminali():
    diretto = _flottante(("a", "b"), F(5))
    inverso = _flottante(("b", "a"), F(5))
    eq_d = _vincolo_tensione(diretto, supernodi_semplici(diretto)[0])
    eq_i = _vincolo_tensione(inverso, supernodi_semplici(inverso)[0])
    assert eq_d.kind == "voltage_constraint"
    assert eq_d.focus == "V1"
    assert eq_d.rhs == F(5)
    assert _coeff(eq_d) == {"a": F(1), "b": F(-1)}
    assert _coeff(eq_i) == {"b": F(1), "a": F(-1)}
    assert eq_i.rhs == F(5)


def test_kcl_supernodo_frontiera_e_ramo_interno_ignorato():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("Rint", "resistor", ("a", "b"), F(7), "Rint"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(20), "R2"),
    ))
    eq = _kcl_del_supernodo(ir, supernodi_semplici(ir)[0])
    assert eq.kind == "kcl"
    assert eq.focus == "V1"
    assert eq.rhs == F(0)
    assert _coeff(eq) == {"a": F(1, 10), "b": F(1, 20), "0": -F(1, 10) - F(1, 20)}
    assert "Rint" not in str(_coeff(eq))


def test_kcl_supernodo_con_generatore_di_corrente():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
        Component.of("Iint", "current_source_dc", ("a", "b"), F(1), "Iint"),
    ))
    eq = _kcl_del_supernodo(ir, supernodi_semplici(ir)[0])
    assert eq.rhs == -F(2)
    assert _coeff(eq)["a"] == F(1, 10)
    assert _coeff(eq)["b"] == F(1, 10)


def test_esecuzione_kcl_e_vincolo_nello_stato():
    ir = _flottante()
    stato = _fino_alle_incognite(ir)
    assert stato.variabile_del_nodo("a").role == "unknown"
    assert stato.variabile_del_nodo("b").known_value is None
    p_kcl, d3 = scrivi_kcl_del_supernodo(ir, stato, "V1")
    assert p_kcl.kind == "write_kcl"
    assert p_kcl.focused_entities == ("V1", "a", "b")
    assert p_kcl.equations[0].kind == "kcl"
    p_v, d4 = scrivi_vincolo_tensione(ir, d3, "V1")
    assert p_v.kind == "write_voltage_constraint"
    assert p_v.focused_entities == ("V1",)
    assert [eq.kind for eq in d4.equations] == ["kcl", "voltage_constraint"]
    with pytest.raises(ValueError, match="duplicate"):
        scrivi_kcl_del_supernodo(ir, d4, "V1")
    with pytest.raises(ValueError, match="duplicate"):
        scrivi_vincolo_tensione(ir, d4, "V1")


def test_applica_passo_vincolo_e_write_kcl_resta_ordinaria():
    ir = _flottante()
    d2 = _fino_alle_incognite(ir)
    with pytest.raises(ValueError, match="senza supernodo"):
        applica_passo("write_kcl", ir, d2)
    p, d3 = applica_passo("write_voltage_constraint", ir, d2)
    assert p.kind == "write_voltage_constraint"
    assert d3.equations[0].kind == "voltage_constraint"
    massa = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(4), "R1"),
    ))
    _, m1 = applica_passo("choose_reference", massa, stato_iniziale(NODO))
    with pytest.raises(ValueError, match="nessun vincolo"):
        applica_passo("write_voltage_constraint", massa, m1)


def test_planner_azioni_supernodo():
    ir = _flottante()
    azioni = _azioni_nodali(ir)
    assert [(a.kind, a.operands) for a in azioni] == [
        ("choose_reference", ()),
        ("define_nodal_unknowns", ()),
        ("write_kcl", ("V1", "a", "b")),
        ("write_voltage_constraint", ("V1",)),
    ]
    piano = pianifica(ir, _req("R1"))
    assert isinstance(piano, DidacticPlan)
    assert piano.technique == "nodal_analysis"
    assert piano.actions == azioni
    assert nodale_disponibile(ir, "voltage")
    assert nodale_disponibile(ir, "current")


def test_partizione_mista_ordinaria_e_supernodo():
    ir = _misto()
    assert nodi_kcl_ordinarie(ir) == ("d",)
    assert nodi_dei_supernodi_semplici(ir) == ("a", "b")
    assert supernodi_semplici(ir) == (SimpleSupernode("V2", "a", "b"),)
    assert nodale_disponibile(ir, "voltage")
    azioni = _azioni_nodali(ir)
    assert [(a.kind, a.operands) for a in azioni] == [
        ("choose_reference", ()),
        ("define_nodal_unknowns", ()),
        ("write_kcl", ("d",)),
        ("write_kcl", ("V2", "a", "b")),
        ("write_voltage_constraint", ("V2",)),
    ]
    stato = _fino_alle_incognite(ir)
    assert stato.variabile_del_nodo("c").role == "known_from_source"
    assert stato.variabile_del_nodo("c").known_value == F(12)
    _, stato = scrivi_kcl_al_nodo(ir, stato, "d")
    _, stato = scrivi_kcl_del_supernodo(ir, stato, "V2")
    _, stato = scrivi_vincolo_tensione(ir, stato, "V2")
    assert [eq.kind for eq in stato.equations] == ["kcl", "kcl", "voltage_constraint"]
    assert [eq.focus for eq in stato.equations] == ["d", "V2", "V2"]


def test_catena_e_overlap_fail_closed():
    catena = _catena()
    assert tuple(c.id for c in _sorgenti_tensione_flottanti(catena)) == ("V1", "V2")
    assert supernodi_semplici(catena) == ()
    assert not nodale_disponibile(catena, "voltage")
    assert isinstance(pianifica(catena, _req("R1")), Refusal)
    with pytest.raises(ValueError, match="non definisce un supernodo"):
        scrivi_kcl_del_supernodo(catena, _fino_alle_incognite(catena), "V1")
    overlap = _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("a", "c"), F(3), "V2"),
        Component.of("R1", "resistor", ("b", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "0"), F(10), "R2"),
    ))
    assert supernodi_semplici(overlap) == ()
    assert not nodale_disponibile(overlap, "voltage")


def test_flottante_verso_nodo_noto_resta_fuori():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("a", "b"), F(3), "V2"),
        Component.of("R1", "resistor", ("b", "0"), F(10), "R1"),
    ))
    assert tuple(c.id for c in _sorgenti_tensione_flottanti(ir)) == ("V2",)
    assert supernodi_semplici(ir) == ()
    assert not nodale_disponibile(ir, "voltage")
    sn = SimpleSupernode("V2", "a", "b")
    with pytest.raises(ValueError, match="noti da generatore"):
        _precondizioni_kcl_supernodo(ir, sn)


def test_precondizioni_assenti_e_tipo_e_terminali():
    ir = _flottante()
    with pytest.raises(ValueError, match="assente"):
        _precondizioni_kcl_supernodo(ir, SimpleSupernode("Vx", "a", "b"))
    with pytest.raises(ValueError, match="terminali"):
        _precondizioni_kcl_supernodo(ir, SimpleSupernode("V1", "b", "a"))
    ir_tipo = _ir(("0", "a", "b"), (
        Component.of("R1", "resistor", ("a", "b"), F(5), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(10), "R2"),
        Component.of("R3", "resistor", ("b", "0"), F(10), "R3"),
    ))
    with pytest.raises(ValueError, match="non è voltage_source_dc"):
        _precondizioni_kcl_supernodo(ir_tipo, SimpleSupernode("R1", "a", "b"))


def test_kcl_supernodo_senza_resistore_o_componente_illecito():
    solo_i = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(1), "I1"),
        Component.of("I2", "current_source_dc", ("b", "0"), F(1), "I2"),
    ))
    assert supernodi_semplici(solo_i) == (SimpleSupernode("V1", "a", "b"),)
    assert not nodale_disponibile(solo_i, "voltage")
    with pytest.raises(ValueError, match="senza contributo resistivo"):
        _precondizioni_kcl_supernodo(solo_i, SimpleSupernode("V1", "a", "b"))
    con_c = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("C1", "capacitor", ("b", "0"), F(1, 1000), "C1"),
    ))
    assert supernodi_semplici(con_c) == (SimpleSupernode("V1", "a", "b"),)
    assert not nodale_disponibile(con_c, "voltage")
    with pytest.raises(ValueError, match="non rappresentabili"):
        _precondizioni_kcl_supernodo(con_c, SimpleSupernode("V1", "a", "b"))


def test_scrittura_senza_incognite_o_ruolo_errato():
    ir = _flottante()
    d0 = stato_iniziale(NODO)
    with pytest.raises(ValueError, match="senza incognite"):
        scrivi_vincolo_tensione(ir, d0, "V1")
    _, d1 = applica_passo("choose_reference", ir, d0)
    amputato = DerivationState(
        "D1", NODO, reference_node=REFERENCE_NODE,
        variables=d1.variables,
    )
    with pytest.raises(ValueError, match="senza incognite"):
        scrivi_kcl_del_supernodo(ir, amputato, "V1")
    d2 = _fino_alle_incognite(ir)
    senza_a = DerivationState(
        d2.identifier, d2.proof_node, d2.reference_node,
        tuple(v for v in d2.variables if v.node != "a"),
    )
    with pytest.raises(ValueError, match="non ha una variabile"):
        scrivi_kcl_del_supernodo(ir, senza_a, "V1")
    noto = DerivationState(
        d2.identifier, d2.proof_node, d2.reference_node,
        tuple(
            v if v.node != "a" else type(v)(
                v.name, v.node, "known_from_source", "V9", F(1),
            )
            for v in d2.variables
        ),
    )
    with pytest.raises(ValueError, match="ruolo known_from_source"):
        scrivi_vincolo_tensione(ir, noto, "V1")


def test_vocabolario_e_assenza_di_supernode_kcl():
    assert ANALYTICAL_KINDS == frozenset({
        "choose_reference",
        "define_nodal_unknowns",
        "write_kcl",
        "write_voltage_constraint",
    })
    assert "supernode_kcl" not in ANALYTICAL_KINDS
    assert EQUATION_KINDS == frozenset({"kcl", "voltage_constraint"})
    assert "supernode_kcl" not in EQUATION_KINDS
    campi = DerivationState.__dataclass_fields__
    assert "supernode" not in campi
    assert "topology" not in campi


def test_vcvs_resta_fuori():
    vcvs = _ir(("0", "A", "C"), (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(4), "V1"),
        Component.of("R1", "resistor", ("A", "0"), F(2), "R1"),
        Component.of(
            "E1", "voltage_controlled_voltage_source", ("C", "0"),
            F(2), "E1", control_nodes=("A", "0"),
        ),
        Component.of("R3", "resistor", ("C", "0"), F(5), "R3"),
    ))
    assert not nodale_disponibile(vcvs, "voltage")
    assert supernodi_semplici(vcvs) == ()


def test_due_supernodi_disgiunti():
    ir = _ir(("0", "a", "b", "c", "d"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("c", "d"), F(3), "V2"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
        Component.of("R3", "resistor", ("c", "0"), F(4), "R3"),
        Component.of("R4", "resistor", ("d", "0"), F(8), "R4"),
    ))
    assert supernodi_semplici(ir) == (
        SimpleSupernode("V1", "a", "b"),
        SimpleSupernode("V2", "c", "d"),
    )
    assert nodale_disponibile(ir, "voltage")
    kinds = [a.kind for a in _azioni_nodali(ir)]
    assert kinds.count("write_kcl") == 2
    assert kinds.count("write_voltage_constraint") == 2
    stato = _fino_alle_incognite(ir)
    _, stato = scrivi_kcl_del_supernodo(ir, stato, "V2")
    _, stato = scrivi_vincolo_tensione(ir, stato, "V2")
    assert stato.equations[0].focus == "V2"


def test_cross_check_kernel_solo_nel_test():
    ir = _flottante(("a", "b"), F(5))
    stato = _fino_alle_incognite(ir)
    _, stato = scrivi_kcl_del_supernodo(ir, stato, "V1")
    _, stato = scrivi_vincolo_tensione(ir, stato, "V1")
    kcl, vincolo = stato.equations
    assert vincolo.rhs == F(5)
    assert _coeff(vincolo)["a"] == F(1)
    assert _coeff(vincolo)["b"] == F(-1)
    assert solve_dc(ir)["V1"]["voltage"] == F(5)
    va = solve_dc(ir)["R1"]["voltage"]
    vb = solve_dc(ir)["R2"]["voltage"]
    assert va - vb == F(5)
    acc = kcl.rhs
    for termine in kcl.terms:
        if termine.variable.node == "a":
            acc -= termine.coefficient * va
        elif termine.variable.node == "b":
            acc -= termine.coefficient * vb
        else:
            acc -= termine.coefficient * F(0)
    assert acc == 0


def test_current_source_esterno_orientato_sul_secondo_nodo():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
        Component.of("I1", "current_source_dc", ("0", "b"), F(3), "I1"),
    ))
    eq = _kcl_del_supernodo(ir, supernodi_semplici(ir)[0])
    assert eq.rhs == F(3)
