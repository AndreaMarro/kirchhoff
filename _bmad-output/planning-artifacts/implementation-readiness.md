# Gate di prontezza all'implementazione — Kirchhoff

**Verdetto: CONCERNS.** Il piano è implementabile. Cinque rilievi: quattro decisioni che le storie
presuppongono e nessun documento registra, più un punto cieco di misura introdotto dal cambio di
rotta del 13 agosto (C5).

Data: 13 agosto 2026 · Eseguito da `bmad-sprint-planning`, `references/readiness-gate.md`.
**Aggiornato lo stesso giorno** dopo il cambio di rotta su Epic 1 — vedi
`sprint-change-proposal-2026-08-13.md`.

## Inventario del piano

| Artefatto | Stato | Note |
|---|---|---|
| `docs/00-fonte-piano-kirchhoff.md` | riferimento immutabile | Decisioni D1–D12 in testa |
| `briefs/brief-Kirchhoff-2026-08-13/brief.md` + `addendum.md` | `final` | Promosso da `draft` il 13 agosto |
| `prds/prd-Kirchhoff-2026-08-13/prd.md` | `final` | 35 FR, 7 UJ, 10 SM + 4 counter-metric |
| `ux-designs/ux-Kirchhoff-2026-08-13/DESIGN.md` + `EXPERIENCE.md` | `final` | 32 token, 8 componenti, 7 Key Flow |
| `architecture/.../ARCHITECTURE-SPINE.md` | `final` | 20 AD, lint pulito |
| `epics.md` | validato | 7 epiche, 40 storie (era 42 prima del cambio su Epic 1) |

Nessun tipo di documento manca. Non esiste un artefatto di test design, ma le storie non
dipendono da decisioni che solo lì potrebbero vivere: i criteri di accettazione sono
autoportanti.

## Tracciabilità

**In avanti.** 35/35 FR arrivano fino ai criteri di accettazione delle storie. 26/26 UX-DR sono
assegnati. 20/20 AD dello spine sono richiamati da almeno un criterio.

**All'indietro.** Nessuna storia orfana: ognuna cita l'FR, l'UX-DR o l'AD che realizza. Le uniche
storie senza un FR proprio sono 2.1 (struttura del progetto con controllo dei confini) e 3.5
(fondamenta del sistema di design) — entrambe risalgono a vincoli registrati, rispettivamente il
paradigma dello spine e il contratto UX.

**Conflitti fra artefatti.** Nessuno rilevato. Il caso a rischio era il vocabolario: il Glossario
del PRD, i nomi dei tipi nello spine e i termini di interfaccia in `EXPERIENCE.md` coincidono.

## Concerns

### C1 — Ateneo e corso del primo Profilo curricolare non decisi 🟠

**Dove vive il buco:** PRD §16 Q1.
**Chi ne dipende:** Story 2.9 (Profilo curricolare).
**Declassata da 🔴 a 🟠 il 13 agosto 2026.** Era bloccante perché le convenzioni del corso
determinavano l'annotazione del gold set fotografico, che precedeva tutto. Con l'insieme di
riferimento ora **strutturato e generato**, l'annotazione non dipende più da un corso reale: la
decisione serve solo quando si arriva a Story 2.9.
**Conseguenza se non risolto:** il Profilo predefinito diventa una scelta implicita — che è
esattamente ciò che FR-16 vieta.
**Chi lo chiude:** decisione dell'utente, prima di Story 2.9.

### C2 — "Ambiente di riferimento documentato" per LaTeX non esiste 🟠

**Dove vive il buco:** FR-18 lo cita, nessun documento lo definisce. Già rilevato dalla revisione
del PRD e rimasto aperto.
**Chi ne dipende:** Story 4.4, il cui criterio "il LaTeX compila senza intervento manuale
nell'ambiente di riferimento documentato" non è chiudibile finché l'ambiente non è nominato.
**Conseguenza se non risolto:** la storia non ha una definizione di fatto verificabile.
**Chi lo chiude:** `bmad-architecture` in modalità update — l'ambiente è un artefatto tecnico e
appartiene allo spine, non al PRD.

### C3 — Formati e-learning prioritari non scelti 🟠

**Dove vive il buco:** PRD §16 Q7. FR-18 dice "i formati di importazione delle piattaforme di
e-learning" senza nominarne uno.
**Chi ne dipende:** Story 4.4 e Story 6.4.
**Conseguenza se non risolto:** chi implementa sceglie un formato a caso e potrebbe non essere
quello del primo cliente B2B.
**Chi lo chiude:** decisione dell'utente, informata dal primo contatto outbound. Può aspettare
fino a Epic 6 — non blocca Epic 1–5.

### C4 — Soglia del limite di uso equo non fissata 🟡

**Dove vive il buco:** PRD §16 Q5. Il numero 150 è indicato come ipotesi.
**Chi ne dipende:** Story 5.4, che richiede che il piano dichiari il proprio limite **prima**
dell'acquisto.
**Conseguenza se non risolto:** il limite non è dichiarabile, quindi il criterio non è
verificabile.
**Chi lo chiude:** decisione dell'utente. Può aspettare fino a Epic 5.

## Ordine di risoluzione consigliato

**Nessuna delle quattro blocca più il primo passo.** Dopo il cambio del 13 agosto, Epic 1 non
richiede decisioni esterne: genera il proprio insieme di riferimento. Margini: C1 prima di Story
2.9, C2 prima di Epic 4, C3 prima di Epic 6, C4 prima di Epic 5.

Nessuna delle quattro giustifica un ulteriore `bmad-correct-course`: sono decisioni mancanti, non
conflitti fra artefatti.

---

## C5 — Punto cieco su SER, introdotto dal cambio del 13 agosto 🔴

**Dove vive il buco:** conseguenza diretta della decisione di saltare il gold set fotografico.
Dichiarato in PRD SM-1 e FR-34, in Epic 1 e nella proposta di cambio.

**Chi ne dipende:** SM-1 è la metrica bloccante del prodotto. Story 1.2 misura VSR e SER sulla sola
catena a valle dell'IR.

**Conseguenza:** l'errore silenzioso nasce quasi tutto nell'estrazione — leggere 30 Ω dove c'è
20 Ω — e i cinque controlli non lo intercettano, perché un circuito letto male è internamente
coerente e supera KCL, KVL e bilancio di potenza. Il prodotto può quindi arrivare in produzione con
la propria metrica di sicurezza cieca sul tratto più pericoloso.

**Non è un difetto del piano: è il prezzo di una decisione presa consapevolmente.** Sta qui perché
resti visibile invece di riemergere come sorpresa.

**Chi lo chiude, se si vuole:** un insieme fotografico anche piccolo — 30–40 immagini dai materiali
di ripetizione esistenti, non una campagna — è sufficiente a distinguere un SER dell'1% da uno del
10%.

