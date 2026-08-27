"""VCVS/VCCS nel DC certificato A/B: oracoli, floating, corruzione, corpus."""
from __future__ import annotations

import importlib
from fractions import Fraction

import pytest

from kirchhoff.domain.independent_dc import (
    TableauBuildError,
    TableauSingularError,
    solve_dc_tableau,
)
from kirchhoff.domain.ir import IR, Component, Magnitude, Request, canonicalize
from kirchhoff.domain.ir.schema import CONTROLLED_SOURCE_TYPES, EXPECTED_UNIT
from kirchhoff.domain.mna import solve_dc
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Validated, validate
from kirchhoff.domain.verify import (
    ATTESTAZIONE_COSTITUTIVE,
    constitutive_residuals,
    verify,
)
from kirchhoff.eval.generator_controlled import generate_vccs_case, generate_vcvs_case
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import ATTESTAZIONE_PERCORSI, Solved, resolve

F = Fraction


def _dc(comps, requests=(), nodes=None) -> IR:
    if nodes is None:
        nodes = tuple(sorted({t for c in comps for t in (*c.terminals, *(c.control_nodes or ()))}))
    return IR("1.0.0", "dc", "generated", nodes, comps, requests)


def _spine():
    return importlib.import_module("kirchhoff.pipeline.resolve")


def _vcvs_massa():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(2), "E_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(5), "R_2"),
    ), (Request("qv", "voltage", "E1"), Request("qi", "current", "E1")))


ATTESO_VCVS_MASSA = {
    "V1": {"voltage": F(10), "current": F(-1)},
    "R1": {"voltage": F(10), "current": F(1)},
    "E1": {"voltage": F(20), "current": F(-4)},
    "R2": {"voltage": F(20), "current": F(4)},
}


def _vcvs_floating():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(12), "V_1"),
        Component.of("R1", "resistor", ("A", "B"), F(4), "R_1"),
        Component.of("R2", "resistor", ("B", "0"), F(8), "R_2"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(2), "E_1", control_nodes=("A", "B")),
        Component.of("R3", "resistor", ("C", "0"), F(10), "R_3"),
    ), (Request("qv", "voltage", "E1"), Request("qi", "current", "E1")))


ATTESO_VCVS_FLOAT = {
    "V1": {"voltage": F(12), "current": F(-1)},
    "R1": {"voltage": F(4), "current": F(1)},
    "R2": {"voltage": F(8), "current": F(1)},
    "E1": {"voltage": F(8), "current": F(-4, 5)},
    "R3": {"voltage": F(8), "current": F(4, 5)},
}


def _vcvs_negativo():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(-2), "E_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(5), "R_2"),
    ), (Request("qv", "voltage", "E1"), Request("qi", "current", "E1")))


ATTESO_VCVS_NEG = {
    "V1": {"voltage": F(10), "current": F(-1)},
    "R1": {"voltage": F(10), "current": F(1)},
    "E1": {"voltage": F(-20), "current": F(4)},
    "R2": {"voltage": F(-20), "current": F(-4)},
}


def _vccs_massa():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("G1", "voltage_controlled_current_source", ("0", "C"),
                     F(1, 10), "G_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(20), "R_2"),
    ), (Request("qv", "voltage", "G1"), Request("qi", "current", "G1")))


ATTESO_VCCS_MASSA = {
    "V1": {"voltage": F(10), "current": F(-1)},
    "R1": {"voltage": F(10), "current": F(1)},
    "G1": {"voltage": F(-20), "current": F(1)},
    "R2": {"voltage": F(20), "current": F(1)},
}


def _vccs_floating():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(12), "V_1"),
        Component.of("R1", "resistor", ("A", "B"), F(4), "R_1"),
        Component.of("R2", "resistor", ("B", "0"), F(8), "R_2"),
        Component.of("G1", "voltage_controlled_current_source", ("0", "C"),
                     F(1, 5), "G_1", control_nodes=("A", "B")),
        Component.of("R3", "resistor", ("C", "0"), F(10), "R_3"),
    ), (Request("qv", "voltage", "G1"), Request("qi", "current", "G1")))


ATTESO_VCCS_FLOAT = {
    "V1": {"voltage": F(12), "current": F(-1)},
    "R1": {"voltage": F(4), "current": F(1)},
    "R2": {"voltage": F(8), "current": F(1)},
    "G1": {"voltage": F(-8), "current": F(4, 5)},
    "R3": {"voltage": F(8), "current": F(4, 5)},
}


