"""Story 1.7 — la prima trasformazione pedagogica, **fino al disegno**.

> «La storia **non e' completa** se produce solo `CircuitIR_before →
> CircuitIR_after`. Deve arrivare allo stato visuale verificato.»

K-0 come criterio di accettazione: *un passo senza disegno non e' un passo*. Le due
meta' della storia stanno quindi in due posti, e questo file le lega:

| AC | Che cosa afferma | Dove si verifica |
|---|---|---|
| AC1 | i sei membri del `TransformResult`, tutti non vuoti | `test_il_prodotto_porta_i_sei_membri…` |
| AC2 | `{R1, R2} → {Req}`, lineage nelle due direzioni | `test_il_delta_dice_che_le_due_sono_diventate_quella` · `test_la_lineage_risponde_nelle_due_direzioni` |
| AC3 | A-0: cio' che e' in `preserve` **non si e' mosso** | `test_cio_che_e_preservato_non_si_e_mosso_di_un_pixel` e i quattro seguenti |
| AC4 | l'equazione **accanto** al sottografo, non sotto il disegno (UX-DR10) | `test_l_equazione_sta_accanto_al_sottografo…` · `test_l_equazione_non_sta_sotto_il_disegno` |
| AC5 | il sottografo evidenziato **prima di qualunque testo** (UX-DR8) | `test_il_sottografo_si_accende_prima_di_qualunque_testo_del_passo` |

La fixture e' quella della Story 1.4 — `V1`, `R1`, `R2`, `LayoutIR` predefinito — e
non e' un riuso di comodo: `R1(b,a)` e `R2(a,0)` sono **gia'** in serie, il nodo `a`
ha grado due e non e' il riferimento. La prima trasformazione pedagogica si applica
al disegno su cui il serializzatore e' stato scritto, che e' il modo di sapere che le
due meta' si incontrano davvero.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from fractions import Fraction as F

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.transform import (
    Delta,
    EntityRef,
    Equation,
    LayoutPatch,
    StructuralDerivation,
    transform,
)
from kirchhoff.render.layout import (
    LayoutIR,
    LayoutStore,
    PatchStore,
    Placement,
    applica,
    mosse,
    operandi_di_vcer,
)
from kirchhoff.render.overlay import TransformOverlay, annota
from kirchhoff.render.serialize import Punto, render
from kirchhoff.render.serialize.geometry import scena
from kirchhoff.render.serialize.svg import (
    _AVANZAMENTO_MONOSPAZIO,
    _IMBOTTITURA,
    _LARGHEZZA_DEL_GLIFO,
    _SOPRA_LA_BASE,
    _SOTTO_LA_BASE,
    _TRATTO_EQUAZIONE,
    CORPO_EQUAZIONE,
    _estensione_emessa,
)

SVG = "{http://www.w3.org/2000/svg}"
ENTROPIA = bytes(range(10))
ISTANTE = 1_755_000_000_000

C = lambda i: EntityRef("component", i)
N = lambda i: EntityRef("node", i)


# --- la fixture: la stessa della Story 1.4, che e' gia' riducibile in serie ---

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

#: L'equivalente che `serie` conia da `R1` e `R2`. Il nome lo fa `engine._nuovo_id`:
#: qui si legge, non si ridichiara, perche' una seconda dichiarazione sarebbe la
#: stessa cosa scritta due volte e terrebbe verdi i test anche se il motore cambiasse.
EQUIVALENTE = C("R1R2eq")


def _prima(istante: int = ISTANTE) -> LayoutIR:
    return LayoutIR.nuovo(PIAZZAMENTI, istante=istante, casualita=ENTROPIA)


def _passo():
    """Il passo intero: `Cₖ`, `Cₖ₊₁`, il prodotto, i due stati visuali, l'overlay."""
    prima = _prima()
    dopo_ir, risultato = transform(CIRCUITO, "serie", "R1", "R2")
    dopo = applica(prima, risultato.layout_patch, risultato.delta,
                   istante=ISTANTE + 1_000, casualita=ENTROPIA)
    return CIRCUITO, dopo_ir, risultato, prima, dopo, annota(risultato)


def _albero(testo: str) -> ET.Element:
    return ET.fromstring(testo)


def _riquadro(elemento: ET.Element) -> tuple[Punto, Punto]:
    """Il riquadro di un `<rect>` emesso, riletto dai byte e non dalle strutture."""
    x, y = F(elemento.get("x")), F(elemento.get("y"))
    return (Punto(x, y),
            Punto(x + F(elemento.get("width")), y + F(elemento.get("height"))))


# --- AC1 · i sei membri, tutti non vuoti -------------------------------------

def test_il_prodotto_porta_i_sei_membri_e_nessuno_e_vuoto():
    """AD-22: *«Ogni campo e' non-vuoto o il prodotto non e' costruibile.»*

    Si guarda ogni membro **per nome**, invece di fidarsi del fatto che il
    costruttore sia passato: un campo aggiunto domani senza guardia non farebbe
    cadere un test che conta soltanto.
    """
    _, _, r, _, _, _ = _passo()
    assert r.preserve
    assert r.delta.derivations
    assert r.boundary.entities
    assert (r.layout_patch.preserve or r.layout_patch.remove
            or r.layout_patch.create)
    assert r.equation.subject and r.equation.expression
    assert r.certificate.checks


def test_il_certificato_elenca_i_controlli_eseguiti_e_nomina_serie():
    """E-65: il `Certificate` non dichiara «valido», elenca cio' che ha girato."""
    _, _, r, _, _, _ = _passo()
    assert r.certificate.operation == "serie"
    assert "validazione elettrica di Cₖ₊₁" in r.certificate.checks


# --- AC2 · `{R1, R2} → {Req}`, interrogabile nelle due direzioni --------------

def test_il_delta_dice_che_le_due_sono_diventate_quella():
    """La riga che la storia chiede, letta come derivazione e non come frase."""
    _, _, r, _, _, _ = _passo()
    fusione = next(d for d in r.delta.derivations
                   if d.operation == "fusione_di_componenti")
    assert set(fusione.inputs) == {C("R1"), C("R2")}
    assert set(fusione.outputs) == {EQUIVALENTE}


def test_la_lineage_risponde_nelle_due_direzioni():
    """Avanti da `R1`, indietro da `Req`. Nessun indice parallelo: cade dal modello."""
    _, _, r, _, _, _ = _passo()
    assert r.delta.derived_from(EQUIVALENTE) == (C("R1"), C("R2"))
    for sorgente in (C("R1"), C("R2")):
        assert r.delta.what_happened_to(sorgente).outputs == (EQUIVALENTE,)


def test_anche_il_nodo_assorbito_risponde_invece_di_tacere():
    """`serie` cancella il nodo comune: chiederne il destino non da' `None`.

    E' l'altra meta' di «interrogabile nelle due direzioni». Un nodo che sparisce
    senza lasciare una derivazione sarebbe muto proprio nel punto in cui lo studente
    chiede *«e quel nodo dov'e' finito?»*.
    """
    _, _, r, _, _, _ = _passo()
    assert r.delta.what_happened_to(N("a")).operation == "eliminazione_di_nodo"


# --- AC3 · A-0, sul disegno risultante ----------------------------------------

