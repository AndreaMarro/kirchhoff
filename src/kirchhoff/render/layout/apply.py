"""`applica` — da `LayoutIR_k` a `LayoutIR_{k+1}`, senza toccare cio' che sopravvive.

E' l'applicatore che la Story 1.3 ha dichiarato **non-goal** e di cui ha scritto il
contratto in `render/layout/__init__.py`, perche' la minaccia che CV6 descrive vive
esattamente dentro questa funzione:

> **U2 — la lettura naturale, e quella vietata.** *«Applicare un `LayoutPatch`
> aggiorna il layout in luogo.»* Sotto U2, *«`p_k` non esiste piu' nel momento in cui
> servirebbe misurarlo»* e VCER e' incalcolabile senza rieseguire la derivazione.

Qui non si aggiorna niente in luogo: si **costruisce un secondo stato visuale**.
`prima` esce dalla funzione come vi e' entrato, con lo stesso `lay_` e gli stessi
piazzamenti, e resta risolvibile dal `LayoutStore` che gia' lo ritiene.

## A-0, che qui e' una copia e non un arrotondamento

*«Cio' che appartiene a `preserve` non si e' mosso.»* Il modo piu' semplice di
sbagliarlo e' ricalcolare la posizione di un sopravvissuto e ottenere «quasi» la
stessa — che VCER misura e penalizza, e che DESIGN.md ammette solo *«salvo necessita'
geometriche dimostrabili»*. Questa funzione non ha necessita' geometriche da
dimostrare: **riusa l'oggetto `Placement`**, non i suoi numeri. Non c'e' un percorso
in cui la coordinata di un preservato passi per un'aritmetica, quindi non c'e' un
percorso in cui possa cambiare.

Ne segue la forma della verifica in `tests/`: non `abs(dopo - prima) < eps`, ma
uguaglianza dell'oggetto. Una tolleranza qui misurerebbe una libertà che la funzione
non ha.

## Dove va cio' che nasce, e perche' non e' autolayout

Un'entita' creata non ha una posizione in `prima` — e' nata adesso. Inventargliela
sarebbe l'autolayout, che e' non-goal dichiarato dalla Story 1.4 e non e' diventato
goal qui. Cio' che questa funzione fa e' invece **leggere la lineage**: il `Delta`
dice da quali entita' la nuova deriva, quelle avevano una posizione, e la nuova si
piazza nel loro **baricentro esatto**.

Non e' una scelta estetica ed e' l'unica che risponde alla domanda della storia. Lo
studente deve pensare *«quelle due sono diventate questa»*: l'equivalente compare
dove stavano le due che ha sostituito, non in un punto che un motore di piazzamento
ha scelto per conto proprio. Il baricentro di due `Fraction` e' esatto — nessun
`float`, nessuna cifra che dipenda dall'ordine delle somme (AD-35).

**Non c'e' un ramo per «una creata senza ascendenti piazzati», e non e' una svista.**
C'era, e sollevava; con il controllo di coerenza fra la patch e il `Delta` e' diventato
irraggiungibile, e la catena che lo rende tale e' corta: `nata ∈ create ⊆ produced`,
quindi esiste la derivazione che la produce; `FORME` impone `ingressi_minimi ≥ 1` a
tutte e cinque le riscritture — *«un'entita' creata senza ascendenza non ha lineage
interrogabile»* — quindi quella derivazione ha almeno un ingresso; `Delta.consumed` e'
l'unione degli ingressi, `consumed == remove` e `remove ⊆ piazzate`, quindi **ogni**
ascendente e' piazzato. Un ramo che non si puo' vedere sollevare non e' una difesa: e'
il modo in cui la convenzione del progetto — *«ogni invariante ha una guardia a runtime
e un test che l'ha vista sollevare»* — smette di voler dire qualcosa. Se la catena si
rompesse comunque, `prima.posizione` solleva `KeyError` e nomina l'entita'.

Resta vero che li' un autolayout servirebbe: **quando** una lineage senza ascendenza
diventera' esprimibile, questa e' la riga che va riaperta, e non e' la storia che
introduce l'autolayout.

## Perche' il `Delta` e non solo la `LayoutPatch`

Il contratto che la Story 1.3 ha scritto nominava `applica(prima, patch, ...)`. La
`LayoutPatch` porta pero' `preserve`, `remove` e `create` come **insiemi**, senza
alcun legame fra cio' che sparisce e cio' che nasce: da sola non sa che `Req` viene
da `R1` e `R2` — e con due creazioni nello stesso passo non saprebbe nemmeno quale
viene da quale. La lineage e' nel `Delta`, che e' il membro del `TransformResult` che
la porta per costruzione, e chiederla qui e' preferibile a dedurla: dedurla
significherebbe che l'applicatore sceglie da se' quale entita' e' diventata quale,
cioe' esattamente l'autocertificazione che AD-22 chiude altrove.

I due argomenti restano coerenti fra loro perche' `TransformResult` lo impone gia':
`delta.consumed == patch.remove` e `delta.produced - preserve == patch.create` sono
verificate alla costruzione del prodotto. **Si riverificano comunque qui**, ed e' la
stessa ragione per cui si riverificano le tre condizioni della patch: nulla nella firma
obbliga i due argomenti a venire dallo stesso prodotto, e una coppia disallineata non
produce un errore che li nomina — produce una diagnosi su qualcos'altro. Misurato: una
`create` che il `Delta` non produce cade nel ramo *«nessuna delle entita' da cui deriva
e' piazzata»* e viene raccontata come autolayout mancante; una `create` che si
sovrappone a `preserve` genera due `Placement` per la stessa entita' e viene fermata a
valle da `LayoutIR.__post_init__`, con un messaggio su `p_k(x)` e VCER. Due accuse
sbagliate, che e' il difetto peggiore di questo prodotto.

## `reroute_scope`, che fino a qui non aveva letto nessuno

FR-38 lo vuole come vincolo **normativo del renderer**: *«il rerouting delle coordinate
cambiate e' limitato allo `reroute_scope` dichiarato»*. Il renderer che quel vincolo
nomina e' questa funzione, ed e' il suo primo consumatore in produzione. La verifica si
fa **sul risultato** e non sul percorso di codice: si guarda quali entita' escono con un
piazzamento diverso da quello che avevano, e si controlla che siano dentro lo scope. Un
controllo sul percorso — «tanto i preservati riusano l'oggetto» — riafferma cio' che il
codice fa, e smetterebbe di misurare il giorno in cui il codice cambia.

Puro tranne l'identita': `istante` e `casualita` entrano dalla firma (AD-17).
"""

