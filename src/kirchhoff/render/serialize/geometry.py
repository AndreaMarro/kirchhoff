"""La geometria del disegno, prima che diventi byte.

AD-31 chiude il difetto piu' grave trovato dal gate del 15 agosto: *«un filo
attaccato al piedino sbagliato, con l'attributo giusto, prende il Badge
Verificata»*. La regola che ne segue e' una regola di **direzione**:

> «L'annotazione e' **derivata** dalla geometria dove possibile, mai il contrario:
> chi genera il disegno non scrive a mano l'attributo che lo certifica.»

Questo modulo e' il posto in cui quella direzione diventa una struttura invece di
una raccomandazione. La `Scena` porta i punti **e** le identita' che li nominano
nello stesso oggetto: `svg.py` non ha una seconda fonte da cui prendere un
`data-component-id`, perche' non ha nessun altro ingresso. Un attributo scritto a
mano non e' vietato dalla revisione: non e' costruibile.

Le guardie di `Scena` sono l'altra meta'. Nulla impedisce a un chiamante futuro —
l'applicatore di `LayoutPatch` della Story 1.7, per esempio — di comporre una scena
a mano; cio' che gli si impedisce e' di comporne una **incoerente**, in cui un filo
dichiara di toccare un terminale che sta altrove. E' la forma locale, a tempo di
emissione, di cio' che la Story 1.6 verifichera' riparsando.

## Perche' `Fraction`

Come in `layout/schema.py`: SM-20 e AD-35 chiedono «stessi byte», e VCER confronta
due posizioni. Un `0.1 + 0.2` dentro l'operando di quel confronto e' rumore binario
dentro un oracolo esatto. L'arrotondamento esiste, ma vive **solo** nella
formattazione decimale di `svg.py`, dove il formato SVG lo impone: fin qui tutto
resta esatto.

## Che cosa questo modulo NON decide

L'autolayout. Le posizioni arrivano dal `LayoutIR` e non si inventano: la Story 1.4
dichiara l'autolayout **non-goal**. Cio' che qui si deriva e' solo cio' che il
`LayoutIR` non puo' portare senza sapere che cosa sia un resistore — l'asse di un
bipolo, i suoi due morsetti, il percorso del filo fino al nodo.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ...domain.identity import verifica
from ...domain.ir import IR, REFERENCE_NODE, Component, ComponentType, Magnitude
from ...domain.transform import EntityRef
from ..layout import LayoutIR


@dataclass(frozen=True, slots=True)
class Forma:
    """L'ingombro di un simbolo, in unita' utente, misurato dal centro.

    `lungo` e' meta' del corpo lungo l'asse del bipolo, `largo` meta' della sua
    estensione trasversale. Il nome italiano non e' decorazione: e' la parola che
    l'alternativa testuale usa, ed e' scritta **qui** perche' un secondo elenco dei
    tipi disegnabili divergerebbe da questo nel posto dove nessuno guarda (E-62).
    """

    nome: str
    lungo: Fraction
    largo: Fraction


#: Distanza dal centro del simbolo al suo morsetto, lungo l'asse.
MEZZO_PASSO = Fraction(24)

#: I soli tipi che questa storia disegna. **L'ambito e' volutamente stretto**: una
#: fixture con soli resistori e un generatore. Un tipo assente qui non produce un
#: `Refusal` ma solleva, e la distinzione conta: un condensatore senza simbolo non
#: e' un circuito che non si puo' certificare, e' un disegno che non abbiamo ancora
#: scritto. Chiamarlo `Refusal` direbbe allo studente che il suo esercizio ha un
#: problema, quando il problema e' nostro — ed e' la falsa accusa che questo
#: prodotto esiste per non fare.
FORME: dict[ComponentType, Forma] = {
    "resistor": Forma("resistore", Fraction(12), Fraction(8)),
    "voltage_source_dc": Forma("generatore di tensione continua",
                               Fraction(12), Fraction(12)),
}


@dataclass(frozen=True, slots=True)
class Punto:
    """Un punto del disegno. Esatto: l'arrotondamento e' cosa della formattazione."""

    x: Fraction
    y: Fraction

    def __post_init__(self) -> None:
        for nome, valore in (("x", self.x), ("y", self.y)):
            if not isinstance(valore, Fraction):
                raise TypeError(
                    f"coordinata {nome} di tipo {type(valore).__name__}, serve una "
                    "Fraction: AD-35 chiede gli stessi byte, e un float li rende "
                    "dipendenti dall'ordine delle somme")


@dataclass(frozen=True, slots=True)
class Terminale:
    """Un morsetto: **dove** sta, e **che cosa** e'. I due nella stessa cosa.

    `indice` e' la posizione in `Component.terminals`, e non e' interscambiabile:
    `mna.py` prende la tensione come `v(terminals[0]) - v(terminals[1])`, quindi su
    un generatore l'indice **e'** la polarita'.
    """

    componente: str
    indice: int
    nodo: str
    punto: Punto


@dataclass(frozen=True, slots=True)
class Simbolo:
    """Un componente disegnato: il corpo, i due morsetti, cio' che vi si scrive.

    `componente` e `simbolico` sono due nomi diversi della stessa cosa e li porta
    entrambi perche' `Component` li porta entrambi: nel caso `dc-00001` dell'insieme
    di riferimento valgono `E1` ed `E_1`. Quale dei due lo studente debba **leggere**
    sul disegno non e' deciso da nessuna autorita', e questa storia non lo decide:
    disegna l'`id`, come faceva, e porta l'altro nell'annotazione perche' una
    serializzazione che lo perde rende la domanda indecidibile anche a chi la
    risolvera'.
    """

    componente: str
    simbolico: str
    tipo: ComponentType
    valore: Magnitude
    centro: Punto
    orizzontale: bool
    terminali: tuple[Terminale, Terminale]

    def __post_init__(self) -> None:
        if self.tipo not in FORME:
            raise ValueError(
                f"{self.componente}: nessun simbolo per un {self.tipo}. La Story 1.4 "
                f"disegna {', '.join(sorted(FORME))} e nient'altro; allargare "
                "l'insieme e' una modifica di `FORME`, non un caso da dedurre.")
        attesi = (0, 1)
        if tuple(t.indice for t in self.terminali) != attesi:
            raise ValueError(
                f"{self.componente}: morsetti con indici "
                f"{tuple(t.indice for t in self.terminali)} invece di {attesi}. "
                "L'indice e' la posizione in `Component.terminals`, e su un "
                "generatore e' la polarita': riordinarlo produce un circuito "
                "diverso che si dichiara uguale.")
        estranei = sorted({t.componente for t in self.terminali} - {self.componente})
        if estranei:
            raise ValueError(
                f"{self.componente}: morsetto di {', '.join(estranei)} montato su "
                "questo simbolo. L'annotazione si deriva da qui, quindi un morsetto "
                "altrui certificherebbe il componente sbagliato.")
        a, b = self.terminali
        if a.nodo == b.nodo:
            raise ValueError(
                f"{self.componente}: entrambi i morsetti sul nodo {a.nodo}. "
                "`Component` lo vieta gia' nel dominio — *«terminali coincidenti»* — e "
                "un simbolo che lo permettesse disegnerebbe un bipolo cortocircuitato "
                "che nessun circuito ha.")
        self._verifica_l_asse(a, b)

    def _verifica_l_asse(self, a: Terminale, b: Terminale) -> None:
        """I due morsetti stanno sull'asse dichiarato, simmetrici rispetto al centro.

        `orizzontale` non e' un'etichetta: `riquadro()` ci orienta il corpo e
        `svg._reoforo` ci attacca il tratto che esce dal bordo. Un simbolo che si
        dichiara orizzontale con i morsetti sopra e sotto disegna un corpo ortogonale
        ai propri reofori — accettato prima di questa guardia, e visibile solo a
        occhio. La simmetria e' la stessa che `_morsetti` produce; imporla qui
        significa che chi compone una scena a mano (Story 1.7) non puo' scriverne una
        che il resto del modulo assume e non verifica.
        """
        if self.orizzontale:
            lungo, trasverso = (a.punto.x, b.punto.x), (a.punto.y, b.punto.y)
            centro_lungo, centro_trasverso = self.centro.x, self.centro.y
            asse = "orizzontale"
        else:
            lungo, trasverso = (a.punto.y, b.punto.y), (a.punto.x, b.punto.x)
            centro_lungo, centro_trasverso = self.centro.y, self.centro.x
            asse = "verticale"
        if trasverso != (centro_trasverso, centro_trasverso):
            raise ValueError(
                f"{self.componente}: simbolo {asse} con i morsetti fuori dal proprio "
                "asse. Il corpo verrebbe disegnato ortogonale ai suoi reofori.")
        if lungo[0] == lungo[1] or lungo[0] + lungo[1] != 2 * centro_lungo:
            raise ValueError(
                f"{self.componente}: morsetti non simmetrici rispetto al centro "
                f"({self.centro.x}, {self.centro.y}). Il corpo e' centrato sul centro, "
                "quindi un morsetto piu' vicino dell'altro lascia un reoforo dentro il "
                "corpo e l'altro staccato.")

    @property
    def forma(self) -> Forma:
        return FORME[self.tipo]

    def riquadro(self) -> tuple[Punto, Punto]:
        """Gli angoli del corpo. Serve all'estensione della `viewBox`."""
        f = self.forma
        dx, dy = (f.lungo, f.largo) if self.orizzontale else (f.largo, f.lungo)
        return (Punto(self.centro.x - dx, self.centro.y - dy),
                Punto(self.centro.x + dx, self.centro.y + dy))


