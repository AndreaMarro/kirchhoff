"""`render` — da uno stato visuale verificato ai suoi byte, sempre gli stessi.

AD-35: *«`render(...)` e' **pura**: stessi ingressi, stessi byte. Niente orologio,
niente identificatori generati a runtime, niente casualita' senza seme esplicito fra
gli ingressi, nessun ordinamento che dipenda dall'ordine d'inserimento in una mappa
— ogni collezione si ordina su una chiave dichiarata.»* Il fallimento e' **di CI**,
non un `Refusal`: il non determinismo non e' un caso che l'utente incontra.

AD-10 v2 aggiunge il perche' conti tanto: *«l'SVG semantico verificato e' la
sorgente unica di ogni altro formato»*. Cio' che esce di qui non e' un'illustrazione
della prova — e' l'oggetto da cui PDF, CircuiTikZ e ogni altro export derivano, e
l'unico che il round-trip della Story 1.6 potra' riparsare.

## Dove sta il determinismo, riga per riga

- **Nessun dizionario decide un ordine.** `FORME` e `_CORPI` sono tavole di
  consultazione: si interrogano per chiave, non si scandiscono. L'ordine delle tre
  collezioni disegnate nasce in `geometry.scena()` da due `sorted` con chiave
  dichiarata — la terza chiave ne discende — ed e' **verificato** da
  `Scena._verifica_l_ordine` prima che un byte esca. Qui si conserva e basta.
- **Nessun identificatore nasce qui.** Gli unici `id` emessi — quelli di `<title>` e
  `<desc>`, che `aria-labelledby` deve poter citare — sono derivati dal `lay_` del
  `LayoutIR` ricevuto, quindi da un ingresso.
- **Nessun `float`.** Le coordinate restano `Fraction` fino a `_numero`, che
  arrotonda a `PRECISIONE` cifre con la regola del pari, su interi. Due esecuzioni
  non possono divergere sull'ultima cifra perche' non c'e' aritmetica binaria.
- **Nessun orologio, nessuna casualita'.** Delle librerie standard il modulo importa
  `collections.abc`, `fractions` e `xml.sax.saxutils`: nessuna delle tre puo' produrre
  un valore che dipenda da quando la si chiama. Il vincolo non e' «poche
  dipendenze» — e' `test_render_non_ha_orologio_ne_casualita_fra_le_dipendenze`, che
  legge gli import sull'albero sintattico e cade se `time`, `datetime`, `random`,
  `uuid`, `secrets` oppure `os` compaiono.

## Chi porta l'identita', e chi la nomina soltanto

La stessa tripla `data-terminal-*` compare su due elementi, ed e' voluto:

- l'**ancoraggio** del morsetto e' il `<circle>` dentro il gruppo del componente,
  layer 3: uno per morsetto, sei in tutto sulla fixture di questa storia;
- il `<polyline>` del layer 2 e' il **conduttore**, e la tripla dice quale morsetto
  quel conduttore tocca.

E' la formulazione di AD-31 — *«ogni conduttore disegnato ha gli estremi coincidenti
… con gli ancoraggi dei terminali che il suo `data-terminal-*` nomina»* — e i due ruoli
sono distinti dall'elemento, non dall'attributo. Chi riparsa in 1.6 conta gli
ancoraggi, non le occorrenze dell'attributo.

## Che cosa NON c'e', e perche'

AD-35 scrive la firma come `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG`.
`TransformOverlay` e `ArmEncoding` **non sono qui**, ed e' una scelta dichiarata,
non una dimenticanza:

- AD-26 assegna l'`ArmEncoding` a `experiment/`, che non esiste: e' *«una mappa da
  ruolo (preservato · cambiato · confine) a stile»*, e nel braccio A e' **vuota**.
  Lo *stile* e' la variabile che Gate A manipola. Inventarlo qui la chiuderebbe per
  inerzia, e AD-26 avverte che implementarlo dentro `render/serialize` e' proprio la
  collocazione velenosa — obbligherebbe il renderer a ricalcolarsi `Pₖ`, riaprendo
  l'autocertificazione che AD-22 chiude.
- Il `TransformOverlay` e' *«cosa la trasformazione annota»*, e i ruoli gli arrivano
  da un `TransformResult`. Questa storia disegna **uno stato visuale fermo**: non c'e'
  nessuna trasformazione in corso, quindi nessun ruolo da cui derivare l'annotazione.

Ne segue che dei nove layer di AD-23 questa storia ne popola tre — `2` fili, `3`
componenti, `4` nodi ed etichette semantiche. I layer `1`, `5` e `6`, che sono quelli
della trasformazione, restano **non emessi** invece che emessi vuoti: un gruppo vuoto
si riempirebbe per errore senza che nessuno decida di riempirlo.

## Accessibilita'

UX-DR25 e FR-15 chiedono che *ogni* disegno porti l'alternativa testuale della
**topologia** — «non "schema del circuito" ma la struttura». La radice porta
`role="img"`, che rende l'intero sottoalbero presentazionale per le tecnologie
assistive: e' esattamente il motivo per cui il `<desc>` deve dire **tutto** il
circuito, compresa la polarita' del generatore. Un'alternativa che dicesse solo
«schema del circuito» darebbe allo studente cieco un circuito diverso da quello che
il sistema ha verificato.

Tre dettagli che l'obiettivo dichiarato — **WCAG 2.2 AA su tutte e tre le superfici** —
rende obbligatori, e che la prima stesura sbagliava:

- `aria-labelledby` cita **solo** il `<title>`; la `<desc>` arriva da
  `aria-describedby`. Citarle entrambe nella prima le fondeva nel *nome* accessibile
  e non lasciava alcuna descrizione: l'alternativa della topologia c'era nei byte e
  non nel canale in cui uno studente la riceve.
- La radice dichiara la propria lingua. AD-10 fa di questo SVG la sorgente di ogni
  altro formato, quindi viaggia da solo: senza `lang`, il lettore di schermo pronuncia
  l'italiano con le regole di un'altra lingua.
- Il testo e' in italiano **con gli accenti**. Vedi `alternativa_testuale`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from fractions import Fraction
from xml.sax.saxutils import escape

from ...domain.ir import IR, SYMMETRIC, Magnitude
from ..layout import LayoutIR
from .geometry import FORME, Giunzione, Punto, Scena, Simbolo, Terminale, scena

#: La lingua del testo emesso. Una sola volta: `lang` e `xml:lang` devono coincidere,
#: e due letterali che devono coincidere prima o poi non coincidono.
LINGUA = "it"

#: Cifre decimali delle coordinate emesse. Dichiarata perche' e' una scelta, non un
#: default: sotto di essa due punti distinti potrebbero scrivere la stessa stringa.
PRECISIONE = 4

#: Spazio fra il riquadro di cio' che si emette — testo compreso — e il bordo della
#: `viewBox`. E' `{spacing.drawing-inset}` di `DESIGN.md`, non un numero scelto qui.
#: Era 30 e doveva «coprire le etichette»: non le copriva, e la fixture di questa
#: storia tagliava «220 ohm». Le etichette ora entrano nell'estensione, e il margine
#: torna a essere quello che il suo nome dice.
MARGINE = Fraction(12)

#: Corpo del testo in unita' utente — `{typography.label-drawing}.fontSize`. La
#: `viewBox` non fissa `width`, quindi il disegno scala col contenitore (UX-DR27); le
#: «11 px effettive» di FR-15 sono una proprieta' del viewport e si misurano **li'**,
#: non in questo file.
CORPO_TESTO = Fraction(11)

#: `{typography.label-drawing}`: famiglia e peso, copiati dal token e non scelti qui.
#: Erano `ui-sans-serif, sans-serif`, che non e' quel token e non e' nessun token.
FAMIGLIA_TESTO = "Inter, system-ui, sans-serif"
PESO_TESTO = "500"

#: La **tinta** dei token non e' emessa, e non e' una dimenticanza. `identity-tag`
#: vuole `{colors.ink-secondary}`, che in `DESIGN.md` ha due valori — `#A6ACB8` e
#: `#565C66` — perche' la modalita' chiara e' *«pari grado, non secondaria»*. Un file
#: che viaggia da solo non sa quale delle due palette e' attiva; `currentColor` lo
#: lascia decidere alla superficie, che e' l'unica a saperlo. La classe resta
#: l'aggancio per chi vuole fissarla.
TINTA = "currentColor"

#: Spessore del tratto dello schema, in unita' utente. **Nessun token di `DESIGN.md`
#: lo fissa**: i quattro che dichiarano uno spessore — `provenance-anchor`,
#: `subgraph-highlight`, `boundary-anchor`, `unchanged-marker` — sono overlay, non il
#: circuito. Dichiarato qui invece di essere lasciato al default del renderer, e
#: registrato come lavoro rinviato: il token manca, non e' stato inventato.
TRATTO = Fraction(3, 2)

#: Limite **superiore** dell'avanzamento di un glifo, in multipli del corpo. Non e'
#: una misura del font: e' un maggiorante, e serve a questo. Nessun glifo latino di
#: un sans proporzionale supera un quadratone; usarne uno piu' stretto significherebbe
#: misurare un font che l'export potrebbe non avere. Il prezzo e' bianco in piu' sui
#: bordi, e il bianco non taglia niente.
_LARGHEZZA_DEL_GLIFO = Fraction(1)
_SOPRA_LA_BASE = Fraction(4, 5)
_SOTTO_LA_BASE = Fraction(1, 4)

_SCOSTAMENTO = Fraction(8)
_INTERLINEA = Fraction(14)
_RAGGIO_MORSETTO = Fraction(2)
_RAGGIO_GIUNZIONE = Fraction(3)
_MEZZA_CROCE = Fraction(4)

#: La massa: tre trattini sotto la giunzione del nodo di riferimento, dal piu' largo
#: al piu' stretto. Mezze larghezze, e il passo fra un trattino e il successivo.
_MASSA_MEZZE_LARGHEZZE = (Fraction(7), Fraction(9, 2), Fraction(2))
_MASSA_PASSO = Fraction(4)

#: Le classi degli elementi disegnati. Sono **l'aggancio dei token**, e sono tutto
#: l'aggancio: AD-26 chiede che i quattro bracci usino gli stessi token di `DESIGN.md`
#: e che l'`ArmEncoding` sia un parametro costruito da `experiment/`, non qualcosa che
#: il renderer deduce. Un braccio scrive `.kf-etichetta { fill: … }` nel proprio foglio
#: e vince sugli attributi di presenza senza nessuna battaglia di specificita', perche'
#: in CSS **qualunque** regola d'autore batte un attributo di presenza.
#:
#: Il valore dei token viaggia come attributo di presenza e non dentro un `<style>`.
#: Non e' una preferenza: un blocco `<style>` con `var()` e' stato scritto, provato su
#: un secondo renderer (`cairosvg`) e ritirato. Quel renderer applica la regola di
#: classe e non conosce `var()`, quindi prende `stroke: var(--kf-ink-primary,
#: currentColor)` come tinta non valida e **non disegna alcun tratto**: il circuito
#: usciva senza fili, senza corpi e senza massa, coi soli pallini e le etichette.
#: AD-10 fa di questo SVG la sorgente di ogni altro formato e D4 — quale stack lo
#: renda — e' una decisione **aperta**: non si puo' presupporre un motore CSS moderno
#: nel percorso di export. Il test che lo tiene chiuso e'
#: `test_il_disegno_non_dipende_da_un_motore_css_per_esistere`.
_CLASSI = ("kf-filo", "kf-corpo", "kf-massa", "kf-morsetto", "kf-giunzione",
           "kf-etichetta")


# --- numeri e attributi -------------------------------------------------------

def _numero(v: Fraction) -> str:
    """Un `Fraction` in decimale, arrotondato al pari su interi. Mai `-0`.

    `round()` su un `Fraction` e' esatto e arrotonda al pari: nessun passaggio da
    `float`, quindi nessuna cifra che dipenda dall'ordine delle somme.
    """
    scala = 10 ** PRECISIONE
    n = round(v * scala)
    segno = "-" if n < 0 else ""
    intera, frazionaria = divmod(abs(n), scala)
    if frazionaria == 0:
        return f"{segno}{intera}"
    return f"{segno}{intera}.{f'{frazionaria:0{PRECISIONE}d}'.rstrip('0')}"


def _attributi(coppie: Iterable[tuple[str, str]]) -> str:
    """Attributi nell'ordine in cui il chiamante li dichiara, sempre fra apici doppi."""
    return "".join(f' {nome}="{escape(valore, {chr(34): "&quot;"})}"'
                   for nome, valore in coppie)