def _vccs_negativo():
    return _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("G1", "voltage_controlled_current_source", ("0", "C"),
                     F(-1, 10), "G_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(20), "R_2"),
    ), (Request("qv", "voltage", "G1"), Request("qi", "current", "G1")))


ATTESO_VCCS_NEG = {
    "V1": {"voltage": F(10), "current": F(-1)},
    "R1": {"voltage": F(10), "current": F(1)},
    "G1": {"voltage": F(20), "current": F(-1)},
    "R2": {"voltage": F(-20), "current": F(-1)},
}


ORACOLI = (
    ("vcvs_massa", _vcvs_massa, ATTESO_VCVS_MASSA),
    ("vcvs_floating", _vcvs_floating, ATTESO_VCVS_FLOAT),
    ("vcvs_negativo", _vcvs_negativo, ATTESO_VCVS_NEG),
    ("vccs_massa", _vccs_massa, ATTESO_VCCS_MASSA),
    ("vccs_floating", _vccs_floating, ATTESO_VCCS_FLOAT),
    ("vccs_negativo", _vccs_negativo, ATTESO_VCCS_NEG),
)


@pytest.mark.parametrize("nome,fabbrica,atteso", ORACOLI, ids=[o[0] for o in ORACOLI])
def test_oracolo_manuale_a_b_resolve(nome, fabbrica, atteso):
    ir = fabbrica()
    a = solve_dc(ir)
    b = solve_dc_tableau(ir)
    assert a == atteso
    assert b == atteso
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione == atteso
    assert ATTESTAZIONE_PERCORSI in esito.verifiche
    assert ATTESTAZIONE_COSTITUTIVE in esito.verifiche
    assert all(r == 0 for r in constitutive_residuals(ir, esito.soluzione).values())


def test_controllo_zero_vcvs():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(5), "E_1", control_nodes=("A", "A")),
        Component.of("R2", "resistor", ("C", "0"), F(4), "R_2"),
    ))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["E1"]["voltage"] == 0
    assert esito.soluzione["E1"]["current"] == 0


def test_controllo_zero_vccs():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("G1", "voltage_controlled_current_source", ("0", "C"),
                     F(3, 10), "G_1", control_nodes=("A", "A")),
        Component.of("R2", "resistor", ("C", "0"), F(4), "R_2"),
    ))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["G1"]["current"] == 0


def test_vcvs_e_vccs_insieme():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(2), "E_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(5), "R_2"),
        Component.of("G1", "voltage_controlled_current_source", ("0", "D"),
                     F(1, 10), "G_1", control_nodes=("C", "0")),
        Component.of("R3", "resistor", ("D", "0"), F(4), "R_3"),
    ))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["E1"]["voltage"] == F(20)
    assert esito.soluzione["G1"]["current"] == F(2)


def test_due_vcvs():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(6), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(6), "R_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(2), "E_1", control_nodes=("A", "0")),
        Component.of("R2", "resistor", ("C", "0"), F(3), "R_2"),
        Component.of("E2", "voltage_controlled_voltage_source", ("D", "0"),
                     F(-1), "E_2", control_nodes=("C", "0")),
        Component.of("R3", "resistor", ("D", "0"), F(4), "R_3"),
    ))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["E2"]["voltage"] == F(-12)


def test_ponte_controllo_interno():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("P", "0"), F(12), "V_1"),
        Component.of("R1", "resistor", ("P", "X"), F(10), "R_1"),
        Component.of("R2", "resistor", ("P", "Y"), F(20), "R_2"),
        Component.of("R3", "resistor", ("X", "0"), F(30), "R_3"),
        Component.of("R4", "resistor", ("Y", "0"), F(40), "R_4"),
        Component.of("Rg", "resistor", ("X", "Y"), F(50), "R_g"),
        Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"),
                     F(1), "E_1", control_nodes=("X", "Y")),
        Component.of("Rl", "resistor", ("C", "0"), F(10), "R_l"),
    ))
    a = solve_dc(ir)
    assert a == solve_dc_tableau(ir)
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["E1"]["voltage"] == a["R3"]["voltage"] - a["R4"]["voltage"]


def test_ordine_componenti_irrilevante():
    ir = _vcvs_floating()
    permutato = IR(ir.ir_version, ir.domain, ir.source_kind, ir.nodes,
                   tuple(reversed(ir.components)), ir.requests, ir.omega)
    assert solve_dc_tableau(ir) == solve_dc_tableau(permutato)


