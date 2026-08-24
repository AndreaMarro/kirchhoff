# Review dei confini architetturali — Spine v2 (Kirchhoff)

Documento sotto esame: `ARCHITECTURE-SPINE.md` v2 (641 righe, aggiornato 15 ago 2026), AD-1…AD-30,
convenzioni, *Structural Seed*, *Capability → Architecture Map*.
Letti come controllo incrociato: `prds/prd-Kirchhoff-2026-08-13/prd.md` v3 (FR-37…FR-53, §7.0.1
A-0, §4 glossario v3), `epics.md`, `implementation-readiness.md`,
`implementation-artifacts/spec-2-1-*.md`, e l'albero sorgente reale — `src/kirchhoff/`,
`scripts/check_boundaries.py`, `pyproject.toml`.

Revisore senza contesto pregresso. Il criterio applicato è uno solo: **un team competente e in
buona fede, che rispettasse ogni AD alla lettera, potrebbe comunque far collassare le quattro
separazioni promesse?**

---

## Verdetto in una riga

**Sì — e tre delle quattro separazioni collassano lungo percorsi che gli AD non solo permettono, ma
richiedono.** `CircuitIR`, `LayoutIR` e `InteractionState` viaggiano legittimamente dentro un unico
tipo serializzato (`ProofSession`) che AD-21 non vieta perché AD-21 vieta solo che i quattro si
contengano *a vicenda*; la validazione del `preserve set` non ha un modulo in cui stare senza
violare AD-1 o AD-22; l'insieme chiuso di `Refusal` è rimasto quello della v1 mentre la v2 ha
aggiunto almeno otto modi di rifiutare, riaprendo esattamente il buco per cui AD-19 fu scritto. La
quarta separazione — kernel/adapter, AD-27 — non collassa: **non è ancora stata dichiarata**, perché
l'albero sorgente non contiene un `kernel/`.

I tre "test di architettura" che dovrebbero reggere tutto questo sono **la stessa frase ripetuta
tre volte** e nessuno dei tre è scrivibile come sta. Non è un difetto di stile: lo stesso documento
sa scrivere istruzioni eseguibili — lo fa in AD-22, AD-23, AD-26 e AD-5. Le promesse coprono i
confini nuovi, le istruzioni i confini vecchi.

---

## R1 — `ProofSession` è il contenitore che AD-21 vieta, ed è AD-27 a richiederlo

AD-21 chiude la porta con precisione: «Nessuno dei quattro contiene un riferimento a un altro se non
per identificatore. **Nessuno scrive in un altro.**» La convenzione la ribadisce: «Un tipo che ne
contenesse un altro è un errore di modellazione, non un'ottimizzazione.»

Poi AD-27 impone la `ProofSession`, «serializzabile e ricostruibile senza il codice di alcuna
superficie», e AD-28 la consegna ad Ardesia come evidenza. FR-48 dice cosa contiene:

> Il kernel produce una **`ProofSession`** — `CircuitIR` + `LayoutIR` + `ProofGraph` +
> `ProofCertificates` + **capacità di interazione** — che nessuna superficie possiede.

Tre delle quattro rappresentazioni disgiunte dentro un solo involucro, e l'involucro deve
contenerle **per valore**: «ricostruibile senza il codice di alcuna superficie» esclude che siano
riferimenti risolvibili altrove. AD-21 è rispettato alla lettera — nessuno dei quattro contiene un
altro — e aggirato nella sostanza da un quinto tipo che li contiene tutti.

**Perché `InteractionState` non ha alternative.** AD-6 impone il server stateless per richiesta;
AD-16 impone che il pannello assistente «non conservi stato locale»; AD-6 dice che lo stato
multi-giro vive in `resume_ref` più la riga a DB. Lo stato di interazione deve quindi essere
serializzato e ritrasmesso, e l'unico contenitore serializzato che attraversa le tre superfici è la
`ProofSession` — che FR-48 dichiara includere «capacità di interazione» e che la superficie MCP
`ProofReplay` usa per «selezione dell'elemento e navigazione nel `ProofGraph`». Il quarto tipo non
ha un modulo proprio in nessun documento: `ui/`, che AD-21 nomina fra i suoi *binds*, non esiste
nell'albero sorgente.

**Effetto.** I «quattro cicli di vita» sopravvivono come convenzione di naming dentro un envelope
unico, versionato insieme, serializzato insieme, invalidato insieme. Il giorno in cui un campo
migra da `LayoutIR` a `InteractionState` per comodità di serializzazione, nessun controllo se ne
accorge — perché il controllo che dovrebbe accorgersene è quello di R5.

---

## R2 — AD-1 e AD-2, emendati lo stesso giorno, si contraddicono su `LayoutPatch`

