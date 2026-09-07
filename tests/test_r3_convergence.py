"""R3: una sola radice applicativa canonica, misurata invece che ricordata.

La radice e' `run_proof_session` (`kirchhoff.pipeline.proof_run`): unica via
verso la chiusura di backend. `resolve` e' compatibilita': delega ogni
domanda alla radice e ne proietta le chiusure in `Solved`. Questi test
falliscono se un secondo motore (planner, solver, gate) ricompare in un
adattatore o se `resolve` smette di delegare.
"""
from __future__ import annotations

import ast
import importlib
from fractions import Fraction
from pathlib import Path

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.eval.generator import generate_case
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "src" / "kirchhoff"


def _albero(modulo: str) -> ast.AST:
    return ast.parse((SORGENTE / modulo).read_text(encoding="utf-8"))


def _moduli_kirchhoff_importati(modulo: str) -> set[str]:
    trovati: set[str] = set()
    for nodo in ast.walk(_albero(modulo)):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name == "kirchhoff" or alias.name.startswith("kirchhoff."):
                    trovati.add(alias.name)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            if nodo.module == "kirchhoff" or nodo.module.startswith("kirchhoff."):
                trovati.add(nodo.module)
    return trovati


def _spine():
    return importlib.import_module("kirchhoff.pipeline.resolve")


def test_la_radice_canonica_ha_un_solo_proprietario_produttivo():
    """Solo proof_run.py chiama orchestrazione, registro e compositore."""
    funzioni = {"orchestrate_didactic_run", "compose_proof_session", "componi_registro"}
    definitori = {
        "orchestrate_didactic_run": "domain/didactic/orchestrate.py",
        "compose_proof_session": "pipeline/proof_session.py",
        "componi_registro": "pipeline/state_registry.py",
    }
    chiamanti: dict[str, set[str]] = {}
    for percorso in sorted(SORGENTE.rglob("*.py")):
        albero = ast.parse(percorso.read_text(encoding="utf-8"))
        for nodo in ast.walk(albero):
            if not isinstance(nodo, ast.Call):
                continue
            nome = None
            if isinstance(nodo.func, ast.Name):
                nome = nodo.func.id
            elif isinstance(nodo.func, ast.Attribute):
                nome = nodo.func.attr
            if nome in funzioni:
                rel = percorso.relative_to(SORGENTE).as_posix()
                if rel != definitori[nome]:
                    chiamanti.setdefault(rel, set()).add(nome)
    assert chiamanti == {"pipeline/proof_run.py": funzioni}


def test_resolve_chiama_solo_la_radice_per_risolvere():
    """resolve.py non importa nessun modulo solutore o didattico."""
    importati = _moduli_kirchhoff_importati("pipeline/resolve.py")
    vietati = {m for m in importati if m.startswith((
        "kirchhoff.domain.mna",
        "kirchhoff.domain.independent_dc",
        "kirchhoff.domain.didactic",
        "kirchhoff.domain.truthfulness",
        "kirchhoff.domain.transform",
        "kirchhoff.domain.verify",
    ))}
    assert vietati == set()
    assert "kirchhoff.pipeline.proof_run" in importati


def test_resolve_non_nomina_selezione_del_solutore():
    """Niente dispatch, planner o gate nei nomi caricati da resolve.py."""
    vietati = {
        "mna", "solve_dc", "solve_phasor", "solve_dc_tableau",
        "pianifica", "orchestrate_didactic_run", "execute_plan",
        "truthfulness_gate", "certify_execution", "transform",
        "compose_proof_session", "componi_registro",
    }
    caricati = set()
    for nodo in ast.walk(_albero("pipeline/resolve.py")):
        if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Load):
            caricati.add(nodo.id)
        elif isinstance(nodo, ast.Attribute) and isinstance(nodo.ctx, ast.Load):
            caricati.add(nodo.attr)
    assert caricati & vietati == set()


def test_il_cli_usa_l_involucro_non_la_radice_nuda():
    """cli.py parla con resolve, non con solver, planner o gate."""
    importati = _moduli_kirchhoff_importati("pipeline/cli.py")
    assert "kirchhoff.pipeline.resolve" in importati
    vietati = {m for m in importati if m.startswith((
        "kirchhoff.domain.mna",
        "kirchhoff.domain.didactic",
        "kirchhoff.domain.truthfulness",
        "kirchhoff.pipeline.proof_run",
    ))}
    assert vietati == set()


