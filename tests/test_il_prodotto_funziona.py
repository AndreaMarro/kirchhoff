"""Il prodotto risolve, verifica e disegna — dalla netlist al disegno."""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline import Risolto, layout_a_maglia, risolvi
from kirchhoff.pipeline.netlist import leggi

PARTITORE = """
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? voltage R2
"""


def test_il_partitore_da_la_risposta_esatta_del_libro():
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R2"]["voltage"] == Fraction(33, 4)
    assert esito.soluzione["R1"]["voltage"] == Fraction(15, 4)
    assert esito.soluzione["R1"]["current"] == Fraction(3, 80)
    assert (esito.soluzione["R1"]["voltage"]
            + esito.soluzione["R2"]["voltage"]) == Fraction(12)


def test_si_verifica_PRIMA_di_disegnare():
    esito = risolvi(leggi(PARTITORE))
    for nome in ("legge dei nodi", "legge delle maglie",
                 "bilancio di potenza", "sanità fisica"):
        assert nome in esito.verifiche


def test_due_esecuzioni_danno_gli_stessi_byte():
    c = leggi(PARTITORE)
    assert risolvi(c).svg == risolvi(c).svg


def test_il_disegno_porta_gli_attributi_semantici():
    esito = risolvi(leggi(PARTITORE))
    for atteso in ('data-component-id="R1"', 'data-component-id="R2"',
                   'data-component-id="V1"', 'data-node-id="a"'):
        assert atteso in esito.svg


def test_un_circuito_che_non_e_una_maglia_viene_RIFIUTATO_non_disposto_male():
    due_maglie = leggi("""
    V1 b 0 12 volt
    R1 b a 100 ohm
    R2 a 0 220 ohm
    R3 a 0 330 ohm
    """)
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(due_maglie)
    esito = risolvi(due_maglie)
    assert isinstance(esito, Risolto)
    assert esito.svg is None and esito.layout is None


def test_una_lettera_non_prevista_nomina_il_colpevole():
    with pytest.raises(ValueError, match="vocabolario e' chiuso"):
        leggi("X1 a b 5 ohm")


def test_un_decimale_viene_respinto_perche_sporca_l_aritmetica_esatta():
    with pytest.raises(ValueError, match="non e' un numero"):
        leggi("R1 a b centoventi ohm")


def test_una_netlist_vuota_lo_dice():
    with pytest.raises(ValueError, match="netlist vuota"):
        leggi("# solo commenti\n\n")


def test_il_rifiuto_dice_quale_controllo_e_di_quanto():
    r = Refusal("residual", "a", "node", "al nodo a restano 3/7 A")
    assert "residual" in str(r) and "3/7" in str(r) and "a" in str(r)


def test_una_maglia_di_due_soli_nodi_si_dispone():
    esito = risolvi(leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n"))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R1"]["current"] == Fraction(3)


def test_una_maglia_lunga_si_dispone_sul_perimetro():
    esito = risolvi(leggi(
        "V1 d 0 12 volt\nR1 d c 10 ohm\nR2 c b 20 ohm\nR3 b 0 30 ohm\n"))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R1"]["current"] == Fraction(1, 5)


def test_un_nodo_con_tre_bipoli_non_e_una_maglia():
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi(
            "V1 a 0 12 volt\nR1 a b 10 ohm\nR2 a b 20 ohm\nR3 b 0 30 ohm\n"))


def test_un_bipolo_isolato_non_e_una_maglia():
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\n"
                              "R2 c d 20 ohm\nR3 c d 30 ohm\n"))


def test_una_domanda_malformata_nomina_la_riga():
    with pytest.raises(ValueError, match="riga 1"):
        leggi("? voltage")


def test_un_bipolo_con_pezzi_mancanti_nomina_la_riga():
    with pytest.raises(ValueError, match="riga 2"):
        leggi("V1 a 0 12 volt\nR1 a b 100\n")


def test_il_rifiuto_scatta_quando_la_legge_dei_nodi_non_torna(monkeypatch):
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {"a": Fraction(3, 7)})
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual" and "3/7" in esito.diagnosis


def test_il_rifiuto_scatta_quando_la_potenza_non_pareggia(monkeypatch):
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "kvl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(ver, "power_balance", lambda ir, sol: Fraction(1, 9))
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Refusal)
    assert esito.cause == "residual" and "1/9" in esito.diagnosis


def _netlist(tmp_path, testo=PARTITORE):
    f = tmp_path / "c.netlist"
    f.write_text(testo, encoding="utf-8")
    return f


