---
title: 'Spike D4 — stack del renderer, con CV6 e D11'
type: 'spike'
created: '2026-08-24'
baseline_commit: 'ad29c8e'
decisione: 'D4 (§27.4) — aperta, decisore owner'
---

# Cosa era già deciso e non lo sapevamo

La spike doveva scegliere fra candidati. Leggendo D4, le sue dipendenze e gli AD v2, **quattro
delle sette domande hanno già una risposta scritta nello spine**, e vincolano la scelta più di
qualunque confronto fra librerie.

**AD-10 v2** — *«l'SVG semantico verificato è la sorgente unica di ogni altro formato»*. Emendata
perché *«PDF e CircuiTikZ non possono portare `data-component-id`, quindi uscivano col Badge
Verificata senza aver mai attraversato alcun round-trip»*. Questa riga **risponde da sola alla
settima domanda**: non esistono due pipeline semantiche, ne esiste una e gli altri formati ne
derivano.

**AD-35 v2** — `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` è **pura**: stessi ingressi,
stessi byte. Niente orologio, niente identificatori generati a runtime, niente casualità senza seme
esplicito fra gli ingressi, **nessun ordinamento che dipenda dall'ordine d'inserimento in una
mappa**. Il determinismo è una famiglia di test obbligatoria, e il fallimento è di CI, non un
`Refusal`. Risponde alla seconda domanda e **squalifica** ogni libreria che non sia usabile in modo
puro.

**AD-31 v2** — un controllo di **incidenza geometrica deterministico** verifica che ogni estremo di
filo tocchi il terminale che l'annotazione dichiara. E la riga che decide tutto:
*«L'annotazione è **derivata** dalla geometria dove possibile, mai il contrario: chi genera il
disegno non scrive a mano l'attributo che lo certifica.»* Squalifica ogni stack in cui gli attributi
semantici si applicano a un disegno prodotto da qualcun altro.

**`RenderPort` è ritirato** (structural seed): *«i port isolano il non deterministico e AD-35 rende
`render/` puro»*. Non c'è un'astrazione dietro cui nascondere una libreria non deterministica.

# I candidati realmente nominati nei documenti

Ricerca su tutto `_bmad-output`, `docs/` e `KIRCHHOFF-KNOWLEDGE` di: schemdraw · CircuiTikZ · TikZ ·
svg.js · snap.svg · d3 · elkjs · dagre · graphviz · cytoscape · konva · two.js · paper.js ·
react-flow · matplotlib · weasyprint · resvg · cairosvg · typst.

| Candidato | Occorrenze | Dove |
|---|---|---|
| LaTeX / CircuiTikZ | ~130 | corpus fonti, `review-versioni.md` (17), spine (5), PRD, epics |
| matplotlib | 3 | `review-versioni.md` |
| d3 | 4 | solo nel corpus di fonti esterne |
| schemdraw · elkjs · dagre · graphviz · svg.js · konva · react-flow | **0** | mai nominati |

Nella tabella `Stack` dello spine (`:779-782`) **CircuiTikZ + pdflatex** compare come «da
confermare», accanto a React+Vite+Tailwind e Redis+RQ. Con vincoli d'ambiente già misurati da
qualcuno: *«niente lmodern, niente babel italiano, label CircuiTikZ con `=` racchiusi in graffe»*.

**Non esiste codice di rendering schematico da nessuna parte.** Verificato con ricerca di
`data-component-id`, `data-terminal`, `circuitikz`, `schemdraw`, `drawSchematic`, `renderSchematic`,
`schematic` su `whiteboard-studio/sim/src`, `whiteboard-studio/studio/src` e `kirchhoff/src`: zero
file.

# Le sette domande

| | Generazione SVG deterministica nostra | CircuiTikZ + pdflatex come renderer | schemdraw | Layout engine a grafo (elkjs/dagre/graphviz) |
|---|---|---|---|---|
| **1** attributi semantici controllabili | ✅ totale | ❌ il PDF non può portarli (AD-10:271) | ⚠️ limitato | ⚠️ attributi applicati a valle |
| **2** determinismo byte per byte | ✅ per costruzione (AD-35) | ⚠️ dipende dall'ambiente LaTeX | ❌ matplotlib non lo garantisce | ❌ euristiche |
| **3** round-trip semantico | ✅ riparso ciò che ho emesso | ❌ non riparsabile in grafo | ⚠️ | ⚠️ |
| **4** layout controllabile per continuità | ✅ è l'unico modo di applicare un `LayoutPatch` | ⚠️ coordinate esplicite ma nessun patch | ❌ | ❌ **ricompone tutto: è il braccio 0** |
| **5** integrazione Studio/React senza raster | ✅ l'SVG è DOM | ❌ compilazione server + PDF | ⚠️ | ✅ |
| **6** `LayoutIR_k` vs `k+1` per VCER | ✅ (dipende dalla ritenzione, non dal renderer) | ❌ | ❌ | ❌ |
| **7** una sola pipeline semantica | ✅ AD-10: SVG sorgente unica | ❌ sarebbe la seconda | ❌ | ❌ |

