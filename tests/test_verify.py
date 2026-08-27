"""I controlli di domain/verify, ciascuno visto fallire."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.verify import kvl_residuals, verify
from kirchhoff.pipeline.netlist import leggi

F = Fraction


def test_kvl_su_una_soluzione_mna_e_identicamente_nulla():
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")
    from kirchhoff.domain.mna import solve_dc
    residui = kvl_residuals(ir, solve_dc(ir))
    assert residui, "un partitore ha una corda"
    assert all(r == 0 for r in residui.values())


def test_kvl_vede_una_tensione_di_corda_falsa():
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")
    from kirchhoff.domain.mna import solve_dc
    sol = {cid: dict(val) for cid, val in solve_dc(ir).items()}
    corda = next(iter(kvl_residuals(ir, sol)))
    sol[corda]["voltage"] = sol[corda]["voltage"] + 1
    residui = kvl_residuals(ir, sol)
    assert residui[corda] == 1


def test_verify_rifiuta_la_corda_falsa():
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")
    from kirchhoff.domain.mna import solve_dc
    sol = {cid: dict(val) for cid, val in solve_dc(ir).items()}
    corda = next(iter(kvl_residuals(ir, sol)))
    sol[corda]["voltage"] += 1
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert esito.subject == corda


def test_una_isola_non_entra_nei_residui_di_maglia():
    ir = leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nR2 c d 20 ohm\nR3 c d 30 ohm\n")
    sol = {c.id: {"voltage": F(0), "current": F(0)} for c in ir.components}
    residui = kvl_residuals(ir, sol)
    assert "R2" not in residui and "R3" not in residui


def test_un_passivo_fasoriale_non_passa_dalla_sanita_razionale():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    from kirchhoff.domain.mna import solve_phasor
    assert verify(ir, solve_phasor(ir)) is None


def test_controlli_eseguiti_in_dc_includono_la_sanita():
    from kirchhoff.domain.mna import solve_dc
    from kirchhoff.domain.verify import controlli_eseguiti
    ir = leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n")
    fatti = controlli_eseguiti(ir, solve_dc(ir))
    assert fatti[-1] == "sanità fisica"
    assert "bilancio di potenza" in fatti


def test_controlli_eseguiti_in_ac_non_attestano_la_sanita_razionale():
    from kirchhoff.domain.mna import solve_phasor
    from kirchhoff.domain.verify import controlli_eseguiti
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    fatti = controlli_eseguiti(ir, solve_phasor(ir))
    assert "sanità fisica" not in fatti
    assert "legge dei nodi" in fatti
    assert "identità di Tellegen" in fatti
    assert "bilancio di potenza" not in fatti


def test_isola_dichiarata_nell_ir_non_entra_nei_residui_kvl():
    """Ramo 47: un componente i cui nodi non stanno nell'albero dal riferimento."""
    ir = IR(
        "1.0.0", "dc_resistive", "generated", ("0", "A", "C", "D"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
         Component.of("R2", "resistor", ("C", "D"), F(20), "R_2"),
         Component.of("R3", "resistor", ("C", "D"), F(30), "R_3")),
        ())
    sol = {c.id: {"voltage": F(0), "current": F(0)} for c in ir.components}
    residui = kvl_residuals(ir, sol)
    assert "R2" not in residui and "R3" not in residui


def test_passivo_che_eroga_e_rifiuto_di_sanita(monkeypatch):
    """Ramo 83: potenza razionale negativa su un passivo, dopo KCL/KVL/ΣVI."""
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(0))
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        ())
    sol = {
        "E1": {"voltage": F(10), "current": F(1)},
        "R1": {"voltage": F(10), "current": F(-1)},
    }
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "sanity"
    assert esito.subject == "R1"
