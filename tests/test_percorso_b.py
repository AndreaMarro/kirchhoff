"""Percorso B come gate obbligatorio di certificazione DC."""
from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

from kirchhoff.domain.independent_dc import TableauSingularError, solve_dc_tableau
from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.eval.generator import generate_case
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import (
    ATTESTAZIONE_PERCORSI,
    Solved,
    resolve,
)

F = Fraction

VR = "V1 a 0 10 volt\nR1 a 0 10 ohm\n"
PARTITORE = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n"
PARALLELO = "V1 b 0 12 volt\nR1 b 0 100 ohm\nR2 b 0 300 ohm\n"
PONTE = """
V1 c 0 12 volt
R1 c a 10 ohm
R2 c b 20 ohm
R3 a 0 30 ohm
R4 b 0 40 ohm
Rg a b 50 ohm
"""
CORRENTE = "I1 0 a 2 ampere\nR1 a 0 5 ohm\n"
MISTO = """
V1 a 0 12 volt
R1 a b 4 ohm
I1 b 0 1 ampere
R2 b 0 6 ohm
"""
NEGATIVA = "V1 a 0 10 volt\nR1 0 a 10 ohm\n"


def test_vr_a_uguale_b():
    esito = resolve(leggi(VR))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione
    assert esito.soluzione["R1"]["voltage"] == F(10)
    assert esito.soluzione["R1"]["current"] == F(1)
    assert esito.soluzione["V1"]["current"] == F(-1)


def test_partitore_a_uguale_b():
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione
    assert esito.soluzione["R2"]["voltage"] == F(33, 4)


def test_parallelo_a_uguale_b():
    esito = resolve(leggi(PARALLELO))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione
    assert esito.soluzione["R1"]["current"] == F(3, 25)
    assert esito.soluzione["R2"]["current"] == F(1, 25)


def test_ponte_a_uguale_b():
    esito = resolve(leggi(PONTE))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione
    assert esito.soluzione["Rg"]["current"] != 0


def test_generatore_di_corrente_a_uguale_b():
    esito = resolve(leggi(CORRENTE))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione
    assert esito.soluzione["R1"]["voltage"] == F(10)
    assert esito.soluzione["R1"]["current"] == F(2)
    assert esito.soluzione["I1"]["current"] == F(2)
    assert esito.soluzione["I1"]["voltage"] == F(-10)


def test_vdc_idc_resistori_a_uguale_b():
    esito = resolve(leggi(MISTO))
    assert isinstance(esito, Solved)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione


def test_corrente_negativa_rispetto_all_orientamento():
    esito = resolve(leggi(NEGATIVA))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["voltage"] == F(-10)
    assert esito.soluzione["R1"]["current"] == F(-1)
    assert esito.soluzione["V1"]["current"] == F(-1)
    assert solve_dc_tableau(esito.circuito) == esito.soluzione


def test_ordine_componenti_non_cambia_la_soluzione_b():
    ir = leggi(PONTE)
    sol = solve_dc_tableau(ir)
    permutato = IR(
        ir.ir_version, ir.domain, ir.source_kind, ir.nodes,
        tuple(reversed(ir.components)), ir.requests, ir.omega,
    )
    sol_p = solve_dc_tableau(permutato)
    assert sol == sol_p


def test_a_corrotto_produce_path_disagreement(monkeypatch):
    import kirchhoff.domain.mna as mna

    vero = mna.solve_dc

    def rotto(ir):
        sol = vero(ir)
        cid = next(iter(sol))
        sporco = dict(sol)
        ramo = dict(sporco[cid])
        ramo["voltage"] = ramo["voltage"] + F(1)
        sporco[cid] = ramo
        return sporco

    monkeypatch.setattr(mna, "solve_dc", rotto)
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "percorso A" in esito.diagnosis
    assert "percorso B" in esito.diagnosis


def test_b_corrotto_produce_path_disagreement(monkeypatch):
    import kirchhoff.domain.independent_dc as b
    import kirchhoff.pipeline.resolve as spine

    vero = b.solve_dc_tableau

    def rotto(ir):
        sol = vero(ir)
        cid = next(iter(sol))
        sporco = dict(sol)
        ramo = dict(sporco[cid])
        ramo["current"] = ramo["current"] + F(1)
        sporco[cid] = ramo
        return sporco

    monkeypatch.setattr(spine, "solve_dc_tableau", rotto)
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"


