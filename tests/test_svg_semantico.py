"""Story 1.4 — l'SVG semantico deterministico, su una fixture a soli resistori.

AD-35: *«stessi ingressi, stessi byte ... nessun ordinamento che dipenda
dall'ordine d'inserimento in una mappa»*. AD-31: *«l'annotazione e' derivata dalla
geometria, mai il contrario»*. AD-10: l'SVG verificato e' la sorgente unica.
UX-DR25 e FR-15: ogni disegno porta l'alternativa testuale della **topologia**.

La fixture e' quella che la storia prescrive — soli resistori piu' un generatore,
`LayoutIR` **predefinito**: nessun autolayout, che e' non-goal dichiarato.
"""

from __future__ import annotations

import ast
import xml.etree.ElementTree as ET
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest

from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import IR, Component, Magnitude
from kirchhoff.domain.transform import EntityRef
from kirchhoff.eval import reference_set
from kirchhoff.render.layout import LayoutIR, Placement
from kirchhoff.render.serialize import Punto, Simbolo, Terminale, render, scena
from kirchhoff.render.serialize.geometry import FORME, Filo, Giunzione
from kirchhoff.render.serialize.svg import (
    CORPO_TESTO,
    _CLASSI,
    _numero,
    _riquadro_del_testo,
    _scritte,
    _verifica_corpi,
    alternativa_testuale,
)

SVG = "{http://www.w3.org/2000/svg}"
ENTROPIA = bytes(range(10))
ISTANTE = 1_755_000_000_000

C = lambda i: EntityRef("component", i)      # noqa: E731
N = lambda i: EntityRef("node", i)           # noqa: E731


# --- la fixture: tre bipoli su una maglia, posizioni date --------------------

def _circuito(*componenti: Component, nodi: tuple[str, ...] = ("0", "a", "b")) -> IR:
    return IR("1.0.0", "dc_resistive", "netlist", nodi, componenti, ())


CIRCUITO = _circuito(
    Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
    Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
    Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
)

PIAZZAMENTI = (
    Placement(N("b"), F(0), F(0)),
    Placement(N("a"), F(200), F(0)),
    Placement(N("0"), F(100), F(160)),
    Placement(C("V1"), F(0), F(80)),
    Placement(C("R1"), F(100), F(0)),
    Placement(C("R2"), F(200), F(80)),
)


def _layout(piazzamenti=PIAZZAMENTI, istante: int = ISTANTE) -> LayoutIR:
    return LayoutIR.nuovo(piazzamenti, istante=istante, casualita=ENTROPIA)


LAYOUT = _layout()
SCENA = scena(CIRCUITO, LAYOUT)


def _albero(testo: str) -> ET.Element:
    return ET.fromstring(testo)


def _con(radice: ET.Element, tag: str, attributo: str) -> list[ET.Element]:
    return [e for e in radice.iter(f"{SVG}{tag}") if attributo in e.attrib]


# --- AC1 · stesso `LayoutIR`, stessi byte ------------------------------------

def test_due_rendering_dello_stesso_layout_danno_gli_stessi_byte():
    """Il criterio, alla lettera: *«si renderizza due volte, i byte coincidono»*."""
    assert render(CIRCUITO, LAYOUT) == render(CIRCUITO, LAYOUT)


def test_l_ordine_di_inserimento_non_cambia_un_byte():
    """AD-35: *«nessun ordinamento che dipenda dall'ordine d'inserimento in una mappa»*.

    E' l'oracolo che la storia prescrive. Elencare gli stessi componenti, gli stessi
    nodi e gli stessi piazzamenti in un altro ordine descrive **lo stesso** stato
    visuale: se i byte cambiano, da qualche parte l'ordine di emissione viene
    dall'ordine in cui qualcosa e' stato inserito, non da una chiave dichiarata.

    Il rosso si ottiene sostituendo, in `geometry.scena()`, il `sorted` sui
    componenti con una scansione di un dizionario costruito lungo `circuito.components`.
    """
    rovesciato = IR("1.0.0", "dc_resistive", "netlist",
                    tuple(reversed(CIRCUITO.nodes)),
                    tuple(reversed(CIRCUITO.components)), ())
    assert render(rovesciato, _layout(tuple(reversed(PIAZZAMENTI)))) \
        == render(CIRCUITO, LAYOUT)


def test_il_disegno_non_dipende_da_quando_e_stato_chiesto():
    """Niente orologio: due layout coniati in istanti diversi differiscono solo
    per il `lay_` che portano, e quello e' un ingresso, non un'ora di lettura."""
    altro = _layout(istante=ISTANTE + 86_400_000)
    assert render(CIRCUITO, LAYOUT).replace(LAYOUT.identifier, "X") \
        == render(CIRCUITO, altro).replace(altro.identifier, "X")


#: Moduli da cui `render/serialize` non puo' dipendere senza smettere di essere
#: puro: i primi quattro sono l'orologio e la casualita' che AD-35 nomina, `os` ci
#: sta per `os.urandom` e `os.environ`, che sono entropia presa fuori dalla firma.
VIETATI_DA_AD_35 = frozenset({"time", "datetime", "random", "uuid", "secrets", "os"})


def _moduli_importati(albero: ast.AST) -> set[str]:
    """I pacchetti di primo livello che un modulo tira dentro. Gli import relativi
    sono interni al progetto e non ci riguardano."""
    nomi: set[str] = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            nomi |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and not nodo.level and nodo.module:
            nomi.add(nodo.module.split(".")[0])
    return nomi