def test_cio_che_e_preservato_non_si_e_mosso_di_un_pixel():
    """A-0, e non «quasi».

    Il confronto e' sull'**oggetto** `Placement`, non su `abs(dopo - prima) < eps`.
    `applica` riusa i piazzamenti dei sopravvissuti invece di ricalcolarli, quindi non
    esiste un percorso in cui una coordinata preservata passi per un'aritmetica: una
    tolleranza qui misurerebbe una liberta' che la funzione non ha, e la lascerebbe
    entrare il giorno in cui qualcuno la prendesse.
    """
    _, _, r, prima, dopo, _ = _passo()
    assert r.preserve                      # l'insieme su cui A-0 si pronuncia
    for entita in r.preserve:
        assert dopo.posizione(entita) == prima.posizione(entita), entita


def test_lo_stato_visuale_di_partenza_esce_intatto_dall_applicatore():
    """U2 di CV6: *«applicare un `LayoutPatch` aggiorna il layout in luogo»* e' la
    lettura **vietata** — sotto U2 `p_k` non esiste piu' quando servirebbe misurarlo."""
    prima = _prima()
    fotografia = (prima.identifier, prima.placements)
    _, r = transform(CIRCUITO, "serie", "R1", "R2")
    applica(prima, r.layout_patch, r.delta, istante=ISTANTE + 1, casualita=ENTROPIA)
    assert (prima.identifier, prima.placements) == fotografia


def test_i_due_stati_visuali_stanno_nello_stesso_registro():
    """Il contratto scritto in 1.3 si controlla qui: un applicatore che riusasse il
    `lay_` farebbe sollevare `LayoutStore.deposita` con «gia' depositato»."""
    _, _, _, prima, dopo, _ = _passo()
    registro = LayoutStore()
    assert registro.deposita(prima) != registro.deposita(dopo)
    assert len(registro) == 2


def test_la_tripla_di_cv6_regge_sul_passo_appena_prodotto():
    """Le cinque condizioni di `operandi_di_vcer`, sul prodotto vero e non su una
    fixture costruita per superarle. Senza `preserve` risolvibile in **entrambi** gli
    stati, `p_k(x)` non e' definita e VCER resta un'ipotesi."""
    from kirchhoff.domain.identity import conia
    from kirchhoff.domain.proof import ProofEdge, ProofGraph, ProofNode

    _, _, r, prima, dopo, _ = _passo()
    layout, patch = LayoutStore(), PatchStore()
    layout.deposita(prima)
    layout.deposita(dopo)
    patch_id = patch.deposita(r.layout_patch, istante=ISTANTE + 2,
                              casualita=ENTROPIA)

    sorgente = conia("ir", ISTANTE, ENTROPIA)
    bersaglio = conia("ir", ISTANTE + 1_000, ENTROPIA)
    grafo = ProofGraph(
        (ProofNode(sorgente, prima.identifier),
         ProofNode(bersaglio, dopo.identifier)),
        (ProofEdge(sorgente, bersaglio, "serie", patch_id),))
    (tripla,) = operandi_di_vcer(grafo, layout, patch)
    assert set(tripla.dominio()) == r.preserve


def test_l_equivalente_nasce_dove_stavano_le_due_che_sostituisce():
    """*«Quelle due sono diventate questa»*, come posizione e non come frase.

    Il baricentro di `R1` e `R2` e' esatto: due `Fraction`, nessun `float`. Non e'
    autolayout — la posizione si **legge** dalla lineage, non si sceglie.
    """
    _, _, _, prima, dopo, _ = _passo()
    atteso = ((prima.posizione(C("R1")).x + prima.posizione(C("R2")).x) / 2,
              (prima.posizione(C("R1")).y + prima.posizione(C("R2")).y) / 2)
    piazzamento = dopo.posizione(EQUIVALENTE)
    assert (piazzamento.x, piazzamento.y) == atteso


def test_cio_che_sparisce_non_e_piu_piazzato():
    _, _, r, _, dopo, _ = _passo()
    assert dopo.entita() & frozenset(r.layout_patch.remove) == frozenset()


def test_il_disegno_risultante_e_quello_del_circuito_risultante():
    """K-0: si arriva **allo stato visuale**, non a due `CircuitIR`. Se il layout
    prodotto non fosse disegnabile insieme al circuito prodotto, la storia si
    fermerebbe un passo prima del criterio che la definisce."""
    _, dopo_ir, _, _, dopo, _ = _passo()
    disegno = scena(dopo_ir, dopo)
    assert [s.componente for s in disegno.simboli] == ["R1R2eq", "V1"]
    assert [g.nodo for g in disegno.giunzioni] == ["0", "b"]


# --- AC3 · le guardie dell'applicatore ----------------------------------------

#: Uno `reroute_scope` che copre ogni entita' della fixture: `LayoutPatch` lo pretende
#: non vuoto, e le guardie provate qui sotto non lo riguardano — quella che lo riguarda
#: e' `test_una_coordinata_che_cambia_fuori_dallo_scope…`, e dichiara il proprio.
SCOPE = (C("R1"), C("R2"), C("V1"), C("nuova"), N("a"), N("b"), N("0"))


def _patch(preserve=(), remove=(), create=(), scope=SCOPE) -> LayoutPatch:
    return LayoutPatch(preserve, remove, create, scope)


def _delta(*derivazioni: StructuralDerivation) -> Delta:
    """Un `Delta` coerente con la patch che lo accompagna.

    Le guardie qui sotto provano **una** incoerenza per volta, e ognuna e' l'ultima
    della catena che il chiamante attraversa: la coerenza fra la patch e il `Delta` si
    verifica per prima, quindi un `Delta(())` accanto a una patch che rimuove qualcosa
    farebbe fallire il test sul controllo sbagliato — e il test resterebbe verde
    misurando un'altra cosa.
    """
    return Delta(derivazioni)


def test_un_preservato_non_piazzato_e_un_difetto_dichiarato():
    prima = _prima()
    with pytest.raises(ValueError, match="in `preserve` ma non piazzata"):
        applica(prima, _patch(preserve=(C("assente"),)), _delta(),
                istante=ISTANTE, casualita=ENTROPIA)


def test_non_si_toglie_cio_che_non_c_era():
    prima = _prima()
    patch = _patch(remove=(C("assente"),))
    delta = _delta(StructuralDerivation(
        "rimozione_di_componente", (C("assente"),), ()))
    with pytest.raises(ValueError, match="in `remove` ma non piazzata"):
        applica(prima, patch, delta, istante=ISTANTE, casualita=ENTROPIA)


def test_un_entita_che_la_patch_non_nomina_non_si_tiene_ne_si_butta():
    """`preserve ∪ remove` e' `Entities(Cₖ)`: fuori da entrambe l'applicatore
    dovrebbe decidere da se', e nessuno gliel'ha chiesto."""
    prima = _prima()
    with pytest.raises(ValueError, match="che la patch non conserva ne' rimuove"):
        applica(prima, _patch(preserve=(N("b"),)), _delta(),
                istante=ISTANTE, casualita=ENTROPIA)


# --- AC3 · la relazione fra i due argomenti, e le due accuse che senza di lei escono

def test_una_create_che_il_delta_non_produce_e_una_coppia_disallineata():
    """Il difetto che questa guardia nomina per quello che e'.

    Senza di lei la stessa coppia arrivava al ramo che cerca gli ascendenti, e usciva
    come *«non c'e' una posizione da cui ricavare la sua»* — cioe' come un autolayout
    mancante. Due argomenti presi da due prodotti diversi non sono un autolayout
    mancante, e diagnosticarli cosi' manda a cercare il difetto dove non e'.
    """
    prima = LayoutIR.nuovo((Placement(N("b"), F(0), F(0)),),
                           istante=ISTANTE, casualita=ENTROPIA)
    patch = _patch(remove=(N("b"),), create=(C("nuova"),))
    delta = _delta(StructuralDerivation("eliminazione_di_nodo", (N("b"),), ()))
    with pytest.raises(ValueError, match="`create` e' .component:nuova."):
        applica(prima, patch, delta, istante=ISTANTE, casualita=ENTROPIA)


