---
tipo: lezione
stato: misurata
prima-volta: 2026-08-26
---

# I backtick in `-m` li esegue la shell

`git commit -m "... `pippo` ..."` non scrive `pippo` fra backtick: la shell esegue
`pippo` come comando **prima** che git veda la stringa, e sostituisce la sua uscita.
Se il comando non esiste, l'uscita e' vuota e la parola sparisce dal commit. Nessun
errore ferma il commit: git riceve una stringa gia' mutilata e la scrive.

## Due misure, e la seconda vale piu' della prima

**26/08/2026, mattina.** Un messaggio di merge conteneva `` `--promuovi` ``. Il
commit e' andato a buon fine e la parola non c'era.

**26/08/2026, sera.** Scrivendo il commit che *documentava questa regola*, il
messaggio conteneva `` `-m` ``. La shell ha stampato `command not found: -m`, il
commit e' passato lo stesso, e il testo finale dice:

> «backtick in  li esegue la shell»

Il commit che spiega il difetto e' stato mangiato dal difetto che spiega. Era gia'
pubblicato quando me ne sono accorto, e riscrivere la storia per nasconderlo sarebbe
stato peggio del difetto.

## La regola

**Il messaggio di commit va in un FILE.**

```bash
git commit -F /tmp/messaggio.txt
git merge --no-ff <ramo> -F /tmp/messaggio.txt
```

Un heredoc quotato (`<<'FINE'`) e' sicuro, perche' le virgolette singole
disattivano l'espansione. Un heredoc NON quotato (`<<FINE`) non lo e'.

## Perche' e' insidioso

Non produce un errore che ferma qualcosa. Produce un commit **valido** e un testo
**sbagliato**, e la differenza si vede solo rileggendo. E chi rilegge un messaggio
di commit appena scritto? Nessuno: e' il momento in cui si e' piu' sicuri di sapere
cosa c'e' scritto.

## Archi

- [[Lezioni sul loop]]
- [[00-INDICE]]
