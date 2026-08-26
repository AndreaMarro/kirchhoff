"""`componi` — la sequenza che K-0 chiede, dentro `src/`.

> *«Un passo senza disegno non e' un passo»* — K-0.

Prima di questa storia i cinque atti che fanno un passo esistevano tutti e cinque
e nessuno li metteva in fila fuori da un file di test: `annota` non aveva un solo
chiamante in `src/`, e `deferred-work.md` lo registra come rilievo aperto della
Story 1.7. Non era un difetto di quella storia — `pipeline/`, `api/` e `adapters/`
erano gia' vuoti prima — ma **questa** storia non e' scrivibile senza chiuderlo:
percorrere avanti e indietro un passaggio richiede che il passaggio sia un
oggetto, e un oggetto lo costruisce qualcuno.

## I cinque atti, e perche' in quest'ordine

    transform  →  applica  →  annota  →  deposita  →  render ×2
    (dominio)     (layout)    (ruoli)   (registri)   (byte)

1. **`transform`** produce `Cₖ₊₁` e il prodotto. E' puro e non sa cosa sia una
   posizione (AD-18): tutto cio' che segue e' fuori dal dominio.
2. **`applica`** costruisce `LayoutIR_{k+1}` conservando i piazzamenti dei
   sopravvissuti. Non muta `LayoutIR_k`, che resta risolvibile — senza quel verso
   `p_k(x)` non esiste piu' nel momento in cui servirebbe misurarlo (CV6).
3. **`annota`** copia i ruoli dal prodotto. Un solo overlay per i due stati:
   e' lo stesso passo annotato su due disegni.
4. **`deposita`** conia il `patch_` e registra i due `lay_`. Da qui il passo e'
   una proiezione **per riferimento**: gli identificatori sono risolvibili.
5. **`render`** emette i due SVG. Due chiamate a una funzione pura, fatte una
   volta sola — vedi il docstring di `schema.py` sul perche' una volta sola.

## Dove finisce questa funzione

Non decide **quale** trasformazione applicare: quello e' il Piano didattico, ed e'
Epic 2. Non pubblica: `publish()` e i suoi otto controlli sono AD-5, e nessun
criterio di questa storia li nomina. Non marca la provenienza: e' FR-18/FR-19.
Compone un passo e restituisce l'oggetto che lo rappresenta — e se la
Trasformazione rifiuta, restituisce il `Refusal` senza costruire niente.
"""

from __future__ import annotations

from ...domain.ir import IR
from ...domain.refusal import Refusal
from ...domain.transform import TransformationKind, transform
from ..layout import LayoutIR, LayoutStore, PatchStore, applica
from ..overlay import annota
from ..serialize import render
from .schema import VisualStep


def componi(
    circuito: IR,
    operazione: TransformationKind,
    *operandi: str,
    layout: LayoutIR,
    layouts: LayoutStore,
    patches: PatchStore,
    istante: int,
    casualita: bytes,
) -> VisualStep | Refusal:
    """Il passo intero, da `Cₖ` e dal suo stato visuale. `Refusal` se non si puo'.

    `istante` e `casualita` entrano **dalla firma** e non si leggono qui: AD-17,
    *«il tempo si inietta»*. Servono a due conii — il `patch_` della `LayoutPatch`
    e il `lay_` dello stato visuale nuovo — e nessuno dei due puo' nascere nel
    dominio, che di orologi non ne ha.

    `layout` e' lo stato visuale di `Cₖ` e **non viene depositato qui se gia' c'e'**:
    lo stesso `LayoutIR` puo' essere il *dopo* di un passo e il *prima* del
    successivo, e il registro e' append-only — ridepositarlo solleverebbe su una
    catena di due passi, che e' il caso ordinario e non un difetto.

    **Il `Refusal` si restituisce, non si solleva** (AD-13): e' un esito di dominio.
    Chi riceve un `Refusal` non ha un passo, e non e' un guasto — e' il sistema che
    dice di non poter certificare. Un `ValueError` da `transform` e' invece un'altra
    cosa: una precondizione violata da chi chiama, e sale.
    """
    esito = transform(circuito, operazione, *operandi)
    if isinstance(esito, Refusal):
        return esito
    dopo_circuito, risultato = esito

    dopo_layout = applica(
        layout, risultato.layout_patch, risultato.delta,
        istante=istante, casualita=casualita)
    overlay = annota(risultato)

    # Il `patch_` nasce al deposito e non nel dominio: `transform` e' pura per
    # AD-2, quindi non ha l'orologio che il conio richiede. Ne segue la proprieta'
    # che SM-14 vuole — un `patch_` identifica **un passo**, non un contenuto.
    patch = patches.deposita(
        risultato.layout_patch, istante=istante, casualita=casualita)
    if layout.identifier not in layouts:
        layouts.deposita(layout)
    layouts.deposita(dopo_layout)

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
            layout.identifier: render(circuito, layout, overlay),
            dopo_layout.identifier: render(dopo_circuito, dopo_layout, overlay),
        },
    )
