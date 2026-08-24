---
name: 'Review — invarianti di dominio'
type: architecture-review
scope: 'ARCHITECTURE-SPINE.md v2 · PRD §7.0.1, FR-37…FR-43, FR-47, FR-53'
question: 'Gli invarianti sono resi impossibili da violare, o solo scritti?'
reviewer: 'revisore indipendente — solo dai file'
date: '2026-08-15'
verdict: 'PARZIALE — il perimetro del kernel è di tipo, il cuore di A-0 è prosa'
sources:
  - ../ARCHITECTURE-SPINE.md
  - ../../../prds/prd-Kirchhoff-2026-08-13/prd.md
---

# Gli invarianti sono impossibili da violare, o solo scritti?

## Verdetto

**Parziale, e la parte debole è esattamente quella che il prodotto vende.**

Gli invarianti *ereditati dalla v1* — gate unico, dipendenza a senso unico, idempotenza, un solo
scrittore, un solo orologio — sono per lo più impossibili da violare: stanno in una firma
(`export(published, format)`), in un vincolo di schema (unicità della chiave di idempotenza), in un
permesso DB o in un errore di compilazione. Lì lo spine fa quello che promette a riga 55: *«un
adapter importato dal dominio è un errore di compilazione, non un rilievo di code review»*.

Gli invarianti *aggiunti dalla v2 attorno ad A-0* — quelli su cui Gate A decide se il prodotto
continua — sono in maggioranza **enunciati al passivo, senza soggetto e senza stadio**. AD-22
condensa in tre righe cinque obblighi distinti («è rifiutato», «viene rifiutato in validazione»,
«non espone alcuna funzione») e non nomina chi rifiuta, in quale stadio, con quale tipo di esito.
Le due formule che il PRD dichiara normative — `id_{k+1}(x) = id_k(x)` e `p_{k+1}(x) ≈ p_k(x)` —
**non compaiono nello spine: zero occorrenze**, in nessuna forma.

Il rapporto è misurabile: dei sette invarianti che reggono A-0, **uno** è applicato dal tipo, **due**
da un controllo runtime (uno dei quali aggirabile), **quattro** sono solo prosa.

---

## Classificazione

| # | Invariante | Dove sta | Categoria | Nota |
|---|---|---|---|---|
| 1 | `id_{k+1}(x) = id_k(x)`, senza eccezioni | PRD FR-38, §7.0.1 — **assente dallo spine** | 🔴 **solo prosa** | Nessun controllo, nessuno stadio, nessuna metrica. Il round-trip non lo vede (R1) |
| 2 | `p_{k+1}(x) ≈ p_k(x)`, `θ` invariato salvo necessità | PRD FR-38, §7.0.1 — **assente dallo spine** | 🟠 **misurato offline, mai applicato** | `eval/` via VCER (AD-15), soglia owner-locked. Tolleranza di `≈` non definita da nessuna parte (R4) |
| 3 | `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` | Spine AD-22 · PRD FR-47 | 🟠 **runtime, aggirabile** | Calcolato *dopo* `node_mapping`, che è uscita del misurato (R3) |
| 4 | Il renderer non propone un `preserve` proprio | Spine AD-22 | 🔴 **solo prosa** | «non espone alcuna funzione» è l'assenza di un'API: si verifica leggendo, non compilando. Confronta AD-26, che per il braccio 0 mette il vincolo **nella firma** |
| 5 | `boundary` vuoto rifiutato | Spine AD-22 · PRD FR-53 | 🔴 **solo prosa** | Passivo senza agente, e **nessuna `Refusal.cause` esiste per esprimerlo** (R2) |
| 6 | `Transform ⇒ PreserveSet + Delta + Boundary + LayoutPatch + Equation + Certificate` | Spine AD-2 (emendata), AD-22 | 🟡 **tipo per la presenza, prosa per la non-vuotezza** | `TransformResult` è un prodotto a sei campi: manca un campo → errore di costruzione. Campo **presente e vuoto** → passa, salvo `Claim` (R5) |
| 7 | Round-trip dentro `publish()` | Spine AD-5 (emendata) | 🟡 **tipo sul percorso terminale, buco sugli intermedi** | `export(published, …)` e «solo `Published` è serializzabile» chiudono l'uscita finale. Gli stati intermedi del `ProofGraph` non passano da lì (R6) |
| 8 | R-Visual-1, ordine dei layer `0…8` | Spine AD-23 · PRD FR-53 | 🟡 **controllo di test, non runtime** | «Il test è permanente» ≠ gate. Il round-trip non vede l'occlusione (PRD SM-C8 lo dice esplicitamente) |

