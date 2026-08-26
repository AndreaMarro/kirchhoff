---
tipo: meccanismo
implementato: 2026-08-14
codice: scripts/bmad_chain.py · tests/test_bmad_chain.py
---

# Tracciamento derivato dalle prove

## Il difetto che l'ha causato

Il 14 agosto il passo 2 della catena era chiuso alle **07:41** — `brief.md` a `version: 3`,
`addendum.md` con la sezione «H. Delta v3» — ma la tabella FASE 1 di `.claude/loop.md` mostrava
ancora `⬜`. **Una ripartenza avrebbe rifatto il lavoro da capo.**

La causa non è distrazione: lo stato viveva in una tabella Markdown che il loop doveva editare da
sé, e un passo che dipende dalla memoria di un contesto fresco è un passo che prima o poi salta.

## Il meccanismo

Lo stato sta in `bmad-chain-status.json`, lo scrive uno script, la tabella in `loop.md` è
**generata**. Ogni passo ha una **prova**: un artefatto che porta il suo timbro. Il confronto fra
dichiarato e provato fallisce in **entrambe** le direzioni:

| Dichiarato | Prove | Verdetto |
|---|---|---|
| `done` | assenti | ✗ dichiarato senza prova |
| ≠ `done` | presenti | ✗ **fatto e non tracciato** ← il difetto del 14 agosto |

La seconda riga è ciò che lo rende a prova di dimenticanza: **emerge anche se il comando di chiusura
non viene eseguito affatto**, perché `verifica` gira come primo comando di ogni iterazione.

## Perché è la forma giusta, misurata

Un giornale **append-only** sotto drift ottiene 0,210 di successo contro **0,309 di nessuna
memoria** — è peggio che ripartire da zero. La proprietà mancante è la **revoca**. E lo stato
aggiornato **solo da fatti verificati dall'ambiente** porta 51,8% → 80,7%.
Fonti in [[Automiglioramento, cosa è misurato]].

Questo tracciatore ha entrambe le proprietà: deriva dall'ambiente e si smentisce da sé.

## Il difetto che ha avuto lui

Vedi [[Il delimitatore iniettato]] — trovato e chiuso il giorno stesso.

← [[Catena BMAD v3]] · [[Lezioni sul loop]]
