"""Invarianti di catalogo sul corpus visibile del Proof Workbench.

Livello corpus, non livello vista: qui si controlla che l'insieme degli
esercizi versionati in `web/public/sessions/` sia coerente — identificatori
unici, titoli presenti, domande valide, indice allineato ai file, nessun
orfano, nessuna promessa di «Product Verified», chiusure con risposta ed
evidenza, rifiuti senza risposta. La validazione profonda della singola
vista resta di `StudentSessionView` e del drift test in
`test_workbench_generation.py`, che qui non si duplicano.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from kirchhoff.domain.ir.schema import QUANTITIES

RADICE = Path(__file__).resolve().parent.parent
SESSIONI = RADICE / "web" / "public" / "sessions"


def _indice() -> list[dict]:
    return json.loads((SESSIONI / "index.json").read_text(encoding="utf-8"))


def _viste() -> dict[str, dict]:
    viste = {}
    for sorgente in sorted(SESSIONI.glob("*.json")):
        if sorgente.name == "index.json":
            continue
        viste[sorgente.stem] = json.loads(sorgente.read_text(encoding="utf-8"))
    return viste


def test_gli_identificatori_sono_unici_e_i_titoli_non_vuoti():
    indice = _indice()
    identificatori = [voce["id"] for voce in indice]
    assert len(set(identificatori)) == len(identificatori)
    for voce in indice:
        assert voce["id"], "esercizio senza identificatore"
        assert voce["titolo"].strip(), f"{voce['id']}: titolo vuoto"


def test_le_domande_usano_il_vocabolario_chiuso():
    for voce in _indice():
        quantita = voce["domanda"]["quantity"]
        assert quantita in QUANTITIES, (
            f"{voce['id']}: quantity {quantita!r} fuori dal vocabolario")
        assert voce["domanda"]["target"].strip(), (
            f"{voce['id']}: domanda senza bersaglio")


def test_indice_e_file_versionati_si_corrispondono_senza_orfani():
    indice = _indice()
    viste = _viste()
    da_indice = {voce["id"] for voce in indice}
    assert da_indice == set(viste), (
        f"indice↔file disallineati: "
        f"solo-indice={sorted(da_indice - set(viste))} "
        f"orfani={sorted(set(viste) - da_indice)}")
    for voce in indice:
        vista = viste[voce["id"]]
        assert vista["outcome"] == voce["outcome"], (
            f"{voce['id']}: esito {vista['outcome']!r} contro indice {voce['outcome']!r}")
        assert vista["question"]["quantity"] == voce["domanda"]["quantity"]
        assert vista["question"]["target"] == voce["domanda"]["target"]


def test_le_chiusure_hanno_risposta_esatta_ed_evidenza():
    for ident, vista in _viste().items():
        if vista["outcome"] != "closed":
            continue
        risposta = vista["answer"]
        assert risposta is not None, f"{ident}: chiusura senza risposta"
        Fraction(risposta["exact"])
        assert risposta["unit"] in ("ampere", "volt"), (
            f"{ident}: unita' {risposta['unit']!r} fuori dal DC visibile")
        assert vista["verification"] is not None, (
            f"{ident}: chiusura senza evidenza")
        assert vista["truth"]["electrical_claim_status"] == "VERIFIED"
        assert vista["truth"]["backend_closure_status"] == "CLOSED"


def test_i_rifiuti_non_hanno_risposta_ma_hanno_diagnosi():
    for ident, vista in _viste().items():
        if vista["outcome"] != "refusal":
            continue
        assert vista["answer"] is None, f"{ident}: rifiuto con risposta"
        assert vista["verification"] is None, f"{ident}: rifiuto con evidenza"
        rifiuto = vista["refusal"]
        assert rifiuto is not None, f"{ident}: rifiuto senza diagnosi"
        assert rifiuto["cause"], f"{ident}: rifiuto senza causa"
        assert rifiuto["diagnosis"].strip(), f"{ident}: rifiuto senza diagnosi"


def test_nessuna_vista_fabbrica_product_verified():
    for sorgente in sorted(SESSIONI.glob("*.json")):
        if sorgente.name == "index.json":
            continue
        vista = json.loads(sorgente.read_text(encoding="utf-8"))
        assert vista["truth"]["product_verified"] is False, (
            f"{sorgente.stem}: product_verified non falso")