def test_un_remove_che_il_delta_non_consuma_e_una_coppia_disallineata():
    prima = _prima()
    with pytest.raises(ValueError, match="`remove` e' .component:R1."):
        applica(prima, _patch(remove=(C("R1"),)), _delta(),
                istante=ISTANTE, casualita=ENTROPIA)


def test_ogni_ascendente_di_una_creata_e_necessariamente_piazzato():
    """La catena che ha reso irraggiungibile il ramo dell'autolayout, misurata invece
    che dedotta: `create ⊆ produced`, ogni riscrittura ha `ingressi_minimi ≥ 1`,
    `consumed` e' l'unione degli ingressi, `consumed == remove` e `remove ⊆ piazzate`.

    Se un giorno una riscrittura ammettesse zero ingressi — `_verifica_forme` oggi lo
    vieta all'import — questo test diventerebbe rosso **prima** che `_baricentro`
    dividesse per zero, ed e' il punto in cui il ramo va riaperto.
    """
    from kirchhoff.domain.transform.primitives import FORME

    assert all(f.ingressi_minimi >= 1 for f in FORME.values())
    _, _, r, prima, _, _ = _passo()
    for nata in r.layout_patch.create:
        ascendenti = r.delta.derived_from(nata)
        assert ascendenti
        assert frozenset(ascendenti) <= prima.entita()


def test_le_mosse_comprendono_un_sopravvissuto_spostato():
    """La meta' del predicato di FR-38 che `applica` non sa produrre, provata sulla
    propria unita'.

    `applica` riusa gli oggetti `Placement` dei sopravvissuti, quindi da lui non esce
    mai un preservato spostato: se `mosse` vivesse dentro `applica`, questa meta' non
    girerebbe mai e il vincolo si ridurrebbe a «le nate sono nello scope». Qui il
    `dopo` si costruisce a mano, con `b` spostato di uno.
    """
    prima = _prima()
    spostato = tuple(
        Placement(p.entity, p.x + F(1), p.y) if p.entity == N("b") else p
        for p in prima.placements)
    dopo = LayoutIR.nuovo(spostato, istante=ISTANTE + 1, casualita=ENTROPIA)
    assert mosse(prima, dopo) == frozenset({N("b")})
    assert mosse(prima, prima) == frozenset()


def test_una_coordinata_che_cambia_fuori_dallo_scope_e_un_rerouting_non_dichiarato():
    """FR-38: *«il rerouting delle coordinate cambiate e' limitato allo
    `reroute_scope` dichiarato»*, sul risultato e non sul percorso di codice."""
    prima = LayoutIR.nuovo(
        (Placement(N("b"), F(0), F(0)), Placement(N("a"), F(10), F(0))),
        istante=ISTANTE, casualita=ENTROPIA)
    # Lo scope nomina `b`, che non si muove; la nata `nato` riceve una coordinata e
    # non e' dichiarata. E' esattamente il rerouting che FR-38 vieta di fare in
    # silenzio.
    patch = LayoutPatch(preserve=(N("b"),), remove=(N("a"),),
                        create=(N("nato"),), reroute_scope=(N("b"),))
    delta = _delta(StructuralDerivation("fusione_di_nodi", (N("a"),), (N("nato"),)))
    with pytest.raises(ValueError, match="non e' nello `reroute_scope` dichiarato"):
        applica(prima, patch, delta, istante=ISTANTE, casualita=ENTROPIA)


@pytest.mark.parametrize("sbagliato, atteso", [
    ((None, _patch(), Delta(())), "invece di LayoutIR"),
    ((_prima(), None, Delta(())), "invece di LayoutPatch"),
    ((_prima(), _patch(), None), "invece di Delta"),
])
def test_l_applicatore_rifiuta_ingressi_di_genere_sbagliato(sbagliato, atteso):
    with pytest.raises(TypeError, match=atteso):
        applica(*sbagliato, istante=ISTANTE, casualita=ENTROPIA)


# --- AC5 · il sottografo prima di qualunque testo del passo (UX-DR8) ---------

def _posizioni(radice: ET.Element) -> list[ET.Element]:
    """Gli elementi nell'ordine del documento, che in SVG e' l'ordine di pittura."""
    return list(radice.iter())


def test_il_sottografo_si_accende_prima_di_qualunque_testo_del_passo():
    """UX-DR8, nella lettura che le fonti sostengono e che non contraddice AD-23.

    `EXPERIENCE.md` mette il circuito sullo schermo al passo 2 — etichette comprese —
    e accende il sottografo al passo 3, *«non e' ancora comparso un solo carattere di
    testo»*. Il testo di cui parla e' quello del **passo**: `DESIGN.md` elenca «tre
    cose, in ordine di comparsa» — evidenziazione, equazione, certificato — e aggiunge
    che *«il resto del circuito non compare in questa lista, ed e' il punto»*.

    Preso invece alla lettera su ogni `<text>` del file, l'invariante obbligherebbe a
    emettere il layer 5 prima del 4, cioe' a comporre i layer fuori dalla scala che
    AD-23 dichiara chiusa. La lettura scelta e' quella che tiene in piedi entrambe le
    autorita', ed e' scritta nel modulo perche' sia contestabile.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    ordine = _posizioni(_albero(render(dopo_ir, dopo, overlay)))
    evidenziazioni = [i for i, e in enumerate(ordine)
                      if e.get("class") == "kf-sottografo"]
    testi_del_passo = [i for i, e in enumerate(ordine)
                       if e.get("class") == "kf-equazione-testo"]
    assert evidenziazioni and testi_del_passo
    assert max(evidenziazioni) < min(testi_del_passo)


def test_il_layer_dell_evidenziazione_non_emette_testo():
    """La condizione che rende vero il test sopra per costruzione e non per fortuna."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (cinque,) = [g for g in radice.findall(f"{SVG}g") if g.get("data-layer") == "5"]
    assert list(cinque.iter(f"{SVG}text")) == []
    assert list(cinque.iter(f"{SVG}rect"))


def test_i_layer_della_trasformazione_sono_il_5_e_il_6():
    """AD-23 fissa la scala `0…8`. Col passo in corso si popolano anche `5` e `6`; il
    `1` — la *regione* di trasformazione — resta non emesso, perche' `region-highlight`
    e' dichiarato variabile sperimentale e non default."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    assert [g.get("data-layer") for g in radice.findall(f"{SVG}g")] == [
        "2", "3", "4", "5", "6"]


def test_senza_overlay_i_layer_della_trasformazione_restano_non_emessi():
    """Uno stato visuale fermo non ha nulla da annotare, e un gruppo vuoto si
    riempirebbe per errore senza che nessuno decida di riempirlo."""
    radice = _albero(render(CIRCUITO, _prima()))
    assert [g.get("data-layer") for g in radice.findall(f"{SVG}g")] == ["2", "3", "4"]


# --- AC4 · l'equazione accanto al sottografo, non sotto il disegno (UX-DR10) --

def _riquadri(radice: ET.Element) -> dict[str, list[tuple[Punto, Punto]]]:
    riquadri: dict[str, list[tuple[Punto, Punto]]] = {}
    for e in radice.iter(f"{SVG}rect"):
        riquadri.setdefault(e.get("class"), []).append(_riquadro(e))
    return riquadri


def test_l_equazione_sta_accanto_al_sottografo_e_non_accanto_al_disegno():
    """UX-DR10, come quantita' e non come preferenza.

    *«Un'equazione staccata dal disegno e' una spiegazione; attaccata, e' una prova.»*
    La meta' che distingue «accanto al **sottografo**» da «accanto al disegno» e'
    l'altezza: il centro verticale del riquadro coincide con quello del sottografo. Se
    il sottografo e' in alto, l'equazione lo segue in alto — altrimenti sarebbe un
    pannello laterale, che `DESIGN.md` esclude con le stesse parole.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    riquadri = _riquadri(_albero(render(dopo_ir, dopo, overlay)))
    (equazione,) = riquadri["kf-equazione"]
    sottografo = riquadri["kf-sottografo"]
    alto = min(b.y for b, _ in sottografo)
    basso = max(a.y for _, a in sottografo)
    assert (equazione[0].y + equazione[1].y) / 2 == (alto + basso) / 2


