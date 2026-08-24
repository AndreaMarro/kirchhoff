"""La riga di comando e' l'unica superficie dell'apparato di misura: va testata."""

import json
from pathlib import Path

from kirchhoff.eval.cli import main


def run(capsys, argv) -> tuple[int, dict]:
    code = main(argv)
    return code, json.loads(capsys.readouterr().out)


def test_build_e_report(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    code, d = run(capsys, ["build", "--n", "8", "--out", out, "--split", "0.5"])
    assert code == 0 and d["ok"] and d["generati"] == 8
    assert d["split"] == {"dev": 4, "holdout": 4}
    assert d["per_classe"] == {"dc_resistive": 2, "transient": 2,
                               "ac_sinusoidal": 2, "three_phase": 2}
    assert "PARZIALE" in d["coverage"]
    assert "three_phase" in d["coverage"]

    code, d = run(capsys, ["report", "--root", out, "--split", "dev"])
    assert code == 0 and d["VSR"] == 1.0 and d["SER"] == 0.0
    assert "NON l'estrazione" in d["coverage"]


def test_report_rifiuta_la_parte_trattenuta(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    run(capsys, ["build", "--n", "6", "--out", out, "--split", "0.5"])
    code, d = run(capsys, ["report", "--root", out, "--split", "holdout"])
    assert code == 2 and d["ok"] is False and "trattenuta" in d["errore"]


def test_report_con_allow_holdout(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    run(capsys, ["build", "--n", "6", "--out", out, "--split", "0.5"])
    code, d = run(capsys, ["report", "--root", out, "--split", "holdout", "--allow-holdout"])
    assert code == 0 and d["total"] == 2


def test_report_su_cartella_vuota(capsys, tmp_path: Path):
    (tmp_path / "dev").mkdir()
    code, d = run(capsys, ["report", "--root", str(tmp_path), "--split", "dev"])
    assert code == 2 and "nessun caso" in d["errore"]


# ---------------------------------------------------------------------------
# Storia 1.2, criterio "stessi input, stesse metriche". TTV misura l'orologio
# della macchina e non puo' essere riproducibile: il rapporto lo dichiara invece
# di fingere, cosi' tutto il resto si confronta riga per riga.
# ---------------------------------------------------------------------------

import pytest

from kirchhoff.eval import metrics


def test_due_esecuzioni_danno_le_stesse_metriche(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    run(capsys, ["build", "--n", "12", "--out", out])
    _, a = run(capsys, ["report", "--root", out, "--split", "dev"])
    _, b = run(capsys, ["report", "--root", out, "--split", "dev"])

    volatili = set(a["campi_dipendenti_dalla_macchina"])
    assert volatili == {"TTV_p90_s"}
    assert {k: v for k, v in a.items() if k not in volatili} == \
           {k: v for k, v in b.items() if k not in volatili}
    assert a["VSR"] == b["VSR"] == 1.0
    assert a["SER"] == b["SER"] == 0.0
    assert a["errors"] == b["errors"]


def test_il_rapporto_dichiara_cosa_non_si_puo_confrontare(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    run(capsys, ["build", "--n", "4", "--out", out])
    _, d = run(capsys, ["report", "--root", out, "--split", "dev"])
    assert d["campi_dipendenti_dalla_macchina"] == ["TTV_p90_s"]
    assert all(k in d for k in ("VSR", "SER", "QPS", "TTV_p90_s", "errors"))


def test_un_tipo_di_errore_inventato_non_allarga_la_matrice():
    """Cinque tipi, chiusi. Un sesto e' un errore del sistema sotto test, non una categoria nuova."""
    class C:
        ir = None
        expected = {}

    def bugiardo(ir):
        return metrics.Outcome(published=False, values={}, error_kind="fantasia")

    with pytest.raises(ValueError, match="fantasia"):
        metrics.run([C()], bugiardo, "test")


def test_nessuna_metrica_esce_quando_la_parte_trattenuta_e_rifiutata(capsys, tmp_path: Path):
    out = str(tmp_path / "rs")
    run(capsys, ["build", "--n", "6", "--out", out, "--split", "0.5"])
    code, d = run(capsys, ["report", "--root", out, "--split", "holdout"])
    assert code == 2
    assert set(d) == {"ok", "errore"}
    assert not any(k in d for k in ("VSR", "SER", "QPS", "TTV_p90_s", "errors", "total"))
