---
title: 'Audit UX — quanto di CircuitCheck era già progettato'
type: 'audit'
created: '2026-08-24'
baseline_commit: '839163b'
fonte: 'ux-Kirchhoff-2026-08-13/EXPERIENCE.md (616 righe) e DESIGN.md (539 righe), letti integralmente'
---

# La risposta alla domanda centrale

**Sì, era CircuitCheck. Poi il 15 agosto è stato deliberatamente messo da parte.**

`EXPERIENCE.md` dichiara in frontmatter:

> `supersedes: "EXPERIENCE v2 (13 ago 2026) — prodotto centrato sull'Anteprima di ricostruzione da foto"`

e spiega:

> *La v2 aveva un centro: **l'Anteprima di ricostruzione**, il confronto fra la foto dello studente e
> l'IR ricostruito, e le riceveva il budget di design più alto. In v3 quel centro **non esiste
> nell'MVP**: l'ingresso è strutturato e non c'è nessuna foto da confrontare. Il nuovo centro è
> **il passo** … Non è una revoca dell'Anteprima: torna intatta a Gate C, che ora corre in parallelo.*

Quindi tre stati, non uno:

| | Prodotto | Rapporto con CircuitCheck |
|---|---|---|
| **UX v2**, 13 ago | percorso foto → Anteprima → conferma → Soluzione verificata | **è il percorso foto di CircuitCheck**, progettato per intero |
| **UX v3**, 15 ago | `ProofSession`: ingresso strutturato, il passo come centro, `ProofGraph` percorribile | è il **motore visuale** di CircuitCheck, senza l'ingresso |
| **mai progettato** | correzione del **procedimento dello studente** | **è la USP, e non c'è in nessuna delle due** |

Il percorso foto non è stato cancellato: è stato **spostato a Gate C**, in parallelo. I sette flussi
KF-1…KF-7 restano validi e *«cominciano tutti da una foto»*.

**Ciò che non esiste in nessuna versione** è il caricamento dello svolgimento dello studente.
KF-4 («Sara studia invece di copiare») è la modalità Studio: il sistema chiede, lo studente risponde
**dentro** il sistema. È «Guidami», non «Correggi». Nessun flusso prende un foglio già scritto.

# Matrice

Legenda: **KEEP** già migliore o equivalente · **EXTEND** buono ma manca il pezzo CircuitCheck ·
**REPLACE** in conflitto · **NEW** non esiste · **DROP** non più utile.

## Ingresso

| Requisito | Design esistente | Stato | Cosa cambia |
|---|---|---|---|
| landing immediata | landing esiste solo per i docenti (UJ-6); le superfici pre-Gate A **escludono** le pubbliche | **NEW** | serve una landing di prodotto con prova in un click |
| prova senza account | *«Apre da mobile web, non autenticato»* · *«nessun incasso prima del verdetto»* · l'account si propone **dopo** la prima Soluzione | **KEEP** | nulla |
| foto del circuito | KF-1 completo, Anteprima a due viste | **KEEP** | riportarlo nell'MVP |
| **foto del procedimento** | — | **NEW** | è la USP |
| PDF in ingresso | previsto solo in uscita | **NEW** | — |
| più pagine | non previsto | **NEW** | — |
| camera mobile | mobile-first, *«scatta la foto storta di un esercizio manoscritto»* | **KEEP** | nulla |

## Percezione

| Requisito | Design esistente | Stato |
|---|---|---|
| source view + canonical | Anteprima: *«la sua foto a sinistra, la ricostruzione a destra»* | **KEEP** |
| provenance bidirezionale | `provenance-anchor`; *«il legame è bidirezionale, perché l'utente può partire da entrambi i lati»* | **KEEP** |
| confidence leggibile | Voice §2: *«Non sono sicuro del valore di R8»*, mai «rilevata possibile ambiguità» | **KEEP** — già come volevi, in prima persona e con l'oggetto |
| confirmation gate | stato *Attesa di conferma*: *«terminale finché l'utente non agisce. Nessun timeout, nessun auto-avanzamento»* | **KEEP** |
| correzione OCR e topologia | editor: *«valori, tipi, collegamenti, polarità»*; *«ogni modifica manuale resta marcata come tale nell'IR»* | **KEEP** |
| tetto alle domande | **massimo due giri, contatore visibile**, poi degrado all'editor | **KEEP** — non l'avevi chiesto ed è migliore |

## Lavoro dello studente — il buco

| Requisito | Design esistente | Stato |
|---|---|---|
| trascrizione del procedimento | — | **NEW** |
| ritaglio originale ↔ passo | la primitiva esiste (`provenance-anchor`), il referente no | **EXTEND** |
| passo editabile | esiste l'editor del **circuito**, non del procedimento | **EXTEND** |
| ambiguo ≠ sbagliato | esiste nella forma *Non certificata ≠ Guasto*, con colore, icona e parole distinti | **EXTEND** — la forma c'è, va portata sul passo dello studente |
| metodi alternativi validi | — | **NEW** |