Riferimento per le categorie: *applicato dal tipo* = un programma che lo viola non compila o non
costruisce l'oggetto; *controllo runtime* = esiste un punto di codice nominato che rifiuta; *solo
prosa* = la regola vive nella disciplina di chi scrive. **La terza categoria è il rilievo.**

---

## Rilievi

### R1 — `id_{k+1}(x) = id_k(x)` non esiste nello spine, e il round-trip non lo cattura

Il PRD lo qualifica come l'unico invariante **senza tolleranza**: *«L'identità non ha tolleranza: un
elemento conservato che cambia identificatore è un difetto, sempre»* (FR-38). §7.0.1 lo ripete come
`id_{k+1}(x) = id_k(x)` — **sempre, senza eccezioni**.

Nello spine: **zero occorrenze**. Non in AD-22, che parla solo di cardinalità del `preserve`; non
in AD-5, i cui controlli sono cinque più il round-trip; non fra le Consistency Conventions, che
sugli identificatori dicono solo «ULID con prefisso per tipo».

**Perché il round-trip non lo copre.** Il round-trip di AD-5/FR-41 confronta l'SVG riparsato con il
`CircuitIR` **atteso dello stesso passo** — è un controllo *intra-passo*. `id_{k+1}(x) = id_k(x)` è
un invariante *inter-passo* sull'identità delle entità del `LayoutIR` fra `k` e `k+1`. Un rename
applicato **coerentemente** da `Transform` e renderer produce un `CircuitIR(Cₖ₊₁)` che contiene il
nuovo id, un SVG che porta lo stesso nuovo id, e un round-trip che passa senza rilievi. Il difetto
che il PRD dichiara «sempre un difetto» è invisibile all'unico controllo visuale del gate.

Aggravante: `Pₖ` è calcolato **dopo `node_mapping`** (AD-22). La mappatura è precisamente ciò che
legittima il rename — sotto mapping l'entità rinominata resta dentro `Pₖ`, quindi nemmeno il
controllo di cardinalità del `preserve` se ne accorge.

> **Rimedio minimo.** Un sesto controllo dentro `publish()` — o una precondizione di
> `apply_patch(LayoutIR, LayoutPatch)` — che verifichi `∀x ∈ Pₖ : id_{k+1}(x) = id_k(x)` prima di
> qualunque misura geometrica. È l'unico invariante di A-0 che si può rendere **di tipo** senza
> discussione, perché non ha tolleranza da negoziare.

### R2 — `boundary` vuoto e `preserve ⊊ Pₖ`: rifiutati da nessuno, e nessuna causa di rifiuto esiste

AD-22 chiude con due obblighi al passivo: *«Un `LayoutPatch` con `preserve` più piccolo di `Pₖ` è
non conforme e viene rifiutato in validazione»* e *«un `boundary` vuoto è rifiutato»*. FR-53 usa la
stessa forma. In nessuno dei due documenti c'è un soggetto.

Tre fatti che rendono il buco strutturale, non redazionale:

1. **Non esiste lo stadio.** L'albero sorgente dello spine descrive `domain/validate/` come
   «Validazione elettrica (puro codice)», e il diagramma degli stadi mostra una sola `val
   [Validazione elettrica]` fra consenso e anteprima — **prima** che esista una trasformazione da
   validare. Non c'è uno stadio di validazione del `Transform`/`LayoutPatch` nel percorso.
