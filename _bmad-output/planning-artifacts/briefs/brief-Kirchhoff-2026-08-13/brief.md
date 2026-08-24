---
title: "Product Brief: Kirchhoff"
version: 3
status: draft
created: 2026-08-13
updated: 2026-08-14
supersedes: "brief v2 (13 ago 2026) — categoria «risolutore verificato»"
upstream: "docs/02-costituzione-kirchhoff.md (owner-locked) · docs/inbox/kirchhoff_01_piano_master_v3.md"
---

# Product Brief: Kirchhoff

## Executive Summary

Kirchhoff non vende il numero giusto. Vende **la derivazione disegnata**: circuito →
trasformazione → circuito ridisegnato → equazione → di nuovo, finché il problema è chiuso — e
ogni stato pubblicato è verificabile a macchina.

È un cambio di categoria rispetto alla versione precedente di questo brief. La verifica
deterministica resta il gate — nessuno stato riceve `Verified` da un modello — ma non è più la
proposta di valore. La proposta è che **puoi seguire con gli occhi come il circuito cambia,
perché quella trasformazione era lecita sulla topologia corrente, e come si sa che il nuovo
circuito è equivalente**. Il disegno non accompagna il ragionamento: ne fa parte, e fa parte
della prova. Le cinque leggi che lo impongono sono in `docs/02-costituzione-kirchhoff.md` e sono
owner-locked.

Il motore serve due prodotti con ruoli economici distinti. **Solve** (B2C) è acquisizione,
utilizzo e — soprattutto — corpus di fallimenti reali. **Studio** (B2B) è il motore di ricavo:
varianti d'esame verificate per tutor, centri di ripetizioni e dipartimenti. Il B2B supera il
B2C in tutti e tre gli scenari a dodici mesi; il B2C produce i dati che rendono il motore
migliore. Il kernel nasce autonomo, con tre adapter — Web/API, MCP e MCP Apps, Ardesia — e
nessun fork per host.

## La frase di categoria

**Kirchhoff trasforma un problema circuitale in una prova visuale interattiva e verificata.**

Non è un chatbot per circuiti. Non è un generatore TikZ. Non è un CAS con una UI. Non è un
simulatore elettronico. È un ambiente in cui **stato, trasformazione, disegno, equazione,
evidenza e verifica sono un unico oggetto navigabile**.

## The Problem

Uno studente di ingegneria davanti a un circuito che non sa chiudere non cerca quasi mai «la
risposta». Cerca una di quattro cose:

1. **Cosa posso fare adesso a questo circuito?**
2. **Perché questa trasformazione è lecita?**
3. **Come cambia concretamente il circuito quando la applico?**
4. **Dove ho deviato io?**

Gli LLM generalisti producono prosa plausibile, formule e spesso anche il risultato giusto. Il
limite è strutturale, non di qualità: **non mantengono con affidabilità una catena lunga di
trasformazioni topologiche**, e nulla garantisce che il disegno intermedio corrisponda al grafo
elettrico che stanno effettivamente usando. Il fallimento non si vede: è una spiegazione
coerente sopra una topologia che è cambiata di nascosto.

I libri risolvono benissimo alcuni esercizi. Un solution manual ne svolge 20–50 dentro un
corpus molto più grande, e il problema dello studente è quasi sempre proprio quello che non c'è.

A questo si somma il costo che il brief precedente aveva già identificato e che resta vero: una
risposta sbagliata presentata con sicurezza è peggio di nessuna risposta, perché rimuove
l'incentivo a controllare.

Dall'altro lato della cattedra il dolore è più cronico e meglio pagato. Un tutor o un centro di
ripetizioni passa 4+ ore a settimana a costruire esercizi nuovi, ricalcolare le soluzioni a mano
e impaginarle — lavoro meccanico, ripetitivo, e soggetto a errori proprio dove l'errore costa di
più: il foglio soluzione.

## The Solution

**Ogni passo ha una grammatica obbligatoria:** `BEFORE · ACTION · AFTER · EQUATION ·
CERTIFICATE · PROVENANCE`. Non è impaginazione, è lo schema dati. Un passo senza disegno non è
un passo: è una riga di calcolo, e va fusa con quella precedente.