def test_resolve_delega_il_refusal_per_identita(monkeypatch):
    """Un Refusal della radice attraversa l'involucro senza essere toccato."""
    involucro = importlib.import_module("kirchhoff.pipeline.resolve")
    from kirchhoff.pipeline.resolve import resolve
    rifiuto = Refusal("unsolvable", "q1", "request", "radice finta")
    monkeypatch.setattr(involucro, "run_proof_session", lambda *a, **k: rifiuto)
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2\n")
    assert resolve(ir) is rifiuto


def test_resolve_delega_il_failure_per_identita(monkeypatch):
    """Un Failure della radice attraversa l'involucro senza essere toccato."""
    involucro = importlib.import_module("kirchhoff.pipeline.resolve")
    from kirchhoff.pipeline.resolve import resolve
    guasto = Failure("orchestrate", "radice finta")
    monkeypatch.setattr(involucro, "run_proof_session", lambda *a, **k: guasto)
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2\n")
    assert resolve(ir) is guasto


def test_resolve_non_lascia_attraversare_eccezioni(monkeypatch):
    """Un'esplosione della radice diventa Failure nominato, mai traceback."""
    involucro = importlib.import_module("kirchhoff.pipeline.resolve")
    from kirchhoff.pipeline.resolve import resolve

    def boom(*a, **k):
        raise RuntimeError("radice rotta")

    monkeypatch.setattr(involucro, "run_proof_session", boom)
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2\n")
    esito = resolve(ir)
    assert isinstance(esito, Failure)
    assert esito.dove == "resolve"


def test_il_canone_d1_3_su_80_vive_sul_percorso_canonico():
    """3/80 A: la corrente di serie del partitore, chiaveata sulla domanda."""
    from kirchhoff.pipeline.resolve import Solved, resolve
    ir = leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? current R1\n")
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert esito.soluzione["R1"]["current"] == Fraction(3, 80)


def test_piu_domande_una_radice_per_domanda(monkeypatch):
    """Ogni domanda passa per la radice; le risposte restano esatte."""
    involucro = importlib.import_module("kirchhoff.pipeline.resolve")
    from kirchhoff.pipeline.resolve import Solved, resolve
    chiamate = []

    vero = involucro.run_proof_session

    def spia(ir, richiesta, **kwargs):
        chiamate.append(richiesta.id)
        return vero(ir, richiesta, **kwargs)

    monkeypatch.setattr(involucro, "run_proof_session", spia)
    ir = leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n"
        "? voltage R2\n? current R1\n")
    esito = resolve(ir)
    assert isinstance(esito, Solved)
    assert chiamate == ["q1", "q2"]
    assert esito.soluzione["R2"]["voltage"] == Fraction(33, 4)
    assert esito.soluzione["R1"]["current"] == Fraction(3, 80)


def test_fasore_e_controllate_rifiutano_sul_percorso_prodotto():
    """Ambito onesto: fuori dalla continua certificabile, Refusal."""
    from kirchhoff.pipeline.resolve import resolve
    fasore = IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
                (Component.of("E1", "voltage_source_ac", ("A", "0"),
                              Fraction(10), "E_1"),
                 Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1")),
                (Request("q1", "voltage", "R1"),), Fraction(314))
    esito = resolve(fasore)
    assert isinstance(esito, Refusal)
    controllata = IR("1.0.0", "dc", "generated", ("0", "A", "C"),
                     (Component.of("V1", "voltage_source_dc", ("A", "0"),
                                   Fraction(10), "V_1"),
                      Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1"),
                      Component.of("E1", "voltage_controlled_voltage_source",
                                   ("C", "0"), Fraction(2), "E_1",
                                   control_nodes=("A", "0")),
                      Component.of("R2", "resistor", ("C", "0"), Fraction(5), "R_2")),
                     (Request("qv", "voltage", "E1"),))
    esito = resolve(controllata)
    assert isinstance(esito, Refusal)
    assert esito.cause == "unsolvable"


def test_ir_senza_domande_e_rifiuto_non_mappa():
    """Senza domanda non c'e' nulla da certificare: Refusal, mai Solved."""
    from kirchhoff.pipeline.resolve import Solved, resolve
    esito = resolve(leggi("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n"))
    assert isinstance(esito, Refusal)
    assert not isinstance(esito, Solved)
    assert esito.cause == "unsolvable"


def test_generato_dc_resistive_certifica():
    """Il generatore eval emette dc_resistive: la radice lo riconosce."""
    from kirchhoff.pipeline.resolve import Solved, resolve
    ir, _atteso, _seq = generate_case(1, depth=3)
    assert ir.domain == "dc_resistive"
    esito = resolve(ir)
    assert isinstance(esito, Solved)
