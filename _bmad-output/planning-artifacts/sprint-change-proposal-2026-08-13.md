# Sprint Change Proposal — 13 agosto 2026

**Portata del cambio: Moderate** (riorganizzazione di backlog).
Approvata dall'utente il 13 agosto 2026.

---

## 1. Issue Summary

**Trigger.** Prima dell'inizio di Epic 1, l'utente dichiara: *"saltiamo la parte foto reali, non
sono sufficientemente buoni i modelli di frontiera"*.

**Tipo di problema:** limitazione tecnica nota a priori — non emersa in implementazione, ma
portata dall'esperienza diretta dell'utente sul dominio.

**Contesto.** Epic 1 era stata costruita per *misurare* invece che assumere: raccogliere 200 foto
reali dagli studenti, annotarle, e misurare la baseline dei modelli frontier sullo stesso insieme.
L'utente esercita giudizio anticipato su quell'esito e chiede di saltare la misura.

**Evidenza.** Valutazione dell'utente basata sull'esperienza di dominio come tutor. Non esiste una
misura registrata: è precisamente ciò a cui si rinuncia con questa decisione, ed è registrato qui
perché la scelta resti riconoscibile come tale.

**Decisione dell'utente sulla portata**, presa esplicitamente: *si salta solo la misura; l'ingresso
da foto resta nel prodotto come pianificato.* Le due alternative offerte — degradare la foto ad
acceleratore con l'editor come ingresso primario, oppure rimandare la foto a v2 — sono state
scartate.

---

## 2. Impact Analysis

### Epic Impact

| Epica | Impatto |
|---|---|
| **Epic 1** | **Ridefinita.** Perde raccolta foto, annotazione del gold set fotografico e misura della baseline. Sopravvive come struttura di misura, con un gold set *strutturato* al posto di quello fotografico. Da 4 storie a 2. |
| Epic 2 | Nessun cambio strutturale. Guadagna rilievo: diventa la prima epica con valore di prodotto. |
| Epic 3 | **Nessun cambio**, per decisione esplicita dell'utente. Costruita senza sapere quanto renda l'estrazione. |
| Epic 4, 5, 6, 7 | Nessun impatto. |

### Story Impact

**Rimosse:** 1.1 (raccolta foto reali), 1.2 (annotazione del gold set), 1.4 (baseline frontier e
verdetto).

**Aggiunta:** una storia per il gold set strutturato — circuiti con risposta nota, generabili
invece che raccolti. Necessaria perché FR-34 richiede comunque un insieme di riferimento annotato,
e senza di esso l'harness non ha nulla da misurare.

**Rinumerate:** l'ex 1.3 (script di valutazione) diventa 1.2.

**Non toccate:** le 8 storie di Epic 3, incluse 3.3 (estrazione multi-pass) e 3.4 (ridondanza
testuale), che restano come scritte.

### Artifact Conflicts

| Artefatto | Conflitto | Azione |
|---|---|---|
| **PRD §7 callout** | Dichiara lo scope condizionato alla misura della baseline. La misura non avverrà: il callout diventa falso. | Riscrivere: la condizione è stata risolta per giudizio, non per misura. |
| **PRD §16 Q8** | "Se la baseline supera l'85%…" — domanda ormai chiusa. | Sostituire con la decisione presa e la sua data. |
| **PRD FR-34** | Richiede un gold set annotato con split sviluppo/trattenuto. Regge, ma la composizione cambia. | Amendare: l'insieme di riferimento è strutturato; annotare il limite di copertura. |
| **PRD SM-1 (SER)** | Resta la metrica bloccante ma diventa **parzialmente cieca**. | Aggiungere il limite esplicito. |
| **ARCHITECTURE-SPINE AD-15** | "L'eval harness gira sul codice di produzione" — invariante intatta. | Nessun cambio. |
| **DESIGN.md / EXPERIENCE.md** | Nessun conflitto: nessuna decisione UX dipendeva dalla baseline. | Nessun cambio. |
| **sprint-status.yaml** | Contiene le tre storie rimosse. | Rigenerare dallo script dopo l'aggiornamento delle epiche. |
| **implementation-readiness.md** | C1 (Profilo curricolare) era motivata dall'annotazione del gold set fotografico. | Aggiornare: resta aperta, ma non blocca più Epic 1. |

### Technical Impact

Nessun impatto su codice o infrastruttura: nulla è ancora implementato. L'impatto è sulla
**capacità di misurare**, non sulla capacità di costruire.

### 🔴 La conseguenza che questa scelta porta con sé

**SER diventa non misurabile sul tratto dove vive il rischio.** Con un gold set strutturato,
l'harness misura solver, Trasformazioni e Verifica — tutta la catena a valle dell'IR. Non misura
l'estrazione, perché non ci sono immagini.