**Il quarto punto della colonna «layout engine» è quello decisivo**: un motore che ricalcola il
layout da zero a ogni passo è la definizione del **braccio 0** dell'esperimento di Gate A, cioè il
termine di paragone che il prodotto deve battere. Usarlo come renderer significherebbe costruire il
braccio 0 e chiamarlo braccio A.

# Raccomandazione

**Generazione SVG semantica e deterministica scritta da noi**, in `render/serialize/`, con
`render/layout/` che applica il `LayoutPatch` e non ricompone (structural seed, AD-22).

**CircuiTikZ + pdflatex non è squalificato: cambia ruolo.** Non è il renderer, è un **formato di
export derivato dall'SVG verificato**, esattamente come AD-10 v2 prescrive. I vincoli d'ambiente
già misurati restano validi lì.

Non è una preferenza di gusto: è ciò che resta quando si applicano AD-10, AD-31 e AD-35 insieme.
Coincide con il default dichiarato dall'owner il 24/08 — *«generazione SVG deterministica
controllata da noi, non un renderer che ci nasconde il DOM»*.

**Costo onesto**: il pezzo difficile non è emettere SVG, è il **layout dei circuiti** — dove mettere
i componenti perché lo schema sia leggibile — e nessuna libreria ce lo regala senza portarsi dietro
il difetto del punto 4.

# CV6 — che cosa manca perché VCER sia misurabile

La preferenza dell'owner (`LayoutIR` immutabile e versionato per nodo, il precedente mai
sovrascritto) **non è ancora scritta da nessuna parte**. Verificato:

- `AD-8:229-238` nomina lo scrittore (`render/layout`) e **tace sulla ritenzione**.
- `Consistency Conventions:748` elenca i prefissi `ir_`, `sol_`, `var_`, `evt_` — **nessun `lay_`,
  nessun `patch_`**.
- `AD-21:452-454` dice che la `ProofSession` porta **gli identificatori dei quattro**, cioè *un*
  `LayoutIR`, non uno per nodo.
- L'ERD (`:776-789`) non conosce `LayoutIR`, `PROOF_GRAPH` né `LAYOUT_PATCH`.

Quattro righe, tutte dentro AD esistenti, e sono le stesse che CV6 aveva già indicato. Nessuna
retention policy alternativa esiste altrove: cercata e non trovata.

Finché non ci sono, **VCER non è calcolabile** e Gate A non ha un verdetto. Il percorso renderer
può iniziare — la scelta dello stack non dipende dalla ritenzione — ma **Gate A no**.

# D11 — compatibile, e più forte del previsto

> *«La costituzione dichiara esplicitamente di **non** decidere questo. Il loop lo traduce in un
> divieto operativo: non importare un simulatore, una memoria studente o una shell dentro
> Kirchhoff.»* **Blocca: Gate F.**

Il divieto è **su Kirchhoff che importa**, non su un prodotto che compone. Il grafo delle dipendenze
voluto dall'owner —

    CircuitCheck → Kirchhoff → infrastruttura di rendering condivisa

— è conforme, e D11 anzi lo protegge: è ciò che impedisce a Kirchhoff di trascinarsi dentro Studio o
Sim. Nessun conflitto. D11 blocca Gate F, non Gate A: non ferma questa spike.

# Una nota su D2, che avevo letto male

L'indice delle decisioni dice che D2 blocca «il catalogo delle trasformazioni». Il documento D2
dice **«Blocca: storia 2.9»** — il *profilo curricolare che restringe il catalogo*, non il catalogo
stesso. La Story 2.6 non è bloccata da D2. Il catalogo pedagogico portato nel dominio in `ad29c8e` è
una copia verificata della lista già chiusa e testata in `eval/`, non una scelta nuova.