## Correzione

| Requisito | Design esistente | Stato |
|---|---|---|
| primo errore | — | **NEW** |
| fermarsi al primo | — | **NEW** |
| mostrare tutti, opzionale | — | **NEW** |
| certezza dell'errore | `badge-suspended`, mai rosso | **EXTEND** |
| localizzare l'errore sul circuito | `subgraph-highlight` è esattamente il meccanismo | **EXTEND** — cambia solo cosa si evidenzia |
| risultato giusto per ragionamento sbagliato | — | **NEW** |

## Lavagna — qui il design esistente vince

| Requisito | Design esistente | Stato |
|---|---|---|
| circuito protagonista | *«`C₀` occupa quasi tutta la superficie utile … ha un costo in pixel che va pagato»* | **KEEP** |
| rivelazione progressiva | ordine di comparsa: sottografo → azione → equazione → certificato. *«Nessun passo si apre con un paragrafo»* | **KEEP** |
| replay | `proofgraph-rail`: *«non è una barra di avanzamento … il rail si usa»* | **KEEP** |
| before / action / after | i **sei campi** di FR-39: `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE · PROVENANCE` | **KEEP** — più completo di quanto avevo proposto |
| continuità visuale | **A-0**: *«un'entità preservata non riceve una modifica del proprio visual state per comunicare la trasformazione»* | **KEEP** — più rigoroso della richiesta |
| niente cromatura Excalidraw | *«Nessun sistema di UI di terze parti»* | **KEEP** |
| «Fammi vedere» | `beforeafter-toggle`, commutabile all'infinito, `{motion.instant}` | **KEEP** |
| «Tocca a me» | modalità Studio, KF-4 | **KEEP** |
| equazione accanto al disegno | `equation-anchor`: *«Un'equazione staccata dal disegno è una spiegazione; attaccata, è una prova»* | **KEEP** — non l'avevo chiesto |

## Timeline

| Requisito | Design esistente | Stato |
|---|---|---|
| struttura | **`ProofGraph`**, con diramazione e ricongiungimento *«fin da subito»* | **KEEP** — supera la timeline lineare |
| K-0 e fusione degli step | *«Se un passo non ha disegno, non è un passo — è una riga di calcolo e va fusa con quello precedente»* | **KEEP** — **la tua interpretazione era già scritta** |
| `LayoutIR` per step | — (è CV6) | **NEW** |

## Domini

| Requisito | Design esistente | Stato |
|---|---|---|
| DC: serie, parallelo, Ohm, partitore | sì, ma *«Il catalogo resta a tre»* nell'MVP | **EXTEND** |
| Thévenin / Norton, nodale, maglie | fuori dall'MVP | **EXTEND** |
| transitori `0⁻ 0⁺ ∞ τ`, grafico sincronizzato | citati solo in KF-3 come **caso di Rifiuto** | **NEW** |
| sinusoidale, fasori, RMS/picco, diagramma fasoriale | **nessuna traccia** | **NEW** |

## Uscita

| Requisito | Design esistente | Stato |
|---|---|---|
| PDF | *«Export SVG/PDF con provenienza ← MVP (art. 50, non retrofittabile)»* | **KEEP** |
| stessa timeline, SVG semantico, CircuiTikZ | AD-10 v2 | **KEEP** |
| provenienza sull'artefatto | *«Marcatura di provenienza inclusa e non rimovibile via CSS»* | **KEEP** |
| stampa | foglio di stile dedicato: *«molti studenti stampano»* | **KEEP** — non l'avevi chiesto |

## Responsive — piccolo conflitto

| Requisito | Design esistente | Stato |
|---|---|---|
| desktop tre pannelli 25/50/25 | colonna singola < 768 px; ≥ 768 px i due stati **affiancati**, non tre pannelli | **EXTEND** — nessun 3-pane progettato |
| mobile a schede/swipe | colonna singola con `proofgraph-rail` contraibile; **domanda aperta 7** dichiara che non è deciso | **EXTEND** — la UX sa di non saperlo |
| priorità al canvas | esplicita | **KEEP** |
| card dell'errore in basso | — | **NEW** |

## Modalità

`Guidami` = modalità Studio **KEEP** · `Mostrami` = KF-0 **KEEP** · `Esplora` = editor, *«fuori Gate A
per decisione owner»* **EXTEND** · **`Correggi` = NEW**, ed è la principale.

## Superficie assistente — interamente già progettata

`ProofReplay` **KEEP** · stesso backend **KEEP** · *«La `ProofSession` deve funzionare senza MCP
Apps»* **KEEP** · web-first **KEEP** · passaggio di stato: *«ogni risposta che ne alimenta uno porta
anche un riassunto testuale strutturato»* **KEEP**.

## Estetica — un conflitto diretto, e va deciso