def test_bug_interno_b_e_failure(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    monkeypatch.setattr(
        spine, "solve_dc_tableau",
        lambda ir: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Failure)
    assert esito.dove == "verify"
    assert "RuntimeError" in esito.messaggio
    assert not isinstance(esito, Refusal)


def test_b_singolare_mentre_a_risolve_e_path_disagreement(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    monkeypatch.setattr(
        spine, "solve_dc_tableau",
        lambda ir: (_ for _ in ()).throw(TableauSingularError("colonna 0")),
    )
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "singolare" in esito.diagnosis


def test_disaccordo_non_chiama_render(monkeypatch):
    import kirchhoff.domain.mna as mna
    import kirchhoff.pipeline.resolve as spine

    chiamato = {"render": False}
    vero = mna.solve_dc

    def rotto(ir):
        sol = vero(ir)
        cid = next(iter(sol))
        sporco = dict(sol)
        ramo = dict(sporco[cid])
        ramo["voltage"] = ramo["voltage"] + F(7)
        sporco[cid] = ramo
        return sporco

    monkeypatch.setattr(mna, "solve_dc", rotto)
    monkeypatch.setattr(spine, "render", lambda ir, lay: chiamato.__setitem__("render", True) or "<svg/>")
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert chiamato["render"] is False


def test_ac_non_invoca_b_e_non_attesta_accordo(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    chiamato = {"b": False}

    def boom(ir):
        chiamato["b"] = True
        raise AssertionError("Percorso B non deve girare in AC")

    monkeypatch.setattr(spine, "solve_dc_tableau", boom)
    ir = IR(
        "1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        (), F(314),
    )
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.solver == "phasor"
    assert esito.svg is None
    assert chiamato["b"] is False
    assert ATTESTAZIONE_PERCORSI not in esito.verifiche


def test_dc_solved_attesta_accordo_percorsi():
    esito = resolve(leggi(VR))
    assert isinstance(esito, Solved)
    assert ATTESTAZIONE_PERCORSI in esito.verifiche


def test_b_senza_un_componente_e_path_disagreement(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    def incompleto(ir):
        sol = solve_dc_tableau(ir)
        cid = next(iter(sol))
        return {k: v for k, v in sol.items() if k != cid}

    monkeypatch.setattr(spine, "solve_dc_tableau", incompleto)
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"


def test_b_senza_una_grandezza_e_path_disagreement(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    def monco(ir):
        sol = solve_dc_tableau(ir)
        cid = next(iter(sol))
        out = {k: dict(v) for k, v in sol.items()}
        del out[cid]["current"]
        return out

    monkeypatch.setattr(spine, "solve_dc_tableau", monco)
    esito = resolve(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "current" in esito.diagnosis


def test_a_senza_una_grandezza_e_path_disagreement(monkeypatch):
    import kirchhoff.domain.mna as mna

    vero = mna.solve_dc

    def monco(ir):
        sol = vero(ir)
        cid = next(iter(sol))
        out = {k: dict(v) for k, v in sol.items()}
        del out[cid]["voltage"]
        return out

    monkeypatch.setattr(mna, "solve_dc", monco)
    esito = resolve(leggi(VR))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "voltage" in esito.diagnosis


def test_b_con_componente_in_piu_e_path_disagreement(monkeypatch):
    import kirchhoff.pipeline.resolve as spine

    def extra(ir):
        sol = dict(solve_dc_tableau(ir))
        sol["ZX"] = {"voltage": F(0), "current": F(0)}
        return sol

    monkeypatch.setattr(spine, "solve_dc_tableau", extra)
    esito = resolve(leggi(VR))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert esito.subject == "ZX"


def test_refusal_esistenti_invariati():
    banana = IR(
        "1.0.0", "banana", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        (),
    )
    assert isinstance(resolve(banana), Refusal)
    assert resolve(banana).cause == "unsolvable"

    req = IR(
        "1.0.0", "dc", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        (Request("q1", "time_constant", "R1"),),
    )
    esito = resolve(req)
    assert isinstance(esito, Refusal)
    assert esito.subject_kind == "request"

    trans = IR(
        "1.0.0", "transient", "generated", ("0", "A", "B"),
        (Component.of("E1", "voltage_source_dc", ("A", "0"), F(12), "E_1"),
         Component.of("R1", "resistor", ("A", "B"), F(2), "R_1"),
         Component.of("C1", "capacitor", ("B", "0"), F(3), "C_1")),
        (),
    )
    assert resolve(trans).cause == "unsolvable"

    cl = leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nC1 a 0 1/1000 farad\n")
    esito = resolve(cl)
    assert isinstance(esito, Refusal)
    assert esito.subject == "C1"


def test_modulo_b_non_importa_mna_ne_il_kernel_di_a():
    testo = Path("src/kirchhoff/domain/independent_dc.py").read_text(encoding="utf-8")
    albero = ast.parse(testo)
    vietati = {
        "kirchhoff.domain.mna",
        "kirchhoff.domain.verify",
        "kirchhoff.domain.exact",
    }
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                assert alias.name not in vietati
                assert not alias.name.startswith("kirchhoff.domain.mna")
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            assert nodo.module not in vietati
            assert "mna" not in nodo.module
            assert nodo.module != "kirchhoff.domain.exact"
            for alias in nodo.names:
                assert alias.name not in {
                    "solve_dc", "_assemble", "solve_linear",
                    "kvl_residuals", "kcl_residuals",
                }
    assert "solve_linear(" not in testo
    assert "mna.solve_dc" not in testo
    assert "._assemble" not in testo
    assert "kvl_residuals" not in testo
    assert "kcl_residuals" not in testo


def test_corpus_generato_dc_concorde():
    n = 30
    accordi = 0
    disaccordi = 0
    rifiuti = 0
    for seed in range(1, n + 1):
        ir, _atteso, _seq = generate_case(seed, depth=3)
        esito = resolve(ir)
        if isinstance(esito, Refusal):
            rifiuti += 1
            continue
        assert isinstance(esito, Solved), esito
        b = solve_dc_tableau(ir)
        if b != esito.soluzione:
            disaccordi += 1
            continue
        accordi += 1
        assert ATTESTAZIONE_PERCORSI in esito.verifiche
    assert accordi + disaccordi + rifiuti == n
    assert disaccordi == 0
    assert accordi == n
    assert rifiuti == 0
