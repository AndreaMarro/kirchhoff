---
name: 'Review di veridicità — Architecture Spine v2'
type: adversarial-review
lane: veridicità
target: ARCHITECTURE-SPINE.md (v2)
authority: docs/02-costituzione-kirchhoff.md (K-0…K-5, owner-locked)
date: '2026-08-15'
method: 'solo file, nessuna esecuzione, nessuna fonte esterna'
---

# Review di veridicità — Architecture Spine v2

**Domanda dell'incarico, alla lettera:** *esiste un percorso, anche indiretto, per cui un modello
linguistico determini un numero, una topologia o un Badge Verificata?*

**Risposta: sì. Cinque percorsi, due critici.** Nessuno richiede malafede, nessuno richiede di
violare un AD: tutti e cinque si percorrono rispettando lo spine alla lettera. È la forma di
difetto che conta, perché è l'unica che sopravvive a una code review.

## Metodo e stato dei file

Lette per intero: `ARCHITECTURE-SPINE.md` (v2, 681 righe), `docs/02-costituzione-kirchhoff.md`,
`prds/prd-Kirchhoff-2026-08-13/prd.md`, `epics.md`, `implementation-readiness.md`,
`ux-designs/.../EXPERIENCE.md` e `DESIGN.md` nelle parti pertinenti.

> ⚠️ **Lo spine è stato modificato durante questa revisione.** Alla prima lettura AD-8 non
> assegnava proprietario a `Claim`, `ProofGraph`, `LayoutIR` e `SourceAsset`, e AD-10 non
> vincolava l'export all'SVG certificato. Alla rilettura entrambi erano emendati. **Questa
> revisione giudica lo stato con AD-8 e AD-10 emendati** (spine a 681 righe, AD-1…AD-30). Due
> rilievi che avevo aperto sono stati chiusi da quelle modifiche e sono registrati come chiusi in
> coda, perché la loro chiusura è parte del giudizio.

## Verdetto

**CONCERNS 🔴 — non pronto per l'implementazione della veridicità.**

Lo spine v2 è *robusto sulla catena che ha nominato* e *cieco sulle quantificazioni*. I due
percorsi critici non nascono da una regola sbagliata: nascono da una regola scritta al **singolare**
dove il dominio è plurale (V1), e da un controllo che confronta un'unità **con sé stessa** (V2).
Sono i due punti in cui il prodotto certifica meno di quanto dichiara di certificare.

Tre precisazioni di merito, perché il verdetto non sia letto più duro di com'è:

- **Sul numero finale la catena tiene.** FR-10 (due percorsi), FR-11 (cinque controlli), AD-4
  (segnaposto) e la tolleranza di Story 2.10 rendono molto difficile che un LLM *inventi* una
  cifra consegnata. Il rischio residuo sui numeri è di **collocazione**, non di invenzione (V3).
- **AD-10 emendato ha chiuso la porta dell'export**, che era la più larga. Va detto.
- **Nessuno dei cinque percorsi richiede un VLM.** La domanda «un VLM può entrare da una porta
  laterale?» ha una risposta più scomoda di sì: la porta laterale del VLM è **chiusa**, e il buco
  che il VLM avrebbe potuto tappare è **aperto e senza custode** (V2).

| # | Percorso | Cosa determina un modello | Gravità |
|---|---|---|---|
| **V1** | `publish()` certifica **un** disegno; la derivazione ne ha *N* | la topologia dei passi intermedi, che sono il prodotto | 🔴 critica |
| **V2** | Il round-trip certifica le annotazioni dell'SVG, non la sua geometria — e le scrive la stessa unità | la topologia *vista*, contro quella dichiarata | 🔴 critica |
| **V3** | AD-4 vieta la cifra inventata, non il segnaposto sbagliato; il `TruthfulnessGate` non è fra i controlli di `publish()` | quale numero compare dove, e l'ordine dei passi | 🟠 alta |
| **V4** | Il degrado a superficie non interattiva produce un Badge che non si apre | il Badge, per omissione della prova | 🟠 alta |
| **V5** | `epics.md` costruisce l'AD-5 **non** emendato: Story 2.8 applica il Badge «se e solo se tutti e cinque» | il Badge, senza round-trip | 🟠 alta |

---

