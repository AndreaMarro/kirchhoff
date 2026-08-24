---
title: 'Sprint Change Proposal — FR-44 e la prima release rivolta allo studente'
date: 2026-08-24
skill: bmad-correct-course
scope: Moderate
baseline_commit: '6ba2643'
---

# 1. Sintesi del problema

**Due artefatti correnti si contraddicono.** `prd.md` v3 colloca `FR-44` (`StudentTrace`) **fuori
MVP, a Gate B**; `epics.md` v2, rigenerato il 24 agosto, lo mette nel **percorso critico** verso la
prima versione pubblicabile di CircuitCheck.

**Come è emerso.** Rilievo **R3** del readiness gate del 24 agosto, che impone di far emergere i
conflitti fra artefatti invece di risolverli in silenzio. Il gate ha restituito `CONCERNS` anche per
questo.

**Perché non è un errore di trascrizione.** `FR-44` porta una conseguenza testabile che è, alla
lettera, il meccanismo del primo errore:

> *«Un `StudentTrace` è confrontabile col `ProofGraph` di riferimento passo per passo, non solo sul
> risultato finale.»*

Il requisito del procedimento dello studente **era già nel PRD**. L'architettura non l'ha mai
implementato e la UX ha progettato «Guidami» e non «Correggi» — è `UX-GAP-01`. CircuitCheck non è
una deviazione dal progetto: è un requisito rimasto sospeso fra gli strati.

# 2. Analisi d'impatto

**Epic.** Epic 2 esiste per `FR-44` e `UX-GAP-01`. Nessun'altra epica cambia. Epic 1 resta la prova
di Gate A e **non richiede** `StudentTrace`.

**Storie.** Nessuna storia cambia di contenuto. Cambia l'eleggibilità di `2.1`, `2.2`, `2.3`, `2.5`,
oggi implicitamente rinviate dalla dicitura «fuori MVP».

**Artefatti in conflitto.** Solo `prd.md`, in due punti: la conseguenza di `FR-44` e l'elenco §7.2.
Lo spine non è toccato — `FR-44` non è citato da alcun AD. La UX non è toccata: il gap è già
registrato come tale.

**Impatto tecnico.** Nessuno. Nessuna riga di codice dipende da questa collocazione.

# 3. Approccio raccomandato — Direct Adjustment

**Non** si riscrive `FR-44`, e **non** lo si sposta in §7.1.

La regola del PRD è esplicita: *«Un FR assente da §7.1 è fuori MVP, comunque sia scritto qui»*, e
§7.1 è *«il Visual Proof Kernel, e nient'altro»*. Spostare `FR-44` lì significherebbe dire che il
kernel visuale ha bisogno del procedimento dello studente per essere provato — **falso**, e
contraddirebbe la decisione di far precedere Visual Slice 0.

Il difetto della formulazione attuale è un altro: **«fuori MVP» sta dicendo due cose insieme** —
«non serve a provare Gate A», che è vero, e «non serve alla prima cosa che pubblichiamo», che non lo
è più. La correzione separa le due.

| | Prova tecnica | Prima release rivolta allo studente |
|---|---|---|
| Cosa dimostra | il kernel visuale regge — Gate A | il prodotto corregge il tuo procedimento |
| Milestone | Visual Slice 0 | CircuitCheck Demo 0 |
| `FR-44` | **non richiesto** | **richiesto** |

Sforzo: due modifiche testuali. Rischio: basso. Impatto sulla scadenza: nessuno — l'ordine di lavoro
non cambia, cambia ciò che il documento dichiara.

# 4. Modifiche proposte

## 4.1 · `prd.md` — conseguenza di `FR-44`

**PRIMA**

```
- **Fuori MVP — Gate B** (tutor interattivo). Scritto qui perché l'addendum §H.4 lo impone come
  vincolo del verifier, e il verifier si costruisce adesso: accettare immagini dopo costerebbe una
  riscrittura del confine.
```

**DOPO**

```
- **Fuori dall'MVP di Gate A, richiesto dalla prima release rivolta allo studente.** Il Visual
  Proof Kernel si prova senza: Visual Slice 0 non ha bisogno di un procedimento da correggere.
  Ma la prima cosa che CircuitCheck pubblica **è** la correzione del procedimento, e senza questo
  requisito sarebbe un risolutore visuale — non il prodotto.
  *Provenienza:* fino al 24 agosto 2026 questa riga diceva «Fuori MVP — Gate B (tutor
  interattivo)». La riprioritizzazione è del 24 agosto, registrata in
  `sprint-change-proposal-2026-08-24.md`; il tutor interattivo e la lavagna restano a Gate B.
  Scritto qui perché l'addendum §H.4 lo impone come vincolo del verifier, e il verifier si
  costruisce adesso: accettare immagini dopo costerebbe una riscrittura del confine.
```

**Il resto di `FR-44` non è toccato.** Il significato tecnico — struttura semantica e non immagine,
confronto passo per passo col `ProofGraph` — resta parola per parola quello di prima.

## 4.2 · `prd.md` §7.2 — l'elenco degli esclusi

**PRIMA**

```
- **Tutor interattivo e lavagna** — Gate B. Con essi **FR-44** (`StudentTrace`), scritto ora perché
  vincola il confine del verifier che si costruisce adesso.
```

**DOPO**

```
- **Tutor interattivo e lavagna** — Gate B.
- **`StudentTrace` — FR-44.** Fuori dall'MVP di Gate A: il kernel visuale si prova senza. **Non**
  fuori dalla prima release rivolta allo studente, che è la correzione del procedimento e lo
  richiede. Separato dal tutor il 24 agosto 2026: erano nella stessa riga e condividevano un
  «Gate B» che per l'uno significa «dopo» e per l'altro «subito dopo Gate A».
```

## 4.3 · Nessuna modifica a §7.1

`FR-44` **non** entra fra i requisiti del Visual Proof Kernel. La regola *«un FR assente da §7.1 è
fuori MVP»* resta vera e non viene aggirata: ciò che cambia è che «fuori MVP» smette di significare
«non pianificato».

## 4.4 · Verificato e non modificato — il rifiuto invece della falsa accusa

Controllato se serva un requisito nuovo perché la prima release possa **astenersi** invece di
inventare un errore. **Non serve.** È già coperto:

- **`FR-12`** — il Rifiuto di certificazione è un esito **progettato**, non un fallimento;
- **`K-3`** — *«il rifiuto è un output valido»*, costituzione, owner-locked;
- **`AD-13`** — `Refusal` e `Failure` su tipi e canali diversi, e il Rifiuto **non consuma Crediti**.

La Story `2.4` (tasso di falsa accusa) resta il modo in cui lo si **misura**, e resta nella
Definition of Done pubblicabile di Epic 2 come già registrato in `epics.md`. Nessun FR aggiunto:
aggiungerne uno duplicherebbe tre requisiti esistenti.

# 5. Handoff

**Classificazione: Moderate.** Non è implementazione diretta — cambia la priorità di un requisito e
riorganizza l'eleggibilità di quattro storie. Non è Major: nessuna ripianificazione, nessun AD
toccato, nessuna epica ridefinita.

**Destinatari.** Il gate di readiness, che dovrà verificare al rerun che il conflitto R3 sia
effettivamente chiuso — non io, che l'ho scritto.

**Criteri di successo.** `prd.md` ed `epics.md` non si contraddicono più su `FR-44` · il significato
tecnico di `FR-44` è invariato · la formulazione precedente resta leggibile come provenienza ·
Visual Slice 0 resta possibile senza `StudentTrace`.
