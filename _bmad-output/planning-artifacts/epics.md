---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - prds/prd-Kirchhoff-2026-08-13/prd.md
  - architecture/architecture-Kirchhoff-2026-08-13/ARCHITECTURE-SPINE.md
  - ux-designs/ux-Kirchhoff-2026-08-13/DESIGN.md
  - ux-designs/ux-Kirchhoff-2026-08-13/EXPERIENCE.md
  - ../../docs/00-fonte-piano-kirchhoff.md
---

# Kirchhoff - Epic Breakdown

> ## ⚠️ AVVISO DI VERSIONE ARCHITETTURALE
>
> **Questo documento è derivato dalla v1 dello spine (35 FR / 20 AD) ed è precedente agli
> emendamenti del 15 agosto 2026.** Il drift ha due facce, entrambe misurate il 24/08/2026:
>
> 1. **Dieci decisioni emendate in loco senza rinumerazione** — AD-1, AD-2, AD-4, AD-5, AD-8,
>    AD-10, AD-11, AD-15, AD-18, AD-19 — che questo testo cita ancora nel significato v1 in circa
>    39 punti.
> 2. **Quindici decisioni che questo documento non nomina affatto.** Lo spine v2 contiene
>    **35 AD** (`grep -c "^### AD-" ARCHITECTURE-SPINE.md` → 35); l'inventario qui sotto ne elenca
>    20. AD-21 … AD-35 — fra cui le quattro rappresentazioni disgiunte, il `preserve set`, il
>    `ProofGraph`, il `TruthfulnessGate` e il rendering deterministico — non compaiono in nessuna
>    Storia.
>
> **In caso di conflitto l'autorità è `ARCHITECTURE-SPINE.md`, non questo file.** Ogni Storia va
> letta secondo il contratto v2 delle decisioni che richiama.
>
> Il 24 agosto 2026 sono state allineate a v2 **soltanto** le parti che bloccavano l'esecuzione
> del percorso 2.4 → 2.6 (vedi le note `[v2 · 24/08/2026]` più sotto). Il resto del drift è
> **debito dichiarato**, non dimenticato: si chiude rigenerando questo documento dallo spine v2
> (passo 6 della catena BMAD). Vedi `implementation-artifacts/debito-rigenerazione-epics.md`.
>
> Verificato il 24/08/2026: la Storia 2.4 è risultata **compatibile** con AD-19 v2 e non è stata
> modificata.

## Overview

Scomposizione completa in epiche e storie per Kirchhoff, derivata dal PRD (35 FR, 7 UJ, status
final), dallo spine di architettura (20 AD, lint pulito) e dal contratto UX (DESIGN.md +
EXPERIENCE.md, entrambi final).

**Gli ID sono quelli dei documenti a monte e non vengono rinumerati.** `FR-n` viene dal PRD,
`AD-n` dallo spine, `UJ-n` dal PRD, `KF-n` da EXPERIENCE.md. La tracciabilità vale più
dell'uniformità di formato.

**Nessun template starter è specificato dall'architettura.** Lo spine fissa il paradigma
(ports-and-adapters con nucleo a pipeline deterministica) e l'albero sorgente, ma non appoggia il
progetto su uno scaffold preconfezionato. Epic 1 Story 1.1 crea quindi la struttura a mano
secondo l'albero dello spine.

## Requirements Inventory

### Functional Requirements

| ID | Requisito |
|---|---|
| FR-1 | Ingestione multi-formato (immagine, LaTeX, netlist) |
| FR-2 | Estrazione multi-pass con misura dell'Accordo (K ≥ 3, ≥ 2 assi di variazione) |
| FR-3 | Ridondanza testuale come secondo canale |
| FR-4 | Validazione elettrica come gate, con diagnosi localizzata |
| FR-5 | Anteprima di ricostruzione, sempre, con conferma esplicita |
| FR-6 | Domanda mirata su Ambiguità residua, con ritaglio ingrandito |
| FR-7 | Tetto di due giri e degrado all'editor |
| FR-8 | Ripresa senza perdita e senza doppio addebito |
| FR-9 | Editor del circuito |
| FR-10 | Risoluzione a percorsi indipendenti (A e B) con confronto |
| FR-11 | Verifica a cinque controlli come gate di pubblicazione |
| FR-12 | Rifiuto di certificazione come esito progettato |
| FR-13 | Nessun valore numerico generato da modello linguistico |
| FR-14 | Piano didattico da Catalogo chiuso, eseguito e verificato |
| FR-15 | Disegno del circuito a ogni passo |
| FR-16 | Profilo curricolare che restringe le Trasformazioni ammesse |
| FR-17 | Modalità Studio a rivelazione progressiva |
| FR-18 | Export multiformato (PDF, LaTeX, SVG, e-learning) |
| FR-19 | Marcatura di provenienza su ogni artefatto |
| FR-20 | Superficie assistente con conferma in conversazione |
| FR-21 | Collegamento dell'account dalla superficie assistente |
| FR-22 | Generazione di Varianti verificate |
| FR-23 | Vincoli di generazione |
| FR-24 | Fogli soluzione separati e verificabili |
| FR-25 | Banco esercizi del tenant |
| FR-26 | Consumo di Crediti solo alla Soluzione consegnata |
| FR-27 | Acquisto di Crediti e piani |
| FR-28 | Registrazione con dichiarazione di età |
| FR-29 | Dichiarazione d'uso dell'IA al primo contatto |
| FR-30 | Cancellazione automatica delle immagini entro 72 ore |
| FR-31 | Offuscamento delle regioni personali |
| FR-32 | Consenso esplicito all'uso dei contenuti per il miglioramento |
| FR-33 | Esercizio dei diritti dell'interessato |
| FR-34 | Eval harness sul gold set |
| FR-35 | Segnalazione di errore dall'utente |

### NonFunctional Requirements

| ID | Requisito | Origine |
|---|---|---|
| NFR-1 | Latenza end-to-end < 45 s al 90° percentile, domande incluse | PRD §9 |
| NFR-2 | Anteprima entro 5 s per immagine fino a 5 MP | PRD §5.1 |
| NFR-3 | Determinismo: a parità di IR confermato, soluzione e passaggi riproducibili | PRD §9 |
| NFR-4 | Tracciabilità: ogni Soluzione ricostruibile da IR + versione del sistema | PRD §9 |
| NFR-5 | Indipendenza dal fornitore: ≥ 2 fornitori intercambiabili; la caduta di uno degrada la qualità, non la disponibilità | PRD §9 |
| NFR-6 | Accessibilità WCAG 2.2 AA su tutte e tre le superfici, pannello assistente incluso | PRD §9, EXPERIENCE.md |
| NFR-7 | Mobile-first: flusso B2C completabile a 360 px senza scorrimento orizzontale | PRD §9 |
| NFR-8 | Isolamento fra tenant a livello di database | PRD §9, AD-14 |
| NFR-9 | Osservabilità: SER, VSR, QPS, TTV, tasso di Rifiuto e correzioni strumentati in produzione | PRD §9 |
| NFR-10 | Non-regressione: nessuna modifica al nucleo raggiunge la produzione senza eval harness | PRD §9 |
| NFR-11 | Il gate di pubblicazione non ha bypass, nemmeno amministrativo o di test | PRD §10.1, AD-5 |
| NFR-12 | Precedenza fra metriche in conflitto: SER prevale su QPS, TTV e VSR, sempre | PRD §10.1 |
| NFR-13 | Costo di elaborazione per Soluzione consegnata sotto il 10% del prezzo effettivo | PRD §10.3 |
| NFR-14 | Residenza dei dati e degli artefatti nell'Unione Europea | PRD §12 |
| NFR-15 | Etichette nei disegni ≥ 11 px effettivi a 360 px di viewport | PRD §5.4, DESIGN.md |
| NFR-16 | Nessuna soluzione parziale mostrata come completa | PRD §10.1 |

### Additional Requirements

Dallo spine di architettura. Ognuno è un vincolo che le storie devono rispettare, non un'attività
a sé — le storie che li implementano sono indicate nella mappa di copertura.

- **AD-1** — L'IR è l'unico contratto fra stadi; firma `(IR, ctx) → IR | Refusal`; nessuno stadio
  a valle dell'estrazione legge l'immagine sorgente.
- **AD-2** — Le Trasformazioni sono funzioni pure
  `transform(CircuitIR, params) → (CircuitIR, TransformResult) | Refusal`; nessuna I/O, nessun
  orologio, nessuna casualità; catalogo chiuso caricato all'avvio.
  *[v2 · 24/08/2026]* Il secondo membro non è più un `Drawing`: è un **`TransformResult`** che
  porta `PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate` (AD-22). Il
  disegno non è un'uscita della Trasformazione — è ciò che il renderer produce applicando il
  `LayoutPatch` al `LayoutIR` precedente.
- **AD-3** — I modelli si raggiungono solo attraverso `ModelPort`; nessun SDK di provider sotto
  `domain/`; almeno due adapter registrati.
- **AD-4** — Il generatore di testo produce segnaposto `[[q1.value]]`, mai cifre; un testo con
  cifra letterale è respinto prima della pubblicazione.
- **AD-5** — Gate di pubblicazione in un unico punto: solo `publish()` produce `Published`; nessun
  `Solution` è serializzabile verso l'esterno.
- **AD-6** — Server stateless per richiesta; lo stato multi-giro vive in `resume_ref` firmato
  HMAC, legato al `subject_id`, TTL 15 min, monouso.
