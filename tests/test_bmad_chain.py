"""Il tracciatore della catena BMAD, verificato invece che creduto.

Un tracciatore che sbaglia in silenzio è peggio di nessun tracciatore: fa credere che il
lavoro sia registrato. Questi test coprono le due direzioni di divergenza — il passo
fatto e non tracciato (il difetto misurato il 14 agosto) e il passo dichiarato senza
prova — più il fatto che la tabella di `loop.md` non possa essere scritta a mano senza
che qualcuno se ne accorga.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent


def _carica_tracciatore():
    percorso = RADICE / "scripts" / "bmad_chain.py"
    spec = importlib.util.spec_from_file_location("bmad_chain", percorso)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["bmad_chain"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


catena = _carica_tracciatore()


@pytest.fixture
def finto(tmp_path: Path) -> Path:
    """Un albero minimo che soddisfa le prove dei passi 1 e 2, e nient'altro."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "02-costituzione-kirchhoff.md").write_text(
        "K-0 ... K-5 e i confini owner-locked\n", encoding="utf-8")
    brief = tmp_path / catena.PIANIFICATI / "briefs" / "brief-Kirchhoff-2026-08-13"
    brief.mkdir(parents=True)
    (brief / "brief.md").write_text(
        "---\nversion: 3\n---\n" + "x" * 10_000, encoding="utf-8")
    (brief / "addendum.md").write_text("## H. Delta v3\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def loop_finto(tmp_path: Path) -> Path:
    f = tmp_path / "loop.md"
    f.write_text(
        f"# Loop\n\ntesto prima\n\n{catena.APERTURA}\nvecchio\n{catena.CHIUSURA}\n\n"
        "testo dopo\n", encoding="utf-8")
    return f


# ── le prove ────────────────────────────────────────────────────────────────────


def test_una_prova_su_file_assente_non_e_soddisfatta(tmp_path: Path):
    p = catena.Prova("non/esiste.md", "qualsiasi")
    assert not p.soddisfatta(tmp_path)


def test_una_prova_con_soglia_di_taglia_respinge_il_segnaposto(tmp_path: Path):
    """Un file creato vuoto col marcatore giusto non è un brief."""
    (tmp_path / "b.md").write_text("version: 3\n", encoding="utf-8")
    assert catena.Prova("b.md", "version: 3").soddisfatta(tmp_path)
    assert not catena.Prova("b.md", "version: 3", min_byte=10_000).soddisfatta(tmp_path)


def test_un_file_binario_non_passa_in_silenzio(tmp_path: Path):
    (tmp_path / "b.md").write_bytes(b"\xff\xfe\x00 version: 3")
    assert not catena.Prova("b.md", "version: 3").soddisfatta(tmp_path)


# ── le due direzioni di divergenza ──────────────────────────────────────────────


def test_il_difetto_del_14_agosto_viene_rilevato(finto: Path):
    """Passo 2 fatto sul disco, stato ancora `backlog`: il lavoro sarebbe stato rifatto."""
    stato = catena.stato_vuoto("08-14-2026 07:41")
    fuori = catena.derive(stato, finto)
    generi = {(d.passo.chiave, d.genere) for d in fuori}
    assert ("02-brief", "fatto-non-tracciato") in generi
    assert ("01-costituzione", "fatto-non-tracciato") in generi
    assert "fatto e non tracciato" in next(
        d for d in fuori if d.passo.chiave == "02-brief").descrivi()


def test_un_passo_dichiarato_senza_prova_e_una_divergenza(finto: Path):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    stato["steps"]["03-prd"]["status"] = "done"
    fuori = [d for d in catena.derive(stato, finto) if d.passo.chiave == "03-prd"]
    assert len(fuori) == 1
    assert fuori[0].genere == "dichiarato-senza-prova"
    assert "prd.md" in fuori[0].descrivi()


def test_lo_stato_allineato_alle_prove_non_produce_divergenze(finto: Path):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    for chiave in ("01-costituzione", "02-brief"):
        stato["steps"][chiave]["status"] = "done"
    assert catena.derive(stato, finto) == []


def test_una_forzatura_dichiarata_non_e_una_divergenza_ma_resta_visibile(finto: Path):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    stato["steps"]["01-costituzione"]["status"] = "done"
    stato["steps"]["02-brief"]["status"] = "done"
    stato["steps"]["03-prd"].update(
        {"status": "done", "forced": True, "reason": "prova non applicabile"})
    assert catena.derive(stato, finto) == []
    assert "⚠️" in catena.rendi_tabella(stato, finto)


def test_il_prossimo_passo_e_il_primo_non_chiuso(finto: Path):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    stato["steps"]["01-costituzione"]["status"] = "done"
    assert catena.prossimo(stato, finto).chiave == "02-brief"


def test_a_catena_chiusa_non_c_e_un_prossimo(finto: Path):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    for voce in stato["steps"].values():
        voce["status"] = "done"
    assert catena.prossimo(stato, finto) is None


# ── persistenza ─────────────────────────────────────────────────────────────────


def test_lo_stato_riletto_e_quello_scritto(tmp_path: Path):
    f = tmp_path / "stato.json"
    stato = catena.stato_vuoto("08-14-2026 12:00")
    stato["steps"]["02-brief"]["status"] = "done"
    catena.salva_stato(stato, f, "08-14-2026 12:05")
    riletto = catena.carica_stato(f)
    assert riletto["steps"]["02-brief"]["status"] == "done"
    assert riletto["last_updated"] == "08-14-2026 12:05"


def test_uno_schema_estraneo_non_viene_interpretato(tmp_path: Path):
    f = tmp_path / "stato.json"
    f.write_text(json.dumps({"schema": "altro@9", "steps": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        catena.carica_stato(f)


def test_un_passo_nuovo_compare_come_backlog_invece_di_far_fallire(tmp_path: Path):
    f = tmp_path / "stato.json"
    catena.salva_stato(
        {"schema": catena.SCHEMA, "source": "x", "steps": {}}, f, "08-14-2026 12:00")
    riletto = catena.carica_stato(f)
    assert set(riletto["steps"]) == {p.chiave for p in catena.CATENA}
    assert riletto["steps"]["07-readiness"]["status"] == "backlog"


def test_uno_stato_assente_non_e_un_errore(tmp_path: Path):
    stato = catena.carica_stato(tmp_path / "mai-creato.json", "08-14-2026 12:00")
    assert all(v["status"] == "backlog" for v in stato["steps"].values())


# ── la tabella in loop.md ───────────────────────────────────────────────────────


def test_la_tabella_sostituisce_solo_il_blocco_fra_i_marcatori(finto, loop_finto):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    assert catena.rendi_file_loop(stato, loop_finto, finto) is True
    testo = loop_finto.read_text(encoding="utf-8")
    assert "testo prima" in testo and "testo dopo" in testo
    assert "vecchio" not in testo
    assert testo.count(catena.APERTURA) == 1


def test_rendere_due_volte_non_cambia_niente(finto, loop_finto):
    stato = catena.stato_vuoto("08-14-2026 12:00")
    catena.rendi_file_loop(stato, loop_finto, finto)
    assert catena.rendi_file_loop(stato, loop_finto, finto) is False


def test_una_tabella_che_contiene_i_marcatori_viene_rifiutata(loop_finto: Path):
    """Il difetto del delimitatore iniettato: si vede solo alla seconda esecuzione.

    Il passo 8 ha per prova l'esistenza dei marcatori in `loop.md`, e la colonna «Prova»
    stampa il testo cercato. Stampare il marcatore intero rendeva la tabella un blocco
    che il render successivo troncava a metà.
    """
    avvelenata = (f"{catena.APERTURA}\n| 8 | Ship loop | «{catena.CHIUSURA}» |\n"
                  f"{catena.CHIUSURA}")
    with pytest.raises(ValueError, match="contiene 2 volte"):
        catena.sostituisci_in_loop(loop_finto.read_text(encoding="utf-8"), avvelenata)


def test_il_render_e_stabile_col_passo_8_soddisfatto(finto: Path):
    """Rendere due volte sull'albero dove anche il passo 8 ha le sue prove."""
    loop = finto / ".claude" / "loop.md"
    loop.parent.mkdir()
    loop.write_text(f"testa\n{catena.APERTURA}\n{catena.CHIUSURA}\ncoda\n",
                    encoding="utf-8")
    stato = catena.stato_vuoto("08-14-2026 12:00")
    assert catena.rendi_file_loop(stato, loop, finto) is True
    primo = loop.read_text(encoding="utf-8")
    assert catena.rendi_file_loop(stato, loop, finto) is False
    assert loop.read_text(encoding="utf-8") == primo
    assert primo.count(catena.APERTURA) == 1
    assert primo.endswith("coda\n")


def test_marcatori_assenti_sono_un_errore_e_non_un_append(tmp_path: Path, finto: Path):
    f = tmp_path / "senza-marcatori.md"
    f.write_text("# Loop senza marcatori\n", encoding="utf-8")
    with pytest.raises(ValueError, match="marcatori"):
        catena.rendi_file_loop(catena.stato_vuoto("08-14-2026 12:00"), f, finto)


def test_marcatori_invertiti_sono_un_errore(tmp_path: Path, finto: Path):
    f = tmp_path / "invertiti.md"
    f.write_text(f"{catena.CHIUSURA}\n{catena.APERTURA}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="marcatori"):
        catena.rendi_file_loop(catena.stato_vuoto("08-14-2026 12:00"), f, finto)


# ── la riga di comando ──────────────────────────────────────────────────────────


def _argv(finto: Path, loop: Path, stato: Path, *resto: str) -> list[str]:
    return ["--radice", str(finto), "--file-loop", str(loop),
            "--file-stato", str(stato), "--data", "08-14-2026 12:00", *resto]


def test_inizializza_deduce_i_passi_gia_fatti(finto, loop_finto, tmp_path, capsys):
    s = tmp_path / "stato.json"
    assert catena.main(_argv(finto, loop_finto, s, "inizializza")) == 0
    dati = json.loads(s.read_text(encoding="utf-8"))
    assert dati["steps"]["02-brief"]["status"] == "done"
    assert dati["steps"]["03-prd"]["status"] == "backlog"


def test_inizializza_non_sovrascrive_senza_forza(finto, loop_finto, tmp_path):
    s = tmp_path / "stato.json"
    assert catena.main(_argv(finto, loop_finto, s, "inizializza")) == 0
    assert catena.main(_argv(finto, loop_finto, s, "inizializza")) == 1


def test_verifica_esce_uno_sulle_divergenze_e_zero_quando_allineato(
        finto, loop_finto, tmp_path):
    s = tmp_path / "stato.json"
    catena.salva_stato(catena.stato_vuoto("08-14-2026 12:00"), s, "08-14-2026 12:00")
    assert catena.main(_argv(finto, loop_finto, s, "verifica")) == 1
    catena.main(_argv(finto, loop_finto, s, "inizializza", "--forza"))
    assert catena.main(_argv(finto, loop_finto, s, "verifica")) == 0


def test_segnare_done_senza_prove_viene_rifiutato(finto, loop_finto, tmp_path, capsys):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    assert catena.main(
        _argv(finto, loop_finto, s, "segna", "--passo", "3", "--stato", "done")) == 1
    assert "prd.md" in capsys.readouterr().err
    dati = json.loads(s.read_text(encoding="utf-8"))
    assert dati["steps"]["03-prd"]["status"] == "backlog"


def test_forzare_senza_motivo_viene_rifiutato(finto, loop_finto, tmp_path):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    assert catena.main(_argv(finto, loop_finto, s, "segna", "--passo", "3",
                             "--stato", "done", "--forza")) == 2


def test_segnare_riscrive_la_tabella_senza_che_glielo_si_chieda(
        finto, loop_finto, tmp_path):
    """L'aggiornamento della tabella non è un secondo comando che si può saltare."""
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    loop_finto.write_text(
        f"{catena.APERTURA}\nmanomessa\n{catena.CHIUSURA}\n", encoding="utf-8")
    assert catena.main(_argv(finto, loop_finto, s, "segna", "--passo", "3",
                             "--stato", "in-progress")) == 0
    assert "manomessa" not in loop_finto.read_text(encoding="utf-8")


def test_rendi_controlla_rileva_la_tabella_manomessa(finto, loop_finto, tmp_path):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    catena.main(_argv(finto, loop_finto, s, "rendi"))
    assert catena.main(_argv(finto, loop_finto, s, "rendi", "--controlla")) == 0
    loop_finto.write_text(
        f"{catena.APERTURA}\n| 3 | PRD | ✅ tutto fatto |\n{catena.CHIUSURA}\n",
        encoding="utf-8")
    assert catena.main(_argv(finto, loop_finto, s, "rendi", "--controlla")) == 1


def test_verifica_con_loop_rileva_la_tabella_manomessa(finto, loop_finto, tmp_path):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    catena.main(_argv(finto, loop_finto, s, "rendi"))
    assert catena.main(_argv(finto, loop_finto, s, "verifica", "--con-loop")) == 0
    loop_finto.write_text(
        f"{catena.APERTURA}\nbugia\n{catena.CHIUSURA}\n", encoding="utf-8")
    assert catena.main(_argv(finto, loop_finto, s, "verifica", "--con-loop")) == 1


def test_un_passo_inesistente_e_un_errore_nominato(finto, loop_finto, tmp_path, capsys):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    assert catena.main(_argv(finto, loop_finto, s, "segna", "--passo", "99",
                             "--stato", "done")) == 2
    assert "passo sconosciuto" in capsys.readouterr().err


def test_stato_json_e_leggibile_da_una_macchina(finto, loop_finto, tmp_path, capsys):
    s = tmp_path / "stato.json"
    catena.main(_argv(finto, loop_finto, s, "inizializza"))
    capsys.readouterr()
    assert catena.main(_argv(finto, loop_finto, s, "stato", "--json")) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == catena.SCHEMA


# ── l'albero vero ───────────────────────────────────────────────────────────────


def test_la_catena_reale_e_coerente():
    """Il gate, sull'albero vero. Se un giorno fallisce, ha ragione lui."""
    stato = catena.carica_stato()
    assert catena.derive(stato) == [], "\n".join(
        d.descrivi() for d in catena.derive(stato))


def test_la_tabella_di_loop_md_e_allineata_allo_stato():
    testo = catena.FILE_LOOP.read_text(encoding="utf-8")
    stato = catena.carica_stato()
    assert catena.sostituisci_in_loop(testo, catena.rendi_tabella(stato)) == testo, (
        "loop.md è stata modificata a mano: esegui "
        "`uv run python scripts/bmad_chain.py rendi`")


def test_ogni_passo_della_catena_ha_almeno_una_prova():
    """Un passo senza prove sarebbe spuntabile a piacere: il difetto di partenza."""
    senza = [p.chiave for p in catena.CATENA if not p.prove]
    assert senza == [], f"passi senza prova: {senza}"
