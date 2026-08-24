---
title: 'Implementation Readiness — CircuitCheck / Kirchhoff'
version: 3
date: 2026-08-24
gate: CONCERNS
skill: bmad-sprint-planning (readiness)
baseline_commit: '84aaf50'
supersedes: "implementation-readiness v1 (13 ago 2026) — certificava 20 AD / 35 FR / 40 storie, conteggi dello spine v1"
---

# Verdetto: **CONCERNS**

Il piano è implementabile **quasi ovunque**, e non lo è nei due punti in cui inizia il percorso
critico. La domanda del gate è una sola — *«uno sviluppatore potrebbe implementare queste epiche
senza inventare decisioni che nessuno registra?»* — e per la maggior parte delle storie la risposta
è sì. Per `1.1` e `1.3` è **no**, e sono le prime due del percorso.

Nessuna delle correzioni richiede una ripianificazione: sono emendamenti puntuali ad AD esistenti,
più un artefatto di processo mai prodotto.

# Inventario degli artefatti

| Artefatto | Stato | Autorità |
|---|---|---|
| Costituzione K-0…K-5 | ✅ presente, **owner-locked** | prodotto |
| PRD v3 · 53 FR · 9 NFR | ✅ presente | requisiti |
| ARCHITECTURE-SPINE v2 · 35 AD | ✅ presente | architettura |
| UX v3 — `DESIGN.md` + `EXPERIENCE.md` | ✅ presente | esperienza |
| Review architetturali (CV1…CV7 e altre dieci lenti) | ✅ presenti | rilievi |
| `epics.md` v2 · 10 epiche · 64 storie | ✅ rigenerato oggi | backlog |
| `KIRCHHOFF-KNOWLEDGE` — decisioni aperte, lezioni del loop, fonti | ✅ presente | costituzione operativa |
| `sprint-status.yaml` · `bmad-chain-status.json` | ✅ presenti e coerenti | stato |
| **`project-context.md` / `AGENTS.md`** | ❌ **assenti** | — |

# Tracciabilità

**53 FR su 53** mappati a un'epica, verificato per confronto insiemistico. Nessun orfano in nessuna
delle due direzioni. Le epiche non hanno dipendenze in avanti; le storie sono completabili in
sequenza. Le decisioni di architettura e UX su cui le storie poggiano sono registrate — **tranne
dove indicato qui sotto**.

---

# I rilievi, per severità

## R1 — L'implementatore lavora a contesto fresco e non esiste un contesto di progetto — **bloccante**

`Loop Kirchhoff v3` consegna l'implementazione a *«un subagente senza contesto di conversazione»*, e
i `persistent_facts` del workflow puntano a `{project-root}/**/project-context.md`, che **non
esiste**. Non esiste nemmeno `AGENTS.md`, dove `bmad-project-context` v6.11.0 scriverebbe il proprio
blocco verificato.

Un agente nuovo, senza quel contesto, inventerebbe o ignorerebbe **almeno** questo:

- Kirchhoff è il motore, **CircuitCheck** è il prodotto — il nome del repository dice il primo
- **«Studio» collide**: la superficie B2B del docente (Epic 7, da costruire) contro
  `~/whiteboard-studio/studio`, l'app React esistente con 88 test — che **non va riscritta**
- il nome autoritativo è **`StudentTrace`** (FR-44), non `StudentSolutionIR`
- **illeggibile ≠ sbagliato**: è un criterio di sistema, non una preferenza di tono
- l'SVG semantico è **canonico**; CircuiTikZ è derivato
- **K-0**: un passo senza disegno non è un passo
- il **Rifiuto è un output valido** e non si dipinge di rosso
- **search-before-build**: questa sessione ha trovato sei volte una capacità già progettata meglio
- **holdout protetto**: `reference-set/holdout/` non si legge in sviluppo
- **niente autolayout generale** per Visual Slice 0
- il solver esiste: **non si riscrive**

**Chi lo chiude:** `bmad-project-context`. **Non a mano** — un markdown scritto da noi diventerebbe
stale come è diventato `epics.md` v1.

## R2 — `1.1` e `1.3` chiedono decisioni che nessun AD registra — **bloccante per quelle due storie**

**Story 1.1 — identità semantica.** AD-22 chiude una direzione sola. Cosa renda *«semanticamente
giustificata»* la conservazione di un'identità **non è definito da nessun AD**, e la forma
dell'attestazione nel `Certificate` non esiste. Uno sviluppatore inventerebbe la regola.

**Story 1.3 — ritenzione del `LayoutIR`.** CV6 nomina con precisione le quattro righe mancanti —
regola di ritenzione in AD-8, prefissi `lay_`/`patch_` nelle convenzioni, `ProofSession` con un
identificatore **per nodo**, ERD allineato — ma **nessuna è entrata nello spine**. Uno sviluppatore
inventerebbe la politica di persistenza dell'entità su cui Gate A emette il verdetto.

**Chi lo chiude:** `bmad-architecture (update)` per emendare AD-8, AD-21, AD-22 e le convenzioni.
Sono righe, non una riscrittura.

## R3 — Due artefatti correnti si contraddicono su FR-44 — **da risolvere, non da ereditare**

