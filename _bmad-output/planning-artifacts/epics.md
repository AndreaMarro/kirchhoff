---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
inputDocuments:
  - ../../../KIRCHHOFF-KNOWLEDGE/10-Costituzione/Costituzione Kirchhoff.md   # K-0..K-5, owner-locked
  - prds/prd-Kirchhoff-2026-08-13/prd.md                                      # PRD v3
  - architecture/architecture-Kirchhoff-2026-08-13/ARCHITECTURE-SPINE.md      # Spine v2, 35 AD
  - architecture/architecture-Kirchhoff-2026-08-13/reviews/review-continuita-visuale.md  # CV1-CV7
  - ux-designs/ux-Kirchhoff-2026-08-13/DESIGN.md                              # UX v3, identita' visiva
  - ux-designs/ux-Kirchhoff-2026-08-13/EXPERIENCE.md                          # UX v3, comportamento
  - ../implementation-artifacts/audit-ux-circuitcheck-2026-08-24.md
  - ../implementation-artifacts/spike-d4-renderer-2026-08-24.md
  - ../implementation-artifacts/matrice-impatto-cv1-cv6-su-delta.md
  - ../implementation-artifacts/audit-recinti-ad21-2026-08-24.md
  - ../implementation-artifacts/riconciliazione-stato-2026-08-24.md
  - ../implementation-artifacts/sprint-status.yaml                            # realta' brownfield
supersedes: "epics.md v1 (13 ago 2026) — generato sopra lo spine v1 (35 FR / 20 AD / 40 storie), conservato in git fino a ecc86fd"
derivedFrom: "PRD v3 · ARCHITECTURE-SPINE v2 · UX v3 — passo 6 della catena BMAD (scripts/bmad_chain.py)"
brownfieldBaseline: "ecc86fd — 245 test verdi, copertura 100%, gate exit 0"
---

# CircuitCheck — motore Kirchhoff - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for CircuitCheck — motore Kirchhoff, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR-1**: Ingestione multi-formato
- **FR-2**: Estrazione multi-pass con misura dell'Accordo
- **FR-3**: Ridondanza testuale come secondo canale
- **FR-4**: Validazione elettrica come gate
- **FR-5**: Anteprima di ricostruzione, sempre
- **FR-6**: Domanda mirata su Ambiguità residua
- **FR-7**: Tetto di due giri e degrado all'editor
- **FR-8**: Ripresa senza perdita e senza doppio addebito
- **FR-9**: Editor del circuito
- **FR-10**: Risoluzione a percorsi indipendenti
- **FR-11**: Verifica a cinque controlli come gate di pubblicazione
- **FR-12**: Rifiuto di certificazione come esito progettato
- **FR-13**: Nessun valore generato da modello linguistico
- **FR-14**: Piano didattico da Catalogo chiuso
- **FR-15**: Disegno del circuito a ogni passo
- **FR-16**: Profilo curricolare
- **FR-17**: Modalità Studio a rivelazione progressiva
- **FR-18**: Export multiformato
- **FR-19**: Marcatura di provenienza su ogni artefatto
- **FR-20**: Superficie assistente con conferma in conversazione
- **FR-21**: Collegamento dell'account dalla superficie assistente
- **FR-22**: Generazione di Varianti verificate
- **FR-23**: Vincoli di generazione
- **FR-24**: Fogli soluzione separati e verificabili
- **FR-25**: Banco esercizi del tenant
- **FR-26**: Consumo per Soluzione consegnata
- **FR-27**: Acquisto di Crediti e piani
- **FR-28**: Registrazione con dichiarazione di età
- **FR-29**: Dichiarazione d'uso dell'IA al primo contatto
- **FR-30**: Cancellazione automatica delle immagini
- **FR-31**: Offuscamento delle regioni personali
- **FR-32**: Consenso esplicito all'uso dei contenuti per il miglioramento
- **FR-33**: Esercizio dei diritti dell'interessato
- **FR-34**: Eval harness sul gold set
- **FR-35**: Segnalazione di errore dall'utente
- **FR-36**: Quota per soggetto anonimo
- **FR-37**: Rappresentazione doppia e persistente
- **FR-38**: La trasformazione è un `LayoutPatch` con invariante di conservazione
- **FR-39**: Grammatica obbligatoria del passo
- **FR-40**: La derivazione è un `ProofGraph`, non una lista
- **FR-41**: Il round-trip visuale è il controllo primario della topologia
- **FR-42**: Il gate di veridicità è componente proprietaria, non skill esterna
- **FR-43**: Catalogo chiuso, e la sua condizione di apertura
- **FR-44**: `StudentTrace` è ingresso semantico, non immagine
- **FR-45**: Un kernel, tre adapter — nessun fork
- **FR-46**: Famiglie di test obbligatorie, e il fallimento sfuggito diventa invariante
- **FR-47**: I quattro bracci di Gate A, dallo stesso passaggio
- **FR-48**: `ProofSession` è indipendente dalla superficie
- **FR-49**: Ispezione del passaggio, ancorata allo stato
- **FR-50**: Quattro classi di stato visivo, e una sola è vincolata
- **FR-51**: Registro di provenienza e licenza — oggetto versionato, non foglio amministrativo
- **FR-52**: Il confine del kernel è `CircuitIR`, e la percezione sta fuori
- **FR-53**: `TransformOverlay` è un layer separato, e non occlude mai un'entità preservata

<!-- 53 requisiti funzionali estratti da prd.md v3 -->

### NonFunctional Requirements

> **Numerazione derivata dal passo 6, non presente nel PRD.** Il PRD v3 elenca gli NFR in §9 *Cross-Cutting NFRs* come voci puntate senza identificatore. Gli identificatori `NFR-1…NFR-9` sono stati assegnati **qui** per rendere i requisiti citabili dalle storie. Il PRD **non** è stato modificato retroattivamente per introdurli.


- **NFR-1 · Budget di latenza end-to-end.** Dal caricamento alla Soluzione consegnata **< 45 s** al 90° percentile, domande incluse. Sopra i 60 s l'utente abbandona.
- **NFR-2 · Determinismo del calcolo.** A parità di IR confermato, soluzione e passaggi sono riproducibili.
- **NFR-3 · Tracciabilità.** Ogni Soluzione consegnata è ricostruibile dall'IR e dalla versione di sistema che l'ha prodotta.
- **NFR-4 · Indipendenza dal fornitore di modelli.** Almeno due fornitori intercambiabili; la caduta di uno degrada la qualità, non la disponibilità.
- **NFR-5 · Accessibilità.** Superfici interattive usabili da tastiera e screen reader, con alternative testuali per ogni disegno. Non negoziabile per i clienti istituzionali.
- **NFR-6 · Mobile-first.** Il flusso B2C si completa su schermo telefono senza scorrimento orizzontale.
- **NFR-7 · Isolamento fra tenant.** Nessun dato di un tenant è raggiungibile da un altro.
- **NFR-8 · Osservabilità.** Tutte le metriche di §8 — le quattro storiche più le nove della v3, **VCER compresa** — più tasso di Rifiuto e correzioni per soluzione, strumentate in produzione, non solo in eval.
- **NFR-9 · Non-regressione della qualità.** Nessuna modifica che tocchi estrazione, Validazione elettrica, Trasformazioni o Piano didattico raggiunge la produzione senza esecuzione dell'eval harness.

### Additional Requirements

Estratti da `ARCHITECTURE-SPINE.md` v2 (**35 AD**, di cui dieci emendati in loco il 15 agosto) e dalle review architetturali. Solo ciò che vincola l'implementazione.

**Nessun template starter.** Lo spine non prescrive alcuno scaffold: il progetto è **brownfield** e la struttura esiste già (`src/kirchhoff/{domain,eval,ports,render,adapters,api,pipeline}`). Epic 1 Story 1 **non** è «inizializza il progetto».

**Contratti che governano il codice**

