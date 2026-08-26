---
title: 'Matrice di impatto CV1–CV6 sul contratto Delta'
type: 'audit'
created: '2026-08-24'
baseline_commit: '82e26e9'
fonte: 'reviews/review-continuita-visuale.md (CV1, CV2, CV3 letti integralmente; CV5, CV6 integralmente; CV4 dal verdetto)'
---

# Verdetto della review, testuale

> **Il braccio A è architettura; i bracci 0, B e C sono ancora prosa.**
> E il verdetto di Gate A è un confronto — un confronto in cui tre termini su quattro
> non hanno tipo non è misurabile.

# Matrice

| Rilievo | Sev. | `PreserveSet` | `Delta` | `Boundary` | `LayoutPatch` | `Certificate` | identità / lineage | Gate A / VCER | **Classificazione per `Delta`** |
|---|---|---|---|---|---|---|---|---|---|
| **CV1** codifica di braccio non tipizzata | critico | ⚠️ rischio di ri-derivazione dal disegno | — | — | ✅ | — | — | ✅ falsa il confronto fra bracci | **richiede un vincolo nel contratto** |
| **CV2** test permanente A-0 falso su B e C | critico | — | — | — | — | — | — | ✅ | **solo metriche / Gate A** |
| **CV3** R-Visual-1 non implicata, nessun predicato di occlusione | critico | — | — | ⚠️ le annotazioni di boundary stanno al layer 6 | ✅ | — | — | ✅ | **richiede un vincolo nel contratto** |
| **CV4** `LayoutIR` del braccio 0, quattro affermazioni | alto | — | — | — | ✅ | — | — | ✅ | **solo rendering / layout** |
| **CV5** «il vincolo è nel tipo» falsificato | alto | — | ⚠️ metodo | — | ✅ | ⚠️ metodo | — | — | **richiede un vincolo di metodo** |
| **CV6** VCER senza entità, identità, ritenzione | alto | — | — | — | ✅ | — | ✅ | ✅ | **ancora aperto, additivo** |

**Nessuno dei tre critici blocca semanticamente `Delta`.** Due lo vincolano, e i vincoli
sono entrati nel contratto.

# I tre vincoli entrati nel contratto

## Da CV1 — `Delta` e `PreserveSet` non si deducono l'uno dall'altro

CV1 descrive un renderer che ricava i preservati come complemento della classe «changed»
in fase di serializzazione: *«non lo propone — lo ricalcola implicitamente»*, e così
*«reintroduce l'autocertificazione che AD-22 ha appena chiuso»*. Il punto di rottura è il
peggiore possibile: *«un bug che si legge come dato»*.

Vincolo: `preserve_set(before, after)` è calcolato **dal confronto dei due circuiti**
(`Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)`, AD-22) e mai dal `Delta`; `Delta` non è definito come
il complemento di `Pₖ`. `check_delta` verifica che siano coerenti, non che uno derivi
dall'altro. Test: `test_preserve_set_si_calcola_dai_circuiti_non_dal_delta`.

## Da CV3 — preservata e boundary non sono disgiunte

CV3 osserva che le entità colpite dal difetto originale, `A` e `B`, sono *«preservate e
insieme boundary»*. Il contratto quindi **non** impone `Boundary ∩ PreserveSet = ∅`.

Conseguenza registrata dentro `Delta`: una entità preservata **può** comparire come uscita
di una derivazione — è dove atterra una fusione — mentre **non può mai** essere consumata.
Test: `test_una_preservata_PUO_essere_uscita_perche_e_li_che_atterra_una_fusione` e
`test_una_preservata_non_puo_essere_consumata`.

## Da CV5 — nessun invariante sta «nel tipo»

CV5: *«Lo stack è Python senza type checker … "il vincolo è nel tipo" non è una proprietà
del sistema: è una convenzione.»*

Vincolo di metodo: ogni invariante di `Delta` ha una guardia che solleva a runtime **e** un
test che l'ha vista sollevare. Le tre guardie strutturali sono state verificate per
mutazione il 24/08/2026 — ognuna uccide esattamente il proprio test, e l'albero ripristinato
torna verde.