AD-1 v2: il `LayoutIR` «**non compare mai nella firma di uno stadio di calcolo**». AD-2 v2:
`transform(CircuitIR, params) → (CircuitIR, TransformResult) | Refusal`, dove `TransformResult`
porta `PreserveSet + Delta + Boundary + **LayoutPatch** + Equation + Certificate`. **L'uscita è
parte della firma.** Un `LayoutPatch` è, per definizione, un riferimento a ciò che rattoppa: AD-21
ammette i riferimenti «per identificatore», ma un patch che dichiara `reroute_scope` e la cui
validità dipende da `p_k` non è un identificatore.

Il punto in cui la contraddizione diventa operativa è la validazione. AD-22: «Un `LayoutPatch` con
`preserve` più piccolo di `Pₖ` è **non conforme** e viene rifiutato **in validazione**». FR-38
aggiunge: «Un `LayoutPatch` che dichiara in `preserve` un elemento assente in `p_k` è rifiutato in
validazione». `p_k` è la mappa di posizioni di `Layout(Cₖ)`. Quindi:

- se il controllo sta nello stadio di **Validazione elettrica** — l'unico "validazione" che il
  glossario del PRD e il diagramma degli stadi conoscano — allora quello stadio legge il
  `LayoutIR`, che AD-1 vieta esplicitamente perché «starebbe facendo dipendere il circuito da come
  è disegnato»;
- se scende in `render/`, allora è il renderer a giudicare la conformità del `preserve` — cioè
  esattamente il potere che AD-22 esiste per togliergli, e con esso l'autocertificazione del kill
  criterion che AD-22 nomina come rischio;
- se nasce un terzo validatore che non è uno stadio, lo spine non lo nomina, l'albero sorgente non
  gli dà una directory e la *Capability → Architecture Map* non lo colloca.

Tutte e tre le uscite sono conformi alla lettera. In nessuna delle tre A-0 ha un guardiano nominato.

**Aggravante: `Drawing` è rimasto in piedi con una premessa falsa.** AD-18 non è stato emendato e
oggi motiva sé stesso citando una regola abrogata: «AD-2 dice che una Trasformazione produce
`(IR, Drawing)`». Non lo dice più. Esistono ora due descrizioni dichiarative del disegno —
`Drawing` sotto AD-18 e `LayoutIR`+`LayoutPatch` sotto AD-21/AD-22 — e la convenzione della v2
**benedice la sopravvivenza della prima**: «il termine sopravvive solo dove `AD-1…AD-20` lo
usavano». AD-18 fu scritto proprio contro questo scenario: due unità che rispettano entrambe la
lettera degli AD e producono strutture incompatibili.

---

## R3 — L'insieme chiuso di `Refusal` è quello della v1; la v2 ha aggiunto otto modi di rifiutare

AD-19: `Refusal.cause` appartiene a un'enumerazione chiusa — `topology`, `units`, `unsolvable`,
`path_disagreement`, `residual`, `sanity` — e «**aggiungere una causa è una modifica dello spine,
non di un modulo**». AD-19 non è stato emendato il 15 agosto. La v2 ha però introdotto rifiuti che
non hanno una casella:

| Rifiuto introdotto dalla v2 | Dove | Causa disponibile in AD-19 |
|---|---|---|
| round-trip visuale fallito dentro `publish()` | AD-5, FR-41 | nessuna |
| `preserve` più piccolo di `Pₖ` | AD-22, FR-47 | nessuna |
| `boundary` vuoto | AD-22, FR-53 | nessuna |
| promozione di `PerceptionCandidate` — «esito di fallimento proprio» | AD-24, FR-52 | nessuna |
| `SourceAsset` in `UNKNOWN`, fail-closed | AD-25, FR-51 | nessuna |
| `Claim` senza evidenza — «stesso trattamento del Rifiuto» | AD-30, FR-42 | nessuna |
| passo privo di uno dei sei campi | FR-39 | nessuna |
| `BEFORE` non coincidente con l'`AFTER` precedente | FR-39 | nessuna |

Un team che rispetti AD-19 alla lettera **non può esprimere i rifiuti della v2**. Le tre uscite
sono: allargare l'enumerazione senza emendare lo spine (violazione diretta), riclassificarli come
`Failure` (violazione di AD-13: sono esiti di dominio, non guasti tecnici), o introdurre un secondo
tipo di rifiuto accanto a `Refusal`. La terza è la più probabile perché è quella che nessuna regola
vieta — ed è **esattamente il buco che AD-19 fu scritto per chiudere**, registrato nel memlog del
13 agosto: «Validazione e Verifica costruivano payload di `Refusal` di forma diversa rispettando
AD-13». La lente avversariale della v1 ha prodotto AD-19; la v2 lo ha riaperto senza accorgersene.