def _tag(nome: str, coppie: Iterable[tuple[str, str]]) -> str:
    return f"<{nome}{_attributi(coppie)}/>"


def _punti(punti: Iterable[Punto]) -> str:
    return " ".join(f"{_numero(p.x)},{_numero(p.y)}" for p in punti)


#: Un testo emesso: dove sta, come e' ancorato, cosa dice. Una sola descrizione, letta
#: due volte — da `_testo`, che la serializza, e da `_riquadro_del_testo`, che la fa
#: entrare nella `viewBox`. Due descrizioni divergerebbero, ed e' esattamente cosi'
#: che l'etichetta di R2 finiva fuori dal disegno.
Scritta = tuple[Punto, str, str]


def _testo(scritta: Scritta) -> str:
    punto, ancora, contenuto = scritta
    return (f"<text{_attributi((('class', 'kf-etichetta'),
                                ('x', _numero(punto.x)), ('y', _numero(punto.y)),
                                ('text-anchor', ancora),
                                ('font-size', _numero(CORPO_TESTO)),
                                ('font-family', FAMIGLIA_TESTO),
                                ('font-weight', PESO_TESTO),
                                ('fill', TINTA)))}>"
            f"{escape(contenuto)}</text>")


def _riquadro_del_testo(scritta: Scritta) -> tuple[Punto, Punto]:
    """Il riquadro che una scritta occupa **al massimo**, dal suo punto d'ancoraggio.

    Maggiorante, non misura: `_LARGHEZZA_DEL_GLIFO` e' un limite superiore e `y` in
    SVG e' la **linea di base**, non il bordo alto — sopra c'e' l'ascendente, sotto il
    discendente. Sbagliare per eccesso lascia bianco; sbagliare per difetto taglia una
    parola, ed e' cio' che accadeva.
    """
    punto, ancora, contenuto = scritta
    larga = _LARGHEZZA_DEL_GLIFO * CORPO_TESTO * len(contenuto)
    sinistra = punto.x if ancora == "start" else punto.x - larga / 2
    return (Punto(sinistra, punto.y - _SOPRA_LA_BASE * CORPO_TESTO),
            Punto(sinistra + larga, punto.y + _SOTTO_LA_BASE * CORPO_TESTO))


