# Kirchhoff — Piano master v3

**Working title:** Kirchhoff  
**Data:** 14 agosto 2026  
**Stato:** proposta di correct-course BMAD, pronta a diventare Brief/PRD/UX/Architecture/Epics  
**Metodo:** BMAD chain-top + readiness gate + loop engineering/harness engineering/graph engineering  
**Stakes:** launch commerciale, utenti paganti, dati personali, superficie MCP pubblica, possibile integrazione Ardesia.

---

## 0. Executive verdict

Kirchhoff non dovrebbe essere definito come “AI circuit solver verificato”. Quella definizione protegge un requisito importante — la separazione tra risultato plausibile e risultato verificato — ma non descrive il bene più raro che emerge dalle fonti.

Il prodotto migliore è un **Verified Visual Reasoning Engine** per problemi circuitali: la soluzione è una sequenza o, quando necessario, un grafo di stati circuitali verificati. Il disegno non accompagna il ragionamento: **è parte del ragionamento e della prova**.

La promessa non è quindi:

> “Ti do il valore giusto.”

né soltanto:

> “Ti do un valore che ha superato cinque controlli.”

ma:

> **“Puoi seguire con gli occhi come il circuito cambia; ogni trasformazione è giustificata dalla topologia corrente, ogni equazione è ancorata allo stato che la rende lecita, e ogni stato pubblicato è verificabile.”**

La verifica deterministica rimane un gate costituzionale. Il prodotto, però, è il **Visual Proof**.

### Il punto da non perdere mai

Le fonti più recenti correggono esplicitamente il framing precedente: il bene scarso non è il numero finale, ma la derivazione disegnata — circuito → trasformazione → circuito ridisegnato → equazione → ripeti. La stessa fonte riconosce che libri, chatbot e solver dedicati raramente forniscono una derivazione visuale completa e continua sul problema specifico dell'utente.

---

# 1. Problema reale

## 1.1 Job to be done

Uno studente di ingegneria non cerca necessariamente “la risposta”. Spesso cerca una delle quattro cose seguenti:

1. **Capire cosa posso fare adesso al circuito.**
2. **Capire perché una trasformazione è lecita.**
3. **Vedere come quella trasformazione cambia concretamente il circuito.**
4. **Capire dove il proprio ragionamento ha deviato.**

I normali LLM possono produrre prosa plausibile, formule e spesso anche risultati corretti. Il limite strutturale è un altro: non mantengono con affidabilità una catena lunga di trasformazioni topologiche e rappresentazioni grafiche coerenti, né garantiscono che il disegno intermedio corrisponda esattamente al grafo elettrico che stanno usando.

I libri di testo risolvono bene alcuni esempi, ma non possono fornire una derivazione completa per qualunque esercizio che lo studente porta. Un solution manual può mostrare 20–50 esercizi ben svolti dentro un corpus molto più grande. Il problema dell'utente è spesso proprio l'esercizio che non è tra quelli svolti.

## 1.2 La frase di categoria

**Kirchhoff trasforma un problema circuitale in una prova visuale interattiva e verificata.**

Non è “un chatbot per circuiti”.  
Non è “un generatore TikZ”.  
Non è “un CAS con una UI”.  
Non è “un simulatore elettronico”.

È un ambiente in cui **stato, trasformazione, disegno, equazione, evidenza e verifica** sono un unico oggetto navigabile.

---

# 2. Correzione competitiva fondamentale

## 2.1 Il Circuit Solution Tree non è nuovo

La competitive intelligence raccolta nelle fonti individua iCircuits/autoCircuits del Politecnico di Torino come precedente importante: rappresenta già una soluzione come una sequenza/grafo di circuiti e metodi, offre un catalogo molto ricco di trasformazioni e mostra ridisegni legati ai passaggi.

Conseguenza: **“circuiti come nodi, metodi come archi” non può essere presentato come moat proprietario.**

Questo è un vantaggio, non una sconfitta:

- dimostra che il paradigma è tecnicamente sensato;
- offre un riferimento scientifico/di prodotto da studiare senza confondere documentazione pubblica e proprietà intellettuale;
- sposta il moat verso problemi ancora non risolti bene in un prodotto consumer/AI moderno.

## 2.2 Moat plausibili

Il candidato moat non è una singola feature. È la combinazione di:

