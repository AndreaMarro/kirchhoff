"""Story 1.8 — Visual Slice 0: prima, azione, dopo, e **ripercorribile**.

> «percorrere avanti e indietro il passaggio, so that possa fissare il cambiamento
> premendo piu' volte invece di guardarlo una volta sola.»

E' il primo punto in cui A-0 ha due disegni da confrontare invece di uno solo, e
quindi il primo in cui la continuita' visuale e' **misurata** e non promessa.

| AC | Che cosa afferma | Dove si verifica |
|---|---|---|
| AC1 | commutazione istantanea, ripetibile all'infinito, senza conferma (UX-DR12) | `TestLaCommutazione` |
| AC2 | toccando `Req` si vede da cosa deriva; toccando un preservato, che e' lo stesso | `TestLIspezioneDelPasso` |
| AC3 | «Perche' posso farlo?»: **quattro** campi gia' calcolati, nessuna prosa (UX-DR23) | `TestPercheePossoFarlo` |
| AC4 | la forma statica per l'export, dalla **stessa** sorgente semantica (AD-10) | `TestLaFormaStatica` |
| autorita' | A-0 fra i due stati: cio' che e' in `preserve` non si muove | `TestA0FraIDueStati` |

La fixture e' quella delle Story 1.4 e 1.7 — `V1`, `R1`, `R2`, `LayoutIR`
predefinito — e resta la stessa per la ragione che 1.7 dichiarava: le due meta'
della promessa si incontrano solo se il passo si applica al disegno su cui il
serializzatore e' stato scritto.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import fields
from fractions import Fraction as F

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import (
    Certificate,
    EntityRef,
    preconditions_of,
    transform,
)
from kirchhoff.render.layout import LayoutIR, LayoutStore, PatchStore, Placement
from kirchhoff.render.step import (
    InteractionState,
    Justification,
    StaticStep,
    VisualStep,
    componi,
)
from kirchhoff.render.step import compose as modulo_di_composizione

SVG = "{http://www.w3.org/2000/svg}"
ENTROPIA = bytes(range(10))
ISTANTE = 1_755_000_000_000

C = lambda i: EntityRef("component", i)
N = lambda i: EntityRef("node", i)

#: L'equivalente che `serie` conia. Il nome lo fa il motore: qui si legge.
EQUIVALENTE = C("R1R2eq")

CIRCUITO = IR("1.0.0", "dc_resistive", "netlist", ("0", "a", "b"), (
    Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
    Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
    Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
), ())

PIAZZAMENTI = (
    Placement(N("b"), F(0), F(0)),
    Placement(N("a"), F(200), F(0)),
    Placement(N("0"), F(100), F(160)),
    Placement(C("V1"), F(0), F(80)),
    Placement(C("R1"), F(100), F(0)),
    Placement(C("R2"), F(200), F(80)),
)


def _layout(istante: int = ISTANTE) -> LayoutIR:
    return LayoutIR.nuovo(PIAZZAMENTI, istante=istante, casualita=ENTROPIA)


def _passo(istante: int = ISTANTE) -> VisualStep:
    """Il passo della Story 1.7, composto ora da `src/` e non da un file di test."""
    esito = componi(
        CIRCUITO, "serie", "R1", "R2",
        layout=_layout(istante), layouts=LayoutStore(), patches=PatchStore(),
        istante=istante + 1_000, casualita=ENTROPIA)
    assert isinstance(esito, VisualStep)
    return esito


#: Tre resistori in fila, per il **secondo** passo: `serie(R1,R2)` lascia `R1R2eq`
#: fra `b` e `c`, e `serie(R1R2eq,R3)` e' allora applicabile. La fixture del passo
#: singolo non lo permette — dopo la sua unica riduzione resta una sola resistenza.
CATENA = IR("1.0.0", "dc_resistive", "netlist", ("0", "a", "b", "c"), (
    Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
    Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
    Component.of("R2", "resistor", ("a", "c"), F(220), "R2"),
    Component.of("R3", "resistor", ("c", "0"), F(330), "R3"),
), ())

PIAZZAMENTI_CATENA = (
    Placement(N("b"), F(0), F(0)),
    Placement(N("a"), F(200), F(0)),
    Placement(N("c"), F(400), F(0)),
    Placement(N("0"), F(200), F(240)),
    Placement(C("V1"), F(0), F(120)),
    Placement(C("R1"), F(100), F(0)),
    Placement(C("R2"), F(300), F(0)),
    Placement(C("R3"), F(400), F(120)),
)


def _layout_catena(istante: int = ISTANTE) -> LayoutIR:
    return LayoutIR.nuovo(PIAZZAMENTI_CATENA, istante=istante, casualita=ENTROPIA)


#: Due resistenze fra gli stessi due nodi, per misurare **l'altra** riduzione: dopo
#: `parallelo(R1,R2)` restano `V1` e l'equivalente fra `b` e `0`, e il circuito
#: resta valido — al contrario della fixture di `test_un_rifiuto_si_restituisce_...`,
#: dove la fusione lascia un ramo aperto e il prodotto e' rifiutato.
PARALLELO = IR("1.0.0", "dc_resistive", "netlist", ("0", "b"), (
    Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
    Component.of("R1", "resistor", ("b", "0"), F(100), "R1"),
    Component.of("R2", "resistor", ("b", "0"), F(220), "R2"),
), ())

PIAZZAMENTI_PARALLELO = (
    Placement(N("b"), F(0), F(0)),
    Placement(N("0"), F(0), F(160)),
    Placement(C("V1"), F(0), F(80)),
    Placement(C("R1"), F(100), F(80)),
    Placement(C("R2"), F(200), F(80)),
)


def _passo_e_circuiti(caso: str) -> tuple[VisualStep, IR, IR]:
    """Un passo composto davvero, col suo `Cₖ` e il suo `Cₖ₊₁`, per ogni forma disponibile.

    Sono i quattro passi che la suite sa comporre — le due riduzioni, e i due
    passi della catena — e servono a misurare le proprieta' universali su ogni
    forma invece che su una fixture sola.
    """
    if caso == "serie":
        dopo_ir, _ = transform(CIRCUITO, "serie", "R1", "R2")
        return _passo(), CIRCUITO, dopo_ir
    if caso == "parallelo":
        passo = componi(
            PARALLELO, "parallelo", "R1", "R2",
            layout=LayoutIR.nuovo(PIAZZAMENTI_PARALLELO, istante=ISTANTE,
                                  casualita=ENTROPIA),
            layouts=LayoutStore(), patches=PatchStore(),
            istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert isinstance(passo, VisualStep)
        dopo_ir, _ = transform(PARALLELO, "parallelo", "R1", "R2")
        return passo, PARALLELO, dopo_ir
    layouts, patches = LayoutStore(), PatchStore()
    uno = componi(CATENA, "serie", "R1", "R2", layout=_layout_catena(),
                  layouts=layouts, patches=patches,
                  istante=ISTANTE + 1_000, casualita=ENTROPIA)
    assert isinstance(uno, VisualStep)
    medio_ir, _ = transform(CATENA, "serie", "R1", "R2")
    if caso == "catena, primo passo":
        return uno, CATENA, medio_ir
    due = componi(medio_ir, "serie", "R1R2eq", "R3",
                  layout=layouts.risolvi(uno.dopo),
                  layouts=layouts, patches=patches,
                  istante=ISTANTE + 2_000, casualita=ENTROPIA)
    assert isinstance(due, VisualStep)
    finale_ir, _ = transform(medio_ir, "serie", "R1R2eq", "R3")
    return due, medio_ir, finale_ir


def _nessun_rendering(monkeypatch, ragione: str) -> None:
    """Chiude **tutte** le strade per arrivare a `render`, non solo l'ultima.

    `from ..serialize import render` lega il nome tre volte — in `serialize.svg` dove
    nasce, in `serialize` che lo riesporta, in `compose` che lo chiama — e sostituirne
    una sola lascia le altre due percorribili. Un oracolo che sostituisce una
    rilegatura che il codice sotto test non attraversa e' verde per costruzione.
    """
    from kirchhoff.render import serialize
    from kirchhoff.render.serialize import svg

    def esplodi(*a, **k):
        pytest.fail(ragione)

    for modulo in (svg, serialize, modulo_di_composizione):
        monkeypatch.setattr(modulo, "render", esplodi)


def _albero(testo: str) -> ET.Element:
    return ET.fromstring(testo)


def _entita_emessa(radice: ET.Element, attributo: str, valore: str) -> ET.Element:
    """L'elemento che porta quell'identificatore semantico, o `AssertionError`.

    Si cerca **nei byte emessi** e non nelle strutture: e' il disegno consegnato che
    deve reggere A-0, e una struttura interna coerente con un disegno diverso e'
    precisamente il caso che questo controllo esiste per prendere.
    """
    trovati = [e for e in radice.iter() if e.get(attributo) == valore]
    assert len(trovati) == 1, f"{attributo}={valore}: {len(trovati)} elementi emessi"
    return trovati[0]


# --- AC1 · la commutazione ----------------------------------------------------

class TestLaCommutazione:
    """UX-DR12: *«due stati commutabili all'infinito, `{motion.instant}`»*."""

    def test_si_apre_su_prima_e_non_avanza_da_solo(self):
        """UX-DR22 vieta l'auto-avanzamento.

        Aprire su `dopo` mostrerebbe il passo gia' compiuto: e' un avanzamento, e
        chi guarda dovrebbe tornare indietro per vedere da dove si partiva.
        """
        passo = _passo()
        assert passo.apertura() == InteractionState(passo.prima)

    def test_commutare_porta_all_altro_stato_e_ritorno(self):
        passo = _passo()
        prima = passo.apertura()
        dopo = passo.commuta(prima)
        assert dopo.mostrato == passo.dopo
        assert passo.commuta(dopo) == prima

    def test_la_commutazione_e_involutiva_su_entrambi_gli_stati(self):
        """`commuta(commuta(s)) == s` e' la forma algebrica di «all'infinito».

        Verificarla su un numero di giri scelto a mano misurerebbe quel numero; la
        proprieta' involutiva dice invece che **ogni** numero pari torna al punto di
        partenza, e non c'e' un giro oltre il quale smetta di valere.
        """
        passo = _passo()
        for stato in (InteractionState(passo.prima), InteractionState(passo.dopo)):
            assert passo.commuta(passo.commuta(stato)) == stato

    def test_mille_giri_restituiscono_gli_stessi_identici_byte(self):
        """«Ripetibile all'infinito» sui byte, non solo sugli identificatori.

        Il confronto e' con `is`: due stringhe uguali passerebbero anche se ogni
        giro avesse renderizzato di nuovo, e un secondo rendering e' esattamente
        cio' che AD-35 obbliga a rendere impossibile invece che improbabile.
        """
        passo = _passo()
        stato = passo.apertura()
        atteso = passo.fotogramma(stato)
        for _ in range(1_000):
            stato = passo.commuta(stato)
        assert stato.mostrato == passo.prima
        assert passo.fotogramma(stato) is atteso

    def test_commutare_non_renderizza_nemmeno_una_volta(self, monkeypatch):
        """«Istantanea» come oracolo, non come aggettivo.

        Si conta quante volte `render` viene chiamata: **due** durante la
        composizione, **zero** in mille commutazioni. Senza questo controllo
        «istantanea» resterebbe un'affermazione su una durata che nessun test
        misura, e la commutazione potrebbe ridisegnare senza che nulla protesti.
        """
        chiamate = []
        vera = modulo_di_composizione.render

        def contando(*a, **k):
            chiamate.append(a[:2])
            return vera(*a, **k)

        monkeypatch.setattr(modulo_di_composizione, "render", contando)
        passo = _passo()
        assert len(chiamate) == 2

        # `commuta` e `fotogramma` stanno in `schema.py`, che non importa `render`:
        # continuare a contare sul solo `compose` non direbbe niente su di loro.
        # Da qui in poi **nessuna** delle tre rilegature deve essere raggiunta.
        _nessun_rendering(monkeypatch, "commutare ha renderizzato")
        stato = passo.apertura()
        for _ in range(1_000):
            stato = passo.commuta(stato)
            passo.fotogramma(stato)
        assert len(chiamate) == 2

    def test_commutare_non_chiede_conferma(self):
        """UX-DR12: *«senza conferma»*, letto sulla firma e non sul comportamento.

        Una conferma entra in una firma in due modi soli: un parametro che la
        chiede, o un esito che dice «non commutato». `commuta` non ha il primo — un
        solo parametro oltre a `self` — e non ha il secondo, perche' restituisce
        sempre un `InteractionState` e su uno stato estraneo solleva invece di
        rispondere con un rifiuto silenzioso.
        """
        import inspect

        firma = inspect.signature(VisualStep.commuta)
        assert list(firma.parameters) == ["self", "stato"]
        assert firma.return_annotation == "InteractionState"

    def test_commutare_uno_stato_di_un_altro_passo_solleva(self):
        """Rispondere `prima` mostrerebbe il disegno di una derivazione diversa."""
        passo = _passo()
        altrove = InteractionState(_layout(ISTANTE + 9_000_000).identifier)
        with pytest.raises(ValueError, match="non e' uno stato visuale di questo passo"):
            passo.commuta(altrove)

    def test_il_fotogramma_di_uno_stato_estraneo_solleva(self):
        passo = _passo()
        altrove = InteractionState(_layout(ISTANTE + 9_000_000).identifier)
        with pytest.raises(ValueError, match="non e' uno stato visuale di questo passo"):
            passo.fotogramma(altrove)

    def test_lo_stato_di_interazione_e_un_identificatore_di_stato_visuale(self):
        """AD-21: nessuna delle quattro contiene un'altra se non per identificatore."""
        with pytest.raises(ValueError):
            InteractionState("ir_01K2F2DKG0000G40R40M30E209")


