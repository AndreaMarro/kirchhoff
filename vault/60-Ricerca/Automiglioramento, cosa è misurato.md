---
tipo: ricerca
fonte: docs/04-ricerca-token-e-automiglioramento.md §3
stato: recuperata da ~/ARDESIA-KNOWLEDGE/50-Research/
---

# Automiglioramento — cosa è misurato

La sintesi che conta, con l'unica colonna che discrimina: **il meccanismo è ancorato a un segnale
esterno, oppure no?**

| meccanismo | ancorato? | esito misurato |
|---|---|---|
| giornale **append-only** sotto drift | no | **0,210 vs 0,309 senza memoria** |
| «aggiungi tutto» | no | **−3,7…−12,1 pp su 4 agenti su 4** |
| agente che riscrive le proprie lezioni | no | **18 282 → 122 token, −9,6 pp** |
| auto-correzione intrinseca | no | **peggiora** |
| auto-memoria vs RAG verbatim | no | 42,0% vs 47,2% |
| **cancello di qualità in scrittura** | **sì** | **+25,45 pp** |
| stato aggiornato **solo da fatti verificati dall'ambiente** | **sì** | **51,8% → 80,7%** |
| **skill programmatiche eseguibili** | **sì** | **+11,3 pt** sopra la prosa |

## La riga che ribalta il senso comune

**Un giornale che solo aggiunge è peggio di nessuna memoria** — 0,210 contro 0,309, cioè il 32,1%
in meno che non ricordare nulla. La proprietà mancante non è la capacità: è la **revoca**.

È il motivo per cui `bmad-chain-status.json` **non** è un log: si ricalcola dalle prove sul disco e
può smentire sé stesso. Vedi [[Tracciamento derivato dalle prove]].

## Le tre conseguenze già applicate al loop

- il cancello in scrittura conta più della memoria → [[Il gate scritto e non installato]]
- le skill devono essere eseguibili → [[Skill eseguibili, non in prosa]]
- il giudice va misurato prima del generatore → [[Il refutatore è un imputato]]

## Il flywheel che ha funzionato, col suo numero

`mechanical_share = finding_meccanici / finding_totali`, **baseline 0,80, deve scendere**. Dichiarata
dagli autori stessi come baseline di **una** sessione su **tre** PR: «non è una legge; è il punto di
partenza contro cui misurare la prossima».

← [[00-INDICE]] · [[Lezioni sul loop]] · [[Cosa non è stato trovato]]