def test_render_non_ha_orologio_ne_casualita_fra_le_dipendenze():
    """AD-35 vieta orologio, id a runtime e casualita' senza seme fra gli ingressi.

    Il gate si installa nella stessa iterazione che lo scopre: il memlog dello spine
    annota *«src/ contiene import random e import time ... e' il primo posto dove
    guardare quando AD-35 diventa un test»*. Adesso lo e'.

    Letto sull'albero sintattico e non col testo, per la ragione che
    `check_boundaries.py` gia' scrive: un'espressione regolare non distingue un
    import da un docstring che lo nomina per spiegare perche' non c'e', e un gate
    che accusa il commento che lo documenta e' peggio di nessun gate.
    """
    radice = Path(__file__).resolve().parent.parent / "src/kirchhoff/render/serialize"
    sorgenti = sorted(radice.glob("*.py"))

    # Il glob e' costruito a mano: su una cartella rinominata o spostata sarebbe
    # vuoto, il ciclo non eseguirebbe alcun assert e QUESTO GATE PASSEREBBE SENZA
    # AVER LETTO UN FILE. Un gate che diventa verde perche' non ha guardato e'
    # peggio di nessun gate: dichiara una garanzia che nessuno sta piu' dando.
    assert sorgenti, (
        f"nessun sorgente in {radice}: il gate di AD-35 non ha letto nulla e "
        "sarebbe passato a vuoto. Se la cartella e' stata spostata, aggiorna qui "
        "il percorso — non cancellare l'asserzione.")

    for file in sorgenti:
        albero = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        trovati = sorted(_moduli_importati(albero) & VIETATI_DA_AD_35)
        assert not trovati, f"{file.name}: {trovati}"


# --- AC2 · le annotazioni di identita' ---------------------------------------

def test_ogni_componente_porta_il_proprio_data_component_id():
    radice = _albero(render(CIRCUITO, LAYOUT))
    gruppi = _con(radice, "g", "data-component-id")
    assert sorted(g.get("data-component-id") for g in gruppi) == ["R1", "R2", "V1"]
    assert [g.get("data-component-type") for g in gruppi] \
        == ["resistor", "resistor", "voltage_source_dc"]


def test_ogni_nodo_porta_il_proprio_data_node_id():
    radice = _albero(render(CIRCUITO, LAYOUT))
    giunzioni = _con(radice, "circle", "data-node-id")
    assert sorted(g.get("data-node-id") for g in giunzioni) == ["0", "a", "b"]


def test_ogni_morsetto_porta_gli_attributi_data_terminal():
    """Sei morsetti, tre attributi ciascuno: componente, indice, nodo.

    L'indice non e' decorazione: `mna.py` prende la tensione come
    `v(terminals[0]) - v(terminals[1])`, quindi su un generatore **e'** la polarita'.
    """
    radice = _albero(render(CIRCUITO, LAYOUT))
    morsetti = _con(radice, "circle", "data-terminal-component")
    assert sorted((m.get("data-terminal-component"), m.get("data-terminal-index"),
                   m.get("data-terminal-node")) for m in morsetti) == [
        ("R1", "0", "b"), ("R1", "1", "a"),
        ("R2", "0", "a"), ("R2", "1", "0"),
        ("V1", "0", "b"), ("V1", "1", "0"),
    ]


def test_i_layer_emessi_sono_quelli_di_ad_23_e_solo_quelli():
    """AD-23 fissa la scala `0…8`. Questa storia popola 2, 3 e 4; i layer della
    trasformazione restano **non emessi**, non emessi vuoti."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    assert [g.get("data-layer") for g in radice.findall(f"{SVG}g")] == ["2", "3", "4"]


# --- AC3 · l'identita' e' derivata dalla geometria emessa ---------------------

def test_ogni_filo_tocca_il_morsetto_che_dichiara_di_toccare():
    """AD-31, letta sui byte usciti e non sulle strutture interne.

    E' il difetto che il gate del 15 agosto ha chiamato il piu' grave: *«un filo
    attaccato al piedino sbagliato, con l'attributo giusto, prende il Badge
    Verificata»*. Qui il confronto e' esatto perche' l'annotazione e il punto hanno
    la stessa origine; la tolleranza dichiarata di AD-31 serve al riparsing (1.6).
    """
    radice = _albero(render(CIRCUITO, LAYOUT))
    morsetti = {(m.get("data-terminal-component"), m.get("data-terminal-index")):
                (m.get("cx"), m.get("cy"))
                for m in _con(radice, "circle", "data-terminal-component")}
    giunzioni = {g.get("data-node-id"): (g.get("cx"), g.get("cy"))
                 for g in _con(radice, "circle", "data-node-id")}
    fili = _con(radice, "polyline", "data-terminal-component")
    assert len(fili) == len(morsetti) == 6
    for filo in fili:
        punti = [tuple(p.split(",")) for p in filo.get("points").split(" ")]
        chiave = (filo.get("data-terminal-component"), filo.get("data-terminal-index"))
        assert punti[0] == morsetti[chiave], chiave
        assert punti[-1] == giunzioni[filo.get("data-terminal-node")], chiave


def test_l_svg_emesso_e_xml_ben_formato():
    """AD-10: e' la sorgente unica di ogni altro formato. Un artefatto che non si
    riparsa non e' la sorgente di niente."""
    assert _albero(render(CIRCUITO, LAYOUT)).tag == f"{SVG}svg"


# --- AC4 · l'alternativa testuale della topologia ----------------------------