@dataclass(frozen=True, slots=True)
class Giunzione:
    """Un nodo disegnato: il punto in cui i fili che lo nominano si incontrano."""

    nodo: str
    punto: Punto
    riferimento: bool


@dataclass(frozen=True, slots=True)
class Filo:
    """Il collegamento fra un morsetto e il nodo che quel morsetto dichiara.

    `punti[0]` e' il morsetto, `punti[-1]` la giunzione. Non e' una convenzione di
    lettura: `Scena` la verifica, ed e' cio' che rende l'annotazione derivata.
    """

    componente: str
    indice: int
    nodo: str
    punti: tuple[Punto, ...]


@dataclass(frozen=True, slots=True)
class Scena:
    """Il disegno intero, coerente per costruzione o non costruito affatto.

    Le sei condizioni che «coerente» significa, ognuna con la sua guardia:

    1. nessun componente e nessun nodo disegnato due volte — `_senza_ripetizioni`;
    2. due entita' annotate non stanno nello stesso punto, **nodi e morsetti
       compresi** — `_punti_distinti`, seconda condizione di AD-31;
    3. ogni filo tocca il morsetto e il nodo che dichiara — `_verifica_i_fili`,
       prima condizione di AD-31;
    4. nessun filo passa per un punto annotato che non dichiara — `_senza_transiti`,
       terza condizione di AD-31;
    5. ogni morsetto porta esattamente un filo: ne' zero, ne' due;
    6. le tre collezioni sono nell'ordine della loro chiave — `_verifica_l_ordine`.

    L'ordine e' **verificato, non imposto**: la scena non riordina. Riordinare qui
    nasconderebbe un ordinamento dipendente da un dizionario invece di farlo vedere,
    e AD-35 chiede che il determinismo sia verificato, non rattoppato all'ultimo
    passaggio.
    """

    layout: str
    simboli: tuple[Simbolo, ...]
    giunzioni: tuple[Giunzione, ...]
    fili: tuple[Filo, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "layout", verifica(self.layout, "lay"))
        if not self.simboli:
            raise ValueError(
                f"{self.layout}: una scena senza simboli non e' un disegno, e K-0 "
                "dice che un passo senza disegno non e' un passo")
        _senza_ripetizioni([s.componente for s in self.simboli], "componente")
        _senza_ripetizioni([g.nodo for g in self.giunzioni], "nodo")
        _punti_distinti(self._punti_nominati())
        self._verifica_i_fili()
        self._verifica_l_ordine()

    def _punti_nominati(self) -> list[tuple[str, Punto]]:
        """Tutto cio' che porta un'identita' nei byte emessi, e dove sta.

        Nodi **e** morsetti in un solo elenco, non due: un nodo e un morsetto sono
        due entita' distinte con due annotazioni distinte — `data-node-id` e
        `data-terminal-*` — e se stanno nello stesso punto nessuna geometria puo'
        piu' dire quale delle due un filo tocchi. Confrontare i nodi solo fra loro e
        i morsetti solo fra loro lasciava passare esattamente quel caso: misurato,
        il nodo piazzato sul morsetto produce `points="76,0 76,0"` e una giunzione di
        raggio 3 sopra un morsetto di raggio 2.
        """
        return ([(f"nodo {g.nodo}", g.punto) for g in self.giunzioni]
                + [(f"morsetto {t.componente}.{t.indice}", t.punto)
                   for s in self.simboli for t in s.terminali])

    def _verifica_i_fili(self) -> None:
        """Le tre condizioni di AD-31, applicate a cio' che stiamo per emettere.

        AD-31 le enumera: *«ogni estremo di filo tocchi il terminale che
        l'annotazione dichiara, entro tolleranza dichiarata; che due terminali
        distinti non siano coincidenti; che nessun filo passi per un terminale che
        non dichiara di toccare»*. La prima e la terza sono qui, la seconda in
        `_punti_distinti`. Qui la tolleranza e' zero perche' l'annotazione e il punto
        hanno la stessa origine esatta; la tolleranza dichiarata serve al riparsing,
        che e' la Story 1.6.

        Un morsetto porta **esattamente** un filo: zero lo lascia in aria, due
        emettono due `<polyline>` con la stessa tripla `data-terminal-*` e la Story
        1.6 riparserebbe due incidenze dove ce n'e' una.
        """
        attesi = {(t.componente, t.indice) for s in self.simboli for t in s.terminali}
        nominati = self._punti_nominati()
        visti: list[tuple[str, int]] = []
        for f in self.fili:
            if len(f.punti) < 2:
                raise ValueError(
                    f"{f.componente}.{f.indice}: un filo con {len(f.punti)} punti "
                    "non congiunge nulla")
            terminale = self._terminale(f.componente, f.indice)
            if terminale.nodo != f.nodo:
                raise ValueError(
                    f"{f.componente}.{f.indice}: il filo dichiara il nodo {f.nodo}, "
                    f"il morsetto dichiara {terminale.nodo}. Due dichiarazioni della "
                    "stessa incidenza che divergono sono il difetto che AD-31 chiude.")
            if f.punti[0] != terminale.punto:
                raise ValueError(
                    f"{f.componente}.{f.indice}: il filo parte da "
                    f"({f.punti[0].x}, {f.punti[0].y}) e il morsetto che dichiara di "
                    f"toccare sta in ({terminale.punto.x}, {terminale.punto.y}). "
                    "Un filo attaccato al piedino sbagliato con l'attributo giusto "
                    "e' esattamente cio' che AD-31 vieta.")
            giunzione = self._giunzione(f.nodo)
            if f.punti[-1] != giunzione.punto:
                raise ValueError(
                    f"{f.componente}.{f.indice}: il filo arriva in "
                    f"({f.punti[-1].x}, {f.punti[-1].y}) e il nodo {f.nodo} sta in "
                    f"({giunzione.punto.x}, {giunzione.punto.y})")
            _senza_transiti(f, nominati)
            visti.append((f.componente, f.indice))
        doppi = sorted({f"{c}.{i}" for c, i in visti if visti.count((c, i)) > 1})
        if doppi:
            raise ValueError(
                f"morsetti con piu' di un filo: {', '.join(doppi)}. Due fili sullo "
                "stesso morsetto emettono due incidenze dove il circuito ne ha una.")
        scoperti = sorted(f"{c}.{i}" for c, i in attesi - set(visti))
        if scoperti:
            raise ValueError(
                f"morsetti disegnati e non collegati: {', '.join(scoperti)}. "
                "Un morsetto senza filo sta in aria nel disegno mentre "
                "l'annotazione lo dichiara attaccato a un nodo.")

    def _verifica_l_ordine(self) -> None:
        """Le tre collezioni sono nell'ordine della loro chiave dichiarata.

        AD-35: *«ogni collezione si ordina su una chiave dichiarata»*. Qui la scena
        **non riordina** — verifica. La differenza conta: riordinare all'ultimo
        passaggio nasconderebbe un ordinamento colato da un dizionario invece di
        farlo vedere, e AD-35 chiede che il determinismo sia verificato, non
        rattoppato. E' anche cio' che rende la chiave osservabile: un produttore che
        la perde viene fermato qui, invece di emettere byte diversi in silenzio.
        """
        for nome, ottenuto in (
                ("simboli", [s.componente for s in self.simboli]),
                ("giunzioni", [g.nodo for g in self.giunzioni]),
                ("fili", [(f.componente, f.indice) for f in self.fili])):
            if list(ottenuto) != sorted(ottenuto):
                raise ValueError(
                    f"{nome} fuori dall'ordine dichiarato: {ottenuto}. AD-35 chiede "
                    "una chiave d'ordine dichiarata per ogni collezione, e questa "
                    "sequenza non e' la sua.")

    def _terminale(self, componente: str, indice: int) -> Terminale:
        for s in self.simboli:
            if s.componente == componente:
                for t in s.terminali:
                    if t.indice == indice:
                        return t
                raise ValueError(f"{componente}: nessun morsetto di indice {indice}")
        raise ValueError(f"filo su {componente}, che non e' disegnato")

    def _giunzione(self, nodo: str) -> Giunzione:
        for g in self.giunzioni:
            if g.nodo == nodo:
                return g
        raise ValueError(f"filo verso il nodo {nodo}, che non e' disegnato")

    def estensione(self) -> tuple[Punto, Punto]:
        """Il riquadro che contiene la geometria: corpi, morsetti, fili, giunzioni.

        Le etichette **non** vi entrano, e non perche' si possano trascurare: la loro
        larghezza dipende dal font, e la tipografia sta in `svg.py`. E' `svg.py` a
        unire questo riquadro con quelli del testo che emette — un margine sperato
        non bastava, e la fixture di questa storia lo dimostrava tagliando «220 ohm».
        """
        punti = [p for f in self.fili for p in f.punti]
        punti += [g.punto for g in self.giunzioni]
        for s in self.simboli:
            punti += [t.punto for t in s.terminali]
            punti += list(s.riquadro())
        return (Punto(min(p.x for p in punti), min(p.y for p in punti)),
                Punto(max(p.x for p in punti), max(p.y for p in punti)))