E l'errore silenzioso che il prodotto esiste per prevenire nasce quasi tutto lì: leggere 30 Ω dove
c'è 20 Ω, poi risolvere impeccabilmente il circuito sbagliato. I cinque controlli non lo
intercettano — un circuito letto male è internamente coerente e supera KCL, KVL e bilancio di
potenza senza battere ciglio.

SM-1 resta la metrica bloccante del PRD e resterà cieca sul suo tratto più pericoloso finché non
esisterà un insieme di riferimento fotografico.

**Non è un'obiezione alla decisione: è il suo prezzo, scritto perché sia visibile.**

---

## 3. Recommended Approach

**Percorso scelto: Direct Adjustment** — modifica delle storie dentro la struttura di epiche
esistente.

**Opzioni valutate:**

| Opzione | Esito |
|---|---|
| **1. Direct Adjustment** | ✅ **Viable, scelta.** Sforzo basso, rischio medio. Le epiche restano sette; cambia solo Epic 1. Il rischio residuo è la cecità di SER, documentata sopra. |
| **2. Rollback** | ❌ Non applicabile: nessun lavoro completato da revertire. |
| **3. PRD MVP Review** | ⚠️ Viable ma non scelta. L'utente ha esplicitamente rifiutato di ridurre lo scope: la foto resta nell'MVP. Il PRD si amenda nei punti resi falsi, non si rifà. |

**Giustificazione.** La decisione dell'utente è sulla misura, non sullo scope. Rifare il PRD
sarebbe sproporzionato: tre storie escono, una entra, e quattro punti del PRD diventano falsi e
vanno corretti. Il resto della catena — 34 storie su 42, 20 AD, due spine UX — non è toccato.

**Impatto su tempi.** Epic 1 passa da circa due settimane (raccolta + annotazione manuale di 100
IR gold + misura) a pochi giorni. Il piano guadagna tempo e perde una garanzia.

---

## 4. Detailed Change Proposals

### 4.1 — epics.md · Epic 1 ridefinita

**OLD**

> ## Epic 1: Il gate che decide se costruire
> Il fondatore ottiene il numero che stabilisce se il prodotto ha senso nella forma prevista: un
> gold set di foto reali annotate, una misura della baseline dei modelli frontier sullo stesso
> insieme, e la struttura di misura che accompagnerà il progetto per sempre.
> — Storie 1.1, 1.2, 1.3, 1.4

**NEW**

> ## Epic 1: La struttura di misura
> Il progetto ottiene l'apparato che misura la qualità del motore per il resto della sua vita: un
> insieme di riferimento di circuiti a risposta nota, e un comando che produce VSR, SER, QPS e
> TTV più la ripartizione degli errori.
> — Storie 1.1 (gold set strutturato), 1.2 (script di valutazione)

**Rationale.** L'utente rinuncia alla misura della baseline; la struttura di misura resta
necessaria per FR-34, AD-15 e SM-1. Cambia la natura dell'insieme di riferimento, non la sua
esistenza.

### 4.2 — epics.md · Storie 1.1, 1.2 e 1.4 rimosse

Escono: raccolta di 200 foto dagli studenti, annotazione manuale degli IR gold, misura della
baseline e verdetto sul criterio di kill.

**Rationale.** Decisione dell'utente del 13 agosto 2026.

### 4.3 — epics.md · Nuova storia 1.1, gold set strutturato

Un insieme di circuiti in forma strutturata con risposta nota, con split
sviluppo/trattenuto conservato, generabile da parametri invece che raccolto e annotato a mano.

**Rationale.** FR-34 richiede un insieme di riferimento; senza, l'harness non ha nulla da
misurare e Story 2.11 non è completabile.

### 4.4 — prd.md §7 · Callout dello scope condizionato

**OLD** — lo scope è condizionato alla misura della baseline; se supera l'85% il PRD viene
riscritto.

**NEW** — la condizione è stata risolta per giudizio dell'utente il 13 agosto 2026, non per
misura. Il B2C foto-based resta nell'MVP. Il rischio che il callout serviva a coprire — che i
modelli frontier rendano superflua l'estrazione — resta aperto e non monitorato.

**Rationale.** Un callout che promette una misura che non avverrà è peggio di nessun callout.

### 4.5 — prd.md §16 Q8 · Domanda aperta chiusa

**OLD** — "Se la baseline dei modelli frontier supera l'85% sul gold set, questo PRD viene
rivisto in modo sostanziale…"

**NEW** — Chiusa il 13 agosto 2026 per decisione dell'utente, senza misura. Con la nota che il
ricontrollo trimestrale della baseline previsto dal registro rischi (R2) non ha più uno strumento.