# --- l'alternativa testuale della topologia (UX-DR25, FR-15) ------------------

def _valore(m: Magnitude) -> str:
    """Magnitudine piu' unita', esatta. La stessa stringa che l'etichetta disegna.

    Esatta e non arrotondata: `_numero` serve alle coordinate, dove il formato SVG
    impone un decimale. Un valore di componente resta la frazione che e' — `1/3 ohm`
    si legge cosi', non come `0.3333`.
    """
    return f"{m.amount} {m.unit}"


def _elenco(voci: list[str]) -> str:
    if len(voci) == 1:
        return voci[0]
    return f"{', '.join(voci[:-1])} e {voci[-1]}"


def _frase_del_componente(s: Simbolo) -> str:
    """Un componente, il suo valore, e i due nodi che tocca — con la polarita'.

    L'ordine dei terminali di un bipolo simmetrico non dice nulla e la frase non lo
    riporta; su un generatore **e' la polarita'**, e `canonical.py` avverte che
    riordinarlo *«produrrebbe un circuito diverso che si dichiara uguale — l'errore
    silenzioso che il prodotto esiste per prevenire»*. La convenzione e' quella di
    `mna.py`: la tensione e' `v(terminals[0]) - v(terminals[1])`, quindi a valore
    positivo il morsetto di indice 0 e' il positivo. `SYMMETRIC` si riusa da
    `domain/ir/canonical`: una seconda tavola della stessa simmetria divergerebbe da
    quella, e questa decide che cosa lo studente cieco sente.

    **Il numero e' quello del componente, col suo segno.** La prima stesura diceva
    «12 volt» di un generatore da −12 e spostava la polarita': vero in fisica, ma
    l'etichetta disegnata continuava a dire «-12 volt» e i due canali si
    contraddicevano sul numero. La regola di microcopy 5 di `EXPERIENCE.md` lo dice
    gia': *«Il testo cita il risultato, non lo riformula»* — prendere il valore
    assoluto e' una riformulazione.
    """
    a, b = s.terminali
    nome = s.forma.nome
    if s.tipo in SYMMETRIC:
        return (f"{s.componente}, {nome} da {_valore(s.valore)}, "
                f"fra il nodo {a.nodo} e il nodo {b.nodo}.")
    if s.valore.amount == 0:
        return (f"{s.componente}, {nome} da {_valore(s.valore)}, col primo morsetto "
                f"al nodo {a.nodo} e il secondo al nodo {b.nodo}.")
    positivo, negativo = _polarita(s)
    return (f"{s.componente}, {nome} da {_valore(s.valore)}, col morsetto "
            f"positivo al nodo {positivo.nodo} e il negativo al nodo {negativo.nodo}.")


