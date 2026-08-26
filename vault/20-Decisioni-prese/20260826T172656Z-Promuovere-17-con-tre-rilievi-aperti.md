---
istante: 20260826T172656Z
sha: d1f04aa3d3c4061a0b514a84ea78f7e8976dd3ea
tipo: decisione-presa
decisore: loop (per delega del 26/08/2026)
questione: 1.7
---

# Promuovere 1.7 con tre rilievi aperti

> Decisione presa dal loop **per delega**, non dal proprietario. E'
> reversibile: la sezione «Cosa la ribalterebbe» dice come.

## La decisione

1.7 sale su main con i tre rilievi della ri-revisione registrati e non chiusi.

## La misura che la sostiene

Eseguita, non ragionata:

799 test, copertura 100%, recinti e dominio verdi. I tre rilievi verificati per esecuzione: annota() ha zero chiamanti in src/ (grep sulle sole chiamate); pipeline/, api/ e adapters/ erano gia' vuoti su main prima della storia (git show main:, 0 righe ciascuno); aggiungere le guardie mancanti a TransformOverlay rende rossi quattro test esistenti.

## Alternative scartate

- Trattenere 1.7 finche' il punto di composizione non esiste — scartata: il buco precede la storia e i suoi AC non chiedono di chiuderlo.
- Chiudere il rilievo 2 aggiungendo le guardie — TENTATA e ritirata: rompe quattro test che costruiscono l'overlay cosi' di proposito.

## Cosa la ribalterebbe

Se una storia successiva definisce dove vive il punto di composizione del prodotto, il rilievo 3 va chiuso li' e questa nota diventa la sua motivazione. Se il proprietario decide che TransformOverlay e' un oggetto stretto derivato dal prodotto, il rilievo 2 si chiude e i quattro test vanno riscritti.

## Archi

- [[Decisioni aperte]]
- [[00-INDICE]]