# --- AC2 · l'ispezione del passo ---------------------------------------------

class TestLIspezioneDelPasso:
    """FR-49: *«ogni elemento della risposta e' un campo del passo»*."""

    def test_toccando_l_equivalente_si_vede_da_cosa_deriva(self):
        passo = _passo()
        assert passo.deriva_da(EQUIVALENTE) == (C("R1"), C("R2"))

    def test_toccando_un_nodo_preservato_si_vede_che_e_lo_stesso(self):
        """`Pₖ` per identificatore, e la stessa posizione nei due disegni.

        Le due meta' sono distinte e servono entrambe: l'appartenenza a `preserve`
        dice che l'entita' **e'** la stessa (AD-22, `id_{k+1}(x) = id_k(x)` senza
        tolleranza), il confronto sui byte dice che il disegno non l'ha spostata.
        Un sistema che affermasse la prima e violasse la seconda e' precisamente
        cio' che A-0 vieta.
        """
        passo = _passo()
        assert passo.e_lo_stesso(N("b"))
        assert passo.e_lo_stesso(N("0"))
        assert passo.e_lo_stesso(C("V1"))

        prima = _entita_emessa(_albero(passo.fotogrammi[passo.prima]), "data-node-id", "b")
        dopo = _entita_emessa(_albero(passo.fotogrammi[passo.dopo]), "data-node-id", "b")
        assert (prima.get("cx"), prima.get("cy")) == (dopo.get("cx"), dopo.get("cy"))

    def test_cio_che_il_passo_consuma_non_e_lo_stesso(self):
        """Il verso negativo, senza il quale `e_lo_stesso` potrebbe dire sempre si'."""
        passo = _passo()
        assert not passo.e_lo_stesso(C("R1"))
        assert not passo.e_lo_stesso(C("R2"))
        assert not passo.e_lo_stesso(N("a"))
        assert not passo.e_lo_stesso(EQUIVALENTE)

    def test_il_nodo_assorbito_non_deriva_da_nulla_ma_la_lineage_lo_dice(self):
        """Da `a` non nasce niente, e `a` non e' rimasto: sono due fatti diversi.

        `deriva_da` risponde vuoto e sarebbe muto da solo — indistinguibile da un
        nodo che il passo non ha toccato. `che_ne_e_stato` porta la riscrittura che
        l'ha inghiottito, che e' la meta' che la Story 1.2 ha separato.
        """
        passo = _passo()
        assert passo.deriva_da(N("a")) == ()
        assorbito = passo.che_ne_e_stato(N("a"))
        assert assorbito is not None
        assert assorbito.operation == "eliminazione_di_nodo"
        assert passo.che_ne_e_stato(N("b")) is None

    def test_le_risposte_sono_quelle_del_prodotto_e_non_una_seconda_lettura(self):
        """E-62: la lineage e' scritta una volta sola, nel `Delta` che l'ha calcolata."""
        passo = _passo()
        assert passo.deriva_da(EQUIVALENTE) is passo.risultato.delta.derived_from(
            EQUIVALENTE)
        assert passo.che_ne_e_stato(N("a")) is passo.risultato.delta.what_happened_to(
            N("a"))


