"""`componi` — la proiezione visuale dell'evidenza certificata, dentro `src/`.

> *«Un passo senza disegno non e' un passo»* — K-0.

Il motore didattico ha gia' prodotto `TransformExecution` — before, after e
results sono fatti certificati a monte. Questa funzione li proietta in un
`VisualStep` e non decide piu' nulla di elettrico: non quale trasformazione
e' avvenuta, non con quali operandi, non qual e' il dopo, non che cosa dice
l'equazione, non quali entita' sono preservate. Tutto questo arriva dentro
l'esecuzione; qui si legge, si dispone, si annota, si deposita, si disegna.

## I quattro atti, e perche' in quest'ordine

    proietta  →  annota  →  deposita  →  render ×2
    (certificato) (ruoli)   (registri)   (byte)

1. **proietta**: `after` e' `esecuzione.after`, il prodotto e'
   `esecuzione.results[0]`, l'operazione e' quella del piano certificato.
   Nessuna riesecuzione di `transform` (H5): se il dominio esplodesse ora,
   la proiezione riuscirebbe comunque, perche' non ne ha bisogno.
2. **`applica`** costruisce `LayoutIR_{k+1}` conservando i piazzamenti dei
   sopravvissuti. Non muta `LayoutIR_k`, che resta risolvibile — senza quel verso
   `p_k(x)` non esiste piu' nel momento in cui servirebbe misurarlo (CV6).
3. **`annota`** copia i ruoli dal prodotto. Un solo overlay per i due stati:
   e' lo stesso passo annotato su due disegni.
4. **`render ×2 + deposita`**: i due SVG nascono prima del deposito, cosi' un
   difetto del disegno non lascia mezzo passo nei registri. Due chiamate a una
   funzione pura, fatte una volta sola — vedi il docstring di `schema.py` sul
   perche' una volta sola. Il `patch_` nasce al deposito e non nel dominio:
   `transform` e' pura per AD-2, quindi non ha l'orologio che il conio richiede.

## Dove finisce questa funzione

Non decide **quale** trasformazione applicare: quello e' il Piano didattico.
Non pubblica, non marca la provenienza, non certifica: il `Certificate` che il
passo porta e' lo stesso oggetto della run, per riferimento. Non crea `Claim`:
un difetto di proiezione diventa `Failure("render", ...)` e non tocca mai un
affermazione elettrica — non ce n'e' nessuna qui da cambiare.

`layout` e' lo stato visuale di `Cₖ` e **non viene depositato qui se gia' c'e'**:
lo stesso `LayoutIR` puo' essere il *dopo* di un passo e il *prima* del
successivo, e il registro e' append-only — ridepositarlo solleverebbe su una
catena di due passi, che e' il caso ordinario e non un difetto.
"""

from __future__ import annotations

from ...domain.didactic.execute import TransformExecution
from ...pipeline.failure import Failure
from ..layout import LayoutIR, LayoutStore, PatchStore, applica
from ..overlay import annota
from ..serialize import render
from .schema import VisualStep


def componi(
    esecuzione: TransformExecution,
    *,
    layout: LayoutIR,
    layouts: LayoutStore,
    patches: PatchStore,
    istante: int,
    casualita: bytes,
) -> VisualStep | Failure:
    """Il passo intero, dall'esecuzione certificata e dal suo stato visuale.

    `istante` e `casualita` entrano **dalla firma** e non si leggono qui: AD-17,
    *«il tempo si inietta»*. Servono a due conii — il `patch_` della `LayoutPatch`
    e il `lay_` dello stato visuale nuovo — e nessuno dei due puo' nascere nel
    dominio, che di orologi non ne ha.

    Un difetto di proiezione (disposizione, annotazione, rendering, deposito)
    diventa `Failure("render", ...)` con la causa conservata: e' un guasto
    visuale, mai un Claim cambiato (H5-6).
    """
    if not isinstance(esecuzione, TransformExecution):
        return Failure(
            "render",
            f"proiezione di {type(esecuzione).__name__} invece di "
            "TransformExecution: la via visuale consuma evidenza certificata")
    risultato = esecuzione.results[0]
    operazione = esecuzione.plan.actions[0].kind
    try:
        dopo_layout = applica(
            layout, risultato.layout_patch, risultato.delta,
            istante=istante, casualita=casualita)
        overlay = annota(risultato)
        prima_svg = render(esecuzione.before, layout, overlay)
        dopo_svg = render(esecuzione.after, dopo_layout, overlay)

        # Il `patch_` nasce al deposito e non nel dominio: `transform` e' pura per
        # AD-2, quindi non ha l'orologio che il conio richiede. Ne segue la proprieta'
        # che SM-14 vuole — un `patch_` identifica **un passo**, non un contenuto.
        patch = patches.deposita(
            risultato.layout_patch, istante=istante, casualita=casualita)
        if layout.identifier not in layouts:
            layouts.deposita(layout)
        layouts.deposita(dopo_layout)
    except Exception as e:
        return Failure("render", f"{type(e).__name__}: {e}")

    return VisualStep(
        operation=operazione,
        prima=layout.identifier,
        dopo=dopo_layout.identifier,
        patch=patch,
        risultato=risultato,
        # **Lo stesso overlay sui due disegni**, che e' cio' che rende A-0
        # misurabile *fra i due stati* invece che dentro uno solo: chi renderizza
        # evidenzia le entita' di `cambiato` che il `LayoutIR` in mano piazza, e le
        # altre non le piazza. La sequenza di `EXPERIENCE.md` accende `R1` e `R2`
        # su `Cₖ` e mostra l'equivalente su `Cₖ₊₁`: un passo, due fotogrammi.
        fotogrammi={
            layout.identifier: prima_svg,
            dopo_layout.identifier: dopo_svg,
        },
    )
