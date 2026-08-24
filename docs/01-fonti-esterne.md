# Fonti esterne per l'insieme di riferimento

Ricerca eseguita il 13 agosto 2026. Vincolo applicato: **solo licenze aperte compatibili con
l'uso commerciale**, perché §5.10 del piano sorgente vieta di costruire il corpus su opere
dell'ingegno altrui.

## ✅ CGHD — usabile, è la fonte che chiude il punto cieco

**A Public Ground-Truth Dataset for Handwritten Circuit Diagram Images** — DFKI.

| | |
|---|---|
| **Licenza** | **CC-BY-4.0** — uso commerciale permesso, richiesta la sola attribuzione |
| Contenuto | 3.173 immagini annotate di circuiti disegnati a mano |
| Provenienza | 32 disegnatori · 12 circuiti ciascuno · 2 disegni per circuito · 4 **fotografie** per disegno |
| Annotazioni | 245.962 bounding box (PASCAL VOC) · 39.955 annotazioni di rotazione · 84.431 stringhe di testo · 284 mappe di segmentazione |
| Ground truth elettrico | **Netlist in formato ASC solo per una parte** — copertura non dichiarata nel paper |
| Distribuzione | `cghd-zenodo-14.zip`, 4,4 GB · Zenodo record 14042961 · repo `DFKI/cghd` |
| Struttura | `drafter_D/{images,annotations,segmentation}` · file `CX_DY_PZ.jpg` |

**Attribuzione da riportare** ovunque il dataset venga usato o citato:

> Handwritten circuit diagram images from the CGHD dataset (DFKI), used under CC-BY-4.0.
> https://zenodo.org/records/14042961

**Cosa risolve.** Toglie interamente il costo di *raccolta* del gold set fotografico: le foto di
circuiti disegnati a mano esistono già, sono 3.173, vengono da 32 mani diverse, e sono
fotografate — non scansionate. È la classe più difficile della stratificazione prevista dal piano.

**Cosa non risolve.** Non porta soluzione dell'esercizio né IR completo. Resta da annotare a mano
un sottoinsieme con IR e risultato corretto. **Un pomeriggio per 30–40 immagini, contro le due
settimane di una campagna di raccolta.**

## ⚠️ Fiore — NON usabile per questo prodotto

*DC / AC Electrical Circuit Analysis: A Practical Approach*, James M. Fiore (MVCC / LibreTexts).
Esercizi con risposte alle dispari, ottimo materiale.

**Licenza CC BY-NC-SA — la clausola NC esclude l'uso commerciale.** Kirchhoff è un prodotto a
pagamento: costruirci sopra l'insieme di riferimento sarebbe uso commerciale di opera NC.
**Escluso dal corpus.** Resta consultabile come riferimento personale di metodo, non come fonte
di dati.

## Dato di contesto, da non fraintendere

Il baseline pubblicato su CGHD per la **sola rilevazione dei simboli** è **18% mAP** (Faster
R-CNN + ResNet-152, arXiv 2402.11093). È un rilevatore addestrato apposta, e va male.

**Non è la stessa metrica di un VLM frontier end-to-end** e non va citato come se lo fosse:
sarebbe esattamente la conflazione contro cui mette in guardia §1.4 del piano sorgente. Vale come
indizio che il compito è genuinamente difficile, non come misura della baseline che è stata
saltata.

## Fonti

- CGHD su Zenodo — https://zenodo.org/records/14042961
- CGHD su GitHub — https://github.com/DFKI/cghd
- *Modular Graph Extraction for Handwritten Circuit Diagram Images* — https://arxiv.org/abs/2402.11093
- Fiore, *DC Electrical Circuit Analysis* (CC BY-NC-SA, escluso) — https://commons.libretexts.org/book/eng-25010

---

# Ricerca del 13 agosto 2026, sera — secondo giro

Verifiche eseguite contro le pagine ufficiali, non contro riassunti.

## ✅ Digitize-HCD — usabile, complementare a CGHD

*Digitize-HCD: A Dataset for Digitization of Handwritten Circuit Diagrams* — Ahmed et al.,
Data in Brief vol. 59 p. 111315, aprile 2025.

