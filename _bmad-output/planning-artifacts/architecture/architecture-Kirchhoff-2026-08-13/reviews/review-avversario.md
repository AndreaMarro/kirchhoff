---
name: 'Kirchhoff — review avversaria della Spine v2'
type: architecture-review
lens: 'avversaria — due unità conformi alla lettera e incompatibili di fatto'
target: 'ARCHITECTURE-SPINE.md v2 (640 righe, AD-1…AD-30, aggiornata 15 ago 2026)'
sources:
  - ../ARCHITECTURE-SPINE.md
  - ../../../prds/prd-Kirchhoff-2026-08-13/prd.md
  - ../.memlog.md
created: '2026-08-15'
verdict: 'La v2 tiene come lista di invarianti e cede come substrato di costruzione: cinque coppie critiche e tre secondarie si costruiscono conformi e non si integrano.'
---

# Review avversaria — Architecture Spine v2

## Metodo

Non ho cercato contraddizioni fra AD. Ne ho cercate poche e le ho scartate quasi tutte: la v2 è
internamente coerente riga per riga. Ho cercato la cosa più costosa, che è un'altra: **due unità
di costruzione, un livello sotto lo spine, ciascuna che obbedisce alla lettera a ogni AD-1…AD-30,
che nondimeno producono strutture che non si incastrano.**

Per ogni coppia il formato è fisso:

- **Le due unità** — nome, collocazione, mandato, e gli AD che ciascuna cita per costruirsi.
- **Perché entrambe sono conformi** — con il testo dello spine, non con una parafrasi.
- **La forma divergente** — il dato conteso e i due modi legittimi di modellarlo.
- **Il punto di rottura** — un test che passa dentro entrambe le unità e fallisce all'integrazione.
- **La chiusura** — testo di spine, non un consiglio.

Il criterio di ammissione è severo: se una delle due unità deve *interpretare* uno spazio bianco
per divergere, la coppia vale; se deve *violare* una riga, la coppia non vale e l'ho scartata.
Le esclusioni sono elencate in fondo, perché un avversario che non dichiara i falsi positivi non è
verificabile.

## Verdetto

**La v2 regge come dichiarazione di invarianti e cede come substrato di costruzione.** Le dieci
decisioni nuove sono state aggiunte alla lista degli invarianti **senza ri-derivare il seed
strutturale**: `Albero sorgente`, `Entità di dominio` (ERD) e `Capability → Architecture Map` sono
rimasti alla v1. Nell'albero non esistono `perception/`, `corpus/`, `experiment/`, `kernel/`,
`domain/proof`, `domain/truthfulness`, `render/layout`; nell'ERD non esistono `LayoutIR`,
`ProofGraph`, `Claim`, `SourceAsset`; la colonna *Governed by* della mappa capability cita solo
`AD-1…AD-15`. **Otto delle coppie qui sotto nascono dentro quella distanza**, e cinque di esse
colpiscono l'oggetto che Gate A deve misurare.

Le due frizioni che l'incarico indicava come sospette esistono entrambe e sono confermate
(C2 e C3), ma **non sono le più gravi**. La più grave è C1, che rende il kill criterion
non falsificabile senza che nessuno debba sbagliare.

| # | Coppia | Attrito | Gravità |
|---|---|---|---|
| **C1** | `render/layout` × `eval/metrics/vcer` | AD-22 × AD-15 em. | 🔴 critica |
| **C2** | `domain/solve/path_b` × `render/layout` | AD-1 em. × AD-2 em./AD-21 | 🔴 critica |
| **C3** | `render/svg_semantic` × `render/circuitikz` | AD-5 em. × AD-10/AD-18 | 🔴 critica |
| **C4** | `domain/proof` × `pipeline/ingest` | AD-8 × AD-2 em./AD-21/AD-29 | 🔴 critica |
| **C5** | `experiment/` × `api/` | AD-11 × AD-26/FR-47/SM-21 | 🟠 alta |
| **C6** | `domain/truthfulness` × `adapters/blob` | AD-9 × AD-25/AD-30 | 🟠 alta |
| **C7** | `domain/verify/roundtrip` × `render/validate_patch` | AD-19 × AD-5 em./AD-22 | 🟠 alta |
| **C8** | `ui/proof_replay` × `api/assistant` | AD-6/AD-16 × AD-21/FR-48 | 🟡 media |

---

## C1 — L'invariante di conservazione è insieme una guardia e una misura, e nessun AD dice quale 🔴

*La coppia più grave del documento. Non produce un errore: produce un numero.*

### Le due unità

**U1 — `render/layout` · applicatore di `LayoutPatch`.** È l'unità che riceve `Layout(Cₖ)` e il
`LayoutPatch` e produce `Layout(Cₖ₊₁)`. Si costruisce su AD-22, che le dice cosa fare di un patch
mal formato: «Un `LayoutPatch` con `preserve` più piccolo di `Pₖ` è **non conforme** e viene
rifiutato in validazione, non ottimizzato.» U1 legge l'invariante di conservazione come **una
precondizione booleana**: un patch che non conserva è respinto prima di disegnare. Costruisce
`validate_patch(patch, P_k) → Ok | Refusal`.

**U2 — `eval/metrics/vcer` · calcolo di VCER.** Si costruisce su AD-15 emendato: «l'harness calcola
**ogni** metrica di §8 … **a ogni esecuzione, con o senza soglia fissata**. … Vale in particolare
per **VCER**: è la grandezza su cui Gate A decide se il prodotto continua, e un gate senza ingresso
non è un gate.» U2 legge l'invariante come **una grandezza continua da contare**: costruisce
`vcer(patches) → rate`, cioè la quota di patch che violano la conservazione su almeno un elemento
di `preserve`.

### Perché entrambe sono conformi

