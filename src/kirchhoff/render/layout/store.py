"""I registri append-only degli operandi di VCER: si deposita, non si sovrascrive.

AD-8, emendata il 24 agosto (v2.1): *«un `LayoutIR` per nodo del `ProofGraph`,
**append-only, mai sovrascritto** per la durata della `ProofSession`»*. Questa e' la
riga che rende VCER calcolabile, ed e' il difetto CV6 nella sua forma piu' corta:

> Con U2, `p_k` non esiste piu' nel momento in cui servirebbe misurarlo.

U2 e' la lettura naturale — applicare un `LayoutPatch` aggiorna il layout in luogo —
ed e' conforme a ogni parola che lo spine aveva scritto prima della v2.1. Sotto U2
`eval/` puo' solo ricostruire `p_k` rieseguendo la derivazione, il che richiede che
il rendering sia gia' deterministico (SM-20), che pero' va misurato **dopo** VCER.
La dipendenza era circolare e non era scritta da nessuna parte. Questo modulo e' U1:
ogni stato visuale resta, e la coppia `(LayoutIR_k, LayoutIR_{k+1})` si risolve dai
due nodi adiacenti senza rieseguire nulla.

## Perche' un registro e non un campo

La ritenzione non e' una proprieta' di un `LayoutIR` — nessun oggetto puo' garantire
di non essere stato sostituito da un altro. E' una proprieta' del posto in cui i
`LayoutIR` stanno, e va imposta li'. `deposita` solleva su un identificatore gia'
scritto invece di accettarlo in silenzio: una sovrascrittura idempotente sarebbe
indistinguibile da un identificatore coniato due volte, che e' un difetto vero.

## Che cosa questo modulo NON e'

**Non e' la persistenza.** Tiene i `LayoutIR` in memoria per la durata di una
sessione: e' l'unita' su cui la regola di ritenzione si verifica, non l'adapter che
la porta su disco. AD-27 vuole quell'adapter fuori dal kernel, e AD-8 impone i
permessi a livello di DB — nessuna delle due cose si decide qui.

**Non applica `LayoutPatch`.** Chi produce lo stato visuale successivo e' il
renderer, ed e' esplicitamente non-goal della Story 1.3.

## Perche' anche il `LayoutPatch` ha un registro, e perche' e' qui

SM-14 misura `p_{k+1}(x) ≈ p_k(x)` **per ogni `x ∈ Pₖ`**: il dominio del confronto
e' `preserve`, che sta nel `LayoutPatch` e in nessun altro posto. Un `patch_` scritto
sull'arco e non risolvibile da nessun registro rende la tripla di CV6 congiungibile
su un lato solo — i due `LayoutIR` si risolvono, il terzo operando no — e VCER resta
un'ipotesi. Il secondo registro di questo modulo chiude quel lato.

**AD-8 non ha una riga per il `LayoutPatch` persistito.** La tabella dei proprietari
nomina `CircuitIR`, `LayoutIR`, `TransformOverlay` (*«non persistito»*), `ProofGraph`,
`Claim`, `SourceAsset`, `ProofSession` e `InteractionState`; il `LayoutPatch` non c'e'
ne' come entita' con scrittore ne' come entita' dichiarata non persistita. Il registro
sta qui, e non sotto `domain/`, perche' e' il posto in cui gli **altri due** operandi
della stessa tripla gia' stanno: `eval/` congiunge in un modulo solo invece che in due
pacchetti. La riga in AD-8 va comunque scritta da chi possiede lo spine — vedi il
rapporto della storia — e finche' non c'e', questa collocazione e' un'assunzione
dichiarata, non un fatto dell'autorita'.

## Chi conia, e perche' non chi produce

`transform` e' pura (AD-2): non ha orologio, quindi non puo' coniare un ULID. Chi
**ritiene** ce l'ha, e conia al deposito con l'istante iniettato — la stessa
disciplina di `LayoutIR.nuovo`, e la ragione per cui le due entita' non hanno due
regole diverse. Ne segue la proprieta' che serve a SM-14: **un `patch_` identifica un
passo, non un contenuto.** Due passi che emettono patch identiche ricevono due
identificatori, quindi il denominatore di VCER li conta due volte, e un'evidenza
«`patch_X` viola la continuita'» sa a quale arco riferirsi.
"""

from __future__ import annotations

from ...domain.identity import IdentityKind, conia
from ...domain.transform import LayoutPatch
from .schema import LayoutIR

#: Il genere che il secondo registro conia. Nominato una volta: il vocabolario
#: chiuso sta in `domain/identity`.
_PATCH: IdentityKind = "patch"


