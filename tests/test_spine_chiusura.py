"""Difetti residui dello spine: domain, Request, attestazioni, eccezioni tipizzate, CI."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import importlib

import pytest

from kirchhoff.domain.exact import SingularSystemError, solve_linear
from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import Solved, renderer_supports, resolve

F = Fraction
PARTITORE = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n"


def _dc(requests=()):
    return IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        requests)


def _ac(requests=()):
    return IR(
        "1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        requests, F(314))


def test_domain_banana_con_circuiti_dc_non_e_solved():
    ir = IR(
        "1.0.0", "banana", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        ())
    esito = resolve(ir)
    assert not isinstance(esito, Solved)
    assert isinstance(esito, Refusal)
    assert esito.subject == "banana"
    assert esito.subject_kind == "operation"


def test_dc_request_voltage_e_solved():
    esito = resolve(_dc((Request("q1", "voltage", "R1"),)))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["voltage"] == F(10)


def test_dc_request_current_e_solved():
    esito = resolve(_dc((Request("q1", "current", "R1"),)))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["current"] == F(1)


def test_dc_request_time_constant_e_refusal():
    esito = resolve(_dc((Request("q1", "time_constant", "R1"),)))
    assert isinstance(esito, Refusal)
    assert esito.subject_kind == "request"
    assert esito.subject == "q1"
    assert "time_constant" in esito.diagnosis


def test_phasor_request_supportata_e_solved():
    esito = resolve(_ac((Request("q1", "voltage", "R1"),)))
    assert isinstance(esito, Solved)
    assert esito.solver == "phasor"


def test_quantity_non_supportata_e_refusal():
    esito = resolve(_ac((Request("q1", "final_value", "R1"),)))
    assert isinstance(esito, Refusal)
    assert esito.subject_kind == "request"


def test_solver_senza_la_quantity_richiesta_non_e_solved(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: {c.id: {"voltage": F(10)} for c in ir.components})
    esito = resolve(_dc((Request("q1", "current", "R1"),)))
    assert not isinstance(esito, Solved)
    assert isinstance(esito, Refusal)
    assert esito.subject == "q1"


def test_ac_non_attesta_bilancio_di_potenza():
    esito = resolve(_ac())
    assert isinstance(esito, Solved)
    assert "bilancio di potenza" not in esito.verifiche
    assert "identità di Tellegen" in esito.verifiche


def test_dc_attesta_bilancio_di_potenza():
    esito = resolve(_dc())
    assert isinstance(esito, Solved)
    assert "bilancio di potenza" in esito.verifiche


def test_tellegen_falso_in_ac_nomina_tellegen_non_la_potenza(monkeypatch):
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: F(1))
    esito = resolve(_ac())
    assert isinstance(esito, Refusal)
    assert "Tellegen" in esito.diagnosis
    assert "bilancio di potenza" not in esito.diagnosis


def test_singolarita_tipizzata_e_refusal(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(
        mna, "solve_dc",
        lambda ir: (_ for _ in ()).throw(SingularSystemError("sistema singolare alla colonna 0")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)


def test_valueerror_generico_solver_e_failure(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(ValueError("indice fuori scala")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"


def test_valueerror_con_testo_singolare_non_e_refusal(monkeypatch):
    """La classificazione non legge la frase. Solo SingularSystemError è Refusal."""
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(
        mna, "solve_dc",
        lambda ir: (_ for _ in ()).throw(ValueError("sistema singolare alla colonna 0")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"


def test_keyerror_solver_e_failure(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(KeyError("nodo")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "solver"


def test_zerodivisionerror_inatteso_e_failure(monkeypatch):
    import kirchhoff.domain.mna as mna
    monkeypatch.setattr(mna, "solve_dc", lambda ir: (_ for _ in ()).throw(ZeroDivisionError("x")))
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert "ZeroDivisionError" in esito.messaggio


def test_cli_non_stampa_non_risolto_sul_percorso_normale(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    f = tmp_path / "c.netlist"
    f.write_text(PARTITORE + "? voltage R2\n", encoding="utf-8")
    assert main([str(f)]) == 0
    fuori = capsys.readouterr()
    assert "non risolto" not in fuori.out + fuori.err
    assert "chiesto: voltage di R2" in fuori.out


def test_cli_request_non_supportata_e_rifiuto_non_solved(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    f = tmp_path / "c.netlist"
    f.write_text(PARTITORE + "? time_constant R1\n", encoding="utf-8")
    assert main([str(f)]) == 3
    assert "RIFIUTATO" in capsys.readouterr().err


def test_quantity_fuori_vocabolario_non_nasce():
    with pytest.raises(ValueError, match="quantity"):
        Request("q1", "impedance", "R1")  # type: ignore[arg-type]


def test_ci_esiste_e_invoca_i_test_reali():
    testo = Path(".github/workflows/test.yml").read_text(encoding="utf-8")
    assert "pytest" in testo
    assert "check_domain_coverage.py" in testo
    assert "3.12" in testo
    assert "kirchhoff-eval build" in testo
    assert testo.index("kirchhoff-eval build") < testo.index("run: pytest")


def test_solve_linear_solleva_singular_system_error():
    with pytest.raises(SingularSystemError, match="singolare"):
        solve_linear([[F(1), F(2)], [F(2), F(4)]], [F(1), F(2)])


def test_ac_valido_e_solved_non_failure():
    esito = resolve(_ac())
    assert isinstance(esito, Solved)
    assert not isinstance(esito, Failure)
    assert esito.solver == "phasor"


def test_ac_solved_puo_avere_svg_assente():
    esito = resolve(_ac())
    assert isinstance(esito, Solved)
    assert esito.svg is None
    assert not renderer_supports(_ac())


def test_dc_con_tipi_supportati_produce_svg():
    esito = resolve(_dc())
    assert isinstance(esito, Solved)
    assert esito.svg is not None and esito.svg.startswith("<svg")
    assert renderer_supports(_dc())


def test_multimaglia_senza_autolayout_resta_solved_numerico():
    esito = resolve(leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\nR3 a 0 330 ohm\n"))
    assert isinstance(esito, Solved)
    assert esito.svg is None
    assert esito.layout is None


def test_render_rotto_su_circuito_supportato_e_failure_anche_se_il_messaggio_sembra_un_simbolo(monkeypatch):
    """La distinzione è FORME, non il testo dell'eccezione."""
    spine = importlib.import_module("kirchhoff.pipeline.resolve")
    monkeypatch.setattr(
        spine, "render",
        lambda ir, lay: (_ for _ in ()).throw(
            ValueError("E1: nessun simbolo per un voltage_source_dc")))
    esito = resolve(_dc())
    assert isinstance(esito, Failure)
    assert esito.dove == "render"