def test_la_radice_dichiara_il_titolo_e_la_descrizione_che_possiede():
    """UX-DR25 e FR-15. `role="img"` rende presentazionale il sottoalbero: e' il
    motivo per cui il `<desc>` deve dire tutto."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    assert radice.get("role") == "img"
    titolo, descrizione = radice.find(f"{SVG}title"), radice.find(f"{SVG}desc")
    assert radice.get("aria-labelledby") == titolo.get("id")
    assert radice.get("aria-describedby") == descrizione.get("id")
    assert all(i.endswith(LAYOUT.identifier)
               for i in (titolo.get("id"), descrizione.get("id")))


def test_l_alternativa_descrive_la_topologia_non_il_disegno():
    """*«non "schema del circuito" ma la struttura»*: ogni componente, ogni nodo,
    e chi si incontra dove."""
    _, descrizione = alternativa_testuale(SCENA)
    assert "R1, resistore da 100 ohm, fra il nodo b e il nodo a." in descrizione
    assert "R2, resistore da 220 ohm, fra il nodo a e il nodo 0." in descrizione
    assert "Al nodo a si incontrano R1 e R2." in descrizione
    assert "il nodo di riferimento è 0." in descrizione


def test_l_alternativa_dice_la_polarita_del_generatore():
    """`canonical.py`: l'ordine dei terminali di un generatore *«e' la polarita'»*, e
    riordinarlo *«produrrebbe un circuito diverso che si dichiara uguale»*. Uno
    studente cieco riceverebbe quel circuito diverso."""
    _, descrizione = alternativa_testuale(SCENA)
    assert ("V1, generatore di tensione continua da 12 volt, col morsetto positivo "
            "al nodo b e il negativo al nodo 0.") in descrizione


def test_un_generatore_di_valore_negativo_ha_la_polarita_rovesciata():
    circuito = _circuito(
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(-12), "V1"),
        Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
    )
    _, descrizione = alternativa_testuale(scena(circuito, LAYOUT))
    assert ("V1, generatore di tensione continua da -12 volt, col morsetto positivo "
            "al nodo 0 e il negativo al nodo b.") in descrizione


def test_un_generatore_spento_non_dichiara_una_polarita_che_non_ha():
    circuito = _circuito(
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(0), "V1"),
        Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
    )
    _, descrizione = alternativa_testuale(scena(circuito, LAYOUT))
    assert "col primo morsetto al nodo b e il secondo al nodo 0." in descrizione


def test_l_alternativa_nomina_anche_i_nodi_poco_frequentati():
    """Un nodo isolato e un nodo con un solo bipolo restano nella descrizione: un
    nodo taciuto e' una topologia diversa."""
    circuito = _circuito(Component.of("R1", "resistor", ("0", "a"), F(47), "R1"),
                         nodi=("0", "a", "z"))
    layout = _layout((Placement(N("0"), F(0), F(0)), Placement(N("a"), F(100), F(0)),
                      Placement(N("z"), F(50), F(90)),
                      Placement(C("R1"), F(50), F(0))))
    _, descrizione = alternativa_testuale(scena(circuito, layout))
    assert "Al nodo 0 arriva solo R1." in descrizione
    assert "Al nodo z non arriva nessun componente." in descrizione


def test_una_scena_senza_nodo_di_riferimento_lo_dice_invece_di_tacerlo():
    """`IR` impone il nodo di riferimento, quindi `scena()` non produce mai questo
    caso; `Scena` e' pero' pubblica, e un'alternativa che tacesse sarebbe peggio."""
    senza = replace(SCENA, giunzioni=tuple(replace(g, riferimento=False)
                                           for g in SCENA.giunzioni))
    _, descrizione = alternativa_testuale(senza)
    assert "nessun nodo di riferimento." in descrizione


# --- la geometria: l'asse e il percorso, dedotti e non inventati --------------

def test_l_asse_di_un_bipolo_viene_dai_nodi_a_cui_e_attaccato():
    """Il `LayoutIR` non porta un orientamento e questa storia non ha autolayout:
    l'asse si legge dalla geometria gia' data."""
    per_nome = {s.componente: s for s in SCENA.simboli}
    assert per_nome["R1"].orizzontale
    assert not per_nome["V1"].orizzontale
    assert per_nome["R1"].terminali[0].punto == Punto(F(76), F(0))


def test_il_filo_esce_lungo_l_asse_e_poi_chiude_a_squadra():
    circuito = _circuito(Component.of("R1", "resistor", ("0", "a"), F(47), "R1"),
                         nodi=("0", "a"))
    layout = _layout((Placement(N("0"), F(0), F(0)), Placement(N("a"), F(100), F(40)),
                      Placement(C("R1"), F(50), F(0))))
    percorsi = {(f.componente, f.indice): f.punti for f in scena(circuito, layout).fili}
    assert percorsi[("R1", 0)] == (Punto(F(26), F(0)), Punto(F(0), F(0)))
    assert percorsi[("R1", 1)] == (Punto(F(74), F(0)), Punto(F(100), F(0)),
                                   Punto(F(100), F(40)))


def test_due_nodi_nello_stesso_punto_non_danno_un_asse():
    layout = _layout((Placement(N("0"), F(0), F(0)), Placement(N("a"), F(0), F(0)),
                      Placement(C("R1"), F(50), F(0))))
    with pytest.raises(ValueError, match="non esiste un asse"):
        scena(_circuito(Component.of("R1", "resistor", ("0", "a"), F(47), "R1"),
                        nodi=("0", "a")), layout)


@pytest.mark.parametrize("mancante", [C("R1"), N("a")])
def test_una_posizione_mancante_si_dichiara_invece_di_inventarla(mancante):
    parziali = tuple(p for p in PIAZZAMENTI if p.entity != mancante)
    with pytest.raises(ValueError, match="non e' piazzata"):
        scena(CIRCUITO, _layout(parziali))


def test_un_layout_di_un_altro_circuito_non_si_disegna():
    """Disegnerebbe un circuito che nessuno ha verificato."""
    with pytest.raises(ValueError, match="che questo circuito non ha"):
        scena(CIRCUITO, _layout((*PIAZZAMENTI, Placement(C("C9"), F(9), F(9)))))


# --- le guardie di `Scena`: coerenti per costruzione o non costruite ---------

def test_una_scena_vuole_un_identificatore_di_layout():
    with pytest.raises(ValueError, match="atteso il prefisso 'lay_'"):
        replace(SCENA, layout=conia("ir", ISTANTE, ENTROPIA))


def test_una_scena_senza_simboli_non_e_un_disegno():
    with pytest.raises(ValueError, match="non e' un disegno"):
        replace(SCENA, simboli=(), fili=())


def test_una_scena_rifiuta_due_geometrie_per_lo_stesso_componente():
    with pytest.raises(ValueError, match="componente disegnato piu' di una volta"):
        replace(SCENA, simboli=(SCENA.simboli[0], SCENA.simboli[0]))