def test_il_comando_risolve_e_stampa(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    assert main([str(_netlist(tmp_path))]) == 0
    fuori = capsys.readouterr().out
    assert "legge dei nodi" in fuori and "bilancio di potenza" in fuori
    assert "33/4" in fuori and "8.25" in fuori


def test_il_comando_scrive_il_disegno(tmp_path):
    from kirchhoff.pipeline.cli import main
    svg = tmp_path / "d.svg"
    assert main([str(_netlist(tmp_path)), "--svg", str(svg)]) == 0
    assert svg.read_text(encoding="utf-8").startswith("<svg")


def test_un_file_che_non_esiste_esce_66(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    assert main([str(tmp_path / "manca.netlist")]) == 66
    assert "non esiste" in capsys.readouterr().err


def test_una_netlist_malformata_esce_65(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    assert main([str(_netlist(tmp_path, "X1 a b 5 ohm"))]) == 65
    assert "vocabolario" in capsys.readouterr().err


def test_un_rifiuto_esce_3_e_dice_perche(tmp_path, capsys, monkeypatch):
    from kirchhoff.pipeline.cli import main
    import kirchhoff.domain.verify as ver
    monkeypatch.setattr(ver, "kcl_residuals", lambda ir, sol: {"a": Fraction(1, 3)})
    assert main([str(_netlist(tmp_path))]) == 3
    assert "RIFIUTATO" in capsys.readouterr().err


def test_il_pdf_assente_lo_DICE_invece_di_scrivere_un_file_vuoto(tmp_path, capsys, monkeypatch):
    from kirchhoff.pipeline import cli
    monkeypatch.setattr(cli, "_chromium", lambda: None)
    assert cli.main([str(_netlist(tmp_path)), "--pdf", str(tmp_path / "x.pdf")]) == 70
    assert "nessun chromium" in capsys.readouterr().err


def test_il_decimale_accompagna_l_esatto_non_lo_sostituisce():
    from kirchhoff.pipeline.cli import _decimale
    assert _decimale(Fraction(33, 4)) == "8.25"
    assert _decimale(Fraction(1, 3)) == "0.3333"


def test_il_pdf_esce_davvero_se_il_browser_c_e(tmp_path):
    from kirchhoff.pipeline import cli
    if cli._chromium() is None:
        pytest.skip("nessun chromium sul disco: `npx playwright install`")
    pdf = tmp_path / "d.pdf"
    assert cli.main([str(_netlist(tmp_path)), "--pdf", str(pdf)]) == 0
    assert pdf.read_bytes()[:5] == b"%PDF-"
    assert not pdf.with_suffix(".stampa.html").exists()


def test_due_gemelli_su_nodi_allineati_in_orizzontale_si_scostano_in_verticale():
    piazzati = layout_a_maglia(leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")).placements
    quote = {p.entity.id: (p.x, p.y) for p in piazzati}
    assert len({quote[c] for c in ("V1", "R1", "R2")}) == 3


def test_un_circuito_senza_nodo_di_riferimento_e_fermato_A_MONTE():
    with pytest.raises(ValueError, match="manca il nodo di riferimento"):
        leggi("R1 a b 10 ohm\nR2 b a 20 ohm\n")


def test_senza_cartella_dei_browser_il_pdf_lo_dice(tmp_path, monkeypatch):
    from kirchhoff.pipeline import cli
    monkeypatch.setattr(cli.pathlib.Path, "home", staticmethod(lambda: tmp_path))
    assert cli._chromium() is None


def test_con_la_cartella_ma_senza_eseguibili_il_pdf_lo_dice(tmp_path, monkeypatch):
    from kirchhoff.pipeline import cli
    (tmp_path / "Library/Caches/ms-playwright/chromium_headless_shell-1").mkdir(parents=True)
    monkeypatch.setattr(cli.pathlib.Path, "home", staticmethod(lambda: tmp_path))
    assert cli._chromium() is None


def test_un_componente_senza_soluzione_non_ferma_la_stampa(tmp_path, capsys, monkeypatch):
    from kirchhoff.pipeline import cli
    vero = cli.resolve

    def parziale(circuito, layout=None):
        pieno = vero(circuito, layout)
        return type(pieno)(
            circuito=pieno.circuito,
            soluzione={k: v for k, v in pieno.soluzione.items() if k != "R1"},
            layout=pieno.layout, svg=pieno.svg, verifiche=pieno.verifiche,
            solver=pieno.solver)

    monkeypatch.setattr(cli, "resolve", parziale)
    assert cli.main([str(_netlist(tmp_path))]) == 0
    fuori = capsys.readouterr().out
    assert "R2" in fuori and "33/4" in fuori


def test_un_grafo_che_si_interrompe_a_meta_non_e_una_maglia():
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi(
            "V1 a 0 12 volt\nR1 a b 10 ohm\nR2 b 0 20 ohm\n"
            "R3 c d 30 ohm\nR4 d e 40 ohm\nR5 e c 50 ohm\n"))


def test_i_gemelli_su_nodi_impilati_si_scostano_in_ORIZZONTALE():
    piazzati = layout_a_maglia(leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n")).placements
    dove = {p.entity.id: (p.x, p.y) for p in piazzati}
    assert dove["V1"] != dove["R1"]
    assert dove["V1"][1] == dove["R1"][1]