## V1 — `publish()` certifica un disegno; la derivazione ne ha *N* 🔴

### Il testo

AD-5 emendato (spine 141-146), al singolare, tre volte:

> «il Badge Verificata è applicato **se e solo se** tutti e cinque passano **e** l'SVG semantico,
> riparsato e canonicalizzato, riproduce esattamente il `CircuitIR` atteso»

`publish(solution) → Published | Refusal` prende **una Soluzione**. AD-29 dice che la derivazione
è un `ProofGraph` e che «la soluzione finale è **l'ultimo nodo del grafo**». Un `ProofGraph` con
cinque passi ha **sei** stati circuitali, **sei** `LayoutIR`, **sei** SVG — e *un* «`CircuitIR`
atteso» nella regola che li certifica.

### Perché è conforme e sbagliato insieme

Un'unità che esegue il round-trip sul solo stato finale rispetta AD-5 alla lettera: c'è un SVG
semantico, è riparsato, è canonicalizzato, riproduce esattamente il `CircuitIR` atteso. Il gate
restituisce `Published`, il Badge è applicato. Anche il diagramma della pipeline (spine 550-566)
la conferma: `sa/sb → ver[Verifica 5 controlli] → pub{Passano tutti?} → out[Published]`, **senza
alcun round-trip e senza alcun ciclo sui nodi**; il round-trip compare solo nel secondo diagramma
(spine 583-591) come `LI → RT → PUB`, cioè **una volta per sessione**.

Il PRD è più forte dello spine su questo punto, ed è la prova che la perdita è avvenuta nella
traduzione: FR-40 «**Ogni** nodo del `ProofGraph` è uno stato visuale certificato»; FR-41 «**Un**
disegno che non supera il round-trip non viene pubblicato»; SM-16 (RRC) è definita come *«quota di
rendering»*, cioè su una popolazione. Lo spine ha compresso una quantificazione universale in un
controllo singolo.

### Il punto di rottura

I disegni intermedi **non sono un allegato**: sono l'oggetto venduto. `EXPERIENCE.md` lo dichiara
senza margine — *«non esiste una superficie "Soluzione" … la sessione è il prodotto e il risultato
numerico è l'ultimo nodo del `ProofGraph`»*. FR-49 li mostra tutti (Prima↔Dopo, `proofgraph-rail`,
provenienza di un elemento). Quindi:

**la parte del prodotto che l'utente guarda di più è quella che il gate copre di meno.** Un errore
di rendering al passo 2 — `R3` disegnata sul nodo sbagliato — è invisibile al gate se lo stato
finale è corretto, e i cinque controlli non lo vedono per costruzione (girano sul `CircuitIR`, non
sul disegno). L'utente vede un passo falso sotto un Badge vero.

E il costo è asimmetrico: **è esattamente il difetto che Gate A misura**. VCER e SM-21 valutano la
continuità visuale passo per passo; se i passi intermedi possono essere sbagliati senza che il gate
se ne accorga, il verdetto di Gate A misura anche il rumore del renderer.

### La chiusura

AD-5 va riscritto con il quantificatore, e la firma va cambiata perché il tipo lo imponga:

> `publish(proof_graph) → Published | Refusal`. Il Badge Verificata è applicato **se e solo se** i
> cinque controlli passano sulla soluzione **e** il round-trip visuale passa su **ogni nodo** del
> `ProofGraph`. Un `ProofGraph` in cui anche un solo nodo non supera il round-trip produce
> `Refusal`, non un `Published` parziale (NFR-16). `publish()` non accetta un singolo stato: non
> esiste una firma che permetta di certificarne uno solo.

E il diagramma della pipeline va corretto: oggi mostra un gate che non contiene il controllo che
AD-5 dice essere dentro il gate.

---

## V2 — Il round-trip certifica le annotazioni dell'SVG, non la sua geometria 🔴

### Il testo

FR-41: il sistema «esporta SVG **semantico** con `data-component-id` e `data-terminal-*`, lo
riparsa in un `ReconstructedCircuitIR`, lo canonicalizza, e lo confronta **esattamente** col
`CircuitIR` atteso», e — testuale — «Il confronto è di grafi, **non di pixel** e non di stringhe».

