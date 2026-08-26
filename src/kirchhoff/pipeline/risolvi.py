"""Da un circuito a una risposta risolta, verificata e disegnata.

**Perche' questo file mancava, e cosa costava.** Il prodotto aveva un solutore
esatto (`domain/mna.py`), un motore di trasformazione, un layout e un
serializzatore SVG — e nessun punto in cui i quattro si incontrano. La revisione
della Story 1.7 lo aveva misurato: *«`annota` ha zero chiamanti in `src/`; la
sequenza che K-0 chiede esiste solo dentro `_passo()` nel file di test»*. Un
prodotto le cui parti si compongono solo nei test non e' un prodotto: e' una
collezione di parti che passano.

**La sequenza, e perche' in quest'ordine.**

1. `solve_dc` risolve, in aritmetica esatta.
2. **Si verifica prima di disegnare.** `kcl_residuals` e `power_balance` sono
   controlli indipendenti dal metodo che ha prodotto la soluzione: la corrente
   entrante in ogni nodo deve annullarsi, e la potenza erogata deve pareggiare
   quella dissipata. Disegnare una soluzione non verificata significherebbe
   mostrare a uno studente un circuito «risolto» di cui nessuno ha controllato
   la risposta — cioe' K-1 al contrario: i modelli propongono, i sistemi
   certificano.
3. Solo dopo si disegna.

**Il rifiuto e' un esito valido** (K-3). Se la verifica non passa, questo modulo
non ritorna un disegno con un asterisco: ritorna un `Rifiuto` che dice quale
controllo ha fallito e di quanto. Un disegno che accompagna una risposta
sbagliata e' peggio di nessun disegno, perche' viene creduto.

**Il layout non e' calcolato.** L'autolayout e' un non-goal dichiarato: qui si
accetta un `LayoutIR` dato, oppure si usa la disposizione a maglia di
`layout_a_maglia`, che serve i circuiti a una maglia e RIFIUTA gli altri invece
di disporli male.
"""
from __future__ import annotations

import dataclasses
import hashlib
from fractions import Fraction

from kirchhoff.domain import mna
from kirchhoff.domain.ir import IR
from kirchhoff.domain.identity import conia
from kirchhoff.domain.transform import EntityRef
from kirchhoff.render.layout import LayoutIR, Placement
from kirchhoff.render.serialize import render

#: Passo della maglia, in unita' di disegno. Coincide con quello che la fixture
#: della Story 1.4 usa a mano: cambiarlo qui cambierebbe i byte di quel golden.
PASSO = Fraction(200)


@dataclasses.dataclass(frozen=True, slots=True)
class Rifiuto:
    """Un esito valido, non un errore.

    `controllo` dice QUALE verifica ha fallito, `misura` di quanto. Senza la
    seconda, un rifiuto e' un'accusa senza prova — e questo prodotto tratta la
    falsa accusa come il difetto peggiore.
    """
    controllo: str
    misura: str

    def __str__(self) -> str:
        return f"rifiutato da «{self.controllo}»: {self.misura}"


@dataclasses.dataclass(frozen=True, slots=True)
class Risolto:
    """Un circuito risolto, verificato e disegnato."""
    circuito: IR
    soluzione: dict
    layout: LayoutIR
    svg: str
    verifiche: tuple[str, ...]


def _giro(circuito: IR) -> list[str] | None:
    """L'ordine dei nodi lungo l'unica maglia, o None se maglia non e'.

    Cammina il grafo partendo dal nodo di riferimento: a ogni passo esiste un
    solo bipolo non ancora percorso, altrimenti non c'e' una maglia sola.
    """
    # I morsetti nominano nodi dichiarati: lo garantisce `IR.__post_init__`, e
    # riverificarlo qui sarebbe una guardia che non puo' fallire (E-65). Provato
    # a tenerla: nessun circuito costruibile la raggiunge.
    vicini: dict[str, list[tuple[str, str]]] = {n: [] for n in circuito.nodes}
    for c in circuito.components:
        a, b = c.terminals
        vicini[a].append((b, c.id))
        vicini[b].append((a, c.id))
    if any(len(v) != 2 for v in vicini.values()):
        return None  # ogni nodo di una maglia ha esattamente due bipoli
    # Il cammino parte dal nodo di riferimento, e NON si verifica qui che
    # esista: `IR.__post_init__` lo pretende gia' e rifiuta con «manca il nodo di
    # riferimento». Un controllo qui sarebbe vacuo — non potrebbe mai scattare —
    # e questo prodotto tratta le guardie che non possono fallire come un difetto
    # (E-65), non come prudenza. Provato aggiungendolo: il test che doveva vederlo
    # rosso falliva perche' l'IR protestava prima.

    giro, visti = [mna.REFERENCE_NODE], set()
    corrente = mna.REFERENCE_NODE
    while len(visti) < len(circuito.components):
        passi = [(n, cid) for n, cid in vicini[corrente] if cid not in visti]
        if not passi:
            return None
        prossimo, cid = passi[0]
        visti.add(cid)
        if prossimo != mna.REFERENCE_NODE:
            giro.append(prossimo)
        corrente = prossimo
    return giro if len(giro) == len(circuito.nodes) else None


