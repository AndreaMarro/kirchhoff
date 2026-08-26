"""Il passo come **proiezione per riferimento**: identificatori e fotogrammi.

AD-21 v2 dice come si scrive un tipo che nomina piu' rappresentazioni senza
diventare il quinto contenitore che le fa collassare:

> `ProofSession` e' una **proiezione per riferimento**, non un aggregato per
> valore. Porta gli identificatori dei quattro e **un'istantanea immutabile di
> cio' che serve a renderla**, mai i tipi mutabili. Ricostruirla significa
> **risolvere gli identificatori**, non deserializzare uno stato.

`VisualStep` e' scritto su quella frase, riga per riga. Porta i `lay_` dei due
stati visuali e il `patch_` che li lega — identificatori, risolvibili nei registri
di `render/layout` — e come istantanea porta i **due SVG gia' emessi**. Non
contiene nessun `LayoutIR`, nessun `CircuitIR`, nessun `TransformOverlay`: chi
volesse le strutture risolve gli identificatori nel `LayoutStore` e nel
`PatchStore`, che e' esattamente cio' che AD-21 chiama ricostruire.

## Perche' i fotogrammi sono byte e non una funzione da chiamare

L'AC chiede che la commutazione *Prima ↔ Dopo* sia **istantanea, ripetibile
all'infinito e senza conferma** (UX-DR12). Con i due SVG gia' emessi la proprieta'
non e' verificata a campione: e' vera per costruzione, perche' commutare
**sceglie fra due stringhe**, non renderizza. AD-35 impone la purezza a `render`,
e la purezza rende i due rendering ripetibili; renderizzarli una volta sola li
rende anche *irripetibili in modo diverso* — non c'e' una seconda corsa che possa
divergere dalla prima.

E' anche l'unico modo di soddisfare AD-10 v2 alla lettera: *«`export()` **non
ri-renderizza**»*. La forma statica e l'interattiva escono dallo stesso oggetto
`str`, non da due chiamate che si spera coincidano — `esporta` restituisce
letteralmente le stesse stringhe, e un test lo verifica con `is`.

## `InteractionState`, e perche' qui non e' persistito

AD-8 gli assegna il client e nessuno scrittore: *«non e' persistito lato server:
non ha riga, quindi non ha scrittore»*. La chiusura di C8 nella review avversaria
lo precisa: e' **stato di vista**, «non compare in alcuna risposta di tool, non
entra in `resume_ref`, e la sua perdita non degrada la `ProofSession`».

Qui c'e' quindi il **tipo**, non un registro: un valore immutabile che nomina per
identificatore lo stato guardato, e nessuna funzione che lo scriva da qualche
parte. `commuta` restituisce il valore nuovo e non tocca niente.

> **Assunzione dichiarata, da ratificare.** AD-21 elenca fra i propri *binds*
> `domain/`, `render/` e `ui/`; `ui/` non esiste nell'albero sorgente, e la review
> dei confini registra proprio questo come il buco di `InteractionState` («il
> quarto tipo non ha un modulo proprio in nessun documento»). Il tipo nasce qui
> perche' qui c'e' il passo che si commuta, ed e' la stessa forma di assunzione
> che la Story 1.3 ha dichiarato per il `PatchStore` e la 1.7 per il layer
> dell'equazione: dichiarata nel modulo, non presentata come se un'autorita' la
> prescrivesse. Chi possiede lo spine decide se `ui/` la reclama.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from ...domain.identity import IdentityKind, verifica
from ...domain.transform import (
    CATALOG,
    Certificate,
    Equation,
    EntityRef,
    StructuralDerivation,
    TransformResult,
    TransformationKind,
    preconditions_of,
)

#: Nominati una volta, come in `domain/proof/graph.py`: il vocabolario chiuso dei
#: generi sta in `domain/identity` e qui si cita, non si ridichiara.
_STATO_VISUALE: IdentityKind = "lay"
_PATCH: IdentityKind = "patch"


@dataclass(frozen=True, slots=True)
class InteractionState:
    """Cosa l'utente sta guardando: uno dei due stati visuali, per identificatore.

    La quarta rappresentazione di AD-21, e la piu' piccola: un `lay_` e nient'altro.
    Non contiene il `LayoutIR` che nomina — *«nessuno dei quattro contiene un
    riferimento a un altro se non per identificatore»* — e non porta ne' selezione
    ne' cronologia, perche' l'AC di questa storia riguarda la commutazione e
    inventare campi per interazioni che nessuna storia chiede li lascerebbe senza
    un test che li veda usati.

    **Non e' un contenitore di stato di dominio.** Perderlo significa non sapere
    quale dei due stati era in vista, e nient'altro: il passo resta intero, i due
    fotogrammi restano gli stessi, la derivazione non si muove.
    """

    mostrato: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "mostrato", verifica(self.mostrato, _STATO_VISUALE))


@dataclass(frozen=True, slots=True)
class Justification:
    """I **quattro** campi di UX-DR23, e nessun quinto.

    > «Perche' posso farlo?» risponde con **quattro campi gia' calcolati** —
    > terminali, precondizioni, formula, certificato — e **non genera
    > spiegazioni.»

    Tre dei quattro sono membri del `TransformResult` e arrivano qui **per
    riferimento**, non copiati: `terminali` e' `boundary.entities`, `formula` e'
    l'`Equation`, `certificato` e' il `Certificate`. `precondizioni` e' la
    dichiarazione del Catalogo per quell'operazione. Nessuno dei quattro viene
    composto al momento della domanda, ed e' cio' che FR-49 chiede quando dice
    *«ogni elemento della risposta e' un campo del passo, non prosa prodotta al
    momento»*.

    Il test che lo tiene chiuso confronta con `is`, non con `==`: l'uguaglianza
    passerebbe anche su una copia ricostruita, e una copia ricostruita e'
    precisamente la cosa che questo tipo esiste per escludere.
    """

    terminali: tuple[EntityRef, ...]
    precondizioni: tuple[str, ...]
    formula: Equation
    certificato: Certificate


@dataclass(frozen=True, slots=True)
class StaticStep:
    """La forma statica del passo: gli stessi byte, senza nulla da premere.

    AD-10 v2: *«l'SVG semantico verificato e' la sorgente unica di ogni altro
    formato»*, ed `export()` *«non ri-renderizza: applica la marcatura e trasforma
    l'SVG gia' certificato»*.

    **Non e' l'`Artifact` di AD-10, e non deve sembrarlo.** Un `Artifact` porta la
    Marcatura di provenienza, che AD-10 dichiara non conformita' se manca; la
    marcatura e' materia di FR-18/FR-19 e dell'Epic 4, e nessun criterio di questa
    storia la nomina. Questo tipo e' cio' che `export()` **consumera'**: il passo
    ridotto ai byte gia' emessi, con gli identificatori che dicono di quali stati
    visuali sono i byte. Prendere il nome `Artifact` senza la marcatura sarebbe
    dichiarare conforme cio' che non lo e' ancora.
    """

    operation: TransformationKind
    prima: str
    dopo: str
    fotogrammi: tuple[str, str]

    def __post_init__(self) -> None:
        """Le stesse guardie delle sorelle, perche' il tipo non dice chi lo costruisce.

        `esporta()` produce istanze corrette per costruzione, e finche' e' l'unico
        costruttore le guardie qui non scattano mai. Ma il tipo e' esportato in
        `__all__` ed e' *«cio' che `export()` consumera'»*: chi lo importa non ha
        modo di sapere che `esporta()` sia l'unica maniera legittima di ottenerne
        uno, e la proprieta' di AD-10 — *«stessi byte, stessa sorgente semantica»* —
        varrebbe allora per le istanze che escono di li' e per nessun'altra.

        E' la convenzione che questo repository dichiara: *«ogni invariante ha una
        guardia a runtime e un test che l'ha vista sollevare»*, perche' lo stack e'
        Python senza type checker e «il vincolo e' nel tipo» qui non e' vero. Prima
        di questa guardia `StaticStep(operation="serie", prima="non-un-lay",
        dopo="non-un-lay", fotogrammi=("",))` si costruiva senza proteste — tre
        invarianti violati in una riga, e nessuno che se ne accorgesse.
        """
        if self.operation not in CATALOG:
            raise ValueError(
                f"operazione {self.operation!r} fuori dal catalogo chiuso. La forma "
                "statica nomina il passo che porta, e un passo che il Catalogo non "
                "conosce non e' stato certificato da nessuno.")
        object.__setattr__(self, "prima", verifica(self.prima, _STATO_VISUALE))
        object.__setattr__(self, "dopo", verifica(self.dopo, _STATO_VISUALE))
        if self.prima == self.dopo:
            raise ValueError(
                f"{self.prima}: i due stati visuali della forma statica sono lo "
                "stesso. Affiancarli (UX-DR27) mostrerebbe due volte lo stesso "
                "disegno sotto l'etichetta *Prima* e sotto quella *Dopo*.")
        if not isinstance(self.fotogrammi, tuple):
            raise TypeError(
                f"fotogrammi {type(self.fotogrammi).__name__} invece di tuple: la "
                "forma statica non ha un comando da premere, quindi la **sequenza** "
                "e' l'unica cosa che dice quale disegno viene prima.")
        if len(self.fotogrammi) != 2:
            raise ValueError(
                f"{len(self.fotogrammi)} fotogrammi invece di due. Un passo ha due "
                "stati visuali e due disegni: uno solo non si commuta e non si "
                "affianca, tre non si sa a quale `lay_` appartengano.")
        for i, svg in enumerate(self.fotogrammi):
            if not isinstance(svg, str) or not svg.strip():
                raise ValueError(
                    f"fotogramma {i} vuoto o non testuale ({type(svg).__name__}). "
                    "AD-10 chiama i due disegni la sorgente unica di ogni altro "
                    "formato, e una sorgente vuota non e' una sorgente.")
        if self.fotogrammi[0] == self.fotogrammi[1]:
            raise ValueError(
                "i due fotogrammi della forma statica sono gli stessi byte. Due "
                "stati visuali distinti che disegnano lo stesso identico SVG sono "
                "un passo che non si vede, e A-0 confronterebbe un disegno con se "
                "stesso — che e' vero per chiunque e non misura nulla.")


@dataclass(frozen=True, slots=True)
class VisualStep:
    """Il passo intero: due identificatori di stato visuale, la patch, due fotogrammi.

    | Cio' che porta | Forma | Perche' cosi' |
    |---|---|---|
    | i due stati visuali | `lay_`, `lay_` | AD-21: per identificatore, mai la struttura |
    | la patch che li lega | `patch_` | il terzo lato della tripla di CV6 |
    | i due disegni | due `str` | l'istantanea immutabile di AD-21 v2 |
    | il prodotto | `TransformResult` | non e' una delle quattro rappresentazioni: e' cio' che AD-2 dice che una Trasformazione restituisce |

    **Il prodotto sta qui per valore e non e' un'eccezione alla regola.** AD-21
    enumera i quattro tipi che non si contengono a vicenda; il `TransformResult`
    non e' fra loro, ed e' l'oggetto da cui ogni risposta di questa storia si
    legge — la lineage dal `Delta`, i terminali dal `Boundary`, la formula
    dall'`Equation`, il certificato dal `Certificate`. Tenerne invece delle copie
    sarebbe la stessa cosa scritta due volte (E-62), nel punto in cui le due
    scritture rispondono alla stessa domanda dell'utente.
    """

    operation: TransformationKind
    prima: str
    dopo: str
    patch: str
    risultato: TransformResult
    fotogrammi: MappingProxyType[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "prima", verifica(self.prima, _STATO_VISUALE))
        object.__setattr__(self, "dopo", verifica(self.dopo, _STATO_VISUALE))
        object.__setattr__(self, "patch", verifica(self.patch, _PATCH))
        if self.prima == self.dopo:
            raise ValueError(
                f"{self.prima}: i due stati visuali del passo sono lo stesso. "
                "Commutare non mostrerebbe niente, e A-0 confronterebbe un disegno "
                "con se stesso — che e' vero per chiunque e non misura nulla.")
        if self.operation != self.risultato.certificate.operation:
            raise ValueError(
                f"il passo si dichiara {self.operation!r} e porta il prodotto di "
                f"{self.risultato.certificate.operation!r}. L'operazione la nomina "
                "il certificato, che e' l'unico dei due ad averla verificata.")
        fotogrammi = dict(self.fotogrammi)
        if set(fotogrammi) != {self.prima, self.dopo}:
            raise ValueError(
                f"i fotogrammi sono per {sorted(fotogrammi)} e gli stati visuali del "
                f"passo sono {sorted((self.prima, self.dopo))}. Un disegno senza il "
                "proprio `lay_` non e' attribuibile a uno stato, e commutare "
                "sceglierebbe fra due immagini di cui una non si sa di che cosa sia.")
        # La ragione scritta nella guardia sui due `lay_` — *«commutare non
        # mostrerebbe niente»* — vale identica per due disegni byte per byte uguali
        # sotto due identificatori diversi, e quel caso passava. Due `lay_` distinti
        # dicono che il registro conserva due stati; solo due **disegni** distinti
        # dicono che commutare mostra qualcosa. La prima guardia parla degli
        # identificatori, questa dei byte, e la seconda non discende dalla prima:
        # `applica` conia sempre un `lay_` nuovo, anche per un passo il cui
        # rendering non cambiasse di un carattere.
        if fotogrammi[self.prima] == fotogrammi[self.dopo]:
            raise ValueError(
                f"i due fotogrammi di {self.prima} e {self.dopo} sono gli stessi "
                "byte. I due stati visuali differiscono di identificatore e non di "
                "disegno: commutare all'infinito (UX-DR12) mostrerebbe sempre la "
                "stessa immagine, e A-0 confronterebbe un disegno con se stesso.")
        # Congelato **dopo** il controllo e a partire da una copia: una mappa
        # passata qui resterebbe altrimenti condivisa col chiamante, che potrebbe
        # sostituire un fotogramma dopo che le guardie sono passate. E' la stessa
        # ragione per cui `LayoutIR` congela i piazzamenti e `ProofGraph` i nodi.
        object.__setattr__(self, "fotogrammi", MappingProxyType(fotogrammi))

    # --- la commutazione ------------------------------------------------------

    def commuta(self, stato: InteractionState) -> InteractionState:
        """L'altro stato visuale. Totale, involutiva, senza conferma (UX-DR12).

        Non c'e' un parametro di conferma e non c'e' un esito «non commutato»: sono
        le due forme in cui una conferma entrerebbe in una firma, e UX-DR12 chiede
        due stati *«commutabili all'infinito»*. `commuta(commuta(s)) == s` per
        costruzione, quindi la ripetibilita' e' una proprieta' algebrica e non una
        misura su un numero di giri scelto da chi scrive il test.

        Solleva su uno stato che non appartiene al passo: e' un errore di
        programmazione — l'`InteractionState` di un altro passo — e rispondere
        `prima` lo renderebbe silenzioso, mostrando all'utente il disegno sbagliato
        senza che nulla se ne accorga.
        """
        if stato.mostrato == self.prima:
            return InteractionState(self.dopo)
        if stato.mostrato == self.dopo:
            return InteractionState(self.prima)
        raise ValueError(
            f"{stato.mostrato} non e' uno stato visuale di questo passo "
            f"({self.prima}, {self.dopo}): commutarlo darebbe il disegno di una "
            "derivazione diversa.")

    def fotogramma(self, stato: InteractionState) -> str:
        """L'SVG dello stato guardato. Una scelta fra due stringhe, non un rendering."""
        try:
            return self.fotogrammi[stato.mostrato]
        except KeyError:
            raise ValueError(
                f"{stato.mostrato} non e' uno stato visuale di questo passo "
                f"({self.prima}, {self.dopo}).") from None

    def apertura(self) -> InteractionState:
        """Lo stato da cui si comincia: *Prima*.

        UX-DR22 vieta l'auto-avanzamento. Aprire su `dopo` mostrerebbe il passo
        gia' compiuto e lascerebbe allo studente il compito di tornare indietro per
        vedere da dove si partiva — che e' un avanzamento che nessuno ha chiesto.
        """
        return InteractionState(self.prima)

    # --- l'ispezione, FR-49 ---------------------------------------------------

    @property
    def entita(self) -> frozenset[EntityRef]:
        """`Entities(Cₖ) ∪ Entities(Cₖ₊₁)`: di chi questo passo puo' parlare.

        Le tre parti sono disgiunte e la loro unione e' esatta: `Pₖ` e' cio' che i
        due circuiti hanno in comune, `consumed` cio' che sta solo in `Cₖ`,
        `produced` cio' che sta solo in `Cₖ₊₁`. Non c'e' una quarta classe, quindi
        non serve risolvere nessun `CircuitIR` per sapere se un'entita' appartiene
        al passo — che e' anche l'unica maniera di chiederlo restando la proiezione
        per riferimento che AD-21 prescrive.
        """
        delta = self.risultato.delta
        return frozenset(self.risultato.preserve) | delta.consumed | delta.produced

    def _sua(self, entita: EntityRef, domanda: str) -> EntityRef:
        """Solleva se `entita` non e' di questo passo. La stessa regola di `commuta`.

        `commuta` e `fotogramma` sollevano gia' su uno stato visuale estraneo, con
        la ragione scritta nel loro docstring: *«rispondere `prima` lo renderebbe
        silenzioso, mostrando all'utente il disegno sbagliato senza che nulla se ne
        accorga»*. Le tre risposte di FR-49 sono la stessa classe d'ingresso e
        avevano la risposta opposta — `()`, `False`, `None` su un'entita' che non
        sta ne' in `Cₖ` ne' in `Cₖ₊₁`.

        `e_lo_stesso` e' il caso che mostra perche' il silenzio non e' innocuo:
        rispondeva `False`, cioe' **affermava** «non e' la stessa attraverso il
        passo» di qualcosa che nel passo non c'e'. E' un'affermazione di dominio su
        un'entita' inesistente, ed e' precisamente cio' che K-2 chiama un claim
        senza evidenza. `()` e `None` sono invece risposte legittime **per
        un'entita' del passo** — `deriva_da(node:a)` e' vuoto perche' da `a` non
        nasce niente — e mantenerle distinguibili dal caso estraneo e' l'unico modo
        perche' vogliano dire qualcosa.
        """
        if not isinstance(entita, EntityRef):
            raise TypeError(
                f"{type(entita).__name__} invece di EntityRef: le tre risposte di "
                "FR-49 si leggono dal `Delta` e da `preserve`, che nominano entita'.")
        if entita not in self.entita:
            raise ValueError(
                f"{entita} non e' un'entita' di questo passo: non sta ne' in `Cₖ` "
                f"ne' in `Cₖ₊₁`. «{domanda}» non ha una risposta su di lei, e "
                "rispondere comunque darebbe a chi chiede un'affermazione di "
                "dominio su un'entita' che il passo non ha mai visto.")
        return entita

    def deriva_da(self, entita: EntityRef) -> tuple[EntityRef, ...]:
        """Da quali entita' `entita` deriva. Vuoto se non deriva da nessuna.

        FR-49: *«selezionando un elemento derivato — per esempio `R34` — il sistema
        mostra da quali elementi deriva»*. La risposta e' del `Delta`, che la porta
        gia' calcolata: qui si inoltra la domanda, non si ricostruisce la lineage
        dai due circuiti.

        Solleva su un'entita' estranea al passo: vedi `_sua`. Vuoto resta la
        risposta di un'entita' **del** passo che non deriva da nessuna.
        """
        return self.risultato.delta.derived_from(
            self._sua(entita, "da cosa deriva?"))

    def e_lo_stesso(self, entita: EntityRef) -> bool:
        """Se `entita` attraversa il passo restando la stessa: appartiene a `Pₖ`.

        FR-49: *«selezionando un nodo, ne mostra la continuita' attraverso il
        passo»*. `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` **dopo `node_mapping`**, e
        chi vi appartiene ha `id_{k+1}(x) = id_k(x)` senza tolleranza (AD-22): la
        risposta e' quindi l'appartenenza al `preserve` che la Trasformazione ha
        calcolato e il certificato ha attestato, non un confronto fatto qui.

        Solleva su un'entita' estranea al passo: vedi `_sua`. `False` significa
        *«e' del passo e non lo attraversa»* — consumata, prodotta — e non
        *«non ne ho mai sentito parlare»*.
        """
        return self._sua(entita, "e' lo stesso?") in self.risultato.preserve

    def che_ne_e_stato(self, entita: EntityRef) -> StructuralDerivation | None:
        """La riscrittura che ha toccato `entita`, o `None` se il passo non l'ha toccata.

        E' l'altra meta' di `deriva_da`, e serve al nodo che il passo **assorbe**:
        `deriva_da(node:a)` e' vuoto perche' da `a` non nasce niente, ma `a` non e'
        rimasto — la fusione l'ha inghiottito, e la lineage lo dice.

        Solleva su un'entita' estranea al passo: vedi `_sua`. `None` significa
        *«e' del passo e il passo non l'ha toccata»* — `che_ne_e_stato(node:b)` —
        e senza la guardia era indistinguibile da un'entita' inesistente.
        """
        return self.risultato.delta.what_happened_to(
            self._sua(entita, "che ne e' stato?"))

    @property
    def giustificazione(self) -> Justification:
        """«Perche' posso farlo?» — quattro campi letti, nessuna prosa (UX-DR23).

        Ogni campo e' **lo stesso oggetto** che il prodotto o il Catalogo portano:
        non si formatta niente, non si concatena niente, non si sceglie fra due
        formulazioni. E' una proprieta' e non un metodo con parametri perche' non
        c'e' nulla da parametrizzare: la risposta non dipende da chi chiede, e una
        risposta che dipendesse da chi chiede sarebbe una spiegazione.
        """
        return Justification(
            terminali=self.risultato.boundary.entities,
            precondizioni=preconditions_of(self.risultato.certificate.operation),
            formula=self.risultato.equation,
            certificato=self.risultato.certificate,
        )

    # --- l'export, AD-10 ------------------------------------------------------

    def esporta(self) -> StaticStep:
        """La forma statica, **dagli stessi byte**. Non ri-renderizza (AD-10 v2).

        Le due stringhe restituite sono gli oggetti che il passo gia' porta, non
        una nuova emissione che si spera identica. E' la differenza che AD-10 v2
        e' stata emendata per chiudere: prima dell'emendamento *«il byte-stream
        verificato non era mai quello che l'utente riceveva»*, perche' l'artefatto
        consegnato nasceva da una seconda passata.

        L'ordine e' `prima → dopo` e non e' arbitrario: la forma statica non ha un
        comando da premere, quindi la sequenza dei due disegni e' l'unica cosa che
        dice quale viene prima. UX-DR27 chiede i due stati **affiancati** sopra i
        768 px, e affiancati in quell'ordine.
        """
        return StaticStep(
            operation=self.operation,
            prima=self.prima,
            dopo=self.dopo,
            fotogrammi=(self.fotogrammi[self.prima], self.fotogrammi[self.dopo]),
        )