**Ciò che non cambia resta fermo.** Una trasformazione produce un patch locale sul layout, non
un ridisegno globale: gli elementi non coinvolti mantengono la stessa posizione da un passo al
successivo. È questa continuità — non la bellezza del disegno — che rende la derivazione
seguibile con gli occhi.

**La soluzione è un grafo, non una lista.** Sovrapposizione, Thévenin su sottoproblemi e
transitori creano rami temporanei che poi si ricongiungono. Il modello di dominio è un
`ProofGraph` di stati verificati, non una sequenza lineare.

**Il disegno viene verificato come dato, non giudicato a vista.** L'SVG pubblicato porta
identità di componenti e terminali, viene riparsato, ricanonicalizzato e confrontato con il
circuito canonico. Il controllo primario è un confronto esatto di grafi — non un modello di
visione che dice «sembra giusto». Un secondo controllo percettivo cerca ciò che il parser non
vede (etichette sovrapposte, fili ambigui, testo illeggibile) ma non certifica la topologia.

**Due modalità.** In *Risolvilo per me* l'utente riceve un ProofGraph navigabile: precedente e
successivo, prima/differenza/dopo, «perché posso farlo?», «mostrami i nodi che lo rendono
lecito», «apri il certificato», «prova tu da qui». In *Risolviamo insieme* la lavagna non è un
canvas separato: cerchiare R3 e R4 e scrivere `R3 + R4?` diventa un'ipotesi strutturata, e il
sistema risponde sul sottografo e sulla regola reale — *serie: falso; parallelo: vero; nodi
condivisi A, B* — invece di improvvisare una spiegazione generica. Il tutor sceglie la strategia
esplicativa; non decide la verità elettrica.

**L'oggetto condivisibile è la prova, non il PDF.** Un Proof Replay apribile da URL — slider
degli stati, before/diff/after, formule, componenti cliccabili, certificato — è
contemporaneamente prodotto, demo, condivisione e dimostrazione tecnica. Il PDF resta un export.

**Studio (B2B).** Un esercizio in ingresso → N varianti parametriche, ognuna con derivazione
completa verificata e foglio soluzione separato. Export LaTeX/CircuiTikZ, PDF, formati e-learning.
Banco esercizi privato del tenant, con provenienza e audit.

## What Makes This Different

**Prima una correzione onesta.** «Circuiti come nodi, metodi come archi» non è un moat
proprietario: iCircuits/autoCircuits del Politecnico di Torino rappresenta già le soluzioni come
sequenza o grafo di circuiti e metodi, con un catalogo ricco di trasformazioni e ridisegni
legati ai passaggi. Non è una sconfitta — dimostra che il paradigma è tecnicamente sensato — ma
il brief precedente vendeva «la sequenza didattica» come terzo moat, e non lo è. È un requisito
di prodotto.

Il moat plausibile non è una feature: è la **combinazione** di cose che un precedente accademico
non risolve in un prodotto consumer moderno.

- **Input arbitrario dell'utente** — foto, screenshot, PDF, LaTeX, netlist, editor.
- **Layout persistente e incrementale** — ciò che non cambia resta fermo, con ancoraggi duri.
- **Visual round-trip** — il disegno pubblicato deve ricostruire lo stesso circuito canonico.
- **Lavagna bidirezionale** — il tentativo dello studente entra nel verifier come input
  semantico, non come immagine.
- **Profilo curricolare** — stesso problema, metodo e notazione coerenti con corso, docente,
  paese. Se il corso non ha ancora fatto Thévenin, Kirchhoff non lo usa.
- **Corpus di fallimenti ed eval propri** — ogni errore sfuggito diventa un invariante permanente.
- **Distribuzione cross-host** via MCP e MCP Apps, oltre alla web app.
- **Traslabilità nativa in Ardesia**, senza duplicare simulatore, memoria, auth o shell.

