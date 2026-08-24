# Revisione di conformità costituzionale — PRD Kirchhoff v3

**Oggetto:** `_bmad-output/planning-artifacts/prds/prd-Kirchhoff-2026-08-13/prd.md` (v3, 1221 righe)
**Contro:** `docs/02-costituzione-kirchhoff.md` v1.0 — `owner-locked`
**Data:** 15 agosto 2026 · **Tipo:** revisione avversariale, condotta solo sui file
**Domanda unica:** c'è qualcosa nel PRD che viola, indebolisce o aggira K-0…K-5 o un confine owner-locked?

---

## Verdetto

**Violazioni trovate.** Sei rilievi bloccanti e uno moderato, più cinque rischi di formulazione.

Il quadro non è uniforme. Le parti del PRD che parlano di *chi certifica* (K-1), *cosa è un claim*
(K-2) e *cosa non facciamo alle persone* (K-5) sono difese bene, in qualche punto meglio della
costituzione stessa. Tutte le violazioni stanno in una sola classe: **il PRD fissa numeri che la
costituzione riserva all'owner**, e in due casi lo fa dopo aver dichiarato, nello stesso documento,
che farlo è una violazione di confine.

Questo non è un difetto di stile. Il §8 del PRD contiene la frase:

> «Le soglie di lancio sono decisione aperta §27.6 ed è **owner-locked**: un agente che le inventa
> viola un confine, e questo PRD deliberatamente non le contiene.» — §8, blocco «Metriche nuove
> della v3»

La regola è enunciata correttamente e poi applicata a metà: vale per le sette metriche nuove,
non vale per le otto vecchie, non vale per le counter-metrics, non vale per la retention, non
vale per il dimensionamento dell'held-out. È esattamente la deriva che la regola di collisione
della costituzione descrive: *«Non sceglie. Non aggira.»*

### Metodo

Ogni numero contestato è stato tracciato a monte prima di essere qualificato come inventato,
su `brief.md` v3, `addendum.md`, e `docs/inbox/kirchhoff_01_piano_master_v3.md`. Dove la
provenienza esiste, lo dico e abbasso la gravità. Dove non esiste, il numero nasce nel PRD.

---

## Violazioni

### V1 — 🔴 Tetto del 15% sul tasso di Rifiuto: un numero inventato su una counter-metric

**Confini toccati:** K-3 · «Counter-metrics» · «Soglie di qualità minima» (tre confini, una riga).

§8, Counter-metrics, SM-C1:

> «**SM-C1 — Tasso di Rifiuto di certificazione.** […] **Non va portato a zero:** il Rifiuto *è* il
> sistema che funziona, e comprimerlo significa ammorbidire il gate. **Va tenuto sotto il 15%**,
> perché oltre quella soglia il prodotto è percepito come inaffidabile a prescindere dalla
> correttezza.»

E di nuovo in FR-12, Notes (§5.3):

> «Il tasso di Rifiuto è una metrica di salute, non un difetto da azzerare — **ma sopra il 15%** il
> prodotto è percepito come inaffidabile a prescindere dalla correttezza.»

**Perché è una violazione, e non una precauzione ragionevole.**

1. **Il numero non esiste a monte.** Cercato in `brief.md`, `addendum.md` e nel piano master. Il
   brief (riga 184) dice: «tasso di rifiuto non va portato artificialmente a zero — il rifiuto *è*
   il sistema che funziona», **senza tetto**. Il piano master §22 elenca le counter-metrics e la
   prima voce è «refusal rate non va portato artificialmente a zero», **senza tetto**. Il 15%
   nasce qui.
2. **Le counter-metrics sono un confine owner-locked nominato**, con la motivazione esplicita:
   *«Esistono per impedire l'ottimizzazione della cosa sbagliata: un agente che le rimuove rimuove
   il freno.»* Mettere un tetto a una counter-metric non la rimuove — le cambia il segno, che è
   peggio, perché il freno resta a bilancio e non frena più.
3. **La frase si contraddice in due righe.** «Comprimerlo significa ammorbidire il gate» e «va
   tenuto sotto il 15%» sono la stessa istruzione operativa con due conclusioni opposte. Le uniche
   due leve per scendere sotto il tetto sono migliorare il sistema o ammorbidire il gate; la prima
   è lenta, la seconda è a costo zero e non lascia traccia. Un tetto senza un meccanismo che
   distingua le due leve è una pressione permanente verso la seconda.