- **AD-7** — Chiave di idempotenza da `(subject_id, circuit_id, request_hash)` con vincolo di
  unicità a schema.
- **AD-8** — Un solo modulo scrive ciascuna entità; `studio` chiama `publish()` ma non scrive mai
  un `Published`.
- **AD-9** — TTL immagini imposto dalla lifecycle policy dello storage, non da un job applicativo.
- **AD-10** — Un solo punto produce artefatti esportabili, e applica la Marcatura di provenienza.
- **AD-11** — Nessun tipo associa una misura di rendimento a un identificatore di persona.
- **AD-12** — La cascata di costo può cambiare quali modelli, mai quanti Pass; `K ≥ 3` imposto dal
  codice.
- **AD-13** — `Refusal` e `Failure` sono tipi diversi, su canali diversi.
- **AD-14** — Isolamento tenant via row-level security a livello DB.
- **AD-15** — L'eval harness gira sul codice di produzione attraverso gli stessi port; nessun ramo
  `if testing`.
- **AD-16** — La superficie assistente è un contratto pubblico versionato; ogni risposta con
  pannello porta anche il riassunto testuale strutturato.
- **AD-17** — Un solo orologio, iniettato via `ClockPort`.
- **AD-18** — *[v2 · 24/08/2026]* **`Drawing` non esiste più.** La regola sopravvive nella forma
  forte: il dominio non produce geometria, non conosce markup, pixel, colori o font — e dalla v2
  non conosce nemmeno il concetto di **posizione**. `p_k` vive nel `LayoutIR`, di cui
  `render/layout` è scrittore unico (AD-8 em., AD-21).
- **AD-19** — `Refusal.cause` da enumerazione chiusa con payload tipizzato che porta sempre
  `subject`.
- **AD-20** — Identità come `subject_id` opaco, anonimo incluso; il collegamento account è una
  fusione esplicita di soggetti.

Requisiti infrastrutturali derivati:

- Bucket object storage in regione UE con lifecycle policy a 72 ore (AD-9, FR-30, NFR-14).
- PostgreSQL in regione UE con row-level security attiva (AD-14, NFR-8, NFR-14).
- Registrazione di almeno due adapter di modello prima del primo rilascio (AD-3, NFR-5).
- Catena LaTeX vincolata: niente `lmodern`, niente babel italiano, label CircuiTikZ con `=` in
  graffe.
- **Nessun template starter**: la struttura è creata a mano secondo l'albero sorgente dello spine.

### UX Design Requirements

| ID | Requisito |
|---|---|
| UX-DR1 | Sistema di token colore: 32 token, coppie chiaro/scuro complete, tutti esadecimali |
| UX-DR2 | Scala tipografica a 7 ruoli: `display`, `title`, `body`, `meta`, `quantity`, `residual`, `label-drawing` |
| UX-DR3 | Cifre tabulari (`font-variant-numeric: tabular-nums`) su ogni quantità, residuo ed etichetta di disegno |
| UX-DR4 | Componente `badge-verified`: pillola, spunta in cerchio pieno, etichetta "Verificata", apribile sul pannello dei residui |
| UX-DR5 | Componente `badge-suspended`: pillola, cerchio barrato, etichetta "Non certificata", **mai rosso, mai icona di allarme**, apribile sulla diagnosi |
| UX-DR6 | Componente `provenance-anchor`: riquadro 2 px sull'immagine sorgente, attivabile da entrambi i lati del confronto |
| UX-DR7 | Componente `quantity-chip` |
| UX-DR8 | Componente `residual-row`: cinque righe, ordine fisso e non riordinabile |
| UX-DR9 | Componente `step-card`: nome Trasformazione, formula letterale, sostituzione numerica, disegno — il disegno è obbligatorio |
| UX-DR10 | Componente `question-card`: ritaglio ingrandito in cima, alternative grandi, campo libero sempre in coda, contatore giri visibile |
| UX-DR11 | Componente `disclosure-bar`: persistente, non chiudibile, presente su tutte e tre le superfici |
| UX-DR12 | Verifica di accessibilità cromatica: ogni schermata resta interpretabile in scala di grigi; nessuno stato portato dal solo colore |
| UX-DR13 | `Refusal` e `Failure` distinti da colore **e** icona **e** parole, mai da uno solo dei tre |
| UX-DR14 | Alternativa testuale topologica per ogni disegno (non "schema del circuito", ma la struttura) |
| UX-DR15 | Percorso completo da tastiera su tutte le superfici, con focus visibile non portato dal solo colore |
| UX-DR16 | Bersagli di tocco ≥ 44 × 44 px, incluse le alternative nelle Domande mirate |
| UX-DR17 | Rispetto di `prefers-reduced-motion`: rimozione di ogni transizione non essenziale |
| UX-DR18 | Progresso a fasi con etichette reali degli stadi, non barra generica |
| UX-DR19 | Layout responsive: < 768 px colonna singola con controllo a due stati (mai accordion); ≥ 768 px Anteprima a due colonne |
| UX-DR20 | Modalità scura pari grado alla chiara, non tema secondario |
| UX-DR21 | Foglio di stile di stampa con Marcatura di provenienza non rimovibile via CSS |
| UX-DR22 | Superficie "Non certificata" con indirizzo proprio, condivisibile, che sopravvive al ricaricamento |
| UX-DR23 | Vocabolario UI vincolato ai termini del Glossario del PRD; nessun sinonimo |
| UX-DR24 | Microcopy secondo le 7 regole di `EXPERIENCE.md` e lista di parole vietate |
| UX-DR25 | Stati vuoti con un esempio reale caricabile con un tocco, non un'illustrazione |
| UX-DR26 | Rendering delle formule come matematica accessibile, non come immagini |

### FR Coverage Map

| FR | Epic | Come vi atterra |
|---|---|---|
| FR-1 | Epic 2 (netlist/LaTeX) + Epic 3 (immagine) | L'ingestione strutturata arriva col motore; quella da foto con la ricostruzione |
| FR-2 | Epic 3 | Estrazione multi-pass e misura dell'Accordo |
| FR-3 | Epic 3 | Ridondanza testuale come secondo canale |
| FR-4 | Epic 2 | Validazione elettrica come gate, puro codice |
| FR-5 | Epic 3 | Anteprima di ricostruzione, sempre |
| FR-6 | Epic 3 | Domanda mirata su Ambiguità residua |
| FR-7 | Epic 3 | Tetto di due giri e degrado all'editor |
| FR-8 | Epic 3 | Ripresa senza perdita né doppio addebito |
| FR-9 | Epic 3 | Editor del circuito |
| FR-10 | Epic 2 | Percorsi A e B con confronto obbligatorio |
| FR-11 | Epic 2 | Verifica a cinque controlli, gate di pubblicazione |
| FR-12 | Epic 2 | Rifiuto di certificazione come esito di dominio |
| FR-13 | Epic 2 | Nessun numero da modello linguistico |
| FR-14 | Epic 2 | Piano didattico da Catalogo chiuso |
| FR-15 | Epic 4 | Disegno del circuito a ogni passo |
| FR-16 | Epic 2 | Profilo curricolare che restringe il Catalogo |
| FR-17 | Epic 4 | Modalità Studio a rivelazione progressiva |
| FR-18 | Epic 4 | Export multiformato |
| FR-19 | Epic 4 | Marcatura di provenienza |
| FR-20 | Epic 7 | Superficie assistente con pannello di conferma |
| FR-21 | Epic 7 | Collegamento dell'account |
| FR-22 | Epic 6 | Generazione di Varianti verificate |
| FR-23 | Epic 6 | Vincoli di generazione |
| FR-24 | Epic 6 | Fogli soluzione con checksum |
| FR-25 | Epic 6 | Banco esercizi del tenant |
| FR-26 | Epic 5 | Consumo alla Soluzione consegnata |
| FR-27 | Epic 5 | Acquisto di Crediti e piani |
| FR-28 | Epic 5 | Dichiarazione di età al signup |
| FR-29 | Epic 5 | Dichiarazione d'uso dell'IA |
| FR-30 | Epic 5 | Cancellazione automatica delle immagini |
| FR-31 | Epic 5 | Offuscamento delle regioni personali |
| FR-32 | Epic 5 | Consenso al miglioramento, OFF di default |
| FR-33 | Epic 5 | Diritti dell'interessato |
| FR-34 | Epic 1 (harness + insieme strutturato) + Epic 2 (metriche del pipeline) | La struttura di misura precede il pipeline che misura. **Copertura parziale: esclude l'estrazione** |
| FR-35 | Epic 5 | Segnalazione di errore dall'utente |
| FR-36 | Epic 5 | Quota per soggetto anonimo — prerequisito di 7.2 in produzione |

Copertura: **35/35 FR mappati**, nessun buco.

## Epic List

Sette epiche. Architettura e UX sono già validate, quindi le epiche sono poche e larghe: si divide
solo dove esiste un vero confine di rischio o dove un riscontro precoce può cambiare direzione a
ciò che segue.

Il confine di rischio dominante è **Epic 1**: se la baseline dei modelli frontier è troppo alta, il
piano cambia e le epiche 3, 4, 5 e 7 vengono riscritte. Per questo Epic 1 è piccola, prima, e
autonoma.

### Epic 1: La struttura di misura

Il progetto ottiene l'apparato che misura la qualità del motore per il resto della sua vita: un
insieme di riferimento di circuiti a risposta nota, e un comando che produce VSR, SER, QPS e TTV
più la ripartizione degli errori per tipo. Nessuna riga di prodotto dipende da questa epica, ma
ogni affermazione sulla qualità sì.

