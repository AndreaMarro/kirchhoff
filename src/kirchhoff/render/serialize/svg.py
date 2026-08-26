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
Dei tre parametri ce ne sono ora due, e il terzo manca per scelta dichiarata:

- il `TransformOverlay` e' arrivato con la Story 1.7 ed e' **opzionale**. Senza, si
  disegna uno stato visuale fermo — nessuna trasformazione in corso, nessun ruolo da
  cui derivare un'annotazione — e i layer `1`, `5` e `6` restano **non emessi**
  invece che emessi vuoti: un gruppo vuoto si riempirebbe per errore senza che
  nessuno decida di riempirlo. Con l'overlay si popolano `5` e `6`; il `1`, che e' la
  *regione* di trasformazione, resta non emesso perche' `region-highlight` porta in
  `DESIGN.md` la nota *«NON e' default: … variabile sperimentale»*.
- l'`ArmEncoding` **non e' qui**. AD-26 lo assegna a `experiment/`, che non esiste:
  e' *«una mappa da ruolo (preservato · cambiato · confine) a stile»*, e nel braccio
  A e' **vuota**. Lo *stile* e' la variabile che Gate A manipola. Inventarlo qui la
  chiuderebbe per inerzia, e AD-26 avverte che implementarlo dentro
  `render/serialize` e' proprio la collocazione velenosa — obbligherebbe il renderer
  a ricalcolarsi `Pₖ`, riaprendo l'autocertificazione che AD-22 chiude.

Il confine regge perche' l'overlay porta **ruoli**, non stile, e li porta gia' fatti:
questo modulo non ha una funzione che deduca chi e' preservato, chi e' cambiato o chi
e' confine. Disegna cio' che riceve.

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
from ...domain.transform import EntityRef
from ..layout import LayoutIR
from ..overlay import TransformOverlay
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
           "kf-etichetta",
           # I cinque dell'overlay (Story 1.7). Stessa regola: la classe e'
           # l'aggancio del token, il valore viaggia come attributo di presenza.
           "kf-sottografo", "kf-confine", "kf-collegamento", "kf-equazione",
           "kf-equazione-testo")

# --- i token dell'overlay, copiati da `DESIGN.md` e non scelti qui ------------
#
# `subgraph-highlight`: `strokeWidth: '2px'`, `halo: '0 0 0 5px'`. L'alone e' li' una
# box-shadow; qui diventa l'imbottitura del riquadro attorno alla sagoma, che e' la
# stessa quantita' espressa nella geometria che questo file possiede. `scope: 'local'`
# e' un obbligo sperimentale, non un'estetica: *«un fondo colorato esteso dietro il
# sottografo e' una versione morbida del braccio C e contaminerebbe il confronto
# A-C»*. Per questo il riquadro sta **stretto attorno alla sagoma** e non attorno alla
# regione, e per questo non ha `fill`.
_ALONE = Fraction(5)
_TRATTO_SOTTOGRAFO = Fraction(2)

#: `boundary-anchor`: `size: '9px'`, `strokeWidth: '1.4px'`, `fill: 'none'`, `layer: 6`.
#: Il `fill: none` non e' un dettaglio — e' cio' che rende vero *«togliendolo, il nodo
#: torna identico»*: un segno che non riempie non puo' cancellare cio' che sta sotto.
_LATO_CONFINE = Fraction(9)
_TRATTO_CONFINE = Fraction(7, 5)

#: `equation-anchor`: `padding: '{spacing.3}'` = 12, `radius: '{rounded.md}'` = 8,
#: `border: '1px solid {colors.rule-hairline}'`, `font: '{typography.quantity}'` =
#: JetBrains Mono 16/500. Lo stacco fra il disegno e il riquadro e' `{spacing.5}` = 24:
#: e' cio' che tiene l'equazione **fuori** dal disegno senza staccarla, ed e' quello
#: che la linea di collegamento attraversa.
CORPO_EQUAZIONE = Fraction(16)
FAMIGLIA_EQUAZIONE = "JetBrains Mono, ui-monospace, monospace"
PESO_EQUAZIONE = "500"
_IMBOTTITURA = Fraction(12)
_RAGGIO_EQUAZIONE = Fraction(8)
_STACCO_EQUAZIONE = Fraction(24)