def test_una_scena_rifiuta_due_geometrie_per_lo_stesso_nodo():
    with pytest.raises(ValueError, match="nodo disegnato piu' di una volta"):
        replace(SCENA, giunzioni=(SCENA.giunzioni[0], SCENA.giunzioni[0]))


def test_due_nodi_coincidenti_rendono_indistinguibile_cio_che_li_tocca():
    """AD-31, seconda condizione: *«che due terminali distinti non siano coincidenti»*."""
    primo, secondo, *resto = SCENA.giunzioni
    with pytest.raises(ValueError, match="punti coincidenti: nodo"):
        replace(SCENA, giunzioni=(primo, replace(secondo, punto=primo.punto), *resto))


def test_due_morsetti_coincidenti_rendono_ambigua_la_derivazione():
    """Il gemello resta un simbolo coerente — asse e simmetria intatti — e a
    coincidere e' solo il suo primo morsetto con quello di R1."""
    r1, r2, v1 = SCENA.simboli
    gemello = replace(v1, centro=Punto(F(76), F(24)), terminali=(
        replace(v1.terminali[0], punto=Punto(F(76), F(0))),
        replace(v1.terminali[1], punto=Punto(F(76), F(48)))))
    with pytest.raises(ValueError, match="punti coincidenti: morsetto"):
        replace(SCENA, simboli=(r1, r2, gemello))


def test_un_nodo_piazzato_su_un_morsetto_non_e_piu_distinguibile_da_esso():
    """La guardia confrontava i nodi fra loro e i morsetti fra loro, mai gli uni con
    gli altri: un nodo sul morsetto passava, e produceva `points="76,0 76,0"` piu' una
    giunzione di raggio 3 sopra un morsetto di raggio 2."""
    r1 = SCENA.simboli[0]
    giunzioni = tuple(replace(g, punto=r1.terminali[0].punto) if g.nodo == "b" else g
                      for g in SCENA.giunzioni)
    with pytest.raises(ValueError, match="punti coincidenti: nodo b e morsetto R1.0"):
        replace(SCENA, giunzioni=giunzioni)


def test_un_filo_di_un_punto_solo_non_congiunge_nulla():
    primo, *resto = SCENA.fili
    with pytest.raises(ValueError, match="non congiunge nulla"):
        replace(SCENA, fili=(replace(primo, punti=primo.punti[:1]), *resto))


def test_un_filo_che_nomina_un_nodo_diverso_dal_morsetto_e_il_difetto_di_ad_31():
    primo, *resto = SCENA.fili
    with pytest.raises(ValueError, match="il morsetto dichiara"):
        replace(SCENA, fili=(replace(primo, nodo="a" if primo.nodo != "a" else "b"),
                             *resto))


def test_un_filo_che_parte_altrove_dal_morsetto_che_dichiara_e_rifiutato():
    primo, *resto = SCENA.fili
    altrove = (Punto(F(999), F(999)), *primo.punti[1:])
    with pytest.raises(ValueError, match="e' esattamente cio' che AD-31 vieta"):
        replace(SCENA, fili=(replace(primo, punti=altrove), *resto))


def test_un_filo_che_non_arriva_al_nodo_che_dichiara_e_rifiutato():
    primo, *resto = SCENA.fili
    corto = (*primo.punti[:-1], Punto(F(999), F(999)))
    with pytest.raises(ValueError, match="e il nodo b sta in|e il nodo a sta in"):
        replace(SCENA, fili=(replace(primo, punti=corto), *resto))


def test_un_morsetto_senza_filo_sta_in_aria():
    with pytest.raises(ValueError, match="disegnati e non collegati"):
        replace(SCENA, fili=SCENA.fili[1:])


def test_un_filo_su_un_componente_non_disegnato_e_rifiutato():
    primo, *resto = SCENA.fili
    with pytest.raises(ValueError, match="che non e' disegnato"):
        replace(SCENA, fili=(replace(primo, componente="R9"), *resto))


def test_un_filo_su_un_morsetto_che_non_esiste_e_rifiutato():
    primo, *resto = SCENA.fili
    with pytest.raises(ValueError, match="nessun morsetto di indice 5"):
        replace(SCENA, fili=(replace(primo, indice=5), *resto))


def test_un_filo_verso_un_nodo_non_disegnato_e_rifiutato():
    """Il morsetto e il filo concordano — su un nodo che nessuno ha disegnato."""
    primo, *altri = SCENA.simboli
    simbolo = replace(primo, terminali=(replace(primo.terminali[0], nodo="zz"),
                                        primo.terminali[1]))
    fili = tuple(replace(f, nodo="zz")
                 if (f.componente, f.indice) == (primo.componente, 0) else f
                 for f in SCENA.fili)
    with pytest.raises(ValueError, match="verso il nodo zz"):
        replace(SCENA, simboli=(simbolo, *altri), fili=fili)


# --- le guardie di `Punto` e `Simbolo` ---------------------------------------

@pytest.mark.parametrize("coordinate", [(0.5, F(0)), (F(0), 0.5)])
def test_un_punto_rifiuta_una_coordinata_che_non_e_una_frazione(coordinate):
    with pytest.raises(TypeError, match="serve una Fraction"):
        Punto(*coordinate)


def test_un_tipo_senza_simbolo_solleva_invece_di_produrre_un_refusal():
    """Un condensatore senza simbolo non e' un circuito che non si puo' certificare:
    e' un disegno che non abbiamo ancora scritto. Chiamarlo `Refusal` accuserebbe
    lo studente di un difetto nostro."""
    with pytest.raises(ValueError, match="nessun simbolo per un capacitor"):
        Simbolo("C1", "C_1", "capacitor", Magnitude(F(1), "farad"),
                Punto(F(0), F(0)), True,
                (Terminale("C1", 0, "0", Punto(F(-24), F(0))),
                 Terminale("C1", 1, "a", Punto(F(24), F(0)))))