**FRs covered:** FR-34 (struttura di misura, copertura piena con 1.3)
**Vincoli portanti:** AD-15, NFR-9, NFR-10
**Autonomia:** completa. Non dipende da nessuna epica e non richiede che il prodotto esista.

> **Limite di copertura, dichiarato.** L'insieme di riferimento è **strutturato**, non fotografico:
> misura la catena a valle dell'IR — solver, Trasformazioni, Verifica — e **non** l'estrazione.
> SER resta la metrica bloccante ma è cieca sul tratto dove l'errore silenzioso nasce quasi tutto.
> Conseguenza accettata con la decisione del 13 agosto 2026 (vedi `sprint-change-proposal-2026-08-13.md`).

### Epic 2: Motore verificato da riga di comando

Dato un circuito in forma strutturata, il sistema lo valida, lo risolve per due percorsi
indipendenti, sottopone il risultato ai cinque controlli, e o consegna una soluzione certificata o
rifiuta di certificarla dicendo dove si rompe. È il nucleo che nessun concorrente può copiare, ed è
utilizzabile — da riga di comando — prima che esista qualunque interfaccia.

**FRs covered:** FR-1 (netlist/LaTeX), FR-4, FR-10, FR-11, FR-12, FR-13, FR-14, FR-16, FR-34
(metriche sul pipeline)
**Vincoli portanti:** AD-1, AD-2, AD-4, AD-5, AD-8, AD-13, AD-17, AD-18, AD-19; NFR-3, NFR-11,
NFR-12, NFR-16
**Autonomia:** completa. Usa la struttura di misura di Epic 1 ma funziona senza.

### Epic 3: Dalla foto al circuito confermato

Uno studente fotografa un esercizio e ottiene una ricostruzione che può verificare con un tocco. Il
sistema legge più volte in modo indipendente, misura quanto le letture divergono, chiede solo ciò
che resta davvero ambiguo, e non calcola mai prima che l'utente abbia confermato.

**FRs covered:** FR-1 (immagine), FR-2, FR-3, FR-5, FR-6, FR-7, FR-8, FR-9
**Vincoli portanti:** AD-3, AD-6, AD-12, AD-20; NFR-1, NFR-2, NFR-5
**Autonomia:** completa sul proprio dominio. Costruisce sul motore di Epic 2.

### Epic 4: La soluzione che si può mostrare e portare via

La soluzione diventa un documento: passi con il circuito ridisegnato a ogni riduzione, modalità di
studio a rivelazione progressiva, ed export in PDF, LaTeX e SVG con la marcatura di provenienza che
li rende riconoscibili.