def _polarita(s: Simbolo) -> tuple[Terminale, Terminale]:
    """Il morsetto positivo e il negativo, dedotti dal segno del valore.

    Una sola volta, letta da due canali: la frase che lo studente cieco sente e la
    croce che lo studente vedente vede. Erano due deduzioni separate, e a valore nullo
    dicevano cose diverse — il testo «col primo morsetto», che non promette polarita',
    e una croce disegnata sul morsetto 0, che la promette. Chiamare questa funzione
    con un valore nullo non ha senso, ed e' il chiamante a doverlo escludere.
    """
    a, b = s.terminali
    return (a, b) if s.valore.amount > 0 else (b, a)


def _frase_del_nodo(disegno: Scena, nodo: str) -> str:
    tocchi = sorted(t.componente for s in disegno.simboli for t in s.terminali
                    if t.nodo == nodo)
    if not tocchi:
        return f"Al nodo {nodo} non arriva nessun componente."
    if len(tocchi) == 1:
        return f"Al nodo {nodo} arriva solo {tocchi[0]}."
    return f"Al nodo {nodo} si incontrano {_elenco(tocchi)}."


def alternativa_testuale(disegno: Scena) -> tuple[str, str]:
    """Titolo breve e descrizione della **topologia**, derivati dalla scena.

    Derivati dalla scena e non dal `CircuitIR`: cosi' il testo e il disegno hanno
    una sola origine e non possono divergere. Se un giorno il disegno perdesse un
    componente, l'alternativa lo perderebbe con lui invece di continuare a
    descrivere un circuito che nessuno vede.

    **In italiano con gli accenti che l'italiano ha.** Questo e' testo che un lettore
    di schermo pronuncia: «e'» al posto di «è» e' un'altra parola, e le Consistency
    Conventions mandano il testo per l'utente alla microcopy di `EXPERIENCE.md`. La
    convenzione ASCII di questo repository vale per docstring e identificatori, non
    per cio' che lo studente sente.
    """
    riferimento = [g.nodo for g in disegno.giunzioni if g.riferimento]
    titolo = (f"Circuito: {len(disegno.simboli)} componenti, "
              f"{len(disegno.giunzioni)} nodi")
    righe = [f"{titolo}; il nodo di riferimento è {_elenco(riferimento)}."
             if riferimento else f"{titolo}; nessun nodo di riferimento."]
    righe += [_frase_del_componente(s) for s in disegno.simboli]
    righe += [_frase_del_nodo(disegno, g.nodo) for g in disegno.giunzioni]
    return titolo, " ".join(righe)


