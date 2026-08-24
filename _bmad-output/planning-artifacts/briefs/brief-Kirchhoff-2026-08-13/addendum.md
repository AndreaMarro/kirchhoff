# Addendum — Product Brief Kirchhoff

Profondità che il brief non regge ma che i documenti a valle (PRD, UX, architettura) devono
avere. Le fonti complete sono `docs/00-fonte-piano-kirchhoff.md` (v2) e
`docs/inbox/kirchhoff_01_piano_master_v3.md` (correct-course chain-top); qui si conserva solo ciò
che serve *decidere*, con il rationale delle alternative scartate.

> **Leggere prima la sezione H.** Il correct-course v3 supera parte di ciò che segue. Ogni voce
> ancora valida è confermata in H; ciò che H non conferma va verificato contro il piano master v3
> prima di essere usato a valle.

---

## A. Alternative considerate e scartate — con motivo

Queste non vanno riaperte senza un fatto nuovo. Se un documento a valle le ripropone, è drift.

| # | Alternativa | Perché scartata |
|---|---|---|
| A1 | **Confidence numerica auto-dichiarata dal VLM** come soglia ("procedi se > 0.95") | Un LLM che scrive `0.51` genera un token plausibile, non una probabilità. Non calibrata, sovra-confidente, sensibile al prompt. Il fallimento risultante è il peggiore possibile: sistema **sicurissimo e sbagliato**. Sostituita da disaccordo multi-pass + verosimiglianza deterministica + ridondanza testuale. |
| A2 | **MCP Sampling** per far generare l'LLM al client | Deprecato in MCP 2026-07-28 (SEP-2577). E architetturalmente peggiore: il costo del modello diventerebbe imprevedibile e dipendente dal client. Il server tiene le proprie credenziali di provider. |
| A3 | **`requestState` con stato inline firmato (HMAC del grafo)** | Perfettamente stateless, ma l'IR serve comunque persistito per cronologia, eval harness e fatturazione a consumo. Scelto il riferimento opaco a DB — con l'ID comunque firmato e legato alla sessione, altrimenti è IDOR. |
| A4 | **Componenti UI predefiniti (DataGrid/ActionForm)** per la MCP App | Non esistono: è una falsa affermazione diffusa da pagine SEO di bassa qualità. MCP Apps usa HTML in iframe sandboxato. Progettare su componenti inesistenti avrebbe bloccato la UI. |
| A5 | **Abbonamento mensile B2C** ✅ **CHIUSA 15 ago 2026** | Stagionalità estrema (picchi gen–feb e giu–lug, deserto ad agosto e novembre) → rimborsi, disdette, recensioni a una stella. Sostituito da crediti prepagati + Pass Sessione. **Esito v3:** resta **scartato**. §16.2 è una lista di candidati «da testare», non una decisione, e contiene già la sostituzione (pass 30 giorni + extra credits): non riapre, enumera. Ragione decisiva aggiunta: l'abbonamento è **incompatibile con l'invariante di billing owner-locked** — si paga il tempo, non le prove certificate, e «il rifiuto non consuma crediti» perde significato. L'**annuale scontato** non è scartato: copre entrambi i picchi. Vedi H.3. |
| A6 | **Modello di visione proprio** | Mesi di lavoro e dataset annotati, superato da un aggiornamento di API di terzi che non controlliamo. Il moat non è lì. |
| A7 | **Simulatore SPICE proprio** | Esiste ngspice; esiste lcapy per la parte simbolica. Nessun valore aggiunto. |
| A8 | **App native iOS/Android** | 30% di commissione, review cycle, zero acquisizione aggiuntiva a questo stadio. PWA con accesso fotocamera. |
| A9 | **Libreria pubblica di temi d'esame reali risolti** (mossa SEO ovvia) | Il tema d'esame è opera dell'ingegno del docente/ateneo. Riprodurla e diffonderla a fini commerciali non è una zona grigia ampia. Sostituita da corpus di varianti generate da noi via Studio. |
| A10 | **Funzioni valutative per istituzioni** (correzione automatica, dashboard "chi è indietro", segnalazione studenti a rischio) | Fa scattare AI Act Allegato III punto 3 → regime alto rischio: risk management, documentazione tecnica, log automatici, valutazione di conformità, banca dati UE, monitoraggio post-mercato. Per un solo-founder è un progetto a sé, mesi, cinque cifre di costi legali. Il valore economico della sola generazione+verifica è quasi identico. |
| A11 | **Stripe + registrazione OSS** al lancio | Soglia UE 10.000 €/anno di vendite transfrontaliere B2C; l'interazione fra forfettario, servizi digitali e OSS è il punto più incasinato del sistema italiano. Merchant of Record al lancio; rivalutare sopra i 60–80k € di ricavo annuo. |
| A12 | **Chat libera generalista** dentro il prodotto | Diventeremmo un chatbot peggiore di quelli gratuiti, cancellando la promessa di verificabilità che è l'unico motivo per pagare. |

