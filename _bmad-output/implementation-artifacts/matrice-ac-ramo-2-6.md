---
title: 'Matrice degli acceptance criteria — ramo loop/iter-20260824T211636Z'
type: 'escalation'
created: '2026-08-25'
verdetto: 'IL RAMO NON CHIUDE ALCUNA STORIA CORRENTE'
classe: 'R3 — la chiave della storia è una decisione di proprietà'
---

# Il ritrovamento che precede la matrice

La matrice doveva essere costruita contro «gli AC originali della Story». Costruendola
è emerso che **la Story 2.6 dell'`epics.md` corrente non è la storia che il ramo
implementa.**

    Story 2.6 (epics.md corrente)
    «Guidami» — la modalità che non rivela
    Autorità: FR-17 · KF-4 · K-5 — nessun punteggio, nessuna percentuale

Una storia di esperienza sulla modalità Studio. Nessun rapporto col catalogo delle
trasformazioni.

Non è una quarta denominazione dello stesso lavoro: sono **due storie diverse**. Il
ramo è stato costruito contro la numerazione **v1**, dove `2.6` era «il catalogo
delle trasformazioni e percorso B». Sotto la v2 quel numero è stato riassegnato.

Il rilievo 14 del Blind Hunter — *«il primo criterio della Story resta non
soddisfatto per un'applicabile su tre»* — era misurato contro il testo v1. Contro
l'`epics.md` corrente il divario è più grande e di natura diversa.

## Dove vive davvero questo lavoro

Ricerca per contenuto e non per numero: le storie correnti che nominano AD-2,
`TransformResult` o il catalogo sono **1.2**, **1.7** e **2.7**. Le prime due sono
le candidate reali.

---

# Matrice — Story 1.2: «Il vocabolario chiuso delle riscritture strutturali»

Il **Contesto** della storia enuncia il difetto da chiudere:

> il catalogo attuale nomina **passi didattici** — `serie`, `parallelo`, … — mentre
> `REMOVE_LOAD` o `ZERO_VOLTAGE_SOURCE` sono **sotto-passi**. Oggi
> `StructuralDerivation.operation` punta al catalogo pedagogico: **è il livello
> sbagliato**.

| AC | Prima | Dopo | Prova |
|---|---|---|---|
| **1.2-AC1** — dalla ricerca nasce un vocabolario chiuso **distinto dal catalogo pedagogico**, con un test che rifiuta ogni operazione fuori insieme | non soddisfatto | **non soddisfatto** | `PRIMITIVES` / vocabolario strutturale: **ASSENTE**. Esiste solo `CATALOG`, che è quello pedagogico (16 voci) |
| **1.2-AC2** — una trasformazione pedagogica composta da più riscritture porta **più** `StructuralDerivation`, e resta **un solo** passo pedagogico | non soddisfatto | **non soddisfatto** | `len(res.delta.derivations) == 1` per la serie; nessuna trasformazione composta esiste, e la capacità non è esercitata |
| **Contesto** — `StructuralDerivation.operation` non deve più puntare al livello pedagogico | difetto presente | **difetto presente** | `d.operation == 'serie'`, e `'serie' in CATALOG` è `True` |

**Verdetto 1.2: NON CHIUSA.** La riparazione non l'ha toccata, e non poteva: chiude
i quattordici rilievi del revisore, che riguardano la correttezza del contratto
esistente, non il livello a cui il vocabolario vive.

---

# Matrice — Story 1.7: «La prima trasformazione pedagogica, fino al disegno»

La storia dichiara il proprio criterio di completezza:

> **K-0 come criterio di accettazione:** la storia **non è completa** se produce solo
> `CircuitIR_before → CircuitIR_after`. Deve arrivare allo stato visuale verificato.