| Requisito | Design esistente | Stato |
|---|---|---|
| niente «AI startup», niente chat protagonista | *«Kirchhoff assomiglia a uno strumento di precisione, non a un'app educativa»* | **KEEP** |
| riferimenti di qualità | *«Linear, Arc, Figma»*; **«il nemico non è la bellezza: è la carineria»** | **KEEP** — più preciso della richiesta |
| animazioni funzionali | *«Il movimento esiste per far capire cosa è cambiato, mai per festeggiare»* | **KEEP** |
| **«bianco/avorio»** | **scuro per default**, deciso dall'owner il 15 agosto: *«l'uso è prevalentemente notturno e sotto scadenza»*. Il chiaro resta pari grado ed è il tema della stampa | **REPLACE o riconferma** |

# Dodici cose migliori che il design esistente ha e che non erano nella richiesta

1. **Pannello dei residui** — cinque righe fisse (KCL, KVL, potenza, accordo fra metodi, coerenza
   fisica), stesso ordine sempre: *«la ripetizione è ciò che rende il pannello leggibile a colpo
   d'occhio dalla seconda volta in poi»*.
2. **«Non certificata» è una superficie con un proprio indirizzo, non un banner.** *«Se fosse un
   banner sopra la Soluzione, il prodotto starebbe dicendo "ecco la soluzione, ma…"»*.
3. **Non certificata ≠ Guasto**, distinti da colore, icona e parole: *«una è il sistema che
   funziona, l'altra è il sistema che è rotto»*.
4. **Mai il rosso per il Rifiuto.** *«È l'errore di design che smonta il posizionamento.»*
5. **«Perché posso farlo?» non genera spiegazioni**: restituisce quattro campi già calcolati —
   terminali, precondizioni, formula, certificato. *«un testo che non corrisponde a un campo è un
   difetto»*.
6. **Alternativa testuale della topologia** (FR-15), non «schema del circuito» ma la struttura:
   *«uno studente ipovedente che studia elettrotecnica esiste, e la topologia è l'informazione»*.
7. **Nessun punteggio sulla persona** (K-5): niente serie, livelli, classifiche.
8. **Progresso a fasi con etichette reali** — *«è l'unico modo di rendere accettabili 45 secondi»*.
9. **Il fondatore non somministra le proprie sessioni** di test.
10. **Vocabolario vincolato**: i termini del glossario del PRD sono i termini dell'interfaccia.
11. **Il criterio con cui si boccia un mock**: *«se il passaggio si capisce solo leggendo la barra
    laterale, il kernel visuale ha fallito»*.
12. **Cifre tabulari obbligatorie** ovunque compaia un numero, disegni inclusi.

# Architettura dell'informazione: dove combacia

```
UX v3 (esistente)                    CircuitCheck (voluto)
─────────────────────                ─────────────────────
                                     Landing                      NEW
Scelta esercizio                     Carica circuito + procedimento
  (raccolta controllata)               EXTEND (circuito) + NEW (procedimento)
[Gate C] Anteprima ricostruzione     «Ho letto questo»            KEEP
[Gate C] Domanda mirata              correzione                   KEEP
—                                    «Ho letto il tuo procedimento così»   NEW
—                                    Primo errore                 NEW
Sessione di prova (passo, rail)      Replay alla lavagna          KEEP
  BEFORE·ACTION·AFTER·EQ·CERT·PROV     ↳ i sei campi ci sono già
ProofGraph                           Soluzione corretta           KEEP
Export SVG/PDF con provenienza       PDF                          KEEP
Non certificata (superficie)         —                            KEEP, da riusare
```

**Due nodi nuovi su nove.** Tutto il resto esiste, e in tre casi è progettato meglio.

# Cosa Studio può già fare

Da `whiteboard-studio/studio` (88 test verdi), senza modifiche:

| Serve | Disponibile oggi |
|---|---|
| caricamento immagini e PDF | ✅ `pdfjs-dist`, PDF come pagine-immagine |
| lavagna e canvas | ✅ Excalidraw — ma la UX vieta cromatura di terzi: utile come **infrastruttura**, non come aspetto |
| replay deterministico | ✅ `JournalRecorder` + `ReplayEngine` |
| formule | ✅ MathLive + MathJax |
| persistenza per stanza | ✅ `WorkspaceStore` |
| esportazione a pacchetto | ✅ bundle `.lesson` (ZIP) |
| superficie a tool ospitati | ✅ `toolhost` + `toolsdk` |
| **rendering schematico** | ❌ **non esiste** |
| **token di design della v3** | ❌ da costruire |
| **`proofgraph-rail`, `step-card`, badge, residui** | ❌ da costruire |

# Domande aperte della UX ancora aperte

7 🟠 densità a 360 px: quale fra circuito, rail ed equazione cede per prima · 8 🟠 larghezza sotto
la quale `ProofReplay` **rifiuta** di presentarsi · 9 🟡 il rail come oggetto d'uso · 10 🟡
**alternativa testuale di un `LayoutPatch`** — descrivere una topologia è risolto, descrivere un
*cambiamento* no · 5 **i mock delle schermate chiave non sono mai stati prodotti**, e la prima della
lista è *«la sessione di prova a metà passaggio — è dove si vince o si perde Gate A»*.
