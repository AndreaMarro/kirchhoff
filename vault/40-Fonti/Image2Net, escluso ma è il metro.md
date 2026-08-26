---
tipo: fonte
licenza: CC BY-NC-ND 4.0
stato: escluso dal corpus
---

# Image2Net — escluso, ma è il metro

*Image2Net: Datasets, Benchmark and Hybrid Framework to Convert Analog Circuit Diagrams into
Netlists* — arXiv 2508.13157.

**Doppiamente incompatibile:** `NC` (non commerciale) **e** `ND` (senza derivate). 2 914 immagini,
84 195 annotazioni, 104 coppie di netlist verificate a mano. **Fuori dal corpus.**

## Perché resta prezioso

È il **confronto pubblicato** contro cui misurarsi:

- **80,77%** di successo sul benchmark
- **0,116** NED medio

## La distinzione che conta

**NED** = *Netlist Edit Distance*, distanza di edit fra grafi normalizzata su dispositivi + net +
porte. Misura quanto il grafo ricostruito dista da quello vero — precisamente ciò che SER non vede.

> **Adottare la definizione di NED è legittimo: è una formula pubblicata, non un'opera coperta.
> Copiare il dataset no.**

NED entra fra le metriche nuove della [[Catena BMAD v3]]. La sua **soglia** no: è
[[D6 Soglie VVDR SER RRC di lancio]].

← [[Licenze verificate]]