1. **Input arbitrario dell'utente**: foto, screenshot, PDF, LaTeX, netlist, circuito creato nell'editor.
2. **ProofGraph verificato**, non prosa generata a posteriori.
3. **Layout persistente/incrementale**: ciò che non cambia resta fermo.
4. **Visual round-trip verification**: il disegno pubblicato deve ricostruire lo stesso circuito canonico.
5. **Lavagna bidirezionale**: il tentativo dello studente diventa input semantico al verifier.
6. **Tutor contestuale sullo stato corrente**, non risposta generica.
7. **Curriculum/notation profiles**: stesso problema, metodo e notazione coerenti con corso/docente/paese.
8. **Failure corpus ed eval propri**: gli errori reali diventano harness permanenti.
9. **Distribuzione cross-host via MCP/MCP Apps** oltre alla web app.
10. **Traslabilità nativa in Ardesia** senza duplicare simulatore, memoria, auth o shell.

---

# 3. Costituzione del prodotto

Prima di PRD ed epiche fisserei invarianti che BMAD deve trattare come contratto a monte.

## K-0 — The circuit is the reasoning

Nessun passaggio materialmente necessario alla comprensione può esistere soltanto come prosa o formula quando dipende dalla topologia del circuito. Ogni trasformazione topologica produce uno stato visuale verificato.

## K-1 — Models propose; deterministic systems certify

VLM/LLM possono proporre letture, trasformazioni, classificazioni, spiegazioni e hint. Non attribuiscono lo stato `Verified` e non sono la fonte autorevole dei numeri finali quando esiste un calcolo deterministico.

## K-2 — No evidence, no claim

Ogni claim di dominio rilevante ha un riferimento a stato, elementi e regola/verifier che lo supportano.

## K-3 — Refusal is a valid output

Se una lettura, trasformazione o derivazione non può essere certificata, il sistema deve rifiutare la certificazione senza inventare. Il rifiuto è stato progettato, non un errore UX.

## K-4 — The proof is inspectable

Badge e certificazioni devono aprire la prova: residui, terminal mapping, cross-check, provenance, versioni dei verificatori.

## K-5 — Student interaction without person scoring

Kirchhoff può osservare errori e tentativi legati a un esercizio e usarli per adattare una spiegazione. Il prodotto standard non deve trasformarli in voto, rank, probabilità di successo, profilazione valutativa o decisione educativa sulla persona.

---

# 4. Modello di dominio

## 4.1 Da SolutionTrace a ProofGraph

Una semplice lista di passi non basta per sovrapposizione, Thévenin/Norton a sottoproblemi, transitori e altri metodi che creano branch temporanei.

```text
ProofGraph
├── ProofState[]
├── Transform[]
├── branch/join relations
├── Evidence[]
└── Certificates[]
```

### ProofState

```text
ProofState
├── state_id
├── CircuitIR
├── LayoutIR
├── givens
├── goals
├── known_quantities
├── derived_quantities
├── provenance_refs
└── verification_status
```

### Transform

```text
Transform
├── transform_id
├── type
├── input_state_ids
├── output_state_ids
├── target_subgraph
├── preconditions
├── preserve[]
├── remove[]
├── create[]
├── node_mapping
├── LayoutPatch
├── equation_schema
├── proof_obligations[]
└── certificate_id
```

## 4.2 CircuitIR e LayoutIR sono distinti

`CircuitIR` rappresenta la verità elettrica: componenti, porte, nodi, orientamenti elettrici, valori, source semantics.

`LayoutIR` rappresenta la verità visuale persistente: posizioni logiche, routing, label anchors, grouping e identità visuale.

Il renderer non deve re-inferire il circuito dal layout e non deve re-layouttare globalmente il circuito a ogni passo.

## 4.3 LayoutPatch

Una trasformazione visuale produce un patch locale:

```json
{
  "preserve": ["V1", "R1", "R2", "node_A", "node_B"],
  "remove": ["R3", "R4"],
  "create": ["R34"],
  "affected_region": "subgraph:R3,R4",
  "node_mapping": {"A": "A", "B": "B"},
  "reroute_scope": "local"
}
```

Principio: per gli oggetti non coinvolti si minimizza la variazione di layout. In forma ideale:

\[
\min \Delta L \quad \text{s.t.}\quad p_{k+1}(x)=p_k(x)\;\forall x\in Preserve(T_k)
\]

Il layout iniziale può usare algoritmi automatici. I layout successivi devono rispettare gli anchor.

