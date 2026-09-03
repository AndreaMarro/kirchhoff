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


def test_kvl_albero_percorre_il_primo_terminale():
    """Ramo terminals[0] == qui: l'albero parte dal primo morsetto del ramo."""
    ir = IR(
        "1.0.0", "dc_resistive", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("0", "A"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        ())
    from kirchhoff.domain.mna import solve_dc
    residui = kvl_residuals(ir, solve_dc(ir))
    assert all(r == 0 for r in residui.values())


def test_passivo_che_eroga_e_rifiuto_di_sanita(monkeypatch):
    """Potenza razionale negativa su un passivo, dopo KCL/KVL/ΣVI."""
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


def test_rifiuto_scarto_potenza_soggetto_deve_essere_primo_componente(monkeypatch):
    """Il rifiuto per ΣVI nomina ir.components[0].id, non un altro indice."""
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "constitutive_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(1))
    monkeypatch.setattr(ver, "_sanita", lambda ir, sol: None)
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")
    from kirchhoff.domain.mna import solve_dc
    sol = solve_dc(ir)
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert esito.subject == ir.components[0].id
    assert esito.subject == "V1"
    assert esito.subject != "R1"
    assert esito.subject != "R2"


def test_verify_rifiuta_sorgente_controllata_vcvs_corrotto(monkeypatch):
    """Se la legge VCVS è violata, verify deve rifiutare anche quando KCL/KVL/ΣVI passano."""
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(0))
    monkeypatch.setattr(ver, "_sanita", lambda ir, sol: None)
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A", "C"),
        (Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
         Component.of("E1", "voltage_controlled_voltage_source", ("C", "0"), F(2), "E_1", control_nodes=("A", "0")),
         Component.of("R2", "resistor", ("C", "0"), F(5), "R_2")),
        ())
    from kirchhoff.domain.mna import solve_dc
    sol = {cid: dict(v) for cid, v in solve_dc(ir).items()}
    sol["E1"]["voltage"] = sol["E1"]["voltage"] + F(1)
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert esito.subject == "E1"


def test_verify_rifiuta_sorgente_controllata_vccs_corrotto(monkeypatch):
    """Se la legge VCCS è violata, verify deve rifiutare."""
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(0))
    monkeypatch.setattr(ver, "_sanita", lambda ir, sol: None)
    ir = IR(
        "1.0.0", "dc", "generated", ("0", "A", "C"),
        (Component.of("V1", "voltage_source_dc", ("A", "0"), F(10), "V_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
         Component.of("G1", "voltage_controlled_current_source", ("0", "C"), F(1, 10), "G_1", control_nodes=("A", "0")),
         Component.of("R2", "resistor", ("C", "0"), F(20), "R_2")),
        ())
    from kirchhoff.domain.mna import solve_dc
    sol = {cid: dict(v) for cid, v in solve_dc(ir).items()}
    sol["G1"]["current"] = sol["G1"]["current"] + F(1)
    esito = verify(ir, sol)
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert esito.subject == "G1"


def test_compare_exact_rifiuta_insieme_componenti_diverso():
    from kirchhoff.domain.verify import compare_exact_solution_paths
    a = {"R1": {"voltage": F(1), "current": F(1)}, "R2": {"voltage": F(2), "current": F(2)}}
    b = {"R1": {"voltage": F(1), "current": F(1)}}
    esito = compare_exact_solution_paths(a, b)
    assert isinstance(esito, Refusal) and esito.cause == "path_disagreement"
    assert "R2" in esito.diagnosis
    esito2 = compare_exact_solution_paths(b, a)
    assert isinstance(esito2, Refusal) and esito2.cause == "path_disagreement"


def test_compare_exact_rifiuta_grandezza_mancante_e_non_fraction():
    from kirchhoff.domain.verify import compare_exact_solution_paths
    a = {"R1": {"voltage": F(1), "current": F(1)}}
    b = {"R1": {"voltage": F(1)}}
    assert compare_exact_solution_paths(a, b).cause == "path_disagreement"
    assert compare_exact_solution_paths(b, a).cause == "path_disagreement"
    af = {"R1": {"voltage": 1.0, "current": F(1)}}
    bf = {"R1": {"voltage": F(1), "current": F(1)}}
    assert compare_exact_solution_paths(af, bf).cause == "path_disagreement"
    assert compare_exact_solution_paths(bf, af).cause == "path_disagreement"
    ac = {"R1": {"voltage": F(1), "current": F(1)}}
    bc = {"R1": {"voltage": F(2), "current": F(1)}}
    assert compare_exact_solution_paths(ac, bc).cause == "path_disagreement"


def test_compare_exact_accetta_identita_esatta():
    from kirchhoff.domain.verify import compare_exact_solution_paths
    a = {"R1": {"voltage": F(3, 2), "current": F(7, 3)}}
    b = {"R1": {"voltage": F(3, 2), "current": F(7, 3)}}
    assert compare_exact_solution_paths(a, b) is None
    assert compare_exact_solution_paths(b, a) is None