Perché AD-22 parla **dell'insieme** e non **delle posizioni**. La sua frase di rifiuto riguarda un
`preserve` *più piccolo di* `Pₖ` — una condizione di appartenenza. Sullo scostamento geometrico di
un elemento correttamente incluso in `preserve`, **lo spine non dice niente**: non dice chi lo
controlla, non dice se sia un rifiuto o una misura, e non fissa alcuna tolleranza.

Il PRD, che è la fonte, dice due cose diverse in due punti:

- **FR-38, corretto il 15 agosto:** «`p_{k+1}(x) ≈ p_k(x)` … salvo necessità geometriche
  dimostrabili. Ogni scostamento è **misurato e penalizzato da SM-14 (VCER)**, mai assolto come
  libertà del renderer.» → è una **misura**, con tolleranza, e l'uguaglianza esatta è dichiarata
  *troppo forte*: «un invariante che il rendering reale viola sempre smette di essere un gate».
- **SM-14, §8:** «Quota di `LayoutPatch` che violano **`p_{k+1}(x) = p_k(x)`** su almeno un
  `x ∈ preserve`.» → uguaglianza **esatta**, cioè una **guardia**.

Lo spine non arbitra fra i due e non riporta né il `≈` né la tolleranza. U1 e U2 leggono lo stesso
corpus e ne estraggono due tipi: `Invariant as Guard` e `Invariant as Rate`.

### La forma divergente

| | U1 `render/layout` | U2 `eval/metrics/vcer` |
|---|---|---|
| Tipo dell'invariante | predicato booleano, precondizione | tasso su popolazione |
| Predicato | `p_{k+1}(x) == p_k(x)` (SM-14) | `dist(p_{k+1}(x), p_k(x)) ≤ τ` (FR-38) |
| `τ` | non esiste: è esatto | inventata dall'unità, nessun documento la fissa |
| Esito su violazione | `Refusal` — il patch non viene applicato | `+1` al numeratore — il patch viene applicato |

### Il punto di rottura

Non è un crash. È **una selezione**.

U1 rifiuta in validazione i patch che violano la conservazione. U2 misura VCER sui patch che
**sono stati applicati** — cioè sui sopravvissuti al filtro di U1, che usa lo stesso predicato.
La popolazione su cui si calcola la metrica del kill criterion è quella che la metrica del kill
criterion ha già ripulito. **VCER tende strutturalmente a zero**, e tende a zero *tanto più
rapidamente quanto più il gate è severo*.

Entrambe le unità passano i propri test. Il test di U1 verifica che un patch che sposta un
preservato sia rifiutato: passa. Il test di U2 verifica che VCER conti correttamente le violazioni
su un input sintetico: passa. All'integrazione, su corpus reale, VCER risulta `0.00` e **il gate
che «può uccidere l'idea» non può più farlo**. Il fallimento non è visibile come fallimento: si
presenta come un risultato eccellente.

Il PRD conosce esattamente questo schema e lo chiude altrove: **SM-20** — «Un renderer non
deterministico rende RRC non falsificabile, quindi si misura prima di leggere RRC, VCER e SEC».
Esiste la difesa per RRC. **Non esiste l'analoga per VCER**, ed è VCER la metrica del kill
criterion.

C'è il corollario simmetrico, di segno opposto. Se U1 adotta invece il `≈` di FR-38 con una `τ`
propria e U2 ne adotta un'altra, **il numero che decide se il prodotto esiste dipende da quale
unità lo si chiede**, e i due valori non sono confrontabili fra bracci né fra esecuzioni. AD-22 ha
chiuso l'autocertificazione dal lato di chi *dichiara* `preserve`; è rimasta aperta dal lato di chi
*definisce l'uguaglianza*.

### La chiusura

