# Il cancello visuale

La suite verifica che `render` emetta certi byte e che quei byte siano XML ben
formato. **Nessuno verificava che un browser, ricevendoli, disegni qualcosa.**

Un SVG può essere valido, deterministico e semanticamente annotato — e non
dipingere un pixel, perché il `viewBox` esclude il contenuto o perché ogni tratto
è largo zero. Sono difetti che la riparsatura della Story 1.6 non vedrebbe: lei
rilegge la struttura, non l'immagine.

```bash
node ops/vista/gate.mjs tests/golden/story-1-4-fixture.svg
```

Esce 0 se tutti e cinque i controlli passano:

| controllo | cosa cattura |
|---|---|
| riquadro non degenere | un `viewBox` che collassa |
| nessun elemento fuori dal riquadro | contenuto disegnato dove nessuno lo vede |
| attributi semantici interrogabili | annotazioni presenti nel testo ma non nel DOM |
| ruolo, titolo e descrizione risolvibili | `aria-describedby` che punta a un id assente |
| dipinge pixel non bianchi | un disegno che non disegna |

## Cosa NON copre, misurato

Con `stroke-width="0"` sulla radice tutti i fili spariscono e **il gate resta
verde**: pallini ed etichette hanno un `fill` proprio e continuano a dipingere 627
pixel, sopra la soglia. Cattura «non disegna niente», non «disegna metà».

Una soglia calibrata su un riferimento lo coprirebbe, al prezzo di un cancello che
diventa rosso a ogni ritocco legittimo del disegno — e un cancello che grida
sempre viene spento. Dichiararlo qui vale più che lasciar credere che copra tutto.

## Il browser

Si prende da quelli già installati sotto `~/Library/Caches/ms-playwright`. Se non
ce n'è nessuno, il gate esce **69** e dice come installarne uno: un cancello che
dipende da un download è un cancello che un giorno non gira.