class LayoutStore:
    """Registro append-only. `render/layout` e' l'unico scrittore (AD-8)."""

    __slots__ = ("_per_identificatore",)

    def __init__(self) -> None:
        self._per_identificatore: dict[str, LayoutIR] = {}

    def deposita(self, layout: LayoutIR) -> str:
        """Scrive uno stato visuale. Restituisce il suo `lay_`.

        Solleva se l'identificatore e' gia' stato scritto — anche con un contenuto
        identico. Due depositi dello stesso `lay_` significano che qualcuno ha
        coniato due volte, oppure che sta per sovrascrivere: la prima e' un difetto,
        la seconda e' cio' che AD-8 v2.1 vieta, e accettarle nasconderebbe entrambe.
        """
        if not isinstance(layout, LayoutIR):
            raise TypeError(
                f"deposito di {type(layout).__name__} invece di LayoutIR: il "
                "registro conserva stati visuali, e chi lo interroga si aspetta di "
                "poterne leggere i piazzamenti.")
        gia = self._per_identificatore.get(layout.identifier)
        if gia is not None:
            raise ValueError(
                f"{layout.identifier} e' gia' depositato: il registro e' append-only "
                "e mai sovrascritto (AD-8 v2.1). Uno stato visuale nuovo prende un "
                "identificatore nuovo; se questo e' lo stesso oggetto, e' stato "
                "coniato due volte — di solito perche' due conii nello stesso "
                "millisecondo hanno ricevuto la stessa entropia, che `conia` "
                "richiede nuova a ogni chiamata."
                + ("" if gia == layout else " Il contenuto per giunta differisce, "
                   "quindi il deposito perderebbe lo stato visuale precedente — "
                   "che e' esattamente `p_k` nel momento in cui serve misurarlo."))
        self._per_identificatore[layout.identifier] = layout
        return layout.identifier

    def risolvi(self, identificatore: str) -> LayoutIR:
        """Lo stato visuale di quel `lay_`, o `KeyError`.

        E' il verso che AC1 misura: dopo che il passo `k+1` e' stato prodotto,
        `risolvi(lay_k)` restituisce ancora `LayoutIR_k`, identico a com'era.
        """
        try:
            return self._per_identificatore[identificatore]
        except KeyError:
            raise KeyError(
                f"{identificatore!r} non e' depositato in questo registro. "
                f"Depositati: {', '.join(self.identificatori()) or 'nessuno'}."
            ) from None

    def identificatori(self) -> tuple[str, ...]:
        """I `lay_` depositati, in ordine di deposito.

        L'ordine di deposito e quello dei ULID coincidono finche' l'orologio non
        torna indietro; sono due cose diverse, e questo restituisce la prima, che e'
        un fatto del registro e non una deduzione dai nomi.
        """
        return tuple(self._per_identificatore)

    def __contains__(self, identificatore: object) -> bool:
        return identificatore in self._per_identificatore

    def __len__(self) -> int:
        return len(self._per_identificatore)


class PatchStore:
    """Registro append-only dei `LayoutPatch`, e unico posto in cui nasce un `patch_`.

    Non e' un `LayoutStore` con un altro tipo dentro: le due entita' differiscono su
    dove nasce l'identita'. Un `LayoutIR` arriva gia' con il proprio `lay_` — chi lo
    costruisce e' `render/layout`, che ha l'orologio — mentre un `LayoutPatch` arriva
    da `transform`, che per AD-2 non ce l'ha, e riceve il nome **qui**.
    """

    __slots__ = ("_per_identificatore",)

    def __init__(self) -> None:
        self._per_identificatore: dict[str, LayoutPatch] = {}

    def deposita(self, patch: LayoutPatch, *, istante: int, casualita: bytes) -> str:
        """Conia il `patch_` di questo passo e lo scrive. Restituisce il nome.

        L'istante e l'entropia entrano dalla firma, come in `LayoutIR.nuovo`: e' la
        disciplina di `ClockPort` (AD-17), e senza di essa un registro con orologio
        proprio renderebbe irriproducibile ogni replay.

        Deposita **per passo**, non per contenuto: la stessa patch emessa da due
        passi va depositata due volte e riceve due nomi. E' cio' che permette a
        SM-14 di contare i passi che violano la continuita' invece dei contenuti
        distinti, e a un'evidenza di nominare l'arco.
        """
        if not isinstance(patch, LayoutPatch):
            raise TypeError(
                f"deposito di {type(patch).__name__} invece di LayoutPatch: il "
                "registro conserva il terzo operando di VCER, e chi lo interroga si "
                "aspetta di poterne leggere `preserve`.")
        identificatore = conia(_PATCH, istante, casualita)
        if identificatore in self._per_identificatore:
            raise ValueError(
                f"{identificatore} e' gia' depositato: il registro e' append-only. "
                "Due depositi che coniano lo stesso nome hanno ricevuto lo stesso "
                "istante e la stessa entropia, e `conia` richiede entropia nuova a "
                "ogni chiamata; accettarlo perderebbe la patch di uno dei due passi.")
        self._per_identificatore[identificatore] = patch
        return identificatore

    def risolvi(self, identificatore: str) -> LayoutPatch:
        """Il `LayoutPatch` di quel `patch_`, o `KeyError`.

        E' il lato della tripla di CV6 che senza registro non si congiungeva: da qui
        `eval/` prende `preserve`, cioe' l'insieme delle `x` su cui `p_{k+1}(x) ≈
        p_k(x)` va deciso.
        """
        try:
            return self._per_identificatore[identificatore]
        except KeyError:
            raise KeyError(
                f"{identificatore!r} non e' depositato in questo registro. "
                f"Depositati: {', '.join(self.identificatori()) or 'nessuno'}."
            ) from None

    def identificatori(self) -> tuple[str, ...]:
        """I `patch_` depositati, in ordine di deposito."""
        return tuple(self._per_identificatore)

    def __contains__(self, identificatore: object) -> bool:
        return identificatore in self._per_identificatore

    def __len__(self) -> int:
        return len(self._per_identificatore)
