# Review del kill criterion — Gate A (Kirchhoff PRD v3)

Documento sotto esame: `prd.md` v3 (1221 righe, 15 ago 2026). Sezioni lette a fondo: §7 (callout +
§7.0, §7.1, §7.2), §5.0 (FR-37…FR-43), §8. Letti come controllo incrociato: `docs/02-costituzione-
kirchhoff.md` (K-0…K-5) e `docs/inbox/kirchhoff_01_piano_master_v3.md` §24 e §27.

Revisore senza contesto pregresso e senza interesse nell'esito. Il criterio applicato è uno solo:
**due team competenti e in buona fede, dato lo stesso artefatto e questo PRD, arriverebbero allo
stesso verdetto?**

---

## Verdetto in una riga

**Il gate non è falsificabile come scritto.** Il confronto decisivo — «continuità visuale vs
re-layout completo» — non ha braccio di confronto in scope, non ha unità di misura comparativa, non
ha campione, non ha regola di decisione, non ha decisore, e la metrica nominata per portarlo
(SM-14 VCER) misura una cosa diversa da quella che il gate afferma. Il gate, così com'è, non può
produrre un «no» che qualcuno accetti — e produrrà quasi certamente un «sì» che non significa
niente.

Il PRD **sa** di avere questo problema e lo scrive:

> `[ASSUMPTION: il kill criterion è valutabile in modo non ambiguo dal confronto fra continuità
> visuale e re-layout completo su serie/parallelo/partitore. Se la valutazione risultasse
> soggettiva, il gate va reso misurabile prima di eseguirlo — è la condizione perché §7 abbia
> senso.]` (§7.0)

Questa review è la risposta a quell'assunzione: **la valutazione *è* soggettiva**, e la condizione
perché §7 abbia senso non è ancora soddisfatta. Non è una critica alla tesi del prodotto — è un
rilievo su uno strumento di misura che non può misurare la tesi.

---

## 1. Falsificabilità

### 1.1 Il testo del gate, e cosa contiene di operativo

> 🔑 **Il kill criterion che precede tutto — Gate A.**
> Se la **continuità visuale non è chiaramente migliore di un re-layout completo**, il catalogo
> delle trasformazioni **non si espande** e il prodotto non ha una ragione di esistere nella forma
> descritta da §1. Bastano **serie, parallelo e partitore** per saperlo. (§7, callout)

Il testo è identico, parola per parola, al piano master §24 («se la continuità visuale non è
chiaramente migliore di un re-layout completo, non espandere il catalogo»). Il PRD **non aggiunge
nulla di operativo** a monte: eredita una frase da roadmap e la promuove a gate di sopravvivenza
del prodotto. Nessuno dei due documenti la rende eseguibile.

Contiene esattamente un elemento operativo — il dominio su cui misurare: serie, parallelo,
partitore. Tutto il resto è da inventare a valle.

### 1.2 Cosa manca, punto per punto

**(a) La baseline — il braccio «re-layout completo» non esiste in scope.**

Il gate è per costruzione un confronto a due bracci. §7.1 elenca ciò che si costruisce, e il
re-layout **non c'è**. Peggio: FR-37 lo vieta esplicitamente come comportamento di sistema.

> - Il sistema **non** ricalcola il layout globale a ogni passo: dopo una trasformazione locale, il
>   numero di elementi con coordinate cambiate è limitato allo `reroute_scope` dichiarato.
> (FR-37, Consequences)

Costruire la baseline significa quindi costruire una modalità che i requisiti escludono, con un
algoritmo che nessun documento nomina. Quale re-layout? Force-directed? Griglia canonica? Sugiyama?
Con quale seed, quale ordinamento dei nodi, quale renderer, quale styling? Un force-directed con
seed casuale e un layout ortogonale deterministico su ordinamento canonico si comportano in modo
**opposto** sulla stabilità posizionale di una riduzione serie/parallelo. La scelta della baseline
determina il verdetto, e la scelta non è fatta né vincolata.

**(b) L'unità di misura — SM-14 VCER non può portare il gate.**

Il PRD nomina la metrica in due punti, senza ambiguità:

> - Vale `p_{k+1}(x) = p_k(x)` per **ogni** `x ∈ preserve`. La violazione è un errore, non una
>   tolleranza: alimenta SM-14 (VCER), che è la metrica del kill criterion. (FR-38)