# --- AC3 · «Perche' posso farlo?» --------------------------------------------

class TestPercheePossoFarlo:
    """UX-DR23: **quattro** campi gia' calcolati, e nessuna spiegazione generata."""

    def test_i_campi_sono_quattro_e_sono_quelli_nominati(self):
        """Il numero e i nomi insieme.

        Contare quattro campi senza guardarne i nomi lascerebbe passare quattro
        campi qualsiasi; guardare i nomi senza contare lascerebbe aggiungere un
        quinto — e un quinto campo e' il primo passo verso una risposta che spiega.
        """
        nomi = tuple(c.name for c in fields(Justification))
        assert nomi == ("terminali", "precondizioni", "formula", "certificato")

    def test_i_quattro_campi_sono_letti_dal_prodotto_non_composti(self):
        """`is`, non `==`: una copia ricostruita passerebbe l'uguaglianza.

        E' la differenza fra «la risposta e' un campo del passo» e «la risposta
        coincide con un campo del passo». La seconda e' vera anche di una
        spiegazione ben scritta, ed e' quella che FR-49 rifiuta.
        """
        passo = _passo()
        prodotto = passo.risultato
        g = passo.giustificazione
        assert g.terminali is prodotto.boundary.entities
        assert g.formula is prodotto.equation
        assert g.certificato is prodotto.certificate
        assert g.precondizioni is preconditions_of("serie")

    def test_i_quattro_campi_esistevano_prima_della_domanda(self):
        """«Gia' calcolati» come ordine temporale, non come aggettivo.

        Si prendono i quattro oggetti **prima** di chiedere, e si verifica che la
        risposta porti quegli stessi oggetti. Un campo prodotto al momento della
        domanda non potrebbe superare questo confronto, qualunque sia il suo
        contenuto.
        """
        passo = _passo()
        attesi = (passo.risultato.boundary.entities, preconditions_of("serie"),
                  passo.risultato.equation, passo.risultato.certificate)
        g = passo.giustificazione
        assert (g.terminali, g.precondizioni, g.formula, g.certificato) == attesi
        assert all(a is b for a, b in zip(attesi, (g.terminali, g.precondizioni,
                                                   g.formula, g.certificato)))

    def test_chiedere_due_volte_da_gli_stessi_oggetti(self):
        """Una risposta che varia fra due domande identiche e' una generazione."""
        passo = _passo()
        prima, seconda = passo.giustificazione, passo.giustificazione
        assert prima == seconda
        assert prima.formula is seconda.formula
        assert prima.certificato is seconda.certificato

    def test_i_terminali_sono_i_due_nodi_su_cui_il_passo_confina(self):
        """`∂Tₖ`: dove il sottografo tocca cio' che resta. Per `serie`, due nodi."""
        passo = _passo()
        assert passo.giustificazione.terminali == (N("0"), N("b"))

    def test_le_precondizioni_sono_quelle_dichiarate_dal_catalogo(self):
        passo = _passo()
        assert passo.giustificazione.precondizioni == (
            "l'operazione nomina esattamente due componenti",
            "i due componenti nominati esistono nel circuito",
            "i due componenti sono entrambi resistori",
            "i due componenti condividono esattamente un nodo",
            "il nodo condiviso non e' il nodo di riferimento",
            "al nodo condiviso non tocca un terzo componente",
            "il circuito di partenza supera la validazione elettrica",
        )

    def test_il_certificato_e_quello_dell_operazione_del_passo(self):
        passo = _passo()
        assert isinstance(passo.giustificazione.certificato, Certificate)
        assert passo.giustificazione.certificato.operation == passo.operation


class TestLeGuardieDellaGiustificazione:
    """L'unico dei quattro tipi esportati che non aveva guardie — e UX-DR23 nomina lui.

    Il controllo di forma della prima revisione era stato installato sul
    produttore (`catalog._verifica_precondizioni`) e non sul tipo che il lettore
    riceve: `Justification(terminali="R1", precondizioni="abc", formula=None,
    certificato=None)` si costruiva senza proteste, e `tuple(precondizioni)` era
    `('a', 'b', 'c')` — l'elenco di lettere che quel controllo esiste per
    escludere, ricostruibile all'ultimo punto prima del lettore aggirando il
    Catalogo. Stessa convenzione delle sorelle: ogni invariante ha una guardia a
    runtime e un test che l'ha vista sollevare.
    """

    def test_la_riga_che_prima_passava_ora_non_passa(self):
        """L'esatto controesempio del rilievo, e non una sua parafrasi."""
        with pytest.raises(TypeError):
            Justification(terminali="R1", precondizioni="abc",
                          formula=None, certificato=None)

    def test_i_terminali_sono_una_tupla_di_entita(self):
        """`terminali` e' `boundary.entities`: nomina entita', non testo."""
        passo = _passo()
        g = passo.giustificazione
        for guasti in ("R1", ("R1", "R2")):
            with pytest.raises(TypeError, match="tupla di EntityRef"):
                Justification(terminali=guasti, precondizioni=g.precondizioni,
                              formula=g.formula, certificato=g.certificato)

    def test_le_precondizioni_non_possono_essere_una_stringa(self):
        """Il caso speculare del controllo di forma del Catalogo, sul tipo."""
        passo = _passo()
        g = passo.giustificazione
        with pytest.raises(TypeError, match="si itera per caratteri"):
            Justification(terminali=g.terminali, precondizioni="abc",
                          formula=g.formula, certificato=g.certificato)

    def test_una_precondizione_vuota_o_non_testuale_e_rifiutata(self):
        passo = _passo()
        g = passo.giustificazione
        for guaste in (("",), ("   ",), (3,)):
            with pytest.raises(ValueError, match="vuota o non testuale"):
                Justification(terminali=g.terminali, precondizioni=guaste,
                              formula=g.formula, certificato=g.certificato)

    def test_la_formula_e_il_certificato_sono_del_tipo_del_prodotto(self):
        """`None` al posto dei due campi del prodotto era il resto del controesempio."""
        passo = _passo()
        g = passo.giustificazione
        with pytest.raises(TypeError, match="invece di Equation"):
            Justification(terminali=g.terminali, precondizioni=g.precondizioni,
                          formula=None, certificato=g.certificato)
        with pytest.raises(TypeError, match="invece di Certificate"):
            Justification(terminali=g.terminali, precondizioni=g.precondizioni,
                          formula=g.formula, certificato=None)

    def test_cio_che_giustificazione_produce_regge_alle_proprie_guardie(self):
        """Il verso positivo: le guardie non rifiutano l'unico costruttore vero."""
        assert isinstance(_passo().giustificazione, Justification)


