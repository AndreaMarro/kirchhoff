---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# FIFO-greedy sotterra le task critiche

**Meccanismo.** Nella fabbrica ARDESIA: `bin/replenish.sh` invoca lo strategist quando il backlog
`[AUTO-OK]` scende sotto 2 e **inserisce le righe nuove in testa**; `bin/promote_pin.py` pesca la
**prima** riga in FIFO-greedy, **senza funzione di valore**.

**Sintomo.** Ogni build drena il backlog sotto 2 → lo strategist inserisce task-mirror a basso
valore in testa → **le task critiche curate vengono sepolte entro un ciclo** e mai promosse.

**Gate.** Nel loop Kirchhoff, §2: **non prendere la prima riga della lista**. Si sceglie il collo di
bottiglia a rischio più alto fra ciò che è sbloccato, e si scrive nel riepilogo **perché**. La
funzione di valore è esplicita: (1) ciò che blocca il kill criterion di Gate A, (2) un difetto che
invalida misure già prese, (3) un vincolo owner-locked non ancora tradotto in gate, (4) la sequenza.

**Fonte.** `~/.claude/skills/ardesia-curate-factory/SKILL.md` — è il modello di cosa deve essere una
skill: un meccanismo di fallimento col suo rimedio, ancora utile mesi dopo.

← [[Lezioni sul loop]]