def _senza_ripetizioni(nomi: list[str], genere: str) -> None:
    doppi = sorted({n for n in nomi if nomi.count(n) > 1})
    if doppi:
        raise ValueError(
            f"{genere} disegnato piu' di una volta: {', '.join(doppi)}. "
            "L'annotazione si deriva dalla geometria, e due geometrie per lo stesso "
            "nome rendono la derivazione ambigua.")


def _punti_distinti(coppie: list[tuple[str, Punto]]) -> None:
    """Due entita' distinte non stanno nello stesso punto.

    E' la seconda condizione di AD-31 — *«che due terminali distinti non siano
    coincidenti»* — applicata gia' in emissione: se due entita' annotate condividono
    un punto, nessun controllo geometrico puo' piu' dire quale delle due un filo
    tocchi.
    """
    for i, (nome, punto) in enumerate(coppie):
        for altro, suo in coppie[i + 1:]:
            if punto == suo:
                raise ValueError(
                    f"punti coincidenti: {nome} e {altro} stanno entrambi in "
                    f"({punto.x}, {punto.y}), e nessuna geometria puo' piu' "
                    "distinguerli")


def _sul_segmento(p: Punto, da: Punto, a: Punto) -> bool:
    """`p` sta sul segmento chiuso `da`–`a`. Esatto: nessun epsilon, nessun `float`.

    Prodotto vettoriale nullo piu' appartenenza al riquadro: su `Fraction` sono due
    confronti esatti, e la «geometria di segmenti» che AD-31 chiede non ha bisogno
    d'altro.
    """
    if (a.x - da.x) * (p.y - da.y) != (a.y - da.y) * (p.x - da.x):
        return False
    return (min(da.x, a.x) <= p.x <= max(da.x, a.x)
            and min(da.y, a.y) <= p.y <= max(da.y, a.y))