def layout_a_maglia(circuito: IR) -> LayoutIR:
    """Dispone un circuito a UNA maglia, e rifiuta gli altri.

    Non e' autolayout e non finge di esserlo. I nodi vanno sul perimetro di un
    poligono regolare nell'ordine in cui la maglia li incontra, e ogni bipolo al
    punto medio dei suoi due nodi: cosi' nessun filo attraversa un nodo che non
    dichiara di toccare.

    **La prima versione li metteva in fila su una riga**, e il renderer l'ha
    fermata: *«R1.0: il filo passa per nodo a in (200, 0), che non dichiara di
    toccare. AD-31 lo vieta: il disegno mostra un'incidenza che il grafo non
    ha.»* La guardia ha detto la stessa cosa che questo docstring gia' diceva —
    un disegno disposto male mente sulla topologia — solo che l'ha detta
    eseguendo. E siccome l'SVG e' la sorgente unica (AD-10), un disegno che mente
    e' un prodotto che mente.

    Un circuito che non e' a una maglia viene RIFIUTATO, non disposto male.
    """
    giro = _giro(circuito)
    if giro is None:
        raise ValueError(
            f"{len(circuito.components)} bipoli su {len(circuito.nodes)} nodi non "
            "formano una maglia sola: questa disposizione farebbe passare fili "
            "attraverso nodi che non toccano, e il renderer la rifiuterebbe. "
            "L'autolayout generale e' un non-goal dichiarato: passa un LayoutIR "
            "costruito a mano.")

    # I nodi sul perimetro, nell'ordine del giro. Coordinate intere: `Placement`
    # vuole `Fraction`, e un poligono con seni e coseni darebbe irrazionali che
    # il formato quantizzerebbe — introducendo la divergenza fra geometria esatta
    # e byte emessi che la revisione della Story 1.4 ha gia' registrato.
    n = len(giro)
    if n == 2:
        posti = [(Fraction(0), Fraction(0)), (Fraction(0), PASSO)]
    elif n == 3:
        posti = [(PASSO / 2, PASSO), (Fraction(0), Fraction(0)), (PASSO, Fraction(0))]
    else:
        lato = (n + 3) // 4  # numero intero di lati, non una coordinata
        perimetro = ([(PASSO * i, Fraction(0)) for i in range(lato + 1)]
                     + [(PASSO * lato, PASSO * i) for i in range(1, lato + 1)]
                     + [(PASSO * (lato - i), PASSO * lato) for i in range(1, lato + 1)]
                     + [(Fraction(0), PASSO * (lato - i)) for i in range(1, lato)])
        posti = perimetro[:n]

    dove = {nodo: posti[i] for i, nodo in enumerate(giro)}
    piazzamenti = [Placement(EntityRef("node", nodo), *dove[nodo]) for nodo in sorted(giro)]
    # **Due bipoli fra gli STESSI due nodi non possono stare nello stesso punto.**
    # La prima versione metteva ogni componente al punto medio dei suoi nodi, e su
    # una maglia di due nodi — un generatore e un resistore in parallelo — i due
    # punti medi coincidevano. Il renderer l'ha fermata: «punti coincidenti:
    # morsetto R1.0 e morsetto V1.0 stanno entrambi in (0, 124), e nessuna
    # geometria puo' piu' distinguerli». Chi condivide entrambi i nodi con un
    # altro viene scostato di mezzo passo, in un verso stabile dato dall'ordine.
    per_coppia: dict[frozenset[str], list] = {}
    for c in sorted(circuito.components, key=lambda c: c.id):
        per_coppia.setdefault(frozenset(c.terminals), []).append(c)

    for coppia, gruppo in sorted(per_coppia.items(), key=lambda kv: sorted(kv[0])):
        for k, c in enumerate(gruppo):
            (x1, y1), (x2, y2) = dove[c.terminals[0]], dove[c.terminals[1]]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if len(gruppo) > 1:
                # **Lo scostamento e' sempre orizzontale, e non e' una svista.**
                # Due bipoli che condividono ENTRAMBI i nodi formano una maglia di
                # due nodi, e il ramo `n == 2` li impila in verticale: il segmento
                # fra i loro nodi ha quindi sempre la stessa x. Un ramo per il caso
                # orizzontale sarebbe codice che nessun circuito raggiunge.
                # Se un giorno la disposizione a due nodi cambia verso, va
                # cambiata anche questa riga — e il test dei gemelli, che verifica
                # proprio che si scostino lungo x, diventera' rosso e lo dira'.
                mx += PASSO * (k - Fraction(len(gruppo) - 1, 2))
            piazzamenti.append(Placement(EntityRef("component", c.id), mx, my))

    impronta = hashlib.blake2b(
        "|".join(f"{p.entity.kind}:{p.entity.id}@{p.x},{p.y}" for p in piazzamenti)
        .encode("utf-8"), digest_size=16).digest()
    return LayoutIR(
        identifier=conia("lay", int.from_bytes(impronta[:6], "big"), impronta[6:16]),
        placements=tuple(piazzamenti))


def risolvi(circuito: IR, layout: LayoutIR | None = None) -> Risolto | Rifiuto:
    """La sequenza intera: risolvi, VERIFICA, e solo allora disegna."""
    soluzione = mna.solve_dc(circuito)

    residui = mna.kcl_residuals(circuito, soluzione)
    non_nulli = {n: r for n, r in residui.items() if r}
    if non_nulli:
        peggiore = max(non_nulli.items(), key=lambda kv: abs(Fraction(str(kv[1]))))
        return Rifiuto("legge dei nodi",
                       f"al nodo {peggiore[0]} la corrente entrante non si annulla: "
                       f"{peggiore[1]}")

    bilancio = mna.power_balance(circuito, soluzione)
    if bilancio not in (0, None) and bilancio != Fraction(0):
        return Rifiuto("bilancio di potenza",
                       f"erogata e dissipata non pareggiano: scarto {bilancio}")

    disegno = layout if layout is not None else layout_a_maglia(circuito)
    return Risolto(circuito=circuito, soluzione=soluzione, layout=disegno,
                   svg=render(circuito, disegno),
                   verifiche=("legge dei nodi", "bilancio di potenza"))