- **AD-1 · `CircuitIR` è l'unico contratto fra stadi.** Firma `(CircuitIR, ctx) → CircuitIR | Refusal`. Il `LayoutIR` è rappresentazione pari grado e **non compare mai nella firma di uno stadio di calcolo** (AD-21).
- **AD-2 em. · Le Trasformazioni sono funzioni pure.** `transform(CircuitIR, params) → (CircuitIR, TransformResult) | Refusal`, con `TransformResult = PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate`. Il `LayoutPatch` nomina **entità, non coordinate**. Catalogo chiuso caricato all'avvio.
- **AD-3 · `ModelPort`.** Nessun modulo sotto `domain/` importa un SDK di fornitore. Almeno due adapter registrati; la selezione è configurazione.
- **AD-4 em. · Nessun numero mostrato all'utente proviene da un modello linguistico.** Segnaposto `[[q.value]]` **legati allo scope del passo**; un segnaposto fuori scope è respinto, uno non risolto produce `Refusal`.
- **AD-5 em. · Gate di pubblicazione unico.** `publish()` esegue otto controlli: i cinque residui, incidenza geometrica, round-trip, `TruthfulnessGate`.
- **AD-8 em. · Un solo scrittore per entità.** `CircuitIR`→`ingest` · `LayoutIR`→`render/layout` (**mai** `domain/`) · `ProofGraph`→`domain/proof` · `Claim`→`domain/truthfulness` · `SourceAsset`→`corpus/` · `InteractionState`→client, non persistito.
- **AD-10 em. · L'SVG semantico verificato è la sorgente unica di ogni altro formato.** PDF e CircuiTikZ **derivano**, non re-interpretano.
- **AD-13 · `Refusal` e `Failure` sono tipi e canali diversi.** Il Rifiuto non consuma Crediti.
- **AD-18 em. · `Drawing` non esiste più.** Il dominio non produce geometria e **non conosce il concetto di posizione**.
- **AD-19 em. · `Refusal.cause` da enumerazione chiusa** con payload che porta sempre `subject`. Cause v2 aggiunte: `identity_violation`, `preserve_nonmaximal`, `empty_boundary`, `render_roundtrip`, `overlay_occlusion`, `claim_unsupported`.
- **AD-21 · Quattro rappresentazioni disgiunte** — `CircuitIR`, `LayoutIR`, `TransformOverlay`, `InteractionState`. Nessuna contiene un'altra. `ProofSession` è **proiezione per riferimento**, non aggregato.
- **AD-22 em. · Il `preserve set` deriva dalla `Transform`, mai dal renderer.** `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` dopo `node_mapping`; `node_mapping` **totale e iniettiva sui sopravvissuti**; `id_{k+1}(x) = id_k(x)` per ogni `x ∈ Pₖ` **senza tolleranza**, verificato *fra un passo e il successivo*. Ogni campo del `TransformResult` è non-vuoto o il prodotto non è costruibile.
- **AD-23 · Ordine dei layer fisso** `0…8`, con R-Visual-1: un'annotazione di trasformazione non occlude mai un'entità semantica preservata.
- **AD-24 · La percezione sta fuori dal kernel**, dietro `PerceptionCandidate`.
- **AD-25 · Nessun artefatto entra nel corpus senza `SourceAsset`**; `UNKNOWN` è fail-closed.
- **AD-27 · Un kernel, tre adapter, dipendenza a senso unico.**
- **AD-29 · Il `ProofGraph` è un grafo dal primo commit.**
- **AD-31 · Incidenza geometrica controllata.** Ogni estremo di filo tocca il terminale che l'annotazione dichiara, entro tolleranza dichiarata. **L'annotazione è derivata dalla geometria, mai il contrario.** Sesto controllo di `publish()`.
- **AD-32 · Il `TruthfulnessGate` è cablato all'uscita**, non solo definito.
- **AD-35 · Il rendering è deterministico per costruzione.** `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` è **pura**: stessi byte, niente orologio, niente id a runtime, nessun ordinamento dipendente dall'inserimento in mappa. Fallimento di CI, non `Refusal`.

**Recinti di dipendenza** (`scripts/check_boundaries.py`). AD-21 v2 dice testualmente: *«`scripts/check_boundaries.py` ha oggi **un solo** recinto (`RECINTO = "domain"`). **Deve averne cinque**, ciascuno una freccia vietata»*. Sono **cinque**, non sei — enumerati qui verbatim dalla fonte invece che contati:

| # | Freccia vietata | Ordinato da | Stato oggi |
|---|---|---|---|
| 1 | `domain/` → qualunque cosa fuori da `domain/` | AD-1, paradigma | ✅ implementato e testato |
| 2 | `domain/` → `render/` | AD-18, AD-21 | ✅ coperto per implicazione dal 1 |
| 3 | `domain/` → `perception/` | AD-24 | ✅ coperto per implicazione dal 1 |
| 4 | `domain/` ∪ `render/` → `adapters/` | AD-27 | ⚠️ solo la metà `domain/`; `render/` non è scandito |
| 5 | qualunque cosa fuori da `corpus/` → il filesystem del corpus | AD-25 | ❌ assente |

**Un sesto recinto è raccomandato da CV5 e non è ancora nello spine**: *«nessun percorso di codice del braccio 0 riceve, importa o risolve un `LayoutIR` di `Cₖ` — né per parametro, né per `ctx`, né per lookup su identificatore»*. È una raccomandazione di review, non un requisito di AD-21: emendare AD-21 è prerequisito per renderlo esigibile.

**Rilievi architetturali aperti che vincolano le storie**

- **CV1** (critico) — la codifica di braccio non è tipizzata: un renderer potrebbe ricalcolare `preserve` come complemento della classe «changed», reintroducendo l'autocertificazione che AD-22 chiude. *«Un bug che si legge come dato.»*
- **CV2** (critico) — il test permanente di A-0 è falso per costruzione sui bracci B e C.
- **CV3** (critico) — R-Visual-1 non è implicata dall'ordine dei layer, non esiste un predicato di occlusione, e `overlay_occlusion` è una causa di `Refusal` che **nessuno stadio solleva**.
- **CV6** (alto) — `LayoutIR` e `LayoutPatch` non hanno identificatore né regola di ritenzione, e l'ERD non li conosce: **VCER non è calcolabile**, quindi Gate A non ha un verdetto.
- **Identità semantica** (verificato il 24/08) — AD-22 impedisce di dichiarare «creata» una sopravvissuta, ma **non** impedisce a una trasformazione di riusare l'id di una vecchia entità per farne apparire preservata una nuova, perché `Pₖ` è l'intersezione **per identificatore**.

**Decisioni owner aperte che bloccano** (`KIRCHHOFF-KNOWLEDGE/30-Decisioni-aperte`)

- **D2** → blocca la storia sul profilo curricolare che restringe il catalogo.
- **D4 — RISOLTA, superseded il 24/08/2026.** Non blocca più Gate A. La risoluzione non è una preferenza: **AD-10 v2** (l'SVG semantico verificato è la sorgente unica di ogni altro formato), **AD-31 v2** (l'annotazione è derivata dalla geometria, mai il contrario) e **AD-35 v2** (`render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` è pura) determinano insieme lo stack, e l'owner ha ratificato: **SVG semantico deterministico generato da noi come rappresentazione visuale canonica verificabile**; CircuiTikZ resta **export derivato di qualità**, non renderer primario; un graph-layout engine che ricompone da zero **è il braccio 0**, non il braccio A; l'autolayout generale **non blocca** Visual Slice 0.
  > Il file storico `D4 Renderer stack web vs PDF.md` continua a dichiararsi `stato: aperta`. Non va riscritto: la decisione è stata **risolta a valle** dalle autorità v2, e questo è il record.
- **D5, D6, D9, D10** → claim commerciali, soglie di lancio, ricavo, condivisione.
- **D11** → blocca Gate F. **Verificato compatibile**: vieta a Kirchhoff di importare simulatore, memoria studente o shell; non vieta a un prodotto superiore di comporre.

**Realtà brownfield** — `git rev-parse HEAD` = `ecc86fd`, **245 test verdi, copertura 100%**, `check_boundaries` e `check_domain_coverage` exit 0, `kirchhoff-eval report --split dev` VSR 1.0 / SER 0.0 su 36 casi.

### UX Design Requirements

Estratti da `ux-designs/ux-Kirchhoff-2026-08-13/` — `DESIGN.md` v3 (identità visiva) ed `EXPERIENCE.md` v3 (comportamento), letti integralmente. **Entrambi dichiarano `supersedes: v2 — prodotto centrato sull'Anteprima da foto`**: la v2 era il percorso foto di CircuitCheck e la v3 lo ha spostato a Gate C.

**Sistema di design**

- **UX-DR1** — Sistema di token completo a **doppio tema**: 22 token colore scuri più 22 chiari pari grado (`surface-*`, `ink-*`, `rule-*`, `verified`, `suspended`, `fault`, `provenance`, `focus-ring`). **Scuro per default**, chiaro completo e non secondario: è il tema della stampa.
- **UX-DR2** — Scala di movimento a tre durate (`instant 90ms`, `quick 140ms`, `considered 220ms`) con easing unico. `prefers-reduced-motion` rimuove ogni transizione tranne il cambio di stato del passo, che diventa istantaneo.
- **UX-DR3** — Sette ruoli tipografici, con **cifre tabulari obbligatorie** (`font-variant-numeric: tabular-nums`) ovunque compaia un numero, disegni inclusi. `label-drawing` a **11 px effettivi minimi** nei disegni: un disegno che scenderebbe sotto va **ricomposto, non rimpicciolito** (vincolo FR-15).

**Diciannove componenti propri** — *«Nessun sistema di UI di terze parti»*, perché l'Anteprima con ancoraggio di provenienza e il pannello dei residui non esistono in nessuna libreria:

- **UX-DR4** — `badge-verified` e `badge-suspended`: **forma, etichetta e colore insieme, mai il colore da solo**; identici per forma e posizione, distinguibili in scala di grigi; **entrambi toccabili** — un badge che non si apre è un'affermazione, uno che si apre è una prova.
- **UX-DR5** — `provenance-anchor`: riquadro sulla sorgente che lega un componente alla sua area di lettura. Legame **bidirezionale**.
- **UX-DR6** — `residual-row` e pannello dei residui: **cinque righe fisse, sempre nello stesso ordine** — KCL, KVL, potenza, accordo fra metodi, coerenza fisica. Non riordinabile.
- **UX-DR7** — `step-card` con i **sei campi di FR-39** nell'ordine `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE · PROVENANCE`. Un passo senza `CERTIFICATE` **non compare**.
- **UX-DR8** — `subgraph-highlight`: marca **solo** i componenti che cambiano, stretto attorno alla sagoma, **scope locale per obbligo sperimentale**; compare **prima di qualunque testo**.
- **UX-DR9** — `boundary-anchor`: overlay effimero al layer 6, `fill: none`, 9 px. Togliendolo il nodo torna identico. Vive nel `TransformOverlay`, non nel `LayoutIR`.
- **UX-DR10** — `equation-anchor`: l'equazione sta **accanto** al sottografo che l'ha generata, collegata da una linea. *«Un'equazione staccata dal disegno è una spiegazione; attaccata, è una prova.»*
- **UX-DR11** — `certificate-chip` **quadrato**, distinto dal `badge-verified` **tondo**: uno certifica il passo, l'altro la soluzione.
- **UX-DR12** — `beforeafter-toggle`: due stati commutabili all'infinito, `{motion.instant}`, **pollice-raggiungibile** su mobile.
- **UX-DR13** — `proofgraph-rail`: la derivazione come **grafo percorribile**, sempre visibile, con diramazione e ricongiungimento. *«Non è una barra di avanzamento: il rail si usa.»*
- **UX-DR14** — `question-card` con **ritaglio ingrandito in cima**, alternative grandi, campo libero sempre in coda; **una domanda per volta**.
- **UX-DR15** — `disclosure-bar` persistente e **non chiudibile**, su ogni superficie, pannello assistente incluso.
- **UX-DR16** — `attenuation`, `unchanged-marker`, `region-highlight`: **non sono default**. Esistono solo come bracci C e B dell'esperimento di Gate A, cioè come pattern comune da battere.

