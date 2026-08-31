"""P1-E: tensioni nodali note da generatori DC verso il riferimento."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.didactic import (
    ExactEquation,
    NodalVariable,
    applica_passo,
    nodi_kcl_ordinarie,
    scrivi_kcl_al_nodo,
    stato_iniziale,
)
from kirchhoff.domain.didactic.analytical import (
    _generatori_verso_riferimento,
    _valore_noto_verso_riferimento,
)
from kirchhoff.domain.didactic.capabilities import nodale_disponibile
from kirchhoff.domain.didactic.kinds import ANALYTICAL_KINDS
from kirchhoff.domain.didactic.planner import _azioni_nodali
from kirchhoff.domain.ir import REFERENCE_NODE, Component, IR
from kirchhoff.domain.mna import solve_dc

F = Fraction
NODO = "nodo-prova"


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def _divisore(v_term: tuple[str, str], amount: Fraction) -> IR:
    return _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", v_term, amount, "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(20), "R2"),
    ))


def _fino_al_riferimento(ir: IR):
    _, d1 = applica_passo("choose_reference", ir, stato_iniziale(NODO))
    return d1


def _fino_alle_incognite(ir: IR):
    _, d2 = applica_passo("define_nodal_unknowns", ir, _fino_al_riferimento(ir))
    return d2


def _coeff(eq: ExactEquation) -> dict[str, Fraction]:
    return {t.variable.node: t.coefficient for t in eq.terms}


def test_riferimento_vale_zero_dopo_choose_reference():
    d1 = _fino_al_riferimento(_divisore(("b", "0"), F(5)))
    v0 = d1.variabile_del_nodo(REFERENCE_NODE)
    assert v0.role == "reference"
    assert v0.source_id is None
    assert v0.known_value == F(0)
    assert v0.known_value is not None


def test_sorgente_nodo_verso_massa_valore_positivo():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    vb = d2.variabile_del_nodo("b")
    assert vb.role == "known_from_source"
    assert vb.source_id == "V1"
    assert vb.known_value == F(5)


def test_sorgente_massa_verso_nodo_valore_negativo():
    d2 = _fino_alle_incognite(_divisore(("0", "b"), F(5)))
    assert d2.variabile_del_nodo("b").known_value == -F(5)


def test_inversione_terminali_produce_valori_opposti():
    diretto = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    inverso = _fino_alle_incognite(_divisore(("0", "b"), F(5)))
    assert diretto.variabile_del_nodo("b").known_value == F(5)
    assert inverso.variabile_del_nodo("b").known_value == -F(5)
    assert (
        diretto.variabile_del_nodo("b").known_value
        == -inverso.variabile_del_nodo("b").known_value
    )


def test_amount_negativo_non_normalizzato():
    verso_massa = _fino_alle_incognite(_divisore(("b", "0"), -F(5)))
    verso_nodo = _fino_alle_incognite(_divisore(("0", "b"), -F(5)))
    assert verso_massa.variabile_del_nodo("b").known_value == -F(5)
    assert verso_nodo.variabile_del_nodo("b").known_value == F(5)


def test_sorgente_zero_volt_non_e_none():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(0)))
    vb = d2.variabile_del_nodo("b")
    assert vb.role == "known_from_source"
    assert vb.known_value == F(0)
    assert vb.known_value is not None
    assert bool(vb.known_value) is False


def test_tensione_frazionaria_resta_esatta():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(7, 3)))
    assert d2.variabile_del_nodo("b").known_value == F(7, 3)
    inverso = _fino_alle_incognite(_divisore(("0", "b"), F(7, 3)))
    assert inverso.variabile_del_nodo("b").known_value == -F(7, 3)


def test_unknown_senza_valore_ne_sorgente():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    va = d2.variabile_del_nodo("a")
    assert va.role == "unknown"
    assert va.source_id is None
    assert va.known_value is None


def test_known_porta_sempre_sorgente_e_valore():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    for v in d2.variables:
        if v.role != "known_from_source":
            continue
        assert v.source_id is not None
        assert v.known_value is not None


def test_riferimento_senza_sorgente():
    d2 = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    v0 = d2.variabile_del_nodo("0")
    assert v0.role == "reference"
    assert v0.source_id is None
    assert v0.known_value == F(0)


def test_costruzioni_manuali_illegali():
    with pytest.raises(ValueError, match="riferimento senza known_value"):
        NodalVariable("v_0", "0", "reference")
    with pytest.raises(ValueError, match="riferimento con known_value"):
        NodalVariable("v_0", "0", "reference", known_value=F(3))
    with pytest.raises(ValueError, match="known_value su un ruolo"):
        NodalVariable("v_a", "a", "unknown", known_value=F(1))
    with pytest.raises(ValueError, match="senza source_id"):
        NodalVariable("v_a", "a", "known_from_source", known_value=F(1))
    with pytest.raises(ValueError, match="senza known_value"):
        NodalVariable("v_a", "a", "known_from_source", "V1")
    with pytest.raises(TypeError, match="Fraction"):
        NodalVariable("v_a", "a", "known_from_source", "V1", 5.0)  # type: ignore[arg-type]


def test_kcl_con_vicino_noto_resta_fisica():
    ir = _divisore(("b", "0"), F(5))
    stato = _fino_alle_incognite(ir)
    _, dopo = scrivi_kcl_al_nodo(ir, stato, "a")
    nodi = {t.variable.node for t in dopo.equations[0].terms}
    assert nodi == {"a", "b", "0"}
    assert stato.variabile_del_nodo("a").known_value is None
    assert stato.variabile_del_nodo("b").known_value == F(5)
    assert stato.variabile_del_nodo("0").known_value == F(0)


def test_inversione_sorgente_cambia_stato_non_topologia_kcl():
    diretto = _divisore(("b", "0"), F(5))
    inverso = _divisore(("0", "b"), F(5))
    eq_d = scrivi_kcl_al_nodo(diretto, _fino_alle_incognite(diretto), "a")[1].equations[0]
    eq_i = scrivi_kcl_al_nodo(inverso, _fino_alle_incognite(inverso), "a")[1].equations[0]
    assert eq_d.terms == eq_i.terms
    assert eq_d.rhs == eq_i.rhs
    assert _fino_alle_incognite(diretto).variabile_del_nodo("b").known_value == F(5)
    assert _fino_alle_incognite(inverso).variabile_del_nodo("b").known_value == -F(5)


def test_ogni_termine_non_unknown_e_valutabile():
    ir = _divisore(("b", "0"), F(5))
    stato = _fino_alle_incognite(ir)
    for nodo in nodi_kcl_ordinarie(ir):
        _, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
    for eq in stato.equations:
        for termine in eq.terms:
            dichiarazione = stato.variabile_del_nodo(termine.variable.node)
            if dichiarazione.role != "unknown":
                assert dichiarazione.known_value is not None


def test_valore_noto_leggibile_dalla_dichiarazione():
    stato = _fino_alle_incognite(_divisore(("b", "0"), F(5)))
    assert stato.variabile_del_nodo("b").known_value == F(5)
    assert stato.variabile_del_nodo("0").known_value == F(0)


def test_sostituzione_manuale_chiude_equazione_e_stato():
    ir = _divisore(("b", "0"), F(5))
    stato = _fino_alle_incognite(ir)
    _, dopo = scrivi_kcl_al_nodo(ir, stato, "a")
    eq = dopo.equations[0]
    acc = eq.rhs
    coeff_va = None
    for termine in eq.terms:
        dichiarazione = dopo.variabile_del_nodo(termine.variable.node)
        if dichiarazione.role == "unknown":
            assert coeff_va is None
            coeff_va = termine.coefficient
            continue
        assert dichiarazione.known_value is not None
        acc -= termine.coefficient * dichiarazione.known_value
    assert coeff_va == F(3, 20)
    assert acc == F(1, 2)


def test_corrente_e_tensione_nota_insieme():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(20), "R2"),
        Component.of("I1", "current_source_dc", ("a", "0"), F(2), "I1"),
    ))
    stato = _fino_alle_incognite(ir)
    _, dopo = scrivi_kcl_al_nodo(ir, stato, "a")
    eq = dopo.equations[0]
    assert {t.variable.node for t in eq.terms} == {"a", "b", "0"}
    assert eq.rhs == -F(2)
    assert dopo.variabile_del_nodo("b").known_value == F(5)
    assert dopo.variabile_del_nodo("0").known_value == F(0)
    assert _coeff(eq)["a"] == F(3, 20)
    assert _coeff(eq)["b"] == -F(1, 10)
    assert _coeff(eq)["0"] == -F(1, 20)


def test_cross_check_kernel_solo_nel_test():
    ir = _divisore(("b", "0"), F(5))
    stato = _fino_alle_incognite(ir)
    _, dopo = scrivi_kcl_al_nodo(ir, stato, "a")
    eq = dopo.equations[0]
    acc = eq.rhs
    coeff_va = None
    for termine in eq.terms:
        dichiarazione = dopo.variabile_del_nodo(termine.variable.node)
        if dichiarazione.role == "unknown":
            coeff_va = termine.coefficient
        else:
            acc -= termine.coefficient * dichiarazione.known_value
    va = acc / coeff_va
    assert va == F(10, 3)
    assert solve_dc(ir)["R2"]["voltage"] == va
    assert solve_dc(ir)["V1"]["voltage"] == F(5)


def test_sorgente_flottante_non_fissa_valori():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(10), "R2"),
    ))
    assert _generatori_verso_riferimento(ir) == {}
    assert not nodale_disponibile(ir, "voltage")
    stato = _fino_alle_incognite(ir)
    assert stato.variabile_del_nodo("a").role == "unknown"
    assert stato.variabile_del_nodo("b").role == "unknown"
    assert stato.variabile_del_nodo("a").known_value is None
    assert stato.variabile_del_nodo("b").known_value is None


def test_due_sorgenti_grounded_su_nodi_distinti():
    ir = _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("b", "0"), F(7), "V2"),
        Component.of("R1", "resistor", ("c", "a"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "b"), F(20), "R2"),
        Component.of("R3", "resistor", ("c", "0"), F(4), "R3"),
    ))
    stato = _fino_alle_incognite(ir)
    assert stato.variabile_del_nodo("a").known_value == F(5)
    assert stato.variabile_del_nodo("b").known_value == F(7)
    assert stato.variabile_del_nodo("c").role == "unknown"


def test_ordine_componenti_non_cambia_i_binding():
    comps = (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("0", "b"), F(7), "V2"),
        Component.of("R1", "resistor", ("c", "a"), F(10), "R1"),
        Component.of("R2", "resistor", ("c", "0"), F(4), "R2"),
    )
    diretto = _fino_alle_incognite(_ir(("0", "a", "b", "c"), comps))
    inverso = _fino_alle_incognite(_ir(("0", "a", "b", "c"), tuple(reversed(comps))))
    assert [v.node for v in diretto.variables] == [v.node for v in inverso.variables]
    for nodo in ("a", "b", "c", "0"):
        va = diretto.variabile_del_nodo(nodo)
        vb = inverso.variabile_del_nodo(nodo)
        assert va.role == vb.role
        assert va.source_id == vb.source_id
        assert va.known_value == vb.known_value
    assert diretto.variabile_del_nodo("a").known_value == F(5)
    assert diretto.variabile_del_nodo("b").known_value == -F(7)


def test_binding_duplicata_fail_closed():
    ir = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("V2", "voltage_source_dc", ("0", "a"), F(3), "V2"),
        Component.of("R1", "resistor", ("b", "a"), F(10), "R1"),
        Component.of("R2", "resistor", ("b", "0"), F(4), "R2"),
    ))
    with pytest.raises(ValueError, match="due generatori verso riferimento"):
        _generatori_verso_riferimento(ir)
    d1 = _fino_al_riferimento(ir)
    with pytest.raises(ValueError, match="due generatori verso riferimento"):
        applica_passo("define_nodal_unknowns", ir, d1)


def test_contratto_di_segno_del_helper():
    assert _valore_noto_verso_riferimento("b", "0", F(5)) == F(5)
    assert _valore_noto_verso_riferimento("0", "b", F(5)) == -F(5)
    assert _valore_noto_verso_riferimento("b", "0", -F(5)) == -F(5)
    assert _valore_noto_verso_riferimento("0", "b", -F(5)) == F(5)
    with pytest.raises(ValueError, match="non è verso il riferimento"):
        _valore_noto_verso_riferimento("a", "b", F(5))


def test_nessun_voltage_constraint_e_planner_invariato():
    ir = _divisore(("b", "0"), F(5))
    stato = _fino_alle_incognite(ir)
    for nodo in nodi_kcl_ordinarie(ir):
        _, stato = scrivi_kcl_al_nodo(ir, stato, nodo)
    assert all(eq.kind == "kcl" for eq in stato.equations)
    assert ANALYTICAL_KINDS == frozenset({
        "choose_reference", "define_nodal_unknowns", "write_kcl",
    })
    assert [a.kind for a in _azioni_nodali(ir)] == [
        "choose_reference", "define_nodal_unknowns", "write_kcl",
    ]
