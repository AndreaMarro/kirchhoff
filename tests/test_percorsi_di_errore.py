"""Copertura dei rami d'errore.

`domain/` e' puro: nessuna I/O, nessun orologio, nessuna casualita'. Non esiste
scusa per un ramo non coperto — se non e' raggiungibile da un test, non serve.
"""

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.mna import solve_dc
from kirchhoff.eval import metrics


def test_terminali_coincidenti_rifiutati():
    with pytest.raises(ValueError, match="terminali coincidenti"):
        Component.of("R1", "resistor", ("A", "A"), Fraction(10), "R_1")


def test_manca_nodo_di_riferimento():
    with pytest.raises(ValueError, match="nodo di riferimento"):
        IR("1.0.0", "dc_resistive", "generated", ("A", "B"),
           (Component.of("R1", "resistor", ("A", "B"), Fraction(10), "R_1"),), ())


def test_terminale_su_nodo_sconosciuto():
    with pytest.raises(ValueError, match="nodo sconosciuto"):
        IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
           (Component.of("R1", "resistor", ("A", "Z"), Fraction(10), "R_1"),), ())


def test_lookup_componente():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1"),), ())
    assert ir.component("R1").value.amount == Fraction(10)
    with pytest.raises(KeyError):
        ir.component("R9")


def test_generatore_flottante_non_a_massa():
    """Sorgente fra A e B, con B a massa via resistore: esercita il ramo `q in idx`."""
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A", "B"),
            (Component.of("E1", "voltage_source_dc", ("A", "B"), Fraction(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1"),
             Component.of("R2", "resistor", ("B", "0"), Fraction(10), "R_2")),
            (Request("q1", "current", "R1"),))
    sol = solve_dc(ir)
    assert sol["E1"]["voltage"] == Fraction(10)
    assert sol["R1"]["current"] == Fraction(1, 2)
    assert sol["R2"]["current"] == Fraction(-1, 2)


def test_sistema_singolare_rilevato():
    """Due generatori identici in parallelo: righe duplicate, matrice singolare."""
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(5), "E_1"),
             Component.of("E2", "voltage_source_dc", ("A", "0"), Fraction(5), "E_2"),
             Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1")),
            (Request("q1", "current", "R1"),))
    with pytest.raises(ValueError, match="singolare"):
        solve_dc(ir)


def test_solver_di_riferimento_rifiuta_l_irrisolvibile():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(5), "E_1"),
             Component.of("E2", "voltage_source_dc", ("A", "0"), Fraction(5), "E_2")),
            (Request("q1", "voltage", "E1"),))
    out = metrics.reference_solver(ir)
    assert out.published is False
    assert out.error_kind == "irrisolvibile"


def test_report_vuoto_non_divide_per_zero():
    r = metrics.Report()
    assert r.vsr == 0.0 and r.ser == 0.0 and r.qps == 0.0 and r.ttv_p90 == 0.0
    assert r.as_dict()["refusal_rate"] == 0.0


def test_report_conta_i_rifiuti_per_tipo():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(5), "E_1"),
             Component.of("E2", "voltage_source_dc", ("A", "0"), Fraction(5), "E_2")),
            (Request("q1", "voltage", "E1"),))

    class C:
        pass
    c = C(); c.ir = ir; c.expected = {}
    rep = metrics.run([c], metrics.reference_solver, "test")
    assert rep.published == 0
    assert rep.errors["irrisolvibile"] == 1
    assert rep.as_dict()["refusal_rate"] == 1.0


def test_generatore_con_primo_terminale_a_massa():
    """Sorgente orientata ('0','A'): esercita il ramo in cui `p` NON e' incognito."""
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("0", "A"), Fraction(6), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Fraction(12), "R_1")),
            (Request("q1", "current", "R1"),))
    sol = solve_dc(ir)
    # v(0) - v(A) = 6  ->  v(A) = -6
    assert sol["R1"]["voltage"] == Fraction(-6)
    assert sol["R1"]["current"] == Fraction(-1, 2)


# ---------------------------------------------------------------------------
# Criteri negativi. Un gate che nessun test ha mai visto fallire e' un gate di
# cui non sappiamo niente: l'aritmetica esatta rende irraggiungibili per
# costruzione certi rami, e li si raggiunge sostituendo la funzione sotto.
# ---------------------------------------------------------------------------

from kirchhoff.domain import mna as mna_mod
from kirchhoff.domain.exact import Cyc12
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.eval import generator_transient, reference_set


