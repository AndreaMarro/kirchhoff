"""Story 1.3 — il `LayoutIR` e il registro append-only di `render/layout`.

AD-8 v2.1: *«un `LayoutIR` per nodo del `ProofGraph`, append-only, mai sovrascritto
per la durata della `ProofSession`»*. Qui si verifica la ritenzione; la relazione
nodo ↔ layout sta in `test_proof.py`.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.identity import conia, genere_di
from kirchhoff.domain.transform import EntityRef, LayoutPatch
from kirchhoff.render.layout import LayoutIR, LayoutStore, PatchStore, Placement

F = Fraction
C = lambda i: EntityRef("component", i)      # noqa: E731
N = lambda i: EntityRef("node", i)           # noqa: E731

ENTROPIA = bytes(range(10))


def _layout(istante: int, *piazzamenti: Placement) -> LayoutIR:
    scelti = piazzamenti or (Placement(C("R1"), F(0), F(0)),)
    return LayoutIR.nuovo(scelti, istante=istante, casualita=ENTROPIA)


# --- Placement ---------------------------------------------------------------

def test_un_piazzamento_nomina_un_entita_non_una_stringa():
    """`component:R1` e `node:R1` sono due entita' diverse."""
    with pytest.raises(TypeError, match="invece di EntityRef"):
        Placement("R1", F(0), F(0))  # type: ignore[arg-type]


@pytest.mark.parametrize("coordinate", [(0.5, F(0)), (F(0), 0.5), (0, F(0))])
def test_un_piazzamento_rifiuta_una_coordinata_che_non_e_una_frazione(coordinate):
    """VCER confronta due posizioni per decidere se il prodotto continua a
    esistere: un float ci porterebbe dentro rumore binario."""
    with pytest.raises(TypeError, match="serve una Fraction"):
        Placement(C("R1"), *coordinate)


def test_due_piazzamenti_della_stessa_entita_in_posti_diversi_sono_diversi():
    assert Placement(C("R1"), F(0), F(0)) != Placement(C("R1"), F(1), F(0))


# --- LayoutIR ----------------------------------------------------------------

def test_un_layout_ha_un_identificatore_col_prefisso_delle_convenzioni():
    """`Consistency Conventions` v2.1: `lay_` per il `LayoutIR`."""
    assert _layout(1).identifier.startswith("lay_")


def test_un_layout_rifiuta_un_identificatore_di_un_altro_genere():
    with pytest.raises(ValueError, match="atteso il prefisso 'lay_'"):
        LayoutIR(conia("ir", 1, ENTROPIA), (Placement(C("R1"), F(0), F(0)),))


def test_un_layout_rifiuta_un_piazzamento_che_non_e_un_piazzamento():
    with pytest.raises(TypeError, match="invece di Placement"):
        LayoutIR(conia("lay", 1, ENTROPIA), ((C("R1"), F(0), F(0)),))  # type: ignore[arg-type]


def test_un_layout_senza_piazzamenti_non_e_uno_stato_visuale():
    """Conservarlo darebbe a VCER un operando su cui ogni confronto riesce."""
    with pytest.raises(ValueError, match="senza alcun piazzamento"):
        LayoutIR(conia("lay", 1, ENTROPIA), ())


def test_un_layout_rifiuta_due_posizioni_per_la_stessa_entita():
    """Renderebbero `p_k(x)` ambiguo, e VCER lo legge come operando."""
    with pytest.raises(ValueError, match="piazzata piu' di una volta"):
        LayoutIR(conia("lay", 1, ENTROPIA),
                 (Placement(C("R1"), F(0), F(0)), Placement(C("R1"), F(9), F(9))))


def test_l_ordine_dei_piazzamenti_e_canonico():
    """Due layout che l'ordine d'ingresso faceva sembrare diversi sono uguali."""
    uno = LayoutIR.nuovo((Placement(C("R2"), F(1), F(0)), Placement(C("R1"), F(0), F(0))),
                         istante=1, casualita=ENTROPIA)
    due = LayoutIR.nuovo((Placement(C("R1"), F(0), F(0)), Placement(C("R2"), F(1), F(0))),
                         istante=1, casualita=ENTROPIA)
    assert uno == due
    assert uno.placements == due.placements


def test_nuovo_conia_un_ulid_ordinabile_nel_tempo():
    """Il layout ha un orologio — a differenza del produttore del `LayoutPatch` —
    quindi due stati visuali identici restano due."""
    prima = _layout(1_000)
    dopo = _layout(2_000)
    assert prima.identifier != dopo.identifier
    assert prima.identifier < dopo.identifier
    assert prima.placements == dopo.placements