**Moat onestamente assenti:** nessun vantaggio sui modelli di visione (usiamo API di terzi);
nessun effetto di rete; nessuna esclusiva sul paradigma del solution tree; nessun vantaggio di
distribuzione oltre alla base esistente di ~300 studenti. Il vantaggio di partenza è velocità di
esecuzione e conoscenza del dominio.

## Who This Serves

**Studente che vuole capire, non copiare (primario B2C).** Ha il procedimento a metà e non sa
quale mossa è lecita adesso. Successo per lui: vedere la trasformazione applicata al *suo*
circuito, capire perché era permessa, e riconoscere il punto in cui era andato fuori strada.
È la coorte che giustifica il prodotto davanti a un dipartimento, ed è quella su cui la modalità
*Risolviamo insieme* vince o perde.

**Studente in emergenza (primario B2C, per volume).** Esame fra 24–72 ore, otto esercizi
arretrati, zero tolleranza per una risposta sbagliata e zero pazienza sopra i 60 secondi. Paga
volentieri una tantum in prossimità dell'esame.

**Tutor privato e centro di ripetizioni (primario B2B).** Vende ore, non contenuti: ogni ora
spesa a preparare esercizi è un'ora non fatturata. Successo: quattro ore a settimana restituite,
con la garanzia che il foglio soluzione è corretto. Basso churn, ciclo di vendita corto, valore
dimostrabile prima della chiamata.

**Docente universitario (canale, non ricavo).** È il critico più pericoloso e il distributore
più efficace. Accesso gratuito, senza obblighi, senza funzioni valutative.

## Success Criteria

**North star: VVDR — Verified Visual Derivation Rate.** Problemi con derivazione visuale
interamente certificata / problemi accettati dal sistema. Una derivazione conta solo se **tutti**
i passaggi materiali hanno prova, equazioni verificate e round-trip visuale valido. È una metrica
che non si può ottimizzare a parole: richiede che il layout persistente e il round-trip esistano
davvero.

Sotto la north star, sette famiglie che dicono *dove* si rompe:

| Metrica | Cosa misura |
|---|---|
| **NED** | distanza strutturale fra circuito estratto e circuito reale |
| **TVR** | trasformazioni proposte che risultano lecite sulla topologia corrente |
| **VCER** | passi in cui la continuità visuale si rompe |
| **SEC** | copertura di evidenza per passo |
| **RRC** | correttezza del round-trip di rendering |
| **VDR** | derivazioni portate a termine |
| **SER** | soluzioni pubblicate come verificate ma numericamente sbagliate |

**SER resta la metrica bloccante,** con i valori già fissati: **< 0,5%** in v1, **< 0,1%** in v2.
VSR (soluzioni verificate e corrette senza correzione umana): 65% in v1, 88% in v2. Se SER sale,
si alza il carico di domande per farla scendere — mai il contrario.

**Le soglie di lancio delle metriche nuove non sono fissate in questo brief.** Sono decisione
aperta (piano master §27.6) e le soglie di qualità minima sono owner-locked: nessun agente le
propone come fatto compiuto.

**Counter-metrics** (owner-locked, esistono per impedire di ottimizzare la cosa sbagliata): il
tasso di rifiuto non va portato artificialmente a zero — il rifiuto *è* il sistema che funziona;
costo per proof verificato; latenza p90; carico di correzione e ambiguità; abbandono durante la
conferma; fallimenti di leggibilità del disegno.

## Il gate che decide se il prodotto esiste

Prima di espandere qualunque cosa: **serie, parallelo, partitore**. Tanto basta per rispondere
alla sola domanda che conta.

> **Kill criterion di Gate A.** Se la continuità visuale non è chiaramente migliore di un
> re-layout completo, non si espande il catalogo.

Se la risposta è no, tutto il resto — foto, modelli, MCP, billing, B2B, Ardesia — poggia su una
tesi falsa, e la mossa corretta è ridurre lo scope a Studio B2B con input strutturato. Il gold
set fotografico da 200 immagini reali con held-out e la baseline dei modelli frontier restano
obbligatori, ma sono il gate di **Gate C**, non più il gate che precede il prodotto: la foto non
è più il primo rischio da comprare.

## Scope

