"""`TransformOverlay` — cosa la trasformazione annota. I ruoli, non lo stile.

AD-21 enumera quattro rappresentazioni disgiunte: `CircuitIR` (cosa il circuito e'),
`LayoutIR` (dove ogni cosa sta), **`TransformOverlay` (cosa la trasformazione
annota)**, `InteractionState` (cosa l'utente sta facendo). *«Nessuno dei quattro
contiene un riferimento a un altro se non per identificatore.»* Qui non ci sono ne'
coordinate ne' colori: ci sono **entita' e il ruolo che hanno nel passo**.

## Perche' i ruoli arrivano da un `TransformResult` e non si calcolano qui

AD-26, emendata il 15 agosto: l'`ArmEncoding` e' *«una mappa da ruolo (preservato ·
cambiato · confine) a stile»*, e i **ruoli** vengono dal `TransformResult`; il
renderer *«non ricalcola mai `Pₖ`»*. La versione velenosa e' scritta nello stesso
emendamento: implementare la codifica dentro `render/serialize` obbligherebbe il
renderer a ricalcolarsi `Pₖ`, *«riaprendo l'autocertificazione che AD-22 chiude»*.

Ne segue la forma di `annota`: legge il prodotto della Trasformazione e lo copia in
ruoli. Non guarda i due circuiti, non ha una funzione per proporre entita' di
propria iniziativa, e non ha modo di aggiungerne una che il `TransformResult` non
nomini.

## Cosa NON c'e', e perche' non e' una dimenticanza

**L'`ArmEncoding`.** AD-26 lo assegna a `experiment/`, che non esiste, e nel braccio
A e' **vuoto**. Lo *stile* — che tinta, che spessore, se attenuare — e' la variabile
che Gate A manipola: fissarlo qui la chiuderebbe per inerzia, e sarebbe una
decisione sperimentale presa da chi scrive il renderer. Questo modulo dichiara i
ruoli; chi li dipinge riceve i valori dei token, non li sceglie.

Ne segue anche cosa **non** viene annotato. Tre voci di `DESIGN.md` portano una
chiave `arm:` — `region-highlight` (*«variabile sperimentale»*), `attenuation`
(braccio C), `unchanged-marker` (braccio B) — e sono i due bracci contro cui A-0 va
confrontata. Nessuna delle tre ha un ruolo qui: un overlay che le nominasse
renderebbe il braccio A indistinguibile dai suoi controlli.

## Un solo overlay per due stati visuali

`cambiato` porta **sia** cio' che sparisce **sia** cio' che nasce, e non e' una
confusione. La sequenza di `EXPERIENCE.md` accende `R3` e `R4` su `Cₖ` (passo 3) e
mostra `R34` su `Cₖ₊₁` (passo 6): e' lo stesso passo, annotato su due disegni. Chi
renderizza evidenzia le entita' di `cambiato` che il `LayoutIR` che sta disegnando
piazza — le altre non le piazza, quindi non le disegna. Due overlay, uno per stato,
sarebbero la stessa cosa scritta due volte (E-62) su un oggetto che deve reggere il
confronto *Prima ↔ Dopo*.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.transform import EntityRef, Equation, TransformResult


def _ordinate(entita: tuple[EntityRef, ...], campo: str) -> tuple[EntityRef, ...]:
    """Ordine canonico e nessun duplicato — la stessa regola del `LayoutPatch`.

    AD-35 chiede una chiave d'ordine dichiarata per ogni collezione: due overlay
    semanticamente uguali devono emettere gli stessi byte, e un insieme che
    conservasse l'ordine d'inserimento non lo garantirebbe.
    """
    for e in entita:
        if not isinstance(e, EntityRef):
            raise TypeError(
                f"{campo}: {type(e).__name__} invece di EntityRef. Un "
                "`TransformOverlay` nomina entita' e ruoli, mai posizioni: una "
                "coordinata qui sarebbe il `LayoutIR` riscritto da chi lo annota "
                "(AD-21).")
    if len(set(entita)) != len(entita):
        raise ValueError(f"{campo}: entita' ripetuta")
    return tuple(sorted(entita))


@dataclass(frozen=True, slots=True)
class TransformOverlay:
    """I tre ruoli di AD-26, piu' l'equazione che il passo giustifica.

    | Ruolo | Segnale di `DESIGN.md` nel braccio A | Layer di AD-23 |
    |---|---|---|
    | `cambiato` | `subgraph-highlight`, stretto attorno alla sagoma | `5` enfasi sul cambiato |
    | `confine` | `boundary-anchor`, sovrapposto e piu' discreto | `6` annotazioni di boundary |
    | `preservato` | **nessuno** — la codifica del braccio A e' vuota | nessuno |
    | `equazione` | `equation-anchor`, accanto al sottografo | vedi sotto |

    **Il terzo ruolo di AD-26 — «preservato» — ha una voce, e la distinzione che lo
    rende innocuo e' fra ruolo e stile.** AD-26 em. enumera i ruoli come `preservato ·
    cambiato · confine` e dice che *«i ruoli le arrivano dal `TransformResult`»*: sono
    tre, non due, e `preserve` e' un membro del prodotto esattamente come `boundary`.
    Portarlo qui e' quindi una **copia**, la stessa che `confine` gia' e', e non il
    ricalcolo di `Pₖ` che lo stesso emendamento chiama velenoso — quello sarebbe
    dedurre i preservati dai due circuiti, o da «tutto cio' che l'overlay non nomina».

    `DESIGN.md` dice in una riga di tabella che `V1`, `R1` preservati ricevono segnale
    **«nessuno»**, e resta vero: e' un'affermazione sullo **stile**, che appartiene
    all'`ArmEncoding` — vuota nel braccio A, e quindi senza voce per quel ruolo. Il
    ruolo esiste e non e' dipinto; e' il modo in cui i bracci B e C possono nascere
    dallo stesso prodotto cambiando la sola codifica, che e' cio' che AD-26 vuole.

    Il ruolo serve inoltre a una cosa che senza di lui non e' calcolabile in `render/`:
    il **predicato di non-occlusione** di AD-23 em. — *«nessun riquadro di livello ≥ 5
    interseca il riquadro di un'entita' di livello 4 appartenente a `Pₖ`»* — nomina
    `Pₖ`, e un renderer che non lo riceve non puo' verificarlo su cio' che emette.

    ## `equazione` e la scala dei layer

    AD-23 fissa `0` sfondo · `1` regione di trasformazione · `2` fili · `3`
    componenti · `4` nodi ed etichette semantiche · `5` enfasi sul cambiato · `6`
    annotazioni di boundary · `7` interazione · `8` debug, e aggiunge: *«Il renderer
    non compone layer fuori da questa scala.»*

    **Nessuno dei nove nomina l'equazione**, che `EXPERIENCE.md` e `DESIGN.md`
    richiedono entrambi accanto al sottografo. Non e' una scelta di questo modulo:
    e' una riga che manca alla scala. Chi renderizza la emette al livello `6`,
    insieme alle altre annotazioni ancorate del passo, e lo **dichiara** invece di
    presentarlo come se AD-23 lo prescrivesse — la stessa forma dell'assunzione che
    la Story 1.3 ha dichiarato per il `PatchStore`, che AD-8 non nomina. Va
    ratificata da chi possiede lo spine.
    """

    cambiato: tuple[EntityRef, ...]
    confine: tuple[EntityRef, ...]
    preservato: tuple[EntityRef, ...]
    equazione: Equation

    def __post_init__(self) -> None:
        object.__setattr__(self, "cambiato", _ordinate(self.cambiato, "cambiato"))
        object.__setattr__(self, "confine", _ordinate(self.confine, "confine"))
        object.__setattr__(self, "preservato",
                           _ordinate(self.preservato, "preservato"))
        if not self.cambiato:
            raise ValueError(
                "overlay senza alcuna entita' cambiata: un passo che non annota "
                "nulla come cambiato non ha un sottografo da accendere, e la "
                "sequenza di `DESIGN.md` comincia proprio da li'.")
        if not isinstance(self.equazione, Equation):
            raise TypeError(
                f"{type(self.equazione).__name__} invece di Equation: l'equazione "
                "e' il membro del `TransformResult` che giustifica il passo, non una "
                "stringa composta da chi annota.")
        # Un'entita' non puo' essere insieme il delta e il confine del delta.
        # `DESIGN.md` distingue i due segnali proprio perche' dicono cose opposte —
        # *«forte: sono cio' che cambia»* contro *«piu' discreto del segnale sul
        # delta»* — e un'entita' con due ruoli riceverebbe entrambi, cioe' verrebbe
        # marcata come cambiata mentre l'altra meta' dell'overlay afferma che non lo
        # e'. Il `TransformResult` lo rende impossibile a monte (`∂Tₖ ⊆ Pₖ`, e una
        # preservata non e' consumata): qui si verifica, perche' un overlay
        # assemblato a mano non attraversa quel prodotto.
        doppie = set(self.cambiato) & set(self.confine)
        if doppie:
            raise ValueError(
                f"{', '.join(sorted(str(e) for e in doppie))} annotata insieme come "
                "cambiata e come confine. I due segnali affermano l'opposto sulla "
                "stessa entita': il confine e' dove il sottografo tocca cio' che non "
                "cambia (`∂Tₖ ⊆ Pₖ`).")
        # La stessa collisione, sull'altra coppia: `Pₖ = Entities(Cₖ) ∩
        # Entities(Cₖ₊₁)` e cio' che il `Delta` consuma o produce sta da una parte
        # sola. Un'entita' in entrambi renderebbe indecidibile il predicato di AD-23,
        # che chiede se un riquadro di livello ≥ 5 tocchi *un'entita' di `Pₖ`*.
        doppie = set(self.cambiato) & set(self.preservato)
        if doppie:
            raise ValueError(
                f"{', '.join(sorted(str(e) for e in doppie))} annotata insieme come "
                "cambiata e come preservata. `Pₖ` e' cio' che i due circuiti hanno "
                "in comune: un'entita' che cambia non vi appartiene, e A-0 "
                "prometterebbe di non muovere proprio cio' che il passo sostituisce.")
        # `∂Tₖ ⊆ Pₖ`, scritto sui due campi che lo portano. Non e' ridondante con la
        # guardia del prodotto: un overlay assemblato a mano non attraversa quel
        # prodotto, ed e' l'ingresso che il renderer riceve.
        fuori = set(self.confine) - set(self.preservato)
        if fuori:
            raise ValueError(
                f"{', '.join(sorted(str(e) for e in fuori))} annotata come confine ma "
                "non come preservata. `∂Tₖ ⊆ Pₖ`: il confine e' dove il sottografo "
                "tocca cio' che resta, e un confine che non resta non e' un confine.")