def test_un_simbolo_rifiuta_morsetti_fuori_ordine():
    """Riordinarli su un generatore e' riscriverne la polarita'."""
    with pytest.raises(ValueError, match="invece di \\(0, 1\\)"):
        Simbolo("R1", "R_1", "resistor", Magnitude(F(1), "ohm"),
                Punto(F(0), F(0)), True,
                (Terminale("R1", 1, "a", Punto(F(24), F(0))),
                 Terminale("R1", 0, "0", Punto(F(-24), F(0)))))


def test_un_simbolo_rifiuta_il_morsetto_di_un_altro_componente():
    with pytest.raises(ValueError, match="montato su questo simbolo"):
        Simbolo("R1", "R_1", "resistor", Magnitude(F(1), "ohm"),
                Punto(F(0), F(0)), True,
                (Terminale("R1", 0, "0", Punto(F(-24), F(0))),
                 Terminale("R9", 1, "a", Punto(F(24), F(0)))))


# --- la formattazione dei numeri e le due tavole -----------------------------

@pytest.mark.parametrize("valore,atteso", [
    (F(0), "0"),
    (F(-1, 2), "-0.5"),
    (F(200), "200"),
    (F(1, 3), "0.3333"),
    (F(5, 10 ** 5), "0"),          # 0,5 all'ultima cifra: al pari, verso lo zero
    (F(15, 10 ** 5), "0.0002"),    # 1,5 all'ultima cifra: al pari, verso il due
    (F(-1, 10 ** 9), "0"),         # mai «-0»
])
def test_le_coordinate_si_formattano_con_una_regola_dichiarata(valore, atteso):
    """`round()` su un `Fraction` e' esatto e arrotonda al pari: nessun passaggio da
    `float`, quindi nessuna cifra che dipenda dall'ordine delle somme."""
    assert _numero(valore) == atteso


def test_i_valori_di_componente_restano_esatti_nell_etichetta_e_nel_testo():
    """`_numero` serve alle coordinate; un valore resta la frazione che e'."""
    circuito = _circuito(Component.of("R1", "resistor", ("0", "a"), F(1, 3), "R1"),
                         nodi=("0", "a"))
    layout = _layout((Placement(N("0"), F(0), F(0)), Placement(N("a"), F(100), F(0)),
                      Placement(C("R1"), F(50), F(0))))
    disegno = render(circuito, layout)
    assert 'data-component-value="1/3"' in disegno
    assert "R1, resistore da 1/3 ohm," in disegno


def test_un_tipo_con_ingombro_e_senza_corpo_si_disegnerebbe_come_niente():
    """Due dichiarazioni dello stesso insieme si confrontano all'import (E-62)."""
    with pytest.raises(RuntimeError, match=r"senza corpo \['resistor'\]"):
        _verifica_corpi(FORME, {"voltage_source_dc": None})
    with pytest.raises(RuntimeError, match=r"senza ingombro \['inductor'\]"):
        _verifica_corpi(FORME, {**{k: None for k in FORME}, "inductor": None})


def test_la_scena_espone_le_stesse_entita_del_circuito():
    """`Filo` e `Giunzione` sono pubblici perche' la Story 1.7 comporra' scene."""
    assert {s.componente for s in SCENA.simboli} == {c.id for c in CIRCUITO.components}
    assert {g.nodo for g in SCENA.giunzioni} == set(CIRCUITO.nodes)
    assert all(isinstance(f, Filo) for f in SCENA.fili)
    assert all(isinstance(g, Giunzione) for g in SCENA.giunzioni)


# --- l'ordine dichiarato: verificato, non rattoppato --------------------------

def test_i_fili_escono_nell_ordine_della_chiave_dichiarata():
    """La chiave dei fili — (componente, indice) — sui byte emessi.

    C'era un `sorted` su questa chiave dentro `scena()`, e non era osservabile:
    toglierlo in copia-ombra lasciava verdi tutti e 52 i test, perche' i fili nascono
    gia' ordinati dentro il ciclo sui componenti ordinati. E' stato tolto, e il
    contratto e' passato dove puo' cadere: `Scena._verifica_l_ordine`.
    """
    radice = _albero(render(CIRCUITO, LAYOUT))
    fili = _con(radice, "polyline", "data-terminal-component")
    emesso = [(f.get("data-terminal-component"), f.get("data-terminal-index"))
              for f in fili]
    assert emesso == sorted(emesso)
    assert emesso[0] == ("R1", "0")


@pytest.mark.parametrize("collezione,rovescia", [
    ("simboli", lambda s: tuple(reversed(s.simboli))),
    ("giunzioni", lambda s: tuple(reversed(s.giunzioni))),
    ("fili", lambda s: tuple(reversed(s.fili))),
])
def test_una_collezione_fuori_dall_ordine_dichiarato_e_rifiutata(collezione, rovescia):
    """AD-35: *«ogni collezione si ordina su una chiave dichiarata»*. `Scena` non
    riordina — verifica: riordinare all'ultimo passaggio nasconderebbe l'ordine colato
    da un dizionario invece di farlo vedere."""
    with pytest.raises(ValueError, match=f"{collezione} fuori dall'ordine dichiarato"):
        replace(SCENA, **{collezione: rovescia(SCENA)})


# --- AD-31, terza condizione: nessun filo passa per cio' che non dichiara -----

def test_un_filo_che_passa_per_un_morsetto_che_non_dichiara_e_rifiutato():
    """AD-31: *«nessun filo passi per un terminale che non dichiara di toccare»*.

    Due bipoli in parallelo piazzati sulla stessa retta: il filo che porta R1 al nodo
    `a` attraversa i due morsetti di R2, e il disegno mostra due incidenze che il
    grafo non ha. Nessuna guardia lo vedeva — la scena confrontava gli **estremi** dei
    fili e nient'altro.
    """
    circuito = _circuito(Component.of("R1", "resistor", ("0", "a"), F(47), "R1"),
                         Component.of("R2", "resistor", ("0", "a"), F(47), "R2"),
                         nodi=("0", "a"))
    layout = _layout((Placement(N("0"), F(0), F(0)), Placement(N("a"), F(400), F(0)),
                      Placement(C("R1"), F(100), F(0)),
                      Placement(C("R2"), F(300), F(0))))
    with pytest.raises(ValueError, match="R1.1: il filo passa per morsetto R2.0"):
        scena(circuito, layout)