> - **SM-14 — VCER (Visual Continuity Error Rate).** Quota di `LayoutPatch` che violano
>   `p_{k+1}(x) = p_k(x)` su almeno un `x ∈ preserve`. **È la metrica del kill criterion.** Valida
>   FR-38. (§8)

VCER è una metrica **a un braccio solo**, **auto-dichiarata**, e **di conformità, non di
confronto**. Tre conseguenze:

1. *Non ha valore nel braccio baseline.* Un sistema a re-layout completo non emette `LayoutPatch`
   e non dichiara `preserve`. Il suo VCER non è alto o basso: è **indefinito**. Non si può
   confrontare `VCER_continuità` con `VCER_relayout`, perché il secondo termine non esiste. La
   metrica designata a decidere un confronto non è calcolabile su una delle due cose da
   confrontare.
2. *È banalmente saturabile.* VCER misura se il sistema rispetta ciò che **ha dichiarato** di
   conservare. Nessun requisito impone che `preserve` sia **massimale**. FR-38 vieta solo il caso
   opposto — dichiarare in `preserve` un elemento assente in `p_k`. Un `LayoutPatch` con
   `preserve = {}` ha VCER = 0 per costruzione e supera ogni controllo scritto. VCER = 0 è quindi
   compatibile con «ho ridisegnato tutto a ogni passo».
3. *Misura FR-38, non §1.* VCER risponde a «l'implementazione rispetta il proprio invariante?».
   Il gate chiede «la continuità visuale vale più di un re-layout?». Sono domande diverse e la
   prima non implica la seconda in nessuna direzione.

Il PRD intravede il problema (2) e istituisce SM-15 proprio contro quello:

> - **SM-15 — SEC (Steps per Edit Cost).** Costo di ri-layout per passo. Distingue «continuità» da
>   «ho ridisegnato tutto e sembrava uguale».

Ma SEC è **una riga**: «costo di ri-layout per passo». Costo in cosa? Elementi con coordinate
mutate? Spostamento totale in unità di layout? Frazione del disegno che cambia? Tempo di
calcolo? Nessuna definizione, nessuna soglia, nessuna direzione. La metrica che dovrebbe reggere
l'anti-confondimento è meno definita della metrica che confonde. **SEC, non VCER, è la candidata
naturale a portare il gate** — è l'unica delle sei nuove che è calcolabile su entrambi i bracci —
ed è la meno specificata di tutte.

**(c) Il campione — non esiste.**

Nessun numero di circuiti, nessuna stratificazione, nessuna distribuzione di difficoltà, nessun
held-out per la dimensione layout. L'unico insieme di riferimento definito è quello di FR-34, e il
PRD dichiara esplicitamente che copre altro:

> **Limite di copertura dal 13 agosto 2026.** L'insieme di riferimento è **strutturato**, non
> fotografico: copre la catena a valle dell'IR — solver, Trasformazioni, Verifica — e **non**
> l'estrazione da immagine. (FR-34, Notes)

«Solver, Trasformazioni, Verifica»: la continuità di layout non è nell'elenco. Non esiste un corpus
di Gate A.

**(d) La regola di decisione — «chiaramente migliore» non ha operatore, e le soglie sono
owner-locked.**

> 0. 🔴 **Soglie di lancio di VVDR, NED, TVR, VCER, SEC, RRC, VDR.** **Owner-locked** […] i numeri
>    **non stanno in questo PRD e non vanno inferiti a valle**. Un artefatto che li propone è in
>    errore, non in evoluzione. Blocca la dichiarazione di superamento di Gate A, **non** la sua
>    costruzione. (§16.0)

La distinzione fra «blocca la dichiarazione» e «blocca la costruzione» è corretta e ben fatta. Ma
il risultato netto è che **il gate non è eseguibile fino a una decisione che non ha né owner
nominato, né data, né definizione di «fatto»**, e che a valle è vietato anche solo proporre. Il PRD
si è chiuso legittimamente una porta e non ne ha aperta un'altra.

Rilievo aggiuntivo verificato a monte: il piano master §27.6 blocca «Soglie **VVDR/SER/RRC** di
lancio». Il PRD estende il lock a sette metriche, includendo **VCER** — cioè proprio la metrica del
kill criterion. L'estensione può essere voluta, ma l'effetto è che la soglia decisiva è l'unica
cosa che nessuno può scrivere.

**(e) Chi decide — non è nominato.**