# --- i corpi dei simboli ------------------------------------------------------

def _lungo_l_asse(s: Simbolo, t: Terminale, distanza: Fraction) -> Punto:
    """Il punto a `distanza` dal centro di `s`, dalla parte del morsetto `t`.

    Il verso si legge dal morsetto, che la geometria ha gia' piazzato, invece di
    ricavarlo da un angolo che nessuno ha scritto: `Simbolo` garantisce che i due
    morsetti stiano sull'asse dichiarato e simmetrici, quindi il confronto di una sola
    coordinata basta. La distanza resta del chiamante — il bordo del corpo per il
    reoforo, meta' raggio per la croce — cosi' nessun disegno la deduce dal passo dei
    morsetti, che non e' suo.
    """
    if s.orizzontale:
        return Punto(s.centro.x + (distanza if t.punto.x > s.centro.x else -distanza),
                     s.centro.y)
    return Punto(s.centro.x,
                 s.centro.y + (distanza if t.punto.y > s.centro.y else -distanza))


def _segmento(da: Punto, a: Punto, classe: str = "kf-corpo") -> str:
    return _tag("line", (("class", classe),
                         ("x1", _numero(da.x)), ("y1", _numero(da.y)),
                         ("x2", _numero(a.x)), ("y2", _numero(a.y)),
                         ("stroke", TINTA)))


def _corpo_resistore(s: Simbolo) -> list[str]:
    """Rettangolo IEC, orientato sull'asse che la geometria ha gia' scelto."""
    basso, alto = s.riquadro()
    return [_tag("rect", (("class", "kf-corpo"),
                          ("x", _numero(basso.x)), ("y", _numero(basso.y)),
                          ("width", _numero(alto.x - basso.x)),
                          ("height", _numero(alto.y - basso.y)),
                          ("fill", "none"), ("stroke", TINTA)))]