def test_un_filo_che_passa_per_una_giunzione_che_non_dichiara_e_rifiutato():
    """Stessa condizione, sull'altro genere di punto annotato — ed e' il caso
    misurato: basta un `LayoutIR` che piazzi il centro di R1 fuori dalla campata dei
    suoi nodi perche' i suoi fili tornino indietro attraversando il nodo `a`, il corpo
    e il morsetto opposto. Era accettato."""
    fuori = tuple(Placement(C("R1"), F(300), F(0)) if p.entity == C("R1") else p
                  for p in PIAZZAMENTI)
    with pytest.raises(ValueError, match="R1.0: il filo passa per nodo a"):
        scena(CIRCUITO, _layout(fuori))


def test_due_fili_sullo_stesso_morsetto_sono_due_incidenze_dove_ce_n_e_una():
    """`Filo` e `Scena` sono pubblici perche' la Story 1.7 comporra' scene: un
    morsetto con due fili emette due `<polyline>` con la stessa tripla, e chi riparsa
    in 1.6 conta due incidenze dove il circuito ne ha una."""
    with pytest.raises(ValueError, match="morsetti con piu' di un filo: R1.0"):
        replace(SCENA, fili=tuple(sorted((*SCENA.fili, SCENA.fili[0]),
                                         key=lambda f: (f.componente, f.indice))))


# --- le guardie di `Simbolo` sull'asse ---------------------------------------

def test_un_simbolo_coi_morsetti_fuori_dal_proprio_asse_e_rifiutato():
    """`riquadro()` orienta il corpo su `orizzontale` e `_reoforo` ci attacca il
    tratto: un simbolo che si dichiara orizzontale coi morsetti sopra e sotto disegna
    un corpo ortogonale ai propri reofori."""
    with pytest.raises(ValueError, match="con i morsetti fuori dal proprio asse"):
        Simbolo("R1", "R_1", "resistor", Magnitude(F(1), "ohm"),
                Punto(F(0), F(0)), True,
                (Terminale("R1", 0, "a", Punto(F(0), F(-24))),
                 Terminale("R1", 1, "b", Punto(F(0), F(24)))))


def test_un_simbolo_coi_morsetti_non_simmetrici_e_rifiutato():
    with pytest.raises(ValueError, match="non simmetrici rispetto al centro"):
        Simbolo("R1", "R_1", "resistor", Magnitude(F(1), "ohm"),
                Punto(F(0), F(0)), True,
                (Terminale("R1", 0, "a", Punto(F(-24), F(0))),
                 Terminale("R1", 1, "b", Punto(F(48), F(0)))))


def test_un_simbolo_con_entrambi_i_morsetti_sullo_stesso_nodo_e_rifiutato():
    """`Component` lo vieta gia' nel dominio — *«terminali coincidenti»* — e la scena
    non lo vietava: lo schema del circuito e quello del disegno dicevano cose diverse
    sullo stesso oggetto."""
    with pytest.raises(ValueError, match="entrambi i morsetti sul nodo a"):
        Simbolo("R1", "R_1", "resistor", Magnitude(F(1), "ohm"),
                Punto(F(0), F(0)), True,
                (Terminale("R1", 0, "a", Punto(F(-24), F(0))),
                 Terminale("R1", 1, "a", Punto(F(24), F(0)))))


# --- la `viewBox` contiene cio' che si emette --------------------------------

def test_nessuna_scritta_esce_dalla_viewbox():
    """Il difetto stava sulla fixture che la storia prescrive: «220 ohm» finiva a
    destra del bordo, e nel PNG restava «220».

    `Scena.estensione()` non conta le etichette — non puo': la tipografia sta in
    `svg.py` — e `MARGINE` copriva per costruzione 22 unita' di testo su un componente
    verticale al bordo destro. Il margine ora e' `{spacing.drawing-inset}` e le
    scritte entrano nell'estensione col loro maggiorante.
    """
    radice = _albero(render(CIRCUITO, LAYOUT))
    x, y, larga, alta = (F(v) for v in radice.get("viewBox").split(" "))
    for scritta in _scritte(SCENA):
        basso, alto = _riquadro_del_testo(scritta)
        assert x <= basso.x and alto.x <= x + larga, scritta[2]
        assert y <= basso.y and alto.y <= y + alta, scritta[2]


def test_il_riquadro_di_una_scritta_e_un_maggiorante_ancorato_alla_linea_di_base():
    """`y` in SVG e' la linea di base: sopra c'e' l'ascendente, sotto il discendente.
    Il maggiorante e' un quadratone per glifo — non una misura del font, che qui non
    si puo' fare, ma un limite che nessun glifo latino supera."""
    basso, alto = _riquadro_del_testo((Punto(F(10), F(100)), "start", "abc"))
    assert (basso.x, alto.x) == (F(10), F(10) + 3 * CORPO_TESTO)
    assert basso.y < F(100) < alto.y
    a_meta = _riquadro_del_testo((Punto(F(10), F(100)), "middle", "abc"))
    assert a_meta[0].x == F(10) - 3 * CORPO_TESTO / 2


# --- il segno del generatore: un solo canale, tre volte ----------------------

def _linee_del_generatore(disegno: str) -> list[tuple[str, ...]]:
    gruppo = [g for g in _albero(disegno).iter(f"{SVG}g")
              if g.get("data-component-id") == "V1"][0]
    return [(e.get("x1"), e.get("y1"), e.get("x2"), e.get("y2"))
            for e in gruppo.iter(f"{SVG}line")]