#: Il bordo del riquadro dell'equazione: **1**, non 1.4. Il token dice `1px solid`, e
#: 1.4 e' lo spessore del `boundary-anchor`, che `DESIGN.md` dichiara *«deliberatamente
#: piu' discreto del segnale sul delta»*: prenderlo in prestito qui avrebbe legato due
#: quantita' che i token tengono separate.
_TRATTO_EQUAZIONE = Fraction(1)

#: Lo spessore della **linea di collegamento**. `equation-anchor` la chiede — *«con una
#: linea di collegamento»* — e non le da' un token: nessuna delle voci di `DESIGN.md`
#: ne fissa lo spessore. E' quindi una quantita' **dichiarata qui**, non copiata, ed e'
#: registrata come lavoro rinviato insieme a `TRATTO`, per la stessa ragione: il token
#: manca, non e' stato inventato. Vale quanto il bordo del riquadro che collega, che e'
#: l'unica relazione che i token permettono di affermare — appartengono alla stessa
#: voce.
_TRATTO_COLLEGAMENTO = _TRATTO_EQUAZIONE

#: L'avanzamento di un glifo del font dell'equazione, in multipli del corpo.
#: **Non e' `_LARGHEZZA_DEL_GLIFO`**, e la differenza non e' una raffinatezza: quello e'
#: un maggiorante per un sans **proporzionale**, dove l'avanzamento dipende dal glifo e
#: l'unico limite sicuro senza misurare il font e' il quadratone. `{typography.quantity}`
#: e' JetBrains Mono, **monospazio**: li' l'avanzamento e' una costante della famiglia —
#: 0,6 em per JetBrains Mono e per i fallback dichiarati nella pila — e un maggiorante
#: da quadratone gonfia il riquadro del 67% e con lui la `viewBox`, cioe' rimpicciolisce
#: il disegno in un contenitore che scala. Resta un maggiorante, con margine per un
#: fallback dall'avanzamento piu' largo: non si misura un font che l'export potrebbe non
#: avere, si limita superiormente una classe di font che si e' scelta.
_AVANZAMENTO_MONOSPAZIO = Fraction(13, 20)


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


# --- i layer 5 e 6: cio' che la trasformazione annota (Story 1.7) -------------
#
# ## UX-DR8, e la lettura che NON si e' presa
#
# *«Il sottografo evidenziato compare prima di qualunque testo.»* Presa alla lettera
# sui byte — l'evidenziazione prima di **ogni** `<text>` del file — la regola
# obbligherebbe a emettere il layer 5 prima del 4, cioe' a comporre i layer fuori
# dalla scala di AD-23, che vieta esattamente questo. Le due autorita' sembrano
# collidere; leggendo la fonte non collidono.
#
# `EXPERIENCE.md` numera la sequenza: al passo 2 *«`C₀` occupa quasi tutta la
# superficie utile»* — il circuito e' gia' sullo schermo, etichette comprese — e solo
# al passo 3 *«`R3` e `R4` si accendono … Non e' ancora comparso un solo carattere di
# testo»*. Il testo di cui si parla e' quello del **passo**, non quello del circuito:
# `DESIGN.md` elenca «tre cose, in ordine di comparsa» — evidenziazione, equazione,
# certificato — e aggiunge che *«il resto del circuito non compare in questa lista,
# ed e' il punto»*. **Di quelle tre questo file ne emette due**: il `certificate-chip`
# non ha una rappresentazione, `TransformOverlay` non porta il `Certificate` e nessun
# criterio di questa storia lo chiede. E' registrato come lavoro rinviato, perche'
# appoggiarsi a un elenco di tre e implementarne due senza dirlo e' il modo in cui una
# lacuna diventa invisibile.
#
# L'invariante emesso e' quindi: **ogni elemento del layer 5 precede ogni testo che
# l'overlay emette**, e il layer 5 non emette testo affatto. Vale per costruzione — 5
# prima di 6, tutto il testo dell'overlay nel 6 — e `_verifica_l_ordine_dell_overlay`
# lo controlla sulle righe prodotte invece di lasciarlo alla disciplina di chi le
# scrive.
#
# ## UX-DR10, che e' una posizione e non una preferenza
#
# *«Accanto al sottografo, non sotto il disegno.»* `DESIGN.md`: *«Un'equazione
# staccata dal disegno e' una spiegazione; attaccata, e' una prova.»* Due quantita'
# rendono la frase verificabile, e sono quelle che `_riquadro_dell_equazione` impone:
#
# 1. il riquadro sta **fuori dal disegno, di fianco** — a destra dell'estensione
#    emessa, oltre `_STACCO_EQUAZIONE`. Ne segue che non copre nulla: la clausola
#    *Prevents* di AD-23 e' soddisfatta per costruzione invece che per controllo;
# 2. il suo centro verticale **coincide** con quello del sottografo, non con quello
#    del disegno. E' questa la meta' che distingue «accanto al sottografo» da
#    «accanto al disegno»: se il sottografo e' in alto, l'equazione lo segue in alto.
#
# La linea di collegamento chiude il resto: `DESIGN.md` la chiede — *«collegata da
# una linea»* — e siccome i due centri verticali coincidono, e' un segmento
# **orizzontale, alla quota del sottografo**. Da dove parte non e' pero' il bordo del
# sottografo, che era la lettura immediata: e' `_attacco`, e il perche' sta li'.
#
# ## Cio' che qui NON si calcola
#
# **`Pₖ`.** AD-26: *«i ruoli gli arrivano da un `TransformResult`»* e `render/` *«non
# ricalcola mai `Pₖ`»*. Dedurre i preservati come «tutto cio' che l'overlay non
# nomina» sarebbe quella deduzione con un altro nome, e riaprirebbe
# l'autocertificazione che AD-22 chiude. Il renderer disegna i ruoli che riceve e non
# ne inferisce un terzo — che nel braccio A e' comunque quello che si annota **non
# annotandolo**.