def test_l_equazione_non_sta_sotto_il_disegno():
    """L'altra meta' della stessa frase, e quella che il difetto abituale viola: un
    riquadro appoggiato **sotto** il disegno e' la posizione che UX-DR10 nomina per
    escluderla."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    riquadri = _riquadri(_albero(render(dopo_ir, dopo, overlay)))
    (equazione,) = riquadri["kf-equazione"]
    _, fondo = _estensione_emessa(scena(dopo_ir, dopo))
    assert equazione[0].y < fondo.y


def test_l_equazione_e_fuori_dal_disegno_quindi_non_copre_nulla():
    """La clausola *Prevents* di AD-23 — *«un'annotazione di trasformazione non
    occlude mai un'entita' semantica preservata»* — qui e' soddisfatta **per
    costruzione**: il riquadro sta oltre il bordo destro di tutto cio' che il disegno
    emette, quindi non c'e' un riquadro di livello 4 con cui possa intersecarsi."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    riquadri = _riquadri(_albero(render(dopo_ir, dopo, overlay)))
    (equazione,) = riquadri["kf-equazione"]
    _, destra = _estensione_emessa(scena(dopo_ir, dopo))
    assert equazione[0].x > destra.x


def test_l_equazione_emessa_e_quella_del_prodotto():
    """`R_eq = R1 + R2`, simbolica: FR-13 e AD-4 vogliono segnaposto risolti a valle,
    mai cifre scelte da chi scrive il testo. Nel riquadro non compare `320`."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (testo,) = [e for e in radice.iter(f"{SVG}text")
                if e.get("class") == "kf-equazione-testo"]
    assert testo.text == "R1R2eq = R1 + R2"
    assert "320" not in testo.text


def test_il_riquadro_contiene_la_scritta_che_ci_sta_dentro():
    """Il riquadro e' un maggiorante della scritta, come `_riquadro_del_testo`: se
    fosse una misura, il font dell'export deciderebbe se l'equazione e' leggibile."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (riquadro,) = [_riquadro(e) for e in radice.iter(f"{SVG}rect")
                   if e.get("class") == "kf-equazione"]
    (testo,) = [e for e in radice.iter(f"{SVG}text")
                if e.get("class") == "kf-equazione-testo"]
    larga = _AVANZAMENTO_MONOSPAZIO * CORPO_EQUAZIONE * len(testo.text)
    assert F(testo.get("x")) >= riquadro[0].x + _IMBOTTITURA
    assert F(testo.get("x")) + larga <= riquadro[1].x
    assert F(testo.get("y")) - _SOPRA_LA_BASE * CORPO_EQUAZIONE >= riquadro[0].y
    assert F(testo.get("y")) + _SOTTO_LA_BASE * CORPO_EQUAZIONE <= riquadro[1].y


def test_la_linea_collega_il_riquadro_all_altezza_del_sottografo():
    """*«Collegata da una linea»* (`DESIGN.md`). Il collegamento e' orizzontale, sta
    **alla quota del sottografo** — che e' la meta' che dice «accanto al sottografo» e
    non «accanto al disegno» — e i suoi estremi sono il bordo destro di cio' che il
    disegno emette e il bordo sinistro del riquadro.

    Non parte dal bordo del sottografo, che era la lettura immediata: partendo da li'
    attraversava cio' che il disegno ha gia' scritto alla sua destra. Il test che lo
    tiene chiuso e' `test_nessuna_annotazione_del_passo_attraversa_il_disegno`.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (linea,) = [e for e in radice.iter(f"{SVG}line")
                if e.get("class") == "kf-collegamento"]
    riquadri = _riquadri(radice)
    (equazione,) = riquadri["kf-equazione"]
    sottografo = riquadri["kf-sottografo"]
    assert F(linea.get("y1")) == F(linea.get("y2"))
    assert F(linea.get("y1")) == (min(b.y for b, _ in sottografo)
                                  + max(a.y for _, a in sottografo)) / 2
    _, alto = _estensione_emessa(scena(dopo_ir, dopo))
    assert F(linea.get("x1")) == max(alto.x, max(a.x for _, a in sottografo))
    assert F(linea.get("x2")) == equazione[0].x


def test_la_viewbox_contiene_il_riquadro_dell_equazione():
    """Un'equazione emessa fuori dalla `viewBox` e' un'equazione che non c'e'. E' il
    difetto che la Story 1.4 ha gia' pagato una volta, con «220 ohm» tagliato."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    x, y, larga, alta = (F(v) for v in radice.get("viewBox").split())
    (equazione,) = _riquadri(radice)["kf-equazione"]
    assert x <= equazione[0].x and equazione[1].x <= x + larga
    assert y <= equazione[0].y and equazione[1].y <= y + alta


# --- il confine, che e' preservato e riceve un segno piu' discreto -----------

def test_i_nodi_di_confine_ricevono_un_ancora_che_non_li_ridisegna():
    """`DESIGN.md`: *«Non si dipinge il nodo di blu: si appoggia un `boundary-anchor`
    sopra di esso. Togliendo l'overlay, `A` torna identico — perche' non era mai
    cambiato»*, ed e' *«il test che distingue le due implementazioni»*.

    Qui lo si esegue davvero: si rende con e senza overlay, e si confronta il layer 4,
    che e' dove i nodi e le loro etichette vivono. Deve essere **identico byte per
    byte** — nei bracci 0 e A, che sono quelli in cui AD-23 dichiara valido questo
    test permanente.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()

    def quattro(testo: str) -> str:
        gruppo = next(g for g in _albero(testo).findall(f"{SVG}g")
                      if g.get("data-layer") == "4")
        # Il `tail` e' lo spazio **fra** un fratello e il successivo, non contenuto
        # del layer: con l'overlay dopo il 4 c'e' il 5, senza c'e' `</svg>`. Lasciarlo
        # dentro farebbe fallire il confronto per una ragione che non e' quella che il
        # test misura — e passare per la stessa, il giorno in cui il 4 cambiasse
        # davvero e il tail compensasse.
        gruppo.tail = None
        return ET.tostring(gruppo, encoding="unicode")

    assert quattro(render(dopo_ir, dopo, overlay)) == quattro(render(dopo_ir, dopo))


def test_l_ancora_di_confine_non_tocca_l_etichetta_del_nodo():
    """Il difetto da cui AD-23 nasce: *«il primo mock dipingeva l'alone sopra le
    etichette di `A` e `B`»*, cioe' cancellava i due elementi preservati piu'
    importanti del passo. L'ancora si ferma a mezzo lato dalla giunzione; l'etichetta
    parte piu' in la'."""
    from kirchhoff.render.serialize.svg import _riquadro_del_testo, _scritte

    _, dopo_ir, _, _, dopo, overlay = _passo()
    ancore = _riquadri(_albero(render(dopo_ir, dopo, overlay)))["kf-confine"]
    etichette = [_riquadro_del_testo(s) for s in _scritte(scena(dopo_ir, dopo))]
    for a_basso, a_alto in ancore:
        for e_basso, e_alto in etichette:
            sovrapposti = (a_basso.x < e_alto.x and e_basso.x < a_alto.x
                           and a_basso.y < e_alto.y and e_basso.y < a_alto.y)
            assert not sovrapposti


def test_il_confine_e_dentro_i_preservati():
    """`∂Tₖ ⊆ Pₖ`. Il boundary e' dove il sottografo tocca cio' che **non** cambia:
    un'ancora su un'entita' consumata annuncerebbe un confine che sta sparendo."""
    _, _, r, _, _, overlay = _passo()
    assert frozenset(overlay.confine) <= r.preserve


