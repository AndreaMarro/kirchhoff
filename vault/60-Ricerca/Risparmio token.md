---
tipo: ricerca
fonte: ~/MATJOURNEY/kirchhoff/docs/04-ricerca-token-e-automiglioramento.md §2
stato: recuperata, non rifatta
---

# Risparmio token

Il documento completo con tutte le fonti è `docs/04-ricerca-token-e-automiglioramento.md`. Qui i
quattro fatti che cambiano un comando.

## 1. Le letture sono il 76,1% del consumo

E il costo cresce **col quadrato** del numero di turni, perché ogni turno rispedisce il prefisso. Il
prompt caching lo rende ~10× più economico ma **resta quadratico**. Solo due cose cambiano
l'esponente invece della costante: **limitare la finestra rispedita** e **tenere i risultati grossi
fuori dal contesto**.

## 2. Il costo fisso si taglia 3,3×

Vedi [[Il costo fisso dell'iterazione]] — con la sua trappola.

## 3. La cache si rompe in silenzio

Ogni breakpoint cammina indietro **al massimo 20 blocchi di contenuto**. Un turno con molte coppie
`tool_use`/`tool_result` lo supera, il breakpoint successivo non trova nulla, e **non c'è nessun
errore**. Sintomo: `cache_read_input_tokens` a zero su turni ripetuti.

## 4. Il segnale di stop viene da fuori

Misurato: i modelli prevedono **oltre il 70% di fattibilità dopo aver bruciato il 60% del budget**;
correlazione fra bravura nel compito e stima del budget residuo **r ≈ 0,35**. L'arresto precoce
risparmia il **28-64% dei token** sui tentativi falliti per **1,6-4,2 punti** di successo.

> Sapere *se* fallirai è apprendibile; sapere *quanto* costerà ancora, no.

## Un numero ritirato, e va detto

«Il contesto ri-inviato è il 62% del conto» è stato **ritirato** dalla fonte stessa:
`input_tokens` è soltanto il resto non cachato, il totale è
`input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. Stato:
`RITIRATO_IN_ATTESA_DI_RIMISURA`, **non** `FALSIFICATO`. Il 76,1% e la crescita quadratica
sopravvivono.

## La leva dell'effort — decisa il 15 agosto

Era l'unica voce lasciata aperta. Owner: *«dipende se vogliamo usare agenti, se no Opus 5 Max»*.

| Chi | Modello · effort |
|---|---|
| loop principale — sceglie, costruisce, decide | **Opus 5, effort max** |
| sottoagenti che **giudicano** | effort alto |
| sottoagenti **meccanici** (ricerca, inventario, conteggio) | effort basso |

**L'effort si abbassa solo su chi non giudica.** Senza delega non si abbassa niente. La ragione non
è prudenza generica: la verifica indipendente è ciò che il prodotto vende, vedi
[[K-1 I modelli propongono, i sistemi certificano]] e [[Il revisore che rivede sé stesso]].

← [[00-INDICE]] · [[Il costo fisso dell'iterazione]] · [[Cosa non è stato trovato]]
