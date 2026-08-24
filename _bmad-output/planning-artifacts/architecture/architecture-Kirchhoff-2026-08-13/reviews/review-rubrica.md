---
lente: rubric walker — checklist «good spine» del Reviewer Gate
file: ARCHITECTURE-SPINE.md (974 righe, 35 AD, version 2)
rubrica: bmad-architecture/references/reviewer-gate.md
data: 2026-08-15
---

# Review di rubrica — Architecture Spine v2 (Kirchhoff)

## Verdetto

Lo spine è **solido su ogni dimensione di dominio che ha deciso e cieco sull'intero involucro
operativo**: esecuzione asincrona, CI come sostrato di enforcement, backup e ripristino, migrazioni
di schema e gestione dei segreti non sono differiti né dichiarati domanda aperta — **non compaiono**,
e quattro di loro entrano in collisione diretta con un AD esistente; a questo si aggiungono due
difetti sui due AD scritti stamattina (AD-34 e AD-35, che nessuna delle sette lenti ha letto) e tre
contraddizioni di conteggio, la più pericolosa delle quali sta nel preambolo.

## Metodo e delimitazione

Ho letto lo spine per intero, il memlog (44 voci) e i titoli di rilievo delle sette review già
rientrate. **Non ripeto** ciò che avversario (C1–C7), confini (R1–R5), continuità visuale (CV1–CV7),
invarianti (R1–R6), privacy (P1–P9), testabilità (T1–T15) e veridicità (V1–V5) hanno già trovato.
In particolare **non sono miei e non li ri-espongo**: la stalezza dell'ERD (T6), la mappa
`Capability → Architecture` ferma a FR-35 (confini:254, veridicità:166, invarianti:103),
l'ordine dei layer che non implica la non-occlusione (CV3), «il vincolo è nel tipo» (CV5), i cinque
recinti che non coprono il braccio 0 (CV5, memlog:36), lo *Structural Seed* v1 (confini R4, già
riscritto), l'insieme chiuso di `Refusal` (confini R3, già esteso).

Dove un mio rilievo nasce come **residuo di una correzione già applicata** da un'altra lente, lo
dichiaro: non è un secondo avvistamento dello stesso difetto, è ciò che la toppa ha lasciato dietro.

Ogni rilievo è verificato di persona sul file e porta `riga`. Nessuna soglia numerica è proposta:
VVDR, RRC, TVR, VCER, SEC e VDR restano owner-locked. Gli ID `AD-1…AD-35` non si rinumerano; dove
serve un AD nuovo il primo libero è **AD-36**.

---

## A. Ampiezza dimensionale — il punto centrale

La rubrica chiede che **ogni dimensione che l'altitudine possiede** sia *decisa*, *differita* o
*domanda aperta*, e dichiara esplicitamente che una dimensione lasciata in silenzio è il
fallimento — «especially the operational/environmental envelope a domain-focused draft skips».
Questo spine è esattamente il caso che la rubrica descrive.

### A.1 Quadro completo

| # | Dimensione | Stato | Dove |
|---|---|---|---|
| 1 | Confini di modulo e regola di dipendenza | decisa | AD-21:441, AD-27:606 |
| 2 | Rappresentazioni e modello dati | decisa | AD-21:441, AD-8:230-238 |
| 3 | Contratto fra stadi | decisa | AD-1:86, AD-19:396 |
| 4 | Modello d'errore e rifiuto | decisa | AD-13:311, AD-19:396 |
| 5 | Identità, tenancy, autorizzazione | decisa | AD-20:428, AD-14:321 |
| 6 | Fatturazione e idempotenza | decisa (solo operazioni addebitabili) | AD-7:202 |
| 7 | Contratto esterno pubblico | decisa | AD-16:351, AD-27:606, AD-28:617 |
| 8 | Determinismo e purezza | decisa (firma incompleta → **RB-9**) | AD-2:99, AD-17:365, AD-35:716 |
| 9 | Osservabilità e metriche di prodotto | decisa (obbligo non assolto → **RB-8**) | AD-34:690 |
| 10 | Gate di verifica | decisa | AD-5:160, AD-31:649, AD-32:667, AD-33:678 |
| 11 | Licenze e corpus | decisa | AD-25:556 |
| 12 | Esperimento e rendering dei bracci | decisa | AD-26:580, AD-11:273, AD-23:509 |
| 13 | Versioni pinnate dello stack | **differita, con condizione** ✔ | 951-953 |
| 14 | Algoritmo di piazzamento del braccio 0 | **differita, con condizione** ✔ | 962-963 |
| 15 | Topologia di deploy e ambienti | differita, **condizione fuori bersaglio** → **RB-13** | 968-971 |
| 16 | Caching dei Pass di estrazione | differita, **premessa falsa** → **RB-12** | 964-965 |
| 17 | Percorso C (ngspice) | differita, senza condizione → **RB-14** | 954-956 |
| 18 | Schema campo-per-campo dell'IR | differita, senza condizione → **RB-14** | 966-967 |
| 19 | Localizzazione | differita, senza condizione → **RB-14** | 972-973 |
| 20 | **Esecuzione asincrona, code, worker** | **SILENZIO** | **RB-1** |
| 21 | **CI come sostrato di enforcement** | **SILENZIO** | **RB-2** |
| 22 | **Backup e ripristino** | **SILENZIO** | **RB-3** |
| 23 | **Migrazioni di schema ed evoluzione di `ir_version`** | **SILENZIO** | **RB-4** |
| 24 | **Gestione dei segreti e delle credenziali** | **SILENZIO** | **RB-5** |
| 25 | **Esercizio: monitoraggio, allarmi, incidenti** | **SILENZIO** | **RB-6** |
| 26 | **Residenza dei dati (regione UE)** | **seed, mai invariante** | **RB-7** |
| 27 | **Port per pagamenti e per la catena LaTeX** | **SILENZIO** (benché il paradigma li nomini) | **RB-11** |
| 28 | Tetti di costo, quota, rate limiting | parziale: pavimento sì, tetto e proprietario no | **RB-24** |