2. **Non esiste il tipo dell'esito.** AD-19 dichiara `Refusal.cause` **enumerazione chiusa**:
   `topology`, `units`, `unsolvable`, `path_disagreement`, `residual`, `sanity` — e aggiunge che
   *«Aggiungere una causa è una modifica dello spine, non di un modulo»*. Nessuna delle sei nomina
   un boundary vuoto, un `preserve` non conforme o un ordine di layer violato. **Lo spine impone due
   rifiuti e contemporaneamente vieta il tipo che li esprime.** È una contraddizione interna
   verificabile a lettura, non un'opinione di revisione.
3. **Non esiste la riga di mappa.** La tabella *Capability → Architecture Map* si ferma a
   **FR-35**: FR-36…FR-53 — cioè tutto il Visual Proof Kernel, l'unico oggetto dell'MVP secondo
   §7.1 — non hanno una riga che dica *Lives in* e *Governed by*. La domanda «chi, dove» non è
   senza risposta per distrazione: la tabella che risponderebbe non è stata estesa alla v3.

### R3 — Il punto in cui il `preserve` si può ancora autocertificare è `node_mapping`

AD-22 dichiara di chiudere l'autocertificazione: *«Con `preserve` dichiarabile, `preserve = {}`
prende VCER perfetto conservando zero»*. La chiusura è reale per quel vettore. **Non lo è per il
livello sotto.**

`Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` **dopo `node_mapping`**. `Entities(Cₖ)` ed `Entities(Cₖ₊₁)`
sono fatti del `CircuitIR`, indipendenti. `node_mapping` **è un campo che il `Transform` espone**
(FR-38 lo elenca fra `preserve_entities`, `remove_entities`, `create_entities`, `preserve_nodes`,
`node_mapping`, `changed_edges`, `boundary`). Quindi l'intersezione è presa nel sistema di
coordinate scelto dal soggetto misurato: un `Transform` che dichiara un'entità sopravvissuta come
*creata* invece che *mappata* rimpicciolisce `Pₖ` **stesso**, il `preserve` risulta conforme perché
il riferimento si è ristretto insieme a lui, e VCER torna perfetto. È lo stesso exploit che AD-22
chiude, spostato di un livello.

Due dettagli che tolgono le difese residue:

- **Lo spine non riporta la clausola di totalità.** FR-38 impone *«`node_mapping` è totale sui nodi
  sopravvissuti»*; AD-22 non la ripete. E anche riportandola non basterebbe: la totalità dice che
  ogni nodo del risultato ha **un'origine dichiarata**, e «creato» è un'origine. Serve
  **massimalità** — nessuna entità sopravvissuta può essere dichiarata creata — che nessuno dei due
  documenti impone. La clausola inoltre parla di *nodi*, mentre `Pₖ` è definito su *entità*.
- **AD-22 enuncia un'uguaglianza e applica una sola disuguaglianza.** Rifiuta il `preserve` «più
  piccolo di `Pₖ`»; il caso `preserve ⊋ Pₖ` non è nominato. FR-38 copre solo il sottocaso
  dell'elemento assente da `p_k`.

> **Rimedio minimo.** Rendere `node_mapping` **verificabile contro i due `CircuitIR`** invece che
> creduto: un controllo che ricalcoli l'identità delle entità sopravvissute dai due grafi
> canonicalizzati e fallisca se il mapping dichiara «creata» un'entità che il confronto trova
> sopravvissuta. Finché `Pₖ` deriva da un campo del misurato, il kill criterion resta autocertificato
> a un livello di indirezione.

### R4 — `p_{k+1}(x) ≈ p_k(x)`: nessuno definisce `≈`, e la metrica misura un altro operatore

Alla domanda **chi misura lo scostamento**, lo spine risponde solo per via transitiva: AD-15 impone
all'harness di calcolare *ogni* metrica di §8 a ogni esecuzione, VCER inclusa — quindi il soggetto
è `eval/`. Alla domanda **dove viene penalizzato**, la risposta è: in una metrica offline, con
soglia owner-locked e non fissata. **Non esiste alcuna conseguenza runtime**: nessun percorso di
codice rifiuta un `LayoutPatch` che sposta un'entità preservata. Il PRD è esplicito che deve
esserci un prezzo — *«uno che sposta per evitare una collisione paga meno, ma paga»* — ma il prezzo
è contabile, non strutturale.

