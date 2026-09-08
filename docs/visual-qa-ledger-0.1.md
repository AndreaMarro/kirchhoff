# Quaderno visuale — Proof Workbench 0.1 (2026-09-07, Chromium 1228, build prod)

Viewport: 1440×900, 768×1024, 390×844. Ogni voce: AREA / ATTEso / OSSERVATO /
FIX / STATO. Niente "sembra buono": solo fatti misurati o visti.

## 1. Tipografia
- ATTESO: tornitura editoriale, mono tabulare per le quantità, mai default browser.
- OSSERVATO: Inter/system + JetBrains Mono; 3/80 A in mono 28px tabulare;
  decimali secondari; bottoni senza font di default.
- FIX: nessuno.
- STATO: ok.

## 2. Spaziatura e gerarchia
- ATTESO: circuito eroe, rotaia 200–240px, ispettore 320–380px, scala 4px.
- OSSERVATO: 224/1fr/344 a 1440px; il circuito domina; a 768px l'ispettore
  va sotto in griglia; a 390px tutto in colonna.
- FIX: nessuno.
- STATO: ok.

## 3. Scala del circuito
- ATTESO: leggibile senza assunzioni desktop, max 62dvh desktop / 46dvh mobile.
- OSSERVATO: partitore, scala e ponte riempiono il palco senza ritagli;
  etichette 11px leggibili; ponte planare senza incroci.
- FIX: nessuno.
- STATO: ok.

## 4. Rotaia della dimostrazione
- ATTESO: sempre visibile, voci con azione + equazione, corrente marcata.
- OSSERVATO: Apertura + passi numerati; equazioni lunghe troncate con
  ellipsis (testo intero nell'ispettore); `aria-current` sullo step.
- FIX: ellipsis CSS sulle sub dei passi (erano 7 righe per le KCL).
- STATO: ok.

## 5. Prima/Dopo
- ATTESO: confronto istantaneo, preservati fermi in px fra i fotogrammi.
- OSSERVATO: E2E misura il centro del nodo `b` prima/dopo: <2px (identico
  a meno di arrotondamento); stessa scala via viewport unita.
- FIX: nessuno (il test `il preservato non si teletrasporta` lo inchioda).
- STATO: ok.

## 6. Risposta esatta
- ATTESO: esatto primario, decimale secondario, mai float in JS.
- OSSERVATO: `3/80 ampere` 28px + `≈ 0.0375 ampere · corrente di R1`;
  decimali formattati in Python; sempre visibile anche nella barra.
- FIX: nessuno.
- STATO: ok.

## 7. Colori semantici
- ATTESO: 90% neutri, 10% significato; mai solo-colore; temi entrambi credibili.
- OSSERVATO: verified/sospeso/guasto solo su pill/badge/risposta; ogni stato
  ha icona+parola; light alternativo verificato a 1440px senza colori grezzi.
- FIX: nessuno.
- STATO: ok.

## 8. Evidenza dell'entità
- ATTESO: click su entità → evidenziata + contestualizzata; tastiera equivalente.
- OSSERVATO: click su R1 seleziona ed evidenzia (dim 0.42 sul resto,
  equazione leggibile); R1R2eq in Prima non oscura (appare in Dopo);
  lista bottoni anche in apertura con risposta sul bersaglio.
- FIX: annotazioni overlay click-through; fallback di prossimità 16px
  (i tratti sottili non si colpiscono al centro del riquadro);
  niente oscuramento a zero match; equazione esclusa dall'oscuramento.
- STATO: ok.

## 9. Mobile 390px
- ATTESO: niente scroll orizzontale, flusso a una mano, target ≥44px.
- OSSERVATO: overflow pagina 48px → 0 (min-width nei flex/grid + barra
  avvolgibile); 0 target <44px (misurato); chip→passo→dopo→risposta
  completabile; rotaia orizzontale, controlli fissi in basso.
- FIX: vedi sopra.
- STATO: ok.

## 10. Stati di fuoco
- ATTESO: fuoco sempre visibile da tastiera.
- OSSERVATO: Tab mostra `:focus-visible` con anello (box-shadow misurato
  ≠ none in E2E); tutti i controlli sono bottoni nativi o details.
- FIX: nessuno.
- STATO: ok.

## 11. Rifiuto e guasto
- ATTESO: «Non certificata» deliberata (ambra, diagnosi, niente risposta);
  guasto rosso e distinto; mai stack trace.
- OSSERVATO: rifiuto reattivo con diagnosi verbatim e Controllo/Soggetto;
  pill ambra in barra; nessun numero inventato; nessun Product Verified.
- FIX: nessuno.
- STATO: ok.

## 12. Apertura
- ATTESO: il primo fotogramma non rivela l'equazione (BEFORE poi ACTION).
- OSSERVATO: apertura resa senza overlay; equazione solo col passo
  selezionato; didascalia breve (la `<desc>` lunga resta nel byte per AT).
- FIX: didascalia breve al posto della descrizione topologica intera.
- STATO: ok.

## 13. Contrasto
- ATTESO: AA sul testo principale, entrambi i temi.
- OSSERVATO: rapporto risposta/sfondo misurato in E2E ≥4.5 (dark);
  light ispezionato: inchiostri scuri su superfici chiare, pill leggibili.
- FIX: nessuno.
- STATO: ok (dark misurato, light ispezionato).

## 14. Moto ridotto
- ATTESO: semantica intatta, durate nulle con prefers-reduced-motion.
- OSSERVATO: `--kf-motion-quick: 0ms` con reduce; flusso prima/dopo
  integro; E2E dedicato verde.
- FIX: nessuno.
- STATO: ok.

## 15. Difetti noti aperti (renderer, non frontend)
- Etichetta valore parzialmente sotto il riquadro di enfasi sui simboli
  piccoli (R1/100 ohm, R1R2eq/320 ohm): geometria del renderer, byte
  certificati intatti, leggibile. Non corretto qui (sarebbe mentire col CSS).
- STATO: aperto, proprietario renderer, fuori ambito 0.1.

Schermate: `docs/img/workbench-desktop.png`, `workbench-mobile.png`,
`workbench-rifiuto.png`. Le schermate integrano le asserzioni E2E, non le
sostituiscono (niente baseline pixel: il raster dei font varia per macchina).