class TestLePrecondizioniSonoFalsificabili:
    """Una precondizione dichiarata e non esigibile e' prosa con un nome di campo.

    Ogni riga dichiarata ha qui un circuito che la viola, e `transform` lo
    respinge — con un `ValueError` quando la impone una porta o una guardia del
    corpo, con un `Refusal` quando la impone `validate` su `Cₖ`, perche' quello
    e' un esito di dominio e si restituisce (AD-13). E' la lezione del gate
    scritto e non installato applicata a una dichiarazione: senza questi casi la
    tabella del Catalogo potrebbe descrivere condizioni che il motore non impone,
    e nessuno se ne accorgerebbe.
    """

    def _ir(self, *componenti: Component, nodi: tuple[str, ...]) -> IR:
        return IR("1.0.0", "dc_resistive", "netlist", nodi, componenti, ())

    def test_serie_esige_un_solo_nodo_in_comune(self):
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "0"), F(100), "R1"),
            Component.of("R2", "resistor", ("b", "0"), F(220), "R2"),
            nodi=("0", "b"))
        with pytest.raises(ValueError, match="condividono 2 nodi"):
            transform(circuito, "serie", "R1", "R2")

    def test_serie_non_elimina_il_nodo_di_riferimento(self):
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("a", "b"), F(12), "V1"),
            Component.of("R1", "resistor", ("a", "0"), F(100), "R1"),
            Component.of("R2", "resistor", ("0", "b"), F(220), "R2"),
            nodi=("0", "a", "b"))
        with pytest.raises(ValueError, match="nodo di riferimento"):
            transform(circuito, "serie", "R1", "R2")

    def test_serie_esige_che_al_nodo_comune_non_tocchi_un_terzo(self):
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
            Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
            Component.of("R3", "resistor", ("a", "0"), F(330), "R3"),
            nodi=("0", "a", "b"))
        with pytest.raises(ValueError, match="ha grado 3"):
            transform(circuito, "serie", "R1", "R2")

    def test_le_riduzioni_esigono_esattamente_due_identificatori(self):
        """La prima delle tre comuni: la impone la porta dell'arita' (`engine.py:648`).

        Sta **prima dello smistamento**, come l'esistenza dei componenti, e prima
        di questa dichiarazione il rifiuto c'era e «perche' posso farlo?» non
        nominava la ragione — la stessa classe delle due gia' riparate, che la
        seconda revisione ha trovato non enumerata.
        """
        for operazione in ("serie", "parallelo"):
            with pytest.raises(ValueError, match="vuole 2 identificatori"):
                transform(CIRCUITO, operazione, "R1")

    def test_le_riduzioni_esigono_un_circuito_di_partenza_valido(self):
        """L'ultima riga delle due dichiarazioni, e l'unica imposta con un `Refusal`.

        La impone `validate` su `Cₖ` dentro `engine._prodotto` (`engine.py:241`),
        **dopo** le guardie del corpo — per questo e' l'ultima — e il rifiuto si
        restituisce, non si solleva (AD-13). I due circuiti hanno un nodo `z`
        pendente estraneo alla coppia: ogni altra precondizione dichiarata e'
        soddisfatta, e il passo e' respinto lo stesso. Era la condizione esigita
        e non dichiarata su `Cₖ` che la voce §7 di `deferred-work.md` non aveva
        misurato, archiviando il verso come irriducibile su una misura incompleta.
        """
        con_pendente = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
            Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
            Component.of("R9", "resistor", ("b", "z"), F(50), "R9"),
            nodi=("0", "a", "b", "z"))
        esito = transform(con_pendente, "serie", "R1", "R2")
        assert isinstance(esito, Refusal)
        assert (esito.cause, esito.subject) == ("topology", "z")

        in_parallelo = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "0"), F(100), "R1"),
            Component.of("R2", "resistor", ("b", "0"), F(220), "R2"),
            Component.of("R9", "resistor", ("b", "z"), F(50), "R9"),
            nodi=("0", "b", "z"))
        esito = transform(in_parallelo, "parallelo", "R1", "R2")
        assert isinstance(esito, Refusal)
        assert (esito.cause, esito.subject) == ("topology", "z")

    def test_le_riduzioni_esigono_che_i_componenti_nominati_esistano(self):
        """La seconda delle tre comuni: la impone la porta di `transform` prima
        dello smistamento (`engine.py:656`) — non `_resistore`, che su un
        identificatore inesistente non arriva mai a girare. Era **esigita e non
        dichiarata**: il circuito veniva respinto e «perche' posso farlo?» non
        nominava la ragione, che e' l'unica cosa per cui l'elenco esiste.
        """
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
            Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
            nodi=("0", "a", "b"))
        for operazione in ("serie", "parallelo"):
            with pytest.raises(ValueError, match="non e un componente"):
                transform(circuito, operazione, "R1", "R9")

    def test_le_riduzioni_esigono_due_resistori(self):
        """La terza delle comuni: *«la riduzione vale fra resistori»*, di
        `engine._resistore` (`engine.py:192`) — l'unica delle tre che le due
        riduzioni attraversano dentro il proprio corpo."""
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
            Component.of("C1", "capacitor", ("a", "0"), F(1), "C1"),
            nodi=("0", "a", "b"))
        for operazione in ("serie", "parallelo"):
            with pytest.raises(ValueError, match="vale fra resistori"):
                transform(circuito, operazione, "R1", "C1")

    def test_parallelo_esige_gli_stessi_due_nodi(self):
        circuito = self._ir(
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
            Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
            nodi=("0", "a", "b"))
        with pytest.raises(ValueError, match="non stanno fra gli stessi due nodi"):
            transform(circuito, "parallelo", "R1", "R2")


# --- AC4 · la forma statica ---------------------------------------------------

class TestLaFormaStatica:
    """AD-10 v2: *«`export()` non ri-renderizza»*, e la sorgente e' una sola."""

    def test_l_export_porta_gli_stessi_identici_byte(self):
        """Il confronto e' con `is`, ed e' il contenuto dell'emendamento del 15 agosto.

        Prima di AD-10 v2 *«il byte-stream verificato non era mai quello che
        l'utente riceveva»*, perche' l'artefatto consegnato nasceva da una seconda
        passata. Due stringhe uguali non lo escluderebbero; due stringhe che sono
        lo stesso oggetto si'.
        """
        passo = _passo()
        statica = passo.esporta()
        assert statica.fotogrammi[0] is passo.fotogrammi[passo.prima]
        assert statica.fotogrammi[1] is passo.fotogrammi[passo.dopo]

    def test_esportare_non_renderizza(self, monkeypatch):
        """Sostituito **dove `render` nasce**, non solo dove `componi` la lega.

        `esporta` sta in `schema.py`, che non importa `render` da nessuna parte:
        sostituirla nel solo `compose` lasciava questo test verde per qualunque
        implementazione di `esporta`, compresa una che chiamasse `serialize.render`
        direttamente. Si sostituiscono percio' tutti e tre i nomi che portano alla
        stessa funzione — quello di origine e le due rilegature — e il test dice
        allora qualcosa sul comportamento invece che sulla propria impostazione.
        """
        passo = _passo()
        _nessun_rendering(monkeypatch, "l'export ha renderizzato di nuovo")
        passo.esporta()

    def test_la_forma_statica_nomina_i_due_stati_nell_ordine_prima_dopo(self):
        """Senza un comando da premere, l'ordine e' l'unica cosa che dice quale viene
        prima (UX-DR27: affiancati sopra i 768 px, e affiancati in quell'ordine)."""
        passo = _passo()
        statica = passo.esporta()
        assert isinstance(statica, StaticStep)
        assert (statica.prima, statica.dopo) == (passo.prima, passo.dopo)
        assert statica.operation == passo.operation

    def test_ogni_fotogramma_dichiara_di_quale_stato_visuale_e(self):
        """La congiunzione fra i byte e l'identificatore, letta dai byte.

        Senza `data-layout-id` la forma statica porterebbe due disegni e due `lay_`
        senza niente che dica quale va con quale — e la tripla di CV6 sarebbe
        congiungibile solo fidandosi dell'ordine di una tupla.
        """
        passo = _passo()
        statica = passo.esporta()
        for identificatore, svg in zip((statica.prima, statica.dopo),
                                       statica.fotogrammi):
            assert _albero(svg).get("data-layout-id") == identificatore

    def test_la_forma_statica_porta_il_patch_del_passo(self):
        """Il terzo lato della tripla di CV6, nel punto in cui l'artefatto esce.

        SM-14, citata da `compose.py`: un `patch_` identifica **un passo**, non un
        contenuto. Senza di esso la forma statica portava due disegni e due `lay_`
        e nessun modo di risalire al passo che li lega: `esporta()` lasciava
        cadere l'unico identificatore del passo proprio dove l'artefatto lascia
        il sistema, e nessun test o voce registrata lo nominava come scelta.
        """
        assert "patch" in {f.name for f in fields(StaticStep)}
        passo = _passo()
        assert passo.esporta().patch == passo.patch

    def test_i_due_stati_e_l_export_vengono_dalla_stessa_sorgente_semantica(self):
        """AD-10: *«l'SVG semantico verificato e' la sorgente unica di ogni formato»*.

        Il disegno interattivo e quello statico non sono due rendering dello stesso
        passo: sono lo stesso rendering, e questo e' il test che lo dice.
        """
        passo = _passo()
        statica = passo.esporta()
        interattivi = {passo.fotogramma(InteractionState(passo.prima)),
                       passo.fotogramma(InteractionState(passo.dopo))}
        assert all(f in interattivi for f in statica.fotogrammi)


# --- l'autorita' della storia · A-0 fra i due stati ---------------------------

