---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# Il delimitatore iniettato

**Meccanismo.** Il generatore stampa, dentro il blocco generato, una stringa che è anche il
**delimitatore di fine blocco**. La prima esecuzione riesce (il delimitatore non c'era ancora); la
seconda trova il delimitatore in mezzo al proprio output e tronca il file.

**Sintomo.** Il passo 8 della catena ha per prova l'esistenza dei marcatori in `loop.md`, e la
colonna «Prova» stampa il testo cercato. Dopo il primo `rendi`, `verifica --con-loop` ha detto
«tabella non allineata» pur avendo appena scritto la tabella.

**Gate.** Due, non uno:
1. la prova del passo 8 usa la sottostringa nuda `BMAD-CHAIN:START` — soddisfatta ugualmente,
   innocua da stampare;
2. `sostituisci_in_loop()` **rifiuta di scrivere** se la tabella generata contiene un marcatore più
   di una volta.

Il secondo è quello che conta: il primo evita *questo* caso, il secondo fa fallire ad alta voce la
prossima variante.

**La classe.** Difetti che si manifestano **solo alla seconda esecuzione**. Un test di idempotenza
li prende, un'esecuzione singola no — e il test di idempotenza esisteva già, ma girava su una
fixture in cui il passo 8 non era soddisfatto.

← [[Lezioni sul loop]]