def _corpo_generatore(s: Simbolo) -> list[str]:
    """Cerchio, piu' una croce dalla parte del morsetto positivo — **dentro** il cerchio.

    Il segno **non** e' scritto a mano accanto al simbolo: la sua posizione si ricava
    dal morsetto che la geometria ha gia' piazzato, e a valore negativo la croce sta
    dall'altra parte perche' il morsetto positivo e' l'altro.

    Due difetti misurati e chiusi qui. **La croce stava fuori dal cerchio**: a tre
    quarti della distanza dal centro al morsetto, cioe' a 18 unita' da un centro con
    raggio 12, finiva sul reoforo e si leggeva come una piastra, non come un piu'.
    Ora la frazione e' del **raggio**, quindi la croce non puo' uscire dal corpo
    qualunque sia il passo dei morsetti. **E a valore nullo la croce non si disegna**:
    l'alternativa testuale dice «col primo morsetto», che non promette polarita', e un
    piu' disegnato la prometteva — i due canali dicevano cose diverse dello stesso
    generatore.
    """
    corpo = [_tag("circle", (("class", "kf-corpo"),
                             ("cx", _numero(s.centro.x)), ("cy", _numero(s.centro.y)),
                             ("r", _numero(s.forma.lungo)),
                             ("fill", "none"), ("stroke", TINTA)))]
    if s.valore.amount == 0:
        return corpo
    positivo, _ = _polarita(s)
    croce = _lungo_l_asse(s, positivo, s.forma.lungo / 2)
    return corpo + [
        _segmento(Punto(croce.x - _MEZZA_CROCE, croce.y),
                  Punto(croce.x + _MEZZA_CROCE, croce.y)),
        _segmento(Punto(croce.x, croce.y - _MEZZA_CROCE),
                  Punto(croce.x, croce.y + _MEZZA_CROCE)),
    ]


_CORPI: dict[str, Callable[[Simbolo], list[str]]] = {
    "resistor": _corpo_resistore,
    "voltage_source_dc": _corpo_generatore,
}


def _verifica_corpi(forme: Iterable[str], corpi: Iterable[str]) -> None:
    """Un tipo con un ingombro e senza corpo si disegnerebbe come niente.

    Stessa figura di `delta._verifica_generi_delle_forme`: due dichiarazioni dello
    stesso insieme non si tengono allineate con la disciplina, si confrontano
    all'import (E-62).
    """
    mancanti = sorted(set(forme) - set(corpi))
    estranei = sorted(set(corpi) - set(forme))
    if mancanti or estranei:
        raise RuntimeError(
            f"tavole disallineate: senza corpo {mancanti}, senza ingombro {estranei}")


_verifica_corpi(FORME, _CORPI)


def _reoforo(s: Simbolo, t: Terminale) -> str:
    """Il tratto fra il bordo del corpo e il morsetto, dedotto dal morsetto stesso."""
    return _segmento(t.punto, _lungo_l_asse(s, t, s.forma.lungo), "kf-corpo")


def _massa(giunzione: Giunzione) -> list[str]:
    """I tre trattini della massa, sotto la giunzione del nodo di riferimento.

    Il nodo di riferimento entrava nel `<desc>` — *«il nodo di riferimento è 0»* — e in
    nessun elemento grafico: chi ascoltava e chi guardava ricevevano due topologie che
    differiscono per un'informazione. K-0 dice che il disegno fa parte della prova, non
    che la illustra, e un pezzo di prova che esiste in un canale solo e' meta' prova.

    Non porta `data-node-id`: la giunzione lo porta gia', e due elementi che dichiarano
    la stessa identita' sono l'ambiguita' che AD-31 esiste per chiudere. Che quel nodo
    sia il riferimento e' scritto **sulla giunzione**, in `data-node-reference`.
    """
    return [_segmento(Punto(giunzione.punto.x - mezza,
                            giunzione.punto.y + _SCOSTAMENTO + _MASSA_PASSO * i),
                      Punto(giunzione.punto.x + mezza,
                            giunzione.punto.y + _SCOSTAMENTO + _MASSA_PASSO * i),
                      "kf-massa")
            for i, mezza in enumerate(_MASSA_MEZZE_LARGHEZZE)]


def _riquadro_della_massa(giunzione: Giunzione) -> tuple[Punto, Punto]:
    profondita = _SCOSTAMENTO + _MASSA_PASSO * (len(_MASSA_MEZZE_LARGHEZZE) - 1)
    return (Punto(giunzione.punto.x - _MASSA_MEZZE_LARGHEZZE[0], giunzione.punto.y),
            Punto(giunzione.punto.x + _MASSA_MEZZE_LARGHEZZE[0],
                  giunzione.punto.y + profondita))