# --- l'overlay: i ruoli arrivano dal prodotto, non si calcolano qui ----------

def test_l_overlay_annota_cio_che_cambia_e_nient_altro():
    """AD-26: i ruoli vengono dal `TransformResult`. `cambiato` e' cio' che il `Delta`
    consuma e produce, meno i preservati — che nel braccio A non ricevono segnale."""
    _, _, r, _, _, overlay = _passo()
    assert set(overlay.cambiato) == {C("R1"), C("R2"), N("a"), EQUIVALENTE}
    assert not set(overlay.cambiato) & r.preserve


def test_lo_stesso_overlay_annota_i_due_stati_visuali():
    """Un solo overlay, due disegni: su `Cₖ` si accendono le due che spariscono, su
    `Cₖ₊₁` quella che nasce. E' cio' che rende possibile *Prima ↔ Dopo* senza tenere
    due oggetti allineati a mano (E-62)."""
    circuito, dopo_ir, _, prima, dopo, overlay = _passo()
    accese = lambda ir, lay: len(
        [e for e in _albero(render(ir, lay, overlay)).iter(f"{SVG}rect")
         if e.get("class") == "kf-sottografo"])
    assert accese(circuito, prima) == 2       # R1 e R2; il nodo assorbito no
    assert accese(dopo_ir, dopo) == 1         # l'equivalente


def test_il_sottografo_marca_solo_i_componenti():
    """`subgraph-highlight`: *«Marca **SOLO i componenti** che cambiano»*, e la
    sequenza di `DESIGN.md` distribuisce i segnali per genere — i componenti che
    cambiano ricevono l'evidenziazione, i nodi di boundary l'ancora.

    Il nodo che una riduzione in serie **assorbe** non e' in nessuna delle due righe, e
    marcarlo col segnale dei componenti era una decisione presa nel renderer. Misurato
    prima di toglierla: il riquadro attorno al nodo `a` finiva a `x=208` e l'etichetta
    del nodo `a` comincia a `x=208`, col tratto 2 centrato sul bordo — l'evidenziazione
    dipingeva sopra il primo tratto del nome. Che il nodo consumato resti senza segnale
    e' registrato come lavoro rinviato: e' una riga che manca a `DESIGN.md`.
    """
    circuito, _, _, prima, _, overlay = _passo()
    assert N("a") in overlay.cambiato
    accesi = {e.id for e in overlay.cambiato if e.kind == "component"}
    riquadri = _riquadri(_albero(render(circuito, prima, overlay)))
    simboli = {s.componente: s.riquadro() for s in scena(circuito, prima).simboli}
    assert len(riquadri["kf-sottografo"]) == len(accesi & set(simboli))
    # e nessuno di essi e' centrato su una giunzione
    giunzioni = {(g.punto.x, g.punto.y) for g in scena(circuito, prima).giunzioni}
    for basso, alto in riquadri["kf-sottografo"]:
        assert ((basso.x + alto.x) / 2, (basso.y + alto.y) / 2) not in giunzioni


def test_l_overlay_porta_i_tre_ruoli_che_ad_26_enumera():
    """AD-26 em.: l'`ArmEncoding` e' *«una mappa da ruolo (preservato · cambiato ·
    confine) a stile»*, e *«i ruoli le arrivano dal `TransformResult`»*. Sono tre.

    `DESIGN.md` dice che nel braccio A un preservato riceve segnale **«nessuno»**, e
    resta vero senza togliergli il ruolo: e' un'affermazione sullo stile, che sta
    nell'`ArmEncoding` — vuota qui. Se il ruolo mancasse, i bracci B e C, che i
    preservati li stilano, non potrebbero nascere dallo stesso prodotto.
    """
    assert {c for c in TransformOverlay.__dataclass_fields__} == {
        "cambiato", "confine", "preservato", "equazione"}


def test_il_ruolo_preservato_e_una_copia_di_p_k_non_un_ricalcolo():
    """La differenza che AD-26 chiama velenosa: dedurre `Pₖ` dai due circuiti, o da
    «tutto cio' che l'overlay non nomina». Qui `preserve` si copia dal prodotto che
    l'ha gia' calcolato e certificato — la stessa copia che `confine` gia' era."""
    _, _, r, _, _, overlay = _passo()
    assert frozenset(overlay.preservato) == r.preserve


def test_un_entita_non_puo_essere_insieme_cambiata_e_preservata():
    with pytest.raises(ValueError, match="cambiata e come preservata"):
        TransformOverlay((C("R1"),), (), (C("R1"),), Equation("Req", "R1 + R2"))


def test_il_confine_dichiarato_fuori_dai_preservati_e_contestato():
    """`∂Tₖ ⊆ Pₖ`, sui due campi che lo portano."""
    with pytest.raises(ValueError, match="come confine ma non come preservata"):
        TransformOverlay((C("R1"),), (N("b"),), (), Equation("Req", "R1 + R2"))


def test_un_entita_non_puo_essere_insieme_il_delta_e_il_confine_del_delta():
    with pytest.raises(ValueError, match="cambiata e come confine"):
        TransformOverlay((N("b"),), (N("b"),), (N("b"),),
                         Equation("Req", "R1 + R2"))


def test_un_overlay_senza_nulla_di_cambiato_non_ha_un_sottografo_da_accendere():
    with pytest.raises(ValueError, match="senza alcuna entita' cambiata"):
        TransformOverlay((), (N("b"),), (N("b"),), Equation("Req", "R1 + R2"))


def test_l_overlay_nomina_entita_non_coordinate():
    with pytest.raises(TypeError, match="invece di EntityRef"):
        TransformOverlay(("R1",), (), (), Equation("Req", "R1 + R2"))


def test_l_overlay_non_ripete_un_entita():
    with pytest.raises(ValueError, match="entita' ripetuta"):
        TransformOverlay((C("R1"), C("R1")), (), (), Equation("Req", "R1 + R2"))


def test_l_equazione_dell_overlay_e_quella_del_prodotto_non_una_stringa():
    with pytest.raises(TypeError, match="invece di Equation"):
        TransformOverlay((C("R1"),), (), (), "Req = R1 + R2")


def test_i_ruoli_vengono_da_un_transform_result_e_da_nessun_altro_posto():
    with pytest.raises(TypeError, match="invece di TransformResult"):
        annota(object())


def test_il_renderer_rifiuta_un_overlay_che_non_e_un_overlay():
    with pytest.raises(TypeError, match="invece di TransformOverlay"):
        render(CIRCUITO, _prima(), "sottografo acceso")