from __future__ import annotations

from fractions import Fraction

from ...domain.transform import Delta, EntityRef, LayoutPatch
from .schema import LayoutIR, Placement


def _elenco(entita: frozenset[EntityRef] | tuple[EntityRef, ...]) -> str:
    return ", ".join(sorted(str(e) for e in entita))


def mosse(prima: LayoutIR, dopo: LayoutIR) -> frozenset[EntityRef]:
    """Le entita' che in `dopo` hanno una coordinata diversa da quella che avevano.

    E' l'insieme che FR-38 vincola: *«il rerouting delle coordinate cambiate e'
    limitato allo `reroute_scope` dichiarato»*. Sta in una funzione propria, e non
    dentro `applica`, per una ragione che vale in questo progetto come regola: la sua
    seconda meta' — un'entita' **sopravvissuta** che si e' mossa — non e' producibile
    da `applica`, che i piazzamenti dei sopravvissuti li riusa come oggetti. Un
    predicato che non si puo' vedere lavorare non e' una difesa, e qui si puo':
    `test_le_mosse_comprendono_un_sopravvissuto_spostato` lo chiama con un `dopo` in
    cui un preservato e' stato spostato a mano.

    Si guarda il **risultato** e non il percorso di codice. Un controllo che dicesse
    «tanto i preservati riusano l'oggetto» riafferma cio' che `applica` fa oggi, e
    smetterebbe di misurare il giorno in cui `applica` cambia — che e' esattamente il
    giorno in cui servirebbe.
    """
    piazzate = prima.entita()
    return frozenset(
        p.entity for p in dopo.placements
        if p.entity not in piazzate or p != prima.posizione(p.entity))


def _baricentro(punti: tuple[Placement, ...]) -> tuple[Fraction, Fraction]:
    """La media esatta delle coordinate. Su `Fraction` non c'e' nulla da arrotondare."""
    n = len(punti)
    return (sum((p.x for p in punti), Fraction(0)) / n,
            sum((p.y for p in punti), Fraction(0)) / n)