def test_verifica_segnala_un_componente_assente_dalla_soluzione():
    from kirchhoff.eval.generator import generate_case
    ir, expected, _ = generate_case(5)
    corrotto = {**expected, "R99": {"voltage": Fraction(1), "current": Fraction(1)}}
    problems = reference_set.verify_independently(ir, corrotto)
    assert any("assente nella soluzione nodale" in p for p in problems)


def test_le_leggi_di_kirchhoff_su_una_soluzione_falsa():
    ir = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(10), "E_1"),
             Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1")),
            (Request("q1", "current", "R1"),))
    falsa = {"E1": {"voltage": Fraction(10), "current": Fraction(3)},
             "R1": {"voltage": Fraction(10), "current": Fraction(1)}}
    problems = reference_set._leggi_di_kirchhoff(ir, falsa)
    assert any("KCL non nullo" in p for p in problems)
    assert any("bilancio di potenza non nullo" in p for p in problems)


def test_trifase_squilibrato_viene_segnalato():
    """Con un carico diverso su una fase le correnti non sommano piu' a zero."""
    ir = IR("1.0.0", "three_phase", "generated", ("0", "a", "b", "c"),
            (Component.of("Ea", "voltage_source_ac", ("a", "0"), Fraction(230), "E_a"),
             Component.of("Eb", "voltage_source_ac", ("b", "0"), Fraction(230), "E_b",
                       phase_steps=-4),
             Component.of("Ec", "voltage_source_ac", ("c", "0"), Fraction(230), "E_c",
                       phase_steps=4),
             Component.of("Ra", "resistor", ("a", "0"), Fraction(10), "R_a"),
             Component.of("Rb", "resistor", ("b", "0"), Fraction(10), "R_b"),
             Component.of("Rc", "resistor", ("c", "0"), Fraction(20), "R_c")),
            (Request("q1", "current", "Ra"),), omega=Fraction(314))
    sol = solve_phasor(ir)
    expected = {c.id: dict(sol[c.id]) for c in ir.components}
    problems = reference_set.verify_independently(ir, expected)
    assert any("non sommano a zero" in p for p in problems)


def _transitorio_corrotto(seed: int, cid: str, **override):
    ir, expected, _ = generator_transient.generate_case(seed)
    corrotto = {**expected, cid: {**expected[cid], **override}}
    return reference_set.verify_independently(ir, corrotto)


def test_valore_iniziale_sbagliato_rilevato():
    problems = _transitorio_corrotto(0, "R1", initial_value=Fraction(0))
    assert any("initial_value" in p for p in problems)


def test_costante_di_tempo_non_positiva_rilevata():
    problems = _transitorio_corrotto(0, "C1", time_constant=Fraction(-1))
    assert any("non positiva" in p for p in problems)


def test_costante_di_tempo_che_non_e_una_frequenza_naturale():
    problems = _transitorio_corrotto(0, "C1", time_constant=Fraction(1))
    assert any("non e' una frequenza naturale" in p for p in problems)


def test_radice_non_negativa_rilevata():
    problems = _transitorio_corrotto(2, "C1", root_1=Fraction(1))
    assert any("radice non negativa" in p for p in problems)


def test_radice_che_non_annulla_la_matrice():
    problems = _transitorio_corrotto(2, "C1", root_1=Fraction(-7))
    assert any("non annulla la matrice MNA" in p for p in problems)


def test_radici_coincidenti_rilevate():
    ir, expected, _ = generator_transient.generate_case(2)
    s1 = expected["C1"]["root_1"]
    corrotto = {**expected, "C1": {**expected["C1"], "root_2": s1}}
    problems = reference_set.verify_independently(ir, corrotto)
    assert any("radici coincidenti" in p for p in problems)


def test_caso_degenere_scartato_e_contato(monkeypatch):
    """Una risonanza esatta si scarta e si conta: non si aggiusta il sorteggio."""
    chiamate = {"n": 0}

    def risonante(seed, depth):
        chiamate["n"] += 1
        if chiamate["n"] <= 2:
            raise ZeroDivisionError("impedenza nulla in serie")
        return generator_transient.generate_case(seed)

    monkeypatch.setitem(reference_set._GENERATORS, "transient", risonante)
    accepted, rejected = reference_set._build_class("transient", "tr", 1, 10, 3)
    assert len(accepted) == 1
    assert len(rejected) == 2
    assert all("caso degenere" in r["problems"][0] for r in rejected)