def _riquadro_con_alone(basso: Punto, alto: Punto) -> tuple[Punto, Punto]:
    return (Punto(basso.x - _ALONE, basso.y - _ALONE),
            Punto(alto.x + _ALONE, alto.y + _ALONE))


def _sagome_del_sottografo(
    disegno: Scena, cambiato: Iterable[EntityRef]
) -> list[tuple[str, tuple[Punto, Punto]]]:
    """Le sagome delle entita' cambiate **che questo stato visuale piazza**.

    Un solo `TransformOverlay` annota due disegni: su `Cₖ` sono piazzate le entita'
    che spariscono, su `Cₖ₊₁` quelle che nascono. Le altre non stanno nel `LayoutIR`
    che si sta disegnando, quindi non hanno una sagoma qui — e saltarle non e' una
    tolleranza, e' cio' che rende lo stesso overlay valido su entrambi gli stati.

    **Solo i componenti.** `subgraph-highlight` porta la nota *«Marca SOLO i
    componenti che cambiano, stretto attorno alla loro sagoma»*, e la sequenza di
    `DESIGN.md` la ripete distribuendo i segnali per genere: *«I componenti che
    cambiano ricevono `subgraph-highlight` …; i nodi di boundary ricevono un
    `boundary-anchor` sovrapposto»*. Un nodo **consumato** — il nodo interno che una
    riduzione in serie assorbe — non e' in nessuna delle due righe: la tabella dei
    segnali ne ha tre, il delta, i preservati-e-boundary e i preservati, e nessuna e'
    la sua. Marcarlo col segnale dei componenti era una decisione presa qui, non un
    token copiato, e sulla fixture di questa storia dipingeva il bordo del riquadro
    esattamente sul primo tratto dell'etichetta del nodo — la geometria dell'aneddoto
    da cui AD-23 nasce. Che il nodo consumato resti senza segnale e' registrato come
    lavoro rinviato: e' una riga che manca a `DESIGN.md`, e chi la scrive e' chi lo
    possiede.
    """
    simboli = {s.componente: s for s in disegno.simboli}
    return [(e.id, _riquadro_con_alone(*simboli[e.id].riquadro()))
            for e in cambiato if e.kind == "component" and e.id in simboli]


def _unione(riquadri: list[tuple[Punto, Punto]]) -> tuple[Punto, Punto]:
    return (Punto(min(b.x for b, _ in riquadri), min(b.y for b, _ in riquadri)),
            Punto(max(a.x for _, a in riquadri), max(a.y for _, a in riquadri)))