def test_un_overlay_che_non_annota_nulla_di_questo_stato_visuale_si_ferma():
    """Il passo si aprirebbe con l'equazione — e *«nessun passo si apre con un
    paragrafo»*. Meglio non disegnarlo che disegnarlo violando la regola."""
    estraneo = TransformOverlay((C("altrove"),), (), (),
                                Equation("Req", "R1 + R2"))
    with pytest.raises(ValueError, match="senza alcuna sagoma da accendere"):
        render(CIRCUITO, _prima(), estraneo)


def test_un_layer_5_che_emettesse_testo_verrebbe_fermato():
    """La guardia si prova sulla propria unita': il produttore corrente non emette
    testo al layer 5, quindi senza questa chiamata diretta il ramo non girerebbe mai —
    e un controllo che non gira e' un controllo che non c'e'."""
    from kirchhoff.render.serialize.svg import _verifica_l_ordine_dell_overlay

    with pytest.raises(ValueError, match="emette 1 elemento/i di testo"):
        _verifica_l_ordine_dell_overlay(["<text>R_eq</text>"])


# --- determinismo, con l'overlay in mezzo (AD-35) ----------------------------

def test_due_rendering_del_passo_danno_gli_stessi_byte():
    """AD-35 non si indebolisce perche' e' comparso un overlay: se il determinismo
    valesse solo sul disegno fermo, ogni confronto fra un prima e un dopo tornerebbe
    intermittente — ed e' precisamente il caso in cui serve."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    assert render(dopo_ir, dopo, overlay) == render(dopo_ir, dopo, overlay)


def test_l_ordine_delle_entita_dell_overlay_non_cambia_un_byte():
    """Le collezioni dell'overlay si ordinano su una chiave dichiarata, come tutte le
    altre: due overlay semanticamente uguali emettono gli stessi byte."""
    _, dopo_ir, _, _, dopo, overlay = _passo()
    rovesciato = TransformOverlay(tuple(reversed(overlay.cambiato)),
                                  tuple(reversed(overlay.confine)),
                                  tuple(reversed(overlay.preservato)),
                                  overlay.equazione)
    assert render(dopo_ir, dopo, rovesciato) == render(dopo_ir, dopo, overlay)


def test_l_applicatore_e_deterministico_a_meno_dell_identita():
    """Stesso ingresso, stessi piazzamenti. Cambia solo il `lay_`, che dipende
    dall'istante iniettato — ed e' l'unica cosa che deve cambiare."""
    prima = _prima()
    _, r = transform(CIRCUITO, "serie", "R1", "R2")
    uno = applica(prima, r.layout_patch, r.delta, istante=ISTANTE + 1,
                  casualita=ENTROPIA)
    due = applica(prima, r.layout_patch, r.delta, istante=ISTANTE + 2,
                  casualita=ENTROPIA)
    assert uno.placements == due.placements
    assert uno.identifier != due.identifier


def test_ogni_elemento_dell_overlay_ha_una_classe_a_cui_agganciare_un_token():
    """AD-26: un braccio deve poter cambiare la codifica visiva **senza toccare il
    renderer**, e la classe e' quell'aggancio. Vale per l'overlay come per lo schema:
    e' proprio sull'overlay che i quattro bracci differiscono."""
    from kirchhoff.render.serialize.svg import _CLASSI

    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    for g in radice.findall(f"{SVG}g"):
        if g.get("data-layer") not in {"5", "6"}:
            continue
        elementi = [e for e in g.iter() if e is not g]
        assert elementi
        for e in elementi:
            assert e.get("class") in set(_CLASSI)


@pytest.mark.parametrize("confine", [C("V1"), N("altrove")], ids=[
    "un componente, che non e' una giunzione",
    "un nodo che questo disegno non ha",
])
def test_un_confine_che_il_disegno_non_ha_solleva_invece_di_sparire(confine):
    """La differenza fra i due layer, provata invece che dichiarata.

    Nel layer 5 un'entita' assente si salta — e' l'altro fotogramma. Nel layer 6 no:
    `∂Tₖ ⊆ Pₖ`, e un preservato e' piazzato in **entrambi** gli stati visuali. Un
    confine assente e' quindi un'incoerenza, e saltarlo emetterebbe un passo a cui
    manca un'ancora senza che nulla lo dica.
    """
    overlay = TransformOverlay((C("R1"),), (confine,), (confine,),
                               Equation("Req", "R1 + R2"))
    with pytest.raises(ValueError, match="che questo stato visuale non disegna"):
        render(CIRCUITO, _prima(), overlay)


# --- FR-53 · rimosso l'overlay, cio' che sta sotto e' identico ----------------
#
# FR-53, seconda *Consequence (testable)*: *«Rimuovendo l'overlay, il rendering delle
# entita' sottostanti e' identico **byte per byte** a quello senza trasformazione in
# corso. E' il test che distingue `style = blue` da `style = unchanged + overlay`, ed
# e' automatizzabile.»* AD-23 em. la qualifica per braccio — *«nei bracci 0 e A»* — e
# FR-46 la mette fra le **famiglie obbligatorie**, cioe' fra i test permanenti.
#
# ## La lettura presa, e quella che resta aperta
#
# «Il rendering delle entita' sottostanti» ammette due letture, e le due non coincidono
# su questo file:
#
# 1. **I corpi dei layer che disegnano le entita'** — `2` fili, `3` componenti, `4`
#    nodi ed etichette — sono gli stessi byte. E' la lettura presa qui, ed e' quella
#    che il requisito puo' distinguere: `style = blue` cambierebbe l'attributo di un
#    elemento *dentro* quei layer, e questa famiglia lo vedrebbe.
# 2. **Il rendering a schermo** e' lo stesso. Non lo e', e la misura sta in
#    `test_l_overlay_allarga_la_viewbox_e_questo_e_dichiarato`: l'equazione sta fuori
#    dal disegno, quindi la `viewBox` cresce, e l'`<svg>` non porta `width`/`height` —
#    scala col contenitore (UX-DR27). Quale delle due letture governi non e' deciso da
#    nessuna autorita', e deciderlo qui significherebbe chiudere per inerzia D4,
#    *«renderer stack web vs PDF»*, che e' aperta e blocca Gate A. Registrata.

_INIZIO = '<g data-layer="{}"'


def _corpo_del_layer(testo: str, livello: int) -> str:
    """Il layer come **byte emessi**, non come albero riserializzato.

    `ET.tostring` di un sottoalbero riparsato normalizza gli attributi e non e' il
    file: un confronto fatto li' resterebbe verde su una differenza di byte che il
    round-trip di FR-41 vedrebbe. FR-53 dice «byte per byte», e questi sono i byte.
    """
    inizio = testo.index(_INIZIO.format(livello))
    fine = testo.index("</g>", inizio)
    return testo[inizio:fine]


@pytest.mark.parametrize("livello", [2, 3, 4], ids=["fili", "componenti", "nodi"])
@pytest.mark.parametrize("fotogramma", ["prima", "dopo"])
def test_rimosso_l_overlay_il_layer_delle_entita_e_identico(livello, fotogramma):
    """La famiglia che FR-53 nomina e AD-23 rende permanente, su entrambi i fotogrammi
    e su tutti e tre i layer che disegnano entita'.

    Vale nel braccio A perche' l'`ArmEncoding` e' vuota. Nei bracci B e C **non si
    applica**, e AD-23 lo dice: `unchanged-marker` e `attenuation` cambiano il
    rendering dei preservati *per definizione del braccio*. Un test senza qualificatore
    ucciderebbe in CI due dei quattro deliverable.
    """
    circuito, dopo_ir, _, prima, dopo, overlay = _passo()
    ir, layout = (circuito, prima) if fotogramma == "prima" else (dopo_ir, dopo)
    con = _corpo_del_layer(render(ir, layout, overlay), livello)
    senza = _corpo_del_layer(render(ir, layout), livello)
    assert con == senza


