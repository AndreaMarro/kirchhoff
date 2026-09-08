"""H5: la via visuale proietta l'evidenza certificata, non la riesegue.

Il motore didattico ha gia' prodotto `TransformExecution` (before, after,
results): la proiezione visuale consuma quegli oggetti certificati e non
decide piu' quale trasformazione e' avvenuta, con quali operandi, qual e'
il dopo o che cosa dice l'equazione. Questi test inchiodano il contratto;
la firma che li fa passare prende l'esecuzione, non operazione+operandi.
"""
from __future__ import annotations

import ast
from fractions import Fraction as F
from pathlib import Path

from kirchhoff.domain.didactic.execute import TransformExecution
from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Request
from kirchhoff.domain.transform import EntityRef
from kirchhoff.domain.truthfulness import Claim
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.risolvi import layout_a_maglia
from kirchhoff.render.layout import LayoutStore, PatchStore
from kirchhoff.render.step import VisualStep, componi
from kirchhoff.render.step import compose as modulo_di_composizione

RADICE = Path(__file__).resolve().parent.parent
ISTANTE = 1_755_000_000_000
ENTROPIA = bytes(range(10))

NETLIST = (
    "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? current R1\n")


def _stato(n: int) -> str:
    return conia("ir", ISTANTE + n, bytes(((n + 101 + j) % 256 for j in range(10))))


def _esecuzione() -> TransformExecution:
    ir = leggi(NETLIST)
    richiesta = next(iter(ir.requests))
    run = orchestrate_didactic_run(
        ir, richiesta,
        state_ids=tuple(_stato(i) for i in range(len(ir.components) + 1)))
    assert isinstance(run, CertifiedDidacticRun)
    assert len(run.transform_executions) == 1
    esecuzione = run.transform_executions[0]
    assert esecuzione.plan.actions[0].kind == "serie"
    return esecuzione


def _proietta(esecuzione: TransformExecution) -> VisualStep:
    esito = componi(
        esecuzione, layout=layout_a_maglia(esecuzione.before),
        layouts=LayoutStore(), patches=PatchStore(),
        istante=ISTANTE + 1_000, casualita=ENTROPIA)
    assert isinstance(esito, VisualStep)
    return esito


def test_h5_1_la_proiezione_non_chiama_transform(monkeypatch):
    """H5-1: a esecuzione certificata esistente, transform puo' esplodere."""
    import kirchhoff.domain.transform.engine as motore
    esecuzione = _esecuzione()

    def esplodi(*a, **k):
        raise AssertionError("la via visuale non riesegue transform")

    monkeypatch.setattr(motore, "transform", esplodi)
    passo = _proietta(esecuzione)
    assert isinstance(passo.fotogrammi[passo.prima], str)


def test_h5_2_il_dopo_visuale_e_il_dopo_certificato(monkeypatch):
    """H5-2: gli IR renderizzati sono gli stessi oggetti certificati."""
    esecuzione = _esecuzione()
    visti: list = []
    vera = modulo_di_composizione.render

    def spia(ir, layout, overlay=None):
        visti.append(ir)
        return vera(ir, layout, overlay)

    monkeypatch.setattr(modulo_di_composizione, "render", spia)
    _proietta(esecuzione)
    assert len(visti) == 2
    assert visti[0] is esecuzione.before
    assert visti[1] is esecuzione.after


def test_h5_3_l_equazione_viene_dal_risultato_certificato():
    """H5-3: equazione, formula e certificato sono gli oggetti della run."""
    esecuzione = _esecuzione()
    passo = _proietta(esecuzione)
    risultato = esecuzione.results[0]
    assert passo.risultato is risultato
    assert passo.giustificazione.formula is risultato.equation
    assert passo.giustificazione.certificato is risultato.certificate
    assert "R1R2eq" in str(passo.giustificazione.formula)


def test_h5_4_i_preservati_restano_stabili():
    """H5-4: l'insieme dei preservati visuali e' quello certificato."""
    esecuzione = _esecuzione()
    passo = _proietta(esecuzione)
    certificati = set(esecuzione.results[0].preserve)
    assert certificati, "la fixture deve avere entita' preservate"
    visuali = {e for e in passo.entita if passo.e_lo_stesso(e)}
    assert visuali == certificati
    assert passo.e_lo_stesso(EntityRef("component", "R1")) is False


def test_h5_5_il_render_non_crea_claim():
    """H5-5: proiettare non certifica niente di nuovo."""
    esecuzione = _esecuzione()
    passo = _proietta(esecuzione)
    assert not isinstance(passo.risultato, Claim)
    for campo in ("operation", "prima", "dopo", "patch", "risultato"):
        assert not isinstance(getattr(passo, campo), Claim)


def test_h5_6_un_difetto_del_renderer_e_failure_non_claim(monkeypatch):
    """H5-6: se il disegno si rompe, e' un guasto visuale, mai un Claim."""
    esecuzione = _esecuzione()

    def rotto(*a, **k):
        raise ValueError("filo attraverso un nodo")

    monkeypatch.setattr(modulo_di_composizione, "render", rotto)
    esito = componi(
        esecuzione, layout=layout_a_maglia(esecuzione.before),
        layouts=LayoutStore(), patches=PatchStore(),
        istante=ISTANTE + 1_000, casualita=ENTROPIA)
    assert isinstance(esito, Failure)
    assert esito.dove == "render"
    assert not isinstance(esito, Claim)


def test_h5_il_render_non_nomina_transform():
    """H5 strutturale: nessuna chiamata a transform() sotto render/."""
    albero = ast.parse(
        (RADICE / "src" / "kirchhoff" / "render" / "step" / "compose.py")
        .read_text(encoding="utf-8"))
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Call):
            nome = None
            if isinstance(nodo.func, ast.Name):
                nome = nodo.func.id
            elif isinstance(nodo.func, ast.Attribute):
                nome = nodo.func.attr
            assert nome != "transform", "render riesegue transform"
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.ImportFrom) and nodo.module and \
                nodo.module.endswith("domain.transform"):
            importati = {alias.name for alias in nodo.names}
            assert "transform" not in importati, "transform importato in render"


def test_h5_7_proiezione_senza_evidenza_e_failure():
    """Chi proietta senza esecuzione certificata riceve un guasto nominato."""
    from kirchhoff.pipeline.failure import Failure
    esito = componi(
        object(), layout=layout_a_maglia(leggi(NETLIST)),
        layouts=LayoutStore(), patches=PatchStore(),
        istante=ISTANTE + 1_000, casualita=ENTROPIA)
    assert isinstance(esito, Failure)
    assert esito.dove == "render"