def _attacco(sottografo: tuple[Punto, Punto],
             disegno: tuple[Punto, Punto]) -> Fraction:
    """L'ascissa da cui comincia il lato dell'equazione: il bordo destro di **tutto
    cio' che il disegno emette**, o del sottografo se il suo alone sporge oltre.

    E' qui che la linea di collegamento parte, e la scelta e' l'unica che rende vera
    per costruzione la meta' geometrica di R-Visual-1 che riguarda il collegamento.
    Partire dal bordo del sottografo, che e' la lettura immediata di *«collegata da
    una linea»*, mandava la linea **attraverso** cio' che il disegno ha gia' scritto
    alla sua destra: sulla fixture di questa storia passava sulla linea di base
    dell'etichetta del componente equivalente e la attraversava da parte a parte, sul
    fotogramma che `EXPERIENCE.md` chiama *«il climax»*. Non era un caso: la quota
    della linea e' il centro verticale del sottografo, e per un sottografo di un solo
    simbolo quella quota **e'** la quota a cui `_scritte_del_simbolo` mette la prima
    etichetta.

    Cio' che dice «accanto al **sottografo**» e non «accanto al disegno» resta
    l'**altezza**, non l'ascissa: e' la meta' che `_riquadro_dell_equazione` impone, e
    se il sottografo e' in alto l'equazione lo segue in alto.
    """
    return max(disegno[1].x, sottografo[1].x)


def _riquadro_dell_equazione(
    testo: str, sottografo: tuple[Punto, Punto], attacco: Fraction
) -> tuple[Punto, Punto]:
    """Dove sta il riquadro dell'equazione: di fianco al disegno, all'altezza del suo
    sottografo.

    La larghezza e' un **maggiorante**, per la stessa ragione di
    `_riquadro_del_testo`: la misura vera dipende dal font, e sbagliare per eccesso
    lascia bianco mentre sbagliare per difetto taglia una parola. Il maggiorante non e'
    pero' lo stesso — `_AVANZAMENTO_MONOSPAZIO` e non `_LARGHEZZA_DEL_GLIFO` — perche'
    il font di `equation-anchor` e' monospazio e il suo avanzamento e' una costante
    della famiglia, non una quantita' che varia col glifo.
    """
    larga = _AVANZAMENTO_MONOSPAZIO * CORPO_EQUAZIONE * len(testo) + 2 * _IMBOTTITURA
    alta = (_SOPRA_LA_BASE + _SOTTO_LA_BASE) * CORPO_EQUAZIONE + 2 * _IMBOTTITURA
    sinistra = attacco + _STACCO_EQUAZIONE
    centro = (sottografo[0].y + sottografo[1].y) / 2
    return (Punto(sinistra, centro - alta / 2),
            Punto(sinistra + larga, centro + alta / 2))


def _rettangolo(classe: str, riquadro: tuple[Punto, Punto], tratto: Fraction,
                raggio: Fraction | None = None) -> str:
    basso, alto = riquadro
    attributi = [("class", classe),
                 ("x", _numero(basso.x)), ("y", _numero(basso.y)),
                 ("width", _numero(alto.x - basso.x)),
                 ("height", _numero(alto.y - basso.y))]
    if raggio is not None:
        attributi.append(("rx", _numero(raggio)))
    return _tag("rect", (*attributi, ("fill", "none"), ("stroke", TINTA),
                         ("stroke-width", _numero(tratto))))


def _enfasi_sul_cambiato(
    sagome: list[tuple[str, tuple[Punto, Punto]]]
) -> list[str]:
    """Layer 5. `subgraph-highlight`, stretto attorno alla sagoma. **Nessun testo.**

    Riceve le sagome invece di ricalcolarle: la stessa collezione decide che cosa il
    layer 5 disegna **e** dove si ancorano l'equazione e il collegamento, e due
    derivazioni della stessa cosa dalla stessa scena non sono tenute uguali da nulla
    (E-62).
    """
    return [_rettangolo("kf-sottografo", riquadro, _TRATTO_SOTTOGRAFO)
            for _, riquadro in sagome]


