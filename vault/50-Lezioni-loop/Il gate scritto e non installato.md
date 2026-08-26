---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# Il gate scritto e non installato

**Meccanismo.** Durante una review l'agente scrive un checker ad hoc per verificare un rilievo, lo
usa una volta, e non lo cabla in nessun punto che giri da solo. Il loop **genera i propri gate come
scarto della review e li butta.**

**Sintomo.** Registrato altrove: due checker scritti in una sessione — un validatore di blocchi YAML
e un verificatore di path — nessuno dei due installato.

**Il costo.** L'80% dei rilievi confermati da sei round di revisione avversariale era
**meccanicamente controllabile**. Una classe di difetto è ricomparsa **sessanta minuti** dopo essere
stata corretta a mano. Un round di revisione costa 20-40 minuti; uno script costa due secondi.

**Il rimedio, misurato.** Cablato in un job CI richiesto, un gate da quattro controlli — ognuno
derivato da un finding reale — ha riprodotto **due dei tre finding dell'ultimo round in meno di un
secondo**, su un documento già fuso.

**Gate.** §7 del loop: il gate si installa **nella stessa iterazione che l'ha scoperto**. Un checker
scritto e non cablato non esiste. E §4: il revisore non parte su un diff che i gate non hanno
approvato — `BLOCKED_BEFORE_REVIEW`.

← [[Lezioni sul loop]]