def test_unita_e_segni():
    assert EXPECTED_UNIT["voltage_controlled_voltage_source"] == "dimensionless"
    assert EXPECTED_UNIT["voltage_controlled_current_source"] == "siemens"
    Component.of("E1", "voltage_controlled_voltage_source", ("A", "0"), F(2), "E", control_nodes=("B", "0"))
    Component.of("E2", "voltage_controlled_voltage_source", ("A", "0"), F(-2), "E", control_nodes=("B", "0"))
    Component.of("G1", "voltage_controlled_current_source", ("A", "0"), F(1, 10), "G", control_nodes=("B", "0"))
    Component.of("G2", "voltage_controlled_current_source", ("A", "0"), F(-1, 10), "G", control_nodes=("B", "0"))
    with pytest.raises(ValueError, match="volt"):
        Component("E1", "voltage_controlled_voltage_source", ("A", "0"),
                  Magnitude(F(2), "volt"), "E", control_nodes=("B", "0"))


def test_control_nodes_obbligatori():
    with pytest.raises(ValueError, match="senza nodi di controllo"):
        Component.of("E1", "voltage_controlled_voltage_source", ("A", "0"), F(2), "E")
    with pytest.raises(ValueError, match="non è controllato"):
        Component.of("R1", "resistor", ("A", "0"), F(10), "R", control_nodes=("B", "0"))
    with pytest.raises(ValueError, match="coppia"):
        Component.of("E1", "voltage_controlled_voltage_source", ("A", "0"), F(2), "E",
                     control_nodes=("B", "0", "Z"))  # type: ignore[arg-type]


def test_canonicalizzazione_distingue_il_controllo():
    e_cd = Component.of("E1", "voltage_controlled_voltage_source", ("A", "B"), F(2), "E", control_nodes=("C", "D"))
    e_ef = Component.of("E1", "voltage_controlled_voltage_source", ("A", "B"), F(2), "E", control_nodes=("E", "F"))
    assert e_cd.control_nodes != e_ef.control_nodes
    ir_cd = IR("1.0.0", "dc", "generated", ("0", "A", "B", "C", "D"),
               (Component.of("V1", "voltage_source_dc", ("C", "0"), F(1), "V"),
                Component.of("R1", "resistor", ("C", "0"), F(1), "R"),
                Component.of("R2", "resistor", ("D", "0"), F(1), "R2"),
                Component.of("R3", "resistor", ("A", "B"), F(1), "R3"), e_cd), ())
    ir_ef = IR("1.0.0", "dc", "generated", ("0", "A", "B", "E", "F"),
               (Component.of("V1", "voltage_source_dc", ("E", "0"), F(1), "V"),
                Component.of("R1", "resistor", ("E", "0"), F(1), "R"),
                Component.of("R2", "resistor", ("F", "0"), F(1), "R2"),
                Component.of("R3", "resistor", ("A", "B"), F(1), "R3"), e_ef), ())
    assert canonicalize(ir_cd) != canonicalize(ir_ef)


def test_nodo_fantasma_e_refusal_topology():
    ir = object.__new__(IR)
    e1 = Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"), F(2), "E_1", control_nodes=("GHOST", "0"))
    comps = (
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"), e1,
        Component.of("R2", "resistor", ("C", "0"), F(5), "R_2"),
    )
    object.__setattr__(ir, "ir_version", "1.0.0")
    object.__setattr__(ir, "domain", "dc")
    object.__setattr__(ir, "source_kind", "generated")
    object.__setattr__(ir, "nodes", ("0", "A", "C"))
    object.__setattr__(ir, "components", comps)
    object.__setattr__(ir, "requests", ())
    object.__setattr__(ir, "omega", F(0))
    esito = validate(ir)
    assert isinstance(esito, Refusal) and esito.cause == "topology" and esito.subject == "GHOST"
    assert isinstance(resolve(ir), Refusal)


def test_vcvs_non_nelle_maglie_indipendenti():
    ir = _dc((
        Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
        Component.of("E1", "voltage_controlled_voltage_source", ("A", "0"), F(1), "E_1", control_nodes=("A", "0")),
        Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
    ))
    assert isinstance(validate(ir), Validated)


def test_parser_non_scambia_terminali_e_controllo():
    ir = leggi("V1 A 0 10 volt\nR1 A 0 10 ohm\nE1 C 0 A 0 2\nR2 C 0 5 ohm\n")
    assert ir.component("E1").terminals == ("C", "0")
    assert ir.component("E1").control_nodes == ("A", "0")
    assert resolve(ir).soluzione["E1"]["voltage"] == F(20)
    irg = leggi("V1 A 0 10 volt\nR1 A 0 10 ohm\nG1 0 C A 0 1/10 siemens\nR2 C 0 20 ohm\n")
    assert irg.component("G1").terminals == ("0", "C")
    assert resolve(irg).soluzione["G1"]["current"] == F(1)
    with pytest.raises(ValueError, match="VCVS"):
        leggi("E1 A 0 2")