AD-8 emendato: `LayoutIR` ha per scrittore unico `render/layout`. AD-18: «la rasterizzazione e la
serializzazione (SVG, CircuiTikZ) appartengono **esclusivamente** a `render/`».

### La forma del difetto

Il round-trip confronta **ciò che `render/` dichiara** (`data-*`) con **ciò che `domain/` sa**
(`CircuitIR`). Non confronta mai ciò che `render/` dichiara con **ciò che `render/` disegna**.

Le due uscite di `render/` — la geometria che lo studente vede e i `data-*` da cui si ricostruisce
il grafo — sono prodotte dalla stessa unità e **nessun controllo le mette a confronto fra loro**.
Un renderer che disegna il filo sul piedino sbagliato ed emette il `data-terminal-*` giusto:

- supera il round-trip (il grafo ricostruito dai `data-*` è corretto);
- supera i cinque controlli (girano sul `CircuitIR`, che è corretto);
- supera R-Visual-1 (AD-23 verifica l'occlusione, non l'incidenza);
- supera SM-20 (è perfettamente deterministico: sbaglia sempre uguale);
- **prende il Badge Verificata su un disegno falso.**

È la stessa autocertificazione che AD-22 vieta esplicitamente altrove — *«che il soggetto misurato
scelga la propria misura»* — qui però permessa, perché la misura e il misurato escono dalla stessa
funzione.

### Il VLM: la porta è chiusa e il buco è scoperto

Qui la domanda dell'incarico sulla percezione trova la sua risposta vera. AD-5 chiude:
«Nessun VLM partecipa alla certificazione della topologia», e FR-41 conferma: «La QA percettiva
esiste, è separata, e non concede `Verified`». **La chiusura è giusta** — K-1 non ammette
alternative.

Ma il seguito manca su tre livelli, e il terzo è quello che conta:

1. La QA percettiva **non ha un metodo di porta**: `ModelPort` espone `extract`, `plan`, `narrate`
   (AD-3, spine 120) e nient'altro.
2. **Non ha un modulo**: l'*Albero sorgente* (spine 621-639) è ancora quello della v1 — non
   contiene `perception/`, `corpus/`, `experiment/`, `kernel/`, `domain/proof` né
   `domain/truthfulness`, cioè cinque dei moduli che AD-8 emendato, AD-24, AD-25, AD-27 e AD-30
   nominano come proprietari. La *Capability → Architecture Map* (spine 661-674) si ferma a FR-35:
   **non esiste una riga per FR-37…FR-53**, quindi nessuna riga governa il kernel visuale, il
   round-trip o il gate di veridicità.
3. **Nessun controllo deterministico è messo al posto del VLM.** SM-C8 del PRD riconosce metà del
   problema — «Il round-trip non la vede: un SVG può riprodurre esattamente il grafo ed essere
   inguardabile» — ma è una *counter-metric* sulla leggibilità, non un gate, e non copre il caso
   geometria-che-contraddice-i-`data-*`.

Un componente che esiste nel testo, non ha porta, non ha modulo e non ha AD è a **un refactor di
distanza** dall'essere chiamato da dove capita. Il rischio non è che qualcuno metta un VLM nel
gate: è che il gate resti senza il controllo che serviva, e che la QA percettiva diventi l'unico
posto dove il difetto si vede — cioè un giudizio di modello su cui nessuno ha messo una regola.

### La chiusura

Serve un **AD nuovo**, non un emendamento, perché introduce un controllo che oggi non esiste in
nessun documento — e **non richiede alcun modello**:

> **AD-31 — Il disegno consegnato è coerente con le proprie annotazioni.**
> *Prevents:* che `render/` certifichi sé stesso — che i `data-*` da cui si ricostruisce il grafo e
> la geometria che lo studente vede divergano senza che alcun controllo le confronti.
> *Rule:* prima del round-trip, `render/` esegue un **controllo di incidenza geometrica**
> deterministico: ogni conduttore disegnato ha gli estremi coincidenti, entro tolleranza
> dichiarata, con gli ancoraggi dei terminali che il suo `data-terminal-*` nomina; ogni
> `data-component-id` racchiude il glifo che dichiara; nessun terminale dichiarato resta
> geometricamente scollegato. È il **sesto controllo** di `publish()` e una **famiglia di test
> obbligatoria** (FR-46). Nessun modello partecipa: è geometria contro metadati, entrambi già in
> memoria.