---

# 5. Grammatica obbligatoria di ogni passaggio

Ogni passaggio importante segue:

**BEFORE + ACTION + AFTER + EQUATION + CERTIFICATE + PROVENANCE**

Non è solo presentation design: è lo schema dati.

### BEFORE

Stato circuitale corrente, con il sottografo coinvolto evidenziato.

### ACTION

Trasformazione tipata e precondizioni.

### AFTER

Nuovo stato con patch locale. Gli oggetti non toccati restano ancorati.

### EQUATION

Formula letterale, sostituzione numerica, unità e convenzioni. La formula è associata a `state_id` e `transform_id`.

### CERTIFICATE

Esempio:

```text
topology_precondition      PASS
equivalent_terminal_map    PASS
algebra                    PASS
solver_crosscheck          PASS
render_roundtrip           PASS
```

### PROVENANCE

Da dove arrivano componenti, valori, nodi e correzioni: immagine, input manuale, profilo, derivazione precedente.

---

# 6. Visual Verification Pipeline

## 6.1 Verità semantica prima della bellezza

Pipeline principale:

```text
CircuitIR + LayoutIR
        ↓
semantic renderer
        ↓
SVG / CircuitikZ / PDF
        ↓
semantic parse / structural reconstruction
        ↓
ReconstructedCircuitIR
        ↓
canonicalize
        ↓
exact / typed graph comparison
```

Il controllo primario non deve essere “il VLM dice che sembra corretto”.

## 6.2 Semantic SVG

Gli elementi renderizzati devono avere ID e metadati strutturali, ad esempio:

```html
<g data-component-id="R3"
   data-terminal-a="A"
   data-terminal-b="B">
```

Wire e junction devono essere ricostruibili.

## 6.3 QA percettiva separata

Un controllo visuale/VLM può cercare problemi che il parser semantico non vede:

- label sovrapposte;
- fili visivamente ambigui;
- junction che sembrano presenti quando non lo sono;
- testo sotto la soglia di leggibilità;
- grafico tagliato;
- differenza tra passi difficile da percepire.

Ma non certifica la topologia.

---

# 7. Due modalità prodotto

## 7.1 Risolvilo per me

L'utente fornisce il problema. Il sistema produce un ProofGraph completo e navigabile.

Interazioni fondamentali:

- precedente / successivo;
- prima / differenza / dopo;
- “perché posso fare questo?”;
- “mostra i nodi che rendono lecita la trasformazione”;
- “apri il certificato”;
- “prova tu da qui”;
- click su quantità, componente, nodo, formula.

## 7.2 Risolviamo insieme

Questa modalità può diventare il differenziatore pedagogico maggiore.

La lavagna non è un canvas indipendente. Produce `StudentTrace`:

```text
StudentTrace
├── strokes
├── text
├── equations
├── selections
├── circled_components
├── arrows
├── proposed_transformations
├── hints_requested
├── corrections
└── attempts
```

Esempio: lo studente cerchia R3/R4 e scrive `R3 + R4?`.

Il sistema traduce il gesto in una ipotesi strutturata e verifica:

```text
series_precondition   = false
parallel_precondition = true
shared_nodes          = [A,B]
```

Il tutor LLM decide la strategia esplicativa; non decide la verità elettrica.

## 7.3 Personalizzazione senza scoring della persona

Persistenza utile:

- errori osservati per concetto;
- hint usati;
- trasformazioni eseguite autonomamente;
- spiegazioni già viste;
- preferenze di notazione/lingua.

Da evitare nel prodotto standard:

- ability score;
- predicted grade;
- rank;
- automatic placement;
- proctoring/cheating score.

---

# 8. Perception: foto e documenti

## 8.1 La foto è un input rischioso, non una verità

Il vecchio change proposal aveva tolto la misura fotografica lasciando però la foto nel prodotto. Questo produce un punto cieco: un circuito letto male può essere internamente coerente e superare KCL/KVL/power.

Il correct-course deve ripristinare un eval reale della perception.

## 8.2 Pipeline

```text
image/PDF
  ↓
pre-processing
  ↓
multiple independent extraction passes
  ↓
components / text / terminals / wires
  ↓
CandidateCircuitIR[]
  ↓
agreement + deterministic validation
  ↓
ambiguity localization
  ↓
MRTR / user confirmation
  ↓
Validated CircuitIR
```

## 8.3 Dataset