def _annotazioni(disegno: Scena, overlay: TransformOverlay,
                 sottografo: tuple[Punto, Punto],
                 equazione: tuple[Punto, Punto],
                 attacco: Fraction) -> list[str]:
    """Layer 6. Le ancore di boundary, poi il collegamento, poi l'equazione.

    L'ancora e' un quadrato **vuoto** centrato sulla giunzione: *«non e' il nodo
    ridisegnato: e' un segno sovrapposto»*. Non tocca l'etichetta del nodo, che parte
    a `_SCOSTAMENTO` dalla giunzione mentre l'ancora si ferma a mezzo lato — e' cosi'
    che *«togliendo l'overlay, il nodo torna identico»* resta vero anche del suo nome.

    **Qui un'entita' assente solleva, mentre nel layer 5 si salta**, e la differenza
    non e' una svista. Nel layer 5 saltare e' il meccanismo: lo stesso overlay annota
    due stati visuali, e cio' che non e' piazzato qui e' piazzato nell'altro. Il
    confine no — `∂Tₖ ⊆ Pₖ`, e un preservato e' piazzato in **entrambi** gli stati,
    altrimenti `operandi_di_vcer` avrebbe gia' rotto la tripla. Un confine che manca
    dal disegno e' quindi un'incoerenza, non l'altro fotogramma, e saltarlo la
    nasconderebbe emettendo un passo a cui manca un'ancora senza dirlo.
    """
    giunzioni = {g.nodo: g for g in disegno.giunzioni}
    righe: list[str] = []
    for e in overlay.confine:
        if e.kind != "node" or e.id not in giunzioni:
            raise ValueError(
                f"il confine nomina {e}, che questo stato visuale non disegna come "
                "giunzione. `∂Tₖ ⊆ Pₖ` e un preservato e' piazzato in entrambi gli "
                "stati: un confine che manca dal disegno non e' l'altro fotogramma, "
                "e' un'incoerenza fra l'overlay e il `LayoutIR`. Un confine su un "
                "componente non ha ancora una geometria dichiarata — nel catalogo "
                "corrente `∂Tₖ` porta solo nodi.")
        p, mezzo = giunzioni[e.id].punto, _LATO_CONFINE / 2
        righe.append(_rettangolo(
            "kf-confine",
            (Punto(p.x - mezzo, p.y - mezzo), Punto(p.x + mezzo, p.y + mezzo)),
            _TRATTO_CONFINE))

    altezza = (sottografo[0].y + sottografo[1].y) / 2
    righe.append(_tag("line", (
        ("class", "kf-collegamento"),
        ("x1", _numero(attacco)), ("y1", _numero(altezza)),
        ("x2", _numero(equazione[0].x)), ("y2", _numero(altezza)),
        ("stroke", TINTA), ("stroke-width", _numero(_TRATTO_COLLEGAMENTO)))))
    # `fill="none"`, dove il token dice `background: '{colors.surface-raised}'`. Non e'
    # una contraddizione presa alla leggera ed e' registrata come lavoro rinviato: la
    # tinta dei token non e' emessa da questo file — `TINTA` spiega perche' — e un
    # riquadro pieno di `currentColor` coprirebbe cio' che ha dietro invece di
    # ambientarlo. Fra un fondo sbagliato e nessun fondo, nessun fondo e' quello che
    # non cancella niente; la classe resta l'aggancio per chi il fondo lo possiede.
    righe.append(_rettangolo("kf-equazione", equazione, _TRATTO_EQUAZIONE,
                             _RAGGIO_EQUAZIONE))
    # La base del testo, non il suo bordo alto: `y` in SVG e' la linea di base.
    base = (equazione[0].y + equazione[1].y) / 2 + _SOPRA_LA_BASE * CORPO_EQUAZIONE / 2
    righe.append(
        f"<text{_attributi((('class', 'kf-equazione-testo'),
                            ('x', _numero(equazione[0].x + _IMBOTTITURA)),
                            ('y', _numero(base)),
                            ('text-anchor', 'start'),
                            ('font-size', _numero(CORPO_EQUAZIONE)),
                            ('font-family', FAMIGLIA_EQUAZIONE),
                            ('font-weight', PESO_EQUAZIONE),
                            ('font-variant-numeric', 'tabular-nums'),
                            ('fill', TINTA)))}>"
        f"{escape(str(overlay.equazione))}</text>")
    return righe


