"""Il prodotto risolve, verifica e disegna — dalla netlist al disegno.

Questi test coprono il percorso che fino al 26/08/2026 non esisteva: le parti si
componevano solo dentro altri test, e la revisione della Story 1.7 lo aveva
misurato («`annota` ha zero chiamanti in `src/`»).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.pipeline import Rifiuto, Risolto, layout_a_maglia, risolvi
from kirchhoff.pipeline.netlist import leggi

PARTITORE = """
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? voltage R2
"""


def test_il_partitore_da_la_risposta_esatta_del_libro():
    """12 V su 100+220 ohm: la corrente e' 3/80 A e su R2 cadono 33/4 V.

    Il valore e' ESATTO, non arrotondato: e' il punto di avere l'aritmetica
    razionale, e un test che accettasse 8.25 con tolleranza non distinguerebbe
    una risposta giusta da una quasi giusta.
    """
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R2"]["voltage"] == Fraction(33, 4)
    assert esito.soluzione["R1"]["voltage"] == Fraction(15, 4)
    assert esito.soluzione["R1"]["current"] == Fraction(3, 80)
    # e le due cadute sommano ESATTAMENTE alla tensione impressa
    assert (esito.soluzione["R1"]["voltage"]
            + esito.soluzione["R2"]["voltage"]) == Fraction(12)


def test_si_verifica_PRIMA_di_disegnare():
    """Le due verifiche sono nominate nel risultato, non implicite.

    Un `Risolto` che non dicesse quali controlli ha superato attesterebbe una
    garanzia che nessuno puo' rileggere — E-65.
    """
    esito = risolvi(leggi(PARTITORE))
    assert esito.verifiche == ("legge dei nodi", "bilancio di potenza")


def test_due_esecuzioni_danno_gli_stessi_byte():
    """L'identificatore del layout e' derivato dal contenuto, non coniato.

    Se venisse dall'orologio, due esecuzioni sullo stesso circuito darebbero
    disegni diversi — e AD-35 vieta esattamente questo.
    """
    c = leggi(PARTITORE)
    assert risolvi(c).svg == risolvi(c).svg


def test_il_disegno_porta_gli_attributi_semantici():
    esito = risolvi(leggi(PARTITORE))
    for atteso in ('data-component-id="R1"', 'data-component-id="R2"',
                   'data-component-id="V1"', 'data-node-id="a"'):
        assert atteso in esito.svg


def test_un_circuito_che_non_e_una_maglia_viene_RIFIUTATO_non_disposto_male():
    """Un disegno disposto male mente sulla topologia, e l'SVG e' la sorgente
    unica (AD-10): meglio un rifiuto esplicito di un disegno che mente."""
    due_maglie = leggi("""
    V1 b 0 12 volt
    R1 b a 100 ohm
    R2 a 0 220 ohm
    R3 a 0 330 ohm
    """)
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(due_maglie)


def test_una_lettera_non_prevista_nomina_il_colpevole():
    """Il vocabolario delle lettere e' chiuso: un componente indovinato verrebbe
    risolto male in silenzio."""
    with pytest.raises(ValueError, match="vocabolario e' chiuso"):
        leggi("X1 a b 5 ohm")


def test_un_decimale_viene_respinto_perche_sporca_l_aritmetica_esatta():
    with pytest.raises(ValueError, match="non e' un numero"):
        leggi("R1 a b centoventi ohm")


def test_una_netlist_vuota_lo_dice():
    with pytest.raises(ValueError, match="netlist vuota"):
        leggi("# solo commenti\n\n")


def test_il_rifiuto_dice_quale_controllo_e_di_quanto():
    """`Rifiuto` senza misura sarebbe un'accusa senza prova, e in questo prodotto
    la falsa accusa e' il difetto peggiore."""
    r = Rifiuto("legge dei nodi", "al nodo a restano 3/7 A")
    assert "legge dei nodi" in str(r) and "3/7" in str(r)


# --- i rami che il percorso interno non raggiunge da solo -------------------