def _scritte_del_simbolo(s: Simbolo) -> list[Scritta]:
    """Nome e valore. Nessuna identita' sopra: la portano il gruppo e i morsetti.

    `role="img"` sulla radice rende presentazionale tutto il sottoalbero, quindi
    ripetere qui `data-component-id` non aiuterebbe nessun lettore e darebbe a chi
    riparsa due elementi diversi che dicono di essere lo stesso componente.
    """
    f = s.forma
    if s.orizzontale:
        primo = Punto(s.centro.x, s.centro.y - f.largo - _SCOSTAMENTO)
        secondo = Punto(s.centro.x, s.centro.y + f.largo + _INTERLINEA)
        ancora = "middle"
    else:
        primo = Punto(s.centro.x + f.largo + _SCOSTAMENTO, s.centro.y)
        secondo = Punto(primo.x, s.centro.y + _INTERLINEA)
        ancora = "start"
    return [(primo, ancora, s.componente), (secondo, ancora, _valore(s.valore))]


def _scritte_del_nodo(g: Giunzione) -> list[Scritta]:
    return [(Punto(g.punto.x + _SCOSTAMENTO, g.punto.y - _SCOSTAMENTO), "start", g.nodo)]


def _scritte(disegno: Scena) -> list[Scritta]:
    """Tutto il testo emesso, nell'ordine in cui il layer 4 lo emette."""
    return ([s for g in disegno.giunzioni for s in _scritte_del_nodo(g)]
            + [s for x in disegno.simboli for s in _scritte_del_simbolo(x)])


# --- i tre layer di AD-23 -----------------------------------------------------

def _layer(livello: int, nome: str, righe: list[str]) -> list[str]:
    """Un gruppo di AD-23. La classe e' prefissata come tutte le altre.

    `class="fili"` nuda collideva con qualunque `.fili` della pagina che inlinea
    questo SVG, e AD-10 lo fa finire dentro documenti che non sono nostri.
    """
    return [f'  <g data-layer="{livello}" class="kf-layer-{nome}">',
            *(f"    {r}" for r in righe),
            "  </g>"]


def _fili(disegno: Scena) -> list[str]:
    """Layer 2. Ogni filo dichiara il morsetto che tocca, e `Scena` lo ha verificato.

    Il filo porta `data-terminal-*` e **non e'** il morsetto: e' il conduttore che lo
    tocca. La distinzione e' quella che AD-31 scrive — *«ogni conduttore disegnato ha
    gli estremi coincidenti … con gli ancoraggi dei terminali che il suo
    `data-terminal-*` nomina»* — e la convenzione che ne segue e' dichiarata nel
    docstring del modulo: l'ancoraggio e' il `<circle>` dentro il gruppo del
    componente, uno per morsetto.
    """
    return [f"<polyline{_attributi((
                ('class', 'kf-filo'),
                ('data-terminal-component', f.componente),
                ('data-terminal-index', str(f.indice)),
                ('data-terminal-node', f.nodo),
                ('points', _punti(f.punti)),
                ('fill', 'none'), ('stroke', TINTA)))}/>"
            for f in disegno.fili]


def _componenti(disegno: Scena) -> list[str]:
    """Layer 3. Il gruppo e' il componente: e' il solo a portare `data-component-type`.

    `data-component-symbolic` c'e' perche' `Component.symbolic` esiste su ogni
    componente e non e' l'`id`: nel caso `dc-00001` dell'insieme di riferimento
    valgono `E1` ed `E_1`. Quale dei due nomi lo studente debba **vedere** non e'
    deciso da nessuna autorita' — resta rinviato — ma perderlo nella serializzazione
    lo renderebbe indecidibile anche dopo, e AD-10 fa di questo SVG la sorgente unica
    di ogni altro formato.
    """
    righe: list[str] = []
    for s in disegno.simboli:
        righe.append(f"<g{_attributi((
            ('data-component-id', s.componente),
            ('data-component-type', s.tipo),
            ('data-component-value', str(s.valore.amount)),
            ('data-component-unit', s.valore.unit),
            ('data-component-symbolic', s.simbolico)))}>")
        for t in s.terminali:
            righe.append(f"  {_reoforo(s, t)}")
        righe += [f"  {r}" for r in _CORPI[s.tipo](s)]
        for t in s.terminali:
            righe.append("  " + _tag("circle", (
                ("class", "kf-morsetto"),
                ("data-terminal-component", t.componente),
                ("data-terminal-index", str(t.indice)),
                ("data-terminal-node", t.nodo),
                ("cx", _numero(t.punto.x)), ("cy", _numero(t.punto.y)),
                ("r", _numero(_RAGGIO_MORSETTO)), ("fill", TINTA))))
        righe.append("</g>")
    return righe