class TestA0FraIDueStati:
    """*«Cio' che sta in `preserve` non si muove fra i due stati.»*

    La Story 1.7 misurava A-0 sui `LayoutIR`; qui si misura sui **due disegni del
    passo**, che e' la forma in cui Gate A ha qualcosa di concreto da guardare. La
    differenza non e' formale: fra il piazzamento e il byte c'e' il serializzatore,
    ed e' li' che un'entita' preservata potrebbe muoversi senza che nessun
    `LayoutIR` cambi.
    """

    def test_ogni_nodo_preservato_sta_nello_stesso_punto_nei_due_fotogrammi(self):
        passo = _passo()
        prima = _albero(passo.fotogrammi[passo.prima])
        dopo = _albero(passo.fotogrammi[passo.dopo])
        preservati = [e for e in passo.risultato.preserve if e.kind == "node"]
        assert preservati, "nessun nodo preservato: il caso non misura niente"
        for entita in preservati:
            a = _entita_emessa(prima, "data-node-id", entita.id)
            b = _entita_emessa(dopo, "data-node-id", entita.id)
            assert (a.get("cx"), a.get("cy")) == (b.get("cx"), b.get("cy")), entita

    def test_ogni_componente_preservato_e_disegnato_identico_nei_due_fotogrammi(self):
        """Non solo la posizione: **gli stessi byte** del sottoalbero emesso.

        Un componente preservato che si spostasse di un pixel, cambiasse
        orientamento o perdesse un'etichetta violerebbe A-0 allo stesso modo, e un
        confronto sulle sole coordinate del gruppo non lo vedrebbe.
        """
        passo = _passo()
        prima = _albero(passo.fotogrammi[passo.prima])
        dopo = _albero(passo.fotogrammi[passo.dopo])
        preservati = [e for e in passo.risultato.preserve if e.kind == "component"]
        assert preservati, "nessun componente preservato: il caso non misura niente"
        for entita in preservati:
            a = _entita_emessa(prima, "data-component-id", entita.id)
            b = _entita_emessa(dopo, "data-component-id", entita.id)
            assert ET.tostring(a) == ET.tostring(b), entita

    def test_cio_che_cambia_invece_non_compare_in_entrambi(self):
        """Il controllo di controllo: senza di lui A-0 sarebbe vera su un passo che
        non cambia nulla, e un passo che non cambia nulla non e' un passo."""
        passo = _passo()
        prima = _albero(passo.fotogrammi[passo.prima])
        dopo = _albero(passo.fotogrammi[passo.dopo])
        emessi = lambda r, a: {e.get(a) for e in r.iter() if e.get(a)}
        assert "R1" in emessi(prima, "data-component-id")
        assert "R1" not in emessi(dopo, "data-component-id")
        assert EQUIVALENTE.id not in emessi(prima, "data-component-id")
        assert EQUIVALENTE.id in emessi(dopo, "data-component-id")
        assert "a" in emessi(prima, "data-node-id")
        assert "a" not in emessi(dopo, "data-node-id")


# --- la composizione ----------------------------------------------------------