FR-43 richiede che la decisione sia registrata, ed è la cosa giusta:

> - L'espansione del Catalogo richiede la decisione registrata che il kill criterion è passato — non
>   è una scelta di implementazione.

Ma il PRD non dice **chi** firma, **su quale pacchetto di evidenze**, in **quale formato**, né cosa
succede in caso di risultato ambiguo. «Decisione registrata» senza contenuto specificato è una
casella, non un controllo.

**(f) Il difetto più profondo: il gate misura una cosa e afferma un'altra.**

Il gate non conclude solo «non espandere il catalogo». Conclude:

> […] e **il prodotto non ha una ragione di esistere nella forma descritta da §1**.

§1 e §7.0 dicono cosa sarebbe da provare:

> Il bene scarso non è il numero finale […] È la **continuità visuale della derivazione** (§1)
> Studio, foto, tutor e lavagna poggiano tutti sulla stessa promessa: che la derivazione disegnata
> valga più della risposta. (§7.0)

«Valga più» è un'affermazione di **valore per un essere umano**. Tutte le misure proposte — VCER,
SEC, VDR, TVR — sono **interne alla macchina**: conservazione dei patch, costo di ri-layout,
determinismo del renderer. Nessuna di esse, in nessuna combinazione, può stabilire che una
derivazione disegnata valga più di una risposta per uno studente.

E l'MVP rimuove per decisione esplicita l'unico strumento che potrebbe misurarlo:

> **Conseguenza accettata:** nessun ricavo nell'MVP, e nessun canale di acquisizione. […]
> **Conseguenza da sorvegliare:** un MVP senza utenti non produce segnale di mercato. (§7.0)

Il PRD registra la conseguenza come rischio commerciale (nessun segnale di mercato) ma **non si
accorge che è anche un problema di misura**: senza nessun umano nel circuito, il gate può al
massimo rispondere a «sappiamo implementare patch di layout locali con basso tasso di violazione?»
— che è una domanda di ingegneria, non la domanda che uccide o salva il prodotto.

Nota costruttiva: il pool di soggetti **esiste già** ed è nel PRD stesso (§17): «Il fondatore
mantiene l'attività di ripetizioni: finanzia lo sviluppo, fornisce il gold set e i primi utenti».
Un protocollo in cieco su 15–20 studenti reali, due bracci, stessa soluzione e stesso numero
finale, rubrica pre-registrata, costa qualche ora e chiude il buco di validità di costrutto. Non è
scritto da nessuna parte.

### 1.3 Dove il documento è invece adeguato — e va detto

- **FR-38 formalizza l'invariante**: `p_{k+1}(x) = p_k(x)` per ogni `x ∈ preserve`, con «la
  violazione è un errore, non una tolleranza». Questo *è* testabile, senza ambiguità. Il problema
  non è l'invariante: è che l'invariante non è il gate.
- **FR-41 è il pezzo migliore del PRD**: «Il confronto è di grafi, non di pixel e non di stringhe»
  e «**Nessun VLM partecipa alla certificazione della topologia**». Un controllo primario
  deterministico, con un esito tipizzato («produce Rifiuto tipizzato, non un avviso»). Questo è
  come si scrive un requisito falsificabile.
- **SM-17 (VDR)** identifica correttamente un pericolo reale e non ovvio: «Un renderer non
  deterministico rende il round-trip non falsificabile». Averlo visto in fase di PRD è merito.
- **SM-C5** è un contatore ben progettato contro il gaming più naturale: «Espandere il catalogo è
  il modo più naturale per far salire VVDR senza aver dimostrato la continuità visuale — cioè per
  ottimizzare la cosa sbagliata. **Deve restare a tre.**»
- **FR-40** giustifica onestamente una scelta che sarebbe altrimenti sovradimensionata: «l'MVP con
  tre trasformazioni produce grafi quasi lineari. Il ProofGraph entra comunque adesso perché
  cambiarlo dopo è una migrazione di dati, non un refactor». Argomento valido, costo basso, non lo
  conto come surplus.
- **§16.0** distingue correttamente fra bloccare la costruzione e bloccare la dichiarazione.
- **§7.0** contiene l'`[ASSUMPTION]` che nomina esattamente questo rischio. Il documento è onesto
  con se stesso; il problema è che l'onestà non è stata convertita in specifica.

---

## 2. Sufficienza dello scope dichiarato