def test_caso_non_verificato_scartato(monkeypatch):
    reale = reference_set.verify_independently
    stato = {"n": 0}

    def a_volte_rotto(ir, expected):
        stato["n"] += 1
        return ["disaccordo simulato"] if stato["n"] == 1 else reale(ir, expected)

    monkeypatch.setattr(reference_set, "verify_independently", a_volte_rotto)
    accepted, rejected = reference_set._build_class("transient", "tr", 1, 20, 3)
    assert len(accepted) == 1
    assert rejected == [{"seed": 20, "problems": ["disaccordo simulato"]}]


def test_generazione_che_non_converge_si_ferma(monkeypatch):
    def sempre_degenere(seed, depth):
        raise ZeroDivisionError("sempre")

    monkeypatch.setitem(reference_set._GENERATORS, "transient", sempre_degenere)
    with pytest.raises(RuntimeError, match="non converge"):
        reference_set._build_class("transient", "tr", 1, 30, 3)


def test_rifiuto_quando_la_grandezza_richiesta_non_e_calcolabile():
    """La costante di tempo nessun risolutore la produce ancora: si rifiuta, non si inventa."""
    ir = IR("1.0.0", "transient", "generated", ("0", "A", "B"),
            (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(12), "E_1"),
             Component.of("R1", "resistor", ("A", "B"), Fraction(2), "R_1"),
             Component.of("C1", "capacitor", ("B", "0"), Fraction(3), "C_1")),
            (Request("q1", "time_constant", "C1"),))
    out = metrics.reference_solver(ir)
    assert out.published is False
    assert out.error_kind == "grandezza_richiesta"


def test_il_gate_non_pubblica_quando_un_controllo_fallisce(monkeypatch):
    """NFR-11: se un controllo dei cinque fallisce, non si pubblica. Nessun bypass."""
    monkeypatch.setattr(mna_mod, "power_balance", lambda ir, sol: Fraction(1))
    stazionario = IR("1.0.0", "dc_resistive", "generated", ("0", "A"),
                     (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(10), "E_1"),
                      Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1")),
                     (Request("q1", "current", "R1"),))
    assert metrics.reference_solver(stazionario).published is False

    transitorio = IR("1.0.0", "transient", "generated", ("0", "A", "B"),
                     (Component.of("E1", "voltage_source_dc", ("A", "0"), Fraction(12), "E_1"),
                      Component.of("R1", "resistor", ("A", "B"), Fraction(2), "R_1"),
                      Component.of("C1", "capacitor", ("B", "0"), Fraction(3), "C_1")),
                     (Request("q1", "final_value", "C1"),))
    out = metrics.reference_solver(transitorio)
    assert out.published is False
    assert out.error_kind == "irrisolvibile"


def test_valore_ciclotomico_non_degrada_mai_a_virgola_mobile():
    z = Cyc12.of(Fraction(1, 3))
    assert all(isinstance(k, Fraction) for k in z.c)
    assert (z * Cyc12.of(3)).c[0] == Fraction(1)


def test_un_float_non_entra_nel_campo_ciclotomico():
    """`Fraction(0.1)` non fallisce: restituisce rumore binario. La porta si chiude prima."""
    with pytest.raises(TypeError, match="non esatto"):
        Cyc12.of(0.1)
    with pytest.raises(TypeError, match="non esatto"):
        Cyc12.of(1) * 0.1          # anche dalla porta di servizio dell'aritmetica


def test_un_float_non_entra_in_un_componente():
    with pytest.raises(TypeError, match="serve una Fraction"):
        Component.of("R1", "resistor", ("A", "0"), 0.1, "R_1")


def test_una_pulsazione_in_virgola_mobile_e_rifiutata():
    with pytest.raises(TypeError, match="serve una Fraction"):
        IR("1.0.0", "ac_sinusoidal", "generated", ("0", "A"),
           (Component.of("R1", "resistor", ("A", "0"), Fraction(10), "R_1"),),
           (Request("q1", "current", "R1"),), 314.0)


def test_il_campo_ciclotomico_resta_hashabile():
    assert len({Cyc12.of(1), Cyc12.of(1), Cyc12.of(2)}) == 2


def test_transitorio_segnala_un_componente_assente():
    ir, expected, _ = generator_transient.generate_case(0)
    corrotto = {**expected, "C99": {"initial_value": Fraction(0)}}
    problems = reference_set.verify_independently(ir, corrotto)
    assert any("assente nella soluzione nodale" in p for p in problems)