def test_l_overlay_allarga_la_viewbox_e_questo_e_dichiarato():
    """La seconda lettura di FR-53, misurata invece che lasciata implicita.

    Non e' un difetto da riparare qui: l'equazione **deve** stare fuori dal disegno
    (UX-DR10), quindi l'estensione emessa cresce necessariamente. Cio' che non e'
    deciso e' se «il rendering delle entita' sottostanti e' identico» vincoli anche la
    scala a cui quelle entita' finiscono a schermo. Il test fissa la misura perche' chi
    decide D4 la trovi, non perche' il numero conti.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    def riquadro(testo): return [F(v) for v in _albero(testo).get("viewBox").split()]
    con = riquadro(render(dopo_ir, dopo, overlay))
    senza = riquadro(render(dopo_ir, dopo))
    assert con[:2] == senza[:2] and con[3] == senza[3]   # origine e altezza uguali
    assert con[2] > senza[2]                             # la larghezza no
    assert _albero(render(dopo_ir, dopo, overlay)).get("width") is None


def test_l_alternativa_testuale_non_cambia_con_l_overlay():
    """`<title>` e `<desc>` descrivono la topologia, e sono gli stessi byte fra i due
    fotogrammi di uno stesso circuito.

    Detto altrimenti: **chi legge con un lettore di schermo non sente la
    trasformazione**, sente due volte lo stesso circuito. Non e' un difetto di questa
    storia — l'alternativa testuale del passo non e' fra i suoi criteri — ma e' una
    misura che il rapporto deve portare invece di limitarsi a dire che l'alternativa
    non descrive la trasformazione. Registrata.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    def testi(t):
        r = _albero(t)
        return (r.find(f"{SVG}title").text, r.find(f"{SVG}desc").text)
    assert testi(render(dopo_ir, dopo, overlay)) == testi(render(dopo_ir, dopo))


# --- R-Visual-1 · il predicato geometrico di AD-23, calcolato ----------------
#
# AD-23 em.: *«nessun riquadro di livello ≥ 5 interseca il riquadro di un'entita' di
# livello 4 appartenente a `Pₖ`»*. `Pₖ` arriva dall'overlay — `preservato`, che e' una
# copia del prodotto — e senza quel ruolo il predicato non e' calcolabile in `render/`
# senza dedurre `Pₖ`, che AD-26 vieta.
#
# **Il predicato e' violato, oggi, da un'ancora che `DESIGN.md` prescrive**, e le due
# autorita' collidono: `boundary-anchor` e' *«un segno **sovrapposto**»* al nodo, e un
# segno sovrapposto interseca cio' su cui sta. La collisione e' registrata come lavoro
# rinviato e non si risolve nel codice. Questo test misura l'eccezione invece di
# lasciarla implicita: l'ancora del confine sta sopra la **propria** giunzione, e
# nient'altro di livello ≥ 5 tocca nulla di livello 4 che appartenga a `Pₖ`.


def _si_intersecano(uno, altro) -> bool:
    (a, b), (c, d) = uno, altro
    return a.x < d.x and c.x < b.x and a.y < d.y and c.y < b.y


def _livello_4_per_entita(disegno) -> dict[EntityRef, dict[str, list]]:
    """I riquadri che il layer 4 disegna, attribuiti all'entita' che li possiede e
    divisi in **segni** (la giunzione, la massa) ed **etichette**.

    La divisione non e' cosmetica: l'aneddoto da cui AD-23 nasce e' *«il primo mock
    dipingeva l'alone sopra le etichette di `A` e `B`»*, e un'annotazione che copre un
    nome e una che si posa su un pallino non sono lo stesso difetto.

    Si leggono dalle strutture e non dai byte per una ragione che e' essa stessa un
    rilievo registrato: gli elementi emessi ai layer 5 e 6 **non portano `data-*`**, e
    nemmeno le etichette del layer 4 ne portano uno che le leghi al proprio
    componente. Dal solo SVG un'etichetta non e' attribuibile, e il predicato di AD-23
    parla di entita'.
    """
    from kirchhoff.render.serialize.svg import (
        _RAGGIO_GIUNZIONE,
        _riquadro_del_testo,
        _riquadro_della_massa,
        _scritte_del_nodo,
        _scritte_del_simbolo,
    )

    per_entita: dict[EntityRef, dict[str, list]] = {}
    for g in disegno.giunzioni:
        segni = [(Punto(g.punto.x - _RAGGIO_GIUNZIONE, g.punto.y - _RAGGIO_GIUNZIONE),
                  Punto(g.punto.x + _RAGGIO_GIUNZIONE, g.punto.y + _RAGGIO_GIUNZIONE))]
        if g.riferimento:
            segni.append(_riquadro_della_massa(g))
        per_entita[N(g.nodo)] = {
            "segni": segni,
            "etichette": [_riquadro_del_testo(s) for s in _scritte_del_nodo(g)]}
    for s in disegno.simboli:
        per_entita[C(s.componente)] = {
            "segni": [],
            "etichette": [_riquadro_del_testo(x) for x in _scritte_del_simbolo(s)]}
    return per_entita


def _tutti_i_riquadri_di_livello_4(disegno) -> list[tuple[Punto, Punto]]:
    return [r for voce in _livello_4_per_entita(disegno).values()
            for genere in voce.values() for r in genere]


def _annotazioni_emesse(radice) -> list[tuple[str, tuple[Punto, Punto]]]:
    """Ogni elemento di livello ≥ 5, col proprio riquadro. La linea ha altezza nulla e
    il testo si maggiora come ogni altro testo di questo file."""
    from kirchhoff.render.serialize.svg import _AVANZAMENTO_MONOSPAZIO

    fuori: list[tuple[str, tuple[Punto, Punto]]] = []
    for classe, riquadri in _riquadri(radice).items():
        fuori += [(classe, r) for r in riquadri]
    for e in radice.iter(f"{SVG}line"):
        if e.get("class") == "kf-collegamento":
            fuori.append((e.get("class"),
                          (Punto(F(e.get("x1")), F(e.get("y1"))),
                           Punto(F(e.get("x2")), F(e.get("y2"))))))
    for e in radice.iter(f"{SVG}text"):
        if e.get("class") == "kf-equazione-testo":
            x, y = F(e.get("x")), F(e.get("y"))
            larga = _AVANZAMENTO_MONOSPAZIO * CORPO_EQUAZIONE * len(e.text)
            fuori.append((e.get("class"),
                          (Punto(x, y - _SOPRA_LA_BASE * CORPO_EQUAZIONE),
                           Punto(x + larga, y + _SOTTO_LA_BASE * CORPO_EQUAZIONE))))
    return [(c, r) for c, r in fuori if c.startswith("kf-")
            and c in {"kf-sottografo", "kf-confine", "kf-collegamento",
                      "kf-equazione", "kf-equazione-testo"}]