def _nodi_ed_etichette(disegno: Scena) -> list[str]:
    """Layer 4 — *«nodi ed etichette semantiche»* (AD-23), in quest'ordine dichiarato.

    La giunzione e' il solo elemento che porta `data-node-id`: e' il punto in cui i
    fili che nominano quel nodo si incontrano, quindi e' li' che l'identita' e'
    derivata dalla geometria. Ogni nodo esce come giunzione, massa se e' il
    riferimento, ed etichetta — in quest'ordine; **poi** escono le etichette dei
    componenti. Un ordine dichiarato vale anche dentro un layer, e questo e' quello,
    non «tutte le etichette insieme in fondo» come diceva prima questa riga.
    """
    righe: list[str] = []
    for g in disegno.giunzioni:
        attributi = [("class", "kf-giunzione"), ("data-node-id", g.nodo)]
        if g.riferimento:
            attributi.append(("data-node-reference", "true"))
        righe.append(_tag("circle", (*attributi,
                                     ("cx", _numero(g.punto.x)),
                                     ("cy", _numero(g.punto.y)),
                                     ("r", _numero(_RAGGIO_GIUNZIONE)),
                                     ("fill", TINTA))))
        if g.riferimento:
            righe += _massa(g)
        righe += [_testo(t) for t in _scritte_del_nodo(g)]
    for s in disegno.simboli:
        righe += [_testo(t) for t in _scritte_del_simbolo(s)]
    return righe


def _estensione_emessa(disegno: Scena) -> tuple[Punto, Punto]:
    """L'estensione della geometria unita a quella di cio' che `svg.py` aggiunge.

    `Scena.estensione()` conosce corpi, morsetti, fili e giunzioni; il testo e la
    massa nascono qui, e finche' non entravano in questo conto la `viewBox` tagliava
    quello che sporgeva. Sulla fixture di questa storia tagliava «220 ohm», cioe' il
    valore di un componente sul caso base.
    """
    basso, alto = disegno.estensione()
    riquadri = [(basso, alto)]
    riquadri += [_riquadro_del_testo(s) for s in _scritte(disegno)]
    riquadri += [_riquadro_della_massa(g) for g in disegno.giunzioni if g.riferimento]
    return (Punto(min(b.x for b, _ in riquadri), min(b.y for b, _ in riquadri)),
            Punto(max(a.x for _, a in riquadri), max(a.y for _, a in riquadri)))


# --- render -------------------------------------------------------------------

def render(circuito: IR, layout: LayoutIR) -> str:
    """Lo stato visuale come SVG semantico. Pura: stessi ingressi, stessi byte.

    Non c'e' un `TransformOverlay` ne' un `ArmEncoding` fra i parametri, e non c'e'
    un autolayout dentro: le posizioni vengono dal `LayoutIR`, che questa storia
    riceve predefinito. Le ragioni stanno nel docstring del modulo.
    """
    disegno = scena(circuito, layout)
    basso, alto = _estensione_emessa(disegno)
    titolo, descrizione = alternativa_testuale(disegno)
    nome, descrizione_id = f"titolo-{disegno.layout}", f"descrizione-{disegno.layout}"

    righe = [
        f"<svg{_attributi((
            ('xmlns', 'http://www.w3.org/2000/svg'),
            ('viewBox', ' '.join((_numero(basso.x - MARGINE), _numero(basso.y - MARGINE),
                                  _numero(alto.x - basso.x + 2 * MARGINE),
                                  _numero(alto.y - basso.y + 2 * MARGINE)))),
            ('role', 'img'),
            ('lang', LINGUA), ('xml:lang', LINGUA),
            ('aria-labelledby', nome),
            ('aria-describedby', descrizione_id),
            ('stroke-width', _numero(TRATTO)),
            ('data-layout-id', disegno.layout)))}>",
        f'  <title id="{nome}">{escape(titolo)}</title>',
        f'  <desc id="{descrizione_id}">{escape(descrizione)}</desc>',
        *_layer(2, "fili", _fili(disegno)),
        *_layer(3, "componenti", _componenti(disegno)),
        *_layer(4, "nodi", _nodi_ed_etichette(disegno)),
        "</svg>",
    ]
    return "\n".join(righe) + "\n"
