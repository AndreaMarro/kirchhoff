---
tipo: legge
id: K-1
---

# K-1 — I modelli propongono, i sistemi deterministici certificano

VLM e LLM possono proporre letture, trasformazioni, classificazioni, spiegazioni e suggerimenti.
**Non** attribuiscono lo stato `Verified` e **non** sono la fonte autorevole dei numeri finali
quando esiste un calcolo deterministico.

## Conseguenza operativa

Nessun `ModelPort` può: concedere `Verified` · mutare la verità canonica senza validator · inventare
quantità mancanti · dichiarare equivalente un sottografo senza un verifier che lo dimostri.

## Perché è anche una legge sul costo

Il gate deterministico costa **zero token**. Fuori dal prodotto, dentro il loop, vale lo stesso
principio: vedi [[Il gate scritto e non installato]] e [[Il costo fisso dell'iterazione]].

← [[Costituzione Kirchhoff]]