---

## B. Vincoli tecnici che il PRD e l'architettura devono rispettare

### B1 — Protocollo MCP, revisione 2026-07-28
- Core **stateless**: niente handshake `initialize`/`initialized` (SEP-2575), niente
  `Mcp-Session-Id` (SEP-2567). Routing su header. Risultati di `list` cacheabili.
  Autorizzazione OAuth 2.0/OIDC.
- **Deprecati:** Roots, Sampling, Logging (SEP-2577, finestra ≥ 12 mesi). Transport HTTP+SSE
  legacy deprecato.
- Conseguenza operativa: load balancer banale, scaling orizzontale, nessuna sticky session,
  nessuno store di sessione condiviso.

### B2 — MRTR (SEP-2322), le regole non negoziabili
- `InputRequiredResult` con `inputRequests` + `requestState`; il client **ri-emette la chiamata
  originale** con `inputResponses`.
- `requestState` **firmato HMAC e legato all'utente autenticato**. Non firmarlo = IDOR sui
  circuiti di altri utenti. Buco reale, non teorico.
- TTL 15 minuti, monouso, **idempotente sui crediti** (stessa chiamata con stesso
  `requestState` non addebita due volte).
- **Massimo 2 round-trip.** Al terzo si degrada all'editor (modalità Esperto). Un'interfaccia
  che fa quattro domande viene abbandonata.

### B3 — MCP Apps (SEP-1865)
- Risorse `ui://`, associate ai tool via `_meta: { ui: { resourceUri } }`. HTML in iframe
  sandboxato. JSON-RPC su postMessage. Negoziazione `io.modelcontextprotocol/ui`.
  SDK `@modelcontextprotocol/ext-apps`.
- **Vincolo che cambia il design:** l'HTML dell'iframe **non arriva al modello** — lo vede solo
  l'utente. Ogni tool con UI deve restituire *anche* un riassunto testuale strutturato, o il
  modello non sa cosa l'utente sta guardando e non può ragionarci.
- Sandbox: niente cookie, niente localStorage, niente DOM dell'host. Lo stato vive in
  `requestState`. Accessibilità (ARIA, tastiera, contrasto) è a nostro carico — non opzionale
  per clienti istituzionali.

### B4 — Il confine dell'LLM
L'LLM fa esattamente tre cose: estrae struttura dall'immagine; sceglie la strategia didattica;
verbalizza passaggi già calcolati. **Non calcola, non giudica correttezza, non inventa valori.**
Ogni numero mostrato all'utente esce da SymPy o dal solver numerico.

Il pianificatore didattico propone una sequenza da un **catalogo chiuso** di trasformazioni
(serie, parallelo, partitore V/I, stella↔triangolo, Thévenin, Norton, Millman, sovrapposizione,
KCL nodale, KVL maglie, impedenza fasoriale, condizioni iniziali 0⁻/0⁺, regime permanente ∞,
costante di tempo τ). Il sistema la **esegue deterministicamente e verifica che porti al
risultato**; se non converge, ripiega sul piano canonico (nodale) invece di lasciare improvvisare.

### B5 — Tolleranze e gate
- Accordo fra percorso A (MNA simbolica) e B (riduzione umana): **1e-9 relativo simbolico,
  1e-6 numerico**. Discordanza → il bug è nel percorso B; **non si pubblica**, si ripiega su A
  e si segnala internamente. Ogni uso in produzione è un test di regressione sulla libreria di
  trasformazioni, la parte più fragile del codice.
- Percorso C (ngspice) opzionale ma ad alto valore commerciale verso i docenti: un terzo motore
  scritto da altri che concorda.

### B6 — Provenienza obbligatoria nell'IR
`provenance.bbox` su **ogni** componente. Senza bbox non c'è overlay sulla foto; senza overlay
non c'è né UX di conferma né human oversight per la compliance. È un requisito, non un extra.

`symbolic` accanto a `magnitude` su ogni valore: serve a (a) verificare la struttura
indipendentemente dai valori, (b) generare varianti parametriche riusando *la stessa* soluzione
simbolica, (c) mostrare formule letterali nei passaggi.

