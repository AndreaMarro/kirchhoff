# Costituzione Kirchhoff — K-0…K-5 e confini owner-locked

**Versione:** 1.0 · **Data:** 14 agosto 2026
**Stato:** `owner-locked` — modificabile solo da decisione umana esplicita, mai da un agente
**Fonte:** `docs/inbox/kirchhoff_01_piano_master_v3.md` §3 e §20
**Passo BMAD:** 1 di 8 nella catena di correct-course chain-top (§25.1 del piano master)

---

## Perché questo documento esiste

Il piano master introduce un cambio di categoria — da *«risolutore verificato»* a **Verified Visual
Reasoning Engine** — che tocca dominio, architettura, UX, metriche ed epiche. Un cambio di quella
portata ha bisogno di un punto fermo che venga **prima** di PRD, spine e storie, e che non si muova
mentre tutto il resto viene riscritto.

Questo è quel punto fermo. Ogni artefatto a valle vi si aggancia. Un artefatto che lo contraddice è
in errore, non in evoluzione.

---

## Le cinque leggi

### K-0 — Il circuito è il ragionamento

Nessun passaggio materialmente necessario alla comprensione può esistere **soltanto** come prosa o
formula quando dipende dalla topologia del circuito. Ogni trasformazione topologica produce uno
stato visuale verificato.

**Conseguenza operativa.** Un passo senza disegno non è un passo: è una riga di calcolo, e va fusa
con quella precedente. Il disegno non accompagna la derivazione — ne fa parte, e fa parte della
prova.

### K-1 — I modelli propongono, i sistemi deterministici certificano

VLM e LLM possono proporre letture, trasformazioni, classificazioni, spiegazioni e suggerimenti.
**Non** attribuiscono lo stato `Verified` e **non** sono la fonte autorevole dei numeri finali
quando esiste un calcolo deterministico.

**Conseguenza operativa.** Nessun `ModelPort` può concedere `Verified`, mutare la verità canonica
senza validator, inventare quantità mancanti, o dichiarare equivalente un sottografo senza un
verifier che lo dimostri.

### K-2 — Nessuna evidenza, nessuna affermazione

Ogni claim di dominio rilevante porta un riferimento allo stato, agli elementi e alla regola o al
verifier che lo sostengono.

**Conseguenza operativa.** Il claim è un tipo, non una frase:

```text
Claim
├── claim_type
├── state_id
├── subject_ids
├── evidence_ids
├── verifier_id + version
└── status
```

### K-3 — Il rifiuto è un output valido

Se una lettura, una trasformazione o una derivazione non può essere certificata, il sistema
**rifiuta di certificare senza inventare**. Il rifiuto è progettato, non è un errore di UX.

**Conseguenza operativa.** `Refusal` e `Failure` restano tipi distinti su canali distinti. Il
rifiuto non consuma crediti. Il tasso di rifiuto è una counter-metric: non va portato a zero.

### K-4 — La prova è ispezionabile

Badge e certificazioni **devono aprirsi** sulla prova: residui, mappatura dei terminali,
cross-check, provenance, versioni dei verificatori.

**Conseguenza operativa.** Un badge che non si apre è un'affermazione. Un badge che si apre è una
prova — ed è l'unica cosa che un modello generalista non può disegnare.

### K-5 — Interazione con lo studente senza punteggio sulla persona

Kirchhoff può osservare errori e tentativi legati a un esercizio e usarli per adattare una
spiegazione. Il prodotto standard **non** li trasforma in voto, rank, probabilità di successo,
profilazione valutativa o decisione educativa sulla persona.

**Conseguenza operativa.** Vietati nel prodotto standard: ability score, predicted grade, ranking,
placement automatico, punteggi di proctoring o anti-copiatura, punteggi per persona rivolti al
docente. Il tutor spiega l'errore sul passo corrente; non valuta chi l'ha fatto.

---

## Confini owner-locked

Dal piano master §20. Il principio che li giustifica, testuale:

> «Un sistema che può modificare autonomamente il proprio standard di verità non è automigliorante:
> è epistemicamente incontrollato.»

### Gli agenti possono modificare da soli

Codice · prompt · routing dei modelli · euristiche di layout · UX · performance · ranking delle
trasformazioni · politica dei suggerimenti · test non protetti.

### Richiedono decisione umana o BMAD chain-top

| Confine | Perché è bloccato |
|---|---|
| **Definizione di `Verified`** | È il prodotto. Un sistema che si ridefinisce cosa significa "verificato" ha smesso di essere verificabile. |
| **Dataset held-out** | Guardarli invalida ogni misura successiva, e nessuno se ne accorge. |
| **Soglie di qualità minima** | Abbassare una soglia è il modo più rapido per far passare una storia rotta. |
| **Invarianti di privacy** | Retention, minimizzazione, consenso: obblighi di legge, non parametri. |
| **Confine AI Act** | Il divieto di funzioni valutative è ciò che tiene il prodotto fuori dall'Allegato III. |
| **Invarianti di billing** | Idempotenza e consumo solo su proof certificato. |
| **Retention massima** | Limite superiore dichiarato, mai estendibile da un agente. |
| **Counter-metrics** | Esistono per impedire l'ottimizzazione della cosa sbagliata: un agente che le rimuove rimuove il freno. |
| **Questa costituzione, K-0…K-5** | Se il loop può riscriverla, non è più un vincolo. |

### Regola di collisione

Un agente che incontra un criterio di accettazione, un rilievo di revisione o una proposta di
ottimizzazione che richiede di violare un confine owner-locked **si ferma e lo segnala**. Non
sceglie. Non aggira. Non chiede scusa e procede.

È un conflitto di piano, e si risolve con `bmad-correct-course` — non nel codice.

---

## Il gate di veridicità non è una skill esterna

Dal piano master §19: il gate di veridicità **non deve dipendere da una skill esterna dentro la
trusted computing base**. Va implementato come componente proprietaria e versionata, con il tipo
`Claim` di K-2.

Le skill di disciplina conversazionale restano utili per come si lavora. Non sono il gate del
prodotto, e nulla che il prodotto certifica può dipendere dalla loro presenza.

---

## Cosa questa costituzione non decide

Deliberatamente fuori: scelte di stack, ordine delle epiche, prezzi, provider di modelli,
denominazione commerciale, confine esatto fra Kirchhoff core e Simulation Plugin di Ardesia.

Sono decisioni di piano, e cambiano. Le cinque leggi no.

---

## Storia delle modifiche

| Versione | Data | Cambio | Autorizzata da |
|---|---|---|---|
| 1.0 | 2026-08-14 | Prima stesura, da piano master §3 e §20 | Andrea |
