---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# Skill eseguibili, non in prosa

**Meccanismo.** «Scrivi la lezione da qualche parte» sembra sufficiente. Non lo è: la **forma**
decide se la lezione sopravvive.

**I numeri.**
- Le skill **eseguibili** battono quelle in prosa di **11,3 punti** a parità di tutto il resto
  (ASI, arXiv 2504.06821 — isola esattamente questa variabile).
- Un file di lezioni che l'agente **riscrive** collassa: **18 282 token → 122 in un solo passo**,
  accuratezza dal 66,7% al 57,1%, cioè **sotto il baseline** (ACE, ICLR 2026).
- Con 34 000 skill reali da cui recuperare, «i benefici delle skill sono **fragili** […] con tassi
  di successo che si avvicinano al baseline senza skill» (arXiv 2604.04323).

**Sintomo locale.** `~/.claude/skills/learned/` è stata creata l'11 agosto alle 19:31 per raccogliere
le lezioni del loop. **È vuota.** In tre giorni il meccanismo non ha prodotto un solo artefatto.

**Gate.** Ordine di preferenza, dal più durevole: (1) un test o un controllo di script; (2) una
prova nella `CATENA` di `bmad_chain.py`; (3) una skill in prosa, **solo** se la lezione non è
esprimibile come codice.

**Nota di coerenza.** Il punto 1 dell'automiglioramento — «ogni escaped failure diventa una fix
**più** un test di regressione» — era già la forma giusta: è una skill eseguibile scritta come test.
Vedi [[La memoria letta e mai scritta]].

← [[Lezioni sul loop]]