Le fonti già raccolte citano dataset aperti come CGHD e Digitize-HCD e dataset non utilizzabili commercialmente come Image2Net/Fiore. Il corpus deve mantenere un registro licenze e attribuzioni.

La metà fotografica deve avere split di sviluppo e held-out reale. 30–40 immagini sono utili per smoke test o per distinguere un sistema evidentemente pessimo da uno promettente, ma non bastano a sostenere claim di SER molto basso.

## 8.4 Metriche perception

- Netlist Edit Distance / equivalente metrico strutturale;
- exact topology match;
- component value accuracy;
- terminal accuracy;
- polarity/orientation accuracy;
- ambiguity detection recall;
- silent extraction error rate.

---

# 9. Verification Engine

La verifica precedente non va eliminata; va resa infrastruttura del ProofGraph.

Possibili famiglie:

- KCL;
- KVL;
- bilancio di potenza;
- doppio percorso/solver agreement;
- physical sanity;
- transform-specific proof obligations;
- visual round-trip;
- unit/dimensional consistency;
- invariant checks per dominio.

Il badge `Verified` viene applicato soltanto quando tutti i gate richiesti per quel tipo di problema e passo passano.

Il pannello residui rimane parte importante del design: “il prodotto mostra il lavoro invece di affermarlo”.

---

# 10. Architettura software

## 10.1 Paradigma

Conservare il principio già presente nello spine: **ports-and-adapters con nucleo deterministico**.

```text
                 Web / PWA
                    │
ChatGPT Plugin ─ Surface adapters ─ Claude/MCP hosts
                    │
                  API/MCP
                    │
┌───────────────────▼────────────────────┐
│            KIRCHHOFF CORE             │
│ CircuitIR        LayoutIR             │
│ ProofGraph       StudentTrace         │
│ TransformCatalog VerificationEngine   │
│ EvidenceGraph    CurriculumProfile    │
│ LanguagePack     TruthfulnessGate     │
└───────┬───────────┬───────────┬────────┘
        │           │           │
   SolverPort   ModelPort   RenderPort
        │           │           │
   MNA/CAS/     ModelRouter  SVG/TikZ
   SPICE
```

## 10.2 Regola dura

Il dominio non importa SDK OpenAI, Anthropic, Google, Alibaba, Stripe, storage o UI host.

## 10.3 LLM boundary

Gli LLM possono:

- leggere/proporre extraction candidate;
- proporre transform;
- scegliere spiegazione/hint;
- localizzare ambiguità;
- tradurre/parafrasare;
- classificare gesture.

Non possono:

- mutare direttamente la verità canonica senza validator;
- inventare quantità mancanti;
- concedere `Verified`;
- alterare gold set o soglie;
- dichiarare equivalente un sottografo senza verifier.

---

# 11. MCP e MCP Apps

## 11.1 Terminologia onesta

“MCP 2.0” può essere un'etichetta informale, ma i documenti tecnici devono usare la specifica/versione reale, indicata nelle fonti come **2026-07-28**.

MCP non è il prodotto: è un protocollo di distribuzione e integrazione.

## 11.2 Strategia

**Web app = system of record e casa commerciale.**  
**MCP = contratto pubblico cross-host.**  
**MCP Apps = superfici interattive native dentro host compatibili.**

Non scegliere MCP-only. La relazione utente, la cronologia, billing, export, B2B e superfici più ricche devono restare controllabili sul dominio proprio.

## 11.3 Superfici MCP Apps

Creare componenti stretti e ad alto valore invece di comprimere l'intera PWA nell'iframe:

- `ProofReplay`;
- `CircuitInspector`;
- `ProofCertificate`;
- `AmbiguityResolver`;
- `WhiteboardMini`;
- `TransformChooser`;
- `VerifyMyStep`.

Ogni tool response con UI deve mantenere anche rappresentazione testuale/structured content coerente, perché il modello host deve sapere cosa l'utente sta guardando/decidendo.

## 11.4 MRTR

Usarlo per ambiguità localizzate e conferme, con:

- request state firmato;
- TTL;
- binding account/tenant;
- idempotenza;
- massimo numero di round-trip prima di degradare a editor completo.

---

# 12. Modelli e routing

## 12.1 Nessun provider come dipendenza identitaria

Il modello giusto non è quello con il benchmark più alto in assoluto. È quello con miglior **costo per Visual Proof accettato** sul tuo harness.