Nota su AD-24 in particolare: «un passaggio esplicito con esito di fallimento proprio, mai un cast»
è l'unica formulazione dello spine che *dichiara* di volere un esito nuovo. Non dice di che tipo
sia, e AD-13 ammette solo due gerarchie.

---

## R4 — Lo *Structural Seed* è quello della v1: nove AD su dieci vincolano moduli che non esistono

L'albero sorgente dello spine elenca `domain/{ir,validate,transform,solve,verify}` · `ports/` ·
`adapters/` · `pipeline/` · `api/{http,assistant}` · `render/` · `eval/`. Il diagramma dei
contenitori dice ancora `dom[Dominio: IR, Trasformazioni, Verifica]` — «IR» al singolare, il
termine che la convenzione della v2 dichiara ambiguo. Contro questo albero:

| AD | Modulo che vincola | Presente nell'albero |
|---|---|---|
| AD-21 | `ui/` | no |
| AD-22 | `render/layout` | no |
| AD-24 | `perception/` | no |
| AD-25 | `corpus/` | no |
| AD-26 | `experiment/` | no |
| AD-27 | `kernel/`, `adapters/pwa`, `adapters/mcp`, `adapters/ardesia` | no |
| AD-29 | `domain/proof` | no |
| AD-30 | `domain/truthfulness` | no |

La *Capability → Architecture Map* — l'unica tabella dello spine che risponda a «dove vive questa
cosa» — ha dieci righe che coprono FR-1…FR-35 e **nessuna riga per FR-36…FR-53**. Conseguenza
diretta: AD-27 vieta al kernel di importare codice di superficie senza che alcun documento dica
quale directory *sia* il kernel. `domain/`? `domain/`+`pipeline/`? più `render/`, che AD-5 rende
parte della certificazione? La risposta cambia il verdetto del test, e non è scritta da nessuna
parte.

**Il secondo effetto è più insidioso: il renderer è insieme modulo e adapter.** `RenderPort` compare
nell'elenco dei port; `render/` compare come pacchetto di pari grado nell'albero. Lo spine non dice
mai quale dei due produce l'SVG. Se è l'adapter dietro `RenderPort`, allora:

- AD-5 v2 mette il round-trip visuale **dentro `publish()`** e dichiara che il gate «non ha flag di
  bypass, nemmeno amministrativo o **di test**»;
- AD-15 autorizza `eval/` a invocare la stessa pipeline «**sostituendo solo gli adapter**».

Le due regole insieme dicono che l'harness può sostituire l'unica unità da cui dipende il verdetto
di certificazione, restando conforme. Il bypass non ha bisogno di un flag: è il meccanismo
sanzionato. E il paradigma stesso motiva male questa scelta — «tutto ciò che è non deterministico
sta fuori, dietro port» — mentre in v2 il rendering non è non deterministico affatto: è portante
per la prova (AD-5, AD-23, AD-26). È il conflitto fra il paradigma ports-and-adapters della v1 e la
struttura a quattro rappresentazioni: la v1 metteva dietro porta ciò di cui non ci si fida; la v2 ha
messo dentro la prova una cosa che sta dietro porta.

---

## R5 — «Un test fallisce sulla dipendenza inversa» è una promessa, tre volte

La stessa frase compare in tre AD con tre soggetti diversi e zero specifiche:

- **AD-21** la chiede fra quattro **tipi**. Nessun documento dichiara in quale modulo risieda
  ciascuno, e fra quattro pari grado non esiste una direzione da invertire: serve dire quale, fra
  `TransformOverlay` e `LayoutIR`, è ammesso conoscere l'altro, in che forma, e cosa conta come
  "scrivere in". Non scrivibile.
- **AD-27** la chiede fra `kernel/` e tre pacchetti adapter. Nessuno dei quattro esiste (R4). Non
  scrivibile finché l'albero non li nomina.
- **AD-24 / FR-52** la chiede fra `domain/` e `perception/`. È l'unica dei tre che
  `scripts/check_boundaries.py` coprirebbe domani estendendo il recinto — ed è anche l'unica il cui
  soggetto è una coppia di directory.

**Lo stesso documento sa scrivere istruzioni.** AD-23 nomina operazione, confronto e controllo:
«rimosso il `TransformOverlay`, il rendering delle entità sottostanti è identico a quello senza
trasformazione in corso». AD-26 nomina la firma: «il braccio 0 non riceve `Layout(Cₖ)` nella propria
firma — il vincolo è nel tipo». AD-22 dà la formula: `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` dopo
`node_mapping`. AD-5 dà la procedura: SVG semantico → riparsa → canonicalizzazione → confronto
esatto di grafi. Quattro istruzioni e tre promesse nello stesso documento: la differenza non è di
stile, è che le istruzioni riguardano i confini della v2 **interni al rendering** e le promesse i
confini **fra moduli**, che sono precisamente quelli che l'albero non ha ancora.

