---
istante: 20260826T212024Z
sha: 0fa9f653803bce5b01929eaac265af49b41cbe78
tipo: decisione-presa
decisore: loop (per delega del 26/08/2026)
questione: ordine della catena
---

# Estendere la catena: irrigidire prima di costruire

> Decisione presa dal loop **per delega**, non dal proprietario. E'
> reversibile: la sezione «Cosa la ribalterebbe» dice come.

## La decisione

Dopo 1.8 la catena prosegue con 1.5, 1.9, 1.6, poi l'Epic 2 (2.1-2.4). L'ordine cambia ragione: la priorita' «vedere il primo risultato nel browser» e' soddisfatta, quindi si irrigidisce cio' che esiste prima di costruirci sopra.

## La misura che la sostiene

Eseguita, non ragionata:

1.4 ha prodotto il primo SVG apribile (verificato in chromium, cinque controlli verdi); 1.8 la fetta visuale completa a 894 test; pipeline/ produce SVG e PDF da una netlist (partitore 12V su 100 e 220 ohm: 15/4 e 33/4 volt esatti, PDF di 23872 byte). 926 test, copertura 99.98%, zero righe scoperte. La catena era esaurita: kirchhoff-loop status diceva «catena esaurita dopo 1-8».

## Alternative scartate

- Andare dritti all'Epic 2 — scartata: pipeline/ e' un adapter nato senza il recinto di 1.5, e ogni storia che passa rende quel confine piu' caro da imporre.
- Mettere 1.6 prima di 1.5 — scartata: il round-trip riparsa cio' che gli adapter producono, e definire il confine dopo aver scritto il riparsatore significa scoprire il confine sbagliato.

## Cosa la ribalterebbe

Se il proprietario ha un'urgenza di prodotto sull'Epic 2 — per esempio una lezione vera da tenere — l'ordine si inverte e 1.5/1.9/1.6 diventano debito dichiarato invece che lavoro fatto. La catena e' DATO, non derivato: basta riscrivere il file.

## Archi

- [[Decisioni aperte]]
- [[00-INDICE]]