def _senza_transiti(filo: Filo, nominati: list[tuple[str, Punto]]) -> None:
    """Terza condizione di AD-31: *«nessun filo passi per un terminale che non
    dichiara di toccare»*.

    I due estremi dichiarati — il morsetto da cui il filo parte e la giunzione a cui
    arriva — sono gia' stati confrontati dal chiamante e sono leciti; qualunque altro
    punto annotato che cada su un tratto e' un transito. Un filo che attraversa il
    morsetto di un altro componente disegna un'incidenza che il grafo non ha, e la
    riparsatura della Story 1.6 non ha modo di sapere che non era voluta.

    Non copre l'attraversamento di un **corpo**: nessuna autorita' lo vieta oggi
    (AD-23 governa l'occlusione fra layer, e i layer che la producono — 5 e 6 — questa
    storia non li emette) ed evitarlo e' materia di autolayout, che la storia dichiara
    non-goal. Il caso concreto in cui un corpo viene attraversato perche' il centro
    del bipolo sta fuori dalla campata dei suoi nodi cade comunque qui: il filo passa
    prima per il morsetto opposto.
    """
    leciti = (filo.punti[0], filo.punti[-1])
    for nome, punto in nominati:
        if punto in leciti:
            continue
        for da, a in zip(filo.punti, filo.punti[1:]):
            if _sul_segmento(punto, da, a):
                raise ValueError(
                    f"{filo.componente}.{filo.indice}: il filo passa per {nome} in "
                    f"({punto.x}, {punto.y}), che non dichiara di toccare. AD-31 lo "
                    "vieta: il disegno mostra un'incidenza che il grafo non ha.")