Sopra questo, tre indeterminazioni che rendono l'invariante **non decidibile** com'è scritto:

| Termine | Chi lo definisce |
|---|---|
| la tolleranza di `≈` | nessun documento. Nessun ε, nessuna normalizzazione, nessuna unità |
| «necessità geometriche **dimostrabili**» | nessun predicato di dimostrabilità, in nessun artefatto |
| «paga meno, ma paga» — costo graduato | nessuna funzione di costo. SM-14 è una **quota binaria** per patch |

E una discordanza letterale: **SM-14 è definita su `p_{k+1}(x) = p_k(x)`** — uguaglianza esatta —
mentre FR-38 e §7.0.1 hanno *corretto il 15 agosto* l'invariante in `≈`, motivando che l'uguaglianza
esatta *«è un invariante che il rendering reale viola sempre»*. La metrica del kill criterion misura
l'operatore che il PRD ha ritirato. Presa alla lettera, VCER vale ~100% su qualunque rendering
responsive e il gate uccide sempre; presa nello spirito, non è definita. Lo spine non arbitra, e
non nomina VCER se non in un `Binds:`.

Nota di merito: il PRD stesso segnala che la grandezza giusta è **SM-18** (*«VCER dice se
l'invariante è violato, SM-18 dice se `preserve` era ambizioso o vuoto»*). Lo spine non cita SM-18
in nessuna regola — solo in un `Binds:` di AD-26.

### R5 — Sei componenti del `Transform`: la presenza è di tipo, la non-vuotezza no

AD-2 emendata stabilisce che il secondo membro è un `TransformResult` che porta i sei componenti. Se
`TransformResult` è un prodotto a campi obbligatori — e con lo stack dichiarato, Pydantic, lo è alla
costruzione — **un campo mancante non passa**: è un errore di costruzione, non un rilievo. Questa
metà della domanda ha risposta buona.

L'altra metà no. Un campo **presente e vuoto** passa ovunque tranne uno:

| Campo | Cosa lo protegge dal vuoto |
|---|---|
| `PreserveSet` | AD-22 via `Pₖ` — ma vedi R3 |
| `Boundary` | «è rifiutato» — da nessuno (R2) |
| `Certificate` | ✅ AD-30: *«Un `Claim` senza evidenza non è pubblicabile»*, `TruthfulnessGate` nominato come soggetto |
| `Equation`, `Delta`, `LayoutPatch` | nulla |

Il contrasto è istruttivo perché è interno allo stesso PRD: i sei campi **del passo** (FR-39) hanno
un gate nominato — *«Un passo privo di uno dei sei campi non è pubblicabile: il gate lo rifiuta»* —
**e** una metrica dedicata, SM-15/SEC, definita su campi *«compilati e non vuoti»*. I sei componenti
**del `Transform`** non hanno né l'uno né l'altra. Due sestine simmetriche, protezione asimmetrica.

Osservazione minore ma di tipo: lo spine non dichiara da nessuna parte che i campi di
`TransformResult` sono obbligatori e non nullable. Con un `Optional` di troppo la sola difesa
strutturale di questo invariante svanisce senza che nessun documento risulti violato.

### R6 — Round-trip in `publish()`: chiuso in uscita, aperto sugli stati intermedi

**Quello che regge.** AD-5 non ha flag di bypass «nemmeno amministrativo o di test»; solo
`Published` è serializzabile verso l'esterno; AD-10 fa passare ogni artefatto da
`export(published, format)`, dove il tipo del parametro rende inesprimibile l'export di un non
pubblicato; AD-8 chiude il caso di confine di `studio`, che *chiama* `publish()` e non scrive mai un
`Published`. Sul percorso terminale la risposta alla domanda è: **no, non c'è un percorso che
aggiri il round-trip.**

**Quello che non regge.** `publish()` ha firma `publish(solution) → Published | Refusal` — **una
soluzione, un colpo, in fondo** — e il diagramma degli stadi conferma un solo `ver → pub` terminale.
Ma FR-40 impone che **ogni nodo del `ProofGraph`** sia uno stato visuale certificato (*«un nodo
senza disegno è un errore di schema»*), e AD-29 aggiunge che la soluzione finale **è l'ultimo nodo
del grafo**, non un oggetto a parte. Se il round-trip vive dentro `publish()` e `publish()` si
esegue una volta sulla soluzione, **i disegni intermedi — che sono il prodotto, non un accessorio —
non attraversano alcun gate.** Lo spine non dice mai che `publish()` gira per nodo, né esiste un
`certify_node()`.

Due vie per cui quei disegni raggiungono comunque l'utente senza essere `Published`:

- **`ProofSession`.** AD-27 e FR-48 la vogliono *«serializzabile e ricostruibile senza il codice di
  alcuna superficie»*, con almeno due adapter che la presentano (PWA e `ProofReplay` MCP). Contiene
  `LayoutIR` + `ProofGraph`. È in **tensione diretta** con AD-5: *«Nessun tipo `Solution` è
  serializzabile verso l'esterno: solo `Published` lo è»*. O `ProofSession` è un `Published` — e
  allora va detto, e `publish()` deve girare per nodo — o è una seconda uscita verso l'esterno che
  AD-5 non contempla.
- **I quattro bracci di Gate A.** AD-26 e FR-47 producono quattro rendering dello stesso passaggio,
  mostrati a studenti valutatori. Sono artefatti visibili, prodotti da `render/`, e nessuna regola li
  fa passare da `publish()` o da `export()`. Se il braccio 0 sbaglia un disegno, l'esperimento
  attribuisce alla discontinuità di layout un difetto di rendering — la stessa contaminazione che
  AD-24 e FR-52 chiudono con cura sul lato percezione, lasciata aperta sul lato disegno.

---

## Rilievo strutturale di contorno

**Gli `AD-21…AD-30` vincolano moduli che l'albero sorgente non dichiara.** I `Binds:` della v2
nominano `perception/`, `corpus/`, `kernel/`, `experiment/`, `domain/proof`, `domain/truthfulness`,
`render/layout`, `adapters/pwa|mcp|ardesia`. L'*Albero sorgente* dello spine è rimasto quello della
v1: `domain/{ir,validate,transform,solve,verify}`, `ports/`, `adapters/`, `pipeline/`, `api/`,
`render/`, `eval/`. Nessuno dei moduli nuovi compare.

Non è pedanteria: **tre AD ordinano un test di architettura** — AD-21 («fallisce sulla dipendenza
inversa» fra le quattro rappresentazioni), AD-24 («`domain/` non importa nulla da `perception/`»),
AD-27 («nessun modulo del kernel importa codice specifico di una superficie»). Un test di
dipendenza si scrive su confini di pacchetto dichiarati. Finché l'albero non nomina `kernel/`,
`perception/` e `corpus/`, i tre test non hanno un confine da controllare, e i tre AD scendono
dalla categoria «applicato dal tipo» — dove sono scritti per stare — alla categoria «prosa».

---

## Sintesi per il committente

- **Impossibile da violare oggi:** dipendenza a senso unico del dominio, unicità dell'export,
  idempotenza di ledger, singolo scrittore, orologio iniettato, `Claim` senza evidenza, braccio 0
  senza `Layout(Cₖ)` in firma. Sette invarianti che stanno in una firma o in uno schema.
- **Scritto e basta:** `id_{k+1}(x) = id_k(x)`, il divieto al renderer di proporre un `preserve`, il
  rifiuto del `boundary` vuoto, l'ordine dei layer a runtime. Quattro invarianti su cui poggia A-0.
- **Il singolo intervento con più resa:** estendere l'enumerazione di `AD-19` con le cause della v3
  (`preserve_nonconformance`, `empty_boundary`, `identity_drift`, `layer_order`) e nominare lo stadio
  che le emette. Senza un tipo che esprima il rifiuto, ogni «è rifiutato» della v2 resta una frase.