def test_a_corrotto_vcvs(monkeypatch):
    import kirchhoff.domain.mna as mna
    vero = mna.solve_dc
    def rotto(ir):
        sol = vero(ir)
        ramo = dict(sol["E1"]); ramo["voltage"] = ramo["voltage"] + F(1)
        return {**sol, "E1": ramo}
    monkeypatch.setattr(mna, "solve_dc", rotto)
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"


def test_a_corrotto_vccs(monkeypatch):
    import kirchhoff.domain.mna as mna
    vero = mna.solve_dc
    def rotto(ir):
        sol = vero(ir)
        ramo = dict(sol["G1"]); ramo["current"] = ramo["current"] + F(1)
        return {**sol, "G1": ramo}
    monkeypatch.setattr(mna, "solve_dc", rotto)
    esito = resolve(_vccs_massa())
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"


def test_b_corrotto(monkeypatch):
    vero = solve_dc_tableau
    def rotto(ir):
        sol = vero(ir)
        ramo = dict(sol["E1"]); ramo["current"] = ramo["current"] + F(1)
        return {**sol, "E1": ramo}
    monkeypatch.setattr(_spine(), "solve_dc_tableau", rotto)
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"


def test_legge_b_mu_invertito(monkeypatch):
    import kirchhoff.domain.independent_dc as bmod
    vero = bmod._costitutiva
    def rotto(c, col_v, col_i, row, known, vcontrol=None):
        if c.type == "voltage_controlled_voltage_source":
            c = Component.of(c.id, c.type, c.terminals, -c.value.amount, c.symbolic, control_nodes=c.control_nodes)
        return vero(c, col_v, col_i, row, known, vcontrol)
    monkeypatch.setattr(bmod, "_costitutiva", rotto)
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"


def test_bug_interno_b(monkeypatch):
    monkeypatch.setattr(_spine(), "solve_dc_tableau", lambda ir: (_ for _ in ()).throw(RuntimeError("boom")))
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Failure) and esito.dove == "verify"


def test_b_singolare(monkeypatch):
    monkeypatch.setattr(_spine(), "solve_dc_tableau", lambda ir: (_ for _ in ()).throw(TableauSingularError("colonna 0")))
    esito = resolve(_vccs_massa())
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"


def test_disaccordo_non_chiama_render(monkeypatch):
    import kirchhoff.domain.mna as mna
    chiamato = {"render": False}
    vero = mna.solve_dc
    def rotto(ir):
        sol = vero(ir)
        ramo = dict(sol["E1"]); ramo["voltage"] = ramo["voltage"] + F(3)
        return {**sol, "E1": ramo}
    monkeypatch.setattr(mna, "solve_dc", rotto)
    monkeypatch.setattr(_spine(), "render", lambda ir, lay: chiamato.__setitem__("render", True) or "<svg/>")
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Refusal) and chiamato["render"] is False


def test_renderer_assente_non_e_failure():
    esito = resolve(_vcvs_massa())
    assert isinstance(esito, Solved) and esito.svg is None


def _raw(cid, tipo, term, mag, ctrl):
    rotto = object.__new__(Component)
    for campo, valore in (("id", cid), ("type", tipo), ("terminals", term),
                          ("value", mag), ("symbolic", cid), ("phase_steps", 0),
                          ("provenance", None), ("control_nodes", ctrl)):
        object.__setattr__(rotto, campo, valore)
    return rotto


def test_mna_e_tableau_senza_control_nodes():
    e = _raw("E1", "voltage_controlled_voltage_source", ("C", "0"), Magnitude(F(2), "dimensionless"), None)
    ir = _dc((Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"),
              Component.of("R1", "resistor", ("A", "0"), F(10), "R"), e,
              Component.of("R2", "resistor", ("C", "0"), F(5), "R2")))
    with pytest.raises(ValueError, match="senza nodi"):
        solve_dc(ir)
    g = _raw("G1", "voltage_controlled_current_source", ("C", "0"), Magnitude(F(1, 10), "siemens"), None)
    ir2 = _dc((Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"),
               Component.of("R1", "resistor", ("A", "0"), F(10), "R"), g,
               Component.of("R2", "resistor", ("C", "0"), F(5), "R2")))
    with pytest.raises(ValueError, match="senza nodi"):
        solve_dc_tableau(ir2)