`prd.md` dichiara FR-44 *«Fuori MVP — Gate B»*. `epics.md` lo colloca nel percorso critico verso il
primo prodotto pubblicabile. Sono **entrambi correnti**, ed è esattamente il conflitto che il gate
impone di far emergere invece di risolvere in silenzio.

La direzione di prodotto è dichiarata: **senza `StudentTrace` e primo errore, CircuitCheck sarebbe
un risolutore visuale**, cioè non il prodotto da pubblicare. Due strade formalmente pulite:

- **A** — il readiness accetta formalmente la riprioritizzazione e la registra qui;
- **B** — `bmad-correct-course` emenda il PRD prima del build.

**B è la strada pulita**, perché lascia il PRD vero. **A senza B lascia due documenti che si
contraddicono.**

## R4 — Tre rilievi critici di review sono aperti e toccano Epic 1 — **rischio, non blocco**

**CV1** — la codifica di braccio non è tipizzata: un renderer potrebbe ricalcolare `preserve` come
complemento della classe «changed». Non tocca `1.4` (fixture senza bracci); tocca `1.7` e il
protocollo A/B. **CV2** — il test permanente di A-0 è falso per costruzione sui bracci B e C.
**CV3** — nessun predicato di occlusione esiste, e `overlay_occlusion` è una causa di `Refusal` che
**nessuno stadio solleva**: un tipo morto.

Nessuno blocca il percorso minimo. Tutti e tre bloccano il **verdetto** di Gate A.

## R5 — L'installazione `_bmad/` è parziale e il build non è mai stato provato — **bloccante per il loop**

Mancano `_bmad/scripts/resolve_customization.py` e `_bmad/bmm/config.yaml` che le skill v6.11.0
risolvono all'attivazione. Il fallback documentato ha retto per i passi 6 e 7. **Non è provato per
`bmad-build`.** È la Story 0.1, e va eseguita **prima** del primo build automatico — non scoperta
durante.

Tre esiti sono validi e nessuno va assunto in anticipo: **(A)** l'installazione renderizzata è
sufficiente; **(B)** mancano due helper di runtime; **(C)** serve una migrazione controllata.

## R6 — `D2` resta aperta — **contenuto, non bloccante**

Blocca la sola Story 4.6 (profilo curricolare), che non è sul percorso critico. `D5`, `D6`, `D9`,
`D10` restano aperte e non toccano l'implementazione. `D1` non blocca. **`D4` è risolta**, **`D11`
verificata compatibile**.

---

# Quali storie possono diventare `ready-for-dev`

| Storia | Verdetto | Perché |
|---|---|---|
| **0.1** preflight BMAD | ✅ **pronta** | è un'indagine con esito misurabile; non dipende da decisioni mancanti |
| 0.2 doctor · status · dry-run | ⏸ dopo 0.1 | l'esito di 0.1 determina cosa il CLI deve verificare |
| 0.3 run · resume | ⏸ dopo 0.2 | e dopo il confronto con il loop Ardesia, che è prerequisito dichiarato |
| **1.1** identità semantica | ⛔ **non pronta** | R2 — serve l'emendamento ad AD-22 |
| 1.2 vocabolario strutturale | ✅ **pronta** | comincia con search-before-build e la creazione è esplicitamente autorizzata |
| **1.3** ritenzione `LayoutIR` | ⛔ **non pronta** | R2 — servono le quattro righe di CV6 nello spine |
| 1.4 serializzatore SVG | ✅ **pronta** | AD-10, AD-31, AD-35 la registrano per intero; D4 risolta |
| 1.5 recinto `render→adapters` | ✅ pronta, dopo 1.4 | AD-21 la registra |
| 1.6 round-trip semantico | ✅ pronta, dopo 1.4 | FR-41, AD-31, AD-19 |
| 1.7 trasformazione `serie` | ⏸ | dipende da 1.1, 1.2, 1.3 |
| 1.8 Visual Slice 0 | ⏸ | dipende da 1.7 |
| 1.9 determinismo | ✅ pronta, dopo 1.4 | AD-35 |
| **2.1** `StudentTrace` | ⚠️ **con riserva** | FR-44 registra il *cosa*, non la forma. Gli stati di lettura sono un'invenzione di questo backlog: vanno registrati come decisione prima o dentro la storia |
| 2.2, 2.3 | ⏸ | dipendono da 2.1 e da R3 |
| 2.4 falsa accusa | ⏸ | dipende da 2.3 |
| 2.5, 2.6, 2.7 | ⏸ | dipendono dalle precedenti |
| Epic 3…10 | ⏸ | storie enumerate, da dettagliare all'ingresso in sprint |

**Quattro storie sono pronte adesso: `0.1`, `1.2`, `1.4`, `1.9`.** Nessuna di loro è la prima del
percorso critico, ed è il fatto più importante di questo gate.

---

# Il minimo per passare a PASS

1. `bmad-project-context` → chiude **R1**
2. `bmad-architecture (update)` su AD-8, AD-21, AD-22, convenzioni → chiude **R2**
3. `bmad-correct-course` sul PRD per FR-44 → chiude **R3**
4. Story 0.1 eseguita → chiude **R5**

**R4** e **R6** non bloccano il percorso minimo e restano registrati.

Nessuno dei quattro è una ripianificazione. Tre sono emendamenti, uno è un'indagine.
