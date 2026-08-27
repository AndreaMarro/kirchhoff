"""Lo spine: Refusal di dominio contro Failure di stadio, misurati in difetto."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.exact import SingularSystemError
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
    assert esito.verifiche == (
        "legge dei nodi", "legge delle maglie",
        "bilancio di potenza", "sanità fisica")


def test_validate_precede_il_solutore():
    esito = resolve(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nR2 a z 20 ohm\n"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "topology"
    assert esito.subject == "z"


def test_un_condensatore_in_netlist_dc_e_rifiuto():
    esito = resolve(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nC1 a 0 1/1000 farad\n"))
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert esito.subject == "C1"


def test_due_maglie_si_certificano_senza_disegno():
    esito = resolve(leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\nR3 a 0 330 ohm\n"))
    assert isinstance(esito, Solved)
    assert esito.svg is None and esito.layout is None
    assert esito.soluzione["R1"]["current"] != 0


def test_due_generatori_in_parallelo_sono_rifiuto_di_validate():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), F(5), "E_1"),
             Component.of("E2", "voltage_source_dc", ("A", "0"), F(5), "E_2"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            ())
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.cause == "topology"


def test_il_fasore_e_sul_percorso_pubblico():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.solver == "phasor"
    assert "sanità fisica" not in esito.verifiche
    assert "legge dei nodi" in esito.verifiche
    assert "identità di Tellegen" in esito.verifiche
    assert "bilancio di potenza" not in esito.verifiche


def test_il_transitorio_si_rifiuta():
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


def test_failure_e_un_tipo_altro_da_refusal():
    assert not issubclass(Failure, Refusal)
    assert not issubclass(Refusal, Failure)
    assert not issubclass(Failure, Exception)


def test_vac_senza_omega_non_nasce_come_ir():
    with pytest.raises(ValueError, match="pulsazione"):
        IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
           (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
            Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
           (), F(0))


def test_sinusoidale_reattivo_senza_omega_arriva_al_dispatch():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("R1", "resistor", ("A", "0"), F(10), "R_1"),
             Component.of("C1", "capacitor", ("A", "0"), F(1, 1000), "C_1")),
            (), F(0))
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert "pulsazione" in esito.diagnosis


def test_fasore_con_generatore_dc_si_rifiuta():
    ir = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.subject == "E1"
    assert "fasoriale" in esito.diagnosis


def test_un_tipo_senza_percorso_si_rifiuta():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
            (), F(314))
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.subject == "E1"
    assert "nessun percorso" in esito.diagnosis


def test_keyerror_del_solver_e_failure(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(KeyError("nodo fantasma")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"
    assert "KeyError" in esito.messaggio


def test_valueerror_generico_del_solver_e_failure(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(ValueError("indice fuori scala")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"


def test_singolare_dichiarata_dal_kernel_e_rifiuto(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(
        mna, "solve_dc",
        lambda ir: (_ for _ in ()).throw(SingularSystemError("sistema singolare alla colonna 0")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert "singolare" in esito.diagnosis


def test_eccezione_inattesa_del_solver_nomina_lo_stadio(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(RuntimeError("heap")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"
    assert "RuntimeError" in esito.messaggio


def test_validate_che_esplode_nomina_validate(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "validate", lambda ir: (_ for _ in ()).throw(RuntimeError("disco")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "validate"


def test_verify_che_esplode_nomina_verify(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "verify", lambda ir, sol: (_ for _ in ()).throw(RuntimeError("residuo rotto")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "verify"


def test_render_che_esplode_con_layout_valido_e_failure(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "render", lambda ir, lay: (_ for _ in ()).throw(ValueError("filo attraverso un nodo")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "render"


def test_validate_che_restituisce_altro_e_failure(monkeypatch):
    import kirchhoff.pipeline.resolve as spine
    monkeypatch.setattr(spine, "validate", lambda ir: "boh")
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "validate"


def test_risolvi_e_lo_stesso_ingresso():
    from kirchhoff.pipeline.resolve import risolvi
    a, b = resolve(leggi(PARTITORE)), risolvi(leggi(PARTITORE))
    assert type(a) is type(b) and a.soluzione == b.soluzione