def _verifica_l_ordine_dell_overlay(enfasi: list[str]) -> None:
    """UX-DR8 sulle righe emesse, non sulla disciplina di chi le ha scritte.

    Due condizioni, e la prima e' quella che regge: il layer 5 esiste, e non emette
    testo. Se il sottografo non producesse alcuna sagoma, l'equazione del layer 6
    comparirebbe senza che nulla si sia acceso prima — cioe' il passo si aprirebbe con
    del testo, che e' esattamente cio' che *«nessun passo si apre con un paragrafo»*
    vieta.

    Gira **prima** che il resto dell'overlay sia costruito, e non alla fine: il
    riquadro dell'equazione si posiziona a partire dal riquadro del sottografo, quindi
    un sottografo vuoto lo farebbe ripiegare su una posizione di ripiego — cioe'
    produrrebbe silenziosamente un disegno che viola la regola, invece di dire che non
    puo' disegnarlo.
    """
    if not enfasi:
        raise ValueError(
            "overlay senza alcuna sagoma da accendere su questo stato visuale: "
            "nessuna delle entita' cambiate e' piazzata nel `LayoutIR` che si sta "
            "disegnando. Il passo si aprirebbe con l'equazione, e UX-DR8 chiede che "
            "il sottografo evidenziato compaia prima di qualunque testo.")
    fuori = [r for r in enfasi if "<text" in r]
    if fuori:
        raise ValueError(
            f"il layer 5 emette {len(fuori)} elemento/i di testo. UX-DR8 vuole "
            "l'evidenziazione prima di qualunque testo del passo, e il layer 5 e' "
            "cio' che deve venire prima: un testo qui sarebbe simultaneo a se stesso.")


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

def render(circuito: IR, layout: LayoutIR,
           overlay: TransformOverlay | None = None) -> str:
    """Lo stato visuale come SVG semantico. Pura: stessi ingressi, stessi byte.

    `overlay` e' il secondo parametro della firma di AD-35 — `render(LayoutIR,
    TransformOverlay, ArmEncoding) → SVG` — ed e' **opzionale** perche' i due casi
    sono due cose diverse, non uno la versione degradata dell'altro: senza overlay si
    disegna uno stato visuale fermo, che e' cio' che la Story 1.4 chiede e che non ha
    nessuna trasformazione in corso da annotare. In quel caso i layer 5 e 6 restano
    **non emessi**, non emessi vuoti — un gruppo vuoto si riempirebbe per errore
    senza che nessuno decida di riempirlo.

    Il terzo parametro, l'`ArmEncoding`, resta assente: AD-26 lo assegna a
    `experiment/`, nel braccio A e' vuoto, e lo stile e' la variabile che Gate A
    manipola. Le ragioni per esteso stanno nel docstring del modulo.

    Non c'e' un autolayout: le posizioni vengono dal `LayoutIR`, che per lo stato
    successivo e' quello che `render/layout.applica` ha costruito conservando i
    piazzamenti dei sopravvissuti.
    """
    disegno = scena(circuito, layout)
    basso, alto = _estensione_emessa(disegno)
    titolo, descrizione = alternativa_testuale(disegno)
    nome, descrizione_id = f"titolo-{disegno.layout}", f"descrizione-{disegno.layout}"

    annotato: list[str] = []
    if overlay is not None:
        if not isinstance(overlay, TransformOverlay):
            raise TypeError(
                f"{type(overlay).__name__} invece di TransformOverlay: i ruoli da "
                "annotare vengono dal prodotto della Trasformazione (AD-26).")
        sagome = _sagome_del_sottografo(disegno, overlay.cambiato)
        enfasi = _enfasi_sul_cambiato(sagome)
        _verifica_l_ordine_dell_overlay(enfasi)
        sottografo = _unione([r for _, r in sagome])
        attacco = _attacco(sottografo, (basso, alto))
        equazione = _riquadro_dell_equazione(
            str(overlay.equazione), sottografo, attacco)
        annotato = [
            *_layer(5, "sottografo", enfasi),
            *_layer(6, "annotazioni",
                    _annotazioni(disegno, overlay, sottografo, equazione,
                                 attacco)),
        ]
        basso, alto = _unione([(basso, alto), equazione, sottografo])

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
        *annotato,
        "</svg>",
    ]
    return "\n".join(righe) + "\n"