def test_vcontrol_irraggiungibile():
    from kirchhoff.domain.independent_dc import _albero_ricoprente, _vcontrol_coeffs
    ir = _vcvs_massa()
    parent, _ = _albero_ricoprente(ir)
    with pytest.raises(TableauBuildError, match="non raggiungibili"):
        _vcontrol_coeffs(ir, parent, "Z", "0")


def test_verify_costitutiva_rotta():
    ir = _vcvs_massa()
    sol = dict(solve_dc(ir))
    ramo = dict(sol["E1"]); ramo["voltage"] = ramo["voltage"] + F(1); sol["E1"] = ramo
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal) and esito.cause == "residual"


def test_validate_resistore_con_controllo():
    rotto = _raw("R1", "resistor", ("A", "0"), Magnitude(F(10), "ohm"), ("A", "0"))
    ir = object.__new__(IR)
    for campo, valore in (("ir_version", "1.0.0"), ("domain", "dc"), ("source_kind", "generated"),
                          ("nodes", ("0", "A")), ("components", (
                              Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"), rotto)),
                          ("requests", ()), ("omega", F(0))):
        object.__setattr__(ir, campo, valore)
    esito = validate(ir)
    assert isinstance(esito, Refusal) and esito.cause == "topology"


def test_validate_controllata_senza_metadata():
    rotto = _raw("E1", "voltage_controlled_voltage_source", ("C", "0"), Magnitude(F(2), "dimensionless"), None)
    ir = object.__new__(IR)
    for campo, valore in (("ir_version", "1.0.0"), ("domain", "dc"), ("source_kind", "generated"),
                          ("nodes", ("0", "A", "C")), ("components", (
                              Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"),
                              Component.of("R1", "resistor", ("A", "0"), F(10), "R"), rotto,
                              Component.of("R2", "resistor", ("C", "0"), F(5), "R2"))),
                          ("requests", ()), ("omega", F(0))):
        object.__setattr__(ir, campo, valore)
    esito = validate(ir)
    assert isinstance(esito, Refusal) and esito.subject == "E1"


def test_constitutive_senza_metadata_salta():
    rotto = _raw("E1", "voltage_controlled_voltage_source", ("C", "0"), Magnitude(F(2), "dimensionless"), None)
    ir = _dc((Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"),
              Component.of("R1", "resistor", ("A", "0"), F(10), "R"), rotto,
              Component.of("R2", "resistor", ("C", "0"), F(5), "R2")))
    assert constitutive_residuals(ir, {"V1": {"voltage": F(10), "current": F(0)},
                                       "R1": {"voltage": F(10), "current": F(1)},
                                       "E1": {"voltage": F(0), "current": F(0)},
                                       "R2": {"voltage": F(0), "current": F(0)}}) == {}


def test_vcontrol_pubblicato_irraggiungibile():
    from kirchhoff.domain.verify import _vcontrol_pubblicato
    with pytest.raises(KeyError, match="non raggiungibile"):
        _vcontrol_pubblicato(_vcvs_massa(), solve_dc(_vcvs_massa()), "Z", "0")


def test_mna_assemble_vccs_senza_control():
    import kirchhoff.domain.mna as mna
    rotto = _raw("G1", "voltage_controlled_current_source", ("C", "0"), Magnitude(F(1, 10), "siemens"), None)
    ir = _dc((Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V"),
              Component.of("R1", "resistor", ("A", "0"), F(10), "R"), rotto,
              Component.of("R2", "resistor", ("C", "0"), F(5), "R2")))
    kinds = [(c, *mna._classify_dc(c)) for c in ir.components]
    with pytest.raises(ValueError, match="senza nodi"):
        mna._assemble(ir, kinds, F(0))


def test_corpus_controlled():
    accordi = 0
    fingerprints = set()
    for i in range(1, 31):
        ir = generate_vcvs_case(i)
        fingerprints.add(("E", tuple((c.id, c.type, c.terminals, c.control_nodes, c.value.amount) for c in ir.components)))
        esito = resolve(ir)
        assert isinstance(esito, Solved)
        assert solve_dc_tableau(ir) == esito.soluzione
        assert all(r == 0 for r in constitutive_residuals(ir, esito.soluzione).values())
        accordi += 1
    for i in range(1, 31):
        ir = generate_vccs_case(i)
        fingerprints.add(("G", tuple((c.id, c.type, c.terminals, c.control_nodes, c.value.amount) for c in ir.components)))
        esito = resolve(ir)
        assert isinstance(esito, Solved)
        assert solve_dc_tableau(ir) == esito.soluzione
        assert all(r == 0 for r in constitutive_residuals(ir, esito.soluzione).values())
        accordi += 1
    assert accordi == 60
    assert len(fingerprints) == 60