def _punto_di(layout: LayoutIR, entita: EntityRef) -> Punto:
    try:
        p = layout.posizione(entita)
    except KeyError:
        raise ValueError(
            f"{layout.identifier}: {entita} non e' piazzata. Questa storia non ha un "
            "autolayout — il `LayoutIR` e' predefinito — quindi una posizione "
            "mancante non si inventa: si dichiara.") from None
    return Punto(p.x, p.y)


def _asse(a: Punto, b: Punto) -> tuple[bool, int]:
    """L'asse del bipolo e il verso del suo primo morsetto, dedotti dai due nodi.

    Il `LayoutIR` non porta un orientamento — AD-21 gli chiede **dove** ogni cosa
    sta, non come e' ruotata — e inventarne uno sarebbe autolayout. Qui si legge
    invece cio' che la geometria gia' dice: un bipolo si stende verso i nodi a cui
    e' attaccato, sull'asse su cui quei due nodi sono piu' lontani.
    """
    dx, dy = b.x - a.x, b.y - a.y
    if dx == 0 and dy == 0:
        raise ValueError(
            "i due nodi di un bipolo sono piazzati nello stesso punto: non esiste un "
            "asse su cui stenderlo, e i suoi due morsetti coinciderebbero")
    orizzontale = abs(dx) >= abs(dy)
    return orizzontale, -1 if (dx if orizzontale else dy) > 0 else 1