Verifica meccanica a supporto (occorrenze nell'intero file): `backup` 0 · `ripristino` 0 ·
`disaster` 0 · `migration` 0 · `segreto/secret` 0 · `rotazione` 0 · `staging` 0 · `runbook` 0 ·
`SLO` 0 · `monitor` 0 · `allarme/alert` 0 · `budget` 0 · `rate limit` 0 · `worker` 0 · `coda` 0 ·
`asincrono` 0 · `timeout` 0. `CI` compare **tre volte** (530, 730, 731) e sempre come *destinatario*
di un obbligo, mai come oggetto di una decisione.

---

### RB-1 🔴 — L'esecuzione asincrona è nello Stack, nel diagramma e in nessun AD

**File:riga.** Stack:772 (`Redis + RQ`) · diagramma degli stadi:825-826 (`ask → val`, sospensione) ·
AD-6:197-199 (`resume_ref`, TTL 15 minuti) · AD-12:307-308 (`K ≥ 3` Pass) · AD-24:532 (percezione
«binario parallelo») · AD-7:204-210 · AD-34:700-703.

Lo Stack introduce una coda di lavoro. La pipeline ha una sospensione con ripresa, un'estrazione a
*K* Pass e un binario di percezione dichiarato parallelo. Nessun AD dice **cosa gira dentro la
richiesta e cosa dentro un worker**, quale semantica di consegna la coda ha, se un lavoro può essere
ri-eseguito, con quale politica di ritentativo e di scadenza, né se un worker è soggetto agli stessi
recinti di `check_boundaries.py` (AD-21:463-478 parla di import, e un worker importa il dominio come
chiunque altro).

**Le due unità.** Una esegue l'estrazione dentro la richiesta HTTP; l'altra la accoda su RQ. Sono
**entrambe conformi** ad AD-6 — «nessuno stato in memoria fra richieste» è soddisfatto in tutti e
due i casi. Il costo della divergenza non è di stile:

- l'idempotenza di AD-7 copre **solo** «ogni operazione addebitabile». Una consegna at-least-once
  ri-esegue anche gli stadi non addebitabili, fra cui `publish()` e le emissioni verso
  l'`ObservationPort`. Le metriche di §8 si contano due volte su un ritentativo, e AD-34(b):708
  ordina a `eval/` di leggere lo **stesso** canale — quindi l'harness eredita il doppio conteggio;
- `K ≥ 3` è «un limite inferiore imposto dal codice» (AD-12:308): se i Pass sono task indipendenti,
  un fallimento parziale produce un consenso su due Pass che nessun controllo intercetta, perché il
  limite è imposto alla configurazione, non al numero di Pass **riusciti**;
- il `resume_ref` è monouso con TTL di 15 minuti (AD-6:198-199); un lavoro in coda che supera quel
  tempo non ha comportamento definito.

**Forma minima della correzione.** Un **AD-36** che fissi tre cose e nient'altro: (a) il confine fra
lavoro sincrono e differito è dichiarato per stadio, non scelto dall'implementatore; (b) la consegna
è assunta **at-least-once**, quindi ogni stadio riesumabile è idempotente sul proprio effetto — non
solo quelli addebitabili — e l'emissione verso l'`ObservationPort` porta una chiave che rende il
doppio conteggio riconoscibile; (c) `K` è contato sui Pass riusciti. In alternativa, se la coda è
prematura, **ritirare `Redis + RQ` dallo Stack**: uno stack che nomina un'infrastruttura che nessun
AD governa è un invito a inventarne la semantica.

---

### RB-2 🔴 — Otto Rule delegano l'applicazione alla CI, e la CI non è decisa da nessuna

**File:riga.** AD-9:252 · AD-11:292 e 296-297 · AD-15:346-349 · AD-21:463-478 · AD-23:526-530 ·
AD-26:601-603 · AD-27:611 · AD-31:658-663 · AD-35:728-731.

Il conto è verificabile: almeno otto Rule affidano la propria applicazione a «un test di conformità
che fallisce», «un test di contratto», «un test di architettura», «un controllo che fallisce se una
famiglia manca», «il controllo `ast` di `check_boundaries.py`», «una delle famiglie obbligatorie».
AD-35:731 arriva a dire che il difetto che previene è **«un difetto che solo la CI può vedere»**.

E poi: nessun AD, nessuna riga delle *Consistency Conventions* e nessuna voce di *Deferred* dice che
la CI esiste, che è bloccante sul merge, chi la possiede, o cosa succede quando un controllo è rosso.
Il paradigma apre (53-56) dichiarando che la separazione «non vive nella disciplina di chi scrive»;
l'intero apparato di enforcement dello spine vive invece nella disciplina di chi configura una CI che
il documento non nomina. AD-21:476-478 lo dice quasi per intero — «non è un errore di compilazione…
è il controllo `ast` a essere l'unica difesa reale» — e si ferma un passo prima della conclusione:
se quel controllo non gira **obbligatoriamente**, non è una difesa.

**Forma minima della correzione.** Una riga in *Consistency Conventions* o un **AD-36** breve: i
controlli che gli AD nominano sono **bloccanti** e girano su ogni modifica; un controllo disattivato,
saltato o marcato «atteso in errore» è una modifica dello spine, non di un modulo — la stessa forma
che AD-19:404 usa già per le cause di `Refusal`. Senza questa riga, AD-35 in particolare non ha
alcun meccanismo: è l'unico AD il cui fallimento non produce mai un `Refusal`.

---

### RB-3 🔴 — Backup e ripristino: zero occorrenze, e sono in collisione con AD-9 e AD-11

**File:riga.** AD-9:245-252 · AD-11:296-297 · Stack:771 (`PostgreSQL (Supabase, regione UE)`) ·
diagramma:800/804.

AD-9 fonda la conformità sulla lifecycle policy del provider: «le immagini sorgente stanno in un
bucket con lifecycle policy a 72 ore lato provider… Un test di conformità fallisce se trova un
oggetto oltre TTL». AD-11:296-297 replica la stessa figura per il `ParticipantToken`: cancellazione
«verificata come il TTL delle immagini (AD-9): da un controllo che fallisce, non da una procedura».

Un backup è **precisamente il meccanismo che conserva ciò che questi due AD ordinano di distruggere**,
e il controllo che entrambi invocano guarda lo stato **corrente**: su un bucket con versioning
attivo la policy scade le versioni correnti e lascia le non correnti; su Postgres gestito il
point-in-time restore conserva le righe cancellate per la finestra di retention del provider, che è
un default, non una scelta di questo documento.

**Le due unità.** Una abilita il ripristino a un punto nel tempo e il versioning sull'object storage,
perché è il default sensato e perché nessuna regola lo vieta; l'altra li lascia spenti per non
violare AD-9. Sono entrambe conformi, e la prima porta il prodotto fuori conformità **superando il
test di conformità**, che è il modo più costoso di fallire.

**Forma minima della correzione.** Estendere AD-9 di una clausola — la finestra di ritenzione di
ogni copia (backup, snapshot, versione non corrente, replica) è **parte del TTL, non un'eccezione**,
e il controllo di conformità interroga anche le copie — oppure un **AD-36** su ritenzione e
ripristino che nomini le tre superfici (immagini, `ParticipantToken`, e i record dell'`ObservationPort`
di AD-34, oggi anch'essi senza ritenzione: **RB-10**). La finestra numerica è dell'owner: qui serve
solo che l'insieme delle copie sia **dentro** il perimetro della regola, non fuori.

---

### RB-4 🔴 — Le migrazioni di schema sono il proprietario mancante di AD-8

**File:riga.** AD-8:219 («Enforcement a livello di permessi DB, non di convenzione») e tabella
230-238 · AD-1:91-93 (`ir_version` semantica) · convenzione *Mutazione di stato*:745 (persistenza
append-only) · AD-29:632 (`Prevents: una migrazione`).

AD-8 è l'unico AD dello spine la cui applicazione è **a permessi di database**: ogni entità ha un
solo scrittore, e il permesso lo impone. Uno strumento di migrazione, per definizione, scrive tutte
le tabelle. È l'unica eccezione legittima alla regola più rigidamente applicata del documento, e non
è nominata: né nella tabella dei proprietari, né altrove.

Attorno a quel vuoto ce ne sono altri due, tutti nella stessa dimensione:

1. `CircuitIR` porta una `ir_version` **semantica** (AD-1:91-93) e la persistenza è append-only
   (:745). Quindi righe di versioni diverse coesistono per progetto, e nessuna regola dice come un
   lettore tratta una versione che non conosce — se rifiuta, se converte, e in tal caso chi possiede
   il convertitore. Due unità: una fa back-fill in loco (violando l'append-only ma restando conforme
   ad AD-8 se il permesso glielo consente), l'altra scrive una nuova versione;
2. AD-29:629-637 sceglie il grafo **proprio per evitare una migrazione** del formato persistito. È
   l'unico punto dello spine che ragioni sull'evoluzione dello schema, e ragiona su un caso solo.

**Forma minima della correzione.** Due righe. In AD-8, una clausola che nomini la migrazione come
l'**unica** scrittura fuori dal proprietario, subordinata a un percorso dichiarato e mai eseguita dal
codice applicativo a runtime. In AD-1 o nelle convenzioni, la regola di lettura di una `ir_version`
sconosciuta: rifiuto tipizzato (una causa di AD-19) e non interpretazione ottimistica.

---

### RB-5 🔴 — Nessuna regola sui segreti, e AD-6 e AD-14 ne dipendono entrambi

**File:riga.** AD-6:198 (`identificatore opaco **firmato HMAC**`) · AD-3:131-132 («almeno due
adapter registrati; la selezione è configurazione») · AD-14:325-326 · Stack:771 · convenzione
*Configurazione*:746 · diagramma:802 (`Merchant of Record`).

Tre dipendenze da materiale segreto, nessuna regola:

- **AD-6.** L'intera difesa dall'IDOR che AD-6 nomina a :199-200 poggia su una chiave HMAC di cui
  nessuna riga dice dove viva, chi la legga, se sia per ambiente e cosa accada alla rotazione. La
  rotazione, peraltro, è a costo quasi nullo qui (TTL 15 minuti): è un'omissione gratuita.
- **AD-14.** «Row-level security… Un filtro applicativo non sostituisce la policy». Vero, e vale
  finché l'applicazione **non si connette con un ruolo che aggira RLS**. Su Postgres gestito quel
  ruolo esiste ed è il percorso di minor resistenza per qualunque operazione lato server. Due unità:
  una si connette col ruolo autenticato e la RLS la governa, l'altra col ruolo di servizio «perché
  il backend deve poter leggere tutto». La seconda **rispetta ogni parola di AD-14** e la annulla.
  Questo è il difetto reale di AD-14, ed è un difetto di segreti, non di policy.
- **AD-3.** «Almeno due adapter registrati» significa almeno due credenziali di provider, più quelle
  del Merchant of Record, più quelle dello storage. La convenzione :746 dice solo che la
  configurazione arriva «da ambiente, validata all'avvio».

**Forma minima della correzione.** Un **AD-36** o una riga di convenzione: nessun segreto nel
repository né nell'immagine; ogni segreto ha un proprietario e un ambito d'ambiente dichiarati; e —
la sola clausola che chiude un buco vero — **l'applicazione non si connette mai al database con un
ruolo che aggira la row-level security**, con un controllo che lo verifica, altrimenti AD-14 è una
policy che nessuno attraversa.

---

### RB-6 🟠 — L'esercizio non esiste, e AD-34 spiega perché nessuno se ne accorgerà

**File:riga.** AD-34:710-712 · convenzione *Log e telemetria*:747.

`monitor` 0, `allarme` 0, `SLO` 0, `incidente` 0, `runbook` 0. Nulla dice chi si accorge che il
prodotto è rotto in produzione, e questa non è la stessa dimensione che AD-34 copre: AD-34 istituisce
un canale di **misura di prodotto** e lo dichiara esplicitamente irrilevante all'esercizio —
«la sua perdita non cambia alcun risultato — cambia solo cosa si può sapere» (:711-712). È una
clausola giusta per il determinismo e devastante per l'esercizio: significa che **un canale morto non
rompe nulla**, quindi nessuno lo scopre, e la prima persona ad accorgersene è chi calcola le metriche
di Gate A su una finestra vuota.

**Forma minima della correzione.** Non serve un apparato di osservabilità nello spine — è altitudine
sbagliata. Serve **una voce di *Deferred* con condizione di revisione** («prima della prima
esecuzione di Gate A» è la condizione naturale, dato che Gate A consuma il canale) e, dentro AD-34,
una riga che renda la **vitalità del canale** verificabile: un canale che non riceve record per uno
stadio che è stato eseguito è un difetto, non un silenzio.

---

### RB-7 🟠 — La residenza UE è seed in tre punti e invariante in nessuno

**File:riga.** Stack:771 · diagramma:800 (`Object storage UE`) e :804 (`PostgreSQL UE`) ·
Deferred:968 (`Un solo VPS UE più object storage UE`) — e **zero AD**.

«UE» compare quattro volte, sempre in una tabella di stack, in un diagramma o in una voce differita,
cioè nei tre luoghi che questo documento tratta come sostituibili. Nessun `Binds`, nessuna `Rule`. Al
tempo stesso AD-11:277-278 costruisce un'intera regola attorno all'Allegato III dell'AI Act e AD-9
costruisce la conformità sulla policy del provider di storage: il documento tratta la conformità come
un invariante e la geografia che la rende possibile come una preferenza.

**Le due unità.** Una crea il bucket nella regione di default dell'SDK; l'altra in UE. Nessuna delle
due viola una riga di questo spine.

**Forma minima della correzione.** Una clausola in AD-9 (che già possiede lo storage) e una in AD-14
(che già possiede il database): la regione è vincolata e verificata da un controllo, come il TTL.
Oppure una dichiarazione esplicita che la residenza è seed e la decisione è dell'owner — accettabile,
purché **detta**, perché oggi il lettore non può distinguere fra le due letture.

---

## B. Invarianti contro seed

Ho applicato a tutti e 35 gli AD il test «due unità un livello sotto potrebbero scegliere in modo
incompatibile». **Trentaquattro lo superano.** Non ho trovato AD che fissino decisioni ovvie prive di
compromesso: anche i più semplici — AD-17 (un solo orologio), AD-13 (`Refusal` ≠ `Failure`) — chiudono
una divergenza reale a costo nullo, ed è il rapporto giusto.

Un solo caso di **seed travestito da invariante**:

### RB-20 🟡 — AD-16 incapsula costanti di protocollo dentro un invariante, e le due date non si parlano

**File:riga.** AD-16:356-363 · Stack:770.

La `Rule` di AD-16 contiene, oltre all'invariante, quattro costanti che appartengono a una specifica
esterna e che l'SDK possiede comunque: lo schema `ui://`, la stringa esatta di `mimeType`, il campo
`_meta.ui.resourceUri` e il trasporto JSON-RPC su postMessage. La parte che regge il test della
rubrica è un'altra ed è ottima: versione dichiarata, deprecazione con sovrapposizione, **`content` e
`structuredContent` entrambi presenti e non intercambiabili**, nessuno stato locale nel pannello —
quest'ultima chiude una divergenza vera (due unità che restituiscono solo `structuredContent`).

In più le due date non sono riconciliate: :363 cita `specification/2026-01-26/apps.mdx`, mentre
Stack:770 dà «revisione protocollo 2026-07-28». Possono essere legittimamente diverse (estensione
*apps* contro revisione del protocollo core), ma il documento non lo dice, e chi implementa deve
indovinare quale delle due governa.

**Forma minima della correzione.** Lasciare in AD-16 l'invariante; spostare le quattro costanti nello
*Stack* o nelle convenzioni, dove un aggiornamento di revisione non richiede di emendare un AD. E una
riga che dichiari la relazione fra le due date. *(La sostanza del protocollo la lascio alla lente MCP;
qui il rilievo è di collocazione e di conteggio delle fonti.)*

---

## C. Forma — `Binds` / `Prevents` / `Rule`

**Struttura: piena.** 35 AD, 35 `Binds`, 35 `Prevents`, 35 `Rule` (verificato meccanicamente).
Nessun segnaposto, nessun ID duplicato.

Due `Prevents` non nominano una divergenza concreta:

### RB-21 ⚪ — AD-18: il `Prevents` è storico per ammissione del documento stesso

**File:riga.** AD-18:377-381, con la nota a :390-394 che dichiara «la premessa è **storica**».

Il `Prevents` argomenta su `(IR, Drawing)`, che AD-2 non produce più. Il documento lo sa e lo scrive.
Il difetto vivo che AD-18 previene esiste ed è **già formulato nella nota**: il dominio potrebbe
continuare a emettere «posizioni logiche», nascendo una quinta rappresentazione con due autorità
sulla posizione.

**Forma minima della correzione.** Promuovere quella frase nel `Prevents` e retrocedere la formulazione
attuale a nota storica — l'operazione inversa di quella fatta oggi. Costo: due righe scambiate.

### RB-22 ⚪ — AD-34: il `Prevents` nomina una lacuna di capacità, non una divergenza

**File:riga.** AD-34:693-699.

«Prevents: che §8 sia misurabile solo a mano» descrive ciò che il prodotto **non potrebbe fare**, non
ciò su cui **due unità sceglierebbero in modo incompatibile**. La divergenza esiste ed è ovvia una
volta detta — due stadi che inventano due forme di record, e la metrica che li attraversa entrambi
non è sommabile — e non è scritta.

**Forma minima della correzione.** Una frase nel `Prevents`. AD-34 è nuovo di stamattina: è il momento
più economico per scriverla.

---

## D. `Deferred` — nomina davvero, o è un cestino?

Sette voci. Due hanno una condizione di revisione esplicita e ben scelta (**versioni pinnate** :951-953,
«prima del primo commit»; **braccio 0** :962-963, «prima di eseguire Gate A»). Una è correttamente
ritirata con motivazione (:957-961). Le altre quattro hanno un problema ciascuna.

### RB-12 🔴 — «Caching dei Pass»: la premessa «nessuna altra unità la percepisce» è falsa tre volte

**File:riga.** Deferred:964-965 · AD-12:307-308 · AD-15:333-335 · AD-34:708.

Il testo differisce la strategia di caching motivandola così: «Ottimizzazione di costo, sotto AD-12.
Nessuna altra unità la percepisce». Tre unità la percepiscono:

1. **AD-12:308** impone `K ≥ 3` come «limite inferiore imposto dal codice». Una cache soddisfa tre
   Pass con una esecuzione: la cascata non ha cambiato *quanti* Pass, e tuttavia l'Accordo — che è
   la grandezza che i *K* Pass servono a produrre — è calcolato una volta e riusato. Il `Prevents`
   di AD-12 («peggiori SER per risparmiare centesimi») è **esattamente** ciò che accade, per una via
   che la sua `Rule` non copre;
2. **AD-15:333** ordina a `eval/` di attraversare «la stessa pipeline attraverso gli stessi port».
   Con una cache calda, l'harness misura l'accordo memorizzato e non quello prodotto: il `Prevents`
   di AD-15 — «che le metriche misurino un percorso che gli utenti non attraversano» — si realizza
   al contrario, ed è **il modo più efficace di ottenere un SER basso e falso**, che è la sua stessa
   frase;
3. **AD-34(b):708** vincola `eval/` a leggere lo stesso canale della produzione, quindi ciò che il
   canale contiene su un colpo di cache cambia la misura.

Questa è la voce che la rubrica cerca quando dice «nothing under Deferred could let two units diverge».

**Forma minima della correzione.** Non decidere il caching — decidere il **suo confine**: la voce
resta differita, con l'aggiunta che nessuna cache può servire un Pass di estrazione ai fini
dell'Accordo né essere calda durante un'esecuzione dell'harness. Due righe, nessun impegno
implementativo.

### RB-13 🟠 — «Topologia di deploy e ambienti»: la condizione di revisione è sullo scaling, il bisogno è già ora

**File:riga.** Deferred:968-971 · AD-15:334-335 · AD-34:708.

La voce differisce insieme due cose diverse — **dove gira** e **quanti ambienti esistono** — e vi
attacca una condizione che riguarda solo la prima: «Da rivedere quando compare il primo cliente
Dipartimento». Ma la seconda è già vincolata **adesso**, da due AD e in due direzioni opposte:

- AD-15:334-335: «La parte trattenuta del gold set è in uno store separato **che la pipeline di
  sviluppo non può leggere**» → esistono almeno due ambienti e un confine di credenziali fra loro;
- AD-34(b):708: `eval/` legge **lo stesso canale della produzione** → l'ambiente che valuta deve
  poter raggiungere l'osservazione di produzione.

Insieme, i due descrivono una topologia di ambienti non banale — uno che non può leggere l'held-out,
uno che deve leggere la telemetria di produzione — che nessuna dimensione del documento decide.

**Forma minima della correzione.** Separare la voce in due. La topologia di deploy resta differita
con la condizione attuale, che è buona. Gli **ambienti** escono dal *Deferred*: sono già vincolati e
il vincolo va scritto dove sta il resto, cioè una clausola in AD-15 che nomini il confine di
credenziali che la sua stessa frase presuppone.

### RB-14 🟡 — Tre voci differite senza condizione di revisione

**File:riga.** Percorso C :954-956 · Schema completo dell'IR :966-967 · Localizzazione :972-973.

Nessuna delle tre dice **quando** si riapre. Percorso C argomenta l'innocuità («aggiungerlo dopo non
cambierà il gate») — buon argomento, ma non è una condizione. Lo schema dell'IR è assegnato al codice
proprio mentre AD-22:500-507 impone su quello schema proprietà strutturali (`node_mapping` totale e
iniettiva, `id_{k+1}(x) = id_k(x)`), quindi la parte differita e la parte decisa si toccano.
La rubrica è netta: «un elemento differito senza condizione di revisione è un elemento dimenticato».

**Forma minima della correzione.** Una condizione per ciascuna, anche grossolana — «al primo esercizio
che il Percorso A non chiude», «alla prima storia che tocca `domain/ir`», «al primo tenant non
italofono». Il valore è nel fatto che qualcuno debba dire di no.

---

## E. Diagrammi

**Cinque blocchi mermaid, tutti sintatticamente validi** (70-79 dipendenze · 784-815 contenitori ·
819-835 stadi · 842-865 percezione · 874-888 ERD): nessun errore di sintassi, nessun nodo orfano,
entità HTML correttamente usate a :849.

**Uno porta forma che la prosa non porta**, ed è il migliore del documento: il diagramma della
percezione (842-865). Le due frecce che il testo commenta a :867-870 — `CONF → TRUST` come unico
ingresso, `kern ⇢ ARD` a senso unico — e soprattutto `STRUCT → TRUST`, che rende visibile in un
colpo d'occhio che l'esperimento di Gate A **non parte dalla percezione**, sono form che nessun
paragrafo restituirebbe con la stessa immediatezza. Va tenuto.

**Tre portano la forma della v1, e quindi non duplicano la prosa: la contraddicono.**

### RB-18 🟠 — Il diagramma delle dipendenze è dichiarato invariante e codifica due recinti su sei

**File:riga.** 68 («Regola di dipendenza, che è essa stessa **un invariante**») · 70-79 ·
AD-21:465-473 · AD-26:601-603.

Il diagramma ha cinque nodi (`api`, `eval`, `pipeline`, `domain`, `ports`, `adapters`) e due frecce
vietate: `domain ↛ adapters`, `domain ↛ ports`. I recinti che gli AD ordinano sono sei, e quattro
non sono rappresentabili in questo grafo perché **i nodi non esistono**: `render/`, `perception/`,
`corpus/`, `experiment/` non compaiono. L'albero del paradigma appena sopra (59-66) ha lo stesso
difetto: sei directory, mentre l'*Albero sorgente* :893-922 ne ha dieci. L'elenco dei port dentro
quello stesso albero **è stato allineato oggi** (memlog:43) e le directory no: è il residuo di quella
correzione.

Chi implementa `check_boundaries.py` guardando la figura che il documento chiama «invariante»
costruisce due regole invece di sei.

**Forma minima della correzione.** Aggiungere i quattro nodi e le quattro frecce vietate al diagramma
70-79 e le quattro directory all'albero 59-66. La tabella dei recinti in AD-21:468-473 è già
corretta: qui si tratta solo di far dire alla figura ciò che la tabella dice.

### RB-17 🟠 — Il diagramma degli stadi dice «Verifica 5 controlli»; AD-5 ne enumera otto

**File:riga.** 830 (`ver[Verifica 5 controlli]`) · 832 (`pub{Passano tutti?}`) · AD-5:185-190.

È il residuo della correzione di veridicità V1: AD-5 è passato a `publish(proof_graph)` con otto
controlli su **ogni nodo**, e il diagramma è rimasto alla v1 — un `ver` unico a valle di `sa`/`sb`,
applicato una sola volta, con il conteggio vecchio. Manca anche `domain/transform/check`, lo stadio
che AD-19:424-426 dichiara **nuovo** ed emettitore di tre cause, e mancano `render/roundtrip`,
`domain/proof` e `domain/truthfulness`. Nota: `verify/ # i cinque controlli` a :900 è invece
**corretto** — `verify/` possiede i cinque originari, mentre incidenza, round-trip e veridicità
vivono altrove. Il difetto è solo nel diagramma, dove il nodo *è* il gate.

**Forma minima della correzione.** Correggere l'etichetta e rendere `publish` un nodo attraversato
per nodo del `ProofGraph`, oppure — se il diagramma vuole restare una vista d'insieme —
etichettarlo esplicitamente come **vista della v1 conservata per orientamento**, che è ciò che AD-18
fa già col proprio `Prevents`. La cosa da non lasciare è un conteggio.

### RB-19 🟡 — Il diagramma dei contenitori è v1 e usa il termine che le convenzioni vietano

**File:riga.** 784-815, in particolare :796 (`dom[Dominio: IR, Trasformazioni, Verifica]`) ·
convenzione *Le quattro rappresentazioni*:750.

Non contiene `render/` — cioè metà del Visual Proof Kernel secondo la nota :929-932 — né
`perception/`, `corpus/`, `experiment/`, né alcun destinatario dell'`ObservationPort`. E usa «IR»
nudo, che :750 dichiara ambiguo dalla v2 e ammette «solo dove `AD-1…AD-20` lo usavano».

**Forma minima della correzione.** Aggiungere i contenitori mancanti e sostituire «IR» con
`CircuitIR`. *(La stalezza dell'ERD 874-888 è già di T6 e non la ri-espongo.)*

---

## F. Coerenza dei conteggi

Ho verificato ogni numero che il documento dichiara di sé. **Due sono corretti e vale la pena dirlo**,
visto quanti ne sono caduti stanotte: «trenta metriche di §8» (AD-15:338) corrisponde al PRD, che ha
SM-1…SM-21 più SM-C1…SM-C9 = 30; e «venti su trenta senza fonte» (AD-34:696) è coerente con la sintesi
della lente di testabilità. Il conteggio degli AD (35), dei `Binds`/`Prevents`/`Rule` (35/35/35) e
delle rappresentazioni (quattro, ovunque) regge.

Tre non reggono.

### RB-15 🔴 — Il preambolo dichiara quattro AD emendati; sono dieci, e autorizza a saltarne sei

**File:riga.** 49-51 · marcature di emendamento verificate a: AD-1:94 · AD-2:107 · **AD-4:143** ·
AD-5:169 · **AD-8:224** · **AD-10:261** · **AD-11:283** · AD-15:336 · **AD-18:383** · **AD-19:420**.

Il preambolo scrive: «quattro sono emendati in loco (AD-1, AD-2, AD-5, AD-15), **gli altri valgono
come scritti**». Sei AD di `AD-1…AD-20` portano un emendamento datato 15 agosto e sono dichiarati
validi nella forma v1 da questa frase. Non è pedanteria di conteggio: è la prima cosa che un
costruttore legge, e ciò che dichiara valido nella vecchia forma include

- **AD-4**, la cui regola sui segnaposto è passata da sintattica a semantica (:143-153);
- **AD-8**, che ha guadagnato la tabella di sette proprietari senza cui il suo enforcement a permessi
  DB è inapplicabile (:224-243);
- **AD-10**, dove l'ordine fra marcatura e certificazione è invertito rispetto alla v1 (:261-271);
- **AD-11**, che senza l'emendamento **vieta** il protocollo di Gate A (:283-300);
- **AD-18**, la cui `Rule` v1 è **ritirata** (:382-383, con cassatura);
- **AD-19**, la cui enumerazione è passata da sei cause a quindici (:406-418, verificato riga per
  riga: sei marcate v1, nove marcate v2).

Un'unità che segua alla lettera il preambolo costruisce AD-18 nella forma che il documento ha
cancellato. È il tipo di difetto che il gate di stanotte ha già visto tre volte, ed è il più grave
dei tre perché sta nel punto di ingresso.

**Forma minima della correzione.** Sostituire l'enumerazione con il criterio: «gli emendamenti sono
marcati in loco e datati; un AD senza marcatura vale come scritto». Un criterio non invecchia; un
elenco sì — è la stessa lezione che AD-15:336-340 ha già imparato sull'inciso dei tredici.

### RB-16 🟠 — AD-21 dice che i recinti sono cinque; AD-26 ne aggiunge un sesto e AD-21 non lo sa

**File:riga.** AD-21:465 («Deve averne **cinque**») e tabella :468-473 · AD-26:601-603 («È il
**sesto recinto** di `check_boundaries.py` … accanto ai cinque di AD-21»).

Residuo della correzione di continuità visuale: il sesto recinto è stato aggiunto dove il difetto era
stato trovato (AD-26) e il proprietario del meccanismo (AD-21) è rimasto a cinque, con un numerale
esplicito e una tabella chiusa. Chi implementa il controllo lo implementa da AD-21, che è l'AD che lo
possiede: costruisce cinque recinti e il braccio 0 resta scoperto — cioè esattamente il buco che la
correzione voleva chiudere.

**Forma minima della correzione.** Una riga in fondo alla tabella di AD-21 con il sesto recinto e il
rimando ad AD-26, o la sostituzione del numerale con «i recinti sono quelli che gli AD dichiarano».

### RB-23 ⚪ — Dentro AD-5 convivono «cinque più il round-trip» e «otto controlli»

**File:riga.** AD-5:169 · AD-5:185-190.

Il primo emendamento («i controlli sono **cinque più il round-trip visuale**») non è cassato sopra la
seconda correzione, che enumera otto controlli in tabella. La sequenza è leggibile e datata, ma AD-18
usa già la cassatura (`~~…~~`) per lo stesso scopo, quindi il documento possiede la convenzione e qui
non la applica.

**Forma minima della correzione.** Cassare la frase, come in AD-18:382.

---

## G. Rilievi sui due AD scritti stamattina (nessuna lente li ha letti)

Le sette review sono rientrate fra le 06:22 e le 06:54; AD-34 e AD-35 sono stati scritti dopo
(memlog:41-43, spine aggiornato alle 09:11). Verificato: `ObservationPort` e `AD-35` hanno **zero
occorrenze** in tutte e sette. Sono l'unica parte non revisionata dello spine, e contengono due
difetti.

### RB-8 🔴 — AD-34 e AD-15 impongono a *questo documento* una mappa che *questo documento* non contiene

**File:riga.** AD-34:702-703 · AD-15:342-346.

Le due frasi sono normative e si rinforzano a vicenda:

- AD-34:702-703: «l'associazione **metrica → stadio emittente** è dichiarata, e una metrica di §8
  senza stadio emittente è **un difetto di questo documento** (AD-15)»;
- AD-15:342-344: «**Ogni metrica di §8 ha una fonte dichiarata** — quale stadio la emette, su quale
  rappresentazione — e una metrica senza fonte è un difetto *di questo documento*».

Lo spine non contiene alcuna associazione del genere. Verificato per nome sulle sei metriche che il
documento nomina: `VVDR` compare 2 volte (344, 696), `VCER` 6, `VDR` 2, `RRC` 1, `SEC` 1, `TVR` **0** —
e **nessuna** delle occorrenze indica uno stadio emittente. Le altre ventiquattro non compaiono mai.
Per le proprie stesse regole, lo spine si dichiara difettoso su trenta metriche su trenta.

Non è formalismo: è il meccanismo che AD-34 nasce per chiudere. Una metrica senza stadio emittente,
«al momento della verifica, viene calcolata a mano o stimata — ed è il modo più economico di far
passare un gate senza che nessuno abbia mentito» (:697-699). Con l'obbligo scritto e la mappa
assente, quel modo resta aperto **e ora ha anche una regola che lo vieta senza impedirlo**, che è
peggio del silenzio: dà l'impressione che la porta sia chiusa.

**Forma minima della correzione.** La tabella esiste già: la lente di testabilità l'ha costruita
(`review-testabilita.md`, §1 «Tabella metrica → fonte», righe 47-110). Va **assorbita nello spine**
come sezione propria, o nominato normativamente il file che la contiene con la regola che
l'aggiornamento della tabella è una modifica dello spine. Nessuna soglia va scritta: solo la coppia
`metrica → stadio · rappresentazione`.

### RB-9 🔴 — La firma pura di AD-35 non ha gli ingressi che AD-4 e AD-19 richiedono a `render/serialize`

**File:riga.** AD-35:725-728 · AD-4:139-141 e :148-153 · AD-19:416 · albero sorgente:907 · AD-10:268-271.

AD-35 dichiara: `render(LayoutIR, TransformOverlay, ArmEncoding) → SVG` è pura, «stessi ingressi,
stessi byte». Tre ingressi. Ma l'unità che produce l'SVG semantico deve fare anche altro:

- AD-4:141 — «Il renderer sostituisce dai risultati calcolati»;
- AD-4:148-153 — i segnaposto risolvono «solo dentro l'insieme delle grandezze in scope per quel nodo
  del `ProofGraph`», e uno non risolto produce `Refusal`;
- AD-19:416 — `placeholder_unbound` è emesso da **`render/serialize`**, che l'albero :907 colloca
  dentro `render/` come «SVG semantico → sorgente unica di PDF e CircuiTikZ».

Nessuno dei tre ingressi dichiarati porta valori calcolati né lo scope di un nodo del `ProofGraph`.

**Le due unità.** Una mette la sostituzione dei segnaposto **dentro** `render()` e deve aggiungere un
quarto ingresso non dichiarato — la firma di AD-35 diventa falsa e con essa la purezza che dichiara.
L'altra la mette **dopo** `render()`: la firma resta vera e l'SVG che `publish()` riparsa **non è
l'uscita della funzione pura**, quindi round-trip, incidenza (AD-31) e non-occlusione (AD-23) tornano
a girare su un artefatto non coperto da AD-35 — cioè restano i test intermittenti che il `Prevents`
di AD-35 (:719-723) nasce per eliminare. Entrambe conformi, e la seconda annulla l'AD restandogli
fedele alla lettera.

**Forma minima della correzione.** Una riga: o la firma nomina il quarto ingresso (la proiezione in
sola lettura dei valori e dello scope del nodo, che soddisfa AD-4 senza far entrare il `ProofGraph`
mutabile in `render/`), oppure AD-35 dichiara che la purezza copre **l'intera catena fino all'SVG
semantico che `publish()` riceve**, `render/serialize` incluso, e la firma è illustrativa. La cosa da
non lasciare è la scelta all'implementatore, perché una delle due strade svuota l'AD.

### RB-10 🟠 — Il record dell'`ObservationPort` non ha proprietario, entità né ritenzione

**File:riga.** AD-34:700-714 · AD-8:230-238 · ERD:874-888.

AD-34 istituisce un record che `eval/` deve poter leggere (:708) — quindi persistito, o almeno
trattenuto — e che «non è persistito nel `ProofGraph`» (:711). La tabella dei proprietari di AD-8 è
stata estesa oggi a otto entità e **non lo contiene**; l'ERD non lo contiene; nessuna regola di
ritenzione lo copre. AD-34 dichiara solo cosa **non** vi entra: «mai l'immagine, mai un identificatore
di persona», più il `ParticipantToken` alle condizioni di AD-11 (:713-714).

Il pezzo scoperto è proprio quello che AD-11:296-297 rende critico: il `ParticipantToken` **può**
entrare nel canale, il token va cancellato alla chiusura dell'analisi con verifica, e il canale non
ha regola di cancellazione. Il token sopravvive nel luogo che il documento ha appena creato.

*(La stalezza generale dell'ERD è di T6; questo rilievo riguarda un'entità che T6 non poteva vedere
perché non esisteva.)*

**Forma minima della correzione.** Una riga nella tabella di AD-8 (`ObservationRecord` → l'emettitore,
in sola scrittura; `eval/` in sola lettura) e una clausola di ritenzione in AD-34 che si agganci a
quella di AD-11 per la parte con `ParticipantToken`. La finestra numerica è dell'owner.

### RB-11 🟠 — Il paradigma mette i pagamenti dietro un port; l'elenco unico dei port non ne ha

**File:riga.** 32 · 62 · 911 · diagramma:800/802 · Stack:774 · AD-10:259-260 · AD-7:202-210.

La frase che apre il documento è categorica: «Tutto ciò che è non deterministico — modelli di visione
e linguaggio, storage, **pagamenti**, host assistente — sta fuori, dietro *port*». L'elenco unico dei
port, allineato stamattina e ora identico nei due punti (`:62` e `:911`), contiene ModelPort,
BlobPort, LedgerPort, ClockPort, SpicePort, ObservationPort. Nessun port per i pagamenti — e
`LedgerPort` non lo è: AD-7:209-210 lo descrive come il registro con vincolo di unicità, cioè
persistenza interna, mentre il `Merchant of Record` sta nel diagramma :802 come adapter raggiunto
**direttamente** da `gw`. Stessa situazione per la catena LaTeX (:800, Stack:774), che AD-10:259-260
fa scrivere dentro `export()` — l'unico punto autorizzato a scrivere file per l'utente — senza alcun
port che la isoli.

**Le due unità.** Una costruisce `ports/PaymentPort` con due adapter, come AD-3 fa per i modelli;
l'altra chiama l'SDK del Merchant of Record da `api/billing`. Entrambe conformi: nessuna riga vieta
la seconda, e la frase che la vieterebbe sta nel paradigma, non in un AD.

**Forma minima della correzione.** O l'elenco dei port si estende ai due mancanti — coerente con la
frase d'apertura e con AD-3 — oppure la frase d'apertura smette di enumerare i pagamenti e un AD dice
dove vive il confine col fornitore di pagamento. La scelta è dell'owner; l'incoerenza fra le due
affermazioni no. È il residuo dell'allineamento di stamattina, che ha riconciliato i **due elenchi
fra loro** e non con la frase che li governa.

### RB-24 🟡 — Quota, rate limiting e tetto di costo: chiave decisa, politica e proprietario no

**File:riga.** diagramma:792 (`gw[API Gateway: auth, quota, rate, audit]`) · AD-20:437-438 ·
AD-12:302-309 · Deferred:964-965.

Il gateway dichiara quattro responsabilità; di queste, `auth` è governata (AD-20, AD-14, convenzione
:748) e `quota` ha una chiave (`subject_id`, AD-20:437) ma non un proprietario né una politica;
`rate` e `audit` non compaiono in alcun AD. Sul costo, il documento possiede un **pavimento** di
qualità (AD-12) e nessun tetto: l'unica voce che parla di costo è differita (RB-12) ed è proprio
quella che, come mostrato, non è innocua. Vale la pena notarlo perché AD-15:336-341 impone il calcolo
di **tutte e trenta** le metriche a **ogni esecuzione** dell'harness, e AD-12:308 impone `K ≥ 3`:
il costo dell'harness è una funzione di due invarianti e non ha proprietario.

**Forma minima della correzione.** Una voce di *Deferred* con condizione («al primo tenant a
contratto» per la quota; «alla prima esecuzione completa dell'harness» per il costo). Non serve un AD
a questa altitudine — serve che qualcuno abbia detto di rimandarlo.

---

## H. Porte verificate e trovate chiuse

Per completezza, ciò che ho controllato e che **non** è un difetto:

- **Conteggio degli AD, dei `Binds`/`Prevents`/`Rule`, delle rappresentazioni**: 35 / 35-35-35 /
  quattro ovunque. Nessun ID duplicato, nessun segnaposto.
- **«Trenta metriche di §8»** (AD-15:338): corretto — il PRD ha SM-1…SM-21 e SM-C1…SM-C9.
- **Tutti i 53 FR** del PRD sono citati almeno una volta nello spine, individualmente o dentro un
  intervallo. *(Il difetto della mappa `Capability` che si ferma a FR-35 è già di confini/veridicità/invarianti.)*
- **Sintassi mermaid**: valida in tutti e cinque i blocchi.
- **`verify/ # i cinque controlli`** (:900): corretto e non in contraddizione con AD-5 — `verify/`
  possiede i cinque originari, gli altri tre vivono in `render/roundtrip` e `domain/truthfulness`.
- **Nessun AD ovvio**: non ho trovato AD che fissino una decisione priva di alternativa reale. Anche
  i più economici (AD-17, AD-13) chiudono una divergenza vera.
- **Nessun AD nuovo indebolisce un AD precedente**: AD-31, AD-32, AD-33, AD-34 e AD-35 aggiungono
  vincoli, non ne allentano. AD-35 **ritira** `RenderPort` (:912-914) con motivazione corretta.

---

## Ordine di chiusura consigliato

| # | Rilievo | Sev. | Riga | Costo |
|---|---|---|---|---|
| 1 | **RB-15** preambolo: quattro emendamenti dichiarati, dieci reali | 🔴 | 49-51 | una frase |
| 2 | **RB-8** la mappa metrica → stadio che AD-34 e AD-15 esigono non esiste | 🔴 | 702-703, 342-346 | assorbire una tabella già scritta |
| 3 | **RB-9** firma di `render()` incompleta contro AD-4 e AD-19 | 🔴 | 725, 141, 416 | una riga |
| 4 | **RB-12** `Deferred` caching: premessa falsa, può far divergere | 🔴 | 964-965 | due righe |
| 5 | **RB-2** la CI è l'enforcement di otto Rule e non è decisa | 🔴 | 730-731 e sette altre | AD-36 breve |
| 6 | **RB-3** backup e ripristino, in collisione con AD-9 e AD-11 | 🔴 | 250-252, 296-297 | clausola in AD-9 |
| 7 | **RB-5** segreti: HMAC senza custodia, RLS aggirabile per ruolo | 🔴 | 198, 325-326 | AD-36 o convenzione |
| 8 | **RB-4** migrazioni: il proprietario mancante di AD-8 | 🔴 | 219, 230-238 | due righe |
| 9 | **RB-1** esecuzione asincrona: coda nello Stack, in nessun AD | 🔴 | 772, 825-826 | AD-36 o ritiro dallo Stack |
| 10 | **RB-16** cinque recinti in AD-21, sei in AD-26 | 🟠 | 465, 601 | una riga |
| 11 | **RB-17** diagramma: «5 controlli» contro gli otto di AD-5 | 🟠 | 830 | un'etichetta |
| 12 | **RB-18** diagramma delle dipendenze: due recinti su sei | 🟠 | 68-79, 59-66 | quattro nodi |
| 13 | **RB-10** `ObservationRecord` senza proprietario né ritenzione | 🟠 | 700-714, 230-238 | una riga di tabella |
| 14 | **RB-11** pagamenti e catena LaTeX senza port | 🟠 | 32, 62, 911 | una scelta, poi una riga |
| 15 | **RB-13** ambienti già vincolati, ancora differiti | 🟠 | 968-971, 334-335 | separare la voce |
| 16 | **RB-6** esercizio silente; AD-34 dice perché nessuno se ne accorge | 🟠 | 710-712 | voce di `Deferred` |
| 17 | **RB-7** residenza UE seed in tre punti, invariante in nessuno | 🟠 | 771, 800, 804, 968 | clausola in AD-9/AD-14 |
| 18 | **RB-14** tre voci differite senza condizione | 🟡 | 954, 966, 972 | tre condizioni |
| 19 | **RB-19** diagramma dei contenitori v1, «IR» nudo | 🟡 | 784-815, 796 | quattro nodi |
| 20 | **RB-20** costanti di protocollo dentro AD-16; due date non riconciliate | 🟡 | 356-363, 770 | spostamento |
| 21 | **RB-24** quota, rate, tetto di costo senza proprietario | 🟡 | 792 | voce di `Deferred` |
| 22 | **RB-21** `Prevents` storico di AD-18 | ⚪ | 377-381 | due righe scambiate |
| 23 | **RB-22** `Prevents` di AD-34 non nomina una divergenza | ⚪ | 693-699 | una frase |
| 24 | **RB-23** «cinque più il round-trip» non cassato in AD-5 | ⚪ | 169 | una cassatura |

**Nota sul metodo.** Nove rilievi su ventiquattro (RB-11, RB-13, RB-15, RB-16, RB-17, RB-18, RB-19,
RB-23, e in parte RB-10) sono **residui di correzioni applicate nelle ultime ore**: la toppa è
atterrata dove il difetto era stato trovato e non dove il numero, il diagramma o l'elenco lo
ripetevano. È il rischio strutturale di un documento emendato in blocco a gate aperto, e vale la pena
che il passo 6 lo verifichi come classe, non come singoli casi.