`schedule` sugli interruttori: gestisce 0⁻/0⁺/∞ con commutazioni multiple — la classe di
esercizi dove le foto ambigue fanno più danno.

`curriculum_profile`: convenzioni di segno, metodi ammessi, notazione, formato d'uscita, per
corso e ateneo. È il gancio della difendibilità.

### B7 — Stack deciso
SymPy + lcapy (simbolico) · ngspice via PySpice (numerico) · NetworkX (grafo) · FastAPI +
Pydantic · SDK MCP Python target 2026-07-28 · Postgres/Supabase region EU · object storage EU
con TTL 24–72 h · React 19 + Vite 7 + Tailwind 4 PWA · Merchant of Record · Redis+RQ (o n8n per
il non critico) · OpenTelemetry · VPS EU.

Vincoli LaTeX noti dall'ambiente esistente: **niente `lmodern`, niente babel italiano, label
CircuiTikZ con `=` racchiusi in graffe.** Se il generatore non produce LaTeX che compila al
primo colpo, non è pronto.

---

## C. Compliance — cosa deve esistere prima del primo euro

### C1 — Il calendario che conta
L'AI Act come modificato dal Digital Omnibus (Reg. UE 2026/1744, in vigore 27 lug 2026) ha
rinviato l'Allegato III **al 2 dicembre 2027**. **Non ha toccato l'art. 50, applicabile dal
2 agosto 2026**, né l'art. 4 (alfabetizzazione, in vigore da febbraio 2025). La finestra di
grazia al 2 dic 2026 per la marcatura ex art. 50(2) vale **solo per sistemi già sul mercato al
2 ago 2026**: un sistema nuovo non ne beneficia. Sanzioni fino a 15 M€ o 3% del fatturato
mondiale (PMI/startup: l'importo inferiore).

### C2 — Art. 50 in concreto
- **50(1)**: badge persistente al primo punto di contatto, non nei ToS. Anche nella MCP App e
  nel primo messaggio di ogni sessione.
- **50(2)**: XMP nei PDF (`ai_generated=true`, versione sistema, timestamp, hash IR); `data-*`
  negli SVG; header nelle risposte API; footer visibile su ogni export.
- Aderire al Code of Practice sulla trasparenza dei contenuti IA: non obbligatorio, ma è il modo
  più economico di dimostrare conformità.

### C3 — GDPR, il trattamento che conta (T2)
L'immagine di un compito può contenere nome, matricola, grafia, nome del docente. Nulla di ciò
serve. Mitigazioni obbligatorie: **cancellazione entro 24–72 h** dopo l'estrazione dell'IR;
**blur automatico** delle regioni testuali non circuitali prima dell'invio al provider; avviso
esplicito all'upload.

**T6 (miglioramento modello) è opt-in esplicito, OFF di default.** È anche argomento di vendita:
*"I tuoi circuiti non addestrano nessun modello, a meno che tu non ce lo chieda."* Posizione che
i concorrenti americani non possono assumere altrettanto credibilmente.

Sub-responsabili: DPA con ogni provider di modello, **zero data retention attiva e verificata**,
residenza UE dove esiste, strumento di trasferimento verificato **alla data del lancio** (lo
scenario cambia), elenco pubblico dei sub-responsabili con notifica preventiva.

### C4 — Minori (Italia)
L'art. 4 L.132/2025 va oltre il GDPR: l'**accesso** — non solo il trattamento — dei minori di 14
anni richiede il consenso genitoriale. Dai 14 il minore consente da sé, ma solo se le
informazioni sono "facilmente accessibili e comprensibili" → informativa in linguaggio
semplificato, separata. Il brief assume 18+ al lancio; 14+ è l'estensione, sotto i 14 è
sconsigliato (costo di compliance sproporzionato al ricavo).

### C5 — Integrità accademica come posizionamento
Lo strumento si può usare per copiare. Fingere il contrario espone al primo docente che scrive un
post arrabbiato, e i docenti hanno più megafono degli studenti. Contromisure che sono anche
marketing: modalità Studio come default educativo; policy di uso accademico pubblica e linkata;
marcatura di provenienza su ogni export (**rendi facile essere onesti e visibile essere
disonesti**); programma docenti gratuito; nessuna "modalità solo risposta" per tenant
istituzionali.

### C6 — Pacchetto documentale
Informativa privacy IT/EN (+ versione semplificata se 14–17) · ToS con esclusione uso valutativo
e età minima · cookie policy · disclosure art. 50(1) in-prodotto · marcatura art. 50(2) · registro
trattamenti art. 30 · elenco sub-responsabili · DPA con i provider + ZDR · policy uso accademico ·
system card · DPIA proporzionata (8–12 pagine) · DPA offerto ai clienti B2B · nota art. 4 ·
registro incidenti. Costo realistico legale + DPO frazionale: **1.500–4.000 €**, da trattare come
costo di lancio.

---

## D. Economia — i numeri che vincolano il prodotto

**Costo per soluzione:** 0,03–0,11 € pieno; 0,01–0,04 € con cascata modello economico → frontier
su escalation. Prezzo effettivo 0,30–0,50 €. **Margine lordo > 88%.**

> Conseguenza per il PRD: **il COGS non sarà mai il problema, il CAC sì.** Non ottimizzare i costi
> del modello prima di aver risolto l'acquisizione. K=3 pass di estrazione triplicano la spesa di
> visione e restano centesimi — è l'investimento con il ritorno più alto del sistema.

**Latenza:** budget totale **< 45 s** dal caricamento alla prima soluzione verificata, domande
incluse. Sopra i 60 s lo studente in panico apre ChatGPT. Ripartizione: preprocessing 0,3 s ·
estrazione ×3 in parallelo 3–4 s · consenso+validazione 0,05 s · solver 0,2–2 s · verifica 0,05 s
· pianificatore 1–2 s · narrazione 2–4 s · rendering 0,3 s.

**Listino.** B2C: Prova 0 € (3/mese, filigrana) · Pacchetto 10 → 4,90 € · Pacchetto 40 → 14,90 € ·
**Pass Sessione 19,90 €** (30 gg illimitati, fair use 150 — SKU principale nei picchi) · Anno
Accademico 59 €. B2B: **Tutor 39 €/mese o 390 €/anno** · Centro 149 €/mese · Dipartimento da
2.400 €/anno (senza funzioni valutative) · **Docenti 0 €**.

**Unit economics.** Pass Sessione a 25 soluzioni: margine lordo 17,35 € (87%). Tutor annuale:
margine lordo 293 € (75%), assumendo ~600 generazioni/anno e ~1,5 h di supporto.

**CAC target.** B2C organico < 3 € · B2C advertising 8–20 € su LTV 25–40 € (rapporto marginale →
**niente advertising nei primi 6 mesi**) · B2B outbound 50–150 € su LTV 800–1.500 €.

**Proiezione 12 mesi** (pessimistico / base / ottimistico): ricavo totale 1.590 € / 10.520 € /
48.060 €. Il B2B supera il B2C in tutti e tre gli scenari.

---

## E. Il gate di validazione — precede il prodotto

**Gold set:** 200 immagini reali stratificate (pulite stampate 40%, manoscritte leggibili 35%,
manoscritte difficili 15%, degradate/storte 10%). Foto scattate dagli studenti, **non scansioni
pulite di libri** — altrimenti il VSR è gonfiato e non lo scopri prima del lancio. Per ognuna: IR
gold, risultato numerico gold, sequenza didattica di riferimento. Split 120 dev / 80 held-out;
**l'held-out non si guarda mai** durante lo sviluppo.

**Baseline frontier:** tre modelli SOTA, prompt semplice, nessun nostro codice. Poi si legge il
numero:

| Baseline | Conseguenza |
|---|---|
| **> 80%** | Il prodotto non può essere "risolvo meglio". Deve essere "risolvo *e certifico*, nel formalismo del tuo corso". Ridimensiona drasticamente l'investimento in visione. |
| **50–80%** | Spazio reale. Multi-pass + validazione elettrica → 90%+; quel delta è vendibile. |
| **< 50%** | Problema più duro del previsto, alto rischio "sicurissimo e sbagliato". Parti con input strutturato assistito; la foto è un acceleratore, non un contratto. |

**Criterio di kill:** baseline > 85% *e* delta del nostro pipeline < 8 punti → il valore non è
nella visione. Si abbandona il B2C foto-based e si va diretti su Studio B2B con input strutturato.

**Casi obbligatori nell'eval del prompt di estrazione:** immagine con un valore deliberatamente
cancellato → deve emettere `null`, non indovinare; incrocio senza punto di giunzione → deve **non**
collegare; due esercizi nella stessa foto → deve elencarli entrambi.

---

## F. Go-to-market — il dettaglio che il PRD eredita

**Canali per CAC crescente:** base esistente di ~300 studenti (CAC ≈ 0, settimana 1) → gruppi di
corso Telegram/WhatsApp (0–2 €, *entra risolvendo*, non spammando) → SEO coda lunga (canale
composto, avviare al mese 2) → video brevi (2–8 €, il corpus esiste già, cambia solo il formato) →
directory MCP (volume incerto, è un'opzione non un piano) → outbound B2B (50–150 €, **la miglior
economia e senza competizione**) → advertising (mai nei primi 6 mesi).

**Il ciclo dei contenuti:** corpus LaTeX esistente → Studio genera varianti verificate → le stesse
varianti diventano (a) pagine SEO pubbliche, (b) prodotto B2B venduto, (c) demo del prodotto, (d)
artefatti legalmente sicuri perché generati da noi. **Un lavoro, quattro output.** Target 300 pagine
entro il mese 6 — non 3.000: la qualità è fattore di ranking e la revisione umana a campione è il
vincolo.

**Timing.** Il lancio B2C deve arrivare **prima** di una sessione d'esame, non durante. Da agosto
2026: engine ago–set, beta a ottobre, spinta piena a **dicembre–gennaio**.

**Messaggi da non usare mai:** "risolve qualsiasi circuito" (falso, si smonta in dieci secondi) ·
"IA avanzata / powered by AI" (messaggio di tutti, non differenzia) · "basato su MCP" nel marketing
B2C (allo studente non interessa il protocollo).

**Dichiarare i limiti è marketing.** La riga "Circuiti non lineari ✗" nella tabella comparativa
della landing non è un errore: dichiarare esplicitamente un limite aumenta la credibilità di tutte
le altre righe — stessa logica che rende credibile il badge di verifica.

---

## G. Il rischio che governa il piano

Il rischio più concreto non è tecnico né normativo: è che Kirchhoff diventi **il sesto progetto al
60%** accanto a ripetizioni, ELAB Builder, StudiaCazzo, Ghost Tutor e broker_v4.

Mitigazione strutturale: scope brutalmente ristretto (sezione Scope del brief), criteri di kill
scritti *prima* di iniziare, ripetizioni non abbandonate. **Se lo spazio non c'è, la mossa corretta
non è costruire più piano: è ridurre lo scope al solo Kirchhoff Studio** — il generatore di varianti
verificate. Più piccolo, utile al fondatore ogni settimana, economia migliore, e senza né visione né
compliance consumer.

Secondo rischio per severità: **R1, l'errore silenzioso** — una soluzione sbagliata mostrata come
verificata. Probabilità media, impatto molto alto, e distrugge in modo permanente la reputazione
presso i docenti. È la ragione per cui SER è la metrica bloccante e per cui l'anteprima si mostra
sempre.

**Nota v3.** R1 resta il rischio più severo, ma il rischio *governante* cambia: prima di poter
sbagliare in silenzio bisogna che la continuità visuale funzioni. Il primo rischio da comprare è
ora R2 del piano master — «layout persistente più difficile del previsto» — e il suo gate è il
kill criterion di Gate A.

---

## H. Delta v3 — cosa il correct-course supera e cosa conserva

Il piano master `docs/inbox/kirchhoff_01_piano_master_v3.md` è un correct-course **chain-top**:
cambia la categoria del prodotto, non un requisito. Questa sezione è l'indice del delta, non una
copia del piano.

### H.1 — Superato o reinterpretato

| Cosa | Perché non regge più |
|---|---|
| Vision centrata su «risposta verificata» | Il bene scarso non è il numero finale ma la derivazione disegnata. La verifica resta gate costituzionale, smette di essere la proposta di valore. (§0) |
| `SolutionTrace` lineare come unico modello | Sovrapposizione, Thévenin su sottoproblemi e transitori creano branch e join: serve un `ProofGraph`. (§4.1) |
| «La sequenza didattica» come terzo moat | iCircuits/autoCircuits del Politecnico di Torino è precedente rilevante: «circuiti come nodi, metodi come archi» non è proprietario. Resta requisito di prodotto, non differenziatore. (§2.1) |
| North star «soluzioni verificate a settimana» | Compatibile con un prodotto che non disegna nulla. Sostituita da VVDR. (§22) |
| Foto nella prima versione | La foto è input rischioso e non è il collo di bottiglia del valore: scende a Gate C, con held-out reale ripristinato. (§8.1, §24) |
| Il gold set fotografico come gate che precede il prodotto | Resta obbligatorio, ma è il gate di Gate C. Il gate che precede tutto è il kill criterion di Gate A. (§24) |
| Backlog B2C-pesante | I ruoli economici sono separati: B2C = acquisizione e dati, B2B = ricavo. (§16.1) |
| Truthfulness Enforcer come skill esterna | Il gate di veridicità non può dipendere da una skill esterna dentro la trusted computing base: componente proprietaria versionata, con il tipo `Claim`. (§19) |

### H.2 — Conservato esplicitamente (§25.2), non ridiscutibile

Solver deterministico · aritmetica esatta e oracolo · harness ed eval · ports-and-adapters · i
cinque controlli · semantica del rifiuto · disclosure e provenienza · concetti di entitlement ·
processo di review a contesto pulito. Sul disco: 159 test verdi, copertura 100%.

Restano validi anche i vincoli tecnici di questo addendum: **B1–B3** (MCP 2026-07-28, MRTR, MCP
Apps), **B4** (confine dell'LLM), **B5** (tolleranze 1e-9 simbolico / 1e-6 numerico e mancata
pubblicazione in caso di discordanza), **B6** (provenienza, `symbolic`, `schedule`,
`curriculum_profile` nell'IR), **B7** (stack), e tutta la sezione **C** (compliance).

### H.3 — Conflitti fra artefatti, non risolti in questo passo

| # | Conflitto | Stato |
|---|---|---|
| H3.1 | **A5 · abbonamento mensile B2C.** Addendum: scartato per stagionalità. Piano v3 §16.2: fra le opzioni da testare, senza rebuttare la stagionalità. | **CHIUSO 15 ago 2026**, decisione delegata dall'owner. Il conflitto era più stretto di come appariva: §16.2 si intitola «B2C **da testare**» ed elenca candidati — fra cui, già, `Exam Sprint: pass 30 giorni` e `extra credits per picchi`, cioè la sostituzione proposta dall'addendum. Non riapre la decisione: enumera le opzioni. **Esito:** mensile scartato · Free, Exam Sprint e crediti prepagati confermati · **annuale scontato resta da testare** (copre entrambi i picchi, la stagionalità non lo tocca; da vendere come accesso annuale *con* crediti, mai come «illimitato»). **Ragione decisiva, che il piano non aveva dato:** l'invariante di billing owner-locked — credito consumato solo su proof certificato, rifiuto che non consuma credito — è ciò che rende onesto K-3, perché fa **costare il rifiuto all'azienda**. Un abbonamento mensile fa pagare il tempo invece delle prove certificate e cancella quell'incentivo. L'invariante resta intatto e non è stato toccato. |

Un agente che incontra questo conflitto **non sceglie**: si ferma e lo segnala. È un conflitto di
piano, e si risolve con `bmad-correct-course`.

### H.4 — Vincoli nuovi che PRD e architettura devono recepire

- **`CircuitIR` e `LayoutIR` distinti.** Il primo è la verità elettrica, il secondo la verità
  visuale persistente. Il renderer non re-inferisce il circuito dal layout e non ri-layoutta
  globalmente a ogni passo. (§4.2)
- **`LayoutPatch`** con `preserve / remove / create / node_mapping / reroute_scope`. Vincolo
  formale: `p_{k+1}(x) = p_k(x)` per ogni `x ∈ preserve`. (§4.3)
- **Grammatica obbligatoria del passo:** `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE ·
  PROVENANCE`. È schema dati, non presentation design. (§5)
- **Visual round-trip** come controllo primario: SVG semantico con `data-component-id` e
  `data-terminal-*` → riparsa → `ReconstructedCircuitIR` → canonicalizzazione → confronto esatto
  di grafi. La QA percettiva è separata e non certifica la topologia. (§6)
- **`StudentTrace`** come input semantico del verifier, non come immagine. (§7.2)
- **Tre adapter, un kernel:** Web/API · MCP e MCP Apps · Ardesia. Nessun fork «Kirchhoff per
  Ardesia»; dentro Ardesia il plugin consuma ToolHost, Simulation Plugin e LessonOS senza
  duplicare auth, shell, dashboard, memoria o simulatore. (§23)
- **Metriche nuove** accanto a SER e VSR: NED, TVR, VCER, SEC, RRC, VDR, e VVDR come north star.
  Le soglie di lancio sono decisione aperta §27.6 e owner-locked. (§22)
- **Famiglie di test obbligatorie**, incluse property-based, metamorfiche, mutation testing,
  golden ProofGraph e visual round-trip. Ogni escaped failure diventa fixture o invariante
  permanente. (§21)