```text
C_VP = total inference + compute cost / verified visual proofs delivered
```

## 12.2 ModelRouter

Testare almeno:

- famiglia OpenAI frontier/cheap;
- Anthropic premium challenger;
- Gemini vision/flash;
- Qwen/Qwen-VL dove deploy/regione/licenza sono compatibili;
- Mistral/OCR come alternativa europea;
- altri provider cinesi solo dietro review privacy/transfer e senza assumere che il prezzo basso compensi la compliance.

Il router decide per task:

- extraction vision;
- OCR/text;
- transform proposal;
- tutoring;
- translation;
- clean-context review;
- coding agents interni.

## 12.3 Ensemble solo quando dimostrato

Due o tre modelli permanenti “per sicurezza” possono distruggere il margine. Usare escalation solo se l'eval dimostra che il costo marginale riduce davvero silent errors o refusal in misura sufficiente.

---

# 13. Multilingua nativa

Separare:

```text
ProofGraph       language-neutral
LanguagePack     IT / EN / ...
NotationProfile  KCL/LKC, decimal separators, symbols
CurriculumProfile methods/conventions/course constraints
LocaleProfile    units/formatting
```

Il solver non “traduce la soluzione”. Renderizza linguisticamente fatti strutturati.

Launch consigliato: italiano + inglese molto curati; espansione successiva dopo evidenza di domanda.

---

# 14. UX e Brand

Conservare il principio già forte del design: **strumento di misura, non app edtech giocosa**.

- palette quasi acromatica;
- verde solo per Verified;
- ambra per Non certificata/sospeso;
- rosso solo per vero guasto;
- blu provenance/attention;
- numeri tabulari;
- niente coriandoli, streak, classifiche, gamification;
- badge Verified sempre apribile;
- provenance a un tocco;
- mobile-first per Solve;
- Studio desktop ad alta densità.

### Hero ideale

**Il circuito è la spiegazione.**

> Ogni passaggio mostra cosa cambia, perché è valido e come è stato verificato.

La demo deve mostrare `PRIMA → trasformazione → DOPO` mantenendo fermi gli elementi non coinvolti.

---

# 15. Oggetto condivisibile: Proof Replay

Il contenuto virale/acquisitivo non deve essere un articolo SEO statico o un PDF.

Un URL pubblico/privato controllato può aprire un **Proof Replay**:

- slider degli stati;
- before/diff/after;
- formule;
- componenti cliccabili;
- certificate;
- “prova il prossimo passo”.

Il PDF rimane export. Il Proof Replay è prodotto, demo, condivisione e prova tecnica nello stesso oggetto.

---

# 16. Business model

## 16.1 Ruoli economici separati

**B2C = product-led acquisition + usage + failure data.**  
**B2B = revenue engine.**

Questo risolve la tensione rilevata dalla Quality Review, dove il PRD aveva molti più FR B2C pur dichiarando economie B2B superiori.

## 16.2 B2C da testare

- Free: pochi Visual Proof/mese;
- Student: abbonamento mensile;
- Exam Sprint: pass 30 giorni;
- annuale scontato;
- extra credits per picchi;
- credito consumato solo su proof consegnato/certificato secondo policy;
- rifiuto di certificazione non consuma credito.

Non promettere “illimitato” senza fair-use chiarissimo.

## 16.3 B2B

Feature ad alto ROI:

- import banco esistente;
- generazione varianti;
- constraints;
- review a campione;
- approve/reject/regenerate;
- bulk export;
- formalismi del corso;
- tenant library;
- provenance/audit;
- SSO/DPA più avanti.

Prezzo da validare con pilot, non da considerare deciso dal PRD.

---

# 17. Pagamenti

Non bloccare il core sul provider. Usare `BillingPort`/entitlements.

Per B2C internazionale valutare Merchant of Record per ridurre VAT/sales-tax/GST e compliance operativa; nelle fonti sono confrontati Stripe Managed Payments, Paddle, Lemon Squeezy e altri. Il confronto definitivo va rifatto sul pricing vigente al momento del lancio con una simulazione di mix geografico e ticket reale.

Per B2B preferire invoicing/contratti annuali quando possibile.

MCP/ChatGPT/Claude devono essere **canali**, non l'unico punto di checkout.

---

# 18. GDPR e AI Act — product boundary

Questa sezione è ingegneria di compliance, non parere legale. Prima del lancio commerciale serve revisione professionale.