### 4.6 — prd.md FR-34 e SM-1 · Limite di copertura dichiarato

Aggiunta a entrambi di una nota che dichiara: l'insieme di riferimento è strutturato, quindi VSR
e SER coprono la catena a valle dell'IR e **non** l'estrazione. SER resta la metrica bloccante, con
questo limite esplicito.

**Rationale.** Una metrica bloccante con un punto cieco non dichiarato è peggio di una metrica
assente: dà fiducia dove non ce n'è.

### 4.7 — sprint-status.yaml · Rigenerazione

Rigenerato dallo script dopo l'aggiornamento delle epiche. Le tre storie rimosse compaiono come
`dropped_orphans` e non vengono trapiantate.

---

## 5. Implementation Handoff

**Portata: Moderate** → Product Owner / Developer. Riorganizzazione di backlog senza replan
strategico.

| Deliverable | Stato |
|---|---|
| `epics.md` con Epic 1 ridefinita | Applicato in questa esecuzione |
| `prd.md` con i quattro punti corretti | Applicato in questa esecuzione |
| `sprint-status.yaml` rigenerato | Applicato in questa esecuzione |
| `implementation-readiness.md` aggiornato | Applicato in questa esecuzione |

**Criteri di successo.** Nessun artefatto contiene più un riferimento alla misura della baseline
come se dovesse avvenire. `sprint-status.yaml` non contiene le tre storie rimosse. FR-34 e SM-1
dichiarano il proprio limite di copertura.

**Prima storia in coda dopo il cambio:** 1.1 — gold set strutturato.

---

## Raccomandazione non richiesta, da tenere o scartare

Il punto cieco su SER si chiude a un costo molto minore di quello rifiutato. Non serve una
campagna con 200 studenti: **30–40 foto dai materiali di ripetizione già esistenti**, annotate una
volta, misurano il tasso di errore silenzioso sull'estrazione abbastanza da distinguere l'1% dal
10%.

È la differenza fra sapere e sperare sul punto in cui il prodotto vive o muore. Costa un
pomeriggio.

Non è una condizione: la decisione presa resta quella eseguita in questa proposta.



---

# ADDENDUM — 13 agosto 2026, sera · inversione parziale

## Cosa cambia

La proposta sopra ha rimosso da Epic 1 la raccolta e l'annotazione fotografica, sul presupposto
che richiedessero una campagna con gli studenti. **Quel presupposto è caduto.** La ricerca del 13
agosto sera ha trovato due dataset con licenza commercialmente compatibile, verificata alla fonte:

- **CGHD** — `cc-by-4.0` (verificata dall'API Zenodo del record 14042961), 3.173 immagini, 32 disegnatori
- **Digitize-HCD** — `CC BY 4.0` (verificata sulla pagina Mendeley Data, versione 2), 1.277 immagini,
  oltre 150 volontari, con **posizioni dei terminali** che a CGHD mancano

**~4.450 immagini, oltre 180 disegnatori, nessuna campagna di raccolta.** La ragione economica che
giustificava la rinuncia non esiste più. L'utente ha deciso di eseguire.

## Perché una storia nuova invece di riaprire la 1.1

La Story 1.1 è `done` e ha consegnato ciò che prometteva: le quattro classi di dominio strutturate,
con verifica indipendente. La metà fotografica ha input diversi (scaricare, annotare a mano),
rischio diverso e criteri diversi. Riaprire una storia chiusa avrebbe reso illeggibile lo storico.

**Nuova Story 1.3 — Metà fotografica dell'insieme di riferimento.** I criteri CGHD che stavano
orfani dentro la 1.1 sono stati spostati lì, il che **risolve il conflitto R5** della retrospettiva
di Epic 1: `epics.md` e questa proposta non si contraddicono più.

Epic 1 torna `in-progress`. È corretto: non era finita.

## Esclusi, con motivo

- **Image2Net** (arXiv 2508.13157) — `CC BY-NC-ND 4.0`. Non commerciale *e* senza derivate. Ha
  104 coppie di netlist verificate a mano, che sarebbero state preziose. Escluso.
  **La sua metrica NED resta adottabile**: una formula pubblicata non è un'opera coperta. Il
  riferimento contro cui misurarsi è 80,77% di successo e 0,116 di NED medio.
- **Fiore, DC/AC Electrical Circuit Analysis** — `CC BY-NC-SA`. Escluso.
- **JUHCCR-v1** — licenza non verificata. Non usare finché non lo è.

## Correzione indipendente su MCP Apps

Verificata la specifica ufficiale (`modelcontextprotocol/ext-apps`, `specification/2026-01-26/apps.mdx`),
FR-20 e AD-16 dicevano una cosa imprecisa. La norma prescrive **due campi distinti**:

> «Tools MUST return meaningful content array even when UI is available»
> `content` — testo per il contesto del modello e per gli host senza UI
> `structuredContent` — dati strutturati per il rendering

Più: `URI MUST start with ui://`, `mimeType MUST be text/html;profile=mcp-app`, associazione via
`_meta.ui.resourceUri`, trasporto JSON-RPC 2.0 su postMessage. Applicato in entrambi i documenti.

## Impatto sulla cecità di SER

Il punto cieco dichiarato in SM-1 passa da 🔴 a 🟠: **in chiusura, non chiuso**. Resta cieco finché
la Story 1.3 non è `done`. Il rapporto dovrà riportare VSR e SER **separati** per metà strutturata e
metà fotografica — mediarli nasconderebbe esattamente il numero che interessa.


---

# ADDENDUM 2 — 14 agosto 2026 · riorganizzazione MCP-first

**Trigger.** L'utente: *«quanto è centrale mcp2.0, mcp apps, chatgptapps, claude apps? Per me deve
essere il nuovo cardine totale.»* Ripetuto due volte, con richiesta di ricerca su entrambi i lati.

## Cosa dice l'evidenza, verificata alla fonte

| Fatto | Fonte | Conseguenza |
|---|---|---|
| Monetizzazione ChatGPT «limited to plugins for **physical goods** purchases» | `developers.openai.com/apps-sdk/build/monetization` | Kirchhoff non è monetizzabile in-host |
| External Checkout: «Payment, billing, taxes, refunds, and compliance handled **entirely on your domain**» | idem | Il dominio proprio è obbligatorio, non preferito |
| Claude: connettori disponibili sul piano **Free**, limite **uno** | `support.claude.com` — custom connectors | Il target raggiungibile a costo zero; uno slot è un fossato |
| Claude: nessun rail di pagamento nativo | idem | Stessa conclusione |
| Stripe Managed Payments **è** merchant of record, beni digitali coperti, 75+ paesi | `stripe.com/managed-payments` + `stripe.com/pricing` | Paddle e Lemon Squeezy escono dal piano |
| Managed Payments **+3,5%** su 1,5% + 0,25 € (std SEE) | `stripe.com/pricing` | 5,0% + 0,25 € tutto compreso |

**Verdetto.** Cardine dell'**acquisizione**: sì, totale. Cardine della **monetizzazione**:
impossibile per regola di piattaforma. La superficie assistente è la porta; il dominio è la cassa;
FR-21 e FR-36 sono la cerniera; SM-11 la misura.

## Modifiche applicate

1. **`epics.md` — ordine di esecuzione MCP-first.** I numeri delle epiche **non cambiano** (PRD e
   spine li referenziano). Cambia l'ordine: 7.1 e 7.2 salgono subito dopo Epic 4; 7.3 resta dopo
   5.1. Tabella di precedenza inclusa.
2. **`epics.md` — nuova Story 5.8**, quota per soggetto anonimo. Buco reale: il listino diceva
   «3 soluzioni al mese», che su un utente in conversazione non è applicabile perché non c'è account
   su cui contare un ciclo.
3. **`prd.md` — nuovo FR-36**, quota per soggetto anonimo.
4. **`prd.md` — nuova SM-11**, conversione conversazione → account. Non esisteva, ed è la metrica
   che decide se il canale è un cardine o una perdita.
5. **`prd.md` — §13 riscritta**: vincolo di piattaforma esplicito, rail a due configurazioni,
   tariffe verificate. Paddle e Lemon Squeezy rimossi.

## Non verificato

- **Ritiro dell'Instant Checkout** (4 marzo 2026, ~30 merchant) — solo fonte di settore, la pagina
  OpenAI risponde 403. Non cambia la conclusione: i beni digitali non erano eleggibili comunque.
- **Volume di scoperta** nelle directory di Claude e ChatGPT. Nessun dato da nessuna delle due.
- **Criteri di approvazione** di Anthropic per la directory.
- **Stripe Billing 0,5–0,8% e 15 $ per contestazione** — solo fonti terze.

## Scartati, con motivo

- **Shopify** — non è merchant of record: riporta addosso l'IVA europea che il MoR toglie. Ha senso
  solo per beni fisici, che non vendiamo. La via Shopify-in-chat via ACP non è comunque disponibile.
- **x402** (micropagamenti in stablecoin per chiamata) — l'utente è uno studente italiano senza
  wallet. L'attrito supera il prezzo.
- **Attendere l'Agentic Commerce Protocol** — i servizi digitali non erano eleggibili nemmeno
  quando era attivo.