def test_una_maglia_di_due_soli_nodi_si_dispone():
    """Un generatore e un resistore: la maglia piu' corta che esista."""
    esito = risolvi(leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n"))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R1"]["current"] == Fraction(3)


def test_una_maglia_lunga_si_dispone_sul_perimetro():
    """Quattro nodi: il ramo del poligono, che le maglie corte non toccano."""
    esito = risolvi(leggi(
        "V1 d 0 12 volt\nR1 d c 10 ohm\nR2 c b 20 ohm\nR3 b 0 30 ohm\n"))
    assert isinstance(esito, Risolto)
    assert esito.soluzione["R1"]["current"] == Fraction(1, 5)


def test_un_nodo_con_tre_bipoli_non_e_una_maglia():
    """`_giro` rifiuta prima ancora di camminare: un nodo di grado tre non
    appartiene a una maglia sola."""
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi(
            "V1 a 0 12 volt\nR1 a b 10 ohm\nR2 a b 20 ohm\nR3 b 0 30 ohm\n"))


def test_un_bipolo_isolato_non_e_una_maglia():
    """Due componenti che non si toccano: il cammino si interrompe."""
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi("V1 a 0 12 volt\nR1 a 0 10 ohm\n"
                              "R2 c d 20 ohm\nR3 c d 30 ohm\n"))


def test_una_domanda_malformata_nomina_la_riga():
    with pytest.raises(ValueError, match="riga 1"):
        leggi("? voltage")


def test_un_bipolo_con_pezzi_mancanti_nomina_la_riga():
    with pytest.raises(ValueError, match="riga 2"):
        leggi("V1 a 0 12 volt\nR1 a b 100\n")


# --- il rifiuto: la guardia e cio che il percorso interno NON produce -------

def test_il_rifiuto_scatta_quando_la_legge_dei_nodi_non_torna(monkeypatch):
    """**Questa guardia non puo scattare sul percorso interno, ed e giusto
    dirlo.** `solve_dc` risolve il sistema che la legge dei nodi stessa
    definisce: la sua soluzione la soddisfa per costruzione, quindi
    `kcl_residuals` su un risultato di `solve_dc` e sempre nullo.

    Non ne segue che il controllo sia inutile: segue che il suo modello di
    minaccia e un solutore SOSTITUITO o guasto, non quello corrente. Per provarlo
    bisogna quindi sostituirlo — ed e cio che questo test fa, invece di
    dichiarare coperto un ramo che nessun circuito raggiunge.

    Registrato in `deferred-work.md`: se un giorno il solutore diventasse
    pluggable, questa guardia sarebbe la prima difesa e andrebbe misurata su un
    solutore vero che sbaglia.
    """
    # `kirchhoff.pipeline.__init__` riesporta la FUNZIONE `risolvi`, che nel
    # namespace del pacchetto copre il MODULO omonimo: `import
    # kirchhoff.pipeline.risolvi as m` restituisce la funzione. E' una
    # collisione di nomi registrata in `deferred-work.md`; qui si prende il
    # modulo da `sys.modules`, dove vive con la sua chiave intera.
    import sys
    modulo = sys.modules["kirchhoff.pipeline.risolvi"]

    monkeypatch.setattr(modulo.mna, "kcl_residuals",
                        lambda ir, sol: {"a": Fraction(3, 7)})
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Rifiuto)
    assert esito.controllo == "legge dei nodi"
    assert "3/7" in esito.misura


def test_il_rifiuto_scatta_quando_la_potenza_non_pareggia(monkeypatch):
    """Stessa natura del precedente: il bilancio di potenza su una soluzione di
    `solve_dc` pareggia sempre, e la guardia difende da un solutore sostituito."""
    # `kirchhoff.pipeline.__init__` riesporta la FUNZIONE `risolvi`, che nel
    # namespace del pacchetto copre il MODULO omonimo: `import
    # kirchhoff.pipeline.risolvi as m` restituisce la funzione. E' una
    # collisione di nomi registrata in `deferred-work.md`; qui si prende il
    # modulo da `sys.modules`, dove vive con la sua chiave intera.
    import sys
    modulo = sys.modules["kirchhoff.pipeline.risolvi"]

    monkeypatch.setattr(modulo.mna, "kcl_residuals", lambda ir, sol: {})
    monkeypatch.setattr(modulo.mna, "power_balance", lambda ir, sol: Fraction(1, 9))
    esito = risolvi(leggi(PARTITORE))
    assert isinstance(esito, Rifiuto)
    assert esito.controllo == "bilancio di potenza"
    assert "1/9" in esito.misura