E la QA percettiva va **nominata dove sta**: modulo proprio nell'albero, fuori dalla trusted
computing base, con la riga «non concede `Verified`, non alimenta alcuna soglia, non è ingresso di
alcun gate» scritta nello spine e non solo nel PRD.

---

## V3 — La cifra non è inventata, ma può essere quella sbagliata 🟠

### AD-4 protegge da un errore e ne lascia passare un altro

AD-4 (spine 128-130): il generatore «riceve e restituisce **segnaposto** in sintassi `[[q1.value]]`,
mai cifre … Un testo generato che contiene una cifra letterale è respinto prima della
pubblicazione.»

Il controllo è **sintattico**: cerca cifre. Nulla verifica che il segnaposto **scelto dal modello**
sia quello di cui la frase parla. Un narratore che scrive *«la corrente nel ramo centrale vale
`[[q2.value]]`»* dove la grandezza del passo è `q1` produce un testo che:

- non contiene cifre → AD-4 lo accetta;
- viene risolto dal renderer con **un numero calcolato correttamente** → nessun residuo lo rileva;
- porta all'utente **il numero giusto sulla grandezza sbagliata**.

E FR-13 — «i testi generati che contengono numeri li riprendono dal risultato calcolato, e **la
coerenza fra i due è verificata** prima della pubblicazione» — è **vacuo per costruzione**: se per
AD-4 il testo non contiene numeri, non c'è nessuna coppia di cui verificare la coerenza. Le due
regole si annullano: AD-4 svuota l'oggetto del controllo di FR-13.

Questo è, alla lettera, il danno che AD-4 dichiara di prevenire — *«l'errore silenzioso più costoso
del prodotto»* — che rientra dalla porta che AD-4 lascia aperta.

### E l'ordine dei passi

Sì, un modello lo determina. AD-3 lega `ModelPort.plan` al «pianificatore didattico»; FR-14 dice
che il sistema «produce un Piano didattico scegliendo solo Trasformazioni del Catalogo». Il vincolo
è reale ma è **solo sul risultato**: Story 2.10 chiede che «il risultato ottenuto coincida con il
Percorso A entro tolleranza». Una sequenza didatticamente assurda che converge allo stesso numero
passa. Poiché §1 vende **la derivazione**, non la risposta, l'oggetto venduto è scelto da un
modello e verificato solo sul suo sottoprodotto commodity.

Non lo chiamo violazione: K-1 dice *«i modelli propongono»*, e proporre un ordine è proporre. Lo
chiamo **misura mancante**: nessuna metrica di §8 valuta la qualità dell'ordine — TVR misura la
validità di ogni trasformazione, SEC la completezza dei campi, VCER la continuità geometrica.
Nessuna dice se la sequenza è un procedimento.

### Il `TruthfulnessGate` esiste e non è cablato

AD-30 dà lo strumento giusto — «ogni affermazione pubblicabile è un `Claim` tipizzato **con la
propria evidenza**» — e AD-8 emendato gli dà lo scrittore unico (`domain/truthfulness`), il che
chiude la domanda dell'incarico *«un adapter può emettere un `Claim` senza passarci?»*: **a
permessi DB, no**.

Ma resta la domanda gemella, che nessun file chiude: **`publish()` chiama il `TruthfulnessGate`?**
AD-5 enumera i propri controlli — cinque più il round-trip — e **il `TruthfulnessGate` non è fra
questi**. Nessun AD dice dove gira. Il risultato è un `Published` i cui `Claim` di narrazione
possono non essere mai passati dal gate che li governa: due gate definiti, uno solo cablato
all'uscita. E AD-19 non ha una causa per questo caso — l'enumerazione chiusa è `topology`, `units`,
`unsolvable`, `path_disagreement`, `residual`, `sanity`.

### La chiusura

Tre righe, tutte piccole:

1. **AD-4 guadagna la seconda metà.** «I segnaposto di un segmento di narrazione sono un
   sottoinsieme delle grandezze nominate dall'`EQUATION` del passo cui il segmento è ancorato e
   dagli `evidence_ids` del suo `Claim`. Un segnaposto che risolve fuori da quell'insieme è
   `Refusal`, non un avviso.» Rende il controllo **semantico** invece che sintattico, ed è ciò che
   fa comporre AD-4 con AD-30.