def _morsetti(c: Component, centro: Punto, a: Punto, b: Punto) -> tuple[
        bool, tuple[Terminale, Terminale]]:
    orizzontale, verso = _asse(a, b)
    def punto(segno: int) -> Punto:
        scarto = MEZZO_PASSO * segno
        return (Punto(centro.x + scarto, centro.y) if orizzontale
                else Punto(centro.x, centro.y + scarto))
    return orizzontale, (
        Terminale(c.id, 0, c.terminals[0], punto(verso)),
        Terminale(c.id, 1, c.terminals[1], punto(-verso)),
    )


def _percorso(orizzontale: bool, da: Punto, a: Punto) -> tuple[Punto, ...]:
    """Dal morsetto al nodo: dritto se allineati, a squadra altrimenti.

    Il primo tratto esce lungo l'asse del bipolo, come esce il reoforo; il secondo
    chiude. Non e' una scelta estetica lasciata al caso: e' una regola dichiarata,
    perche' AD-35 vieta che due esecuzioni scelgano percorsi diversi.
    """
    if da.x == a.x or da.y == a.y:
        return (da, a)
    gomito = Punto(a.x, da.y) if orizzontale else Punto(da.x, a.y)
    return (da, gomito, a)


def scena(circuito: IR, layout: LayoutIR) -> Scena:
    """Da `CircuitIR` piu' `LayoutIR` alla geometria annotata. Pura.

    ## L'ordine e' dichiarato qui, e verificato da `Scena`

    AD-35: *«nessun ordinamento che dipenda dall'ordine d'inserimento in una mappa —
    ogni collezione si ordina su una chiave dichiarata»*. Le chiavi ordinate qui sono
    **due** — l'identificatore del componente e il nome del nodo — e la terza, la
    coppia (componente, indice del morsetto) dei fili, **ne discende**: i fili
    nascono dentro il ciclo sui componenti gia' ordinati, due per componente
    nell'ordine dell'indice.

    C'era un terzo `sorted` sui fili, ed e' stato tolto perche' non era osservabile:
    applicato a una sequenza gia' ordinata per costruzione, toglierlo lasciava verdi
    tutti e 52 i test — misurato in copia-ombra. Un ordinamento che nessuna mutazione
    puo' far cadere non e' un oracolo: e' codice morto che sembra una garanzia. Il
    contratto d'ordine non e' pero' sparito: `Scena._verifica_l_ordine` lo **impone**
    su tutte e tre le collezioni, e li' cade se un produttore lo perde.

    Non c'e' nessun dizionario da cui l'ordine possa colare: le posizioni si cercano
    nel `LayoutIR` con una scansione, non con una mappa costruita per l'occasione.

    ## Perche' due ingressi e non uno

    AD-35 scrive `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` e non
    nomina il `CircuitIR`. Non e' implementabile alla lettera: il `LayoutIR` porta
    **dove** ogni cosa sta e nient'altro (AD-21), quindi da solo non sa che `R1` e'
    un resistore, quali nodi tocca, ne' che valore ha — e senza quello non esistono
    ne' `data-terminal-*` ne' l'alternativa testuale della topologia, che sono due
    criteri di accettazione di questa storia. I due ingressi restano due
    rappresentazioni distinte che si nominano per identificatore, come AD-21 chiede:
    nessuna delle due contiene l'altra.
    """
    componenti = sorted(circuito.components, key=lambda c: c.id)
    nomi_di_nodo = sorted(circuito.nodes)

    ignote = sorted(str(e) for e in layout.entita()
                    - {EntityRef("component", c.id) for c in componenti}
                    - {EntityRef("node", n) for n in nomi_di_nodo})
    if ignote:
        raise ValueError(
            f"{layout.identifier}: piazza {', '.join(ignote)}, che questo circuito "
            "non ha. Un layout di un altro stato visuale disegnerebbe un circuito "
            "che nessuno ha verificato.")

    giunzioni = tuple(
        Giunzione(n, _punto_di(layout, EntityRef("node", n)), n == REFERENCE_NODE)
        for n in nomi_di_nodo)

    simboli: list[Simbolo] = []
    fili: list[Filo] = []
    for c in componenti:
        centro = _punto_di(layout, EntityRef("component", c.id))
        capi = tuple(_punto_di(layout, EntityRef("node", n)) for n in c.terminals)
        orizzontale, terminali = _morsetti(c, centro, capi[0], capi[1])
        simboli.append(
            Simbolo(c.id, c.symbolic, c.type, c.value, centro, orizzontale, terminali))
        for t in terminali:
            arrivo = _punto_di(layout, EntityRef("node", t.nodo))
            fili.append(Filo(t.componente, t.indice, t.nodo,
                             _percorso(orizzontale, t.punto, arrivo)))

    return Scena(layout.identifier, tuple(simboli), giunzioni, tuple(fili))
