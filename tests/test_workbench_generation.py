"""Le viste versionate sono rigenerabili dal kernel, mai scritte a mano.

Ogni JSON in `web/public/sessions/` nasce da `scripts/generate_workbench.py`
attraverso la radice canonica. Questi test rigenerano in una directory
temporanea e confrontano: a `source_sha` normalizzato i byte devono
coincidere, e ogni risposta deve accordarsi con l'involucro di prodotto.
"""
from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from pathlib import Path

from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import resolve

RADICE = Path(__file__).resolve().parent.parent
SESSIONI = RADICE / "web" / "public" / "sessions"
SHA_FISSO = "c" * 40


def _generatore():
    import sys
    spec = importlib.util.spec_from_file_location(
        "generate_workbench", RADICE / "scripts" / "generate_workbench.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generate_workbench"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _normalizza(vista: dict) -> dict:
    copia = json.loads(json.dumps(vista))
    if copia.get("provenance"):
        copia["provenance"]["source_sha"] = "0" * 40
    return copia


def test_le_viste_versionate_esistono():
    attesi = {"partitore-d1", "scala-due-riduzioni", "ponte-nodale", "rifiuto-reattivo"}
    trovati = {p.stem for p in SESSIONI.glob("*.json")} - {"index"}
    assert trovati == attesi
    indice = json.loads((SESSIONI / "index.json").read_text(encoding="utf-8"))
    assert {voce["id"] for voce in indice} == attesi


def test_rigenerazione_byte_identica_a_sha_normalizzato(tmp_path):
    gen = _generatore()
    gen.genera(tmp_path, SHA_FISSO)
    for sorgente in sorted(SESSIONI.glob("*.json")):
        if sorgente.name == "index.json":
            rigenerato = (tmp_path / "index.json").read_text(encoding="utf-8")
            assert rigenerato == sorgente.read_text(encoding="utf-8")
            continue
        versione = json.loads(sorgente.read_text(encoding="utf-8"))
        fresco = json.loads((tmp_path / sorgente.name).read_text(encoding="utf-8"))
        assert _normalizza(fresco) == _normalizza(versione), sorgente.name
        assert len(fresco["provenance"]["source_sha"]) == 40


def test_ogni_risposta_si_accorda_con_l_involucro_di_prodotto():
    gen = _generatore()
    for ex in gen.ESERCIZI:
        vista = json.loads((SESSIONI / f"{ex.id}.json").read_text(encoding="utf-8"))
        if vista["outcome"] != "closed":
            continue
        esito = resolve(leggi(ex.netlist))
        assert not isinstance(esito, Exception)
        from kirchhoff.pipeline.failure import Failure
        from kirchhoff.domain.refusal import Refusal
        assert not isinstance(esito, (Refusal, Failure))
        qid, quantita, obiettivo = ex.domanda
        assert esito.soluzione[obiettivo][quantita] == Fraction(vista["answer"]["exact"])


def test_nessuna_vista_promette_product_verified():
    for sorgente in sorted(SESSIONI.glob("*.json")):
        testo = sorgente.read_text(encoding="utf-8")
        assert "Product Verified" not in testo