2. **AD-5 nomina il `TruthfulnessGate` fra i propri controlli**, o AD-30 dichiara il proprio punto
   di chiamata. Oggi né l'uno né l'altro.
3. **AD-19 guadagna la causa** `claim_unsupported` (subject: il `Claim` o il segnaposto), altrimenti
   il rifiuto non è esprimibile e chi implementa userà `sanity` per tutto.

---

## V4 — Il degrado a superficie non interattiva produce un badge che non si apre 🟠

K-4 è la legge più corta della costituzione e non ha eccezioni: *«Badge e certificazioni **devono
aprirsi** sulla prova: residui, mappatura dei terminali, cross-check, provenance, versioni dei
verificatori … Un badge che non si apre è un'affermazione.»*

AD-27 dichiara previsto il percorso che la rende impossibile: «**funziona senza MCP Apps**: il
degrado a superficie non interattiva è un percorso previsto, non un guasto». `EXPERIENCE.md`
descrive che cosa resta — «passi come immagini semantiche più il testo strutturato».

AD-16 impone che ogni risposta con pannello porti `content`, «rappresentazione testuale per il
contesto del modello e per gli host senza UI». **Non impone che cosa `content` debba contenere.**
Quindi la variante economica del degrado — mostro il Badge, non porto la prova — è conforme ad
AD-16, ad AD-27 e ad AD-5, e viola K-4 senza che alcun controllo la veda.

**È il percorso «meglio di niente» che l'incarico chiede di cercare, ed è progettato.** K-3 dice che
il rifiuto è progettato; qui è progettato il **degrado**, e il rifiuto — o il declassamento
dell'affermazione — non è raggiungibile.

