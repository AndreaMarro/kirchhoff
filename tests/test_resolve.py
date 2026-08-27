"""Lo spine applicativo: validate → dispatch → solve → verify → publish."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, resolve

F = Fraction

PARTITORE = """
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? voltage R2
"""


def test_il_partitore_passa_tutto_lo_spine():
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Solved)
    assert esito.solver == "dc"
    assert esito.soluzione["R2"]["voltage"] == F(33, 4)
    assert esito.svg is not None and esito.svg.startswith("<svg")
    assert "legge dei nodi" in esito.verifiche
    assert "legge delle maglie" in esito.verifiche


def test_validate_precede_il_solutore():
    esito = resolve(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nR2 a z 20 ohm\n"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "topology"
    assert esito.subject == "z"


def test_un_condensatore_in_netlist_dc_non_esplode():
    esito = resolve(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nC1 a 0 1/1000 farad\n"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert esito.subject == "C1"
    assert "continua" in esito.diagnosis


def test_un_induttore_stessa_sorte():
    esito = resolve(leggi("V1 a 0 12 volt\nL1 a 0 1/100 henry\n"))
    assert isinstance(esito, Refusal)
    assert esito.subject == "L1"


def test_due_maglie_si_risolvono_senza_disegno():
    esito = resolve(leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\nR3 a 0 330 ohm\n"))
    assert isinstance(esito, Solved)
    assert esito.svg is None and esito.layout is None
    assert esito.soluzione["R1"]["current"] != 0


def test_un_sistema_singolare_e_rifiuto_non_eccezione():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), F(5), "E_1"),
             Component.of("E2", "voltage_source_dc", ("A", "0"), F(5), "E_2"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            ())
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.cause in ("topology", "unsolvable")


def test_il_fasore_e_sul_percorso_pubblico():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.solver == "phasor"
    assert esito.soluzione["R1"]["voltage"] == esito.soluzione["E1"]["voltage"]


def test_il_transitorio_si_rifiuta_non_si_certifica_a_meta():
    ir = IR("1.0.0", "transient", "generated", ("0", "A", "B"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), F(12), "E_1"),
             Component.of("R1", "resistor", ("A", "B"), F(2), "R_1"),
             Component.of("C1", "capacitor", ("B", "0"), F(3), "C_1")),
            ())
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert "transitorio" in esito.diagnosis


def test_kcl_falso_rifiuta_con_residual(monkeypatch):
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {"a": F(3, 7)})
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert "3/7" in esito.diagnosis


def test_potenza_falsa_rifiuta_con_residual(monkeypatch):
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(1, 9))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual"
    assert "1/9" in esito.diagnosis


def test_passivo_che_eroga_e_sanity():
    from kirchhoff.domain.verify import verify
    ir = leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n")
    esito = verify(ir, {"V1": {"voltage": F(9), "current": F(3)},
                        "R1": {"voltage": F(9), "current": F(-3)}})
    assert isinstance(esito, Refusal)
    assert esito.cause == "sanity" and esito.subject == "R1"


def test_failure_e_un_tipo_altro_da_refusal():
    assert not issubclass(Failure, Refusal)
    assert not issubclass(Refusal, Failure)
    assert not issubclass(Failure, Exception)
    f = Failure("resolve", "boom")
    assert "resolve" in str(f) and "boom" in str(f)


def test_failure_si_difende():
    with pytest.raises(ValueError, match="senza stadio"):
        Failure("", "x")
    with pytest.raises(ValueError, match="senza messaggio"):
        Failure("resolve", "")


def test_fasore_senza_omega_si_rifiuta():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(0))
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert "pulsazione" in esito.diagnosis


def test_fasore_con_generatore_dc_si_rifiuta():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.subject == "E1" and "fasoriale" in esito.diagnosis


def test_un_tipo_senza_percorso_si_rifiuta():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            ())
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.subject == "E1" and "nessun percorso" in esito.diagnosis


def test_il_solutore_che_solleva_diventa_rifiuto(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(ValueError("matrice singolare")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable" and "singolare" in esito.diagnosis


def test_un_guasto_imprevisto_e_failure_non_eccezione(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "validate", lambda ir: (_ for _ in ()).throw(RuntimeError("il disco ha mentito")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "resolve" and "RuntimeError" in esito.messaggio


def test_validate_che_restituisce_altro_e_failure(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "validate", lambda ir: "boh")
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure) and esito.dove == "validate"


def test_risolvi_e_lo_stesso_ingresso():
    from kirchhoff.pipeline.resolve import risolvi
    a, b = resolve(leggi(PARTITORE)), risolvi(leggi(PARTITORE))
    assert type(a) is type(b) and a.soluzione == b.soluzione