**La prova che il meccanismo funziona quando l'istruzione c'è.** La Storia 2.1 ha una matrice
criterio → test e ha prodotto `scripts/check_boundaries.py`: analisi dell'albero sintattico,
risoluzione degli import relativi e assoluti, uscita non nulla con file, riga e import, eseguito
dentro la suite. Copre **una sola freccia** del grafo delle dipendenze — `domain/` non importa nulla
del progetto fuori da sé. Non verifica che `adapters/` sia importato solo dalla composizione radice,
non verifica `ports/ ↛ adapters/`, e non conosce né kernel, né superfici, né i quattro tipi.

**Infine, la frase del paradigma è falsa per lo stack scelto.** Riga 56 dello spine: «un adapter
importato dal dominio è **un errore di compilazione**, non un rilievo di code review». Lo stack è
Python 3.12; `pyproject.toml` ha `dependencies = []` e dev `pytest` + `pytest-cov`; **non esiste né
compilazione né type checker** nel progetto. L'enforcement reale è uno script in CI — meglio della
disciplina, ma non ciò che il paradigma promette. La Storia 2.8 ripete l'errore per la
serializzabilità di `Solution`: «quando il codice viene compilato o il test di contratto gira,
fallisce».

---

## Nota di deriva a valle (non è un rilievo, è il costo di una scelta)

Il memlog registra la decisione di **emendare in loco senza rinumerare**, motivata così:
«Verificato: `epics.md` e `implementation-readiness.md` citano tutti e 20 gli AD, quindi rinumerare
avrebbe rotto due artefatti a valle.» La verifica riguardava i **numeri**. I due artefatti
riproducono però il **testo** della v1 dei quattro AD emendati, e `epics.md` lo eleva a vincolo:
«Ognuno è un vincolo che le storie devono rispettare».

- `epics.md`: «AD-2 — Le Trasformazioni sono funzioni pure `transform(IR, params) → (IR, Drawing)`»
  — la forma che AD-2 v2 abroga.
- `epics.md`, Storia 2.6, criterio di accettazione: «restituisce `(IR, Drawing)` … e `Drawing` è
  dichiarativo». Un team che implementasse la storia alla lettera costruirebbe esattamente ciò che
  AD-22 vieta: il disegno come uscita della Trasformazione.
- `epics.md`: AD-5 senza round-trip, AD-15 senza VCER né famiglie di test obbligatorie.
- `implementation-readiness.md` certifica «20 AD, lint pulito», «35/35 FR», «40 storie», verdetto
  CONCERNS su quattro decisioni della v1. Nessuna riga sui 53 FR, sui 30 AD, su Gate A.

Ricerca testuale su entrambi i file: **zero occorrenze** di `AD-21`…`AD-30`, `kernel`, `perception`,
`corpus`, `LayoutIR`, `TransformOverlay`, `InteractionState`, `ProofGraph`, `ProofSession`, `Claim`,
`SourceAsset`. Non rinumerare ha protetto i riferimenti; non ha protetto i contratti.

---

## Cosa chiuderebbe i cinque rilievi

Nessuno richiede una decisione di prodotto. Tutti e cinque sono lavoro di spine.

1. **R1** — dichiarare `ProofSession` come *proiezione* e non come contenitore: quali dei quattro
   entrano per valore, quali per identificatore, e chi è autorizzato a ricomporli. Poi dare a
   `InteractionState` una directory.
2. **R2** — decidere se il `LayoutPatch` esce dal `Transform` (e allora AD-1 va emendato una seconda
   volta per ammettere l'eccezione, nominandola) o se lo compone un modulo terzo dai campi
   circuitali di FR-38. Ritirare o riscrivere AD-18, oggi motivato da una regola abrogata.
3. **R3** — emendare AD-19 con le otto cause nuove, o dichiarare esplicitamente il secondo tipo di
   esito e il suo canale. È una modifica dello spine per definizione dello spine stesso.
4. **R4** — aggiornare lo *Structural Seed* con le otto directory mancanti, estendere la
   *Capability → Architecture Map* a FR-36…FR-53, e sciogliere l'ambiguità `render/` vs
   `RenderPort` — in particolare se il renderer del round-trip sia sostituibile da `eval/`.
5. **R5** — trasformare le tre frasi in tre istruzioni con lo stesso grado di dettaglio di AD-23 e
   AD-26, ed estendere `check_boundaries.py` oltre `domain/`. Correggere «errore di compilazione»
   in riga 56, o aggiungere un type checker allo Stack.

**Ordine.** R4 precede R5 (non si scrive un test su directory che non esistono) e R2 precede R1
(dove viva il `LayoutPatch` decide cosa `ProofSession` debba contenere). R3 è indipendente e si
chiude in mezz'ora.

---

*Revisione condotta sui soli file. Nessuna esecuzione di test, nessuna verifica in rete.*
