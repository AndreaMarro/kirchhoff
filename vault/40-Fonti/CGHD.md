---
tipo: fonte
licenza: CC-BY-4.0
stato: usabile
---

# CGHD

*A Public Ground-Truth Dataset for Handwritten Circuit Diagram Images* — DFKI.

- **3 173 immagini** annotate di circuiti disegnati a mano
- 32 disegnatori · 12 circuiti ciascuno · 2 disegni per circuito · **4 fotografie per disegno**
- 245 962 bounding box · 39 955 annotazioni di rotazione · 84 431 stringhe di testo
- Netlist ASC **solo per una parte** — copertura non dichiarata nel paper
- 4,4 GB · https://zenodo.org/records/14042961

## Cosa risolve

Toglie interamente il costo di **raccolta** del gold set fotografico. Sono fotografie, non
scansioni: è la classe più difficile della stratificazione prevista dal piano.

## Cosa non risolve

Niente soluzione dell'esercizio, niente IR completo. Resta da annotare a mano un sottoinsieme —
**un pomeriggio per 30-40 immagini, contro le due settimane di una campagna di raccolta.**

## Il numero da non fraintendere

Il baseline pubblicato su CGHD per la **sola rilevazione dei simboli** è **18% mAP** (Faster R-CNN +
ResNet-152, arXiv 2402.11093). È un rilevatore addestrato apposta, e va male. **Non è la stessa
metrica di un VLM frontier end-to-end** e non va citato come se lo fosse. Vale come indizio che il
compito è difficile, non come misura di una baseline saltata.

← [[Licenze verificate]] · complementare a [[Digitize-HCD]]