def test_posizione_e_la_p_k_di_sm14():
    layout = LayoutIR.nuovo(
        (Placement(C("R1"), F(0), F(0)), Placement(N("b"), F(1, 2), F(3))),
        istante=1, casualita=ENTROPIA)
    assert layout.posizione(N("b")) == Placement(N("b"), F(1, 2), F(3))


def test_posizione_di_un_entita_non_piazzata_solleva():
    with pytest.raises(KeyError):
        _layout(1).posizione(C("MaiPiazzata"))


def test_entita_e_il_dominio_su_cui_p_k_e_definita():
    layout = LayoutIR.nuovo(
        (Placement(C("R1"), F(0), F(0)), Placement(N("b"), F(1), F(1))),
        istante=1, casualita=ENTROPIA)
    assert layout.entita() == {C("R1"), N("b")}


def test_un_layout_non_porta_l_identificatore_del_proprio_nodo():
    """AD-8 v2.1 scrive la relazione **una volta sola**, sul nodo. Scriverla ai due
    capi sarebbe E-62 su una relazione che deve reggere un gate."""
    assert tuple(LayoutIR.__slots__) == ("identifier", "placements")


# --- LayoutStore: la ritenzione ----------------------------------------------

def test_un_layout_depositato_si_risolve_identico():
    registro = LayoutStore()
    layout = _layout(1)
    assert registro.deposita(layout) == layout.identifier
    assert registro.risolvi(layout.identifier) == layout


def test_depositare_due_volte_lo_stesso_identificatore_solleva():
    """Append-only: una sovrascrittura idempotente sarebbe indistinguibile da un
    identificatore coniato due volte, che e' un difetto vero."""
    registro = LayoutStore()
    layout = _layout(1)
    registro.deposita(layout)
    with pytest.raises(ValueError, match="e' gia' depositato"):
        registro.deposita(layout)


def test_depositare_un_contenuto_diverso_sullo_stesso_identificatore_lo_dice():
    """E' il caso peggiore: il deposito perderebbe `p_k` nel momento in cui serve
    misurarlo — CV6 alla lettera — e il messaggio lo nomina."""
    registro = LayoutStore()
    registro.deposita(_layout(1, Placement(C("R1"), F(0), F(0))))
    with pytest.raises(ValueError, match="Il contenuto per giunta differisce"):
        registro.deposita(_layout(1, Placement(C("R1"), F(9), F(9))))


def test_il_registro_conserva_stati_visuali_e_non_altro():
    with pytest.raises(TypeError, match="invece di LayoutIR"):
        LayoutStore().deposita("lay_" + "0" * 26)  # type: ignore[arg-type]


def test_risolvere_un_identificatore_mai_depositato_elenca_cio_che_c_e():
    """Un vuoto che somiglia a una misura e' il difetto che l'error ledger
    ricorda: qui il messaggio dice che cosa il registro contiene davvero."""
    registro = LayoutStore()
    registro.deposita(_layout(1))
    with pytest.raises(KeyError, match="lay_"):
        registro.risolvi("lay_" + "0" * 26)


def test_il_registro_vuoto_lo_dice_invece_di_tacere():
    with pytest.raises(KeyError, match="nessuno"):
        LayoutStore().risolvi("lay_" + "0" * 26)


def test_il_registro_si_conta_e_si_interroga_per_appartenenza():
    registro = LayoutStore()
    primo, secondo = _layout(1), _layout(2)
    registro.deposita(primo)
    registro.deposita(secondo)
    assert len(registro) == 2
    assert primo.identifier in registro
    assert "lay_" + "0" * 26 not in registro
    assert registro.identificatori() == (primo.identifier, secondo.identifier)


def test_i_piazzamenti_di_lay_k_non_cambiano_quando_si_deposita_lay_successivo():
    """AC1 misurato **sui piazzamenti**, non sull'identificatore.

    Un registro che riscrivesse le coordinate dei layout gia' depositati lasciando
    intatti `lay_` ed entita' e' precisamente il caso di CV6 — `p_k` esiste ma non e'
    piu' quello di prima — e passerebbe ogni altro test di questo file, che confronta
    identificatori e insiemi di entita'. Qui si confrontano le posizioni.
    """
    registro = LayoutStore()
    prima = _layout(1, Placement(C("R1"), F(0), F(0)), Placement(N("b"), F(1), F(2)))
    registro.deposita(prima)
    atteso = prima.placements

    registro.deposita(_layout(2, Placement(C("R1"), F(7), F(7)),
                              Placement(N("b"), F(8), F(9))))

    recuperato = registro.risolvi(prima.identifier)
    assert recuperato.placements == atteso
    assert recuperato.posizione(C("R1")) == Placement(C("R1"), F(0), F(0))
    assert recuperato is prima


