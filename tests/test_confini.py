"""Il confine di dipendenza dello spine, verificato invece che ricordato.

`domain/` non importa nulla del progetto fuori da sé. Finora era una regola che
qualcuno controllava con un `grep` quando se ne ricordava — e un `grep` non vede
`import kirchhoff.adapters as a`, non vede `from kirchhoff import ports`, e
soprattutto non gira quando nessuno lo lancia.

Questi test fanno girare il controllo dentro la suite: un'infrazione fa fallire i
test, che è ciò che "blocca la fusione" significa in un progetto senza pipeline.
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "src" / "kirchhoff"
DIRECTORY_SPINE = ("domain", "ports", "adapters", "pipeline", "api", "render", "eval")
LAB_IMPORTS = frozenset({
    "hypothesis",
    "mutmut",
    "cosmic_ray",
    "networkx",
    "lcapy",
    "sympy",
    "schemdraw",
    "spqrtree",
    "crosshair",
})


def _carica_controllo():
    percorso = RADICE / "scripts" / "check_boundaries.py"
    spec = importlib.util.spec_from_file_location("check_boundaries", percorso)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["check_boundaries"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


confini = _carica_controllo()


def test_le_sette_directory_dello_spine_sono_pacchetti():
    for nome in DIRECTORY_SPINE:
        d = SORGENTE / nome
        assert d.is_dir(), f"manca la directory {nome}/"
        assert (d / "__init__.py").exists(), f"{nome}/ non e' un pacchetto inizializzato"
        importlib.import_module(f"kirchhoff.{nome}")


def test_il_dominio_reale_e_pulito():
    """Il gate, sull'albero vero. Se un giorno fallisce, ha ragione lui."""
    assert confini.violazioni(SORGENTE) == []


def test_il_dominio_non_importa_strumenti_del_laboratorio():
    """P1-M0: gli oracoli esterni restano fuori dalla semantica proprietaria."""
    trovati: list[tuple[Path, str]] = []
    for percorso in (SORGENTE / "domain").rglob("*.py"):
        albero = ast.parse(percorso.read_text(encoding="utf-8"), filename=str(percorso))
        for nodo in ast.walk(albero):
            if isinstance(nodo, ast.Import):
                moduli = (alias.name for alias in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module is not None:
                moduli = (nodo.module,)
            else:
                continue
            for modulo in moduli:
                if modulo.split(".", 1)[0].lower() in LAB_IMPORTS:
                    trovati.append((percorso.relative_to(SORGENTE), modulo))

    assert trovati == []


def test_import_relativo_verso_ports_rilevato(tmp_path: Path):
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "colpevole.py").write_text(
        "from ..ports.clock import ClockPort\n", encoding="utf-8")

    trovate = confini.violazioni(tmp_path / "kirchhoff")
    assert len(trovate) == 1
    assert trovate[0].modulo_importato == "kirchhoff.ports.clock"


def test_import_assoluto_verso_adapters_rilevato(tmp_path: Path):
    """Un `grep` su `from ..adapters` non vedrebbe questa forma."""
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "furbo.py").write_text(
        "import kirchhoff.adapters as a\n"
        "from kirchhoff import pipeline\n", encoding="utf-8")

    trovate = confini.violazioni(tmp_path / "kirchhoff")
    importati = {v.modulo_importato for v in trovate}
    assert importati == {"kirchhoff.adapters", "kirchhoff.pipeline"}


def test_la_libreria_standard_e_gli_import_interni_sono_ammessi(tmp_path: Path):
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "onesto.py").write_text(
        "from fractions import Fraction\n"
        "import json\n"
        "from .ir import IR\n"
        "from kirchhoff.domain.mna import solve_dc\n", encoding="utf-8")

    assert confini.violazioni(tmp_path / "kirchhoff") == []


def test_il_messaggio_nomina_file_riga_e_import(tmp_path: Path):
    """Un controllo che dice solo 'fallito' costringe a rifare l'indagine che ha gia' fatto."""
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "colpevole.py").write_text(
        "from fractions import Fraction\n"
        "\n"
        "from ..adapters.openai import Modello\n", encoding="utf-8")

    v = confini.violazioni(tmp_path / "kirchhoff")[0]
    messaggio = confini.descrivi(v)
    assert "colpevole.py" in messaggio
    assert ":3" in messaggio
    assert "kirchhoff.adapters.openai" in messaggio


def test_un_file_illeggibile_non_passa_in_silenzio(tmp_path: Path):
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "rotto.py").write_text("def (((\n", encoding="utf-8")

    with pytest.raises(SyntaxError):
        confini.violazioni(tmp_path / "kirchhoff")


def test_il_controllo_esce_zero_sull_albero_vero():
    assert confini.main([str(SORGENTE)]) == 0


def test_il_controllo_esce_uno_quando_trova_una_violazione(tmp_path: Path, capsys):
    dominio = tmp_path / "kirchhoff" / "domain"
    dominio.mkdir(parents=True)
    (tmp_path / "kirchhoff" / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "__init__.py").write_text("", encoding="utf-8")
    (dominio / "colpevole.py").write_text("from ..ports import clock\n", encoding="utf-8")

    assert confini.main([str(tmp_path / "kirchhoff")]) == 1
    uscita = capsys.readouterr().out
    assert "colpevole.py" in uscita and "kirchhoff.ports" in uscita


def test_una_radice_sbagliata_non_dichiara_tutto_pulito(tmp_path: Path):
    """Il modo peggiore di fallire per un gate: puntato altrove, e sembra verde."""
    with pytest.raises(FileNotFoundError, match="nessuna directory"):
        confini.violazioni(tmp_path / "non-esiste")