**Continuità visuale**

- **UX-DR17** — **A-0, Unmarked Preservation Hypothesis**: un'entità preservata non riceve modifica del proprio visual state per comunicare la trasformazione. Invariante **semantico-spaziale, non pixel-perfect**: `id_{k+1}(x) = id_k(x)` senza eccezioni, `p_{k+1}(x) ≈ p_k(x)` salvo necessità geometriche dimostrabili, comunque **misurate e penalizzate da VCER**.
- **UX-DR18** — **Ordine dei layer 0…8** deterministico, con R-Visual-1.
- **UX-DR19** — **Quattro classi di stato visivo**, e solo la prima è vincolata da A-0: trasformazione (sì), interazione, accessibilità, ispezione/debug (no).

**Stati e interazione**

- **UX-DR20** — **Undici stati** con regola dominante: *Non certificata* e *Guasto* **non devono mai assomigliarsi** — colore, icona e parole devono distinguerli tutti e tre insieme.
- **UX-DR21** — **«Non certificata» è una superficie con indirizzo proprio**, condivisibile, che sopravvive al ricaricamento. Non un banner.
- **UX-DR22** — Sette primitive di interazione: un tocco per confermare · tocco su un valore = provenienza · tocco sul badge = prova · **massimo due giri di domande con contatore visibile** · nessuna azione distruttiva senza annullamento · **nessun auto-avanzamento** · movimento minimo.
- **UX-DR23** — «Perché posso farlo?» risponde con **quattro campi già calcolati** — terminali, precondizioni, formula, certificato — e **non genera spiegazioni**.
- **UX-DR24** — Progresso a fasi con **etichette reali** («normalizzo l'immagine», «leggo il circuito», «controllo la rete», «risolvo», «verifico»).

**Accessibilità — pavimento non negoziabile, WCAG 2.2 AA su tutte e tre le superfici**

- **UX-DR25** — **Alternativa testuale della topologia** per ogni disegno: non «schema del circuito» ma la struttura. Requisito di prodotto (FR-15).
- **UX-DR26** — Flusso intero percorribile da tastiera; **nessuno stato portato dal solo colore** — verifica operativa: la schermata resta interpretabile in scala di grigi; bersagli ≥ 44 × 44 px; formule accessibili **come matematica**; nessun limite di tempo.

**Responsive e superfici**

- **UX-DR27** — < 768 px colonna singola, disegni interi entro 360 px senza scorrimento orizzontale; ≥ 768 px i due stati **affiancati** ma il toggle **resta**; modalità scura pari grado; **foglio di stile di stampa** con marcatura di provenienza non rimovibile via CSS.
- **UX-DR28** — Superficie assistente `ProofReplay`: **nessuno stato locale** · ogni risposta porta **anche un riassunto testuale strutturato** perché l'assistente non vede il pannello · **parità funzionale sui gate** · accessibilità pari.
- **UX-DR29** — **La `ProofSession` deve funzionare senza MCP Apps**: il degrado a superficie non interattiva è un percorso **progettato**, non un guasto.

**Voce**

- **UX-DR30** — Sette regole di microcopy, **vocabolario vincolato** al Glossario del PRD, e parole vietate: «magia», «istantaneo», «perfetto», «garantito al 100%», «IA avanzata», «potenziato dall'IA».
- **UX-DR31** — **Mai il rosso per il Rifiuto di certificazione**: *«è l'errore di design che smonta il posizionamento»*. Nessuna celebrazione sulla soluzione corretta. **Nessun punteggio sulla persona** (K-5).

**Protocollo di ricerca**

- **UX-DR32** — Protocollo A/B di Gate A: quattro bracci su **un asse solo**, disegno **entro-soggetti** a quadrato latino, **sei misure** di cui cinque oggettive e la preferenza soggettiva **in coda**. *«Un braccio che vince solo sulla 6 non ha vinto.»* **Nessuna differenza estetica fra i bracci** — è il vincolo di design che non ammette eccezioni.

---

### Classificazione delle voci UX

Le trentadue voci sopra **non sono omogenee** e vanno lette per genere, non in blocco:

| Genere | Quali | Significato |
|---|---|---|
| **UX REQUIREMENT** | UX-DR1…3, 4…16, 20…24, 27…30 | va costruito |
| **UX CONSTRAINT** | UX-DR17, 18, 19, 25, 26, 31, 32 | vincola *come* si costruisce; violarlo invalida A-0, l'accessibilità o l'esperimento |
| **UX EXISTING PATTERN** | UX-DR21, 22, 23 | già progettato e riusabile così com'è |
| **UX GAP** | vedi sotto | **manca**, ed è la voce che genera storie nuove |

### UX GAP

- **UX-GAP-01 — la UX corrente non offre il flusso «Correggi»: non esiste alcun percorso che importi un `StudentTrace` già svolto.**

  **Provenienza del gap, in tre strati:**
  1. **Il PRD lo richiede già.** `FR-44 — StudentTrace è ingresso semantico, non immagine`: *«Quando il sistema controlla una derivazione prodotta dallo studente, la riceve come struttura semantica — passi, equazioni, grandezze dichiarate»*, e *«un `StudentTrace` è confrontabile col `ProofGraph` di riferimento **passo per passo**, non solo sul risultato finale»*. Il meccanismo del primo errore è **già una conseguenza testabile del PRD**.
  2. **L'architettura e il dominio non l'hanno mai implementato.** Nessun tipo `StudentTrace` esiste nel codice.
  3. **La UX ha progettato «Guidami», non «Correggi».** KF-4 è la modalità Studio: il sistema chiede, lo studente risponde **dentro** il sistema. Nessuno dei sette flussi importa un lavoro già svolto.

  **Conseguenza per il backlog:** CircuitCheck non è una deviazione dal progetto. È la concretizzazione di un requisito rimasto **sospeso fra gli strati** — richiesto dal PRD, mai sceso in architettura, mai progettato in UX, quindi mai implementato.

  **Tensione da risolvere nella decomposizione, non da nascondere:** FR-44 si dichiara *«Fuori MVP — Gate B (tutor interattivo)»*, mentre la priorità di prodotto dell'owner mette il primo errore **presto**. La collocazione di Gate va decisa esplicitamente dalle Epic, non ereditata in silenzio.

  **Vincolo di naming (search-before-build eseguito):** il nome autoritativo è **`StudentTrace`**, non `StudentSolutionIR`. Nessun tipo nuovo va introdotto senza aver prima stabilito se `StudentTrace` è già il contenitore cercato.

### FR Coverage Map

Tutti i **53** requisiti funzionali del PRD v3 hanno un'epica primaria. Nessun orfano.

| FR | Epica | In una riga |
|---|---|---|
| FR-1 | 3 | ingestione multi-formato |
| FR-2 | 3 | estrazione multi-pass con misura dell'Accordo |
| FR-3 | 3 | ridondanza testuale come secondo canale |
| FR-4 | 3 | validazione elettrica come gate — **SATISFIED** |
| FR-5 | 3 | Anteprima di ricostruzione, sempre |
| FR-6 | 3 | Domanda mirata su Ambiguità residua |
| FR-7 | 3 | tetto di due giri e degrado all'editor |
| FR-8 | 3 | ripresa senza perdita e senza doppio addebito |
| FR-9 | 3 | editor del circuito |
| FR-10 | 4 | risoluzione a percorsi indipendenti |
| FR-11 | 4 | verifica a cinque controlli come gate di pubblicazione |
| FR-12 | 4 | Rifiuto di certificazione come esito progettato |
| FR-13 | 4 | nessun valore generato da modello linguistico |
| FR-14 | 4 | piano didattico da Catalogo chiuso |
| FR-15 | 1 | disegno del circuito a ogni passo — **K-0** |
| FR-16 | 4 | profilo curricolare — **bloccato da D2** |
| FR-17 | 2 | modalità Studio a rivelazione progressiva — «Guidami» |
| FR-18 | 5 | export multiformato |
| FR-19 | 5 | marcatura di provenienza su ogni artefatto |
| FR-20 | 6 | superficie assistente con conferma in conversazione |
| FR-21 | 6 | collegamento dell'account dalla superficie assistente |
| FR-22 | 7 | generazione di Varianti verificate |
| FR-23 | 7 | vincoli di generazione |
| FR-24 | 7 | fogli soluzione separati e verificabili |
| FR-25 | 7 | banco esercizi del tenant |
| FR-26 | 8 | consumo per Soluzione consegnata |
| FR-27 | 8 | acquisto di Crediti e piani |
| FR-28 | 8 | registrazione con dichiarazione di età |
| FR-29 | 8 | dichiarazione d'uso dell'IA al primo contatto |
| FR-30 | 8 | cancellazione automatica delle immagini |
| FR-31 | 8 | offuscamento delle regioni personali |
| FR-32 | 8 | consenso esplicito all'uso dei contenuti |
| FR-33 | 8 | esercizio dei diritti dell'interessato |
| FR-34 | 1 | eval harness sul gold set — **SATISFIED** |
| FR-35 | 2 | segnalazione di errore dall'utente |
| FR-36 | 8 | quota per soggetto anonimo |
| FR-37 | 1 | rappresentazione doppia e persistente |
| FR-38 | 1 | la trasformazione è un `LayoutPatch` con invariante di conservazione |
| FR-39 | 1 | grammatica obbligatoria del passo — i sei campi |
| FR-40 | 1 | la derivazione è un `ProofGraph`, non una lista |
| FR-41 | 1 | il round-trip visuale è il controllo primario della topologia |
| FR-42 | 4 | il gate di veridicità è componente proprietaria |
| FR-43 | 1 | catalogo chiuso, e la sua condizione di apertura |
| FR-44 | 2 | **`StudentTrace` è ingresso semantico** — la USP |
| FR-45 | 6 | un kernel, tre adapter — nessun fork |
| FR-46 | 1 | famiglie di test obbligatorie |
| FR-47 | 1 | i quattro bracci di Gate A |
| FR-48 | 6 | `ProofSession` indipendente dalla superficie |
| FR-49 | 1 | ispezione del passaggio, ancorata allo stato |
| FR-50 | 1 | quattro classi di stato visivo |
| FR-51 | 5 | registro di provenienza e licenza |
| FR-52 | 3 | il confine del kernel è `CircuitIR` |
| FR-53 | 1 | `TransformOverlay` è un layer separato |

**Distribuzione:** Epic 1 → 13 · Epic 2 → 3 · Epic 3 → 10 · Epic 4 → 7 · Epic 5 → 3 · Epic 6 → 4 ·
Epic 7 → 4 · Epic 8 → 9 · Epic 9 e 10 → estendono, non coprono. **Totale 53.**

### Copertura non-FR

| Requisito | Dove atterra |
|---|---|
| **K-0** il circuito è il ragionamento | Epic 1, criterio di accettazione di ogni trasformazione pedagogica |
| **K-3** il rifiuto è un output valido | Epic 4 — `Refusal` già implementato |
| **K-5** nessun punteggio sulla persona | Epic 2, vincolo negativo su «Guidami» |
| **AD-10** SVG sorgente unica | Epic 5, vincolo su tutti gli export |
| **AD-21** i cinque recinti | Epic 1 (recinto 4 quando nasce `render/`) ed Epic 3 (recinto 3 quando nasce `perception/`) |
| **AD-22** preserve set e identità | Epic 1, storia bloccante |
| **AD-31** incidenza geometrica | Epic 1, sesto controllo di `publish()` |
| **AD-35** rendering deterministico | Epic 1, famiglia di test obbligatoria |
| **CV1, CV2, CV3** | Epic 1 — toccano la codifica di braccio, il test permanente di A-0 e l'occlusione |
| **CV6** ritenzione del `LayoutIR` | Epic 1, **prerequisito perché Gate A abbia un verdetto** |
| **UX-GAP-01** | Epic 2, è la ragione per cui l'epica esiste |
| **NFR-1…NFR-9** | trasversali; NFR-2 e NFR-8 sono criteri di accettazione in Epic 1 |

### Dipendenze fra epiche

```
Epic 4 (verifica)  ──┐
                     ├──> Epic 1 (derivazione visibile)  ──> Epic 2 (correggi)
Epic 3 (percezione) ─┘                │                          │
                                      ├──> Epic 5 (export)       │
                                      └──> Epic 6 (assistente)   │
                                                                 │
Epic 7 (docente) ──> Epic 8 (ricavo)          Epic 9, 10 ────────┘ (dominio)
```

**Nessuna epica richiede una successiva per funzionare.** Epic 2 costruisce su Epic 1 ma **non
richiede Epic 3**: con un `StudentTrace` strutturato il primo errore funziona senza fotografia. È il
vincolo di prioritizzazione di prodotto più importante del backlog — mettere la percezione prima del
primo errore semantico spenderebbe lo sprint sulla parte meno differenziante.

## Epic List

## Epic List

Otto epiche di prodotto più due estensioni di dominio differite. Organizzate per **esito utente**,
non per strato tecnico. Ogni epica dichiara il proprio Gate, il proprio stato brownfield e le
proprie dipendenze — e nessuna richiede un'epica successiva per funzionare.

> **Il principio che ha guidato la decomposizione.** Il vecchio backlog aveva come obiettivo
> implicito «completare Kirchhoff». Questo ha come obiettivo **rendere vera, verificabile e
> pubblicabile una sola promessa**: *«Fammi vedere cosa hai fatto e ti mostro esattamente il primo
> punto in cui il tuo ragionamento ha smesso di essere corretto.»* Kirchhoff resta il motore
> verificato che la rende possibile.

---

### Epic 1: La derivazione che si vede e che si può controllare

**Gate primario: A** (Visual Proof Kernel — *kill criterion*) · Gate secondario: nessuno

Uno studente segue una riduzione del circuito **senza perdere mentalmente il circuito che stava
guardando**, e ogni passo porta con sé la prova che è lecito. Al termine non ha una pagina di
risposta: ha una derivazione percorribile avanti e indietro, in cui può chiedere a ogni elemento da
dove viene e perché quel passaggio era permesso.

È l'epica su cui il prodotto vive o muore: se la continuità visuale non batte un re-layout completo,
il catalogo non si espande e il resto non si costruisce.

**FR coperti:** FR-15, FR-34, FR-37, FR-38, FR-39, FR-40, FR-41, FR-43, FR-46, FR-47, FR-49, FR-50, FR-53

**Stato brownfield:** solver esatto e catalogo pedagogico **SATISFIED** · `Delta` e lineage
**SATISFIED** (`ad29c8e`) · validazione elettrica **SATISFIED** (`265bab1`) · eval harness e holdout
**SATISFIED** · identità semantica **PARTIAL** (AD-22 chiude una direzione sola) · ritenzione del
`LayoutIR` **MISSING** (CV6: senza, VCER non è calcolabile) · renderer SVG semantico **MISSING** ·
recinti 4 e 5 **MISSING**.

---

### Epic 2: «Fammi vedere cosa hai fatto»

**Gate primario: B** · Gate secondario: **A** (consuma la derivazione verificata come riferimento)

Uno studente che ha già risolto l'esercizio **sul proprio foglio** carica ciò che ha fatto, e il
sistema gli dice **dove il ragionamento ha smesso di essere valido** — non se il risultato è giusto.
Distingue *«non riesco a leggere questo passaggio»* da *«questo passaggio è sbagliato»*, e preferisce
dichiarare di non sapere piuttosto che accusare a torto.

È la USP di CircuitCheck, ed è la chiusura di **UX-GAP-01**: il PRD lo richiedeva già con FR-44,
l'architettura non l'ha mai implementato, la UX ha progettato «Guidami» e non «Correggi».

**FR coperti:** FR-17, FR-35, FR-44

**Stato brownfield:** `StudentTrace` **MISSING** in ogni forma · allineamento passo-per-passo col
`ProofGraph` **MISSING** · modalità Studio «Guidami» **DESIGNED, non implementata** · tassonomia degli
errori del procedimento **MISSING**.

**Decisione di collocazione da prendere esplicitamente:** FR-44 si dichiara *«Fuori MVP — Gate B»*,
mentre la priorità di prodotto mette il primo errore **presto**. L'epica va collocata dal readiness
gate, non ereditata in silenzio.

---

### Epic 3: Dal foglio fotografato al circuito confermato

**Gate primario: C** · Gate secondario: **B** (la stessa conferma serve al procedimento)

Uno studente fotografa l'esercizio e, **prima che il sistema giudichi qualsiasi cosa**, vede cosa ha
letto e può correggerlo. La conferma non è attrito da minimizzare: è il momento in cui nasce la
fiducia, ed è la sorveglianza umana che la conformità richiede. Un solo tocco quando non c'è nulla da
correggere; al massimo due giri di domande; poi l'editor.

**FR coperti:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-52

**Stato brownfield:** FR-4 validazione elettrica **SATISFIED** · `Provenance` normalizzata già nel
contratto dell'IR **SATISFIED** · estrazione, accordo multi-pass, anteprima, domanda mirata, editor
**MISSING** · `perception/` è un pacchetto vuoto.

---

### Epic 4: Un numero di cui si può rispondere

**Gate primario:** nessuno diretto — è la fondazione che gli altri Gate certificano

L'utente ottiene un risultato **solo** quando ha superato i controlli, e quando non li supera ottiene
una spiegazione onesta invece di un numero. *«Non ti mostro un numero di cui non posso rispondere»* è
la promessa detta nel momento in cui costa qualcosa dirla.

**FR coperti:** FR-10, FR-11, FR-12, FR-13, FR-14, FR-16, FR-42

**Stato brownfield:** MNA esatta multi-dominio **SATISFIED** · residui KCL e bilancio di potenza
**SATISFIED** · `Refusal` come tipo di dominio **SATISFIED** (`265bab1`) · cinque controlli come gate
unico **PARTIAL** · Percorso B **MISSING** · `TruthfulnessGate` e `Claim` **MISSING** · piano didattico
da catalogo chiuso **MISSING** · profilo curricolare **BLOCCATO da D2**.

---

### Epic 5: Portarlo via

**Gate primario: D** (distribuzione) · Gate secondario: **A**

Lo studente si porta via la soluzione in una forma che resta leggibile fuori dal prodotto — stampata,
allegata, condivisa — e **ogni artefatto dichiara da dove viene**. Non è un'aggiunta di comodo: la
marcatura di provenienza non è retrofittabile e l'art. 50 la impone.

**FR coperti:** FR-18, FR-19, FR-51

**Stato brownfield:** tutto **MISSING**. Vincolo autoritativo AD-10 v2: l'SVG semantico verificato è
la **sorgente unica**; PDF e CircuiTikZ derivano e non re-interpretano il circuito.

---

### Epic 6: Dentro una conversazione

**Gate primario: D** · Gate secondario: nessuno

Lo stesso lavoro, dentro un assistente di terzi, **senza che il prodotto ci viva dentro**. La
`ProofSession` funziona anche dove l'iframe interattivo non funziona: il degrado a superficie non
interattiva è un percorso progettato, non un guasto.

**FR coperti:** FR-20, FR-21, FR-45, FR-48

**Stato brownfield:** tutto **MISSING**. `adapters/` è un pacchetto vuoto. Vincolo: **nessuna logica
di prodotto dentro il widget** — il core sta nelle API di dominio, la superficie assistente è un
adapter.

---

### Epic 7: Il banco del docente

**Gate primario: E** (ricavo B2B) · Gate secondario: **A**

Un docente genera dodici varianti verificate del proprio tema d'esame, **e vede anche quelle
scartate perché non verificate, con il motivo**. Un generatore che consegna 12 su 15 senza dirlo è un
generatore di cui non ci si fida.

**FR coperti:** FR-22, FR-23, FR-24, FR-25

**Stato brownfield:** generatori dell'insieme di riferimento **SATISFIED come infrastruttura**
(`eval/generator*.py` producono già casi verificati con risposta nota) · superficie Studio, banco,
vincoli di generazione, fogli soluzione **MISSING**.

---

### Epic 8: Identità, crediti e dati

**Gate primario: E** · Gate secondario: nessuno

L'utente prova il prodotto **senza registrarsi**, paga solo per ciò che ha ricevuto — un Rifiuto non
consuma Crediti — e in ogni momento sa cosa il sistema conserva di lui e per quanto.

**FR coperti:** FR-26, FR-27, FR-28, FR-29, FR-30, FR-31, FR-32, FR-33, FR-36

**Stato brownfield:** tutto **MISSING**. Nessun incasso prima del verdetto di Gate A (PRD §7.0):
questa epica **non si costruisce prima**.

---

### Epic 9 (differita): Oltre il continuo — transitori reali

**Gate primario: G** (secondo dominio) · Gate secondario: **A**

Lo studente vede il circuito **cambiare nel tempo**: la configurazione prima della commutazione, la
grandezza di stato che deve restare continua attraverso il confine, il circuito a `0⁺`, il regime, e
la costante di tempo con il circuito da cui si ricava.

Caso dimostrativo prioritario: *«Hai posto v_C(0⁺)=0, ma dal circuito per t<0 risulta v_C(0⁻)=5 V, e
la tensione del condensatore è continua.»*

**FR coperti:** nessuno in proprio — **estende** FR-10, FR-14, FR-39, FR-43 al dominio dinamico.

**Stato brownfield:** transitori **PARTIAL e solo a stato zero** — `domain/transient.py::initial_state`
sostituisce gli accumulatori con valore `ZERO` e la sua docstring dichiara *«a t = 0+, a stato zero»*.
Condizioni iniziali non nulle, commutazione, epoche topologiche e invarianti di stato attraverso il
confine: **MISSING**. Il contratto `Delta` è stato progettato per **non** rappresentarli: la
transizione temporale si comporrà accanto, non dentro.

---

### Epic 10 (differita): Oltre il continuo — regime sinusoidale

**Gate primario: G** · Gate secondario: **A**

Lo studente vede il passaggio **al dominio dei fasori** come un cambio di rappresentazione dichiarato,
non come una trasformazione fisica del circuito, e il ritorno nel tempo alla fine.

**FR coperti:** nessuno in proprio — **estende** FR-10, FR-14, FR-39, FR-43.

**Stato brownfield:** `solve_phasor` e `mna_matrix_at` **SATISFIED** · convenzione RMS/picco **MISSING
dall'IR** — nulla distingue un'ampiezza di picco da un valore efficace · fase limitata ai **multipli
di 30°** (`Cyc12` è l'anello ciclotomico dodicesimo, `phase_steps` è un intero): un fasore a −18° non
è rappresentabile in aritmetica esatta · proiezione di dominio come primitiva **MISSING**.

---

## Nota sulla risoluzione delle storie

Le storie di **Epic 0, 1 e 2** — il percorso critico verso Demo 0 e la USP — sono scritte alla
risoluzione piena richiesta dal Loop Kirchhoff v3: valore, ambito, non-goal, autorità
architetturale, realtà brownfield, dipendenze, criteri di accettazione, verifica, **controllo
dell'oracolo** ed evidenza. Ognuna è consumabile da un agente a **contesto fresco** senza conoscere
questa conversazione.

Le storie di **Epic 3–10** sono enumerate con titolo, user story e criteri essenziali. Il dettaglio
pieno si scrive **all'ingresso nello sprint**, non adesso: scriverlo oggi produrrebbe esattamente il
drift che questo passo 6 è servito a chiudere.

---

## ⚠️ Disambiguazione: due cose si chiamano «Studio»

Il nome collide, e la collisione può generare la storia sbagliata.

| Nome | Cos'è | Stato brownfield |
|---|---|---|
| **Studio** (PRD, Epic 7) | la **superficie B2B per il docente** — banco esercizi, generazione di Varianti, fogli soluzione | **MISSING** come superficie di prodotto |
| **`~/whiteboard-studio/studio`** | l'applicazione React/Vite esistente — Excalidraw, MathLive, pdfjs, `JournalRecorder`, `ReplayEngine`, `WorkspaceStore`, `toolhost`, bundle `.lesson` | **ESISTE**, 88 test verdi |

**Nessuna storia di questo backlog dice «costruisci Studio».** Ciò che manca non è l'applicazione:
è **l'integrazione e la shell specifiche di CircuitCheck** sopra capacità che esistono già.
Caricamento di immagini e PDF, replay deterministico, composizione di formule, persistenza,
esportazione a pacchetto e superficie a tool ospitati sono **capability disponibili da adattare**,
non da riscrivere. Da costruire ci sono i token della UX v3, i diciannove componenti propri, il
`proofgraph-rail`, la `step-card` e il pannello dei residui — perché *«nessun sistema di UI di terze
parti»* vale per i componenti centrali, non per l'infrastruttura sotto.

---

## Epic 0: L'esecuzione del metodo

**Non ha valore utente, e lo dichiara.** È la condizione perché tutto il resto venga costruito dal
loop invece che da una conversazione. Non copre alcun FR e non compare nella mappa di copertura.

Il metodo esiste già come `.claude/loop.md` — *Loop Kirchhoff v3*, 396 righe, costruito sul modello
operativo usato per Ardesia. Quello che manca è che sia **eseguibile e ispezionabile da shell**.

### Story 0.1: Preflight dell'installazione BMAD

As a chi avvia il loop,
I want sapere prima di partire se questa installazione BMAD può davvero eseguire un ciclo completo,
So that non scopro al primo build automatico che manca un requisito di runtime.

**Contesto autoritativo:** `_bmad/config.toml` esiste alla radice; `_bmad/scripts/resolve_customization.py` e `_bmad/bmm/config.yaml`, che le skill v6.11.0 si aspettano, **non esistono**. Il `bmad-build` renderizzato è in `_bmad/render/bmad-build/kirchhoff-d07b09e6efac/`. Il fallback di risoluzione previsto dalle skill ha funzionato per il passo 6, ma non è stato provato per il build.

**Non-goal:** reinstallare o aggiornare BMAD. Prima si misura perché l'installazione è parziale.

**Acceptance Criteria**

**Given** l'installazione corrente
**When** si esegue il preflight
**Then** riporta, per ciascuno, presente o assente con il percorso esatto: risoluzione del workflow · risoluzione della customizzazione · risoluzione del config · handoff di implementazione a contesto fresco · handoff della review Blind Hunter · aggiornamento dello stato di storia · comandi di verifica · handoff di commit
**And** esce diverso da zero se anche uno solo dei requisiti di runtime del build manca
**And** non modifica nulla.

**Verifica:** esecuzione reale, exit code letto senza pipe. **Oracolo:** il preflight deve essere visto fallire su un requisito rimosso apposta, altrimenti è verde per costruzione. **Evidenza:** output completo con exit code.

### Story 0.2: `doctor`, `status` e `dry-run` da riga di comando

As a proprietario del progetto,
I want interrogare lo stato del loop da terminale senza aprire una sessione di modello,
So that posso sapere dove siamo e cosa succederebbe, prima di lasciarlo lavorare.

**Contesto autoritativo:** lo stato **non vive nella memoria della sessione**. Le fonti sono `bmad-chain-status.json` (`scripts/bmad_chain.py`), `sprint-status.yaml`, git, e le ricevute di evidenza.

**Ambito:** un entrypoint CLI che riusa `bmad_chain.py` invece di duplicarne la logica.
- `doctor` — i controlli della Story 0.1 più: git in uno stato accettabile, deny sull'holdout attivo, measurement gate attivo, boundary gate e domain-coverage gate invocabili, nessuna storia illegittimamente `ready-for-dev`.
- `status` — passo di catena, sprint, epica, storia, stato, ultimo gate verde, ultimo commit, blocco corrente, **prossima azione permessa**.
- `dry-run` — *«se partissi ora eseguirei X perché Y»*, con i gate che girerebbero e la stop condition che potrebbe fermarli. Non modifica nulla.

**Non-goal:** implementare `run` e `resume`. Non introdurre Redis, Temporal, code, database o servizi in background.

**Acceptance Criteria**

**Given** un repository in uno stato qualsiasi
**When** si esegue `doctor`
**Then** ogni controllo riporta esito e percorso, e l'exit code è diverso da zero se un controllo bloccante fallisce
**And** `status` ricostruisce lo stato **solo** da artefatti su disco e git
**And** `dry-run` nomina la prossima storia eleggibile e **la ragione** della sua eleggibilità
**And** `dry-run` lascia il working tree e gli artefatti byte-identici.

**Verifica:** `git status --porcelain` vuoto dopo `dry-run`. **Oracolo:** `status` deve essere visto riportare un blocco reale — si porta lo sprint in uno stato bloccato e si verifica che lo dica. **Evidenza:** le tre uscite salvate.

### Story 0.3: `run` e `resume`

As a proprietario del progetto,
I want lanciare il loop e ritrovarlo al punto giusto dopo un'interruzione,
So that lo sviluppo ordinario proceda senza una lunga conversazione manuale.

**Contesto autoritativo:** la gerarchia è `CLI → Loop Kirchhoff v3 → stato BMAD → storia ready-for-dev → bmad-build → contesto fresco → test e gate → Blind Hunter → fix → riverifica → evidenza → stato → commit → prossima storia`. **Il CLI orchestra BMAD, non lo scavalca.**

**Prerequisito di indagine:** confronto esplicito fra il loop Ardesia degli ultimi giorni, `Loop Kirchhoff v3` e BMAD v6.11.0, con classificazione `REUSE / ADAPT / DROP / MISSING` per: entrypoint · status · run · resume · wakeup · recupero dello stato · ricevute · retry · handoff a contesto fresco · review indipendente · esecuzione dei gate · commit · stop condition · automiglioramento. **Riusare ciò che ha funzionato per Ardesia, non reinterpretarlo.** `~/ardesia-loop-control-plane-v2` è **fonte di studio, mai dipendenza di runtime**.

**Non-goal:** un secondo scheduler. Se `ScheduleWakeup` è già il meccanismo di continuazione, si riusa.

**Acceptance Criteria**

**Given** una storia `ready-for-dev` e i gate verdi
**When** si esegue `run`
**Then** il ciclo procede fino al commit **senza chiedere conferma per passaggi già governati da BMAD**
**And** si ferma **solo** per: `OWNER_DECISION`, `ARCHITECTURE_CONFLICT`, `BREAKING_CONTRACT`, `READINESS_FAILURE`, `REPO_INTEGRITY_RISK`, `HOLDOUT_OR_SECRET_RISK`, `PRODUCT_KILL_CRITERION`, `UNRECOVERABLE_INFRA_FAILURE`
**And** **non** si ferma per un test rosso, un rilievo di review, un bug, un lint o un debito non bloccante — quelli sono parte dell'iterazione

**Given** un loop interrotto a metà iterazione
**When** si esegue `resume`
**Then** lo stato è ricostruito da git, artefatti BMAD, `sprint-status.yaml`, `bmad-chain-status.json` ed evidenze — **mai dalla memoria del modello**
**And** il lavoro riparte dal punto giusto senza ripetere ciò che era già committato.

**Verifica:** interruzione reale con `SIGINT` a metà iterazione, poi `resume`. **Oracolo:** dopo `resume` in una sessione nuova senza contesto, lo stato ricostruito deve coincidere con quello prima dell'interruzione. **Evidenza:** log delle due esecuzioni e diff dello stato.

---

## Epic 1: La derivazione che si vede e che si può controllare

**Gate A — kill criterion.** FR-15, FR-34, FR-37…FR-41, FR-43, FR-46, FR-47, FR-49, FR-50, FR-53.
UX-DR7…UX-DR13, UX-DR17…UX-DR19, UX-DR25.

### Story 1.1: L'identità preservata dev'essere giustificata, non dichiarata

As a chi si fida di una derivazione,
I want che un'entità risulti preservata solo se è davvero la stessa entità semantica,
So that una trasformazione non possa far apparire preservata un'entità nuova riusandone l'identificatore.

**Il difetto, verificato il 24/08/2026:** AD-22 chiude una direzione sola — *«un controllore strutturale confronta `Cₖ` e `Cₖ₊₁` per identità e rifiuta se un'entità presente in entrambi compare in `create`»* — ma `Pₖ` è **l'intersezione per identificatore**. Se una trasformazione battezza `R1` la nuova resistenza equivalente, `R1` compare in entrambi i circuiti e **risulta preservata**.

**Perché blocca:** `Pₖ` è l'ingresso di VCER, della codifica di braccio e di A-0. Un `Pₖ` falsificabile rende il verdetto di Gate A **leggibile e falso** — CV1: *«un bug che si legge come dato»*.

**Autorità:** AD-22 em. · CV1 · CV3 · CV5 (*«il vincolo non è nel tipo»*: guardia a runtime + test, mai annotazione).

**Non-goal:** `preserved == immutable`. CV3 stabilisce che preservato e boundary coesistono e che una preservata **può** cambiare proprietà entro la semantica della trasformazione.

**Brownfield:** `domain/transform/delta.py` e `check.py` esistono (`ad29c8e`), con `preserve_set` calcolato dai due circuiti. Manca **solo** la giustificazione dell'identità.

**Dipendenze:** nessuna. È la prima.

**Acceptance Criteria**

**Given** una trasformazione che produce un'entità nuova riusando l'identificatore di una consumata
**When** il controllo gira
**Then** viene rifiutata
**And** il rifiuto nomina l'entità e la trasformazione

**Given** un'entità realmente preservata che cambia una proprietà **ammessa da quella trasformazione**
**When** il controllo gira
**Then** passa
**And** il `Certificate` porta l'attestazione dell'identità per il caso non banale

**Given** una derivazione `{R1, R2} → {Req}`
**When** il controllo gira
**Then** `Req` ha identità nuova e lineage nel `Delta`, e **non** compare in `Pₖ`.

**Verifica:** `pytest`, `check_domain_coverage`, `check_boundaries`. **Oracolo:** il test negativo va **visto rosso** rimuovendo la guardia, e il rosso dev'essere un fallimento di asserzione — non `exit 4` da errore d'uso né `127` da comando inesistente (debito `2-4d`). **Evidenza:** output della mutazione e del ripristino.

### Story 1.2: Il vocabolario chiuso delle riscritture strutturali

As a chi legge un `Delta`,
I want che ogni derivazione porti un'operazione da un vocabolario chiuso di primitive strutturali,
So that il catalogo pedagogico non venga contaminato da micro-operazioni e K-0 non imponga un fotogramma a ognuna.

**Contesto:** il catalogo attuale nomina **passi didattici** — `serie`, `parallelo`, `resistenza_equivalente_di_thevenin`, `circuito_equivalente_a_t0` — mentre `REMOVE_LOAD` o `ZERO_VOLTAGE_SOURCE` sono **sotto-passi**. Oggi `StructuralDerivation.operation` punta al catalogo pedagogico: è il livello sbagliato.

**Prerequisito obbligatorio — search-before-build:** cercare per concetto in PRD, spine, UX, `KIRCHHOFF-KNOWLEDGE`, memlog, review e codice: *primitive · rewrite · graph edit · internal transform · source suppression · reduction · substep · micro-step · atomic transform · edit script · operation vocabulary*. **Se un'autorità esiste, si riusa.** Solo se manca si crea.

**Non-goal:** aggiungere `REMOVE_LOAD` al catalogo pedagogico. K-0 governa il livello pedagogico.

**Acceptance Criteria**

**Given** la ricerca conclusa
**When** non emerge alcun vocabolario autoritativo
**Then** ne nasce uno chiuso, distinto dal catalogo pedagogico, con un test che rifiuta ogni operazione fuori insieme

**Given** una trasformazione pedagogica composta da più riscritture
**When** produce il `TransformResult`
**Then** il `Delta` porta più `StructuralDerivation`, e resta **un solo** passo pedagogico.

### Story 1.3: Un `LayoutIR` recuperabile per ogni stato visuale

As a chi deve emettere il verdetto di Gate A,
I want poter osservare insieme `LayoutIR_k` e `LayoutIR_{k+1}`,
So that VCER sia calcolabile e la continuità visuale misurabile invece che asserita.

**Il difetto, CV6:** `AD-8` nomina lo scrittore e **tace sulla ritenzione**; le convenzioni elencano i prefissi `ir_`, `sol_`, `var_`, `evt_` e **nessun `lay_` o `patch_`**; `ProofSession` porta **un** identificatore di `LayoutIR`, non uno per nodo; l'ERD non conosce l'entità. *«Con U2, `p_k` non esiste più nel momento in cui servirebbe misurarlo.»*

**Direzione decisa dall'owner:** `LayoutIR` **immutabile e versionato per ogni stato visuale persistente**, append-only per l'intera sessione. **Ma il proprietario del riferimento va cercato**, non presupposto: `ProofGraph`, nodo di timeline, stato di replay o struttura già prevista — non si patcha `ProofSession` solo perché è il primo posto disponibile.

**Non-goal:** decidere il renderer. Questa storia rende **osservabile**, non disegna.

**Acceptance Criteria**

**Given** una derivazione di due passi
**When** si chiede lo stato visuale del passo `k` dopo che `k+1` è stato prodotto
**Then** `LayoutIR_k` è ancora recuperabile e non è stato sovrascritto
**And** `LayoutIR` e `LayoutPatch` hanno un identificatore proprio secondo le convenzioni
**And** la relazione fra nodo della derivazione e layout è interrogabile in entrambe le direzioni.

### Story 1.4: Serializzatore SVG semantico deterministico, su una fixture a soli resistori

As a studente,
I want che il circuito che vedo sia lo stesso oggetto che il sistema ha verificato,
So that il disegno faccia parte della prova e non ne sia un'illustrazione.

**Autorità:** AD-35 — `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` **pura**, stessi byte, niente orologio, niente id a runtime, **nessun ordinamento dipendente dall'inserimento in mappa**. AD-31 — l'annotazione è **derivata dalla geometria**, mai il contrario. AD-10 — l'SVG verificato è la **sorgente unica**.

**Ambito volutamente stretto:** una fixture con soli resistori e un generatore, **`LayoutIR` predefinito**. L'autolayout generale è **non-goal**: serve validare la promessa della trasformazione visuale prima di risolvere il problema del diagram layout.

**Acceptance Criteria**

**Given** lo stesso `LayoutIR`
**When** si renderizza due volte
**Then** i byte coincidono
**And** ogni componente porta `data-component-id`, ogni terminale `data-terminal-*`, ogni nodo `data-node-id`
**And** nessun attributo di identità è scritto a mano: è derivato dalla geometria emessa
**And** ogni disegno porta l'alternativa testuale della **topologia** (UX-DR25, FR-15).

**Oracolo:** il test di determinismo va visto rosso introducendo un ordinamento dipendente da un dizionario.

### Story 1.5: Il recinto `render/ → adapters/` nasce con `render/`

As a chi mantiene l'architettura,
I want che il recinto 4 di AD-21 sia installato nella stessa iterazione che crea `render/`,
So that non nasca un confine dichiarato e non verificato.

**Legge del progetto:** *«un gate scoperto ma non cablato non esiste»*. Oggi `check_boundaries.py` ha un solo recinto e non scandisce `render/`.

**Acceptance Criteria**

**Given** `render/` esistente
**When** gira il controllo dei confini
**Then** un import da `render/` verso `adapters/` fallisce il gate
**And** il gate solleva se puntato su una radice inesistente, invece di dichiarare tutto pulito.

### Story 1.6: Round-trip semantico — l'SVG riparsato deve ridare il circuito

As a chi mostra un Badge Verificata,
I want che il disegno consegnato sia lo stesso che è stato certificato,
So that «verificato» non significhi «verificato altrove».

**Autorità:** FR-41 (il round-trip è il controllo **primario** della topologia, non un modello che dice «sembra giusto») · AD-31 (incidenza geometrica, sesto controllo di `publish()`) · AD-19 (`render_roundtrip` come causa di `Refusal`).

**Acceptance Criteria**

**Given** un SVG semantico emesso
**When** viene riparsato e canonicalizzato
**Then** il grafo ricostruito coincide **esattamente** con il `CircuitIR` atteso
**And** un filo attaccato al piedino sbagliato **con l'attributo giusto** viene rifiutato dall'incidenza geometrica
**And** il fallimento produce `Refusal.cause = render_roundtrip`.

### Story 1.7: La prima trasformazione pedagogica, fino al disegno

As a studente,
I want vedere due resistenze in serie diventare la loro equivalente **restando dov'erano**,
So that pensi «quelle due sono diventate questa» invece di «mi hanno mostrato un circuito nuovo».

**Perché `serie`:** è la più semplice del catalogo pedagogico esistente. `REMOVE_LOAD` **non** è nel catalogo ed è una primitiva strutturale, non un passo didattico.

**K-0 come criterio di accettazione:** la storia **non è completa** se produce solo `CircuitIR_before → CircuitIR_after`. Deve arrivare allo stato visuale verificato.

**Acceptance Criteria**

**Given** un circuito con `R1` e `R2` in serie
**When** si applica `serie`
**Then** il `TransformResult` porta `PreserveSet`, `Delta`, `Boundary`, `LayoutPatch`, `Equation` e `Certificate`, tutti non vuoti
**And** il `Delta` contiene `{R1, R2} → {Req}` con lineage interrogabile nelle due direzioni
**And** nel disegno risultante **ciò che appartiene a `preserve` non si è mosso** (A-0)
**And** l'equazione `R_eq = R1 + R2` compare **accanto** al sottografo, non sotto il disegno (UX-DR10)
**And** il sottografo evidenziato compare **prima di qualunque testo** (UX-DR8).

### Story 1.8: Visual Slice 0 — prima, azione, dopo, e ripercorribile

As a studente,
I want percorrere avanti e indietro il passaggio,
So that possa fissare il cambiamento premendo più volte invece di guardarlo una volta sola.

**Acceptance Criteria**

**Given** la derivazione a un passo della Story 1.7
**When** si commuta *Prima ↔ Dopo*
**Then** la commutazione è istantanea, ripetibile all'infinito e senza conferma (UX-DR12)
**And** toccando `Req` si vede da cosa deriva, toccando un nodo preservato si vede che è lo stesso
**And** «Perché posso farlo?» risponde con **quattro campi già calcolati** e **non genera prosa** (UX-DR23)
**And** lo stesso passo è renderizzabile in forma statica per l'export, dalla **stessa** sorgente semantica (AD-10).

### Story 1.9: Determinismo del rendering come famiglia di test obbligatoria

As a chi legge VCER,
I want che due rendering identici siano identici byte per byte,
So that round-trip, incidenza e non-occlusione non siano test intermittenti.

**Autorità:** AD-35 — *«un rendering che varia fra due esecuzioni rende rosso a caso ogni controllo che confronta due rendering, e la reazione naturale a un test intermittente è spegnerlo»*. Il fallimento è **di CI, non un `Refusal`**.

**Acceptance Criteria**

**Given** lo stesso ingresso
**When** si renderizza due volte in processi separati
**Then** i byte coincidono
**And** il test appartiene alle famiglie obbligatorie e la sua assenza fa fallire il controllo di completezza (FR-46).

---

## Epic 2: «Fammi vedere cosa hai fatto»

**Gate B, e la ragione per cui CircuitCheck esiste.** FR-17, FR-35, FR-44 · UX-GAP-01.

### Story 2.1: `StudentTrace` — il modello minimo, con gli stati di lettura

As a studente,
I want che il sistema rappresenti quello che ho scritto **prima** di giudicarlo,
So that non venga confuso «non riesco a leggere questo» con «questo è sbagliato».

**Autorità:** FR-44 — *«lo riceve come struttura semantica — passi, equazioni, grandezze dichiarate — e non come fotografia»*, e *«il verifier non accetta un'immagine come `StudentTrace`: l'eventuale conversione avviene prima ed è un altro stadio, con il proprio esito di fallimento»*.

**Vincolo di naming:** il nome autoritativo è **`StudentTrace`**. Search-before-build prima di introdurre qualunque altro tipo.

**Ambito:** uno `StudentStep` porta almeno regione di provenienza, trascrizione, forma matematica normalizzata, intento inferito, entità bersaglio, convenzioni dichiarate, confidenza e **stato di lettura**. Gli stati sono **strutturalmente distinti**: `valid · invalid · ambiguous · unreadable · unsupported`.

**Il principio, come criterio di accettazione di sistema e non come frase di prompt:** **illeggibile ≠ sbagliato.** Deriva da una lezione misurata dell'error ledger — *«un file che non compila somiglia a un test rosso e non lo è»*.

**Non-goal:** OCR, percezione, fotografia. L'ingresso è strutturato.

**Acceptance Criteria**

**Given** un passo con confidenza insufficiente
**When** il sistema lo classifica
**Then** lo stato è `unreadable` o `ambiguous`, **mai** `invalid`
**And** il messaggio dice *«non riesco a leggere con sicurezza questo passaggio»*, non *«questo passaggio è sbagliato»*
**And** la confidenza è esposta come stato comprensibile, non come numero decimale (UX-DR: *Letto chiaramente · Controlla questo · Non sono sicuro*)

**Given** un'immagine passata come `StudentTrace`
**When** il verifier la riceve
**Then** la rifiuta con un esito di fallimento proprio, distinto da un errore del procedimento.

### Story 2.2: Allineamento passo per passo col `ProofGraph`

As a studente,
I want che il sistema confronti il **mio** procedimento con la derivazione verificata,
So that mi dica dove ho deviato e non solo se il risultato finale è giusto.

**Autorità:** FR-44 — *«confrontabile col `ProofGraph` di riferimento **passo per passo**, non solo sul risultato finale»*. È una conseguenza testabile del PRD, non un'invenzione.

**Non-goal:** giudicare. Questa storia **allinea**; la successiva decide.

**Acceptance Criteria**

**Given** uno `StudentTrace` e la derivazione verificata dello stesso esercizio
**When** gira l'allineamento
**Then** ogni passo dello studente è associato a un'operazione sul circuito, a un'equazione o a una scelta di metodo — oppure marcato come non allineabile
**And** un metodo **diverso ma valido** viene allineato, non respinto: se lo studente usa le maglie dove il riferimento usa la nodale, il procedimento resta corretto.

### Story 2.3: Il primo passo non valido

As a studente,
I want vedere dove il ragionamento ha smesso di essere valido,
So that possa correggere il pensiero invece del numero.

**Il primo caso, deliberatamente semplice:** lo studente riduce come serie due resistenze che **topologicamente non lo sono**.

**Acceptance Criteria**

**Given** uno `StudentTrace` con un passo la cui operazione dichiarata è incompatibile col circuito
**When** gira il rilevatore
**Then** indica **il primo** passo non valido e si ferma lì, perché tutto ciò che segue potrebbe dipenderne
**And** «mostrami comunque tutti gli errori» è disponibile ma **non è il default**
**And** classifica l'errore per genere: segno, topologia, KCL/KVL, modello, scelta del metodo, algebra, valore copiato

**Given** un procedimento in cui due errori di segno si compensano e il risultato finale è corretto
**When** gira il rilevatore
**Then** **non** dichiara il procedimento corretto: segnala che il valore coincide ma il passaggio `k` non è valido

**Given** un procedimento interamente corretto
**When** gira il rilevatore
**Then** non indica alcun errore.

### Story 2.4: Il tasso di falsa accusa come metrica di prima classe

As a proprietario del prodotto,
I want che accusare a torto sia molto peggio che non sapere,
So that lo studente possa fidarsi della correzione.

**Ambito:** un corpus di casi difficili — procedimenti corretti · metodi alternativi validi · passaggi illeggibili · convenzioni diverse ma coerenti · risultato corretto da ragionamento non valido · risultato errato con percorso corretto fino al passo in esame. Più le metriche: indice del primo errore, **tasso di falsa accusa**, correttezza del rifiuto, tasso di ambiguità.

**Acceptance Criteria**

**Given** il corpus dei casi difficili
**When** gira la misura
**Then** il tasso di falsa accusa è riportato separatamente e non aggregato in un punteggio unico
**And** su un procedimento corretto il sistema **non** indica errori
**And** quando l'evidenza non basta, dichiara *«non ho evidenza sufficiente per dirti dove hai sbagliato»* invece di indicare un passo.

**Oracolo:** il corpus deve contenere casi che il rilevatore **sbaglia**, altrimenti non misura nulla.

### Story 2.5: «Fino a qui corretto. Qui cambia il ragionamento.»

As a studente,
I want vedere l'errore **sul circuito** prima di leggerne la spiegazione,
So that lo capisca guardando invece che leggendo.

**Autorità:** UX-DR8 (il sottografo prima del testo) · UX-DR20 (*Non certificata* e *Guasto* non si assomigliano mai) · UX-DR31 (**mai il rosso** per il rifiuto) · K-5 (nessun punteggio sulla persona).

**Acceptance Criteria**

**Given** un primo errore individuato
**When** viene presentato
**Then** il ramo o il nodo coinvolto si evidenzia sul circuito **prima** che compaia il testo
**And** il passo dello studente e l'elemento del circuito sono evidenziati insieme
**And** la spiegazione breve precede quella estesa, che si apre a richiesta
**And** «Fammi vedere» apre la trasformazione visuale della Epic 1
**And** un passaggio ambiguo usa un trattamento visivo **diverso** da un passaggio errato.

### Story 2.6: «Guidami» — la modalità che non rivela

As a studente,
I want provare io il passo successivo prima che me lo mostrino,
So that scopra il metodo invece di leggerlo.

**Autorità:** FR-17 · KF-4 · K-5 — nessun punteggio, nessuna percentuale, nessun registro.

**Acceptance Criteria**

**Given** una derivazione in modalità Studio
**When** lo studente sbaglia la trasformazione proposta
**Then** prima di rivelare, il sistema mostra **perché** non è applicabile, evidenziando la condizione violata sul disegno
**And** nessuno stato prosegue da solo dopo un timeout
**And** non viene registrato né mostrato alcun punteggio.

### Story 2.7: Segnalare un errore del sistema

As a studente,
I want dire al sistema che si è sbagliato,
So that il mio caso diventi una fixture invece di restare un aneddoto.

**Acceptance Criteria**

**Given** una correzione che lo studente ritiene errata
**When** la segnala
**Then** la segnalazione porta con sé lo `StudentTrace`, il circuito e la derivazione verificata
**And** entra in un percorso che può trasformarla in caso del corpus (FR-46: *«ogni fallimento sfuggito diventa fixture o invariante permanente»*).

---

## Epic 3: Dal foglio fotografato al circuito confermato

**Gate C.** FR-1…FR-9, FR-52. **Non è prerequisito di Epic 2.**

- **Story 3.1** Ingestione multi-formato e selezione dell'esercizio quando la foto ne contiene due — il sistema **non sceglie mai e non fonde mai**.
- **Story 3.2** Estrazione multi-pass con misura dell'Accordo, dietro `PerceptionCandidate`; il recinto 3 di AD-21 nasce con `perception/`.
- **Story 3.3** Ridondanza testuale come secondo canale.
- **Story 3.4** Anteprima di ricostruzione con ancoraggio di provenienza **bidirezionale**; un solo controllo primario, *Confermo*.
- **Story 3.5** Domanda mirata con ritaglio ingrandito in cima, **tetto di due giri con contatore visibile**, poi degrado all'editor.
- **Story 3.6** Ripresa senza perdita e senza doppio addebito.
- **Story 3.7** Editor del circuito: ogni modifica manuale resta **marcata come tale** nell'IR.
- **Story 3.8** Lo stesso percorso di conferma applicato al **procedimento**, non solo al circuito.

## Epic 4: Un numero di cui si può rispondere

**Fondazione.** FR-10…FR-14, FR-16, FR-42.

- **Story 4.1** Percorso B come esecutore del piano didattico, indipendente dal Percorso A.
- **Story 4.2** I cinque controlli come **gate unico** di `publish()`, con gli otto controlli di AD-5.
- **Story 4.3** `TruthfulnessGate` e `Claim` **cablati all'uscita**, non solo definiti (AD-32).
- **Story 4.4** Segnaposto legati allo scope del passo; uno fuori scope è **respinto** (AD-4 em.).
- **Story 4.5** Piano didattico dal catalogo chiuso — il modello sceglie il percorso, **mai il valore né la topologia**.
- **Story 4.6** Profilo curricolare — **bloccata da D2**, non entra in sprint finché D2 è aperta.

## Epic 5: Portarlo via

**Gate D.** FR-18, FR-19, FR-51.

- **Story 5.1** Export dall'SVG semantico verificato come sorgente unica; nessun secondo modello riscrive la soluzione.
- **Story 5.2** Marcatura di provenienza non rimovibile via CSS, foglio di stile di stampa incluso.
- **Story 5.3** Export CircuiTikZ **derivato** dall'SVG verificato, con i vincoli d'ambiente LaTeX già misurati.
- **Story 5.4** Registro di provenienza e licenza come oggetto versionato.

## Epic 6: Dentro una conversazione

**Gate D.** FR-20, FR-21, FR-45, FR-48.

- **Story 6.1** `ProofSession` come proiezione per riferimento, indipendente dalla superficie.
- **Story 6.2** `ProofReplay` alla larghezza minima, che **rifiuta di presentarsi** sotto una soglia invece di degradare.
- **Story 6.3** Riassunto testuale strutturato in ogni risposta — *l'assistente non vede il pannello*.
- **Story 6.4** Degrado a superficie non interattiva come percorso **progettato**.
- **Story 6.5** Collegamento dell'account **dopo** la prima Soluzione consegnata, mai prima.

## Epic 7: Il banco del docente

**Gate E.** FR-22…FR-25.

- **Story 7.1** Banco esercizi del tenant con isolamento a livello di database.
- **Story 7.2** Generazione di Varianti verificate, riusando i generatori dell'insieme di riferimento.
- **Story 7.3** Vincoli di generazione — serie E24, intervallo del risultato.
- **Story 7.4** Rassegna che mostra **anche le Varianti scartate, col motivo**.
- **Story 7.5** Fogli soluzione separati e verificabili con checksum.

## Epic 8: Identità, crediti e dati

**Gate E.** FR-26…FR-33, FR-36. **Non si costruisce prima del verdetto di Gate A.**

- **Story 8.1** Soggetto opaco, anonimo incluso, con quota.
- **Story 8.2** Ledger dei Crediti idempotente — un Rifiuto **non addebita**.
- **Story 8.3** Acquisto di Crediti e piani.
- **Story 8.4** Dichiarazione d'uso dell'IA su ogni superficie, non chiudibile.
- **Story 8.5** Ciclo di vita e minimizzazione delle immagini, TTL imposto dallo storage.
- **Story 8.6** Offuscamento delle regioni personali.
- **Story 8.7** Consenso esplicito e diritti dell'interessato.

## Epic 9 (differita): Transitori reali

**Gate G.** Estende FR-10, FR-14, FR-39, FR-43.

- **Story 9.1** Search-before-build su `circuito_equivalente_a_t0`, `t0`, `0-`, `0+`, condizione iniziale, commutazione, continuità, condensatore, induttore — **il catalogo nomina già `circuito_equivalente_a_t0`**, quindi qualcuno ha già pensato la rappresentazione pedagogica.
- **Story 9.2** Condizioni iniziali con **provenienza**: dato del testo, soluzione per `t<0`, o inferenza dal regime.
- **Story 9.3** Commutazione ed epoche topologiche; `initial_state` resta la funzione «a stato zero» e non viene estesa con un flag.
- **Story 9.4** Invarianti di stato attraverso il confine — `v_C(0⁺)=v_C(0⁻)`, `i_L(0⁺)=i_L(0⁻)` — **verificabili**, non equazioni decorative. Non dentro `Delta`.
- **Story 9.5** Costante di tempo col circuito da cui si ricava `R_eq`, e andamento sincronizzato col circuito.

## Epic 10 (differita): Regime sinusoidale

**Gate G.** Estende FR-10, FR-14, FR-39, FR-43.

- **Story 10.1** Convenzione di ampiezza esplicita nell'IR: `peak` o `rms`, dichiarata e non dedotta dal contesto.
- **Story 10.2** Fase arbitraria — analisi del vincolo `Cyc12` (fasi a multipli di 30°) e proposta che **preservi l'aritmetica esatta dove possibile**, con fallback numerico dichiarato. Non «passiamo tutto a double».
- **Story 10.3** Proiezione di dominio tempo → fasori come **primitiva distinta**, non come `Delta` strutturale: il circuito fisico non cambia.
- **Story 10.4** Ritorno nel dominio del tempo, con il `√2` gestito dalla convenzione dichiarata.
- **Story 10.5** Diagramma fasoriale quando utile, sincronizzato col circuito.