def applica(
    prima: LayoutIR, patch: LayoutPatch, delta: Delta, *,
    istante: int, casualita: bytes,
) -> LayoutIR:
    """`LayoutIR_{k+1}`, nuovo di identita', con i sopravvissuti **non toccati**.

    `prima` non viene mutato e il suo `lay_` non viene riusato: depositare i due nello
    stesso `LayoutStore` fallirebbe se lo fosse, ed e' li' che il contratto si
    controlla.

    Solleva — non restituisce un `Refusal` — su ogni incoerenza fra la patch e lo
    stato visuale che riceve. AD-13 riguarda gli esiti di dominio che l'utente legge;
    una patch che dichiara di togliere cio' che non c'era e' un difetto del
    programma, e degradarlo a esito di dominio lo consegnerebbe all'utente come se
    fosse una risposta sul suo circuito.
    """
    if not isinstance(prima, LayoutIR):
        raise TypeError(f"{type(prima).__name__} invece di LayoutIR")
    if not isinstance(patch, LayoutPatch):
        raise TypeError(f"{type(patch).__name__} invece di LayoutPatch")
    if not isinstance(delta, Delta):
        raise TypeError(f"{type(delta).__name__} invece di Delta")

    piazzate = prima.entita()
    conservate = frozenset(patch.preserve)
    tolte = frozenset(patch.remove)

    # **La relazione fra i due argomenti**, che e' l'unica che li lega e la sola che
    # nessuna delle guardie qui sotto vedrebbe. Le ragioni per riverificarla — e le due
    # diagnosi sbagliate che senza di lei escono — stanno nel docstring del modulo.
    if frozenset(delta.consumed) != tolte:
        raise ValueError(
            f"la patch e il `Delta` non parlano dello stesso passo: `remove` e' "
            f"{{{_elenco(tolte)}}} e cio' che il `Delta` consuma e' "
            f"{{{_elenco(frozenset(delta.consumed))}}}. `TransformResult` impone "
            "`delta.consumed == patch.remove`: due argomenti che non vengono dallo "
            "stesso prodotto lo violano, e la firma non puo' impedirlo.")
    if frozenset(delta.produced) - conservate != frozenset(patch.create):
        raise ValueError(
            f"la patch e il `Delta` non parlano dello stesso passo: `create` e' "
            f"{{{_elenco(frozenset(patch.create))}}} e cio' che il `Delta` produce "
            f"fuori dai preservati e' "
            f"{{{_elenco(frozenset(delta.produced) - conservate)}}}. "
            "`TransformResult` impone `delta.produced - preserve == patch.create`.")

    # Le tre condizioni che `operandi_di_vcer` verifichera' poi sulla tripla intera.
    # Due si possono verificare **qui**, prima di produrre lo stato successivo, e
    # verificarle qui e' meglio: una tripla rotta scoperta a valle nomina il passo,
    # una patch incoerente scoperta qui nomina la patch.
    fuori = conservate - piazzate
    if fuori:
        raise ValueError(
            f"{prima.identifier}: {_elenco(fuori)} in `preserve` ma non piazzata. "
            "A-0 dice che un preservato non si muove; di uno che non c'era non si "
            "puo' dire ne' che si e' mosso ne' che e' rimasto fermo, e SM-14 "
            "valuterebbe `p_k(x)` dove non e' definita.")
    fuori = tolte - piazzate
    if fuori:
        raise ValueError(
            f"{prima.identifier}: {_elenco(fuori)} in `remove` ma non piazzata. "
            "Il passo toglie al renderer cio' che non c'era.")

    # **Cio' che il layout piazza e la patch non nomina.** Non e' un caso innocuo:
    # `preserve` e' `Entities(Cₖ) ∩ Entities(Cₖ₊₁)` e `remove` e' cio' che sparisce,
    # quindi la loro unione e' `Entities(Cₖ)`. Un'entita' fuori da entrambe e'
    # piazzata in uno stato visuale del circuito sbagliato, e l'applicatore
    # dovrebbe decidere da se' se tenerla o buttarla — una decisione che nessuno gli
    # ha dato e che sopravviverebbe silenziosa dentro il disegno.
    orfane = piazzate - conservate - tolte
    if orfane:
        raise ValueError(
            f"{prima.identifier}: piazza {_elenco(orfane)}, che la patch non "
            "conserva ne' rimuove. `preserve ∪ remove` e' l'insieme delle entita' "
            "dello stato visuale di partenza: un'entita' fuori da entrambe verrebbe "
            "tenuta o buttata per scelta dell'applicatore, non del passo.")

    # A-0: si riusano gli oggetti, non si ricalcolano le coordinate.
    successivi = [prima.posizione(e) for e in sorted(conservate)]

    for nata in sorted(patch.create):
        # Nessun filtro `if a in piazzate` e nessun ramo per il caso vuoto: la catena
        # che li rende inutili e' nel docstring del modulo, e passa dal controllo di
        # coerenza qui sopra. Filtrare avrebbe nascosto un ascendente non piazzato
        # dietro un baricentro calcolato sui rimanenti — cioe' avrebbe spostato la
        # nata senza dirlo.
        ascendenti = tuple(
            prima.posizione(a) for a in sorted(delta.derived_from(nata)))
        x, y = _baricentro(ascendenti)
        successivi.append(Placement(nata, x, y))

    dopo = LayoutIR.nuovo(tuple(successivi), istante=istante, casualita=casualita)

    # FR-38 sul risultato.
    fuori = mosse(prima, dopo) - frozenset(patch.reroute_scope)
    if fuori:
        raise ValueError(
            f"{prima.identifier}: {_elenco(fuori)} riceve una coordinata diversa da "
            "quella che aveva, e non e' nello `reroute_scope` dichiarato "
            f"({_elenco(frozenset(patch.reroute_scope))}). FR-38: *«il rerouting "
            "delle coordinate cambiate e' limitato allo `reroute_scope` "
            "dichiarato»*, ed e' un vincolo normativo di chi applica la patch.")
    return dopo