# --- il comando ------------------------------------------------------------

def _netlist(tmp_path, testo=PARTITORE):
    f = tmp_path / "c.netlist"
    f.write_text(testo, encoding="utf-8")
    return f


def test_il_comando_risolve_e_stampa(tmp_path, capsys):
    from kirchhoff.pipeline.cli import main
    assert main([str(_netlist(tmp_path))]) == 0
    fuori = capsys.readouterr().out
    assert "verificato da legge dei nodi e bilancio di potenza" in fuori
    # il valore ESATTO e quello leggibile, accanto — mai l'uno al posto dell'altro
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
    """K-3: il rifiuto e' un output valido. Il codice di uscita lo distingue da
    un errore d'uso (65) e da un file mancante (66), perche' chi chiama deve
    poter reagire diversamente."""
    import sys
    from kirchhoff.pipeline.cli import main
    modulo = sys.modules["kirchhoff.pipeline.risolvi"]
    monkeypatch.setattr(modulo.mna, "kcl_residuals", lambda ir, sol: {"a": Fraction(1, 3)})
    assert main([str(_netlist(tmp_path))]) == 3
    assert "RIFIUTATO" in capsys.readouterr().err


def test_il_pdf_assente_lo_DICE_invece_di_scrivere_un_file_vuoto(tmp_path, capsys, monkeypatch):
    """Un PDF mancante annunciato e' un problema; un PDF vuoto scritto in
    silenzio e' un difetto."""
    from kirchhoff.pipeline import cli
    monkeypatch.setattr(cli, "_chromium", lambda: None)
    assert cli.main([str(_netlist(tmp_path)), "--pdf", str(tmp_path / "x.pdf")]) == 70
    assert "nessun chromium" in capsys.readouterr().err


def test_il_decimale_accompagna_l_esatto_non_lo_sostituisce():
    from kirchhoff.pipeline.cli import _decimale
    assert _decimale(Fraction(33, 4)) == "8.25"
    assert _decimale(Fraction(1, 3)) == "0.3333"


def test_il_pdf_esce_davvero_se_il_browser_c_e(tmp_path):
    """Il PDF non e' simulato: si scrive e si rilegge l'intestazione.

    Salta se sulla macchina non c'e' un browser — un test che finge di aver
    provato quando non ha provato e' peggio di un test assente.
    """
    from kirchhoff.pipeline import cli
    if cli._chromium() is None:
        pytest.skip("nessun chromium sul disco: `npx playwright install`")
    pdf = tmp_path / "d.pdf"
    assert cli.main([str(_netlist(tmp_path)), "--pdf", str(pdf)]) == 0
    assert pdf.read_bytes()[:5] == b"%PDF-"
    assert not pdf.with_suffix(".stampa.html").exists(), "il file d'appoggio resta"


def test_due_gemelli_su_nodi_allineati_in_orizzontale_si_scostano_in_verticale():
    """Lo scostamento segue l'orientamento del segmento.

    Su una maglia di tre nodi due dei tre stanno alla stessa quota: due bipoli
    fra quella coppia devono separarsi in VERTICALE, altrimenti si
    sovrappongono lungo il filo che li unisce.
    """
    piazzati = layout_a_maglia(leggi(
        "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n")).placements
    quote = {p.entity.id: (p.x, p.y) for p in piazzati}
    assert len({quote[c] for c in ("V1", "R1", "R2")}) == 3, "due bipoli coincidono"


