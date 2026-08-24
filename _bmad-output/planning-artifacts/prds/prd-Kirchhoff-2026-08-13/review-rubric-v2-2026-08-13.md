# PRD Quality Review — Kirchhoff

Rubrica: `bmad-prd/assets/prd-validation-checklist.md`. Stakes: **launch** (utenti paganti +
esposizione regolatoria). Forma: **chain-top** (alimenta UX → architettura → epiche/storie).
Documento: 7.316 parole, 35 FR, 7 UJ, 10 SM + 4 counter-metric.

## Overall verdict

Il PRD regge come documento di decisione: ha una tesi esplicita ("la separazione fra plausibile e
verificato"), le feature la servono, e le metriche la validano invece di misurare attività. Il
rischio non è nella strategia ma in due punti concreti: **alcuni FR non sono ancora testabili
perché dipendono da numeri che il PRD stesso lascia aperti**, e **la massa di FR è sbilanciata
verso il B2C mentre la tesi economica dice che il B2B porta più ricavo in tutti gli scenari**. Il
primo è meccanico e si chiude prima delle storie; il secondo è una tensione strategica reale che
va decisa, non smussata.

## 1. Decision-readiness — **strong**

Le decisioni sono dichiarate come decisioni, non nascoste fra le "considerazioni". §6 Non-Goals è
categorico e motivato ("Ogni richiesta di cliente in questa direzione va rifiutata o riformulata
come generazione"). §10.1 fissa una precedenza esplicita fra metriche in conflitto, e SM-C2 la
ripete dove serve: *"Se SER e QPS sono in conflitto, vince SER."* Un PRD che dice quale metrica
perde è raro e vale più di dieci pagine di allineamento.

I trade-off nominano cosa si è rinunciato: §7.2 differisce il Percorso C dichiarandone il costo
("l'argomento di vendita più forte verso un dipartimento") invece di far finta che sia
irrilevante. Le Open Questions sono davvero aperte — Q1, Q3 e Q8 non hanno la risposta nella frase
successiva.

### Findings
- **medium** — Q8 non è una domanda aperta, è un innesco di kill (§16). Q8 dice che se la baseline
  frontier supera l'85% il PRD viene riscritto e il B2C esce. È l'elemento più consequenziale del
  documento ed è in ottava posizione in un elenco. *Fix:* promuoverlo a callout in §7 MVP Scope,
  lasciando in §16 solo il rimando.

## 2. Substance over theater — **strong**

Nessuna sezione persona standalone: il contesto vive dentro le UJ, come prescritto. Gli NFR hanno
soglie specifiche del prodotto (45 s al 90° percentile, costo sotto il 10% del prezzo, almeno due
fornitori intercambiabili) invece di aggettivi. La Vision non è trasferibile a un altro PRD della
categoria: *"non mostra mai un risultato di cui non può rispondere"* descrive questo prodotto e
nessun altro. La differenziazione non è inventata: il documento a monte dichiara i moat assenti
invece di fabbricarne.

### Findings
- **low** — §14 Platform è arredamento. Tre punti che ripetono decisioni già prese in §7.1 e §5.6.
  *Fix:* fondere in §7.1 In Scope, o eliminare.

## 3. Strategic coherence — **strong** (con una tensione reale)

La tesi è dichiarata e le feature ci si allineano. Le SM validano la tesi anziché misurare
attività: SM-1 è SER, cioè la metrica della tesi stessa; non c'è una singola metrica di vanità. Le
quattro counter-metric sono sostanziali — SM-C1 arriva a dire che il tasso di Rifiuto **non va
portato a zero**, che è il tipo di affermazione che impedisce a un ingegnere di ottimizzare la
cosa sbagliata.

### Findings
- **high** — Allocazione FR contro tesi economica (§5, §8). La proiezione dice che il B2B genera
  più ricavo del B2C in tutti e tre gli scenari, e che 14 clienti B2B valgono più di 200 B2C. Ma
  5 UJ su 7 e circa 25 FR su 35 sono B2C; Studio ne ha 4. Se la tesi economica è giusta, la massa
  di lavoro è nel posto sbagliato. *Fix:* decidere esplicitamente una delle due — (a) il B2C è il
  motore di acquisizione e merita davvero la massa di FR, e allora dirlo in §7; oppure (b)
  espandere §5.7 con gli FR che un tutor pagante richiede davvero (importazione del banco
  esistente, ri-generazione, revisione a campione) e ribilanciare l'MVP.

## 4. Done-ness clarity — **adequate** (dimensione più debole)

La maggior parte degli FR porta conseguenze verificabili e concrete: FR-2 ("i Pass differiscono
per almeno due assi"), FR-11 ("il Badge Verificata è applicato se e solo se tutti e cinque
passano"), FR-26 ("un Rifiuto di certificazione non consuma Crediti") sono direttamente
traducibili in test. FR-13 è particolarmente forte perché formulato come proprietà negativa
verificabile.

Ma tre FR rimandano a valori che il PRD stesso non ha ancora fissato, e come sono scritti oggi non
sono testabili.

### Findings
- **high** — FR-30 dipende da un numero che è Open Question (§5.9, §16 Q4). "Entro il periodo di
  conservazione dichiarato" non è verificabile finché il periodo è un intervallo 24–72 h da
  fissare. *Fix:* fissare il valore adesso (72 h è il limite superiore già accettato) e trattare
  ogni riduzione come miglioramento successivo.
- **medium** — FR-18 rimanda a un documento che non esiste (§5.5). "L'ambiente di riferimento
  documentato" per la compilazione LaTeX non è ancora scritto. *Fix:* l'architettura deve
  produrlo come artefatto nominato; finché non esiste, l'FR non è chiudibile.
- **medium** — FR-15 usa un aggettivo dove serve un limite (§5.4). "Leggibili a larghezza mobile"
  non ha soglia. *Fix:* dare una larghezza minima di riferimento e una dimensione minima del testo
  nei disegni.

## 5. Scope honesty — **strong**

§6 fa lavoro reale: il divieto di funzioni valutative è motivato, ripetuto in §11, e accompagnato
dall'istruzione operativa su cosa fare quando un cliente lo chiede. §7.2 dà una ragione per ogni
rinvio e marca con `[NOTE FOR PM]` i due emotivamente carichi (Percorso C, localizzazione).

Densità di elementi aperti: 8 Open Questions + 4 assunzioni + 4 `[NOTE FOR PM]` = 16 su un PRD di
lancio. Accettabile in valore assoluto, ma la composizione conta più del numero.

### Findings
- **high** — Q1 non è una domanda aperta, è un blocco di fase (§16). La scelta di ateneo e corso
  per il primo Profilo curricolare determina le convenzioni con cui si annota il gold set, e il
  gold set precede tutto il resto. Lasciarla aperta blocca il primo passo del piano. *Fix:*
  risolverla prima di iniziare l'annotazione; nel frattempo marcarla come blocco di fase, non
  come domanda.

## 6. Downstream usability — **strong**

Verificato meccanicamente: FR-1…FR-35 contigui e senza duplicati, nessun FR referenziato ma non
definito, UJ-1…UJ-7 tutti definiti e tutti referenziati da almeno un FR, SM-1…SM-10 più
SM-C1…SM-C4 presenti. Il Glossario copre tutti i sostantivi di dominio usati in §5, e gli FR li
usano alla lettera. Ogni sezione regge estratta da sola: i rimandi passano per termini del
Glossario, non per "vedi sopra".

### Findings
- **low** — Doppia forma "IR" / "Rappresentazione Intermedia" (§4 e trasversale). Il Glossario
  definisce la coppia, quindi non è deriva. *Fix:* l'architettura scelga una forma sola e la usi
  nel codice e nello schema.

## 7. Shape fit — **strong**

Forma corretta per un prodotto consumer con una gamba B2B che alimenta UX, architettura e storie:
le UJ sono portanti, ognuna ha un protagonista con nome e contesto inline, nessuna UJ fluttuante.

Nota positiva fuori rubrica: **UJ-3 è un percorso di fallimento** — "il sistema rifiuta di
certificare". È inusuale ed è la scelta giusta: è il momento in cui la promessa del prodotto si
dimostra o si smonta, e senza una UJ dedicata nessuno lo progetta come esperienza. Ha un suo FR
(FR-12) e una sua counter-metric (SM-C1).

## Mechanical notes

- **Continuità ID:** nessuna lacuna, nessun duplicato, nessun riferimento non risolto. Verificato
  per FR, UJ, SM.
- **Roundtrip Assumptions Index:** *era rotto* — due voci dell'indice (§17) non avevano il
  corrispondente tag inline. **Corretto durante questa revisione:** aggiunto `[ASSUMPTION]` al
  titolo e in §2 per la dedizione parziale.
- **Deriva di glossario:** nessuna. Termini definiti in §4 e usati identici in §5, §8, §9.
- **Protagonisti UJ:** tutti nominati (Marco, Giulia, Sara, Davide, prof.ssa Ferrari).
- **Sezioni richieste per stakes e tipo:** presenti, inclusi i cluster Adapt-In che il prodotto
  richiede davvero (NFR trasversali, guardrail, compliance, data governance, monetizzazione,
  piattaforma, contratto di superficie pubblica, why now).