Un secondo esemplare, più piccolo, della stessa forma: FR-14 e Story 2.10 fanno «ripiegare il
sistema sul **piano canonico nodale**, senza intervento manuale» quando il Piano didattico non
converge. Il numero resta vero, ma il metodo nodale produce pochissime trasformazioni topologiche,
quindi pochissimi stati visuali: il prodotto consegna, con Badge pieno, **la cosa che dichiara di
non essere** — un calcolo invece di una derivazione disegnata. VVDR e VDR la contano come
derivazione completa e certificata; **nessuna counter-metric misura la quota di soluzioni prodotte
per ripiego** (SM-C5 sorveglia l'ampiezza del catalogo, non il fallback).

### La chiusura

- **AD-16:** «Su una superficie che non può aprire la prova, `content` porta i cinque residui,
  l'esito del round-trip e `verifier_id` + versione. Se non può portarli, il Badge non è reso: si
  rimanda alla superficie che apre la prova (`EXPERIENCE.md`: *mai una versione degradata*). Un
  Badge senza la propria prova sulla stessa superficie è una violazione di K-4, non un limite di
  formato.»
- **Counter-metric nuova** — quota di derivazioni consegnate per ripiego sul piano nodale.
  Controbilancia SM-3 e VDR. Le soglie sono owner-locked; il numero no, esattamente come per VCER.

---

## V5 — `epics.md` costruisce l'AD-5 non emendato 🟠

Lo spine v2 spiega perché non ha rinumerato: «`epics.md` e `implementation-readiness.md` li citano
tutti e venti». Ha protetto **le citazioni** e lasciato indietro **i contenuti**. `epics.md` è oggi
l'unico artefatto da cui si costruisce, e dichiara in testa: «35 FR», «20 AD». Conseguenze
puntuali, verificate riga per riga:

| Dove | Che cosa dice `epics.md` | Che cosa dice lo spine v2 |
|---|---|---|
| Story 2.8 | «il Badge Verificata è applicato **se e solo se tutti e cinque i controlli** sono passati (FR-11)» | cinque **più il round-trip**, dentro `publish()` (AD-5 em.) |
| Story 2.6 | la Trasformazione «restituisce `(IR, Drawing)`» | `TransformResult`; **`Drawing` non esiste più** (AD-2 em., AD-18 em.) |
| riga 102 | AD-4 nella forma non emendata | invariata, ma senza il legame al `Claim` (V3) |
| Additional Requirements | AD-1…AD-20 | AD-1…AD-30 |

Story 2.8 è **la storia che implementa il gate**. Eseguita alla lettera, produce un Badge senza
round-trip — cioè ricrea a valle esattamente il rilievo che `review-costituzione.md` aveva marcato
🔴 bloccante come V5 («`Verified` è definito escludendo il round-trip visuale») e che il PRD aveva
chiuso in FR-11.

**Chiusura:** `epics.md` va rigenerato prima di aprire Epic 2, e fino ad allora Story 2.6 e Story
2.8 sono note-come-errate. `implementation-readiness.md` va riletto con esso: dichiara «Conflitti
fra artefatti: **nessuno rilevato**» su uno stato del mondo che non esiste più.

---

## Annesso A — due rilievi chiusi durante la revisione

Registrati perché la loro chiusura fa parte del giudizio, e perché un lettore che confronti versioni
diverse dello spine non li ritrovi come aperti.

- **`Claim` senza scrittore unico** — AD-8 elencava quattro entità e la v2 ne aveva aggiunte sette,
  fra cui `Claim`. L'enforcement «a permessi DB» era inapplicabile su una tabella senza
  proprietario. **Chiuso** dalla tabella di AD-8 emendato (`Claim` → `domain/truthfulness`).
- **L'export come porta laterale** — `export(published, format)` applicava la marcatura **dopo** la
  certificazione, e PDF/CircuiTikZ non possono portare `data-component-id`: uscivano col Badge senza
  round-trip. **Chiuso** da AD-10 emendato («l'SVG semantico verificato è la sorgente unica di ogni
  altro formato; `export()` non ri-renderizza»). È la chiusura migliore delle due.

## Annesso B — le porte che ho verificato e che risultano chiuse

Perché una revisione che elenca solo i buchi non dice quanto è coperta la superficie.

| Porta cercata | Esito |
|---|---|
| **Export** | chiusa da AD-10 emendato (Annesso A) |
| **Studio / Varianti** | chiusa: AD-8 «`studio` **chiama** `publish()` e scrive solo `Variant`» |
| **Bypass amministrativo o di test** | chiusa: AD-5 «nemmeno amministrativo o di test» + NFR-11 + Story 2.8 (compilazione o test di contratto fallisce) |
| **`eval/` come percorso alternativo** | chiusa da AD-15 («nessun ramo `if testing`») |
| **Percezione → kernel** | chiusa da AD-24 e FR-52: `PerceptionCandidate`, promozione esplicita con esito di fallimento proprio, mai un cast |
| **Ardesia / LessonOS come seconda autorità** | chiusa da AD-28: sola lettura, `TruthfulnessGate` resta in Kirchhoff |
| **Turno di chat come sorgente di verità** | chiusa da FR-48: «nessun valore o topologia proviene dal turno di chat» |
| **Cache** | **non governata**: la parola compare solo nel *Prevents* di AD-5 e nel *Deferred* (cache dei Pass di estrazione). Nessun AD dice se un `Published` o un SVG certificato siano cacheabili, né con quale chiave. Non l'ho contata fra i cinque percorsi perché oggi non esiste una cache: va nominata **prima** che esista, non dopo |
| **Anteprima di ricostruzione (FR-5)** | fuori Gate A (percorso foto → Gate C). Segnalo per il momento in cui rientra: è un disegno che l'utente **conferma** e che non attraversa alcun round-trip — la conferma umana, che è anche la sorveglianza richiesta dalla conformità, si esercita oggi su un artefatto non verificato |

## Ordine di risoluzione

1. **V1** e **V2** prima di scrivere `publish()` — cambiano la firma del gate e aggiungono un
   controllo. Dopo, sono una migrazione.
2. **V5** prima di aprire Epic 2 — è l'artefatto da cui si costruisce.
3. **V3** prima del primo testo narrato; **V4** prima del primo adapter non interattivo.
4. **Cache** e **Anteprima** (Annesso B): da nominare quando entrano, non quando si scoprono.

Nessuno dei cinque tocca un confine owner-locked: nessuno propone una soglia, nessuno ridefinisce
`Verified` al ribasso. **V1, V2 e V3 lo stringono** — e se stringere la definizione di `Verified`
richiede comunque la decisione dell'owner, questa revisione si ferma e lo segnala, come impone la
regola di collisione della costituzione. Non sceglie, non aggira.