# Ciò che resta fuori da `Delta`

- **CV2, CV4** — rendering e protocollo sperimentale. Nessun contatto.
- **CV6** — `LayoutPatch` e `LayoutIR` non hanno identificatore né regola di ritenzione, e
  VCER non è calcolabile come specificata. `Delta` non ha geometria, quindi non è toccato.
  Resta aperto e va chiuso **prima** del percorso renderer.

# Correzione a un audit precedente

`audit-recinti-ad21-2026-08-24.md` elenca **cinque** recinti. CV5 ne richiede un **sesto**:

> nessun percorso di codice del braccio 0 riceve, importa o risolve un `LayoutIR` di `Cₖ` —
> né per parametro, né per `ctx`, né per lookup su identificatore.

Motivo, con le parole della review: un braccio 0 che abbia visto il layout precedente è
*«più continuo del dovuto»*, quindi il divario 0 ↔ A si assottiglia, quindi **il kill
criterion uccide un prodotto valido** — ed è invisibile, perché somiglia a «un rendering un
po' più stabile del previsto». Aggiunto alla storia `2-1b`.

# Un disallineamento di vocabolario, non un difetto

Il catalogo chiuso nomina **passi didattici** — `serie`, `parallelo`, `stella_triangolo`,
`resistenza_equivalente_di_thevenin`, `circuito_equivalente_a_t0` … — mentre le
trasformazioni discusse a voce (`REMOVE_LOAD`, `ZERO_VOLTAGE_SOURCE`, `COLLAPSE_SERIES`)
sono **operazioni atomiche sul grafo**, sotto-passi di quelle. Non sono nel catalogo, e
`test_operazione_fuori_catalogo_rifiutata` lo dimostra usando proprio `REMOVE_LOAD`.

Non l'ho risolto: è la scelta fra estendere il catalogo alle primitive atomiche, oppure
tenere il catalogo al livello didattico e modellare le atomiche come derivazioni interne a
un passo. Tocca direttamente la `SolutionTimeline` e va decisa insieme allo scavo delle
trasformazioni didattiche reali.

## Risolto il 26/08/2026 — Story 1.2

**La seconda.** Il catalogo resta al livello didattico e le atomiche sono derivazioni
interne a un passo: `domain/transform/primitives.py` porta un secondo vocabolario chiuso di
cinque **riscritture strutturali**, disgiunto da `CATALOG`, e `StructuralDerivation.operation`
punta a quello. Il legame fra i due livelli è `catalog.COMPOSITION`, che dichiara di quali
riscritture — con la loro molteplicità — ciascun passo è composto; `TransformResult` esige
che il `Delta` eserciti esattamente la composizione dichiarata. Una `serie` è quindi **un
solo** passo pedagogico con **due** derivazioni: `{R1,R2} --fusione_di_componenti--> {Req}`
e `{b} --eliminazione_di_nodo--> {∅}`.

Le due conseguenze che avevano motivato la scelta:

- SM-C5 non si muove: il numero delle Trasformazioni applicabili resta tre, perché nessuna
  micro-operazione è entrata nel catalogo;
- K-0 continua a pretendere un fotogramma per **passo**, non per riscrittura, che è
  esattamente ciò che chiedeva — «un passo senza disegno è una riga di calcolo».

`REMOVE_LOAD` è coperto (`rimozione_di_componente`); `ZERO_VOLTAGE_SOURCE` **no**, e
l'assenza è deliberata: resta la decisione del proprietario registrata in `deferred-work.md`.
Il paragrafo qui sopra cita `test_operazione_fuori_catalogo_rifiutata`, che non esiste più:
il rifiuto vive ora in `test_una_riscrittura_fuori_vocabolario_e_rifiutata` e nei due test
che distinguono i due sotto-passi invece di confonderli.

Resta aperto l'impatto su `SolutionTimeline`, che nessuna storia ha ancora costruito.