| AC | Prima | Dopo | Prova |
|---|---|---|---|
| **1.7-AC1** — il `TransformResult` porta `PreserveSet`, `Delta`, `Boundary`, `LayoutPatch`, `Equation`, `Certificate`, tutti non vuoti | soddisfatto | **soddisfatto** | sei membri presenti e non vuoti; `Boundary` si rifiuta di esistere vuoto per costruzione |
| **1.7-AC2** — il `Delta` contiene `{R1, R2} → {Req}` con lineage interrogabile **nelle due direzioni** | soddisfatto **a metà** | **soddisfatto** | prima `what_happened_to(node:b)` → `None`; ora la derivazione include il nodo assorbito, e `derived_from(Req) == (R1, R2, node:b)`. Chiuso da P0-A |
| **1.7-AC3** — nel disegno risultante ciò che appartiene a `preserve` **non si è mosso** (A-0) | non soddisfatto | **non soddisfabile** | `src/kirchhoff/render/` contiene solo `__init__.py`. Nessun renderer, nessun `LayoutIR`, nessun disegno |
| **1.7-AC4** — l'equazione compare **accanto** al sottografo, non sotto il disegno (UX-DR10) | non soddisfatto | **non soddisfabile** | idem. L'`Equation` ora nomina l'entità che definisce (P0-B), ma nessuno la dispone |
| **1.7-AC5** — il sottografo evidenziato compare **prima di qualunque testo** (UX-DR8) | non soddisfatto | **non soddisfabile** | idem |

**Verdetto 1.7: NON CHIUSA.** Due criteri su cinque sono soddisfatti, e i tre
mancanti richiedono il renderer — che è un'altra storia, non un residuo di questa.

---

# Che cosa il ramo ha davvero prodotto

Non «una Story completata». Un **contratto di dominio corretto e verificato**:

- il `TransformResult` attraversa otto controlli invece di cinque, e il `Certificate`
  li elenca tutti
- i tre canali — `CircuitIR`, `Delta`, `LayoutPatch` — non possono più raccontare
  storie diverse sulla stessa entità
- il `Boundary` è verificato nel contenuto
- gli errori del chiamante entrano dalle porte tipizzate che il contratto dichiara
- il vocabolario degli errori ha una fonte sola
- il registro è chiuso anche a runtime
- l'equazione nomina ciò che definisce
- 365 test, copertura 100%, recinti e dominio verdi

È lavoro buono e promuovibile **come contratto**. Non è la chiusura di una storia,
perché la storia contro cui è stato scritto non esiste più con quel numero.

---

# La decisione che serve

Non la prendo. Riguarda quale storia questo lavoro chiude, ed è la stessa famiglia
della migrazione `old-key → new-key` che hai deliberatamente rinviato.

Tre uscite, e nessuna è ovvia:

**A — il ramo è un contributo a 1.2 e 1.7, e nessuna delle due si chiude ora.**
Onesto, e lascia due storie aperte con lavoro dentro. Richiede che il ledger sappia
rappresentare «parzialmente implementata», che oggi non fa.

**B — nasce una storia nuova per il contratto di dominio**, di cui questo ramo è
l'implementazione completa, e 1.2 e 1.7 restano come sono. Il lavoro ha un contorno
netto — il contratto di `transform` e i suoi controlli — che nessuna delle due
storie descrive per intero.

**C — la migrazione del ledger viene prima**, e la chiave canonica di questo lavoro
si stabilisce lì. Coerente col fatto che il problema è nato dalla rinumerazione, ma
lega la promozione del ramo a una decisione più grande.

## Il vincolo che vale in tutte e tre

Hai scritto: *«la chiave canonica deriva programmaticamente dall'artefatto BMAD
corrente che possiede la Story; branch, journal, router e sprint ledger la
consumano»*. Oggi nessuno dei quattro la deriva: il ramo la porta nel nome, il
router la riceve come argomento, il ledger ne ha un'altra, l'epics una terza. Finché
resta così, questo ritrovamento si ripeterà alla prossima storia.