def test_un_circuito_senza_nodo_di_riferimento_e_fermato_A_MONTE():
    """Non da `layout_a_maglia`: dall'IR stesso.

    Il test esiste per DOCUMENTARE dove sta la guardia. Scrivendo
    `layout_a_maglia` avevo aggiunto un controllo sul nodo di riferimento, e non
    poteva scattare: `IR.__post_init__` rifiuta prima. Un controllo che non puo'
    fallire e' E-65, e l'ho tolto — questo test tiene il ricordo del perche'.
    """
    with pytest.raises(ValueError, match="manca il nodo di riferimento"):
        leggi("R1 a b 10 ohm\nR2 b a 20 ohm\n")


# --- i rami che restavano scoperti -----------------------------------------

def test_senza_cartella_dei_browser_il_pdf_lo_dice(tmp_path, monkeypatch):
    """Il ramo «la cartella non esiste», distinto da «esiste ma e' vuota»."""
    from kirchhoff.pipeline import cli
    monkeypatch.setattr(cli.pathlib.Path, "home", staticmethod(lambda: tmp_path))
    assert cli._chromium() is None


def test_con_la_cartella_ma_senza_eseguibili_il_pdf_lo_dice(tmp_path, monkeypatch):
    """La cartella c'e' e non contiene nessun guscio: caso diverso dal precedente,
    e il codice ha due `return None` distinti perche' arriva da due strade."""
    from kirchhoff.pipeline import cli
    (tmp_path / "Library/Caches/ms-playwright/chromium_headless_shell-1").mkdir(parents=True)
    monkeypatch.setattr(cli.pathlib.Path, "home", staticmethod(lambda: tmp_path))
    assert cli._chromium() is None


def test_un_componente_senza_soluzione_non_ferma_la_stampa(tmp_path, capsys, monkeypatch):
    """Il `continue`: un bipolo per cui il solutore non riporta la tensione viene
    saltato invece di far esplodere il comando a meta' tabella."""
    from kirchhoff.pipeline import cli

    # Si sostituisce `risolvi`, non `solve_dc`: togliere un componente dalla
    # soluzione grezza rompe `kcl_residuals` a valle con un KeyError, e il test
    # misurerebbe quel guasto invece del ramo che vuole vedere.
    vero = cli.risolvi

    def parziale(circuito, layout=None):
        pieno = vero(circuito, layout)
        return type(pieno)(
            circuito=pieno.circuito,
            soluzione={k: v for k, v in pieno.soluzione.items() if k != "R1"},
            layout=pieno.layout, svg=pieno.svg, verifiche=pieno.verifiche)

    monkeypatch.setattr(cli, "risolvi", parziale)
    assert cli.main([str(_netlist(tmp_path))]) == 0
    fuori = capsys.readouterr().out
    assert "R2" in fuori and "33/4" in fuori


def test_un_grafo_che_si_interrompe_a_meta_non_e_una_maglia():
    """Il `return None` di `_giro` quando il cammino resta senza passi: due
    triangoli separati hanno tutti i nodi di grado due, quindi superano il primo
    controllo, e cadono solo camminando."""
    with pytest.raises(ValueError, match="non formano una maglia sola"):
        layout_a_maglia(leggi(
            "V1 a 0 12 volt\nR1 a b 10 ohm\nR2 b 0 20 ohm\n"
            "R3 c d 30 ohm\nR4 d e 40 ohm\nR5 e c 50 ohm\n"))


def test_i_gemelli_su_nodi_impilati_si_scostano_in_ORIZZONTALE():
    """L'altro verso dello scostamento: quando i due nodi condividono la x, i
    gemelli si separano lungo x. Il ramo verticale era gia' coperto."""
    piazzati = layout_a_maglia(leggi("V1 a 0 9 volt\nR1 a 0 3 ohm\n")).placements
    dove = {p.entity.id: (p.x, p.y) for p in piazzati}
    assert dove["V1"] != dove["R1"], "i due gemelli coincidono"
    assert dove["V1"][1] == dove["R1"][1], "si sono scostati nel verso sbagliato"