> **AD-31 — L'invariante di conservazione ha una sola definizione, un solo proprietario, e non
> filtra la propria popolazione.**
>
> - **Binds:** `domain/layout_invariant`, `render/layout`, `eval/`, AD-22, AD-15, FR-38, SM-14
> - **Prevents:** che la grandezza del kill criterion sia calcolata su una popolazione già filtrata
>   dallo stesso predicato, e che due unità la definiscano con due tolleranze.
> - **Rule:** il predicato di conservazione è **una sola funzione**, `preserved(x, p_k, p_{k+1}) →
>   Deviation`, in `domain/layout_invariant`, con la tolleranza `τ` **costante nominata e
>   versionata col codice**, importata sia dal validatore sia dall'harness. Nessuna unità ne
>   ridefinisce una propria.
>   L'invariante **di appartenenza** (`preserve ⊇ Pₖ`, AD-22) è una **guardia**: rifiuta.
>   L'invariante **di posizione** (`p_{k+1}(x) ≈ p_k(x)`) è una **misura**: non rifiuta mai, si
>   registra. Un `render/layout` che rifiuta un patch per scostamento geometrico è non conforme.
>   VCER è calcolata su **tutti** i patch emessi dalle Trasformazioni, inclusi quelli rifiutati da
>   AD-22, che entrano come violazione, non come esclusione. La cardinalità del denominatore è
>   pubblicata insieme al tasso: un VCER senza denominatore non è una misura.
>   SM-14 va riallineata a `≈`; l'uguaglianza esatta resta solo su identità e ordine relativo
>   (FR-38: «L'identità non ha tolleranza»).

---

## C2 — Il `LayoutPatch` non ha un veicolo legale fra dominio e renderer 🔴

*La frizione indicata nell'incarico fra AD-18 e AD-2 emendata esiste, ed è la seconda metà di questa.*

### Le due unità

**U1 — `domain/solve/path_b` · esecutore del Piano didattico.** È uno stadio della pipeline. Si
costruisce su AD-1 emendato, che è categorico sulla firma: «ogni stadio ha firma
`(CircuitIR, ctx) → CircuitIR | Refusal`» e «Nessuno stadio a valle dell'estrazione legge
l'immagine sorgente: **se un dato serve, sta nel `CircuitIR` o non esiste**.» U1 costruisce una
catena di stadi che si passano `CircuitIR` e nient'altro.

**U2 — `render/layout` · applicatore del patch.** Si costruisce su AD-2 emendato: «il disegno …
è ciò che il renderer produce **applicando il `LayoutPatch` al `LayoutIR` precedente**», e su AD-22:
«Il renderer **non espone alcuna funzione** per proporre un `preserve` proprio: **lo riceve**.» U2
costruisce `apply(layout_k, patch) → layout_{k+1}` e attende che qualcuno le consegni il patch.

### Perché entrambe sono conformi

- AD-2 dice che la Trasformazione **restituisce** `(CircuitIR, TransformResult)`, e che
  `TransformResult` porta `PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate`.
- AD-1 dice che **uno stadio** restituisce `CircuitIR | Refusal` — un solo membro.
- AD-21 dice che «Nessuno dei quattro contiene un riferimento a un altro se non per identificatore»
  e che gli altri tre «**non entrano mai in una firma di stadio**».

Le tre righe sono singolarmente ineccepibili e insieme non lasciano **nessun canale** al
`LayoutPatch` per arrivare dal dominio al renderer:

- non può viaggiare nel valore di ritorno dello stadio → AD-1 lo vieta (un solo membro, `CircuitIR`);
- non può stare dentro il `CircuitIR` → AD-21 lo vieta (nessuno contiene un altro), e sarebbe la
  fusione che AD-21 esiste per impedire;
- non può essere il `LayoutIR` → AD-1 emendato lo vieta esplicitamente nelle firme di stadio;
- resta `ctx`, che **lo spine non definisce in nessun punto**.

E qui entra AD-18, **non emendato**, che resta in vigore alla lettera e offre a U1 una via d'uscita
apparentemente ortodossa. La sua motivazione è ormai falsa — «AD-2 dice che una Trasformazione
produce `(IR, Drawing)`» non è più vero dal 15 agosto — ma la sua **regola** vale: «`Drawing` è una
struttura dichiarativa di dominio — nodi, rami, **posizioni logiche**, etichette.» Un'unità che
legge AD-18 costruisce, dentro il dominio, una struttura che contiene posizioni: **una quinta
rappresentazione**, che AD-21 non vieta perché AD-21 governa solo i quattro tipi che nomina.

### La forma divergente

U1, dovendo far viaggiare qualcosa e trovando `ctx` non definito, sceglie una delle due strade
legittime: **(a)** deposita il `TransformResult` in `ctx` come effetto collaterale, trasformando
`ctx` in un canale mutabile — cioè esattamente la «struttura ad hoc» che AD-1 esiste per prevenire,
ma dentro un parametro che AD-1 stesso nomina; **(b)** emette un `Drawing` conforme ad AD-18, con
posizioni logiche calcolate nel dominio.

U2, in entrambi i casi, non lo riceve: attende un `LayoutPatch` e trova o un `ctx` opaco o un
`Drawing` con posizioni **già decise a monte**. Nella variante (b) esistono due autorità sulla
posizione: `Drawing.posizioni_logiche` (dominio) e `LayoutIR` (renderer). Il `preserve` è calcolato
su una, il disegno mostrato all'utente deriva dall'altra, **e VCER misura la prima mentre lo
studente guarda la seconda**.

### Il punto di rottura

Test di U1: «`transform(ir, params)` restituisce un `TransformResult` con `boundary` non vuoto e
`preserve = Pₖ`» — passa. Test di U2: «`apply(layout_k, patch)` conserva la posizione di ogni
`x ∈ preserve`» — passa, sul patch di fixture. All'integrazione, `pipeline/` non ha una firma in cui
il patch possa transitare: o si emenda AD-1, o il patch viaggia in un canale non dichiarato, e
**A-0 diventa non verificabile end-to-end** perché la sola prova che il patch applicato sia quello
emesso dalla Trasformazione è una convenzione fra due moduli.

### La chiusura

> **Emendamento in loco ad AD-1 (v2.1).** La firma di stadio diventa
> `(CircuitIR, ctx) → StageResult | Refusal`, con `StageResult = { ir: CircuitIR, transform:
> TransformResult? }`. `ctx` è **immutabile e di sola lettura** per gli stadi: non è un canale.
> La clausola «se un dato serve, sta nel `CircuitIR` o non esiste» si legge d'ora in poi «sta nel
> `CircuitIR` o nel `TransformResult` del passo, o non esiste».
>
> **AD-32 — Il `LayoutPatch` viaggia sull'arco del `ProofGraph`, e da nessun'altra parte.**
> AD-29 stabilisce «archi = `Transform`». L'arco è quindi il **solo** portatore del
> `TransformResult`, e `render/layout` lo legge **dall'arco**, mai da un valore di ritorno di
> pipeline né da `ctx`. Il patch applicato e il patch registrato sono lo stesso oggetto, per
> costruzione e non per disciplina.
>
> **Ritiro di AD-18 e sostituzione.** `Drawing` **non esiste più** come tipo. AD-18 va riscritta,
> conservando il numero: la sua regola diventa «`domain/` non produce alcuna struttura che contenga
> posizioni. Le posizioni vivono **solo** nel `LayoutIR`, prodotto da `render/layout`. Il dominio
> non sa cosa sia un pixel **né una coordinata**.» La motivazione di AD-18 va riscritta perché cita
> un AD-2 che non esiste più: **una motivazione falsa in un invariante in vigore è un difetto, non
> un residuo storico.**

---

## C3 — Il disegno certificato e il disegno consegnato non sono lo stesso disegno 🔴

*La seconda frizione indicata nell'incarico: AD-10 × il round-trip che ora consuma l'SVG semantico.*

### Le due unità

**U1 — `render/svg_semantic`.** Serializza `LayoutIR + CircuitIR` in SVG semantico con
`data-component-id` e `data-terminal-*`. Esiste perché AD-5 emendato lo richiede *dentro* il gate:
«il Badge Verificata è applicato se e solo se … **l'SVG semantico, riparsato e canonicalizzato,
riproduce esattamente il `CircuitIR` atteso** … Il round-trip è **dentro `publish()`**». U1 produce
un ingresso di certificazione, non un file per l'utente: non applica marcatura.

**U2 — `render/circuitikz` + `render/pdf`.** Produce l'artefatto che l'utente scarica. Esiste perché
AD-10 lo impone: «ogni artefatto passa da `export(published, format) → Artifact`, che applica
marcatura leggibile dalla macchina e visibile. **Nessun altro modulo scrive file destinati
all'utente.**» Lo Stack conferma la catena: `CircuiTikZ + pdflatex`.

### Perché entrambe sono conformi

AD-10 vincola **l'origine** degli artefatti e la **marcatura**; non dice una parola sul fatto che
l'artefatto esportato debba essere *lo stesso disegno* che ha superato il round-trip. AD-5 vincola
il round-trip **sull'SVG semantico** — l'unico formato che possa avere `data-component-id`. Nessuna
riga dello spine collega i due.

E c'è un vincolo di ordine che chiude la porta anche volendo: `export()` prende in ingresso un
`published`, e `published` esiste **solo dopo** `publish()`, che a sua volta richiede il round-trip.
La marcatura di provenienza è quindi applicata **dopo** la certificazione, per costruzione. Il
byte-stream certificato non è mai quello consegnato.

### La forma divergente

Due nozioni di «il disegno del passo»:

| | U1 | U2 |
|---|---|---|
| Formato | SVG semantico, attributi `data-*` | CircuiTikZ → PDF, e SVG marcato |
| Round-trip | obbligatorio, esatto, sul grafo | **impossibile**: LaTeX non porta `data-component-id` |
| Marcatura | assente | presente, applicata dopo il gate |
| Chi lo vede | nessuno | l'utente, il docente, il revisore |

### Il punto di rottura

Un utente esporta il PDF di una Soluzione. Il PDF porta il **Badge Verificata** e la Marcatura di
provenienza, entrambi legittimi. Il disegno dentro quel PDF **non è mai stato sottoposto ad alcun
round-trip**: è stato prodotto da una seconda catena di rendering, che nessun AD obbliga a
coincidere con la prima. K-0 dice che il disegno fa parte della prova; qui il disegno che fa parte
della prova e il disegno che l'utente riceve sono due oggetti diversi, generati da due unità
diverse, e il Badge è attaccato al secondo dopo essere stato guadagnato dal primo.

La variante SVG è più sottile e altrettanto reale: se `export()` ri-serializza o ottimizza l'SVG
mentre applica la marcatura — riscrittura di `id`, rimozione di attributi `data-*` sconosciuti,
minificazione, che è il comportamento predefinito di ogni ottimizzatore SVG — l'artefatto
consegnato **non ricostruisce più il `CircuitIR`**, e non esiste alcun punto in cui questo venga
notato: il round-trip è già avvenuto, a monte, su un'altra stringa.

Entrambe le unità hanno test verdi. U1: «l'SVG semantico riparsa esattamente». U2: «ogni artefatto
esportato porta la marcatura». Nessun test dello spine chiede: *l'artefatto esportato riparsa
esattamente?* — e SM-16 (RRC) misura «la quota di **rendering**» il cui SVG riparsa, non la quota di
**artefatti consegnati**.

### La chiusura

> **Emendamento in loco ad AD-5 e AD-10 (v2.1).**
> `publish()` non certifica un `CircuitIR`: certifica un **`CertifiedRendering`**, cioè la coppia
> `(CircuitIR, artefatto già marcato)`. **La Marcatura di provenienza è applicata prima del
> round-trip**, non dopo: si certifica il byte-stream che esce, non un suo antenato.
> `export(published, format)` **non ri-serializza il disegno**: lo trascrive. Un exporter che
> rigenera l'SVG è non conforme.
> Per ogni formato che lascia il prodotto e che **non** può essere riparsato — PDF, CircuiTikZ — vale
> una sola via: l'artefatto è derivato dal `CertifiedRendering` per una trasformazione dichiarata
> **preservante il grafo**, con un test permanente (famiglie obbligatorie, AD-15) che ricostruisce
> il `CircuitIR` dal sorgente CircuiTikZ e lo confronta esattamente. **Un formato per cui quel test
> non esiste non porta il Badge Verificata**: porta la Soluzione, senza marchio di certificazione
> del disegno. È un rifiuto parziale, non un declassamento silenzioso.
> RRC (SM-16) si misura sugli **artefatti consegnati**, non sui rendering interni.

---

## C4 — Nessuno possiede il `LayoutIR`, e due unità scrivono `CircuitIR` dopo il passo *k* 🔴

### Le due unità

**U1 — `pipeline/ingest`.** Si costruisce su AD-8: «`IR` scritto solo da `ingest`», con
«Enforcement a livello di permessi DB, non di convenzione». U1 chiede e ottiene il permesso di
scrittura esclusivo sulla tabella `IR_VERSION` dell'ERD.

**U2 — `domain/proof`.** Si costruisce su AD-29: «nodi = stati circuitali, archi = `Transform`»,
con «Diramazione e ricongiungimento … supportati dallo schema e dalla persistenza fin da subito», e
su FR-40: «Ogni nodo del `ProofGraph` è **uno stato visuale certificato**; un nodo senza disegno è
un errore di schema». U2 deve quindi persistere, per ogni nodo, uno stato circuitale **e** il suo
stato visuale.

### Perché entrambe sono conformi

AD-8 elenca quattro proprietà: `IR` ← `ingest`, `Solution`/`Published` ← `solve`, `CreditLedger` ←
`billing`, `Variant` ← `studio`. **L'elenco non è stato toccato dalla v2.** Non nomina `LayoutIR`,
non nomina `ProofGraph`, non nomina `TransformOverlay`, `InteractionState`, `SourceAsset`, `Claim`,
`ProofSession`. L'ERD di §*Entità di dominio* non li contiene: è ancora quello della v1, con
`CIRCUIT ||--|{ IR_VERSION` e nessun `LAYOUT`. La convenzione sugli identificatori conferma
l'omissione: «ULID con prefisso per tipo (`ir_`, `sol_`, `var_`, `evt_`)» — **quattro prefissi per
sette tipi persistenti nuovi**, quindi due unità che ne inventano uno divergeranno anche sul nome
(`lay_` contro `lyt_`, `pg_` contro `proof_`).

AD-21 non risolve: proibisce che una rappresentazione **contenga** o **scriva dentro** un'altra, non
dice chi possiede ciascuna. U1 e U2 possono quindi scrivere entrambe, ciascuna nel proprio store,
senza violare una riga.

### La forma divergente

Sul `CircuitIR` del passo *k*, l'alternativa è binaria e lo spine non la decide:

- **U2 lo referenzia** (per identificatore, come AD-21 preferisce). Ma allora **qualcuno deve
  scriverlo** in `IR_VERSION`, e AD-8 dice che quel qualcuno è `ingest`, che non gira al passo *k*.
  → per rispettare AD-8, U2 deve chiamare `ingest` a ogni trasformazione, il che è assurdo, oppure
  AD-8 è violata.
- **U2 lo incorpora** nel nodo. Allora lo stesso stato circuitale esiste in due store con due
  identità, la persistenza append-only sugli IR (convenzione *Mutazione di stato*) non lo vede, e
  il confronto fra `Cₖ` ricostruito da `IR_VERSION` e `Cₖ` letto dal nodo può divergere senza che
  nessuna guardia se ne accorga.

Sul `LayoutIR` la divergenza è ancora più diretta, perché **due unità hanno un mandato scritto per
scriverlo**: `render/layout` è la sola applicatrice del patch (AD-2 em., AD-22) e produce il layout
del passo; `domain/proof` deve persistere lo «stato visuale certificato» del nodo (FR-40). Entrambe
scrivono, in buona fede, il layout di `Cₖ₊₁`. E il braccio 0 (AD-26) ne scrive un **terzo**: è «l'unico
che rigenera il layout», quindi per lo stesso `Cₖ₊₁` esistono due `LayoutIR` legittimi e nessuna
regola dice quale sia *il* layout del nodo, quale sia quello certificato dal round-trip, e quale sia
quello su cui si misura VCER.

### Il punto di rottura

Il fallimento canonico che AD-8 esiste per prevenire — «due scrittori dello stesso record che
divergono su invarianti» — si riapre esattamente sull'entità su cui A-0 è misurata, e **l'enforcement
prescritto è inapplicabile**: non si possono configurare permessi DB esclusivi su una tabella di cui
nessun documento nomina il proprietario. Il test di architettura previsto da AD-21 («fallisce sulla
dipendenza inversa») non vede nulla: nessuna delle due unità scrive *dentro* l'altra
rappresentazione; scrivono due copie della propria.

### La chiusura

> **Emendamento in loco ad AD-8 (v2.1) — la tabella di proprietà si estende a tutte le entità v2.**
>
> | Entità | Scrittore unico | Prefisso ULID |
> |---|---|---|
> | `CircuitIR` **radice** (stato iniziale) | `pipeline/ingest` | `ir_` |
> | `CircuitIR` **derivato** (passo *k*>0) | `domain/proof`, come nodo del grafo | `ir_` |
> | `LayoutIR` | `render/layout` | `lay_` |
> | `ProofGraph` (nodi, archi) | `domain/proof` | `pg_` |
> | `TransformOverlay` | `render/overlay` — **effimero, mai persistito** | — |
> | `InteractionState` | client — **mai persistito lato server** | — |
> | `SourceAsset` | `corpus/` | `src_` |
> | `Claim` | `domain/truthfulness` | `clm_` |
> | `Published` | `solve` (invariato) | `sol_` |
> | `ProofSession` | **nessuno**: è una proiezione, non un record | — |
>
> Un nodo del `ProofGraph` **referenzia** `CircuitIR` e `LayoutIR` per identificatore e non li
> incorpora (AD-21). La scrittura del `CircuitIR` derivato avviene **solo** attraverso `domain/proof`
> alla creazione del nodo: `ingest` possiede la radice, il grafo possiede il resto.
> **Per lo stesso nodo esiste un solo `LayoutIR` canonico**, quello del braccio A; i layout degli
> altri bracci sono `LayoutIR` **alternativi etichettati con `arm`**, non scrivibili sul nodo e non
> ammissibili come ingresso di `publish()`. Il round-trip certifica il canonico; VCER si misura sul
> canonico; il braccio 0 non ha nodo proprio.
>
> **Aggiornare l'ERD e l'Albero sorgente**, che sono rimasti alla v1: senza `LAYOUT`, `PROOF_GRAPH`,
> `CLAIM`, `SOURCE_ASSET` nell'ERD e senza `render/layout`, `domain/proof`, `domain/truthfulness`,
> `perception/`, `corpus/`, `experiment/` nell'albero, ogni unità colloca da sé i propri file e la
> mappa `Capability → Architecture` (che cita solo AD-1…AD-15) non arbitra.

---

## C5 — Il tipo che Gate A deve costruire è vietato da AD-11 🟠

### Le due unità

**U1 — `experiment/` · protocollo di Gate A.** Deve produrre SM-21, che lo spine promuove a
ingresso del verdetto e il PRD chiama «il secondo braccio del verdetto, accanto a VCER». SM-21 è
«cinque misure oggettive» per partecipante — tempi ed **errori** — sul confronto cieco a quattro
bracci, con «assegnazione … controbilanciata **fra partecipanti**, registrata per sessione»
(FR-47, e la convenzione *Bracci dell'esperimento*: «Il braccio è registrato per sessione insieme
all'ordine di presentazione»). Per controbilanciare e per misurare, U1 costruisce
`ParticipantReading { participant_id, arm, errors_unchanged, errors_identity, time_to_delta, … }`.

**U2 — `api/` + il test di contratto di AD-11.** Si costruisce sulla riga: «**non esiste alcun tipo
che associ una misura di rendimento a un identificatore di persona**. … Un test di contratto verifica
che nessuna risposta API contenga un campo di punteggio associato a un utente.» U2 implementa quel
test, e nella forma più difendibile: un controllo di architettura che cerca **tipi**, non solo
risposte, perché la regola dice «non esiste alcun tipo».

### Perché entrambe sono conformi

Perché AD-11 è ambigua fra il proprio *Binds* e la propria *Rule*, e le due letture sono entrambe
letterali:

- **Lettura per `Binds`** — «modalità Studio, telemetria, API, Studio B2B, §6 Non-Goals»: `experiment/`
  non compare, quindi la regola non lo tocca. U1 costruisce il tipo.
- **Lettura per `Rule`** — «non esiste **alcun** tipo»: è universale e non ammette eccipienti. U2
  fa fallire la build su `ParticipantReading`.

L'ambiguità non è un dettaglio redazionale: AD-11 è l'invariante che tiene il prodotto fuori
dall'Allegato III dell'AI Act, e il PRD lo chiama «un confine permanente, non un rinvio». Un
invariante di quel peso che ammette due letture è, di per sé, il difetto.

### Il punto di rottura

`errors_unchanged` — la misura 2, che il PRD indica come «quella che parla direttamente ad A-0» — è
un conteggio di errori commessi da una persona identificata almeno pseudonimamente, necessario per
il controbilanciamento. È esattamente la forma `(identificatore di persona, misura di rendimento)`.
La build si spacca fra il deliverable dell'MVP e il confine permanente, **e si spacca a Gate A**,
cioè adesso.

Il rischio secondario è peggiore del primo: la risoluzione naturale, se nessuno chiude il buco, è
esentare `experiment/` a mano. Un'esenzione manuale su AD-11 è la crepa da cui il confine si
degrada, e il PRD dice che la deriva verso l'Allegato III «avviene **per accumulo di richieste
ragionevoli**, non per una decisione esplicita». Questa sarebbe la prima.

### La chiusura

> **Emendamento in loco ad AD-11 (v2.1).** La regola si mantiene assoluta sul prodotto e si dichiara
> esplicita sull'esperimento:
>
> «Nessun tipo del **prodotto** associa una misura di rendimento a un identificatore di persona.
> Il protocollo di Gate A misura **letture, non persone**: l'unità è `Reading { reading_id, arm,
> misure }`, dove `reading_id` è effimero, generato dentro la sessione sperimentale e **non
> collegabile per schema** a `subject_id`, `user_id` o a qualunque anagrafica — nessuna tabella
> porta entrambe le colonne, nessuna vista le congiunge. Il controbilanciamento usa `reading_id`.
> I dati sperimentali non transitano da alcuna superficie API di prodotto, non sono persistiti oltre
> la chiusura dell'esperimento, e l'esito pubblicato è aggregato. Un `Reading` che risulti
> ricollegabile a una persona è un difetto di conformità, non un dato imperfetto.»
>
> Il test di contratto di AD-11 si estende a un test di schema: **l'assenza del join** è la prova,
> non l'intenzione di chi lo scrive.

---

## C6 — L'evidenza evapora a 72 ore mentre il `Claim` la esige per sempre 🟠

### Le due unità

**U1 — `adapters/blob`.** Applica AD-9 alla lettera: «le immagini sorgente stanno in un bucket con
lifecycle policy a **72 ore** lato provider. **L'applicazione non è autorizzata a scriverle altrove
né a copiarle.** Un test di conformità fallisce se trova un oggetto oltre TTL.»

**U2 — `domain/truthfulness`.** Applica AD-30: «ogni affermazione pubblicabile è un `Claim`
tipizzato **con la propria evidenza** … Un `Claim` senza evidenza **non è pubblicabile** — stesso
trattamento del Rifiuto, non un avviso», e AD-25, che vuole `evidence.license_snapshot_hash` e
`evidence_ref` come prove raccolte «all'acquisizione o non esistono più». FR-42 aggiunge: «Ogni
`Claim` pubblicato ha `evidence_ids` non vuoto e un `verifier_id` risolvibile a una versione».

### Perché entrambe sono conformi

AD-9 governa le immagini sorgente e vieta ogni copia. AD-30 governa i `Claim` e ne esige l'evidenza.
Nessuna riga dice **cosa sia** un `evidence_id` quando l'evidenza è un'immagine, né cosa accada al
`Claim` quando l'oggetto puntato viene cancellato dalla policy di storage. Le due unità si
costruiscono e non si accorgono l'una dell'altra: U1 cancella, U2 punta.

### Il punto di rottura

Al quarto giorno, un `Claim` pubblicato su una derivazione nata da percezione ha `evidence_ids` non
vuoto e **non risolvibile**. Le conseguenze si escludono a vicenda:

- se il gate ricontrolla la risolvibilità, la Soluzione diventa **retroattivamente non
  pubblicabile** — un artefatto già consegnato che perde il Badge da solo;
- se non la ricontrolla, `evidence_ids` è un campo che sembra una prova e non lo è, e K-4 («la prova
  ispezionabile») diventa una promessa che scade in tre giorni;
- **non esiste la terza via**, perché copiare l'immagine altrove è esplicitamente vietato da AD-9.

Il conflitto è **non risolvibile a valle**: nessuna unità può obbedire a entrambi senza una
modifica dello spine. Non morde nell'MVP, dove la foto è a Gate C, ed è precisamente questo che lo
rende pericoloso: quando morderà, il formato dei `Claim` sarà già persistito.

### La chiusura

> **AD-33 — L'evidenza sopravvive al proprio soggetto: si conservano derivati, mai originali.**
>
> - **Binds:** `domain/truthfulness`, `corpus/`, `adapters/blob`, AD-9, AD-25, AD-30, FR-42
> - **Prevents:** che un `Claim` diventi non verificabile per effetto di una policy di ritenzione, e
>   che qualcuno «risolva» copiando un'immagine che AD-9 vieta di copiare.
> - **Rule:** un `evidence_id` non punta **mai** a un oggetto soggetto a TTL. L'evidenza persistita è
>   un **derivato non reversibile e non identificante**: `artifact_hash`, `license_snapshot_hash`,
>   `perceptual_digest`, riferimento al `SourceAsset`, esito e versione del verificatore. L'immagine
>   sorgente resta nel bucket a 72 ore e non è evidenza: è ingresso.
>   Un `Claim` la cui evidenza include un riferimento a un oggetto con TTL **non è pubblicabile**, e
>   il controllo sta dentro `publish()` (AD-5), non a valle. Un test di conformità verifica entrambe
>   le direzioni: nessun oggetto oltre TTL nel bucket, **e** nessun `evidence_id` che punti al
>   bucket.

---

## C7 — Il round-trip e la validazione del patch falliscono con cause che l'enumerazione non ha 🟠

### Le due unità

**U1 — `domain/verify/roundtrip`.** AD-5 emendato la mette dentro `publish()`; FR-41 impone che un
disegno che non supera il round-trip «produce **Rifiuto tipizzato**, non un avviso». U1 deve quindi
costruire un `Refusal`.

**U2 — `render/validate_patch`.** AD-22: un `LayoutPatch` con `preserve` più piccolo di `Pₖ` «viene
**rifiutato in validazione**»; e «un `boundary` vuoto è rifiutato». Anche U2 deve costruire un
`Refusal`.

### Perché entrambe sono conformi

AD-19 chiude l'enumerazione: «`Refusal.cause` appartiene a un'enumerazione chiusa (`topology`,
`units`, `unsolvable`, `path_disagreement`, `residual`, `sanity`) … **Aggiungere una causa è una
modifica dello spine, non di un modulo.**» Le due unità **non possono** aggiungerne una: devono
riusarne una esistente. U1 sceglie `topology` — è un disaccordo topologico. U2 sceglie `sanity` — è
un patch insensato. Oppure il contrario, con pari legittimità. Nessuna delle due sta violando
qualcosa; entrambe stanno facendo la sola cosa che AD-19 lascia loro fare.

### Il punto di rottura

È il fallimento che AD-19 esiste per prevenire, testualmente: «costringendo la UI a gestire due
schemi e il messaggio all'utente a divergere fra i due casi». Con l'aggravante che `topology` ha già
un significato assegnato — il fallimento della Validazione elettrica — e riusarlo per il round-trip
rende **SM-19** («Copertura della causa di Rifiuto … localizzata e azionabile») e la diagnostica
indistinguibili fra un circuito mal ricostruito e un disegno mal serializzato: due difetti in due
unità diverse, con la stessa etichetta.

### La chiusura

> **Emendamento in loco ad AD-19 (v2.1).** L'enumerazione si estende ai modi di fallimento
> introdotti dalla v2, ciascuno con il proprio `subject`:
> `round_trip` (subject: entità o terminale che non ricostruisce) ·
> `preserve_violation` (subject: entità preservata mancante da `preserve`) ·
> `boundary_empty` (subject: la `Transform`) ·
> `layer_order` (subject: la primitiva fuori scala, AD-23) ·
> `license_unknown` (subject: il `SourceAsset`, AD-25) ·
> `claim_unsupported` (subject: il `Claim` privo di evidenza, AD-30).
> Resta il vincolo: aggiungerne un'altra è una modifica dello spine. **Un AD nuovo che introduce un
> modo di fallimento e non estende AD-19 è incompleto**, e questa frase va aggiunta ad AD-19 come
> regola di redazione.

---

## C8 — `InteractionState` è una delle quattro rappresentazioni e non ha domicilio 🟡

### Le due unità

**U1 — `ui/proof_replay` (superficie assistente).** Costruisce l'ispezione di FR-49 — Prima↔Dopo,
selezione dell'elemento, navigazione nel `ProofGraph` — dentro il pannello MCP. Tiene
l'`InteractionState` sul client, come AD-21 suggerisce dandogli «un ciclo di vita proprio».

**U2 — `api/assistant`.** Applica AD-16: «**Il pannello non conserva stato locale**», e AD-6:
«nessuno stato in memoria fra richieste. Lo stato di una conversazione multi-giro vive in
`resume_ref` … **TTL 15 minuti, monouso**». U2 conclude che ogni stato di interazione deve tornare
al server.

### Perché entrambe sono conformi

AD-21 crea `InteractionState` come quarta rappresentazione con ciclo di vita proprio, e non dice
dove viva. AD-16 vieta lo stato locale del pannello. AD-6 offre l'unico contenitore di stato
previsto, `resume_ref`, che è **monouso e a TTL 15 minuti**: un token bruciato per ogni `hover`.
Le tre righe insieme non lasciano a `InteractionState` nessun posto abitabile.

### Il punto di rottura

FR-48 impone che «almeno due adapter» presentino la `ProofSession`, e che essa «funziona **senza**
MCP Apps», col degrado a superficie non interattiva come «percorso previsto, non un guasto». U1 e U2
si dividono su chi tiene la selezione corrente: se la tiene il client, AD-16 è violata alla lettera;
se la tiene il server, ogni interazione consuma un `resume_ref` monouso o richiede un secondo
meccanismo di stato che AD-6 non prevede. Due implementazioni conformi della stessa `ProofSession`,
con due modelli di stato incompatibili, sulla superficie che il PRD chiama «il cardine» (SM-11).

### La chiusura

> **Emendamento in loco ad AD-16 e AD-21 (v2.1).** «Il pannello non conserva stato locale» si
> restringe al suo scopo originale: **non conserva stato di dominio**. `InteractionState` è, per
> definizione, **stato di vista**: vive nel client, non è mai persistito lato server, non compare in
> alcuna risposta di tool, non entra in `resume_ref`, e la sua perdita non degrada la
> `ProofSession`. Un `InteractionState` ricostruibile dal server sarebbe stato di dominio travestito.
> `resume_ref` resta riservato alla continuazione di dominio (AD-6): un'interazione di vista non lo
> consuma mai.

---

## Cosa NON è un buco — falsi positivi verificati e scartati

Un avversario che non elenca ciò che ha provato e non è passato non è verificabile. Queste sono
sembrate coppie e non lo sono:

- **`studio` che scrive `Published`.** Chiusa esplicitamente in AD-8 («*Caso di confine chiuso
  esplicitamente*»): `studio` **chiama** `publish()` e scrive solo `Variant`, referenziando per id.
  Non c'è spazio di divergenza.
- **La chiave di idempotenza per l'utente anonimo.** Chiusa da AD-20 e riallineata in AD-6 e AD-7:
  tutti e tre dicono `subject_id`, nessuno dice `user_id`. Era il buco della v1 ed è stato chiuso
  bene.
- **Il braccio 0 che riceve `Layout(Cₖ)`.** Chiusa nel tipo, non nella buona fede: AD-26 dice
  «**non riceve `Layout(Cₖ)` nella propria firma**». Il vincolo è verificabile staticamente.
- **La promozione di `PerceptionCandidate` a `CircuitIR`.** Chiusa da AD-24: «passaggio esplicito
  con esito di fallimento proprio, mai un cast», e il diagramma la marca come «l'unico ingresso».
- **`preserve` proposto dal renderer.** Chiusa due volte, da AD-22 («non espone **alcuna funzione**»)
  e da FR-47. È il difetto di autocertificazione già trovato al gate precedente, e la chiusura tiene.
- **Ardesia che certifica.** Chiusa da AD-28 con una freccia a senso unico nel diagramma e la
  proprietà del `TruthfulnessGate` in Kirchhoff. Nessuna ambiguità.

E due **frizioni minori** che non arrivano al rango di coppia ma vanno annotate:

- **`kernel/` non esiste nell'albero sorgente.** AD-27 vincola «nessun modulo del kernel importa
  codice specifico di una superficie» e prescrive un test di architettura. L'albero sorgente conosce
  `domain/`, `ports/`, `adapters/`, `pipeline/`, `api/`, `render/`, `eval/` — **nessun `kernel/`**, e
  nessun `adapters/pwa|mcp|ardesia`. Il test di AD-27 passerebbe **a vuoto**, che è peggio che
  fallire. Va nominata la corrispondenza (`kernel/ ≡ domain/ + pipeline/ + render/`) o rinominato
  l'albero.
- **Il bootstrap chiede modelli a un MVP che non ne usa.** AD-3 esige «almeno due adapter
  registrati» e AD-12 impone `K ≥ 3` con «una configurazione che lo viola non si avvia». L'MVP di
  Gate A è a ingresso strutturato e non chiama alcun modello: o non si avvia, o il controllo viene
  ristretto a mano — e la convenzione *Configurazione* vieta il degrado silenzioso. Va detto che
  AD-3 e AD-12 vincolano `perception/`, e che la loro validazione all'avvio è **condizionata alla
  presenza del binario di percezione**.
- **«Provenienza» è un omonimo triplo.** `PROVENANCE` come campo del passo (FR-39: da quali elementi
  deriva), `source_provenance` del `PerceptionCandidate` (AD-24, licenza e origine), e *Marcatura di
  provenienza* dell'export (AD-10, dichiarazione IA). La convenzione sui nomi vieta i **sinonimi** e
  tace sugli **omonimi**: tre unità useranno la stessa parola per tre cose. Aggiungere alla tabella
  *Consistency Conventions*: «un termine del Glossario nomina **una** cosa; un omonimo è un difetto
  di modellazione».

## Chiusure, in ordine di costo

| Ordine | Chiusura | Costo se fatta adesso | Costo se fatta dopo |
|---|---|---|---|
| 1 | **AD-19** esteso (C7) | una riga di enumerazione | due schemi di errore in UI, diagnostica ambigua |
| 2 | **AD-11** disambiguata (C5) | un emendamento in loco | build spaccata a Gate A, o un'esenzione che apre il confine |
| 3 | **AD-8** esteso a sette entità + ERD e albero (C4) | una tabella | due scrittori del `LayoutIR`, permessi DB non configurabili |
| 4 | **AD-31**, invariante unico (C1) | una funzione e una costante | kill criterion non falsificabile, e non te ne accorgi |
| 5 | **AD-1/AD-32**, veicolo del patch, ritiro di `Drawing` (C2) | una firma | riplumbing di ogni stadio dopo il primo commit |
| 6 | **AD-5/AD-10**, `CertifiedRendering` (C3) | ordine di due operazioni | Badge su artefatti mai certificati, già distribuiti |
| 7 | **AD-33**, evidenza derivata (C6) | uno schema di `evidence` | formato dei `Claim` già persistito quando il conflitto morde |
| 8 | **AD-16/AD-21**, domicilio di `InteractionState` (C8) | una riga di scopo | due modelli di stato sulla superficie che il PRD chiama cardine |

**La regola di redazione che manca, e che eviterebbe metà di queste.** La v2 ha aggiunto dieci AD e
ne ha emendati quattro **senza rileggere i sedici rimasti**: AD-18 cita un AD-2 che non esiste più,
AD-8 elenca quattro entità su undici, AD-19 enumera sei cause su dodici, AD-11 non sa dell'esperimento
che l'MVP deve eseguire. Va aggiunta in testa alla sezione *Invariants & Rules*:

> **Un emendamento a un AD obbliga a rileggere ogni AD che lo cita, e ogni AD che governa un'entità
> che l'emendamento introduce o divide. L'`Albero sorgente`, l'ERD e la mappa
> `Capability → Architecture` fanno parte dello spine: un AD che nomina un modulo o un tipo assente
> da quei tre non è ancora costruibile.**