**FRs covered:** FR-15, FR-17, FR-18, FR-19
**Vincoli portanti:** AD-10, AD-18, AD-4; NFR-6, NFR-7, NFR-15
**Autonomia:** completa. Costruisce su Epic 2 (e su Epic 3 quando l'ingresso è una foto).

### Epic 5: Account, Crediti e conformità in prodotto

Un utente si registra, compra Crediti, e paga solo per ciò che ha ottenuto davvero. Gli obblighi di
trasparenza e i controlli sui dati sono funzionalità implementate e testate, non una pagina legale.

**FRs covered:** FR-26, FR-27, FR-28, FR-29, FR-30, FR-31, FR-32, FR-33, FR-35
**Vincoli portanti:** AD-7, AD-9, AD-11, AD-20; NFR-13, NFR-14
**Autonomia:** completa. Richiede da Epic 2 il concetto di Soluzione consegnata.

### Epic 6: Studio — varianti verificate per chi insegna

Un tutor prende un esercizio e ne ottiene N varianti con valori diversi, ognuna con soluzione
completa verificata e foglio soluzione separato. Le varianti scartate perché non verificate sono
mostrate, non nascoste.

**FRs covered:** FR-22, FR-23, FR-24, FR-25
**Vincoli portanti:** AD-5, AD-8, AD-14; NFR-8
**Autonomia:** completa. Riusa `publish()` di Epic 2 e il rendering di Epic 4.

### Epic 7: Kirchhoff dentro l'assistente

Lo studente risolve senza uscire dalla conversazione che ha già aperto: pannello di conferma reso
in conversazione, e l'assistente che sa cosa l'utente ha confermato perché riceve anche il
riassunto testuale.

**FRs covered:** FR-20, FR-21
**Vincoli portanti:** AD-6, AD-16, AD-20, AD-5
**Autonomia:** completa. Espone su una superficie nuova ciò che Epic 3 e 4 già fanno.

---

**Verifica di sovrapposizione sui file.** Le sette epiche toccano zone distinte dell'albero
sorgente: Epic 1 e 2 → `eval/` e `domain/`; Epic 3 → `pipeline/` e `adapters/model`; Epic 4 →
`render/`; Epic 5 → `api/` e `billing`; Epic 6 → `studio`; Epic 7 → `api/assistant`. La condivisione
è incidentale (tutte leggono l'IR), non "stesso componente end-to-end": nessun consolidamento
necessario.

**Dipendenze naturali.** 1 → nessuna · 2 → nessuna (usa 1 per misurarsi) · 3 → 2 · 4 → 2 · 5 → 2 ·
6 → 2, 4 · 7 → 3, 4. Nessuna epica richiede un'epica *successiva* per funzionare.

---

## Ordine di esecuzione — MCP-first (14 agosto 2026)

**I numeri delle epiche non cambiano** — PRD e spine li referenziano e rinumerarli romperebbe ogni
riferimento. Cambia **l'ordine in cui si costruiscono**.

**Perché.** La monetizzazione dentro gli assistenti è chiusa ai servizi digitali: su ChatGPT
l'approvazione è limitata ai beni fisici, su Claude non esiste rail di pagamento. Ma il piano Free
di Claude dà **un** connettore, e la directory è self-serve. Per un fondatore senza pubblico, che
non può permettersi advertising e ha sei mesi di rampa SEO davanti, **la superficie assistente è il
miglior canale di acquisizione disponibile** — e non serve a niente se arriva ultima.

```
1  struttura di misura
2  motore verificato
3  dalla foto al circuito confermato
4  soluzione mostrabile
   ├─ 7.1  contratto della superficie assistente     ← anticipate
   └─ 7.2  pannello di conferma in conversazione     ← anticipate
5  account, crediti, conformità   (5.1 identità · 5.8 quota anonima obbligatorie qui)
   └─ 7.3  collegamento account                      ← dipende da 5.1
6  Studio
```

**Vincoli di precedenza, non opinioni.**

| Storia | Non prima di | Perché |
|---|---|---|
| 7.1, 7.2 | Epic 4 completa | Il pannello mostra Anteprima e Soluzione renderizzata: senza, non c'è cosa mostrare |
| 5.8 | 5.1 | La quota si conta su `subject_id`, che 5.1 introduce |
| 7.2 in produzione | 5.8 | Una superficie pubblica senza quota è compute gratuito per sconosciuti |
| 7.3 | 5.1 | Il collegamento è una fusione di soggetti |

**Effetto collaterale che vale l'anticipo.** Il connettore singolo del piano Free lo installa anche
il **tutor**, che è il cliente Studio da 390 €/anno. La directory non è solo acquisizione B2C: è
generazione di lead B2B a costo marginale zero.

**La metrica che governa la scelta è SM-11** — conversione da soluzione in conversazione ad account
collegato. Se resta bassa, la superficie assistente è una perdita e va ridimensionata: porta uso e
non porta clienti.

---

## Epic 1: La struttura di misura

Il progetto ottiene l'apparato che misura la qualità del motore per il resto della sua vita.

### Story 1.1: Insieme di riferimento strutturato a risposta nota

As a fondatore,
I want un insieme di circuiti in forma strutturata con risultato corretto noto, generabile invece
che raccolto,
So that esista un oracolo contro cui misurare il motore senza dipendere da una campagna di
raccolta.

**Acceptance Criteria:**

**Given** un generatore parametrico di circuiti
**When** l'insieme di riferimento è prodotto
**Then** copre le quattro classi di dominio in scope — reti resistive in DC, transitori RL/RC/RLC,
regime sinusoidale, trifase
**And** ogni elemento porta IR, risultato numerico corretto e sequenza di Trasformazioni di
riferimento (FR-34).

> **Chiusa il 13 agosto 2026.** Tutte e quattro le classi di dominio implementate e verificate.
> La metà **fotografica** è stata spostata nella Story 1.3, che è dove vive adesso: qui restava
> come criterio orfano e contraddiceva `sprint-change-proposal-2026-08-13.md`.

**Given** l'insieme prodotto
**When** viene diviso
**Then** esiste uno split fra parte di sviluppo e parte trattenuta
**And** la parte trattenuta è in uno store separato che il flusso di sviluppo non può leggere.

**Given** un circuito la cui soluzione corretta è ricavata dal generatore stesso
**When** viene inserito nell'insieme
**Then** il risultato è verificato in modo indipendente dal generatore che l'ha prodotto — un
oracolo che si autocertifica non è un oracolo.

### Story 1.2: Script di valutazione con metriche e matrice degli errori

As a fondatore,
I want un comando che, dato l'insieme di riferimento, produca VSR, SER, QPS e TTV più la
ripartizione degli errori per tipo,
So that ogni discussione sulla qualità si faccia sui numeri e sia riproducibile.

**Acceptance Criteria:**

**Given** l'insieme di riferimento e il gold corrispondente
**When** lo script viene eseguito
**Then** produce le quattro metriche e una ripartizione degli errori per tipo (topologia, valore,
unità, grandezza richiesta, irrisolvibile)
**And** l'esecuzione è riproducibile: stessi input, stesse metriche.

**Given** una configurazione che punta alla parte trattenuta
**When** lo script viene eseguito in modalità di sviluppo
**Then** l'esecuzione fallisce con un messaggio esplicito
**And** nessuna metrica viene prodotta.

**Given** un rapporto prodotto dallo script
**When** viene letto
**Then** dichiara esplicitamente che la copertura esclude l'estrazione da immagine, così che
nessuna lettura successiva scambi SER parziale per SER complessivo.

---

### Story 1.3: Metà fotografica dell'insieme di riferimento

As a fondatore,
I want un sottoinsieme di fotografie reali di circuiti disegnati a mano, annotate con IR e
risultato,
So that SER smetta di essere cieca sull'estrazione — il tratto dove nasce quasi tutto l'errore
silenzioso.

**Acceptance Criteria:**

**Given** i due dataset a licenza aperta verificati in `docs/01-fonti-esterne.md` — CGHD
(`cc-by-4.0`, 3.173 immagini, 32 disegnatori) e Digitize-HCD (`CC BY 4.0`, 1.277 immagini, oltre
150 volontari, con **posizioni dei terminali**)
**When** si costruisce la metà fotografica
**Then** almeno 30 immagini portano IR e risultato numerico annotati a mano
**And** la stratificazione dichiarata è rispettata: le immagini vengono da almeno 10 disegnatori
diversi, così che il campione non misuri la calligrafia di una persona sola
**And** nessuna immagine proviene da una fonte con licenza non commerciale — Image2Net
(`CC BY-NC-ND`) e Fiore (`CC BY-NC-SA`) restano esclusi.

**Given** un artefatto che usa o cita i dataset
**When** viene prodotto
**Then** porta l'attribuzione richiesta dalla licenza CC-BY, testualmente come indicato in
`docs/01-fonti-esterne.md`
**And** l'assenza dell'attribuzione fa fallire un controllo automatico, perché è un obbligo di
licenza e non una cortesia.

**Given** la metà fotografica presente nell'insieme di riferimento
**When** `kirchhoff-eval report` viene eseguito
**Then** il campo `coverage` smette di dichiarare `PARZIALE` per l'estrazione
**And** il rapporto riporta VSR e SER separatamente per la metà strutturata e per quella
fotografica, perché mediarle nasconderebbe esattamente il numero che interessa.

**Given** la metrica di distanza fra grafi definita in Image2Net — NED, distanza di edit fra il
grafo ricostruito e quello vero, normalizzata su dispositivi, net e porte
**When** si misura la qualità dell'estrazione
**Then** il rapporto riporta anche NED accanto a SER
**And** la formula è reimplementata da noi: si adotta una definizione pubblicata, non si copia un
dataset con licenza incompatibile.

> **Riferimento pubblicato contro cui misurarsi:** Image2Net dichiara 80,77% di successo e 0,116
> di NED medio. Non è un obiettivo di v1, è il metro esistente.

---

## Epic 2: Motore verificato da riga di comando

Dato un circuito in forma strutturata, il sistema lo valida, lo risolve per due percorsi
indipendenti, e o consegna una soluzione certificata o rifiuta di certificarla dicendo dove si
rompe.

### Story 2.1: Struttura del progetto con confini di dipendenza verificati

As a sviluppatore,
I want una struttura di progetto in cui la regola di dipendenza dello spine è verificata
automaticamente,
So that la separazione fra dominio e adapter non dipenda dalla disciplina di chi scrive.

**Acceptance Criteria:**

**Given** l'albero sorgente dello spine (`domain/`, `ports/`, `adapters/`, `pipeline/`, `api/`,
`render/`, `eval/`)
**When** il progetto viene creato
**Then** ogni directory esiste con il proprio pacchetto inizializzato
**And** la configurazione valida all'avvio con schema, e una configurazione non valida impedisce
l'avvio invece di degradare in silenzio (AD-17, convenzioni).

**Given** un modulo sotto `domain/` che importa qualcosa da `adapters/` o da `ports/`
**When** il controllo dei confini gira in integrazione continua
**Then** il controllo fallisce nominando file e import
**And** il fallimento blocca la fusione (AD-1, paradigma).

### Story 2.2: Schema IR e canonicalizzazione

As a sviluppatore,
I want un IR versionato con provenienza e forma simbolica accanto a ogni valore,
So that ogni stadio a valle abbia un contratto unico e una soluzione sia riproducibile dal solo IR.

**Acceptance Criteria:**

**Given** un IR costruito da qualunque sorgente
**When** viene validato contro lo schema
**Then** porta `ir_version` semantica, e ogni componente ha valore con magnitudine **e** unità **e**
forma simbolica
**And** ogni componente porta la propria area di provenienza quando la sorgente è un'immagine
**And** un valore numerico senza unità è respinto dallo schema (convenzione sulle grandezze fisiche).

**Given** due IR che descrivono lo stesso circuito con ordine di nodi e componenti diverso
**When** vengono canonicalizzati
**Then** producono la stessa forma canonica
**And** il confronto fra i due risulta identico.

### Story 2.3: Ingestione da netlist e da LaTeX

As a sviluppatore,
I want fornire un circuito in forma strutturata e ottenere un IR valido,
So that il motore sia esercitabile e misurabile prima che esista qualunque lettura da immagine.

**Acceptance Criteria:**

**Given** una netlist ben formata
**When** viene ingerita
**Then** produce un IR che supera la validazione dello schema
**And** le grandezze richieste dichiarate nella sorgente compaiono in `requests`.

**Given** una sorgente LaTeX che descrive più di un esercizio
**When** viene ingerita
**Then** il sistema restituisce l'elenco degli esercizi trovati e richiede una selezione
**And** non ne sceglie uno d'ufficio e non li fonde (FR-1).

### Story 2.4: Validazione elettrica con diagnosi localizzata

As a sviluppatore,
I want che ogni IR passi da una batteria di controlli deterministici che, fallendo, nominano
l'elemento coinvolto,
So that un fallimento sia un'informazione utilizzabile e non un rifiuto generico.

**Acceptance Criteria:**

**Given** un IR con un grafo non connesso, un nodo di grado 1, un loop di soli generatori di
tensione, un taglio di soli generatori di corrente, un'unità incompatibile col tipo, o un valore
richiesto inesistente
**When** la validazione gira
**Then** produce un `Refusal` con causa dall'enumerazione chiusa e payload che porta `subject` —
il nodo, il ramo o il componente coinvolto (FR-4, AD-19)
**And** nessun IR raggiunge lo stato confermato.

**Given** un valore resistivo fuori dalle serie E12/E24 in un esercizio manoscritto
**When** la validazione gira
**Then** l'elemento è segnalato come sospetto senza bloccare
**And** il sospetto è disponibile a valle come possibile Ambiguità residua.

**Given** un IR valido
**When** la validazione gira
**Then** l'IR è promosso e nessun falso positivo è emesso sul gold set di sviluppo.

### Story 2.5: Percorso A — analisi nodale modificata simbolica

As a sviluppatore,
I want risolvere qualunque IR valido per analisi nodale modificata in forma simbolica,
So that esista un oracolo generale e robusto contro cui misurare ogni altro metodo.

**Acceptance Criteria:**

**Given** un IR valido in regime continuo, sinusoidale, transitorio o trifase
**When** il Percorso A gira
**Then** produce un valore per **ogni** grandezza richiesta, non solo per la prima (FR-10)
**And** la risoluzione avviene prima in forma simbolica e poi per sostituzione dei valori.

**Given** lo stesso IR risolto due volte
**When** i risultati vengono confrontati
**Then** coincidono esattamente (NFR-3).

### Story 2.6: Catalogo delle Trasformazioni e Percorso B

As a sviluppatore,
I want un catalogo chiuso di Trasformazioni pure che producono un nuovo `CircuitIR` e un
`TransformResult` che dichiara *cosa* è cambiato,
So that esista un secondo percorso risolutivo indipendente, e i passaggi siano quelli che uno
studente scriverebbe a mano.

**Acceptance Criteria:**

*[v2 · 24/08/2026 — criterio riallineato ad AD-2 em. e AD-18 em.; la formulazione precedente
chiedeva `(IR, Drawing)`, contratto ritirato il 15 agosto.]*

**Given** una Trasformazione del catalogo applicata a un `CircuitIR`
**When** viene eseguita
**Then** restituisce `(CircuitIR, TransformResult) | Refusal` senza alcuna I/O, senza lettura
dell'orologio e senza casualità (AD-2 em.)
**And** il `TransformResult` porta `PreserveSet`, `Delta`, `Boundary`, `LayoutPatch`, `Equation`
e `Certificate` (AD-22)
**And** il `LayoutPatch` nomina **entità e non coordinate**: `preserve`, `remove`, `create` sono
insiemi di identificatori, `node_mapping` è una mappa fra identificatori, `reroute_scope` è
l'insieme dei rami la cui instradatura è libera — nessun numero, nessuna posizione (AD-2 em.)
**And** il dominio non produce geometria né markup e non conosce il concetto di posizione
(AD-18 em., AD-21)
**And** `domain/transform/check` verifica **massimalità, identità e boundary** senza mai leggere
il `LayoutIR`, ed emette `identity_violation`, `preserve_nonmaximal` o `empty_boundary` quando
falliscono (AD-19 em.)
**And** il `CircuitIR` risultante supera la validazione elettrica.

**Given** una richiesta di applicare una Trasformazione non presente nel catalogo
**When** l'esecuzione viene tentata
**Then** fallisce prima di eseguire qualunque calcolo
**And** il catalogo non è estendibile a runtime.

**Given** un IR e una sequenza di Trasformazioni che arriva alla grandezza richiesta
**When** il Percorso B gira
**Then** il risultato coincide con quello del Percorso A entro tolleranza relativa 1e-9 simbolica
e 1e-6 numerica (FR-10)
**And** nessun valore mostrato all'utente proviene da un modello linguistico: il testo dei passi
porta segnaposto risolti dal renderer (FR-13, AD-4)
**And** *[v2 · 24/08/2026]* ogni segnaposto è **legato al passo che lo possiede**: `[[q.value]]`
risolve solo dentro l'insieme delle grandezze in scope per quel nodo del `ProofGraph`; un
segnaposto fuori scope è **respinto** e uno non risolto produce `Refusal`, mai una stringa vuota
o il proprio nome letterale (AD-4 em.).

### Story 2.7: Verifica a cinque controlli

As a sviluppatore,
I want sottoporre ogni soluzione a cinque controlli indipendenti con residui numerici,
So that la promessa del prodotto sia dimostrabile e non asserita.

**Acceptance Criteria:**

**Given** una soluzione calcolata
**When** la Verifica gira
**Then** produce cinque residui — KCL per nodo, KVL per maglia indipendente, bilancio di potenza,
accordo fra percorsi, sanità fisica — calcolati **sostituendo** la soluzione ottenuta e non
ri-derivandola (FR-11)
**And** ogni residuo è ispezionabile con il proprio valore numerico.

**Given** una soluzione con un errore di segno che soddisfa KCL e KVL
**When** la Verifica gira
**Then** il bilancio di potenza lo rileva e la Verifica fallisce.

**Given** una rete puramente passiva
**When** la sanità fisica gira
**Then** rileva ogni elemento passivo con potenza negativa e ogni tensione di nodo fuori
dall'inviluppo dei generatori.

### Story 2.8: Gate di pubblicazione unico e Rifiuto tipizzato

As a sviluppatore,
I want che una soluzione possa uscire dal sistema solo attraverso un unico punto che esegue la
Verifica,
So that nessuna superficie possa mostrare un risultato non certificato, ora o in futuro.

**Acceptance Criteria:**

**Given** una soluzione che supera tutti e cinque i controlli
**When** `publish()` viene chiamata
**Then** restituisce un `Published` con i residui allegati, e il Badge Verificata è applicato se e
solo se tutti e cinque i controlli sono passati (FR-11)
**And** `Published` è l'unico tipo serializzabile verso l'esterno (AD-5).

**Given** una soluzione che fallisce almeno un controllo
**When** `publish()` viene chiamata
**Then** restituisce un `Refusal` con causa dall'enumerazione chiusa e `subject` popolato
**And** nessun valore di risultato è incluso nella risposta
**And** `Refusal` non condivide gerarchia di tipi né canale con `Failure` (AD-13, AD-19).

**Given** un tentativo di serializzare un `Solution` non pubblicato da qualunque modulo
**When** il codice viene compilato o il test di contratto gira
**Then** fallisce
**And** non esiste alcun flag che disattivi il gate, nemmeno in configurazione di test (NFR-11).

### Story 2.9: Profilo curricolare che restringe il Catalogo

As a docente o tutor,
I want che il sistema usi solo i metodi che il mio corso ha già svolto e le mie convenzioni di
segno,
So that la soluzione sia utilizzabile dai miei studenti invece di introdurre strumenti che non
conoscono.

**Acceptance Criteria:**

**Given** un Profilo curricolare che esclude Thévenin
**When** viene prodotto un Piano didattico sotto quel Profilo
**Then** nessun passo usa Thévenin (FR-16)
**And** se nessun piano è raggiungibile con le Trasformazioni ammesse, il sistema lo dichiara
invece di violare il Profilo.

**Given** un Profilo con convenzione di segno dichiarata
**When** la soluzione viene prodotta
**Then** la convenzione è applicata coerentemente a risultato, disegni e testo.

**Given** nessun Profilo associato
**When** la soluzione viene prodotta
**Then** viene usato un profilo predefinito dichiarato ed esplicito, non un comportamento implicito.

### Story 2.10: Piano didattico proposto, eseguito e verificato

As a studente,
I want che i passaggi seguano una sequenza sensata e non una derivazione meccanica,
So that il procedimento sia quello che il professore si aspetta di vedere sul foglio.

**Acceptance Criteria:**

**Given** un IR validato e un Profilo curricolare
**When** il pianificatore propone una sequenza
**Then** ogni elemento appartiene al Catalogo, e il sistema la esegue deterministicamente (FR-14)
**And** il risultato ottenuto coincide con il Percorso A entro tolleranza, altrimenti la soluzione
non è pubblicabile.

**Given** una sequenza proposta che non converge o non è applicabile
**When** l'esecuzione la incontra
**Then** il sistema ripiega sul piano canonico nodale senza intervento manuale
**And** l'evento è registrato per l'analisi di qualità.

### Story 2.11: Metriche del pipeline nell'harness

As a fondatore,
I want che l'harness misuri il nostro pipeline attraverso lo stesso percorso che attraversano gli
utenti,
So that VSR e SER non descrivano un codice che nessuno esegue.

**Acceptance Criteria:**

**Given** l'harness di Epic 1 e il pipeline di questa epica
**When** l'eval gira
**Then** invoca la stessa pipeline degli utenti sostituendo solo gli adapter, e produce VSR, SER,
QPS e TTV più la ripartizione degli errori per tipo (FR-34, AD-15)
**And** non esiste alcun ramo condizionale di test nel percorso di dominio.

**Given** una modifica a estrazione, validazione, Trasformazioni o Piano didattico
**When** l'integrazione continua gira
**Then** l'eval viene eseguito e il risultato è confrontato con la soglia corrente
**And** una regressione di SER blocca la fusione (NFR-10).

---

## Epic 3: Dalla foto al circuito confermato

Uno studente fotografa un esercizio e ottiene una ricostruzione che può verificare con un tocco.

### Story 3.1: Ingestione dell'immagine e selezione dell'esercizio

As a studente,
I want caricare la foto del mio esercizio anche se storta e in penombra,
So that non debba rifarla o ritagliarla prima di ottenere una risposta.

**Acceptance Criteria:**

**Given** una foto JPEG, PNG, HEIC o un PDF a pagina singola fino a 20 MB
**When** viene caricata
**Then** è accettata e normalizzata — correzione prospettica, raddrizzamento, normalizzazione del
contrasto, ingrandimento delle regioni ad alta densità di testo
**And** vengono prodotte tre versioni deliberatamente diverse per l'estrazione a valle.

**Given** una foto che contiene due esercizi
**When** viene caricata
**Then** il sistema mostra i candidati e chiede quale
**And** non ne sceglie uno d'ufficio e non li fonde (FR-1).

**Given** un file che non è interpretabile come esercizio
**When** viene caricato
**Then** il messaggio dice cosa manca, non "errore generico" (voce e tono).

### Story 3.2: ModelPort e due adapter di fornitore

As a sviluppatore,
I want raggiungere i modelli solo attraverso un'interfaccia astratta con almeno due
implementazioni,
So that la caduta o il rincaro di un fornitore degradi la qualità e non la disponibilità.

**Acceptance Criteria:**

**Given** l'interfaccia `ModelPort` con `extract`, `plan`, `narrate`
**When** il progetto viene compilato
**Then** almeno due adapter di fornitore sono registrati e selezionabili da configurazione
**And** nessun modulo sotto `domain/` importa un SDK di fornitore (AD-3).

**Given** un fornitore che restituisce un JSON non conforme allo schema d'uscita
**When** la risposta viene ricevuta
**Then** viene rifiutata e ritentata con vincolo esplicito
**And** dopo i tentativi previsti l'esito è un `Failure`, non un IR parziale.

**Given** un fornitore non raggiungibile
**When** l'estrazione gira
**Then** il sistema usa i restanti adapter registrati e prosegue
**And** l'evento di degrado è strumentato (NFR-5).

### Story 3.3: Estrazione multi-pass e misura dell'Accordo

As a studente,
I want che il sistema legga il mio circuito più volte e sappia dove le letture divergono,
So that mi venga chiesto solo ciò di cui è davvero incerto.

**Acceptance Criteria:**

**Given** le tre versioni dell'immagine
**When** l'estrazione gira
**Then** esegue almeno tre Pass che differiscono per almeno due assi fra modello, preprocessing e
inquadratura del prompt
**And** produce un Accordo per componente e complessivo, calcolato confrontando gli IR
canonicalizzati e **mai** leggendo un campo di confidence emesso da un modello (FR-2, AD-12).

**Given** una configurazione che imposta K minore di 3
**When** il sistema si avvia
**Then** l'avvio fallisce con messaggio esplicito (AD-12).

**Given** un valore illeggibile nell'immagine
**When** l'estrazione lo incontra
**Then** lo emette come assente con le alternative osservate
**And** non emette un valore plausibile inventato — verificato da un caso del gold set con un
valore deliberatamente cancellato.

**Given** due fili che si incrociano senza punto di giunzione
**When** l'estrazione li legge
**Then** non li collega.

### Story 3.4: Ridondanza testuale come secondo canale

As a studente,
I want che il sistema usi i valori scritti nel testo dell'esercizio per confermare quelli letti nel
disegno,
So that non mi chieda cose che erano già scritte nero su bianco.

**Acceptance Criteria:**

**Given** un esercizio in cui i valori compaiono sia nel disegno sia nel testo
**When** l'estrazione gira
**Then** i valori testuali sono conservati in un campo distinto e non fusi con le letture dal
disegno (FR-3)
**And** una lettura con Accordo basso confermata dal testo non genera Domanda mirata.

**Given** un disaccordo fra testo e disegno
**When** viene rilevato
**Then** genera sempre una Domanda mirata, qualunque sia l'Accordo.

### Story 3.5: Fondamenta del sistema di design

As a sviluppatore frontend,
I want token, scala tipografica e componenti di base implementati secondo il contratto UX,
So that ogni schermata successiva erediti coerenza e accessibilità invece di ricostruirle.

**Acceptance Criteria:**

**Given** il frontmatter di `DESIGN.md`
**When** il sistema di design è implementato
**Then** i 32 token colore esistono con le coppie chiaro/scuro complete, e i 7 ruoli tipografici
sono definiti (UX-DR1, UX-DR2)
**And** ogni quantità, residuo ed etichetta di disegno è resa con cifre tabulari (UX-DR3)
**And** la modalità scura è pari grado alla chiara, non un tema secondario (UX-DR20).

**Given** qualunque schermata costruita sulle fondamenta
**When** viene resa in scala di grigi
**Then** resta interpretabile: nessuno stato è portato dal solo colore (UX-DR12).

**Given** il vocabolario del Glossario del PRD
**When** l'interfaccia mostra un termine di dominio
**Then** usa esattamente quel termine, senza sinonimi (UX-DR23)
**And** i testi rispettano le sette regole di microcopy e non contengono parole della lista vietata
(UX-DR24).

**Given** una superficie con contenuto assente
**When** viene mostrata
**Then** offre un esempio reale caricabile con un tocco, non un'illustrazione (UX-DR25).

**Given** navigazione da tastiera su qualunque superficie
**When** il focus si sposta
**Then** è sempre visibile e non è portato dal solo colore (UX-DR15)
**And** ogni bersaglio di tocco misura almeno 44 × 44 px (UX-DR16)
**And** con `prefers-reduced-motion` attivo ogni transizione non essenziale è rimossa (UX-DR17).

### Story 3.6: Anteprima di ricostruzione con ancoraggio di provenienza

As a studente,
I want vedere il circuito che il sistema ha letto accanto alla mia foto, con ogni componente legato
al punto da cui viene,
So that possa accorgermi di un errore prima che il sistema calcoli qualcosa.

**Acceptance Criteria:**

**Given** un IR ricostruito, con o senza Ambiguità residua
**When** l'elaborazione arriva a questo punto
**Then** l'Anteprima è mostrata **sempre** e la conferma esplicita è richiesta
**And** nessuna soluzione è calcolata prima della conferma (FR-5).

**Given** l'Anteprima mostrata
**When** l'utente tocca un componente nella ricostruzione o una regione nella foto
**Then** l'ancoraggio si accende nell'altra vista, in entrambe le direzioni (UX-DR6).

**Given** nessuna correzione da fare
**When** l'utente conferma
**Then** la conferma è una singola azione.

**Given** un viewport di 360 px
**When** l'Anteprima è mostrata
**Then** usa una colonna singola con controllo a due stati, mai un accordion; a 768 px o più
passa a due colonne affiancate (UX-DR19).

**Given** l'elaborazione in corso
**When** l'utente attende
**Then** il progresso mostra le etichette reali degli stadi, non una barra generica (UX-DR18).

### Story 3.7: Domanda mirata, tetto di due giri e ripresa

As a studente,
I want che il sistema mi chieda solo ciò di cui è incerto, mostrandomi il pezzo di foto in
questione, e riprenda da dove era,
So that la correzione costi un tocco e non una ripartenza.

**Acceptance Criteria:**

**Given** un'Ambiguità residua sopravvissuta ad Accordo, Validazione elettrica e Ridondanza
testuale
**When** la Domanda mirata viene posta
**Then** mostra il ritaglio ingrandito della regione, le alternative osservate e sempre un campo
libero
**And** il contatore dei giri è visibile (UX-DR10)
**And** nessuna Domanda è posta per un elemento che ha superato i tre filtri (FR-6).

**Given** due giri di domande già posti e ambiguità ancora aperte
**When** il sistema dovrebbe porre un terzo giro
**Then** apre invece l'editor con l'IR corrente precaricato, preservando tutte le risposte già
date (FR-7).

**Given** un `resume_ref` valido
**When** la stessa chiamata viene ri-emessa
**Then** l'elaborazione riprende dallo stesso punto e produce lo stesso risultato
**And** un solo addebito è registrato (FR-8, AD-7).

**Given** un `resume_ref` appartenente a un altro soggetto o non firmato
**When** viene usato
**Then** la richiesta è rifiutata e nessun dato altrui è esposto (AD-6, AD-20).

**Given** un `resume_ref` scaduto
**When** viene usato
**Then** il messaggio offre di ripartire, non un errore opaco.

### Story 3.8: Editor del circuito

As a studente,
I want correggere direttamente ciò che il sistema ha letto male,
So that un'ambiguità che non si chiude con una domanda non mi blocchi.

**Acceptance Criteria:**

**Given** un IR ricostruito
**When** l'utente modifica valore, tipo, collegamento, polarità o grandezza richiesta
**Then** la modifica è registrata nell'IR come manuale, distinta da una lettura automatica (FR-9)
**And** è visibile come tale nell'Anteprima.

**Given** una modifica applicata
**When** l'utente prova a risolvere
**Then** la Validazione elettrica è rieseguita e il suo esito è mostrato prima che la risoluzione
parta.

**Given** l'editor aperto
**When** l'utente usa solo la tastiera
**Then** ogni modifica è raggiungibile e completabile (NFR-6).

---

## Epic 4: La soluzione che si può mostrare e portare via

La soluzione diventa un documento: passi con il circuito ridisegnato, studio progressivo, ed export
riconoscibili.

### Story 4.1: Passi con il circuito ridisegnato

As a studente,
I want vedere il circuito ridisegnato dopo ogni riduzione, non solo la formula,
So that possa ricopiare il procedimento come lo vuole il professore.

**Acceptance Criteria:**

**Given** un Piano didattico eseguito
**When** la soluzione è mostrata
**Then** ogni passo ha nome della Trasformazione, formula letterale, sostituzione numerica e
disegno del circuito risultante (UX-DR9)
**And** un passo senza disegno non esiste: è fuso con il precedente.

**Given** un viewport di 360 px
**When** un disegno è mostrato
**Then** è interamente visibile senza scorrimento orizzontale della pagina
**And** le etichette dei componenti restano a non meno di 11 px effettivi (FR-15, NFR-15).

**Given** un disegno qualsiasi
**When** viene letto da uno screen reader
**Then** l'alternativa testuale descrive la topologia risultante, non "schema del circuito"
(UX-DR14).

**Given** una formula
**When** viene resa
**Then** è composta come matematica accessibile e selezionabile, non come immagine (UX-DR26).

### Story 4.2: Badge di stato e pannello dei residui

As a studente,
I want poter controllare la prova con un tocco invece di fidarmi di un'etichetta,
So that la promessa di verifica sia dimostrata e non affermata.

**Acceptance Criteria:**

**Given** una soluzione con Badge Verificata
**When** l'utente tocca il badge
**Then** si apre il pannello con cinque righe — sempre le stesse cinque, sempre nello stesso
ordine, non riordinabili — ciascuna con nome del controllo, residuo in cifre tabulari ed esito
(UX-DR4, UX-DR8).

**Given** un Rifiuto di certificazione
**When** viene mostrato
**Then** usa la pillola "Non certificata" con cerchio barrato, **mai** rosso e **mai** icona di
allarme (UX-DR5)
**And** si distingue da un Guasto per colore **e** icona **e** parole, non per uno solo dei tre
(UX-DR13)
**And** nessun valore di risultato è mostrato.

**Given** un Rifiuto di certificazione
**When** l'utente arriva alla superficie
**Then** questa ha un indirizzo proprio, è condivisibile e sopravvive al ricaricamento (UX-DR22)
**And** nessun Credito risulta addebitato (FR-12).

### Story 4.3: Modalità Studio a rivelazione progressiva

As a studente che vuole capire,
I want provare a indovinare il passo successivo prima di vederlo, e capire perché sbaglio,
So that studiare mi serva più che copiare.

**Acceptance Criteria:**

**Given** una soluzione aperta in modalità Studio
**When** un passo è stato mostrato
**Then** il successivo non è visibile finché l'utente non ha risposto o esplicitamente saltato
(FR-17)
**And** nessuno stato avanza da solo dopo un tempo.

**Given** una risposta errata
**When** viene inviata
**Then** il sistema spiega *perché* è errata, evidenziando l'elemento sul disegno, prima di
rivelare il passo corretto.

**Given** qualunque risposta data in modalità Studio
**When** la sessione termina
**Then** nessun punteggio, percentuale o misura di rendimento è associato all'utente né persistito
(FR-17, AD-11).

### Story 4.4: Export multiformato

As a studente o tutor,
I want portare via la soluzione in PDF, LaTeX o SVG,
So that possa stamparla, allegarla o riusarla nei miei materiali.

**Acceptance Criteria:**

**Given** una Soluzione consegnata
**When** viene esportata
**Then** il PDF conserva i disegni come grafica vettoriale, e il LaTeX compila senza intervento
manuale nell'ambiente di riferimento documentato (FR-18)
**And** il LaTeX prodotto rispetta i vincoli d'ambiente: niente `lmodern`, niente babel italiano,
label CircuiTikZ con `=` racchiusi in graffe.

**Given** un export che fallisce
**When** l'errore si verifica
**Then** la causa è dichiarata e nessun file parziale è prodotto.

**Given** un artefatto prodotto da qualunque modulo
**When** il controllo di architettura gira
**Then** verifica che sia passato dall'unico punto di export (AD-10).

### Story 4.5: Marcatura di provenienza e stampa

As a docente,
I want riconoscere a colpo d'occhio un elaborato prodotto con Kirchhoff,
So that l'onestà sia facile e la disonestà visibile.

**Acceptance Criteria:**

**Given** un artefatto esportato in qualunque formato
**When** viene ispezionato
**Then** contiene metadati leggibili dalla macchina che dichiarano origine assistita da IA,
versione del sistema, momento di generazione e riferimento verificabile all'IR
**And** contiene un elemento visibile che dichiara la stessa cosa in linguaggio naturale (FR-19).

**Given** un PDF marcato
**When** viene copiato o ristampato in PDF
**Then** la marcatura sopravvive.

**Given** una soluzione stampata dal browser
**When** il foglio di stile di stampa si applica
**Then** la marcatura è presente e non rimovibile via CSS (UX-DR21).

---

## Epic 5: Account, Crediti e conformità in prodotto

Un utente si registra, compra Crediti, e paga solo per ciò che ha ottenuto davvero.

### Story 5.1: Identità come soggetto opaco, anonimo incluso

As a studente al primo contatto,
I want provare il prodotto senza registrarmi, e poi conservare quello che ho fatto se decido di
registrarmi,
So that l'iscrizione arrivi dopo il valore e non prima.

**Acceptance Criteria:**

**Given** una richiesta da un utente non autenticato
**When** entra nel sistema
**Then** porta un `subject_id` opaco legato alla sessione, della stessa forma di quello di un
utente autenticato (AD-20)
**And** firma, quota, ledger e chiave di idempotenza usano solo `subject_id`.

**Given** un utente anonimo che ha già ottenuto soluzioni
**When** collega un account
**Then** i soggetti sono fusi esplicitamente e la cronologia è trasferita
**And** nessun Credito o soluzione va perso nella fusione.

### Story 5.2: Registrazione con dichiarazione di età

As a operatore del servizio,
I want che ogni utente dichiari di avere l'età minima al momento della registrazione,
So that l'obbligo sull'accesso dei minori sia soddisfatto e documentabile.

**Acceptance Criteria:**

**Given** un modulo di registrazione
**When** l'utente non dichiara l'età minima
**Then** la registrazione non si completa (FR-28).

**Given** un account che risulta non conforme
**When** viene segnalato
**Then** esiste una procedura documentata di rimozione, ed è eseguibile.

### Story 5.3: Ledger dei Crediti idempotente

As a studente,
I want pagare solo quando ottengo davvero una soluzione certificata,
So that un rifiuto, un guasto o una domanda intermedia non mi costino nulla.

**Acceptance Criteria:**

**Given** una Soluzione consegnata con Badge Verificata
**When** viene mostrata
**Then** un Credito è consumato e il saldo aggiornato (FR-26).

**Given** un Rifiuto di certificazione, un guasto di sistema, o una ripresa dopo Domanda mirata
**When** l'operazione si conclude
**Then** nessun Credito è consumato.

**Given** la stessa operazione addebitabile ripetuta con la stessa chiave di idempotenza
**When** arriva al ledger
**Then** il vincolo di unicità a livello di schema impedisce il secondo addebito (AD-7)
**And** la risposta è identica alla prima.

**Given** un saldo insufficiente
**When** l'utente sta per iniziare un'elaborazione
**Then** il saldo e le opzioni sono mostrati **prima** dell'elaborazione, mai dopo aver fatto
lavorare l'utente.

### Story 5.4: Acquisto di Crediti e piani

As a studente sotto esame,
I want comprare quello che mi serve in pochi secondi,
So that l'acquisto non sia l'ostacolo alle due di notte.

**Acceptance Criteria:**

**Given** il listino
**When** i prezzi sono mostrati a un consumatore
**Then** includono le imposte applicabili (FR-27)
**And** un piano a tempo dichiara il proprio limite di uso equo prima dell'acquisto.

**Given** un acquisto completato
**When** l'utente lo cerca
**Then** la ricevuta o fattura è disponibile.

### Story 5.5: Dichiarazione d'uso dell'IA su ogni superficie

As a utente,
I want sapere subito che sto usando un sistema di intelligenza artificiale,
So that possa valutare quello che leggo con il giusto criterio.

**Acceptance Criteria:**

**Given** il primo contatto con qualunque superficie — web, Studio, pannello assistente
**When** la superficie viene mostrata
**Then** la dichiarazione è visibile senza alcuna interazione, prima di qualunque caricamento
(FR-29, UX-DR11)
**And** non è chiudibile.

**Given** i soli termini di servizio che contengono la dichiarazione
**When** la conformità viene verificata
**Then** questo non è sufficiente: la dichiarazione in prodotto è richiesta.

### Story 5.6: Ciclo di vita e minimizzazione dei dati dell'immagine

As a studente,
I want che la foto del mio compito sparisca appena non serve più,
So that il mio nome e la mia matricola non restino su un server.

**Acceptance Criteria:**

**Given** un'immagine sorgente caricata
**When** sono trascorse 72 ore dall'estrazione dell'IR
**Then** l'oggetto non esiste più, per effetto della lifecycle policy dello storage e non di un job
applicativo (FR-30, AD-9)
**And** un controllo automatico fallisce se trova un oggetto oltre TTL.

**Given** l'IR e la Soluzione
**When** l'immagine è stata cancellata
**Then** restano disponibili.

**Given** un'immagine con regioni testuali non circuitali
**When** l'utente sceglie di offuscarle
**Then** l'offuscamento avviene **prima** della trasmissione a qualunque fornitore esterno (FR-31)
**And** l'avviso a non includere dati identificativi è mostrato al caricamento.

**Given** un nuovo account
**When** l'impostazione di uso dei contenuti per il miglioramento viene letta
**Then** è disattivata (FR-32)
**And** la revoca ha effetto sugli usi successivi ed è ispezionabile dall'utente.

### Story 5.7: Diritti dell'interessato e segnalazione di errore

As a utente,
I want poter accedere ai miei dati, portarli via, cancellarli, e dire quando una soluzione è
sbagliata,
So that il controllo resti mio e gli errori del sistema diventino misurabili.

**Acceptance Criteria:**

**Given** una richiesta di accesso, portabilità o cancellazione
**When** viene presentata
**Then** è evasa entro il termine di legge (FR-33)
**And** la cancellazione dell'account rimuove IR e Soluzioni entro il termine dichiarato.

**Given** una Soluzione consegnata che l'utente ritiene sbagliata
**When** la segnala dall'artefatto stesso
**Then** la segnalazione allega automaticamente l'IR e l'identificativo della soluzione (FR-35)
**And** le segnalazioni sono conteggiate per mille Soluzioni consegnate come indicatore
anticipatore di SER.

### Story 5.8: Quota per soggetto anonimo

As a studente che incontra Kirchhoff dentro una conversazione,
I want provare il prodotto senza registrarmi e capire chiaramente quando la prova finisce,
So that l'iscrizione arrivi dopo che il valore è atterrato, non prima.

**Acceptance Criteria:**

**Given** un `subject_id` anonimo senza account
**When** chiede la prima soluzione
**Then** la riceve **completa** — badge, residui, passaggi, disegni (FR-36)
**And** nessun limite gli è mostrato prima di quel momento.

**Given** una quota esaurita
**When** il soggetto chiede un'altra soluzione
**Then** la superficie mostra il collegamento al dominio proprio, non un modale di pagamento
**And** il conteggio è **per soggetto**, non per mese di calendario: in conversazione non esiste
un account su cui contare un ciclo.

**Given** un soggetto anonimo che ricrea la sessione per azzerare la quota
**When** torna
**Then** il sistema lo rileva e la quota non riparte.

**Given** una fusione di soggetti al collegamento dell'account (FR-21)
**When** avviene
**Then** la quota consumata segue il soggetto e non si azzera.

---

## Epic 6: Studio — varianti verificate per chi insegna

Un tutor prende un esercizio e ne ottiene N varianti con soluzione completa verificata.

### Story 6.1: Banco esercizi del tenant con isolamento a livello di database

As a tutor,
I want un archivio dei miei esercizi che nessun altro possa vedere,
So that il mio materiale resti mio.

**Acceptance Criteria:**

**Given** due tenant distinti
**When** uno interroga il proprio banco
**Then** nessun record dell'altro è raggiungibile, per effetto della row-level security e non del
solo filtro applicativo (FR-25, AD-14).

**Given** un esercizio nel banco
**When** viene etichettato
**Then** supporta almeno corso, ateneo, argomento e difficoltà, ed è ritrovabile per ciascuno.

### Story 6.2: Generazione di Varianti verificate

As a tutor,
I want dodici versioni dello stesso esercizio con valori diversi,
So that i miei studenti non possano passarsi la soluzione.

**Acceptance Criteria:**

**Given** un esercizio sorgente e un numero N di Varianti richieste
**When** la generazione gira
**Then** ogni Variante consegnata ha superato la Verifica esattamente come una Soluzione consegnata
(FR-22, AD-5)
**And** le Varianti differiscono nei valori e coincidono nella struttura simbolica.

**Given** una Variante che non supera la Verifica
**When** la generazione si conclude
**Then** non è consegnata, non è conteggiata verso N, ed è **mostrata** nella rassegna con il
motivo dello scarto — non nascosta.

**Given** una Variante verificata
**When** viene persistita
**Then** `studio` scrive solo il record `Variant`, che referenzia il `Published` per id, e non
scrive mai un `Published` (AD-8).

### Story 6.3: Vincoli di generazione

As a tutor,
I want che i valori generati siano realistici e i risultati leggibili,
So that le varianti sembrino esercizi veri e non numeri casuali.

**Acceptance Criteria:**

**Given** un vincolo di serie di valori, un intervallo, o una proprietà del risultato
**When** la generazione gira
**Then** nessuna Variante che li viola è consegnata (FR-23).

**Given** un insieme di vincoli insoddisfacibile
**When** la generazione gira
**Then** il sistema lo dichiara esplicitamente
**And** non produce in silenzio meno Varianti del richiesto.

### Story 6.4: Fogli soluzione separati e verificabili

As a tutor,
I want un foglio soluzione distinto per ogni variante, con un modo di verificare che sia il suo,
So that non consegni per errore la soluzione della variante sbagliata.

**Acceptance Criteria:**

**Given** una Variante consegnata
**When** viene esportata
**Then** il Foglio soluzione è un artefatto distinto dal testo dell'esercizio ed è esportabile
separatamente (FR-24).

**Given** un Foglio soluzione e una Variante
**When** il checksum viene confrontato
**Then** conferma o smentisce che appartengano alla stessa generazione.

**Given** un insieme di Varianti generate
**When** l'utente esporta in blocco
**Then** ottiene testi e fogli soluzione in un'unica operazione, con la Marcatura di provenienza su
ognuno (AD-10).

---

## Epic 7: Kirchhoff dentro l'assistente

Lo studente risolve senza uscire dalla conversazione che ha già aperto.

### Story 7.1: Contratto della superficie assistente

As a sviluppatore di un host assistente,
I want un contratto minimo, versionato e stabile,
So that l'integrazione non si rompa senza preavviso.

**Acceptance Criteria:**

**Given** la superficie esposta
**When** viene ispezionata
**Then** espone il numero minimo di operazioni che copre il flusso, non il massimo possibile
(AD-16)
**And** dichiara la propria versione.

**Given** una modifica che rompe la compatibilità
**When** viene rilasciata
**Then** è preceduta da una deprecazione annunciata con periodo di sovrapposizione.

**Given** una risposta che alimenta un pannello
**When** viene prodotta
**Then** porta **anche** un riassunto testuale strutturato di ciò che l'utente sta guardando
(AD-16, FR-20).

### Story 7.2: Pannello di conferma in conversazione

As a studente,
I want confermare la ricostruzione senza uscire dalla conversazione,
So that non debba cambiare applicazione a metà di un problema.

**Acceptance Criteria:**

**Given** un'immagine inviata attraverso un assistente
**When** il flusso parte
**Then** l'Anteprima e le Domande mirate sono utilizzabili dentro il pannello (FR-20)
**And** il pannello non conserva alcuno stato locale fra un giro e l'altro (AD-6).

**Given** il pannello in conversazione
**When** l'utente lo usa
**Then** la dichiarazione d'uso dell'IA è presente anche qui (FR-29)
**And** l'accessibilità è pari a quella della superficie web (NFR-6).

**Given** una soluzione prodotta su questa superficie
**When** attraversa il sistema
**Then** anteprima obbligatoria, tetto di due giri, gate di verifica e Rifiuto valgono identici,
senza scorciatoie (FR-20).

### Story 7.3: Collegamento dell'account dalla conversazione

As a studente arrivato da un assistente,
I want conservare cronologia e Crediti se decido di restare,
So that il canale mi porti un prodotto e non solo una risposta.

**Acceptance Criteria:**

**Given** un utente non collegato
**When** ottiene la prima Soluzione consegnata
**Then** solo allora il collegamento dell'account è proposto, mai prima (FR-21).

**Given** un utente non collegato
**When** opera sulla superficie
**Then** vale una quota di prova legata alla sessione.

**Given** un collegamento completato
**When** l'utente apre la propria cronologia
**Then** ciò che ha prodotto nella sessione è presente (AD-20).

---

## Copertura dei requisiti UX

| UX-DR | Storia che lo copre |
|---|---|
| UX-DR1, UX-DR2, UX-DR3, UX-DR20 | 3.5 |
| UX-DR4, UX-DR8 | 4.2 |
| UX-DR5, UX-DR13 | 4.2 |
| UX-DR6, UX-DR19 | 3.6 |
| UX-DR7 | 3.5 |
| UX-DR9, UX-DR14, UX-DR26 | 4.1 |
| UX-DR10 | 3.7 |
| UX-DR11 | 5.5 |
| UX-DR12, UX-DR15, UX-DR16, UX-DR17 | 3.5 |
| UX-DR18 | 3.6 |
| UX-DR21 | 4.5 |
| UX-DR22 | 4.2 |
| UX-DR23, UX-DR24, UX-DR25 | 3.5 |

Copertura: **26/26 UX-DR** assegnati ad almeno una storia.

## Totali

**7 epiche · 40 storie.**

| Epica | Storie |
|---|---|
| 1 — La struttura di misura | 2 |
| 2 — Motore verificato da riga di comando | 11 |
| 3 — Dalla foto al circuito confermato | 8 |
| 4 — La soluzione che si può mostrare e portare via | 5 |
| 5 — Account, Crediti e conformità in prodotto | 7 |
| 6 — Studio: varianti verificate per chi insegna | 4 |
| 7 — Kirchhoff dentro l'assistente | 3 |

Nessuna storia dipende da una storia successiva della stessa epica; nessuna epica richiede
un'epica successiva per funzionare.

---

## Validazione finale

Eseguita secondo `step-04-final-validation.md`.

**Copertura FR.** 35/35 citati dentro il corpo delle storie, non solo nella mappa. Otto FR
(FR-3, FR-4, FR-10, FR-11, FR-13, FR-14, FR-16, FR-34) erano coperti dalla mappa ma non
richiamati nei criteri di accettazione: **corretto in questa validazione**, perché lo sviluppatore
legge la storia, non la mappa.

**Copertura UX-DR.** 26/26 assegnati ad almeno una storia.

**Copertura AD.** Tutti e 20 gli AD dello spine sono richiamati da almeno un criterio di
accettazione. Nessun invariante di architettura resta senza una storia che lo renda verificabile.

**Template starter.** L'architettura non ne specifica nessuno. La struttura è quindi creata a mano
nella Story 2.1, che include il controllo automatico dei confini di dipendenza — senza quello, il
paradigma dello spine sarebbe una raccomandazione anziché un vincolo.

**Creazione di entità.** Nessuna storia crea schema in anticipo. Ogni entità nasce nella prima
storia che ne ha bisogno: `IR` in 2.2, `Published` in 2.8, `CreditLedger` in 5.3, banco e
`Variant` in 6.1 e 6.2. Non esiste una storia "crea tutte le tabelle".

**Criteri di accettazione.** Tutte le 40 storie hanno almeno un blocco Given/When/Then. Le
condizioni negative — quelle che verificano che il sistema *non* faccia qualcosa — sono presenti
dove contano: assenza di bypass del gate (2.8), nessun valore inventato (3.3), nessun punteggio
persistito (4.3), nessun doppio addebito (5.3), nessun accesso cross-tenant (6.1).

**Dipendenze in avanti.** Nessuna storia richiede una storia successiva della propria epica.
Verifica per campione sui punti più a rischio: la 3.6 (Anteprima) non richiede la 3.7 (Domanda
mirata), perché l'Anteprima si mostra anche quando non ci sono ambiguità — ed è precisamente il
requisito FR-5. La 2.7 (Verifica) non richiede la 2.8 (gate), perché i cinque controlli sono
calcolabili e testabili prima che esista il punto unico di pubblicazione.

**Indipendenza delle epiche.** Ogni epica funziona senza le successive. Il caso limite è Epic 2,
che usa la struttura di misura di Epic 1: se Epic 1 non fosse fatta, Epic 2 funzionerebbe comunque
e resterebbe soltanto non misurata.

**Sovrapposizione sui file.** Le sette epiche insistono su zone distinte dell'albero sorgente. La
condivisione è incidentale — tutte leggono l'IR — e non è "stesso componente end-to-end": nessun
consolidamento richiesto.

**Rilievo aperto, non risolvibile qui.** Epic 1 non ha valore per un utente finale: il suo utente è
il fondatore. È una deviazione consapevole dal principio "ogni epica deve abilitare un risultato
utente", accettata perché senza apparato di misura nessuna affermazione sulla qualità è
verificabile.

**Cambio del 13 agosto 2026.** Epic 1 originariamente misurava anche la baseline dei modelli
frontier ed era il gate di kill del piano. L'utente ha deciso di saltare quella misura. Epic 1 è
stata ridefinita e tre storie sono state rimosse; il dettaglio, l'impatto e il prezzo della scelta
sono in `sprint-change-proposal-2026-08-13.md`.
