---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# Fatto e non tracciato

**Meccanismo.** Lo stato di avanzamento vive in una tabella Markdown che l'agente deve editare da
sé. Un contesto fresco non ricorda di averlo fatto, e la tabella resta indietro rispetto al disco.

**Sintomo.** Il 14 agosto il passo 2 della [[Catena BMAD v3]] era chiuso alle 07:41 — `brief.md` a
`version: 3`, `addendum.md` §H, sei voci di memlog — e la tabella diceva ancora `⬜`. Una ripartenza
avrebbe **rifatto il lavoro da capo**.

**Gate.** `scripts/bmad_chain.py verifica` confronta il dichiarato con le **prove sul disco** e
fallisce in entrambe le direzioni. Gira come primo comando di ogni iterazione, quindi emerge anche
se il comando di chiusura non viene eseguito affatto. Vedi [[Tracciamento derivato dalle prove]].

**Perché la direzione «fatto e non tracciato» è quella che conta.** Un tracciatore che controlla solo
«dichiarato senza prova» impedisce di barare, ma non impedisce di **dimenticare** — ed è la
dimenticanza che costa il lavoro rifatto.

← [[Lezioni sul loop]]
