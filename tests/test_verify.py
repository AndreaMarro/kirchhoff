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
    """Un ramo su nodi che l'albero dal riferimento non raggiunge si salta."""
    ir = leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nR2 c d 20 ohm\nR3 c d 30 ohm\n")
    sol = {c.id: {"voltage": F(0), "current": F(0)} for c in ir.components}
    residui = kvl_residuals(ir, sol)
    assert "R2" not in residui and "R3" not in residui


def test_un_passivo_fasoriale_non_passa_dalla_sanita_razionale():
    """Cyc12 non è Fraction: la sanità DC non lo accusa a caso."""
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    from kirchhoff.domain.mna import solve_phasor
    assert verify(ir, solve_phasor(ir)) is None