4. **La giustificazione è di percezione, non di verità:** «percepito come inaffidabile *a
   prescindere dalla correttezza*». È l'argomento che K-3 esiste per neutralizzare. Il PRD lo
   scrive e poi lo accoglie come vincolo numerico.
5. **Il freno punta nella stessa direzione di ciò che deve frenare.** SM-C1 dichiara di
   controbilanciare SM-2 e SM-3 (VVDR, la metrica nord). VVDR ha i Rifiuti fuori dal numeratore:
   ogni Rifiuto in meno la alza. Con un tetto al 15%, SM-C1 e SM-3 spingono nello stesso verso.

**Seconda istanza, stesso difetto.** SM-C2 fissa `0,3` come pavimento di QPS («Abbassare QPS sotto
0,3 significa quasi certamente che il sistema ha smesso di chiedere»). Anche questo numero non ha
provenienza a monte. Stessa classe, gravità minore perché la direzione è protettiva.

**Azione.** Rimuovere `15%` e `0,3` dal PRD. SM-C1 e SM-C2 restano *nominate e strumentate*, senza
soglia. Se un tetto di percezione serve davvero, è una decisione owner e va registrata come tale,
insieme al meccanismo che distingue «meno rifiuti perché il sistema è migliorato» da «meno rifiuti
perché il gate si è abbassato» — senza quel meccanismo il tetto è ingovernabile a qualunque valore.

---

### V2 — 🔴 La retention è fissata nel PRD, su due confini owner-locked distinti

**Confini toccati:** «Invarianti di privacy» · «Retention massima — *Limite superiore dichiarato,
mai estendibile da un agente*».

FR-30 (§5.9) e la sua nota:

> «Il sistema cancella l'immagine sorgente entro **72 ore** dall'estrazione dell'IR.»
> «**Notes:** 72 h è il limite superiore accettato, **fissato qui** perché un requisito con una
> forbice non è testabile.»

«Fissato qui» è la confessione del rilievo. Il limite superiore di retention è, testualmente, il
confine che *«mai»* un agente estende — e fissarlo per la prima volta in un artefatto a valle è
l'atto che il confine descrive, indipendentemente dal valore scelto.

**Aggravanti:**

- **Il PRD si contraddice tre volte sullo stesso dato.** FR-30 lo fissa a 72 h come requisito
  testabile; §12 lo riporta come intervallo «immagini sorgente (24–72 ore)»; §16.4 lo dichiara
  ancora aperto: «Periodo esatto di conservazione delle immagini entro la finestra 24–72 h: da
  fissare». Tre stati per un numero soggetto a obbligo di legge.
- **Sceglie il massimo della forbice.** L'addendum (riga 132) prescrive «cancellazione entro
  24–72 h»; il piano master (riga 709) chiede «retention breve e dichiarata». Fra i due estremi
  ammessi, il PRD fissa quello che favorisce il prodotto e non l'interessato, e lo motiva con la
  testabilità — che è soddisfatta identicamente da 24 h.
- **Gli altri periodi non hanno alcuna provenienza a monte.** §12:

  > «Account (durata del rapporto + **30 giorni**) · […] telemetria pseudonimizzata (**14 mesi**) ·
  > log di sicurezza (**6–12 mesi**)»

  Nessuno di questi tre numeri compare in brief, addendum o piano master. Nascono nel PRD. `14
  mesi` in particolare non è un dettaglio implementativo: è un periodo di conservazione di
  telemetria su persone identificabili, deciso a valle.

**Azione.** Marcare l'intera tabella di §12 e il numero di FR-30 come `[OWNER-DECISION PENDING]`.
FR-30 resta scritto con il segnaposto, non con 72. Risolvere la contraddizione FR-30 / §12 / §16.4
in un unico punto, che è la decisione owner.

---

### V3 — 🔴 L'held-out fotografico viene dimensionato a valle, invertendo la cautela di monte

**Confine toccato:** «Dataset held-out».

FR-34, Notes (§5.10):