## 18.1 Privacy by architecture

Default consigliato:

```text
upload
  ↓
temporary encrypted object
  ↓
extraction
  ↓
CircuitIR + minimal evidence crops
  ↓
confirmation
  ↓
raw source deletion according to retention policy
```

- minimizzazione;
- EU region dove richiesta/disponibile;
- retention breve e dichiarata;
- nessun training su upload per default;
- opt-in distinto per corpus;
- export/delete self-service;
- subprocessor registry;
- tenant isolation;
- log senza raw image quando non necessario.

## 18.2 AI disclosure

Mantenere disclosure persistente e provenance degli artefatti generati con assistenza AI.

## 18.3 Confine educativo

Nel prodotto standard mantenere non-goal duri:

- grading automatico degli studenti;
- admission/placement decision;
- ranking;
- predicted grade;
- cheating/proctoring score;
- teacher-facing person score.

Il tutor può spiegare un errore sul passo corrente senza trasformarlo in una valutazione della persona.

## 18.4 Minori

Per ridurre il rischio iniziale: validare prima su universitari/adulti. L'espansione a scuole/minori richiede flussi di consenso, contratto e governance dedicati.

---

# 19. Truthfulness Gate

Il “Truthfulness Enforcer” non dovrebbe dipendere da una skill esterna dentro la trusted computing base.

Implementare un gate proprietario:

```text
Claim
├── claim_type
├── state_id
├── subject_ids
├── evidence_ids
├── verifier_id/version
└── status
```

Esempio:

```text
claim: R3 and R4 are parallel
evidence: terminals(R3), terminals(R4)
verifier: same_terminal_pair
status: VERIFIED
```

La stessa filosofia governa gli agenti di sviluppo: nessun “story done” senza evidenze di test/gate.

---

# 20. Agent factory e automiglioramento

## 20.1 Sì ai loop perpetui, no alla costituzione mutabile autonomamente

Gli agenti possono modificare:

- codice;
- prompt;
- model routing;
- layout heuristics;
- UX;
- performance;
- transform ranking;
- hint policy;
- test non-protetti.

Sono owner-locked o richiedono review umana/decisione BMAD chain-top:

- definizione di `Verified`;
- holdout datasets;
- qualità minima;
- privacy invariants;
- AI Act boundary;
- billing invariants;
- retention maxima;
- counter-metrics;
- costituzione K-0…K-5.

Un sistema che può modificare autonomamente il proprio standard di verità non è automigliorante: è epistemicamente incontrollato.

---

# 21. Harness engineering

Famiglie obbligatorie:

1. unit;
2. integration;
3. property-based;
4. metamorphic;
5. mutation testing;
6. golden ProofGraph;
7. visual round-trip;
8. multimodal extraction benchmark;
9. adversarial student interaction;
10. E2E web/MCP/host;
11. tenant/security/privacy tests.

### Metamorphic examples

- commutatività del parallelo;
- translation/rotation visuale che non cambia CircuitIR;
- wire waypoint change che non cambia netlist;
- junction insertion che deve cambiare netlist;
- renaming component IDs che non cambia physics;
- equivalent transform ordering dove matematicamente permesso.

Ogni escaped failure diventa regression fixture o invariant.

---

# 22. Metriche

Conservare SER e VSR ma aggiungere metriche coerenti col nuovo prodotto:

- **NED** o equivalente strutturale extraction;
- **TVR** — Transformation Validity Rate;
- **VCER** — Visual Continuity Error Rate;
- **SEC** — Step Evidence Coverage;
- **RRC** — Render Roundtrip Correctness;
- **SER** — Silent Error Rate;
- **VDR** — Visual Derivation completion rate;
- **VVDR** — Verified Visual Derivation Rate.

North star candidata:

\[
VVDR = \frac{\text{problemi con derivazione visuale interamente certificata}}{\text{problemi accettati dal sistema}}
\]

Una derivazione conta solo se tutti i passaggi materiali hanno prova, equazioni verificate e round-trip visuale valido.

Counter-metrics:

- refusal rate non va portato artificialmente a zero;
- cost per verified proof;
- p90 latency;
- correction/ambiguity burden;
- user abandonment durante confirmation;
- visual clutter/readability failures.

---

# 23. Ardesia compatibility by construction

Kirchhoff deve nascere con kernel autonomo e tre adapter principali:

```text
Kirchhoff Core
├── Web/API adapter
├── MCP/MCP Apps adapter
└── Ardesia adapter
```

Non creare un fork “Kirchhoff per Ardesia”.

Dentro Ardesia il plugin di reasoning deve consumare:

- ToolHost;
- Simulation Plugin per circuit scene/simulation quando serve;
- LessonOS per eventi/evidence;
- host identity/storage/capabilities.

Non deve importare o duplicare:

- auth;
- shell;
- dashboard;
- memoria propria concorrente;
- simulator renderer/solver già owned dal Simulation Plugin;
- report system generale.

---

# 24. Roadmap a gate

## Gate A — Visual Proof Kernel

Structured CircuitIR → transform → local LayoutPatch → after state → equation → certificate → SVG → reparse → exact graph check → interactive ProofReplay.

Prime trasformazioni:

- serie;
- parallelo;
- partitore;
- Millman;
- Thévenin/Norton semplice.

Poi:

- superposition;
- nodal/mesh;
- first-order transient;
- AC/phasor;
- Laplace/transfer/Bode dove coerente.

**Kill criterion:** se la continuità visuale non è chiaramente migliore di un re-layout completo, non espandere il catalogo.

## Gate B — Interactive Tutor

Lavagna + StudentTrace + hypothesis verification + hint contestuale.

**Kill criterion:** se l'esperienza è sostanzialmente “chat con screenshot”, la semantizzazione non è sufficiente.

## Gate C — Perception

Foto/PDF → validated CircuitIR con benchmark held-out.

## Gate D — Distribution

PWA + remote MCP + MCP Apps + ChatGPT/Claude surfaces.

## Gate E — Revenue

B2C entitlements + B2B Studio pilot.

## Gate F — Ardesia

Plugin `io.ardesia.circuit-reasoning` + Simulation Plugin + LessonOS.

## Gate G — Horizontal proof

Dimostrare che l'astrazione State/Transform/Layout/Evidence/Verifier funziona su un secondo dominio visuale (controlli/diagrammi a blocchi è candidato naturale), senza allargare prematuramente il prodotto consumer.

---

# 25. BMAD correct-course richiesto

Il cambio è abbastanza profondo da richiedere **correct-course chain-top**, non una patch locale a FR-15.

## 25.1 Ordine

1. **Constitution / Decision log** — K-0…K-5.
2. **Product Brief update** — category, JTBD, ICP, differentiation, B2C/B2B roles.
3. **PRD v3** — ProofGraph/LayoutIR/StudentTrace/MCP/Ardesia/compliance.
4. **UX Pro update** — ProofReplay, before/diff/after, whiteboard, certificate, mobile.
5. **Architecture Spine v2** — domain types, ports, truthfulness, render roundtrip, host adapters.
6. **Epic rebalance** — visual kernel prima di perception/monetization breadth.
7. **Readiness gate** — testability, open decisions, compliance, dependency graph.
8. **Ship loop v3**.

## 25.2 Non ripianificare ciò che è valido

Riutilizzare:

- deterministic solver work;
- exact arithmetic/oracle;
- eval harness;
- ports-and-adapters;
- five-check verification;
- refusal semantics;
- disclosure/provenance;
- entitlements concepts;
- clean-context review process.

Superare/reinterpretare:

- Vision centrata solo su “verified answer”;
- FR-15 troppo debole;
- SolutionTrace lineare come unico modello;
- foto presente senza vero held-out eval;
- B2C-heavy backlog non giustificato economicamente.

---

# 26. Loop v3 BMAD + engineering loops

```text
OBSERVE
  ↓
CLASSIFY CHANGE
  ↓
if chain-top → BMAD correct-course
  ↓
SELECT HIGHEST-RISK BOTTLENECK
  ↓
STORY SPEC + acceptance→test map
  ↓
TDD BUILD IN ISOLATION
  ↓
CLEAN-CONTEXT PARALLEL REVIEW
  ↓
HARNESS / MUTATION / METAMORPHIC / VISUAL RT
  ↓
TRUTHFULNESS GATE
  ↓
SHADOW/CANARY
  ↓
MEASURE QUALITY × COST × LATENCY × UX
  ↓
RETROSPECTIVE
  ↓
escaped failure → permanent test/invariant
  └──────────────→ OBSERVE
```

Reviewer routing per diff:

- electrical/domain reviewer;
- silent-failure hunter;
- type/API reviewer;
- security/privacy reviewer;
- MCP contract reviewer;
- UI/UX Pro;
- accessibility reviewer;
- visual-continuity reviewer.

Non tutti su ogni story: il coordinator seleziona lenti necessarie.

---

# 27. Decisioni ancora aperte

Queste non vanno nascoste nel piano:

1. Nome/marchio “Kirchhoff” e disponibilità legale.
2. Primo curriculum profile reale.
3. Limite e-learning/export prioritario.
4. Exact renderer stack per interactive web vs PDF.
5. Dimensione minima held-out fotografico prima del claim commerciale.
6. Soglie VVDR/SER/RRC di lancio.
7. Provider model pool e regione UE al momento del lancio.
8. Merchant of Record definitivo.
9. Pricing test reale.
10. Policy sui proof pubblici/condivisibili e copyright dei problemi caricati.
11. Confine tra Kirchhoff core e Ardesia Simulation Plugin per schematic canvas vs breadboard/physical scene.
12. Possibile collaborazione/licenza con precedenti accademici: va valutata senza assumere disponibilità o diritti.

---

# 28. Rischi principali

## R1 — LLM frontier chiudono parte del gap

Mitigazione: investire in persisted layout, verifier, ProofGraph, interaction state e corpus di failure; non in prompt-only step generation.

## R2 — Layout persistente più difficile del previsto

Mitigazione: vertical slice stretto, local patches, hard anchors, no global relayout.

## R3 — Perception produce silent errors

Mitigazione: benchmark reale, ambiguity resolver, confirmation, refusal.

## R4 — Troppo scope

Mitigazione: prodotto verticale circuiti; orizzontalità solo nell'architettura; secondo dominio solo dopo gate.

## R5 — B2C economics deboli

Mitigazione: B2B Studio come revenue engine; B2C come acquisition/data loop.

## R6 — MCP platform dependency

Mitigazione: web app system of record; MCP come adapter; no lock-in su host.

## R7 — Agent factory degrada gli standard

Mitigazione: owner-locked constitution/holdout/thresholds; agents propose, gate decides.

## R8 — Compliance educational profiling

Mitigazione: niente person scoring/grading/proctoring nel prodotto standard; DPO/legal review.

## R9 — Founder bandwidth / Ardesia fragmentation

Mitigazione: Kirchhoff nasce come kernel/plugin alleato di Ardesia; niente duplicazione di simulator/memory/shell.

---

# 29. Cosa NON costruire ora

- marketplace di plugin Kirchhoff;
- decine di materie;
- LMS completo;
- social network;
- grading/proctoring;
- gamification;
- “AI study companion” generico;
- simulator fisico duplicato da Ardesia;
- agent framework proprietario enorme prima del Visual Proof Kernel;
- monetizzazione in-host come unica via;
- 25 MCP apps separate.

---

# 30. Definizione di successo

Kirchhoff ha raggiunto il suo primo vero milestone quando un utente può prendere un circuito strutturato, osservare una derivazione di 5–10 trasformazioni e dire, senza leggere lunghi paragrafi:

> “Vedo esattamente cosa è cambiato, perché era consentito e come so che il nuovo circuito è equivalente.”

E quando, interrompendo quel percorso e proponendo un passo sbagliato sulla lavagna, il sistema può rispondere sul **sottografo e sulla regola reale** invece di improvvisare una spiegazione generica.

Quello è il prodotto. Tutto il resto — foto, modelli, MCP, billing, export, B2B, Ardesia — amplifica quella capacità; non la sostituisce.

---

# 31. Provenienza interna del documento

Questo piano consolida e corregge, senza trattarle tutte come simultaneamente vere, le seguenti classi di fonti consegnate:

- conversazioni e note MCP Apps;
- documento “GRAFITE Piano v2” (titolo storico della fonte, non nome adottato qui);
- piano completo Kirchhoff con ricerca tecnica/compliance/business;
- PRD Kirchhoff;
- UX EXPERIENCE/DESIGN richiamati dalle fonti;
- Architecture Spine;
- Epic Breakdown;
- Sprint Change Proposal;
- Loop di costruzione v2;
- Quality Review e readiness material incorporati nelle fonti;
- note su dataset e competitive intelligence;
- stato/architettura Ardesia consultato nella conversazione corrente.

Per il testo integrale vedere `kirchhoff_00_corpus_fonti_integrali.md`.