§7.0 fa una tesi precisa: **«Serve poco per saperlo. Tre trasformazioni — serie, parallelo,
partitore — bastano a misurare la continuità visuale.»** La tesi va testata nelle due direzioni.

### 2.1 In scope ma non necessario al verdetto (lavoro a rischio)

| Elemento (§7.1) | Serve al verdetto? | Nota |
|---|---|---|
| **Marcatura di provenienza su export PDF/SVG** | **No** | Giustificato con «art. 50 AI Act si applica dal 2 agosto 2026 e non si retrofitta». Ma l'art. 50 riguarda sistemi **immessi sul mercato**, e §7.0 dichiara «nessun ricavo nell'MVP, e nessun canale di acquisizione». Un kernel senza utenti non immette nulla. FR-19 non è banale (marcatura macchina + percepibile, sopravvive a copia e stampa, «Nessun percorso del prodotto produce un artefatto esportabile privo di marcatura»): è lavoro reale contro un rischio che non può materializzarsi prima di Gate A. **Attenzione a non tagliare troppo**: l'export **SVG semantico** serve eccome — è il substrato di FR-41. È la *marcatura* e il PDF a essere surplus. |
| **Editor del circuito** | **No** | §7.1 lo mette in scope («Ingresso strutturato soltanto: netlist e sorgente LaTeX, **più l'editor del circuito**»). Per alimentare il kernel bastano netlist e LaTeX. Un editor è una superficie UI, e non è ciò che il gate giudica in nessuna delle due letture (macchina o umano). Surplus netto. |
| **Verifica a cinque controlli, completa** | **Parzialmente** | «Accordo fra percorsi» richiede Percorso A oltre a Percorso B, ed è ciò che rende non vuoto il campo `CERTIFICATE` di FR-39: difendibile. Ma **bilancio di potenza** e **sanità fisica** su reti resistive DC con serie/parallelo/partitore non aggiungono nulla a un verdetto sulla continuità. Difendibile per K-1, non portante per il gate. |
| **Rifiuto tipizzato + SM-16 (RRC)** | **No** | Costituzionalmente dovuto (K-3), non necessario a decidere se la continuità batte il re-layout. |
| **ProofGraph con branch/join** | **No, ma giustificato** | Vedi FR-40: l'argomento della migrazione dati regge. Non lo conto come finding. |

### 2.2 Necessario al verdetto ma assente dallo scope (direzione più grave)

1. **Il braccio baseline.** Nessuna riga di §7.1 costruisce un re-layout completo. Senza, non c'è
   confronto — e il gate è una frase comparativa. **Questo è il buco principale.**
2. **Un corpus di Gate A.** Numero di circuiti, stratificazione per dimensione della rete e per
   profondità della catena di trasformazioni, split held-out. FR-34 esiste per altro.
3. **Un read-out umano.** Se «chiaramente migliore» riguarda il valore, serve un protocollo:
   soggetti, cecità, rubrica pre-registrata, ordine randomizzato. Costo basso, pool già
   disponibile (§17), zero righe nel PRD.
4. **Requisito di massimalità su `preserve`.** VCER deve essere calcolato contro una verità di
   riferimento («cosa *poteva* essere conservato», derivata confrontando `p_k` e `p_{k+1}` in modo
   indipendente dal patch dichiarato), non contro l'auto-dichiarazione del sistema.
5. **Definizione e unità di SEC.** È la metrica anti-confondimento e oggi è una riga.
6. **Una regola di composizione.** Anche con tutte le soglie fissate, il PRD non dice **quale**
   metrica decide, come si combinano VCER/SEC/VDR in un unico pass/fail, né la direzione del
   confronto (delta assoluto? relativo? su quale percentile?).
7. **Contenuto della «decisione registrata»** di FR-43: chi firma, su quali evidenze, con quale
   formato, e cosa si fa in caso di esito ambiguo.

### 2.3 Un difetto di potenza statistica dentro la scelta di scope

§7.1 restringe a **reti resistive DC** e **tre trasformazioni**: serie, parallelo, partitore.
Queste sono esattamente le riduzioni su cui **anche un buon re-layout globale deterministico** —
ordinamento canonico dei nodi, seed fisso — tende a restare stabile, perché il grafo cambia poco e
in modo locale. Il PRD ha scelto il regime in cui l'effetto che vuole misurare è **più piccolo**.
La tesi «bastano tre trasformazioni per saperlo» (§7.0, punto 2) è affermata, mai argomentata, e
va nella direzione sbagliata rispetto alla potenza del test: la continuità visuale dovrebbe
divergere dal re-layout su reti più grandi e catene più lunghe, non su una serie di due resistori.

---

## 3. Come questo gate produce un verdetto sbagliato — modi di fallimento in ordine di probabilità

### A. **Falso PASS per invariante auto-soddisfatto** — probabilità: alta

Il percorso di minor resistenza. Il team costruisce il kernel, VCER esce ≈ 0 perché il sistema
dichiara in `preserve` solo ciò che già sa di non aver toccato, la baseline non è mai stata
costruita (non è in §7.1), e il risultato viene letto come «l'invariante regge → la continuità è
chiaramente migliore». Il confronto non avviene mai: **un test di conformità prende il posto di un
test comparativo**. Tutto nel documento spinge in questa direzione: VCER è l'unica metrica con una
definizione formale, è etichettata due volte «la metrica del kill criterion», e il braccio
alternativo non esiste. Aggravante di incentivo: chi valuta è chi ha speso l'intero MVP a
costruire il braccio che vince.

*Cosa va specificato per chiuderlo:* (i) `preserve` massimale, verificato da un checker
indipendente dal patch dichiarato; (ii) il braccio re-layout come **deliverable in scope di §7.1**,
con algoritmo e configurazione nominati; (iii) il gate riformulato come **delta fra due bracci su
una metrica calcolabile su entrambi** (candidata: SEC, una volta definita), non come livello su una
metrica calcolabile su uno solo.

### B. **Falso PASS per sostituzione di costrutto** — probabilità: alta

Anche costruendo la baseline: la grandezza misurata (elementi spostati per passo) non è la
proprietà affermata (che la derivazione disegnata valga più della risposta). Un sistema può avere
stabilità di layout perfetta e produrre derivazioni che nessuno capisce e nessuno paga. Il gate
dichiara «il prodotto non ha una ragione di esistere» — una conclusione sul valore — sulla base di
una metrica di spostamento. Nessun umano è nel circuito di misura, per decisione esplicita di §7.0.

*Cosa va specificato per chiuderlo:* un read-out umano con rubrica pre-registrata e cecità sul
braccio; e il gate riformulato come **congiunzione** («invariante macchina **e** preferenza umana»)
con la regola di precedenza dichiarata in caso di disaccordo — nello stile che il PRD già usa
altrove e bene: «Se SER e QPS sono in conflitto, **vince SER**» (SM-C2).

### C. **Verdetto distorto dalla baseline non specificata — in entrambe le direzioni** — probabilità: medio-alta

Poiché nessuno ha specificato il re-layout, chi lo costruisce lo costruisce come capita.
- *Verso il falso PASS:* baseline fantoccio (force-directed con seed casuale che rimescola il
  disegno a ogni passo). Contro quella, **qualunque** sistema a patch sembra «chiaramente
  migliore», e il gate passa senza aver dimostrato niente.
- *Verso il falso FAIL:* baseline forte (layout ortogonale deterministico su ordinamento canonico)
  su un corpus di circuiti piccoli — cioè esattamente il dominio di §7.1 — resta quasi stabile
  sulle riduzioni serie/parallelo. Nessun vantaggio misurabile, e un prodotto potenzialmente valido
  viene ucciso su un campione senza potere statistico.

*Cosa va specificato per chiuderlo:* algoritmo e configurazione della baseline nominati e
congelati **prima** di misurare; corpus stratificato per includere i casi in cui l'ipotesi predice
una differenza (reti oltre una soglia di nodi, catene oltre una soglia di passi); e la
constatazione, da mettere per iscritto, che tre trasformazioni su reti resistive **potrebbero non
bastare** — al contrario di quanto §7.0 afferma senza prova.

### D. **Nessun verdetto: il gate non viene mai eseguito** — probabilità: media, ma è l'esito modale se nulla cambia

§16.0 blocca la dichiarazione di superamento fino a soglie owner-locked senza owner-data;
l'`[ASSUMPTION]` di §7.0 dice che se la valutazione risultasse soggettiva «il gate va reso
misurabile prima di eseguirlo», senza assegnare a nessuno il compito di renderlo misurabile. Esito
prevedibile: il kernel si costruisce, il gate non si esegue formalmente, il catalogo si espande
sotto pressione (Millman e Thévenin sono già elencati come «Prime trasformazioni» nel piano master
§24), e il kill criterion diventa decorazione. L'unico presidio è SM-C5, che è una counter-metric —
un'osservazione, non un blocco.

*Cosa va specificato per chiuderlo:* trasformare «soglie fissate + baseline specificata + corpus
definito» in una **precondizione che blocca l'inizio della costruzione di Gate A**, non solo la sua
dichiarazione di superamento; e dare a SM-C5 un enforcement (es. un test che fallisce se il
catalogo supera tre voci senza il record di decisione di FR-43).

### E. **Falso FAIL per non-determinismo del renderer** — probabilità: bassa, e il PRD lo vede già

SM-17 (VDR) è esattamente questo pericolo, correttamente identificato. Residuo: VDR non ha soglia e
non ha **ordinamento** — VDR va verificata *prima* che VCER/SEC significhino qualcosa, altrimenti
si misura rumore. Un'ordinanza di una riga chiude il residuo.

---

## 4. Rilievo trasversale: il gate lega due decisioni di peso diversissimo

La frase del callout produce **due** conseguenze da una sola misura:

1. «il catalogo delle trasformazioni **non si espande**» — guardrail di ingegneria, economico,
   reversibile;
2. «il prodotto **non ha una ragione di esistere**» — conclusione che chiude l'azienda,
   irreversibile.

Una sola soglia per entrambe è mal posta in ogni caso: se la si tara sul kill, il guardrail non
scatta mai; se la si tara sul guardrail, si uccide il prodotto per un risultato tecnico
intermedio. **Vanno separate**: una soglia «non espandere ancora, itera sul layout engine» e una
soglia distinta, più alta e con più evidenza, «ferma tutto». Il PRD sa fare questo genere di
distinzione — SM-1 la fa già («sopra il 2% e non in discesa, il prodotto si ferma», distinto dal
target < 0,5%). Qui non è stata fatta.

---

## 5. Findings per severità

### 🔴 Blocker — impediscono al gate di produrre un verdetto accettabile

- **B1. Il braccio baseline «re-layout completo» non è in scope e non è specificato.** §7.1 non lo
  costruisce; FR-37 vieta il comportamento che lo costituisce («Il sistema **non** ricalcola il
  layout globale a ogni passo»). Senza secondo braccio, la frase comparativa del gate non è
  eseguibile.
- **B2. SM-14 (VCER) non può portare il kill criterion pur essendo designata a portarlo.** È a un
  braccio solo (indefinita sul re-layout), auto-dichiarata (nessun requisito di massimalità su
  `preserve` → `preserve = {}` dà VCER = 0), e di conformità a FR-38, non di confronto.
- **B3. «Chiaramente migliore» non ha operatore, soglia, campione né decisore** — e le soglie sono
  owner-locked (§16.0) senza owner nominato, senza data, e con divieto esplicito a valle di
  proporle. Il gate non è dichiarabile passato né fallito da nessuno, oggi.

### 🟠 Major — il verdetto sarebbe formalmente producibile ma non significativo

- **M1. Buco di validità di costrutto.** Il gate conclude su un valore («il prodotto non ha ragione
  di esistere») misurando grandezze interne alla macchina, e §7.0 rimuove per decisione ogni umano
  dal circuito di misura senza notare che così rimuove anche lo strumento.
- **M2. Il dominio scelto minimizza l'effetto da rilevare.** Reti resistive DC + serie/parallelo/
  partitore sono il regime in cui anche un buon re-layout globale resta stabile. La tesi «bastano
  tre trasformazioni per saperlo» (§7.0) è affermata e mai argomentata.
- **M3. SM-15 (SEC) è la vera candidata a portare il gate ed è la metrica meno definita del
  documento**: «Costo di ri-layout per passo», senza unità, senza direzione, senza soglia.
- **M4. Nessun requisito di massimalità su `preserve`**, che è la precondizione perché VCER (e ogni
  metrica derivata) sia interpretabile.
- **M5. Nessun corpus di Gate A.** FR-34 dichiara di coprire «solver, Trasformazioni, Verifica»:
  la dimensione layout non è nell'elenco.
- **M6. Le due conseguenze del gate — non espandere il catalogo, e fermare il prodotto — condividono
  un'unica soglia** (§4 di questa review).

### 🟡 Medium

- **Md1. Scope surplus rispetto al verdetto:** Marcatura di provenienza + export PDF (l'art. 50
  presuppone immissione sul mercato, che §7.0 esclude — l'SVG semantico invece serve, per FR-41);
  editor del circuito; controlli «bilancio di potenza» e «sanità fisica» della Verifica; RRC. Se
  Gate A fallisce, è lavoro buttato che non ha contribuito al verdetto.
- **Md2. FR-43 richiede una «decisione registrata» senza specificarne contenuto, firmatario,
  pacchetto di evidenze o gestione dell'esito ambiguo.**
- **Md3. SM-C5 è l'unico presidio contro l'espansione del catalogo ed è una counter-metric**, cioè
  un'osservazione, non un blocco.
- **Md4. Divergenza di acronimi col piano master, verificata alla fonte.** Master §22: TVR =
  *Transformation Validity Rate*, SEC = *Step Evidence Coverage*, RRC = *Render Roundtrip
  Correctness*, VDR = *Visual Derivation completion rate*. PRD §8: TVR = *Topology Violation Rate*,
  SEC = *Steps per Edit Cost*, RRC = *Refusal Reason Coverage*, VDR = *Visual Determinism Rate*.
  Quattro sigle su sette significano cose diverse nei due documenti che il PRD dichiara come propri
  upstream. Conseguenza pratica: il rinvio di §16.0 a «§27.6 del piano master» è instabile — §27.6
  blocca «Soglie **VVDR/SER/RRC**», e RRC lì è un'altra metrica.
- **Md5. §16.0 estende l'owner-lock oltre §27.6 del master** (che blocca VVDR/SER/RRC) fino a
  includere **VCER**, cioè la soglia che decide il gate. L'estensione può essere voluta; l'effetto
  è che il numero decisivo è l'unico che nessuno a valle può scrivere.
- **Md6. Manca l'ordinamento fra le verifiche:** SM-17 (VDR) va soddisfatta *prima* che VCER, SEC e
  il round-trip di FR-41 siano interpretabili. Il PRD identifica il pericolo ma non fissa la
  sequenza.

### ✅ Adeguato — non ci sono rilievi, e va riconosciuto

- FR-38: invariante formale con «la violazione è un errore, non una tolleranza».
- FR-41: confronto **di grafi, non di pixel e non di stringhe**; «Nessun VLM partecipa alla
  certificazione della topologia»; esito tipizzato invece di avviso. Requisito falsificabile
  esemplare.
- FR-40: giustificazione onesta e corretta del ProofGraph anticipato (migrazione dati vs refactor).
- SM-17: identificazione di un pericolo non ovvio (renderer non deterministico → round-trip non
  falsificabile).
- SM-C5: contatore ben mirato al gaming più naturale del kill criterion.
- §16.0: distinzione corretta fra bloccare la costruzione e bloccare la dichiarazione.
- §7.0 `[ASSUMPTION]`: il documento nomina da solo il rischio che questa review conferma. È il
  segno di un PRD scritto in buona fede — e la ragione per cui i rilievi qui sopra sono chiudibili
  con lavoro di specifica, non con un ripensamento della tesi.

---

## 6. La forma minima che renderebbe il gate falsificabile

Non è una riprogettazione: sono sette righe di specifica che oggi mancano.

1. **Baseline nominata e congelata:** algoritmo di re-layout completo, configurazione, seed,
   renderer identico al braccio continuità.
2. **Corpus di Gate A:** N circuiti, stratificati per numero di nodi e lunghezza della catena,
   con split held-out, generati prima di guardare qualunque risultato.
3. **Metrica comparativa primaria:** SEC definita in un'unità calcolabile su **entrambi** i bracci
   (proposta: frazione di elementi con coordinate mutate per passo, più spostamento mediano), non
   VCER.
4. **VCER declassata a controllo di conformità di FR-38**, con `preserve` massimale verificato da
   un checker indipendente dal patch dichiarato.
5. **Regola di decisione:** direzione, delta minimo, percentile, e cosa fare in caso di risultato
   fra le due soglie.
6. **Due soglie separate:** «non espandere il catalogo» e «fermare il prodotto».
7. **Read-out umano** con rubrica pre-registrata, cecità sul braccio e ordine randomizzato, sul
   pool già disponibile in §17 — e regola di precedenza dichiarata fra esito macchina ed esito
   umano.

Finché i punti 1, 3 e 5 mancano, la clausola condizionale di §7.0 è attiva: **il gate va reso
misurabile prima di eseguirlo.**