class TestLaComposizione:
    """I cinque atti in fila, e cio' che il passo lascia nei registri."""

    def test_i_due_stati_visuali_restano_risolvibili_dopo_il_passo(self):
        """CV6: senza `p_k` risolvibile, VCER non e' calcolabile e Gate A non ha un
        verdetto. La proiezione e' *per riferimento*, e un riferimento che non si
        risolve non e' una proiezione."""
        layouts, patches = LayoutStore(), PatchStore()
        passo = componi(CIRCUITO, "serie", "R1", "R2", layout=_layout(),
                        layouts=layouts, patches=patches,
                        istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert layouts.risolvi(passo.prima).identifier == passo.prima
        assert layouts.risolvi(passo.dopo).identifier == passo.dopo
        assert patches.risolvi(passo.patch) is passo.risultato.layout_patch

    def test_il_layout_di_partenza_gia_depositato_non_si_rideposita(self):
        """Il *dopo* di un passo e' il *prima* del successivo, e il registro e'
        append-only: ridepositarlo solleverebbe sul caso ordinario di una catena."""
        layouts, patches = LayoutStore(), PatchStore()
        partenza = _layout()
        layouts.deposita(partenza)
        passo = componi(CIRCUITO, "serie", "R1", "R2", layout=partenza,
                        layouts=layouts, patches=patches,
                        istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert len(layouts) == 2
        assert passo.prima == partenza.identifier

    def test_un_rifiuto_si_restituisce_e_non_lascia_niente_nei_registri(self):
        """AD-13: il `Refusal` e' un esito di dominio, non un'eccezione.

        Il circuito e' quello di `test_transform.py`: `R1` e `R2` sono davvero in
        parallelo, ma fonderle lascia `a` con un solo terminale — un ramo aperto —
        e `validate` rifiuta il prodotto. Il passo non esiste, quindi non deve
        esistere nemmeno la meta' di passo che i registri avrebbero conservato.
        """
        circuito = IR("1.0.0", "dc_resistive", "netlist", ("0", "a", "b"), (
            Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
            Component.of("R4", "resistor", ("b", "0"), F(40), "R4"),
            Component.of("R1", "resistor", ("a", "b"), F(10), "R1"),
            Component.of("R2", "resistor", ("a", "b"), F(20), "R2"),
        ), ())
        layouts, patches = LayoutStore(), PatchStore()
        esito = componi(circuito, "parallelo", "R1", "R2", layout=_layout(),
                        layouts=layouts, patches=patches,
                        istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert isinstance(esito, Refusal)
        assert (esito.cause, esito.subject) == ("topology", "a")
        assert len(layouts) == 0 and len(patches) == 0

    def test_una_precondizione_violata_sale_da_componi_e_non_lascia_mezzo_passo(self):
        """L'altro dei due esiti che `componi` dichiara, finora senza oracolo.

        Il docstring di `compose.py` distingue: il `Refusal` si restituisce
        (AD-13), un `ValueError` da `transform` *«e' un'altra cosa … e sale»*. Il
        primo esito aveva un test coi registri controllati; il secondo nessuno — i
        circuiti di `TestLePrecondizioniSonoFalsificabili` non passano mai da
        `componi`, quindi niente diceva che una precondizione violata attraversi
        il punto di composizione senza depositare mezzo passo. Visto rosso col
        mutante che sposta il deposito del layout sopra `transform`.
        """
        layouts, patches = LayoutStore(), PatchStore()
        with pytest.raises(ValueError, match="non e un componente"):
            componi(CIRCUITO, "serie", "R1", "R9", layout=_layout(),
                    layouts=layouts, patches=patches,
                    istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert len(layouts) == 0 and len(patches) == 0

    def test_comporre_due_volte_lo_stesso_passo_da_gli_stessi_byte(self):
        """AD-35 sulla composizione intera, non sulla sola `render`.

        Gli identificatori differiscono — sono coniati da istanti diversi — e i
        disegni no. Se coincidessero anche gli identificatori il test misurerebbe
        la ripetizione di un conio, che non e' la proprieta' che AD-35 chiede.
        """
        uno, due = _passo(), _passo(ISTANTE + 5_000)
        assert uno.prima != due.prima and uno.dopo != due.dopo
        assert (uno.fotogrammi[uno.prima].replace(uno.prima, "")
                == due.fotogrammi[due.prima].replace(due.prima, ""))
        assert (uno.fotogrammi[uno.dopo].replace(uno.dopo, "")
                == due.fotogrammi[due.dopo].replace(due.dopo, ""))


class TestLeGuardieDelPasso:
    """Cio' che rende `VisualStep` una proiezione e non una tupla di comodo."""

    def _campi(self, passo: VisualStep) -> dict:
        return {"operation": passo.operation, "prima": passo.prima,
                "dopo": passo.dopo, "patch": passo.patch,
                "risultato": passo.risultato, "fotogrammi": dict(passo.fotogrammi)}

    def test_due_stati_visuali_uguali_non_sono_un_passo(self):
        passo = _passo()
        campi = self._campi(passo)
        campi["dopo"] = campi["prima"]
        campi["fotogrammi"] = {campi["prima"]: passo.fotogrammi[passo.prima]}
        with pytest.raises(ValueError, match="sono lo stesso"):
            VisualStep(**campi)

    def test_l_operazione_dichiarata_deve_essere_quella_certificata(self):
        """Il certificato e' l'unico dei due ad aver verificato l'operazione."""
        passo = _passo()
        campi = self._campi(passo)
        campi["operation"] = "parallelo"
        with pytest.raises(ValueError, match="si dichiara 'parallelo'"):
            VisualStep(**campi)

    def test_un_fotogramma_senza_il_proprio_stato_visuale_e_rifiutato(self):
        passo = _passo()
        campi = self._campi(passo)
        campi["fotogrammi"] = {passo.prima: passo.fotogrammi[passo.prima]}
        with pytest.raises(ValueError, match="Un disegno senza il proprio"):
            VisualStep(**campi)

    def test_i_fotogrammi_sono_congelati_alla_costruzione(self):
        """Una mappa condivisa col chiamante lascerebbe sostituire un disegno dopo
        che le guardie sono passate — la stessa ragione per cui `LayoutIR` congela i
        piazzamenti."""
        passo = _passo()
        campi = self._campi(passo)
        mutabile = campi["fotogrammi"]
        nuovo = VisualStep(**campi)
        mutabile[nuovo.prima] = "<svg/>"
        assert nuovo.fotogrammi[nuovo.prima] != "<svg/>"
        with pytest.raises(TypeError):
            nuovo.fotogrammi[nuovo.prima] = "<svg/>"

    def test_gli_identificatori_sono_verificati_per_genere(self):
        passo = _passo()
        campi = self._campi(passo)
        campi["patch"] = passo.prima
        with pytest.raises(ValueError):
            VisualStep(**campi)

    def test_i_due_fotogrammi_devono_differire_e_non_solo_i_due_lay(self):
        """La ragione della guardia sui `lay_` vale identica sui byte, e non discendeva.

        *«Commutare non mostrerebbe niente»* e' vero anche per due disegni uguali
        carattere per carattere sotto due identificatori diversi, e quel caso si
        costruiva: `applica` conia sempre un `lay_` nuovo, anche per un passo il cui
        rendering non cambiasse. Due `lay_` distinti dicono che il registro conserva
        due stati; solo due disegni distinti dicono che c'e' qualcosa da commutare.
        """
        passo = _passo()
        campi = self._campi(passo)
        campi["fotogrammi"] = {passo.prima: passo.fotogrammi[passo.prima],
                               passo.dopo: passo.fotogrammi[passo.prima]}
        with pytest.raises(ValueError, match="sono gli stessi byte"):
            VisualStep(**campi)

    def test_i_fotogrammi_scambiati_fra_i_due_stati_sono_rifiutati(self):
        """L'unico caso silenzioso fra quelli non guardati, e il piu' costoso.

        Le altre guardie prendono vuoto, tre, non-tupla, uguali — forme che si
        notano. Due disegni giusti sotto gli identificatori invertiti superavano
        invece ogni controllo, e `fotogramma(apertura())` restituiva il disegno
        del **dopo**: il caso esatto che `apertura()` esiste per escludere
        (UX-DR22), servito senza che nulla protestasse. I byte dichiarano gia' di
        quale stato sono (`data-layout-id`, sulla radice): la guardia esige che la
        dichiarazione e la chiave coincidano.
        """
        passo = _passo()
        campi = self._campi(passo)
        campi["fotogrammi"] = {passo.prima: passo.fotogrammi[passo.dopo],
                               passo.dopo: passo.fotogrammi[passo.prima]}
        with pytest.raises(ValueError, match="dichiara nei byte di essere"):
            VisualStep(**campi)


class TestLeGuardieDellaFormaStatica:
    """`StaticStep` e' esportato, e il tipo non dice chi ha il diritto di costruirlo.

    `esporta()` produce istanze corrette per costruzione. Ma il tipo sta in
    `__all__` ed e' *«cio' che `export()` consumera'»*: senza guardie la proprieta'
    di AD-10 — *«stessi byte, stessa sorgente semantica»* — varrebbe per le istanze
    che escono da `esporta()` e per nessun'altra, e niente lo direbbe. E' la
    convenzione che questo repository dichiara: ogni invariante ha una guardia a
    runtime **e un test che l'ha vista sollevare**.

    Prima di queste guardie `StaticStep(operation="serie", prima="non-un-lay",
    dopo="non-un-lay", fotogrammi=("",))` si costruiva senza proteste: quattro
    invarianti violati in una riga.
    """

    def _campi(self, passo: VisualStep) -> dict:
        statica = passo.esporta()
        return {"operation": statica.operation, "prima": statica.prima,
                "dopo": statica.dopo, "patch": statica.patch,
                "fotogrammi": statica.fotogrammi}

    def test_la_riga_che_prima_passava_ora_non_passa(self):
        """L'esatto controesempio del rilievo, piu' il `patch` che la seconda
        revisione ha aggiunto al tipo: senza un valore il controesempio non
        arriverebbe alle guardie che deve vedere sollevare."""
        with pytest.raises(ValueError):
            StaticStep(operation="serie", prima="non-un-lay", dopo="non-un-lay",
                       patch="non-un-patch", fotogrammi=("",))

    def test_l_operazione_deve_stare_nel_catalogo(self):
        passo = _passo()
        campi = self._campi(passo) | {"operation": "trasfigurazione"}
        with pytest.raises(ValueError, match="fuori dal catalogo chiuso"):
            StaticStep(**campi)

    def test_gli_identificatori_sono_verificati_per_genere(self):
        """Anche il `patch` della seconda revisione: stessa `verifica`, per genere."""
        passo = _passo()
        for guasto in ({"prima": passo.patch}, {"patch": passo.prima}):
            campi = self._campi(passo) | guasto
            with pytest.raises(ValueError):
                StaticStep(**campi)

    def test_i_due_stati_visuali_devono_differire(self):
        passo = _passo()
        campi = self._campi(passo) | {"dopo": passo.prima}
        with pytest.raises(ValueError, match="sono lo stesso"):
            StaticStep(**campi)

    def test_i_fotogrammi_sono_una_tupla_perche_l_ordine_e_l_unica_sequenza(self):
        """Senza un comando da premere, la sequenza dice quale disegno viene prima:
        una collezione senza ordine dichiarato non lo direbbe (UX-DR27)."""
        passo = _passo()
        campi = self._campi(passo) | {"fotogrammi": list(passo.esporta().fotogrammi)}
        with pytest.raises(TypeError, match="invece di tuple"):
            StaticStep(**campi)

    def test_i_fotogrammi_sono_due(self):
        passo = _passo()
        statica = passo.esporta()
        for quanti in ((statica.fotogrammi[0],), (*statica.fotogrammi, "<svg/>")):
            campi = self._campi(passo) | {"fotogrammi": quanti}
            with pytest.raises(ValueError, match="fotogrammi invece di due"):
                StaticStep(**campi)

    def test_un_fotogramma_vuoto_non_e_una_sorgente(self):
        """AD-10 chiama i due disegni la sorgente unica di ogni altro formato."""
        passo = _passo()
        for guasto in ("", "   ", None):
            campi = self._campi(passo) | {
                "fotogrammi": (guasto, passo.esporta().fotogrammi[1])}
            with pytest.raises(ValueError, match="vuoto o non testuale"):
                StaticStep(**campi)

    def test_i_due_fotogrammi_devono_differire(self):
        passo = _passo()
        uguale = passo.esporta().fotogrammi[0]
        campi = self._campi(passo) | {"fotogrammi": (uguale, uguale)}
        with pytest.raises(ValueError, match="sono gli stessi byte"):
            StaticStep(**campi)

    def test_i_fotogrammi_scambiati_sono_rifiutati(self):
        """Nella forma statica lo scambio e' ancora piu' muto che nel passo.

        Non c'e' un comando da premere: la sequenza `prima → dopo` e' l'unica cosa
        che dice quale disegno viene prima (UX-DR27), e due disegni scambiati la
        rispettano esattamente al contrario — l'etichetta *Prima* sopra il passo
        gia' compiuto. Le sette guardie della prima revisione non lo vedevano.
        """
        passo = _passo()
        statica = passo.esporta()
        campi = self._campi(passo) | {
            "fotogrammi": (statica.fotogrammi[1], statica.fotogrammi[0])}
        with pytest.raises(ValueError, match="dichiara nei byte di essere"):
            StaticStep(**campi)

    def test_un_fotogramma_che_non_dichiara_il_proprio_stato_e_rifiutato(self):
        """Le due forme del difetto: byte che non sono un documento, e un documento
        senza `data-layout-id`. Per chi costruisce il passo sono lo stesso fatto —
        il disegno non dice di quale stato e', quindi non e' attribuibile."""
        passo = _passo()
        for muto in ("non sono un documento svg", "<svg><g/></svg>"):
            campi = self._campi(passo) | {
                "fotogrammi": (muto, passo.esporta().fotogrammi[1])}
            with pytest.raises(ValueError, match="nessuno stato visuale"):
                StaticStep(**campi)

    def test_cio_che_esporta_produce_regge_alle_proprie_guardie(self):
        """Il verso positivo: le guardie non rifiutano l'unico costruttore vero."""
        assert isinstance(_passo().esporta(), StaticStep)


class TestLEntitaEstraneaAlPasso:
    """Le tre risposte di FR-49 su qualcosa che nel passo non c'e'.

    `commuta` e `fotogramma` sollevavano gia' su uno stato visuale estraneo, con la
    ragione scritta nel docstring: *«rispondere `prima` lo renderebbe silenzioso,
    mostrando all'utente il disegno sbagliato senza che nulla se ne accorga»*. Le
    tre risposte dell'AC2 sono la stessa classe d'ingresso e avevano la risposta
    opposta — `()`, `False`, `None` — su un'entita' che non sta ne' in `Cₖ` ne' in
    `Cₖ₊₁`.

    `e_lo_stesso` e' il caso che mostra perche' il silenzio non e' innocuo:
    rispondeva `False`, cioe' **affermava** «non e' la stessa attraverso il passo»
    di qualcosa che nel passo non c'e'. E' un claim senza evidenza (K-2).
    """

    ESTRANEE = (C("R99"), N("z"))

    @pytest.mark.parametrize("estranea", ESTRANEE, ids=lambda e: str(e))
    def test_le_tre_risposte_sollevano_invece_di_rispondere(self, estranea):
        passo = _passo()
        for domanda in (passo.deriva_da, passo.e_lo_stesso, passo.che_ne_e_stato):
            with pytest.raises(ValueError, match="non e' un'entita' di questo passo"):
                domanda(estranea)

    def test_le_tre_risposte_esigono_un_EntityRef(self):
        """Le risposte si leggono dal `Delta` e da `preserve`, che nominano entita'."""
        passo = _passo()
        for domanda in (passo.deriva_da, passo.e_lo_stesso, passo.che_ne_e_stato):
            with pytest.raises(TypeError, match="invece di EntityRef"):
                domanda("R1")

    def test_vuoto_e_none_restano_risposte_legittime_per_le_entita_del_passo(self):
        """La guardia non deve inghiottire i due casi che dicono qualcosa.

        `deriva_da(node:a)` e' vuoto perche' da `a` non nasce niente, e
        `che_ne_e_stato(node:b)` e' `None` perche' il passo non l'ha toccato. Sono
        risposte, e restano distinguibili dal caso estraneo solo perche' il caso
        estraneo ora solleva.
        """
        passo = _passo()
        assert passo.deriva_da(N("a")) == ()
        assert passo.che_ne_e_stato(N("b")) is None
        assert passo.e_lo_stesso(C("R1")) is False

    @pytest.mark.parametrize("caso", ("serie", "parallelo", "catena, primo passo",
                                      "catena, secondo passo"))
    def test_le_entita_del_passo_sono_l_unione_dei_due_circuiti(self, caso):
        """`Pₖ ∪ consumed ∪ produced = Entities(Cₖ) ∪ Entities(Cₖ₊₁)`, esatta.

        Le tre parti sono disgiunte e non c'e' una quarta classe: e' quel che rende
        la domanda «e' di questo passo?» rispondibile **senza risolvere nessun
        `CircuitIR`**, cioe' restando la proiezione per riferimento di AD-21.

        La seconda revisione l'ha voluta su **ogni** forma di passo che la suite sa
        comporre, non su una fixture sola: un'unione a cui mancasse qualcosa
        farebbe sollevare `e_lo_stesso(x)` dove la risposta corretta e' `True` —
        una falsa accusa, cioe' il difetto peggiore di questo prodotto. La clausola
        non e' una proprieta' del tipo: la impongono i controllori del motore, e il
        docstring di `entita` dice quali e dove. Qui la si misura.
        """
        passo, prima_ir, dopo_ir = _passo_e_circuiti(caso)
        entita = lambda ir: ({C(c.id) for c in ir.components}
                             | {N(n) for n in ir.nodes})
        assert passo.entita == entita(prima_ir) | entita(dopo_ir)


class TestLaCatenaDiDuePassi:
    """*«Il dopo di un passo e' il prima del successivo»*, eseguito invece che detto.

    Il ramo `if layout.identifier not in layouts` di `componi` esiste per questo
    caso, e l'unico test che lo toccava simulava la catena depositando il layout a
    mano. Qui i due passi si compongono davvero, in fila.
    """

    def _catena(self):
        layouts, patches = LayoutStore(), PatchStore()
        uno = componi(CATENA, "serie", "R1", "R2", layout=_layout_catena(),
                      layouts=layouts, patches=patches,
                      istante=ISTANTE + 1_000, casualita=ENTROPIA)
        assert isinstance(uno, VisualStep)
        # `componi` scarta `Cₖ₊₁`: per il secondo passo va **rieseguita** la
        # trasformazione. E' il costo ergonomico registrato in `deferred-work.md`
        # — Story 1.8, seconda revisione, voce 8 — e questo test e' il posto in
        # cui si vede.
        dopo_ir, _ = transform(CATENA, "serie", "R1", "R2")
        due = componi(dopo_ir, "serie", "R1R2eq", "R3",
                      layout=layouts.risolvi(uno.dopo),
                      layouts=layouts, patches=patches,
                      istante=ISTANTE + 2_000, casualita=ENTROPIA)
        assert isinstance(due, VisualStep)
        return layouts, patches, uno, due

    def test_il_dopo_del_primo_e_il_prima_del_secondo(self):
        _, _, uno, due = self._catena()
        assert due.prima == uno.dopo

    def test_il_registro_append_only_non_solleva_e_conserva_tre_stati(self):
        """Il ramo scritto per la catena, percorso dalla catena.

        Tre `lay_` e non quattro: lo stato intermedio e' depositato una volta sola
        pur essendo il *dopo* di un passo e il *prima* dell'altro. Ridepositarlo
        solleverebbe, ed e' cio' che il ramo evita.
        """
        layouts, patches, uno, due = self._catena()
        assert len(layouts) == 3
        assert len(patches) == 2
        assert set(layouts.identificatori()) == {uno.prima, uno.dopo, due.dopo}

    def test_i_due_passi_restano_risolvibili_tutti_e_due(self):
        """CV6 sulla catena: `p_k(x)` deve esistere per **ogni** passo, non per
        l'ultimo. Un registro che perdesse lo stato intermedio renderebbe VCER
        incalcolabile sul primo passo nel momento in cui il secondo e' composto."""
        layouts, patches, uno, due = self._catena()
        for passo in (uno, due):
            assert layouts.risolvi(passo.prima).identifier == passo.prima
            assert layouts.risolvi(passo.dopo).identifier == passo.dopo
            assert patches.risolvi(passo.patch) is passo.risultato.layout_patch

    def test_il_secondo_passo_e_un_passo_intero_come_il_primo(self):
        """La catena non degrada il secondo passo a un mezzo passo: due fotogrammi,
        una giustificazione a quattro campi, una forma statica."""
        _, _, _, due = self._catena()
        assert set(due.fotogrammi) == {due.prima, due.dopo}
        assert due.giustificazione.certificato.operation == "serie"
        assert isinstance(due.esporta(), StaticStep)
        assert due.deriva_da(C("R1R2eqR3eq")) == (C("R1R2eq"), C("R3"))

    def test_cio_che_sopravvive_ai_due_passi_non_si_e_mosso(self):
        """A-0 attraverso **due** passi: `V1` e `node:0` stanno nello stesso punto
        nel primo fotogramma della catena e nell'ultimo. E' la proprieta' che
        `EXPERIENCE.md` chiede a `C₀ → T₁ → C₁ → T₂ → C₂`, e un passo solo non la
        puo' misurare."""
        _, _, uno, due = self._catena()
        primo = _albero(uno.fotogrammi[uno.prima])
        ultimo = _albero(due.fotogrammi[due.dopo])
        for attributo, identificatore in (("data-component-id", "V1"),
                                          ("data-node-id", "0"),
                                          ("data-node-id", "b")):
            a = _entita_emessa(primo, attributo, identificatore)
            b = _entita_emessa(ultimo, attributo, identificatore)
            assert (a.get("cx"), a.get("cy")) == (b.get("cx"), b.get("cy")), \
                identificatore


# --- misure registrate, non riparate -----------------------------------------

class TestLeMisureRegistrate:
    """Tre fatti misurati che questa storia **non** chiude, e la ragione di ciascuno.

    E' la forma che la Story 1.7 ha usato per `test_l_overlay_allarga_la_viewbox_e_
    questo_e_dichiarato`: *«il test fissa la misura perche' chi decide la trovi, non
    perche' il numero conti»*. Ognuno dei tre e' reale, verificato per esecuzione, e
    la sua riparazione richiede una decisione che nessun criterio di accettazione di
    questa storia prende. Il verso che conta e' che d'ora in poi **cambiare il
    comportamento fa fallire un test**, invece di passare inosservato.
    """

    def _viewbox(self, svg: str) -> tuple[F, F, F, F]:
        x, y, larga, alta = (F(v) for v in _albero(svg).get("viewBox").split())
        return x, y, larga, alta

    def test_i_due_fotogrammi_hanno_viewbox_diverse(self):
        """A-0 e' definita su `p_k(x)`, e questa e' l'altra meta' che nessuno misura.

        UX-DR17 scrive A-0 come invariante **semantico-spaziale, non pixel-perfect**:
        `id_{k+1}(x) = id_k(x)` senza eccezioni, `p_{k+1}(x) ≈ p_k(x)` *«salvo
        necessita' geometriche dimostrabili, comunque misurate e penalizzate da
        VCER»*. `TestA0FraIDueStati` confronta coordinate in spazio utente, che e'
        esattamente cio' che `p_k(x)` significa: quei test misurano la cosa giusta.

        Ma l'`<svg>` non porta `width`/`height` — scala col contenitore (UX-DR27) —
        e le due `viewBox` differiscono **di origine e di dimensione**, non solo di
        larghezza. In un riquadro di larghezza fissa ogni entita' preservata si
        sposta percio' a schermo, pur non essendosi mossa in spazio utente. E' la
        «necessita' geometrica» che UX-DR17 dice di misurare, e la misura e' questa.

        **Perche' non e' riparata qui.** Unificare le due `viewBox` significa
        decidere che i due fotogrammi di un passo condividono un riquadro — cioe'
        scegliere quale delle due letture di FR-53 governi, che e' la decisione che
        la Story 1.7 ha registrato e lasciata aperta per non chiudere D4 per inerzia
        (*«renderer stack web vs PDF»*, aperta, blocca Gate A). Il rilievo della 1.7
        riguardava *overlay vs senza overlay*, dove l'**origine restava uguale**;
        questa e' la variante *fra i due fotogrammi dello stesso passo*, e ha una
        forma diversa. Registrata in `deferred-work.md`.
        """
        passo = _passo()
        prima = self._viewbox(passo.fotogrammi[passo.prima])
        dopo = self._viewbox(passo.fotogrammi[passo.dopo])
        assert prima != dopo
        assert prima[1] != dopo[1], "l'origine differisce: e' la variante nuova"
        assert (prima[2], prima[3]) != (dopo[2], dopo[3]), "e anche la dimensione"
        for lay in (passo.prima, passo.dopo):
            radice = _albero(passo.fotogrammi[lay])
            assert radice.get("width") is None and radice.get("height") is None

    def test_il_fotogramma_di_apertura_porta_gia_l_equazione_del_passo(self):
        """Il contro-controllo che mancava accanto a `apertura()`.

        `apertura()` restituisce `prima` e ne scrive la ragione: *«aprire su `dopo`
        mostrerebbe il passo gia' compiuto»*. Il fotogramma d'apertura enuncia pero'
        il passo compiuto lo stesso — nel layer 6 c'e' `R1R2eq = R1 + R2`, il nome
        dell'equivalente che in `Cₖ` non esiste, e la sua formula. La causa e' la
        scelta di `componi` di usare **un solo overlay** per i due render, che porta
        con se' l'equazione su entrambi.

        `test_cio_che_cambia_invece_non_compare_in_entrambi` sta accanto a questo
        fatto e non lo vede: guarda i `data-component-id`, dove `R1R2eq` davvero non
        compare in `prima`, e non guarda il testo del layer 6.

        **Perche' non e' riparato qui.** `EXPERIENCE.md` distingue tre momenti — 3-4
        *PRIMA* (*«non e' ancora comparso un solo carattere di testo»*), 5 *AZIONE*
        (l'equazione compare), 6 *DOPO* — e `VisualStep` ne ha **due**. Decidere a
        quale dei due fotogrammi appartenga l'equazione e' una scelta di sequenza
        UX che nessun criterio di questa storia prende, e realizzarla significa
        rendere opzionale `TransformOverlay.equazione`, cioe' allentare una guardia
        che la Story 1.7 ha scritto apposta. Registrata in `deferred-work.md`.
        """
        passo = _passo()
        testi = lambda lay: [e.text for e in _albero(passo.fotogrammi[lay]).iter()
                             if e.get("class") == "kf-equazione-testo"]
        assert testi(passo.prima) == ["R1R2eq = R1 + R2"]
        assert testi(passo.prima) == testi(passo.dopo)
        # E il verso che rende il fatto un difetto e non una scelta: l'equivalente
        # non e' fra le entita' che `Cₖ` disegna, ma il suo nome e' scritto.
        emessi = {e.get("data-component-id")
                  for e in _albero(passo.fotogrammi[passo.prima]).iter()}
        assert EQUIVALENTE.id not in emessi

    def test_i_due_identificatori_del_passo_nascono_dalla_stessa_entropia(self):
        """`componi` conia due volte da un solo `(istante, casualita)`.

        `conia` documenta l'entropia come *«nuova a ogni conio»* e il messaggio
        d'errore di `PatchStore.deposita` la chiama *«entropia nuova a ogni
        chiamata»*; l'unico chiamante in `src/` la riusa, e la firma non offre modo
        di fornirne due. Ne segue che le 26 cifre del `lay_` del *dopo* e quelle del
        `patch_` coincidono, e ciascuno e' ricavabile dall'altro.

        **Il danno oggi e' nullo e va detto:** i due generi hanno prefissi diversi,
        quindi non collidono in nessun registro — la ragione per cui `conia` chiede
        entropia nuova e' proprio la collisione. Cio' che e' violato e' il
        contratto dichiarato, e il costo si presenta il giorno in cui `componi`
        conia due identificatori **dello stesso** genere.

        **Perche' non e' riparato qui.** Le due strade sono cambiare la firma
        pubblica di `componi` perche' accetti due entropie, o derivarne una seconda
        da quella ricevuta — cioe' introdurre un meccanismo di derivazione che
        nessun port dello spine nomina, in un repository che registra le assunzioni
        non ratificate invece di installarle. Registrata in `deferred-work.md`.
        """
        passo = _passo()
        assert passo.dopo.removeprefix("lay_") == passo.patch.removeprefix("patch_")
        # Il verso di controllo: il `lay_` di **partenza** ha invece cifre proprie,
        # perche' nasce da un conio che `componi` non fa.
        assert passo.prima.removeprefix("lay_") != passo.patch.removeprefix("patch_")

    def test_l_alternativa_testuale_non_racconta_il_passo(self):
        """AC1 e AC2 per chi non vede i due disegni: oggi non esistono.

        I due `<desc>` — l'unico rendering del passo disponibile a chi legge con
        un lettore di schermo — differiscono, e la differenza non basta: nessuno
        dei due dice che una trasformazione e' avvenuta, ne' da che cosa `R1R2eq`
        derivi. L'equazione sta nel layer 6 **visuale** e in nessun testo
        alternativo. Il rapporto della prima iterazione liquidava il fatto con
        «vale anche fra i due fotogrammi»; misurato, e' piu' preciso di cosi': la
        differenza c'e', e' la **narrazione** a mancare.

        **Perche' non e' riparato qui.** Il `<desc>` e' l'alternativa testuale
        della **topologia** di un circuito (Story 1.4, `alternativa_testuale`),
        non del passo: fargli raccontare la trasformazione significa decidere la
        narrazione accessibile del passo — quale testo, in quale dei due
        fotogrammi, o in un canale terzo — cioe' la stessa famiglia di decisioni
        della voce sull'equazione d'apertura, su un canale che nessun criterio
        della 1.8 nomina. Registrata in `deferred-work.md`.
        """
        passo = _passo()
        desc = lambda lay: next(e.text for e in _albero(passo.fotogrammi[lay]).iter()
                                if e.tag == f"{SVG}desc")
        prima, dopo = desc(passo.prima), desc(passo.dopo)
        # La meta' vera della frase del rapporto: i due testi differiscono.
        assert prima != dopo
        # E la meta' che mancava: l'equivalente e' nominato, la sua storia no —
        # tolto il suo nome, `R1` e `R2` non compaiono, e nessuno dei due testi
        # contiene una parola di trasformazione o derivazione.
        assert "R1R2eq" in dopo
        senza_equivalente = dopo.replace("R1R2eq", "")
        assert "R1" not in senza_equivalente and "R2" not in senza_equivalente
        for testo in (prima, dopo):
            assert "serie" not in testo
            assert "trasforma" not in testo
            assert "deriva" not in testo