def test_la_croce_del_generatore_sta_dentro_il_cerchio():
    """Era a tre quarti della distanza dal centro al morsetto — 18 unita' da un centro
    di raggio 12 — quindi fuori dal corpo e sovrapposta al reoforo: nel PNG si leggeva
    come una piastra, non come un piu'."""
    gruppo = [g for g in _albero(render(CIRCUITO, LAYOUT)).iter(f"{SVG}g")
              if g.get("data-component-id") == "V1"][0]
    cerchio = [c for c in gruppo.iter(f"{SVG}circle") if c.get("r") == "12"][0]
    centro, raggio = F(cerchio.get("cy")), F(cerchio.get("r"))
    croce = [l for l in gruppo.iter(f"{SVG}line")
             if l.get("x1") != l.get("x2") or abs(F(l.get("y1")) - F(l.get("y2"))) == 8]
    assert len(croce) == 2
    for linea in croce:
        for y in (F(linea.get("y1")), F(linea.get("y2"))):
            assert abs(y - centro) <= raggio


def test_un_generatore_spento_non_disegna_una_polarita_che_non_ha():
    """L'alternativa testuale dice «col primo morsetto», che non promette polarita';
    la croce la prometteva. I due canali dicevano cose diverse dello stesso oggetto."""
    circuito = _circuito(
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(0), "V1"),
        Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
    )
    disegno = render(circuito, LAYOUT)
    assert "col primo morsetto al nodo b" in disegno
    assert len(_linee_del_generatore(disegno)) == 2      # i due reofori, nient'altro


def test_a_valore_negativo_la_croce_si_sposta_e_il_numero_resta_quello_del_componente():
    """Microcopy 5 di `EXPERIENCE.md`: *«Il testo cita il risultato, non lo
    riformula»*. L'etichetta disegnava «-12 volt» e il testo diceva «12 volt»: due
    canali che si contraddicono sul numero dello stesso generatore."""
    circuito = _circuito(
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(-12), "V1"),
        Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
        Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
    )
    disegno = render(circuito, LAYOUT)
    assert ">-12 volt</text>" in disegno
    assert "da -12 volt, col morsetto positivo al nodo 0" in disegno
    croce = [l for l in _linee_del_generatore(disegno) if l[0] != l[2]][0]
    positiva = [l for l in _linee_del_generatore(render(CIRCUITO, LAYOUT))
                if l[0] != l[2]][0]
    assert F(croce[1]) > F(positiva[1])     # sotto il centro invece che sopra


# --- il nodo di riferimento: detto **e** disegnato ---------------------------

def test_il_nodo_di_riferimento_e_disegnato_oltre_che_detto():
    """Entrava nel `<desc>` e in nessun elemento grafico: chi guarda e chi ascolta
    ricevevano due topologie che differiscono per un'informazione. K-0 dice che il
    disegno fa parte della prova."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    marcate = [g.get("data-node-id") for g in _con(radice, "circle", "data-node-id")
               if g.get("data-node-reference") == "true"]
    assert marcate == ["0"]
    masse = [l for l in radice.iter(f"{SVG}line") if l.get("class") == "kf-massa"]
    assert len(masse) == 3
    giunzione = [g for g in _con(radice, "circle", "data-node-id")
                 if g.get("data-node-id") == "0"][0]
    for linea in masse:
        assert F(linea.get("y1")) > F(giunzione.get("cy"))


# --- l'identita': un solo portatore per morsetto -----------------------------

def test_l_ancoraggio_del_morsetto_e_uno_solo_e_sta_nel_gruppo_del_componente():
    """La tripla `data-terminal-*` compare due volte per morsetto, ed e' voluto: il
    `<circle>` del layer 3 **e'** l'ancoraggio, il `<polyline>` del layer 2 e' il
    conduttore che lo tocca. AD-31 usa questa distinzione — *«ogni conduttore disegnato
    ha gli estremi coincidenti … con gli ancoraggi dei terminali che il suo
    `data-terminal-*` nomina»* — e chi riparsa in 1.6 conta gli ancoraggi, non le
    occorrenze dell'attributo.
    """
    radice = _albero(render(CIRCUITO, LAYOUT))
    ancoraggi = [(g.get("data-component-id"), m.get("data-terminal-index"))
                 for g in _con(radice, "g", "data-component-id")
                 for m in _con(g, "circle", "data-terminal-component")]
    assert len(ancoraggi) == 6
    assert sorted(ancoraggi) == ancoraggi
    fuori = [m for m in _con(radice, "circle", "data-terminal-component")
             if m.get("data-component-id") is not None]
    assert fuori == []


def test_ogni_componente_porta_anche_il_nome_simbolico_che_il_dominio_gli_da():
    """`Component.symbolic` non e' l'`id`: in `dc-00001` valgono `E1` ed `E_1`. Quale
    dei due lo studente debba leggere non e' deciso da nessuna autorita' e questa
    storia non lo decide; perderlo nella serializzazione lo renderebbe indecidibile
    anche dopo, e AD-10 fa di questo SVG la sorgente unica."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    assert [g.get("data-component-symbolic")
            for g in _con(radice, "g", "data-component-id")] == ["R1", "R2", "V1"]


# --- accessibilita' -----------------------------------------------------------

def test_la_radice_dichiara_la_lingua_del_testo_che_porta():
    """WCAG 2.2 AA e' l'obiettivo dichiarato di `EXPERIENCE.md`. AD-10 fa viaggiare
    questo SVG da solo: senza `lang`, un lettore di schermo pronuncia l'italiano con
    le regole di un'altra lingua."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    assert radice.get("lang") == "it"
    assert radice.get("{http://www.w3.org/XML/1998/namespace}lang") == "it"


def test_il_testo_per_lo_studente_e_in_italiano_con_gli_accenti():
    """«e'» letto ad alta voce e' un'altra parola. La convenzione ASCII di questo
    repository vale per docstring e identificatori, non per cio' che si pronuncia."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    descrizione = radice.find(f"{SVG}desc").text
    assert "è" in descrizione
    assert "e'" not in descrizione


