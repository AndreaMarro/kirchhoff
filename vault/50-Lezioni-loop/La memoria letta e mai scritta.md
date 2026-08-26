---
tipo: lezione
formato: meccanismo · sintomo · gate
---

# La memoria letta e mai scritta

**Meccanismo.** Un file di stato viene **letto** dal codice che decide cosa fare, e **nessuno lo
scrive mai**. Il contatore vale sempre zero, la condizione non scatta, e il sistema si comporta come
se la memoria non esistesse — **ma sembra che esista**.

**Sintomo.** Registrato altrove: `ops/loop/compiti.py` legge `stato/compiti-tentati.json` alle righe
289 e 292; nessuno lo scrive. La memoria anti-treadmill non ha mai funzionato, e nessuno se n'era
accorto perché il codice che la consulta c'era.

**Gate.** Ogni file di stato deve avere **un test che lo scrive e lo rilegge**. Nel tracciatore
della catena è `test_lo_stato_riletto_e_quello_scritto`. Un lettore senza scrittore è un difetto,
non una feature non ancora usata.

**La classe.** È il modo peggiore di fallire per una memoria: **sembra funzionare**. Vale anche per
`~/.claude/skills/learned/`, creata l'11 agosto per raccogliere lezioni e ancora **vuota** — vedi
[[Skill eseguibili, non in prosa]].

← [[Lezioni sul loop]]
