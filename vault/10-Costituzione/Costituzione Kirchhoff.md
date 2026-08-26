---
tipo: sintesi
stato: owner-locked
fonte: ~/MATJOURNEY/kirchhoff/docs/02-costituzione-kirchhoff.md
versione: 1.0
data: 2026-08-14
---

# Costituzione Kirchhoff

**Il documento è `docs/02-costituzione-kirchhoff.md` ed è owner-locked: si legge, non si modifica.**
Questa nota è una mappa, non una copia.

## Perché esiste

Il piano master introduce un cambio di categoria — da *risolutore verificato* a **Verified Visual
Reasoning Engine** — che tocca dominio, architettura, UX, metriche ed epiche. Un cambio di quella
portata ha bisogno di un punto fermo che venga **prima** di PRD, spine e storie, e che non si muova
mentre tutto il resto viene riscritto.

> Ogni artefatto a valle vi si aggancia. Un artefatto che lo contraddice è **in errore, non in
> evoluzione**.

## Le cinque leggi

| | |
|---|---|
| [[K-0 Il circuito è il ragionamento]] | un passo senza disegno non è un passo |
| [[K-1 I modelli propongono, i sistemi certificano]] | nessun `ModelPort` concede `Verified` |
| [[K-2 Nessuna evidenza, nessuna affermazione]] | il claim è un tipo, non una frase |
| [[K-3 Il rifiuto è un output valido]] | il rifiuto è progettato, non è un errore di UX |
| [[K-4 La prova è ispezionabile]] | un badge che non si apre è un'affermazione |
| [[K-5 Nessun punteggio sulla persona]] | il tutor spiega l'errore, non valuta chi l'ha fatto |

## Cosa NON decide

Deliberatamente fuori: stack, ordine delle epiche, prezzi, provider di modelli, denominazione
commerciale, confine fra Kirchhoff core e Simulation Plugin di Ardesia — quest'ultimo è
[[D11 Confine Kirchhoff core e Ardesia Simulation]].

Sono decisioni di piano, e cambiano. Le cinque leggi no.

Vedi anche: [[Confini owner-locked]] · [[Catena BMAD v3]]