**Dentro la prima versione — Gate A, Visual Proof Kernel.** Ingresso **strutturato** (netlist,
LaTeX, editor). Trasformazioni: serie, parallelo, partitore, Millman, Thévenin/Norton semplice.
ProofGraph con stati e certificati. LayoutPatch locale con ancoraggi. SVG semantico e round-trip
esatto. Proof Replay interattivo.

**Poi, in quest'ordine:** **B** lavagna e tutor contestuale · **C** perception da foto e PDF con
held-out reale · **D** distribuzione PWA, MCP e MCP Apps · **E** ricavo, entitlement B2C e pilot
Studio · **F** Ardesia · **G** prova di orizzontalità su un secondo dominio.

**Fuori dalla prima versione:** la foto (è Gate C); circuiti non lineari; modello di visione
proprio; simulatore SPICE da zero; app native; chat libera generalista; marketplace di plugin;
LMS; gamification; agent framework proprietario prima del kernel; venticinque MCP app separate.

**Fuori senza scadenza — il confine che regge tutto il resto:** nessuna funzione valutativa.
Niente voti, punteggi di merito, ranking, predicted grade, proctoring, dashboard «chi è
indietro». È la legge K-5 della costituzione, è scritto nei ToS ed è imposto tecnicamente:
nessun endpoint restituisce un punteggio per persona identificata. È ciò che tiene il prodotto
fuori dall'Allegato III dell'AI Act.

## Vision

A due o tre anni Kirchhoff non è «l'app dei circuiti». È il motore che dimostra che
l'astrazione **stato · trasformazione · layout · evidenza · verifier** regge fuori dai circuiti:
diagrammi a blocchi e controlli sono il candidato naturale, poi elettronica digitale, analisi
numerica, algebra lineare. Ogni dominio nuovo riusa il kernel e porta il proprio catalogo di
trasformazioni e il proprio profilo curricolare — ma solo dopo il gate, mai prima.

Il corpus verificato per corso e ateneo resta l'asset che nessuno ricostruisce in fretta, e il
canale B2B resta la base economica stabile sotto un prodotto consumer stagionale.

Il primo vero milestone è più modesto e più preciso di una visione: **un utente prende un
circuito strutturato, osserva cinque-dieci trasformazioni e dice, senza leggere un paragrafo,
«vedo esattamente cosa è cambiato, perché era consentito e come so che il nuovo circuito è
equivalente»** — e quando interrompe quel percorso proponendo un passo sbagliato sulla lavagna,
il sistema risponde sul sottografo reale.

---

## Decisioni aperte

Le dodici decisioni aperte del correct-course sono elencate nel piano master §27 e non vengono
duplicate qui. Quelle che toccano direttamente questo brief:

1. **Soglie di lancio di VVDR, SER e RRC** — owner-locked, non inferibili. `[§27.6]`
2. **Packaging B2C.** ⚠️ **Conflitto di piano aperto.** L'addendum §A5 dichiara scartato
   l'abbonamento mensile B2C per stagionalità estrema (picchi gen–feb e giu–lug, deserto ad
   agosto e novembre), sostituito da crediti prepagati e Pass Sessione. Il piano master §16.2
   rimette l'abbonamento mensile fra le opzioni B2C da testare, **senza rebuttare l'argomento
   stagionalità**. Non risolto qui: serve una decisione owner. L'invariante di billing —
   credito consumato solo su proof certificato, rifiuto che non consuma credito — non è in
   discussione ed è owner-locked.
3. **Primo profilo curricolare reale** e ateneo di partenza. `[§27.2]`
4. **Età minima.** 18+ al lancio, gate nei ToS; 14+ apre il segmento ITIS ma obbliga a
   un'informativa semplificata ex art. 4 L.132/2025. `[ASSUMPTION]`
5. **Nome e marchio** — «Kirchhoff» non verificato su TMview/UIBM. `[ASSUMPTION]`
6. **Dedizione.** Il piano assume che le ripetizioni continuino: finanziano lo sviluppo,
   forniscono il gold set e sono il primo cliente B2B. `[ASSUMPTION]`
7. **Regime IVA** (Merchant of Record vs OSS) — da confermare prima del primo incasso.