| | |
|---|---|
| **Licenza** | **CC BY 4.0** — verificata sulla pagina Mendeley Data, versione 2, 5 febbraio 2025 |
| Contenuto | 1.277 immagini di circuiti disegnati a mano da **oltre 150 volontari** |
| Annotazioni | 18.602 su 17 classi di simboli · etichette di testo · **posizioni dei terminali** |
| Distribuzione | https://data.mendeley.com/datasets/rngcz5wtv8/2 |

**Perché conta accanto a CGHD.** CGHD annota i simboli ma non i terminali; Digitize-HCD annota
**le porte dei componenti**, che sono l'informazione da cui si ricostruisce la connettività. Le due
fonti sono complementari, non alternative.

**Attribuzione richiesta:**

> Digitize-HCD dataset (Ahmed et al., Data in Brief 59:111315, 2025), used under CC BY 4.0.
> https://data.mendeley.com/datasets/rngcz5wtv8/2

## ❌ Image2Net — NON usabile, ma è il riferimento da citare

*Image2Net: Datasets, Benchmark and Hybrid Framework to Convert Analog Circuit Diagrams into
Netlists* — arXiv 2508.13157.

**Licenza `CC BY-NC-ND 4.0`.** Non commerciale **e** senza derivate: doppiamente incompatibile.
2.914 immagini, 84.195 annotazioni, **104 coppie di netlist verificate a mano**. Escluso dal corpus.

Resta prezioso come **riferimento pubblicato** — è il confronto contro cui misurarsi:

- **80,77%** di successo sul benchmark
- **0,116** NED medio (*Netlist Edit Distance* = distanza di edit fra grafi normalizzata su
  dispositivi + net + porte)

Il NED è la metrica giusta per l'estrazione: misura quanto il grafo ricostruito dista da quello
vero, che è precisamente ciò che SER non vede oggi. **Adottare la definizione di NED è legittimo —
è una formula pubblicata, non un'opera coperta.** Copiare il dataset no.

## ❌ Altri esclusi

- **Fiore, DC/AC Electrical Circuit Analysis** — `CC BY-NC-SA`, la clausola NC esclude l'uso commerciale.
- **JUHCCR-v1** (Nature Sci. Rep.) — licenza non verificata in questa ricerca. Non usare finché non lo è.

## Corpus utilizzabile, totale

**~4.450 immagini, oltre 180 disegnatori, entrambe CC-BY.** Sufficiente e abbondante per la metà
fotografica dell'insieme di riferimento: non serve nessuna campagna di raccolta.

---

# Superfici native — verificate alla fonte primaria

Specifica **MCP Apps**, repo ufficiale `modelcontextprotocol/ext-apps`,
`specification/2026-01-26/apps.mdx`. Righe normative, citate:

- `URI MUST start with ui:// scheme`
- Associazione tool → UI tramite **`_meta.ui.resourceUri`**
- `mimeType MUST be text/html;profile=mcp-app` (altri tipi riservati a estensioni future)
- Comunicazione: **JSON-RPC 2.0 su postMessage**; «UI iframes act as MCP clients, connecting to the
  host via a postMessage transport»

**Riga che corregge il nostro piano:**

> «Tools MUST return meaningful content array even when UI is available»
> `content`: Text representation for model context and text-only hosts
> `structuredContent`: Structured data optimized for UI rendering

Sono **due campi distinti e normati**, non un generico "riassunto testuale" come scritto in FR-20 e
AD-16. La correzione è applicata in quei due punti.

**Supporto host dichiarato:** Claude (web e desktop), ChatGPT, VS Code GitHub Copilot, Microsoft
365 Copilot, Cursor, Goose, Postman, MCPJam, Archestra.AI, PostHog Code.

**Cronologia:** SEP-1865 proposta il 21 novembre 2025, prima estensione ufficiale MCP il 26 gennaio
2026, assorbita nel framework delle estensioni con la specifica 2026-07-28.

## Fonti del secondo giro

- Digitize-HCD — https://data.mendeley.com/datasets/rngcz5wtv8/2
- Image2Net — https://arxiv.org/html/2508.13157v1
- MCP Apps, spec ufficiale — https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx
