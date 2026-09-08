"""Percorso B come gate obbligatorio di certificazione DC."""
from __future__ import annotations

import ast
import importlib
from fractions import Fraction
from pathlib import Path

from kirchhoff.domain.independent_dc import TableauSingularError, solve_dc_tableau
from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.eval.generator import generate_case
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import (
    Solved,
    VERIFICHE,
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


def _spine():
    return importlib.import_module("kirchhoff.pipeline.resolve")


def _con(netlist: str, domande: tuple[tuple[str, str], ...]) -> IR:
    """La netlist condivisa piu' le domande esplicite del test."""
    return leggi(netlist + "".join(f"? {q} {t}\n" for q, t in domande))


def _accordo_su_chiesto(esito: Solved) -> None:
    """Ogni risposta sotto chiave originale concorda col percorso B."""
    b = solve_dc_tableau(esito.circuito)
    for cid, grandezze in esito.soluzione.items():
        if cid not in b:
            continue
        for q, v in grandezze.items():
            assert b[cid][q] == v


def test_vr_a_uguale_b():
    esito = resolve(_con(VR, (("voltage", "R1"), ("current", "R1"), ("current", "V1"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["voltage"] == F(10)
    assert esito.soluzione["R1"]["current"] == F(1)
    assert esito.soluzione["V1"]["current"] == F(-1)
    _accordo_su_chiesto(esito)


def test_partitore_a_uguale_b():
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R2"]["voltage"] == F(33, 4)
    _accordo_su_chiesto(esito)


def test_parallelo_a_uguale_b():
    esito = resolve(_con(PARALLELO, (("current", "R1"), ("current", "R2"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["current"] == F(3, 25)
    assert esito.soluzione["R2"]["current"] == F(1, 25)
    _accordo_su_chiesto(esito)


def test_ponte_a_uguale_b():
    esito = resolve(_con(PONTE, (("current", "Rg"), ("current", "R4"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["Rg"]["current"] != 0
    assert esito.soluzione["R4"]["current"] == F(87, 425)
    _accordo_su_chiesto(esito)


def test_generatore_di_corrente_a_uguale_b():
    esito = resolve(_con(CORRENTE, (
        ("voltage", "R1"), ("current", "R1"),
        ("current", "I1"), ("voltage", "I1"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["voltage"] == F(10)
    assert esito.soluzione["R1"]["current"] == F(2)
    assert esito.soluzione["I1"]["current"] == F(2)
    assert esito.soluzione["I1"]["voltage"] == F(-10)
    _accordo_su_chiesto(esito)


def test_vdc_idc_resistori_a_uguale_b():
    esito = resolve(_con(MISTO, (("voltage", "R2"), ("current", "R1"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R2"]["voltage"] == F(24, 5)
    assert esito.soluzione["R1"]["current"] == F(9, 5)
    _accordo_su_chiesto(esito)


def test_corrente_negativa_rispetto_all_orientamento():
    esito = resolve(_con(NEGATIVA, (
        ("voltage", "R1"), ("current", "R1"), ("current", "V1"))))
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["voltage"] == F(-10)
    assert esito.soluzione["R1"]["current"] == F(-1)
    assert esito.soluzione["V1"]["current"] == F(-1)
    _accordo_su_chiesto(esito)


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
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "percorso A" in esito.diagnosis
    assert "percorso B" in esito.diagnosis


def test_b_corrotto_produce_path_disagreement(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    vero = b.solve_dc_tableau

    def rotto(ir):
        sol = vero(ir)
        cid = next(iter(sol))
        sporco = dict(sol)
        ramo = dict(sporco[cid])
        ramo["current"] = ramo["current"] + F(1)
        sporco[cid] = ramo
        return sporco

    monkeypatch.setattr(b, "solve_dc_tableau", rotto)
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"


def test_bug_interno_b_e_failure(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    monkeypatch.setattr(
        b, "solve_dc_tableau",
        lambda ir: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Failure)
    assert esito.dove == "orchestrate"
    assert "boom" in esito.messaggio
    assert not isinstance(esito, Refusal)


def test_b_singolare_mentre_a_risolve_e_path_disagreement(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    monkeypatch.setattr(
        b, "solve_dc_tableau",
        lambda ir: (_ for _ in ()).throw(TableauSingularError("colonna 0")),
    )
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "singolare" in esito.diagnosis


def test_disaccordo_non_chiama_render(monkeypatch):
    import kirchhoff.domain.mna as mna

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
    monkeypatch.setattr(_spine(), "render", lambda ir, lay: chiamato.__setitem__("render", True) or "<svg/>")
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Refusal)
    assert chiamato["render"] is False


def test_ac_rifiuta_prima_di_verificare_e_senza_percorso_b(monkeypatch):
    import kirchhoff.domain.independent_dc as b

    chiamato = {"b": False}

    def boom(ir):
        chiamato["b"] = True
        raise AssertionError("Percorso B non deve girare in AC")

    monkeypatch.setattr(b, "solve_dc_tableau", boom)
    ir = IR(
        "1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
        (Component.of("E1", "voltage_source_ac", ("A", "0"), F(10), "E_1"),
         Component.of("R1", "resistor", ("A", "0"), F(10), "R_1")),
        (Request("q1", "voltage", "R1"),), F(314),
    )
    esito = resolve(ir)
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"
    assert chiamato["b"] is False


def test_dc_certificato_attesta_claim_e_sessione():
    esito = resolve(_con(VR, (("voltage", "R1"),)))
    assert isinstance(esito, Solved)
    assert esito.verifiche == VERIFICHE
    assert "Claim elettrico: VERIFIED" in esito.verifiche
    assert "Sessione backend: CLOSED" in esito.verifiche


def test_b_senza_un_componente_e_path_disagreement(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    def incompleto(ir):
        sol = solve_dc_tableau(ir)
        cid = next(iter(sol))
        return {k: v for k, v in sol.items() if k != cid}

    monkeypatch.setattr(b, "solve_dc_tableau", incompleto)
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"


def test_b_senza_una_grandezza_e_path_disagreement(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    def monco(ir):
        sol = solve_dc_tableau(ir)
        cid = next(iter(sol))
        out = {k: dict(v) for k, v in sol.items()}
        del out[cid]["current"]
        return out

    monkeypatch.setattr(b, "solve_dc_tableau", monco)
    esito = resolve(_con(PARTITORE, (("voltage", "R2"),)))
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
    esito = resolve(_con(VR, (("voltage", "R1"),)))
    assert isinstance(esito, Refusal)
    assert esito.cause == "path_disagreement"
    assert "voltage" in esito.diagnosis


def test_b_con_componente_in_piu_e_path_disagreement(monkeypatch):
    import kirchhoff.domain.truthfulness as b

    def extra(ir):
        sol = dict(solve_dc_tableau(ir))
        sol["ZX"] = {"voltage": F(0), "current": F(0)}
        return sol

    monkeypatch.setattr(b, "solve_dc_tableau", extra)
    esito = resolve(_con(VR, (("voltage", "R1"),)))
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

    cl = leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\nC1 a 0 1/1000 farad\n? voltage R1\n")
    esito = resolve(cl)
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"


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
        concorda = True
        for cid, grandezze in esito.soluzione.items():
            if cid not in b:
                continue
            for q, v in grandezze.items():
                if b[cid][q] != v:
                    concorda = False
        if not concorda:
            disaccordi += 1
            continue
        accordi += 1
        assert esito.verifiche == VERIFICHE
    assert accordi + disaccordi + rifiuti == n
    assert disaccordi == 0
    assert accordi == n
    assert rifiuti == 0