# --- i token di `DESIGN.md` (AD-26) ------------------------------------------

def test_le_etichette_portano_il_token_tipografico_e_non_un_font_inventato():
    """`identity-tag` prescrive `{typography.label-drawing}`: `Inter, system-ui,
    sans-serif` a 11 px, peso 500. Era `ui-sans-serif, sans-serif`, che non e' quel
    token — e AD-26 chiede che i quattro bracci usino **gli stessi** token."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    scritte = list(radice.iter(f"{SVG}text"))
    assert scritte
    for t in scritte:
        assert t.get("font-family") == "Inter, system-ui, sans-serif"
        assert (t.get("font-size"), t.get("font-weight")) == ("11", "500")


def test_ogni_elemento_disegnato_ha_una_classe_a_cui_agganciare_un_token():
    """AD-26: l'`ArmEncoding` e' *«un parametro di rendering costruito da
    `experiment/`»*, e un braccio che volesse cambiare tinta o peso deve poterlo fare
    senza toccare il renderer — implementarlo dentro `render/serialize` e' la
    collocazione che AD-26 chiama velenosa. La classe e' quell'aggancio: in CSS
    qualunque regola d'autore batte un attributo di presenza."""
    radice = _albero(render(CIRCUITO, LAYOUT))
    disegnati = [e for tag in ("polyline", "line", "rect", "circle", "text")
                 for e in radice.iter(f"{SVG}{tag}")]
    assert len(disegnati) == 38
    assert {e.get("class") for e in disegnati} <= set(_CLASSI)
    assert all(e.get("class") for e in disegnati)


def test_il_disegno_non_dipende_da_un_motore_css_per_esistere():
    """Il difetto che questo test chiude e' stato **misurato**, non temuto.

    Una stesura emetteva un `<style>` con `stroke:var(--kf-ink-primary,currentColor)`
    sulle classi. Rasterizzata con `cairosvg` — un secondo renderer, indipendente da
    quello di sistema — la fixture usciva **senza un solo tratto**: niente fili, niente
    corpi, niente massa, solo i pallini e le etichette. Quel renderer applica la regola
    di classe e non conosce `var()`, quindi sostituisce l'attributo di presenza con una
    tinta non valida invece di ignorare la dichiarazione.

    AD-10 fa di questo SVG la sorgente di **ogni** altro formato, e D4 — quale stack di
    rendering, web contro PDF — e' una decisione aperta che tocca Gate A: presupporre
    un motore CSS moderno nel percorso di export significa scommettere su una decisione
    che nessuno ha preso. Un circuito esportato senza fili e' il modo peggiore in cui
    questo prodotto possa fallire: il disegno **e'** la prova.
    """
    disegno = render(CIRCUITO, LAYOUT)
    assert "var(" not in disegno
    assert "<style" not in disegno
    radice = _albero(disegno)
    for tag in ("polyline", "line", "rect"):
        elementi = list(radice.iter(f"{SVG}{tag}"))
        assert elementi
        for e in elementi:
            assert e.get("stroke") == "currentColor", ET.tostring(e)
    assert radice.get("stroke-width") == "1.5"
    for cerchio in radice.iter(f"{SVG}circle"):
        assert cerchio.get("fill") in ("none", "currentColor")


# --- il golden: l'unico oracolo che vede cambiare il formato -----------------

GOLDEN = Path(__file__).resolve().parent / "golden" / "story-1-4-fixture.svg"


def test_i_byte_emessi_sono_quelli_depositati():
    """Due rendering uguali fra loro non dicono nulla sul **formato**: un cambio di
    forma passerebbe in silenzio fino alla riparsatura della Story 1.6. Il golden e'
    l'oracolo che lo vede.

    FR-46: *«un cambio di golden e' una modifica esplicita e revisionata, non un
    aggiornamento automatico che assorbe la regressione»*. Nessuno script lo riscrive.
    """
    assert render(CIRCUITO, LAYOUT) == GOLDEN.read_text(encoding="utf-8")


# --- un circuito che non e' stato inventato per l'occasione ------------------

def test_un_circuito_dell_insieme_di_riferimento_si_disegna():
    """`render()` non era mai stato eseguito su un circuito dell'insieme di
    riferimento, benche' i casi `dc-*` di `dev` abbiano esattamente i tipi di `FORME`:
    la fixture di questa storia era inventata per l'occasione, e nessuno aveva
    verificato che il renderer regga un circuito che il progetto possiede davvero.

    Il `LayoutIR` resta **predefinito** — l'autolayout e' non-goal — ma il circuito no:
    `dc-00001` e' un generatore in parallelo a un resistore fra `A` e `0`, ed e' il
    caso in cui `id` e `symbolic` differiscono davvero (`E1` ed `E_1`).
    """
    radice_del_progetto = Path(__file__).resolve().parent.parent
    casi = reference_set.load(radice_del_progetto / "reference-set", "dev")
    caso = next(c for c in casi if c.case_id == "dc-00001")
    layout = _layout((Placement(N("A"), F(0), F(0)), Placement(N("0"), F(0), F(160)),
                      Placement(C("E1"), F(0), F(80)), Placement(C("R1"), F(120), F(80))))

    radice = _albero(render(caso.ir, layout))
    gruppi = _con(radice, "g", "data-component-id")
    assert [(g.get("data-component-id"), g.get("data-component-symbolic"))
            for g in gruppi] == [("E1", "E_1"), ("R1", "R1")]
    assert sorted(g.get("data-node-id")
                  for g in _con(radice, "circle", "data-node-id")) == ["0", "A"]
    assert len(_con(radice, "polyline", "data-terminal-component")) == 4
    _, descrizione = alternativa_testuale(scena(caso.ir, layout))
    assert "Al nodo A si incontrano E1 e R1." in descrizione