@pytest.mark.parametrize("fotogramma", ["prima", "dopo"])
def test_nessuna_annotazione_occlude_un_preservato_salvo_l_ancora_sul_proprio_nodo(
        fotogramma):
    """Il predicato di AD-23 em., calcolato sull'uscita e non dedotto.

    L'unica intersezione ammessa e' quella che `DESIGN.md` prescrive: `boundary-anchor`
    e' *«un segno sovrapposto»* al nodo di boundary, quindi il suo riquadro contiene
    per forza la giunzione su cui e' centrato. Ogni altra e' un difetto, e questa e' la
    forma in cui la collisione fra le due autorita' resta visibile invece di sparire.
    """
    circuito, dopo_ir, _, prima, dopo, overlay = _passo()
    ir, layout = (circuito, prima) if fotogramma == "prima" else (dopo_ir, dopo)
    radice = _albero(render(ir, layout, overlay))
    disegno = scena(ir, layout)
    quattro = _livello_4_per_entita(disegno)
    giunzioni = {N(g.nodo): g.punto for g in disegno.giunzioni}

    ammesse = 0
    for classe, riquadro in _annotazioni_emesse(radice):
        for entita in overlay.preservato:
            voce = quattro.get(entita, {"segni": [], "etichette": []})
            # **Nessuna eccezione sulle etichette.** E' li' che sta l'aneddoto, ed e'
            # la meta' del predicato che vale senza qualificatori.
            for etichetta in voce["etichette"]:
                assert not _si_intersecano(riquadro, etichetta), (classe, entita)
            for segno in voce["segni"]:
                if not _si_intersecano(riquadro, segno):
                    continue
                # L'unica intersezione ammessa: `boundary-anchor` e' *«un segno
                # sovrapposto»* al nodo, quindi sta per forza sopra la geometria del
                # nodo su cui e' centrato — il pallino della giunzione e, se e' il
                # riferimento, il simbolo di massa che gli sta sotto.
                centro = ((riquadro[0].x + riquadro[1].x) / 2,
                          (riquadro[0].y + riquadro[1].y) / 2)
                assert classe == "kf-confine", (classe, entita)
                assert entita in giunzioni, entita
                assert centro == (giunzioni[entita].x, giunzioni[entita].y)
                ammesse += 1
    # L'eccezione esiste davvero: se scendesse a zero, il test starebbe misurando
    # un'uscita in cui le ancore sono sparite invece di un predicato soddisfatto. Tre:
    # il pallino di `b`, il pallino di `0` e la massa di `0`, che e' il riferimento.
    assert ammesse == 3


@pytest.mark.parametrize("fotogramma", ["prima", "dopo"])
def test_nessuna_annotazione_del_passo_attraversa_il_disegno(fotogramma):
    """La meta' che si chiude **per costruzione**, e che vale per ogni entita' e non
    per i soli preservati: l'equazione, il suo testo e la linea di collegamento stanno
    oltre il bordo destro di tutto cio' che il disegno emette.

    Misurato prima della correzione, sul fotogramma *Dopo* — quello che
    `EXPERIENCE.md` chiama *«il climax»*: `kf-collegamento` andava da `x=163` a
    `x=267` alla quota `y=40`, e l'etichetta `R1R2eq` sta a `x=166` con linea di base
    `y=40`. La linea correva **sulla** linea di base dell'etichetta e la attraversava
    da parte a parte. Non era un caso: la quota della linea e' il centro verticale del
    sottografo, che per un sottografo di un solo simbolo verticale coincide con la
    quota della prima etichetta del simbolo.
    """
    circuito, dopo_ir, _, prima, dopo, overlay = _passo()
    ir, layout = (circuito, prima) if fotogramma == "prima" else (dopo_ir, dopo)
    radice = _albero(render(ir, layout, overlay))
    tutti = _tutti_i_riquadri_di_livello_4(scena(ir, layout))
    del_passo = {"kf-collegamento", "kf-equazione", "kf-equazione-testo"}
    trovati = 0
    for classe, riquadro in _annotazioni_emesse(radice):
        if classe not in del_passo:
            continue
        trovati += 1
        for sotto in tutti:
            assert not _si_intersecano(riquadro, sotto), (classe, riquadro, sotto)
    assert trovati == 3


# --- i token dell'equazione, copiati e non scelti -----------------------------

def test_il_bordo_dell_equazione_e_quello_del_token():
    """`equation-anchor`: `border: '1px solid {colors.rule-hairline}'`. **1**, non 1.4.

    1.4 e' lo spessore del `boundary-anchor`, che `DESIGN.md` dichiara *«deliberatamente
    piu' discreto del segnale sul delta»*: prenderlo in prestito qui avrebbe legato due
    quantita' che i token tengono separate, e lo avrebbe fatto senza dirlo.
    """
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (riquadro,) = [e for e in radice.iter(f"{SVG}rect")
                   if e.get("class") == "kf-equazione"]
    assert F(riquadro.get("stroke-width")) == _TRATTO_EQUAZIONE == 1


def test_il_riquadro_dell_equazione_si_misura_col_passo_di_un_monospazio():
    """`{typography.quantity}` e' JetBrains Mono, **monospazio**: l'avanzamento e' una
    costante della famiglia, non una quantita' che varia col glifo.

    `_LARGHEZZA_DEL_GLIFO` e' il maggiorante da quadratone per un sans proporzionale, e
    applicarlo qui gonfiava il riquadro del 67% — 280 unita' dove ne bastano 190,4 per
    16 caratteri a corpo 16 — e con lui la `viewBox`, che in un contenitore che scala
    rimpicciolisce ogni entita' preservata.
    """
    assert _AVANZAMENTO_MONOSPAZIO < _LARGHEZZA_DEL_GLIFO
    _, dopo_ir, _, _, dopo, overlay = _passo()
    radice = _albero(render(dopo_ir, dopo, overlay))
    (riquadro,) = _riquadri(radice)["kf-equazione"]
    testo = str(overlay.equazione)
    assert riquadro[1].x - riquadro[0].x == (
        _AVANZAMENTO_MONOSPAZIO * CORPO_EQUAZIONE * len(testo) + 2 * _IMBOTTITURA)


# --- «quelle due sono diventate questa», sul disegno e non sull'aritmetica ----

def test_l_equivalente_e_disegnato_dentro_l_ingombro_delle_due_che_sostituisce():
    """L'affermazione della storia, misurata sulla **geometria emessa**.

    `test_l_equivalente_nasce_dove_stavano_le_due_che_sostituisce` ricalcola il
    baricentro e lo confronta col baricentro: prova che l'aritmetica di `_baricentro` e'
    quella dichiarata, e non prova nulla su cosa lo studente vede. Qui si guarda il
    disegno: la sagoma dell'equivalente sul fotogramma *Dopo* sta dentro l'ingombro che
    `R1` e `R2` occupavano sul fotogramma *Prima*. E' cio' che rende dicibile *«quelle
    due sono diventate questa»* invece di *«mi hanno mostrato un circuito nuovo»*.
    """
    circuito, dopo_ir, _, prima, dopo, _ = _passo()
    sagome = {s.componente: s.riquadro() for s in scena(circuito, prima).simboli}
    ingombro = (Punto(min(sagome["R1"][0].x, sagome["R2"][0].x),
                      min(sagome["R1"][0].y, sagome["R2"][0].y)),
                Punto(max(sagome["R1"][1].x, sagome["R2"][1].x),
                      max(sagome["R1"][1].y, sagome["R2"][1].y)))
    (nata,) = [s.riquadro() for s in scena(dopo_ir, dopo).simboli
               if s.componente == EQUIVALENTE.id]
    assert ingombro[0].x <= nata[0].x and nata[1].x <= ingombro[1].x
    assert ingombro[0].y <= nata[0].y and nata[1].y <= ingombro[1].y