def annota(risultato: TransformResult) -> TransformOverlay:
    """L'overlay del passo, copiato dal prodotto della Trasformazione.

    Non decide niente, e i tre ruoli sono tre copie: `cambiato` e' cio' che il `Delta`
    consuma e produce meno i preservati, `confine` e' `∂Tₖ` e `preservato` e' `Pₖ`,
    ciascuno come il prodotto lo porta. Un renderer che ricalcolasse questi insiemi dai
    due circuiti riaprirebbe l'autocertificazione che AD-22 chiude (AD-26); copiarli da
    chi li ha gia' calcolati e certificati e' l'esatto contrario.
    """
    if not isinstance(risultato, TransformResult):
        raise TypeError(
            f"{type(risultato).__name__} invece di TransformResult: i ruoli "
            "dell'overlay vengono dal prodotto della Trasformazione e da nessun "
            "altro posto (AD-26).")
    delta = risultato.delta
    # `- preserve` e non `- boundary`: una fusione puo' atterrare su un'entita'
    # preservata — `check_delta` lo ammette — e quella non e' cambiata, e' rimasta.
    cambiato = (delta.consumed | delta.produced) - risultato.preserve
    return TransformOverlay(
        cambiato=tuple(cambiato),
        confine=risultato.boundary.entities,
        preservato=tuple(risultato.preserve),
        equazione=risultato.equation,
    )