def test_lo_stato_visuale_recuperato_regge_a_una_catena_di_depositi():
    """Non solo il deposito immediatamente successivo: `p_0` va confrontato con
    `p_n`, e la ritenzione vale per tutta la sessione (AD-8 v2.1)."""
    registro = LayoutStore()
    primo = _layout(1, Placement(C("R1"), F(0), F(0)))
    registro.deposita(primo)
    for k in range(2, 8):
        registro.deposita(_layout(k, Placement(C("R1"), F(k), F(k))))
    assert registro.risolvi(primo.identifier).placements == primo.placements


# --- PatchStore: il terzo operando di CV6 ------------------------------------

def _patch(*, preserve=(), remove=(), create=(), scope=None) -> LayoutPatch:
    return LayoutPatch(preserve, remove, create,
                       scope if scope is not None else (C("R1"),))


def test_una_patch_depositata_si_risolve_identica():
    registro = PatchStore()
    patch = _patch(preserve=(C("R1"),))
    identificatore = registro.deposita(patch, istante=1, casualita=ENTROPIA)
    assert registro.risolvi(identificatore) == patch


def test_il_patch_e_un_ulid_col_prefisso_delle_convenzioni():
    """«ULID con prefisso per tipo … `patch_`». Non un'impronta del contenuto: le
    convenzioni dicono ULID, e un ULID porta dentro l'istante."""
    registro = PatchStore()
    presto = registro.deposita(_patch(preserve=(C("R1"),)), istante=1_000,
                               casualita=ENTROPIA)
    tardi = registro.deposita(_patch(preserve=(C("R2"),)), istante=2_000,
                              casualita=ENTROPIA)
    assert genere_di(presto) == genere_di(tardi) == "patch"
    assert presto < tardi


def test_un_patch_identifica_un_passo_e_non_un_contenuto():
    """La proprieta' che SM-14 richiede: due passi che emettono patch identiche
    ricevono due nomi, quindi il denominatore di VCER conta due passi e un'evidenza
    puo' dire di quale arco parla."""
    registro = PatchStore()
    stessa = _patch(preserve=(C("R1"),))
    uno = registro.deposita(stessa, istante=1, casualita=ENTROPIA)
    due = registro.deposita(stessa, istante=2, casualita=ENTROPIA)
    assert uno != due
    assert registro.risolvi(uno) == registro.risolvi(due) == stessa
    assert len(registro) == 2


def test_da_una_patch_depositata_si_legge_il_dominio_di_p_k():
    """E' la ragione per cui il registro esiste: senza `preserve`, `p_{k+1}(x) ≈
    p_k(x)` non ha le `x` su cui valutarsi."""
    registro = PatchStore()
    identificatore = registro.deposita(
        _patch(preserve=(C("R1"), N("b"))), istante=1, casualita=ENTROPIA)
    assert registro.risolvi(identificatore).preserve == (C("R1"), N("b"))


def test_due_depositi_con_lo_stesso_istante_e_la_stessa_entropia_sollevano():
    """A entropia costante due conii nello stesso millisecondo collidono, e
    accettarlo perderebbe la patch di uno dei due passi."""
    registro = PatchStore()
    registro.deposita(_patch(preserve=(C("R1"),)), istante=1, casualita=ENTROPIA)
    with pytest.raises(ValueError, match="entropia nuova a ogni chiamata"):
        registro.deposita(_patch(preserve=(C("R2"),)), istante=1, casualita=ENTROPIA)


def test_il_registro_delle_patch_conserva_patch_e_non_altro():
    with pytest.raises(TypeError, match="invece di LayoutPatch"):
        PatchStore().deposita("patch_" + "0" * 26, istante=1,  # type: ignore[arg-type]
                              casualita=ENTROPIA)


def test_risolvere_una_patch_mai_depositata_elenca_cio_che_c_e():
    registro = PatchStore()
    registro.deposita(_patch(preserve=(C("R1"),)), istante=1, casualita=ENTROPIA)
    with pytest.raises(KeyError, match="patch_"):
        registro.risolvi("patch_" + "0" * 26)


def test_il_registro_delle_patch_si_conta_e_si_interroga_per_appartenenza():
    registro = PatchStore()
    uno = registro.deposita(_patch(preserve=(C("R1"),)), istante=1, casualita=ENTROPIA)
    due = registro.deposita(_patch(preserve=(C("R2"),)), istante=2, casualita=ENTROPIA)
    assert len(registro) == 2
    assert uno in registro and "patch_" + "0" * 26 not in registro
    assert registro.identificatori() == (uno, due)


def test_il_registro_delle_patch_non_conia_dall_orologio_di_sistema():
    """L'istante entra dalla firma (AD-17). Senza, un replay non e' riproducibile."""
    with pytest.raises(TypeError):
        PatchStore().deposita(_patch(preserve=(C("R1"),)))  # type: ignore[call-arg]
