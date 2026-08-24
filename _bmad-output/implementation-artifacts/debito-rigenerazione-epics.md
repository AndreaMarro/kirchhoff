---
title: 'Debito dichiarato — rigenerazione v2 di epics.md'
type: 'debt'
created: '2026-08-24'
baseline_commit: 'ef3017f'
status: 'open'
---

# Il debito

`_bmad-output/planning-artifacts/epics.md` è stato generato il 13 agosto 2026 dal passo 3 della
catena BMAD, sopra la **v1** dello spine (35 FR / 20 AD / 40 storie). Il 15 agosto lo spine è
stato emendato in v2: **dieci decisioni riscritte in loco senza rinumerazione** — AD-1, AD-2,
AD-4, AD-5, AD-8, AD-10, AD-11, AD-15, AD-18, AD-19 — più le nuove AD-21 e AD-22.

`epics.md` non è mai stato rigenerato. Cita quelle decisioni nel significato v1 in **circa 39
punti**. La misura non è mia: è nel `.memlog.md` dell'architettura, che la registra come
**domanda aperta**, non chiusa:

> *epics.md 1495 righe, 42 storie, costruito su 35 FR / 20 AD / 40 storie. `Drawing` (ritirato da
> AD-18) compare 4 volte, incluso il criterio di accettazione della Storia 2.6 (epics.md:584-586).
> […] Conclusione: il passo 6 è una RIGENERAZIONE, non un aggiornamento di conteggi.*

# Cosa è stato chiuso il 24/08/2026, e perché solo quello

Regola applicata, decisa dal proprietario: **coerenza locale completa sul percorso in esecuzione,
nessuna bonifica globale oggi.** Il percorso in esecuzione è 2.4 → 2.6.

| Punto | Azione | Motivo |
|---|---|---|
| Avviso di versione in testa a `epics.md` | aggiunto | rende impossibile scambiare il documento per l'autorità corrente |
| Inventario AD-2 | riallineato a v2 | è il contratto che la 2.6 implementa |
| Inventario AD-18 | riallineato a v2 (`Drawing` ritirato) | idem |
| Story 2.6 — intento | riscritto | chiedeva «una descrizione di disegno» |
| Story 2.6 — primo criterio di accettazione | riscritto | chiedeva letteralmente `(IR, Drawing)`: implementarlo avrebbe prodotto un contratto ritirato |
| Story 2.6 — criterio su AD-4 | esteso | AD-4 v2 lega il segnaposto allo scope del passo; la forma v1 era soddisfacibile senza soddisfare v2 |
| **Story 2.4** | **nessuna modifica** | verificata compatibile: cita FR-4 e AD-19, e AD-19 in v2 resta valido e si allarga con tre cause nuove emesse da `domain/transform/check`, che la 2.4 non usa |

Le annotazioni inserite portano il marcatore `[v2 · 24/08/2026]`.

# Cosa resta aperto

- I ~35 riferimenti v1 residui su AD-1, AD-5, AD-8, AD-10, AD-11, AD-15 negli Epic 3–7, che non
  stiamo eseguendo. Coperti dal solo avviso globale.
- `implementation-readiness.md` certifica «20 AD / 35 FR / 40 storie»: conteggi v1.
- L'espressione «cinque controlli» compare 8 volte in `epics.md` e 1 in
  `implementation-readiness.md`, ma **AD-5 in v2 ne enumera otto**. Tocca la Story 2.7, non la 2.6.
- Chiusura: rigenerare `epics.md` dal passo 6 della catena BMAD sopra lo spine v2, e verificare
  alla rigenerazione che il drift sia sparito e non ereditato.

# Ritrovamento collaterale, da non duplicare

`_bmad-output/planning-artifacts/ux-designs/ux-Kirchhoff-2026-08-13/` contiene già
**`EXPERIENCE.md` (40 KB)** e **`DESIGN.md` (28 KB)**, entrambi datati 15 agosto 2026 — la stessa
revisione della v2. `EXPERIENCE.md` ha sezioni per Foundation, Information Architecture, Voice and
Tone, Component Patterns (con «Il kernel — v3» e «Il percorso foto — Gate C»), State Patterns,
Interaction Primitives, Accessibility Floor, Responsive & Platform, vincoli della superficie
assistente, protocollo A/B di Gate A, Key Flows e domande aperte.

Qualunque lavoro di UI deve partire da lì. Le specifiche UX discusse in chat il 24 agosto vanno
**riconciliate** con questi due documenti prima di scrivere codice di interfaccia, non affiancate.