> «Chiuderlo richiede un insieme fotografico anche piccolo (**30–40 immagini bastano** a
> distinguere un SER dell'1% da uno del 10%).»

Il piano master, riga 404, dice l'opposto sulla parte che conta:

> «La metà fotografica deve avere split di sviluppo e held-out reale. 30–40 immagini sono utili per
> smoke test o per distinguere un sistema evidentemente pessimo da uno promettente, **ma non
> bastano a sostenere claim di SER molto basso**.»

Il PRD conserva la prima metà della frase e cancella la seconda. La seconda metà è quella che morde:
il target di SM-1 è **SER < 0,5%**, cioè precisamente il «claim di SER molto basso» che 30–40
immagini, per ammissione della fonte, non sostengono. Il risultato è un documento che dimensiona
l'held-out a un livello e fissa un target di qualità che quel livello non può misurare.

**Aggravante decisiva:** il piano master §27 «Decisioni ancora aperte» contiene, al punto 5:

> «5. Dimensione minima held-out fotografico prima del claim commerciale.»

È una decisione owner esplicitamente aperta. Il PRD la chiude in una nota a piè di FR-34, senza
dichiarare di averlo fatto e senza citare §27.5.

**Azione.** Rimuovere «30–40 immagini bastano» e sostituirlo con il rinvio a piano master §27.5.
Se una cifra indicativa serve al planning, va scritta come tale e con la cautela di monte intatta:
sufficiente a smoke test, **non** sufficiente a sostenere il target di SM-1.

---

### V4 — 🔴 SER viene tolta dalla lista owner-locked delle soglie, citando la fonte che ce la mette

**Confini toccati:** «Soglie di qualità minima» · regola di collisione.

§16, Open Question 0:

> «0. 🔴 **Soglie di lancio di VVDR, NED, TVR, VCER, SEC, RRC, VDR.** **Owner-locked** (**§27.6 del
> piano master**, e «soglie di qualità minima» fra i confini della costituzione).»

Il §27.6 del piano master, citato come autorità, recita:

> «6. Soglie **VVDR/SER/RRC** di lancio.»

Il PRD espande la lista alle metriche nuove della v3 (NED, TVR, VCER, SEC, VDR) e **rimuove SER**
dalla lista che sta citando. Poi, in §8, fissa i numeri di SER:

> «Target v1 **< 0,5%**, v2 **< 0,1%**. […] *È la metrica bloccante: **sopra il 2% e non in discesa,
> il prodotto si ferma**.*»

L'ultima clausola non è un target ma una **soglia di kill di prodotto**, che è il caso più puro di
«soglia di qualità minima».

**Attenuante reale, che va detta.** Il brief v3 (riga 175) tratta questi valori come già decisi:
«SER resta la metrica bloccante, con i valori **già fissati**: < 0,5% in v1, < 0,1% in v2», e
analogamente VSR 65%/88%. Quindi le cifre di SM-1 e SM-2 hanno una provenienza owner plausibile e
**non sono inventate dal PRD**.

**Perché resta comunque una violazione.** Brief e piano master v3 sono in conflitto su SER: uno la
dà per fissata, l'altro la elenca fra le decisioni aperte del correct-course che *supera* la v2. Di
fronte a un conflitto fra due upstream su un confine owner-locked, la costituzione non lascia
margine:

> «Un agente che incontra un criterio di accettazione, un rilievo di revisione o una proposta di
> ottimizzazione che richiede di violare un confine owner-locked **si ferma e lo segnala**. Non
> sceglie. Non aggira.»

Il PRD sceglie — nella direzione permissiva — e non segnala. Il difetto non è il valore di SER: è
che il documento risolve da solo un conflitto che doveva salire, e lo fa modificando in silenzio
l'elenco della fonte che cita.

**Azione.** Ripristinare SER nella lista di §16.0 e annotare il conflitto brief §«già fissati» ↔
piano master §27.6 come punto da chiudere con `bmad-correct-course`. La soglia di stop al 2% va
segnata come decisione owner, non come corollario.

---

### V5 — 🔴 `Verified` è definito escludendo il round-trip visuale

**Confini toccati:** «Definizione di `Verified`» (il primo della tabella) · K-0.

FR-11 (§5.3):

> «Il Badge Verificata è applicato **se e solo se tutti e cinque passano**.»

I cinque sono, da §4: «residui KCL, residui KVL, bilancio di potenza, Accordo fra percorsi, sanità
fisica». **Il round-trip visuale non è fra questi.** Il piano master §22 definisce invece:

> «Una derivazione conta solo se tutti i passaggi materiali hanno prova, equazioni verificate **e
> round-trip visuale valido**.»

E K-0 è esplicito sul punto: *«Il disegno non accompagna la derivazione — ne fa parte, e fa parte
della prova.»*

Un «se e solo se» su cinque controlli che non includono la prova visuale **restringe la definizione
di `Verified`** rispetto a monte e rispetto a K-0. La definizione di `Verified` è il primo confine
owner-locked della tabella, con la motivazione: *«È il prodotto. Un sistema che si ridefinisce cosa
significa "verificato" ha smesso di essere verificabile.»*

**Attenuante:** FR-41 rende il round-trip un gate di pubblicazione — «Un disegno che non supera il
round-trip **non viene pubblicato**: produce Rifiuto tipizzato» — quindi nella pratica una
derivazione con round-trip fallito non arriva all'utente.

**Perché resta un rilievo bloccante.** La definizione e il gate sono cose diverse, e il PRD le
separa. Il Badge è ciò che l'utente vede, ciò che il PRD chiama «Soluzione consegnata», e ciò che
**consuma il Credito** (FR-26: «consuma Crediti solo alla consegna di una Soluzione con Badge
Verificata»). Con la formulazione attuale, `Verified` è attribuibile a uno stato la cui prova
visuale non è mai stata certificata, e la protezione dipende interamente dal fatto che un secondo
requisito, in un'altra sezione, intercetti il caso. La definizione owner-locked non deve dipendere
dal fatto che un altro FR faccia da rete: la rete è un'implementazione, e le implementazioni
cambiano senza chain-top. Si aggiunge che anche la grammatica obbligatoria di FR-39 è di fatto una
condizione di pubblicabilità, e nemmeno lei compare nella definizione.

**Azione.** Portare la definizione di `Verified` in un solo punto normativo che includa i cinque
controlli **più** il round-trip visuale di FR-41 **più** la completezza della grammatica di FR-39,
e marcarlo `owner-locked`. Ogni altro FR vi rimanda, nessuno la ridefinisce.

---

### V6 — 🔴 Tre counter-metrics del piano master non sono state riportate

**Confine toccato:** «Counter-metrics» — *«un agente che le rimuove rimuove il freno»*.

Piano master §22:

> «Counter-metrics: refusal rate non va portato artificialmente a zero; **cost per verified proof**;
> p90 latency; correction/ambiguity burden; **user abandonment durante confirmation**; **visual
> clutter/readability failures**.»

Il PRD porta SM-C1 (refusal), SM-C2 (≈ correction/ambiguity burden), SM-C3 (≈ p90 latency), e ne
aggiunge due proprie di merito — SM-C4 copertura di dominio, SM-C5 ampiezza del Catalogo. **Tre
cadono:**

- **`cost per verified proof`** — sopravvive come vincolo di §10.3 («sotto il 10% del prezzo
  effettivo»), non come counter-metric. Un vincolo si verifica; una counter-metric si sorveglia
  mentre si ottimizza altro. Non sono lo stesso strumento.
- **`user abandonment durante confirmation`** — sparita. È il freno naturale di FR-5, che rende
  l'Anteprima obbligatoria e non saltabile. Senza di essa, SM-6 (attivazione > 60%) spinge da sola
  verso la riduzione dell'attrito di conferma, cioè verso l'indebolimento di FR-5.
- **`visual clutter/readability failures`** — sparita. È il freno naturale di VVDR, che il PRD
  promuove a metrica nord. Senza di essa, un modo diretto per far salire VVDR è produrre più stati
  visuali certificati e meno leggibili: certificati sì, comprensibili non misurato. FR-15 pone
  vincoli statici (360 px, 11 px), che non sono una misura di regressione.

I due freni mancanti sono precisamente quelli delle due cose che la v3 promuove a centro del
prodotto: la conferma obbligatoria e la derivazione visuale.

**Azione.** Reintrodurre le tre counter-metrics come SM-C6/C7/C8, nominate e strumentate, **senza
soglie** (vedi V1).

---

### V7 — 🟠 Altre soglie fissate nel PRD senza provenienza a monte

**Confine toccato:** «Soglie di qualità minima». Gravità moderata: nessuna è un gate di kill, ma
tutte sono numeri che diventeranno criteri di accettazione a valle.

| Soglia | §  | Provenienza a monte |
|---|---|---|
| QPS ≤ 1,5 (v1) / ≤ 0,5 (v2) — SM-4 | §8 | **nessuna** |
| SM-6 attivazione > 60% | §8 | **nessuna** |
| SM-7 ritorno alla seconda soluzione > 70% | §8 | **nessuna** |
| SM-8 correzioni per soluzione < 1,0 | §8 | **nessuna** |
| §10.3 costo di elaborazione < 10% del prezzo | §10.3 | parziale (addendum: margine > 88%) |
| TTV < 45 s / < 25 s; abbandono a 60 s | §8, §9 | ✅ addendum riga 179 — **non contestata** |
| SER < 0,5% / < 0,1%; VSR 65% / 88% | §8 | ✅ brief riga 175-176 — vedi V4 |

Il costo di elaborazione è fuori dal perimetro costituzionale (i prezzi sono esplicitamente fra le
cose che la costituzione «non decide»), quindi §10.3 non è contestato come confine: lo elenco solo
per completezza della tracciatura.

**Azione.** Le quattro righe senza provenienza vanno marcate `[OWNER-DECISION PENDING]` come le
sette metriche nuove della v3, per coerenza con la regola che il §8 già enuncia.

---

## Rischi di formulazione (non violazioni)

Li separo deliberatamente: nessuno di questi contraddice la costituzione oggi. Tutti permettono a
un artefatto a valle di contraddirla senza accorgersene.

**W1 — `Refusal` e `Failure` non sono tipizzati come richiede K-3.**
K-3 prescrive: *«`Refusal` e `Failure` restano tipi distinti su canali distinti.»* Il PRD li
distingue nel comportamento — §4 («Non è un errore di sistema: è un esito previsto»), FR-26
(«Un Rifiuto di certificazione non consuma Crediti. Un errore di sistema non consuma Crediti»),
FR-41 («Rifiuto tipizzato, non un avviso») — ma non nomina mai un tipo `Failure` né due canali. La
conseguenza operativa di K-3 è mezza recepita, e l'architettura può collassarli in un unico canale
di errore restando formalmente conforme al PRD.

**W2 — K-4 non è esteso agli artefatti statici.**
FR-11 rende i residui ispezionabili *dall'utente nel prodotto*. FR-19 impone su ogni export
metadati con «un riferimento verificabile all'**IR**» — cioè al circuito, non al certificato, non
ai residui, non alla versione del verificatore. Un PDF esportato, e ancor più le «pagine pubbliche
di esercizi […] indicizzabili» di §14 e la «prova gratuita limitata con filigrana» di §13, possono
quindi portare un Badge che non si apre su nulla. K-4: *«Un badge che non si apre è
un'affermazione.»* Non è una violazione — nulla dice che non si apra — ma è il comportamento
predefinito che si otterrà se nessuna storia dice il contrario. Basta estendere FR-19 al
riferimento del `Claim` (`verifier_id` + versione + `evidence_ids`), che FR-42 già produce.

**W3 — FR-36: rilevamento su persona non autenticata, senza perimetro dichiarato.**
> «Un soggetto anonimo che ricrea la sessione per azzerare la quota **viene rilevato**.»

Non è una violazione di K-5: è antifrode di billing, non valutazione educativa della persona, e
K-5 vieta i punteggi *valutativi*. Ma è l'unico requisito del PRD che chiede di osservare una
persona non autenticata attraverso sessioni distinte, il meccanismo non è specificato, e §12 non
prevede alcuna classe di dato né retention per l'identificatore persistente che lo rende possibile
— che è confine owner-locked (invarianti di privacy). È anche l'unico punto da cui una storia
potrebbe far nascere, in buona fede, un punteggio di sospetto per persona: la distanza fra «rileva
l'elusione della quota» e «assegna un punteggio di rischio all'utente» è una riga di codice e
nessuna riga di PRD. Va vincolato esplicitamente: segnale binario, finalità di sola quota, nessuna
persistenza oltre la finestra della quota, mai esposto a un docente o a un tenant.

**W4 — §16.8 è obsoleta e contraddice §7.2.**
> «~~Se la baseline dei modelli frontier supera l'85%…~~ **Chiusa il 13 agosto 2026** […] e
> **l'ingresso da foto resta nell'MVP**.»

§7.2 sposta la foto a Gate C, e §7 dice che quel gate «resta obbligatorio ma non è più il primo».
La domanda 8 è ferma al 13 agosto. Rileva perché la decisione è registrata come presa «**senza
misura**» su una questione che è il gate del gold set — cioè accanto a V3 e V4. Da riallineare.

**W5 — La scheda di sistema pubblica (§11) pubblica numeri senza vincolo di copertura.**
§11 prevede una scheda pubblica con «SER e VSR **misurati**». FR-34 impone giustamente che «Ogni
rapporto prodotto dichiari esplicitamente la propria copertura», ma la scheda di §11 non è legata a
quella regola. Dato il punto cieco che SM-1 stessa dichiara — «Resta cieca finché 1.3 non è
`done`» — un SER pubblicato senza la sua copertura è un claim di dominio senza evidenza. Estendere
il vincolo di FR-34 a §11 chiude il caso.

---

## Dove non ho trovato nulla — detto in chiaro

**Nessun percorso che permetta a un modello di concedere `Verified`.** Cercato in tutti gli FR e in
§7.1. Il PRD è netto e in più punti più esplicito della costituzione:

- FR-41: «**Nessun VLM partecipa alla certificazione della topologia.** La QA percettiva esiste, è
  separata, e non concede `Verified` (K-1).»
- FR-13: «Nessun numero presentato all'utente ha come unica origine un'uscita di modello
  linguistico», con il controllo di coerenza fra testo generato e risultato calcolato.
- FR-2: l'Accordo è calcolato «confrontando gli IR canonicalizzati, **mai leggendo un campo di
  confidence emesso da un modello**» — chiude la scorciatoia più naturale.
- FR-42 soddisfa anche il requisito della costituzione «il gate di veridicità non è una skill
  esterna»: «un ambiente senza skill installate produce gli stessi verdetti».

**Nessun claim di dominio pubblicato senza evidenza.** FR-39 impone `CERTIFICATE` con `verifier_id`
e versione; FR-42 impone `evidence_ids` non vuoto e `verifier_id` risolvibile. Il tipo `Claim` di
K-2 è riportato campo per campo. L'unico spigolo è W5, che riguarda un numero di reportistica, non
un claim di dominio.

**Nessun punteggio, ranking, stima di abilità, voto previsto, placement, segnale di proctoring o
punteggio per studente rivolto al docente.** È la categoria che ho cercato più a fondo, ed è la
meglio difesa del documento. §6: «Nessun endpoint restituisce un punteggio associato a una persona
identificata»; FR-17: «Nessuna risposta dell'utente in modalità Studio è registrata come punteggio,
voto o misura di rendimento attribuita a una persona»; §3.2 esclude come non-utenti le
«Istituzioni che vogliono valutare studenti»; §10.4 vieta la modalità «solo risposta» ai tenant
istituzionali; §11 impone la riverifica **a ogni release** «perché la deriva avviene per accumulo
di richieste ragionevoli». Le metriche SM-6, SM-7, SM-8, SM-11 sono aggregate di prodotto e non
attribuite a persona; l'etichetta «difficoltà» di FR-25 è dell'esercizio, non dello studente.
L'unico punto adiacente è W3, che non è valutativo.

**Nessuna violazione degli invarianti di billing.** FR-26 realizza alla lettera «consumo solo su
proof certificato»; FR-8, FR-26 e §15 realizzano l'idempotenza. Il Rifiuto non consuma Crediti in
tre punti indipendenti. I prezzi non sono contestabili: la costituzione li mette esplicitamente fra
ciò che non decide.

**Il rifiuto non è trattato come un fallimento.** UJ-3 lo mette al centro di una user journey,
FR-12 lo tipizza come esito progettato con interfaccia propria, SM-16 (RRC) ne misura la qualità
esplicitamente «Vincolata a K-3». L'unico difetto è il tetto di V1 — che però basta da solo a
rovesciare l'incentivo.

**Nessun badge senza prova all'interno del prodotto.** FR-11 rende i residui ispezionabili, FR-42
porta la versione del verificatore nella prova citando K-4. Il rischio è solo sugli artefatti che
escono dal prodotto (W2).

**Il §16.0 e il §7 sono, sul loro perimetro, esemplari.** Il §16.0 tiene owner-locked le soglie
delle sette metriche nuove e distingue correttamente fra «blocca la dichiarazione di superamento di
Gate A» e «blocca la sua costruzione». Il §7.0 registra l'assunzione che il kill criterion potrebbe
risultare soggettivo e che in quel caso «il gate va reso misurabile prima di eseguirlo». Sono la
prova che la disciplina è compresa: le violazioni di questa revisione sono l'assenza della stessa
disciplina altrove, non la sua ignoranza.

---

## Riepilogo

| # | Rilievo | § | Confine | Gravità |
|---|---|---|---|---|
| V1 | Tetto 15% sul tasso di Rifiuto (e 0,3 su QPS) | §8 SM-C1/C2, FR-12 Notes | K-3 · counter-metrics · soglie | 🔴 bloccante |
| V2 | Retention fissata a valle (72 h, 30 gg, 14 mesi, 6–12 mesi) | FR-30, §12 | privacy invariants · retention massima | 🔴 bloccante |
| V3 | Held-out fotografico dimensionato a 30–40, cautela di monte cancellata | FR-34 Notes | dataset held-out | 🔴 bloccante |
| V4 | SER rimossa dalla lista owner-locked citando §27.6 che ce la mette | §16.0, §8 SM-1 | soglie di qualità minima · regola di collisione | 🔴 bloccante |
| V5 | `Verified` definito «se e solo se cinque controlli», round-trip escluso | FR-11 | definizione di `Verified` · K-0 | 🔴 bloccante |
| V6 | Tre counter-metrics del piano master non riportate | §8 | counter-metrics | 🔴 bloccante |
| V7 | QPS, SM-6, SM-7, SM-8 senza provenienza | §8 | soglie di qualità minima | 🟠 moderato |
| W1 | `Failure` non tipizzato, canali non separati | §4, FR-26 | K-3 (conseguenza operativa) | 🟡 rischio |
| W2 | K-4 non esteso a export, pagine pubbliche, prova con filigrana | FR-19, §13, §14 | K-4 | 🟡 rischio |
| W3 | Rilevamento su soggetto anonimo senza perimetro né classe di dato | FR-36 | privacy invariants · adiacente K-5 | 🟡 rischio |
| W4 | §16.8 obsoleta, contraddice §7.2, decisione «senza misura» | §16.8 | — | 🟡 rischio |
| W5 | Scheda di sistema pubblica non vincolata alla copertura di FR-34 | §11 | K-2 (adiacente) | 🟡 rischio |

**Nessun rilievo** in: modello che concede `Verified`; modello come fonte autorevole dei numeri
finali; claim di dominio senza evidenza; rifiuto trattato come fallimento; badge privo di prova
dentro il prodotto; punteggio per persona in qualunque forma; invarianti di billing.

---

## Cosa fare, nell'ordine

1. **Non correggere i numeri: toglierli.** V1, V2, V3, V4 e V7 si chiudono sostituendo cifre con
   `[OWNER-DECISION PENDING]` e il rinvio alla fonte owner. Il PRD non deve proporre valori
   alternativi — proporre un numero diverso sullo stesso confine è la stessa violazione.
2. **V5 e V6 sono modifiche di struttura, non di valore**, e si possono fare subito: un punto
   normativo unico per `Verified`, e tre counter-metrics reintrodotte senza soglia.
3. **Portare V4 a `bmad-correct-course`.** È un conflitto fra due upstream su un confine
   owner-locked, e la regola di collisione dice che si segnala, non si sceglie. È l'unico rilievo
   che non si chiude dentro il PRD.
4. **W1…W5 sono modifiche di formulazione** e possono viaggiare con il prossimo giro editoriale.
5. **Nessuna di queste correzioni tocca §5.0, il Visual Proof Kernel, né il kill criterion di
   Gate A.** La costruzione dell'MVP non è bloccata da questa revisione. È bloccata la
   *dichiarazione di superamento* di Gate A — che è esattamente ciò che §16.0 già prevede.
