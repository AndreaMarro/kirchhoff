"""Il prodotto di Ohm dichiarato distingue operando errato e aritmetica."""
from hashlib import sha256

import pytest

from kirchhoff.domain.student_trace import StudentStep, StudentTrace, diagnose
from kirchhoff.pipeline.netlist import leggi


NETLIST = "V1 a 0 12 volt\nR1 a b 1000 ohm\nR2 b 0 2000 ohm\n? voltage R2"


def check(*steps, netlist=NETLIST):
    trace = StudentTrace(sha256(netlist.encode()).hexdigest(), steps)
    return diagnose(leggi(netlist), trace, netlist)


def ohm(resistance="R2", value="8", target="R2", reading="clear"):
    return StudentStep("V_R2 = I_R2 * R_usata", "ohm-tensione", target, resistance, value, reading)


def test_prodotto_di_ohm_sullo_stesso_resistore_e_valido():
    assert check(ohm())["outcome"] == "valid_so_far"


def test_ohm_non_sostituisce_il_circuito_di_lavoro_per_una_riduzione_successiva():
    reduction = StudentStep("R1 + R2 = 3000 ohm", "serie", "R1", "R2", "3000")
    assert check(ohm(), reduction)["outcome"] == "valid_so_far"


def test_r1_al_posto_di_r2_e_un_errore_di_riferimento_dopo_la_corrente_corretta():
    current = StudentStep("I_R2 = 1/250 A", "corrente", "R2", "", "1/250")
    result = check(current, ohm("R1", "4"))
    assert (result["outcome"], result["step"], result["category"], result["focus"]) == (
        "first_invalid", 2, "reference", ["R2", "R1"])
    assert "1000" in result["message"] and "2000" in result["message"]
    assert "4 V" in result["message"] and "8 V" in result["message"]


def test_riferimento_corretto_con_prodotto_errato_e_un_errore_aritmetico():
    result = check(ohm(value="4"))
    assert (result["outcome"], result["category"]) == ("first_invalid", "algebra")


def test_resistenza_di_valore_identico_non_impone_un_unico_metodo():
    netlist = NETLIST.replace("2000 ohm", "1000 ohm")
    assert check(ohm("R1", "6"), netlist=netlist)["outcome"] == "valid_so_far"


def test_con_corrente_nulla_un_altro_fattore_non_prova_un_errore():
    netlist = NETLIST.replace("12 volt", "0 volt")
    result = check(ohm("R1", "0"), netlist=netlist)
    assert (result["outcome"], result["category"]) == ("not_assessable", "simplification")


@pytest.mark.parametrize("step,category", [
    (ohm("RX"), "identifier"),
    (ohm(target="RX"), "identifier"),
    (ohm("V1"), "model"),
    (ohm(target="V1"), "model"),
    (ohm(value=None), "transcription"),
    (ohm(value="otto"), "transcription"),
    (ohm(value="1/0"), "transcription"),
    (ohm(reading="unreadable"), "unreadable"),
])
def test_una_dichiarazione_non_interpretabile_non_e_accusata(step, category):
    result = check(step)
    assert (result["outcome"], result["category"]) == ("not_assessable", category)


def test_ohm_non_accusa_se_i_due_percorsi_indipendenti_non_concordano(monkeypatch):
    import kirchhoff.domain.student_trace as module
    monkeypatch.setattr(module, "_verified_dc_observables", lambda _: None)
    result = check(ohm("R1", "4"))
    assert (result["outcome"], result["category"]) == ("not_assessable", "proof")


def test_payload_ohm_conserva_i_due_riferimenti_fino_alla_diagnosi():
    from kirchhoff.pipeline.student_trace import diagnose_payload
    result = diagnose_payload(NETLIST, {
        "schema": "student-trace.v1",
        "circuit_fingerprint": sha256(NETLIST.encode()).hexdigest(),
        "steps": [{"transcription": "V_R2 = I_R2 * R1 = 4 V", "operation": "ohm-tensione",
                   "first": "R2", "second": "R1", "claimed_value": "4", "reading": "clear"}],
    })
    assert (result["outcome"], result["category"], result["focus"]) == (
        "first_invalid", "reference", ["R2", "R1"])
