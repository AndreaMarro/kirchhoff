# Review di testabilità e misurabilità — Architecture Spine v2

**Lente:** testabilità e misurabilità. La domanda unica: *il giorno della verifica, da dove esce
ogni numero?*
**Oggetto:** `ARCHITECTURE-SPINE.md` (872 righe, 33 AD, `version: 2`, aggiornata il 15 agosto).
**Fonte vincolante:** `prds/prd-Kirchhoff-2026-08-13/prd.md` — §8, FR-34, FR-39, FR-41, FR-46,
FR-53, §7.0.1, §16 Q0.
**Letti per non ripetere:** `review-avversario.md`, `review-invarianti.md`, `review-confini.md`,
`review-veridicita.md`. Dove un mio rilievo tocca un loro rilievo lo dichiaro e dico perché la
mia affermazione è diversa.
**Letto in aggiunta, come controprova a valle:** `epics.md` (le storie non chiudono nessuna delle
lacune qui sotto; è ancora l'artefatto pre-v3 già segnalato da `review-veridicita.md` V5).

**Criterio di classificazione — dichiarato una volta e applicato senza eccezioni.** Per ogni
metrica di §8 ho cercato nella Spine tre cose: *chi la calcola* (un modulo nominato), *su quale
rappresentazione*, *in quale stadio*. Poi:

- 🟢 **fonte dichiarata** — la Spine nomina un modulo che produce quel numero;
- 🟡 **derivabile ma non assegnata** — esiste un artefatto con proprietario noto da cui il numero si
  ricava, ma nessun AD dice chi lo ricava né dove esce;
- 🔴 **nessuna fonte** — non esiste modulo, non esiste artefatto, o l'artefatto che servirebbe è
  vietato/non prodotto. Il giorno della verifica quel numero sarà calcolato a mano o inventato.

---

## Verdetto

**La Spine dichiara *chi calcola* e non dichiara *da dove arrivano i dati*. Su 30 metriche di §8,
20 non hanno alcuna fonte nominata — inclusa la metrica nord (VVDR) e inclusa SM-20, che il PRD
impone di leggere *prima* di RRC, VCER e SEC.** Le due misure meglio protette del documento —
VCER e la lettura umana di Gate A — sono anche le due che dipendono da artefatti che altri AD
dichiarano non persistiti o non serializzabili.

Non è un problema di completezza redazionale. È che AD-15 risolve una domanda («l'harness gira sul
codice di produzione») e ne lascia aperta un'altra della stessa taglia: **la pipeline non ha un
canale di osservazione tipizzato.** Ogni metrica che non sia una funzione dell'artefatto finale —
QPS, TTV, il costo di ri-layout, l'abbandono, il ripiego, le cinque misure di Gate A — non ha modo
di uscire dal sistema.

Nella Spine compaiono per nome **cinque** metriche di §8 su trenta: `SM-1` e `SM-2` (AD-15:330),
`SM-14`/`VCER` (AD-2:120, AD-15:339, 819), `SM-21` (AD-11:276,283 e AD-26:542), `SM-C3`
(AD-12:304). **Gli acronimi `VVDR`, `RRC`, `SEC`, `NED`, `TVR`, `VDR`, `VSR`, `QPS`, `TTV` non
compaiono mai.**

---

## 1. Tabella metrica → fonte

Colonna «Chi la emette» = ciò che la Spine dice, non ciò che sarebbe ragionevole. Dove dice nulla,
scrivo **nessuno**.

### Primary

| Metrica | Chi la emette (secondo la Spine) | Rappresentazione | Stadio | Stato |
|---|---|---|---|---|
| **SM-1 — SER** | `eval/` sulla parte trattenuta (AD-15:330 *Binds*, :333-335). La seconda metà della definizione — «e sulle segnalazioni» (prd:1493) — **non ha modulo**: la mappa capacità (845) manda FR-35 in `eval/`, che AD-15:333 definisce harness offline | `Published` contro verità annotata | dopo `publish()`, fuori linea | 🟢 parziale |
| **SM-2 — VSR** | `eval/` (AD-15:330) | `CircuitIR` + **evento di correzione umana, che non esiste**: nessun tipo in AD-8:231-238, e FR-9 è fuori MVP | ingest → publish | 🟢 nominale, numeratore non osservabile |
| **SM-3 — VVDR** ⭐ metrica nord | **nessuno.** Mai nominata nella Spine | `ProofGraph` interamente certificato / «problemi accettati» — **nessuno dei due è un tipo della Spine** | — | 🔴 |

### Metriche nuove della v3

| Metrica | Chi la emette (secondo la Spine) | Rappresentazione | Stadio | Stato |
|---|---|---|---|---|
| **SM-12 — NED** | **nessuno.** L'estrazione vive su `perception/` (AD-24:521-525, 809), che **non è la pipeline** che AD-15:333 autorizza `eval/` a invocare | ambigua fra `PerceptionCandidate<CircuitIR>` e `CircuitIR` promosso — due numeri diversi, il secondo filtrato dalla conferma umana | binario parallelo, Gate C | 🔴 |
| **SM-13 — TVR** | **nessuno.** `domain/validate` sta *prima* che una trasformazione esista (797); `domain/transform/check` (799) verifica solo insiemi di entità (AD-22:481-486). Nessun modulo rivalida `Cₖ₊₁` né calcola equivalenza sulle grandezze conservate (prd:1528-1530) | `CircuitIR(Cₖ)` ↔ `CircuitIR(Cₖ₊₁)` | dopo `transform`, stadio inesistente | 🔴 |
| **SM-14 — VCER** | `eval/` — **unica assegnazione esplicita del documento** (AD-2:120, AD-15:336-339, 819) | `LayoutIR(k)` + `LayoutIR(k+1)` + `Pₖ` | dopo `render/layout`, a posteriori | 🟢 (τ non definita: già rilevato da *invarianti* R4 e *avversario* C1; `LayoutIR` non persistito: T6) |
| **SM-15 — SEC** | **nessuno.** I sei campi che SEC conta (prd:400-401, 1543-1545) **non sono un tipo della Spine**; i sei componenti di AD-22:484-486 sono sei *altri* | non assegnata: né nodo né arco del `ProofGraph` | — | 🔴 |
| **SM-16 — RRC** | Il **controllo** ha proprietario — `render/roundtrip` (807, AD-19:407, AD-5:185-189) — la **metrica** no: nessuno conta, e il numeratore è ambiguo per la causa condivisa con AD-31 (T9) | SVG semantico → `ReconstructedCircuitIR` vs `CircuitIR` | dentro `publish()` | 🟡 |
| **SM-17 — VDR** | **nessuno, e strutturalmente bloccato**: AD-5:167-168 non serializza nulla che non sia `Published`, e il `Refusal` (forma degli errori, 645) non porta il `ProofGraph`. Una derivazione **completa ma non certificata** non lascia artefatto | `ProofGraph` completo, certificato o no | — | 🔴 |
| **SM-18 — Costo di ri-layout** | **nessuno.** Richiede il diff `LayoutIR(k)` ↔ `LayoutIR(k+1)`; il diagramma delle entità (775-789) non ha `LayoutIR` | coppia di `LayoutIR` | per passo | 🔴 |
| **SM-19 — Copertura causa di Rifiuto** | **nessuno** — e ≈1 per costruzione: AD-19:396-412 rende impossibile un Rifiuto senza causa e `subject`. Il segnale reale (degrado a `sanity` o a `Failure`) non è tipizzato (T10) | `Refusal` | dopo il gate | 🔴 |
| **SM-20 — Determinismo del rendering** | **nessuno — e nessun invariante lo rende vero** (T3) | SVG × SVG a parità di `LayoutIR` | `render/serialize` | 🔴 |
| **SM-21 — Lettura umana di Gate A** | `experiment/` (AD-11:290-300, 811, AD-26:542) — **per la reportistica aggregata.** Le cinque misure oggettive (prd:1373-1380) non hanno percorso di cattura (T7) | risposte del partecipante, di natura client-side | sessione sperimentale | 🟢 nominale / la parte oggettiva è di fatto 🔴 |

### Secondary

| Metrica | Chi la emette (secondo la Spine) | Rappresentazione | Stadio | Stato |
|---|---|---|---|---|
| **SM-4 — QPS** | **nessuno.** Il nodo `ask` esiste nel diagramma (726) ma non è un evento tipizzato; i log (648) portano solo `ir_id` e `stage` | conteggio di Domande mirate / Soluzione | `pipeline/` | 🔴 |
| **SM-5 — TTV** | **nessuno.** `ClockPort` (364) regola *chi legge* l'ora, non *chi emette* la durata; nessuna serie temporale, nessun p90 | durata ingest→publish | `pipeline/` | 🔴 |
| **SM-6 — Attivazione** | **nessuno.** Richiede funnel per soggetto entro 10 minuti; la convenzione di log (648) esclude dati identificativi e non definisce un canale alternativo | eventi per `subject_id` | trasversale | 🔴 |
| **SM-7 — Ritorno alla seconda soluzione** | **nessuno.** Stessa lacuna di SM-6 | eventi per `subject_id` | trasversale | 🔴 |
| **SM-8 — Correzioni per soluzione** | **nessuno.** Stesso evento mancante di SM-2 | `CircuitIR` + correzioni | disambiguazione | 🔴 |
| **SM-9 — Segnalazioni per mille** | **nessuno** (T13): FR-35 è assegnato a `eval/` (845), che è offline; nessuna entità «segnalazione» in AD-8, nessun ingresso in `api/` (816-818) | segnalazione utente | runtime | 🔴 |
| **SM-10 — Varianti per utente Studio** | Nessuno conta, ma l'artefatto ha proprietario: `studio` scrive `Variant` (AD-8:218, ER:786) | `Variant` | Studio | 🟡 |
| **SM-11 — Conversione conversazione → account** | Nessuno conta; l'evento esiste come operazione esplicita di dominio: fusione di soggetti (AD-20:432-433) | `subject_id` fusi | `api/assistant` | 🟡 |

### Counter-metrics

| Metrica | Chi la emette (secondo la Spine) | Rappresentazione | Stadio | Stato |
|---|---|---|---|---|
| **SM-C1 — Tasso di Rifiuto** | Nessuno conta; `REFUSAL` è persistito (ER:783) e `Refusal` è tipo di dominio (AD-13:317-319) | `Refusal` | dopo il gate | 🟡 |
| **SM-C2 — QPS al ribasso** | **nessuno.** Dipende da SM-4 (senza fonte) e dall'Accordo, che è uno stadio del diagramma (723) senza tipo d'uscita nominato | QPS + Accordo | `pipeline/` | 🔴 |
| **SM-C3 — TTV al ribasso** | AD-12:304 la nomina in *Binds*, ma AD-12 è una **guardia d'avvio** (`K ≥ 3`, 308-309), non una misura. TTV non ha fonte | TTV + numero di Pass | selezione modello | 🔴 |
| **SM-C4 — Copertura di dominio** | **nessuno.** Nessuna tassonomia dei tipi di circuito supportati esiste nella Spine | classi di circuito | — | 🔴 |
| **SM-C5 — Ampiezza del Catalogo** | Nessuno la dichiara come uscita, ma è la **meglio strumentata delle trenta**: il Catalogo è «un registro chiuso caricato all'avvio» (AD-2:105-106) — il numero è `len(registro)` ed è perfino imponibile all'avvio | registro delle Trasformazioni | avvio | 🟡 |
| **SM-C6 — Costo per prova verificata** | **nessuno.** `ModelPort` espone `extract`, `plan`, `narrate` (AD-3:131) e **non riporta consumo**; `LedgerPort` misura Crediti (ricavo), non costo fornitore | costo × derivazioni certificate | trasversale | 🔴 |
| **SM-C7 — Abbandono durante la conferma** | Nessuno conta; inferibile da righe `resume_ref` mai consumate (AD-6:198-199) più `stage` nei log (648) | sessione | disambiguazione | 🟡 |
| **SM-C8 — Illeggibilità del disegno** | **nessuno.** La geometria per calcolarla esiste in `render/` (AD-31:604-609), ma nessun AD assegna la misura — e sarebbe il renderer a misurare sé stesso, cioè l'autocertificazione che AD-22:474-479 vieta altrove | geometria dell'SVG | `render/` | 🔴 |
| **SM-C9 — Ripiego sul piano nodale** | **nessuno** (T11). Lo stato non esiste nella macchina a stati (720-736), non c'è campo sull'artefatto, e AD-33 non distingue i Badge | `Published` senza derivazione | `domain/solve` | 🔴 |

### Sintesi numerica

| Stato | Conteggio | Metriche |
|---|---|---|
| 🟢 fonte dichiarata | **4** | SM-1, SM-2, SM-14, SM-21 |
| 🟡 derivabile, non assegnata | **6** | SM-10, SM-11, SM-16, SM-C1, SM-C5, SM-C7 |
| 🔴 **nessuna fonte dichiarata** | **20** | **SM-3 (VVDR)**, SM-4 (QPS), SM-5 (TTV), SM-6, SM-7, SM-8, SM-9, SM-12 (NED), SM-13 (TVR), SM-15 (SEC), SM-17 (VDR), SM-18, SM-19, SM-20, SM-C2, SM-C3, SM-C4, SM-C6, SM-C8, SM-C9 |

---

## 2. Risposte brevi alle sette domande

1. **Da dove vengono i dati?** Tabella sopra. Venti metriche su trenta da nessuna parte. La causa
   comune è **T1**: non esiste un canale di osservazione. `eval/` è dichiarato *calcolatore* e mai
   *lettore*.
2. **Come si enumera una famiglia di test?** Non si enumera. La lista è fissa e scritta in
   AD-15:340-341, ma **nessun meccanismo la rende decidibile**: nell'albero (793-820) non c'è
   `tests/`, non c'è `scripts/`, e la convenzione «Test» (650) non nomina famiglie. Vedi **T5**.
3. **Pixel, DOM o grafo?** La Spine **non sceglie** (AD-23:511-513 dice solo «identico»), il PRD sì
   e dice **«byte per byte»** (prd:587). Peggio: l'unico canonicalizzatore che la Spine possiede
   confronta **grafi** (AD-5:171, prd:427), cioè è cieco alla proprietà che il test deve vedere.
   Vedi **T4**.
4. **Round-trip e incidenza.** Artefatto: SVG semantico. Esecutore: `render/roundtrip` (807).
   Fallimento: `Refusal.cause = render_roundtrip` — **ma la stessa causa copre due controlli
   diversi** (AD-31:609 e AD-19:407), quindi nessuna metrica li separa e AD-31 introduce una
   **seconda tolleranza senza proprietario**. Vedi **T9**.
5. **Le sei misure di Gate A.** `experiment/` esiste (811) e AD-11:290-300 protegge il confine, ma
   **non c'è percorso di cattura**: gli eventi sono di natura client-side, AD-8:238 dice che lo
   stato client non ha scrittore e non è persistito, non esiste `api/experiment` (816-818) né un
   port, e AD-11:293 vieta al token di entrare in «un'API di prodotto» — che è l'unico ingresso
   esistente. Vedi **T7**.
6. **Determinismo.** **No, la Spine non lo dichiara.** AD-2:105 vieta casualità e orologio alle
   *Trasformazioni*; AD-17:364 copre l'orologio ovunque; **niente copre `render/`**, e il *Deferred*
   (861) lascia aperto proprio l'algoritmo di piazzamento del braccio 0 — la famiglia di algoritmi
   che più spesso è randomizzata. Vedi **T3**.
7. **Contro-metriche.** Una sola (SM-C5) ha un artefatto pronto; due (SM-C1, SM-C7) sono derivabili;
   **sei su nove sono dichiarazioni d'intento senza strumentazione**, e due di esse — SM-C8 e SM-C9
   — nominano esattamente i due modi di far salire VVDR senza costruire il prodotto.

---

## 3. Rilievi

Ordine per severità. Ogni rilievo: cosa può divergere, e la **forma minima** della correzione.
`AD-1…AD-33` non si rinumerano: dove serve un AD nuovo, il primo libero è **AD-34**.

---

### T1 🔴 — La pipeline non ha un canale di osservazione, e AD-15 non se ne accorge

**File:riga.** `ARCHITECTURE-SPINE.md:328-343` (AD-15); `:61` e `:812` (i due elenchi dei port);
`:648` (convenzione di log); `:676` (OpenTelemetry nello Stack); `:845` (mappa capacità).

AD-15:336-337 impone all'harness di calcolare «**ogni** metrica di §8 … a ogni esecuzione». AD-15:333
dice *come* l'harness accede al sistema: «invoca la stessa pipeline attraverso gli stessi port,
sostituendo solo gli adapter». Queste due frasi insieme coprono soltanto le metriche che sono
**funzioni del valore di ritorno**. Tutte le altre — QPS (quante Domande mirate ci sono state),
TTV (quanto è durato), SM-18 (quanto layout è stato riscritto a ogni passo), SM-C7 (dove si è
fermata la sessione), SM-C9 (se c'è stato ripiego) — sono **osservazioni intra-pipeline**, e non
esiste il tipo che le trasporta.

Le prove che il canale non esiste, in ordine:

- L'insieme dei port è enumerato **due volte e in modo diverso**: `:61` dice
  «ModelPort, BlobPort, LedgerPort, SpicePort, **RenderPort**», `:812` dice
  «ModelPort, BlobPort, LedgerPort, **ClockPort**, SpicePort». Nessuno dei due contiene un port di
  osservazione. *(La divergenza `RenderPort` è già stata rilevata da* `review-confini.md` *R4 con un
  altro scopo — lì è il renderer come adapter; qui la cito solo come prova che l'elenco non è
  autorevole.)*
- `OpenTelemetry` sta nello Stack (`:676`) e **nessun AD lo governa**: non c'è una regola che dica
  cosa è una metrica, chi la emette, con quale schema, con quale identificatore di correlazione.
- L'unica riga che parla di uscita è la convenzione di log (`:648`): «Strutturati, con `ir_id` e
  `stage` su ogni evento della pipeline». Un log con due campi non è una fonte di metriche: non ha
  schema per unità, non ha esito, non ha durata. E la stessa riga chiude la porta a metà delle
  metriche secondarie — «mai dati identificativi» — senza dire come si misura allora SM-6, SM-7 o
  SM-11, che sono funnel per soggetto.

**Cosa può divergere.** Due unità entrambe conformi. L'unità *A* costruisce `eval/` come lettore
del solo artefatto finale: produce SER, VSR, RRC e nient'altro, e dichiara le altre «non
calcolabili offline» — coerente con AD-15:333. L'unità *B* costruisce un emettitore di eventi
dentro `pipeline/`, sceglie da sé il formato, e produce QPS e TTV — coerente con AD-15:336. Le due
non si accorgono l'una dell'altra fino al primo rapporto, quando lo stesso nome di metrica designa
due popolazioni diverse (per *A* «tutte le esecuzioni dell'harness», per *B* «tutto il traffico»).
E poiché nessuna delle due è sbagliata, il rapporto di Gate A avrà due colonne che non si sommano.

**Forma minima della correzione.** **Nuovo AD-34 — «Una metrica esce da un solo canale
tipizzato»**: nomina il port di osservazione, dice che ogni metrica di §8 è un'uscita tipizzata con
`ir_id`/`proof_graph_id` come chiave di correlazione, e che l'harness la **legge** invece di
ricostruirla. Più un emendamento di una riga ad AD-15: dopo «calcola ogni metrica» aggiungere *da
dove le prende*.

---

### T2 🔴 — AD-15 ridefinisce §8 come tredici metriche, e la metrica nord non è in nessuno dei due gruppi

**File:riga.** `ARCHITECTURE-SPINE.md:336-337`; `prd.md:1086-1087` (FR-34); `prd.md:1503-1507`
(SM-3).

AD-15:336-337: «l'harness calcola **ogni** metrica di §8 del PRD — *le quattro storiche più le nove
della v3* — a ogni esecuzione». L'inciso è presentato come glossa della prima clausola. È falso:
§8 contiene **21 metriche SM più 9 contro-metriche = 30**. «Le quattro storiche» sono SER, VSR,
QPS, TTV; «le nove della v3» sono l'elenco di FR-34 (prd:1086-1087): NED, TVR, VCER, SEC, RRC, VDR,
SM-18, SM-19, SM-20. Somma: **13**.

Il residuo non è materiale di contorno. Ne restano fuori:

- **SM-3 — VVDR, la metrica nord** (prd:1503). Non è «storica» (sostituisce «Soluzioni consegnate a
  settimana») e non è nell'elenco dei nove. È l'unica metrica del documento marcata ⭐ e in tutta la
  Spine **non compare né come `SM-3` né come `VVDR`**.
- **SM-21**, che AD-11 e AD-26 citano come vincolante ma che FR-34 non elenca fra i nove.
- **Tutte e nove le contro-metriche**, che per definizione sono il contrappeso delle prime.
- Le otto metriche secondarie SM-4…SM-11.

**Cosa può divergere.** Un implementatore che legge AD-15 come specifica di scopo costruisce
tredici calcoli e chiude la storia. Il controllo di completezza che AD-15 stessa promette — «una
metrica di §8 che l'harness non calcola è un difetto dell'harness» — passa, perché il difetto è
misurato contro l'inciso e non contro §8. **La contraddizione è dentro la stessa frase**, e
l'inciso è la parte azionabile.

**Forma minima della correzione.** Emendare AD-15 cancellando l'inciso, oppure sostituendolo con il
conteggio vero e con l'obbligo esplicito che l'elenco includa SM-3 e SM-C1…SM-C9. Una riga.
*Osservazione, non proposta di soglia:* se l'owner decide che una parte di §8 è fuori MVP, quella
decisione è di §8, non di AD-15 — la Spine non può restringere il PRD per apposizione.

---

### T3 🔴 — Il determinismo del rendering è misurato (SM-20) e non è imposto da nessun invariante

**File:riga.** `ARCHITECTURE-SPINE.md:99-106` (AD-2), `:360-366` (AD-17), `:803-808` (`render/`),
`:855-861` (*Deferred*); `prd.md:1558-1560` (SM-20); `prd.md:587` (FR-53).

Il paradigma si chiama «nucleo a pipeline deterministica» (`:7`, `:29`), ma l'unica regola che
vieta il non determinismo è AD-2:105 — «Nessuna I/O, nessuna sorgente di casualità, nessun
orologio» — e **vincola le Trasformazioni**, cioè `domain/transform`. AD-17:364 chiude l'orologio
per tutti. Restano scoperti, e tutti dentro `render/`:

- **la casualità**: nessuna regola la vieta a `render/layout` o `render/serialize`. Il *Deferred*
  (`:861`) lascia aperto proprio «l'algoritmo di piazzamento del braccio 0» — la famiglia
  force-directed / annealing è la scelta naturale, ed è randomizzata per costruzione;
- **l'ordine di iterazione**: lo stack è Python (`:665`); l'ordine di un insieme non è stabile fra
  processi. Il `LayoutPatch` è fatto di **insiemi di identificatori** (AD-2:114-118) e
  `reroute_scope` è «l'insieme dei rami». Serializzare in ordine d'insieme produce SVG diversi a
  parità di `LayoutIR`;
- **la forma canonica dell'uscita**: la parola «canonicalizza» compare solo sul percorso di
  *ingresso* (`:171` in AD-5, `:807` in `render/roundtrip`, `:796` in `domain/ir`). **Non esiste una
  forma canonica dell'SVG emesso** — né ordine degli attributi, né formato dei numeri in virgola
  mobile, né normalizzazione degli spazi.

**Cosa può divergere — e perché è la lacuna più costosa della lente.** SM-20 non è una metrica fra
le altre: prd:1558-1560 dice «Un renderer non deterministico rende RRC **non falsificabile**,
quindi si misura **prima** di leggere RRC, VCER e SEC». Se `render/` non è riproducibile:

- il test di FR-53 — «identico **byte per byte**» (prd:587) — fallisce in modo intermittente e
  verrà rilassato dalla prima unità che lo incontra, e con lui cade il test di A-0 (T4);
- il braccio 0 di Gate A non è riproducibile, e il braccio 0 è **la baseline che decide il
  verdetto**;
- ogni test di round-trip diventa instabile, esattamente come il committente sospetta.

**Forma minima della correzione.** **Nuovo AD-34/35 — «`render/` è riproducibile»**: estende la
clausola di purezza di AD-2 a `render/layout` e `render/serialize` (nessuna casualità non seminata,
nessun ordine dipendente dall'inserimento, forma canonica dichiarata dell'SVG emesso), e dichiara
che il seme del piazzamento del braccio 0 è **congelato e versionato** prima di eseguire Gate A —
cosa che il *Deferred* già chiede a mezza voce («va nominato e congelato prima di eseguire Gate A»)
senza legarla a un invariante. In alternativa, emendamento ad AD-18, che è l'AD che già separa
dominio e `render/`.

---

### T4 🔴 — «Togli l'overlay e il rendering è identico»: la Spine non dice a quale livello, e l'unico comparatore che possiede è cieco

**File:riga.** `ARCHITECTURE-SPINE.md:503-513` (AD-23), `:166-190` (AD-5), `:807` (`render/roundtrip`);
`prd.md:585-589` (FR-53), `prd.md:427` (FR-41), `prd.md:1284-1285` (§7.0.1).

AD-23:511-513: «**Il test è permanente** …: rimosso il `TransformOverlay`, il rendering delle entità
sottostanti è **identico** a quello senza trasformazione in corso.» Il PRD, sulla stessa frase, dice
di più: «il rendering delle entità sottostanti è identico **byte per byte**» (prd:587). **La Spine
ha lasciato cadere la qualificazione**, e con essa l'unica indicazione di livello esistente.

Tre livelli, tre test diversi:

| Livello | Cosa vede | Cosa serve |
|---|---|---|
| **pixel** | tutto, incluso l'anti-aliasing | rasterizzatore + tolleranza percettiva — nessuno dei due esiste nella Spine |
| **byte/DOM SVG** | colore, opacità, ordine dei layer | determinismo (T3) + forma canonica (T3) |
| **grafo** | topologia, **e nient'altro** | `render/roundtrip`, che già esiste |

**Il difetto è che il terzo è l'unico strumento che la Spine possiede** — AD-5:171 e prd:427
dicono che il confronto del round-trip è «di grafi, non di pixel e non di stringhe» — **e il grafo
non contiene lo stato visivo.** Un'implementazione che riusa il comparatore già scritto (la scelta
economicamente ovvia per l'unità che possiede `render/roundtrip`) ottiene un test che **passa anche
se l'entità preservata è dipinta di blu**. Cioè: il test permanente che deve distinguere
`style = blue` da `style = unchanged + overlay` (prd:1279-1285) diventa un test che quella
distinzione non può vedere. È teatro con un comparatore vero dentro.

**Seconda ambiguità, indipendente dalla prima.** «Il rendering **senza trasformazione in corso**»
ha due letture: *(a)* lo stesso `LayoutIR` reso con overlay vuoto — confronto stretto, legittimo a
livello di byte; *(b)* il rendering di `Cₖ₊₁` prodotto da un percorso che non ha mai avuto una
trasformazione — cioè **il braccio 0**, un `LayoutIR` diverso, che può differire legittimamente e
per il quale «identico» è falso a qualunque livello, sostituito da `≈` (che *invarianti* R4 ha già
mostrato essere indefinito). Le due letture sono entrambe grammaticali. Una dà un test rosso
sempre, l'altra un test verde sempre.

**Forma minima della correzione.** Emendare AD-23 aggiungendo alla *Rule* tre nomi: **l'artefatto**
(SVG semantico serializzato in forma canonica), **il livello** (quello che il PRD ha già scelto:
byte, che è possibile solo se T3 è chiuso), **il termine di paragone** (lettura *(a)*: stesso
`LayoutIR`, `TransformOverlay` vuoto). Tre nomi, una frase — ma senza T3 la frase non è eseguibile.

---

### T5 🟠 — «Tutte le famiglie passano» non è verificabile: la lista è fissa, il meccanismo di enumerazione non esiste

**File:riga.** `ARCHITECTURE-SPINE.md:340-343` (AD-15), `:650` (convenzione «Test»), `:793-820`
(albero), `:458` (`scripts/check_boundaries.py`); `prd.md:1115-1125` (FR-46).

Buona notizia: la lista **è** fissa e sta in un solo posto — AD-15:340-341 elenca sette famiglie
(unit, integration, property-based, metamorfiche, mutation, golden `ProofGraph`, visual
round-trip). Non è una convenzione di naming diffusa, e questo è un merito del documento.

Cattiva notizia: **niente dice come si constata che una famiglia c'è.**

- Nell'albero sorgente (793-820) **non esiste `tests/`**. Le sette famiglie non hanno domicilio.
- **Non esiste `scripts/`** nell'albero, benché AD-21:458 citi `scripts/check_boundaries.py` come
  file esistente. Il controllo di FR-46 non ha dove stare, e il recinto di AD-21 nemmeno.
- La convenzione «Test» (`:650`) parla solo di test di proprietà per Trasformazione: **non nomina
  le famiglie**, non definisce marcatori, non definisce cartelle.

**Cosa può divergere.** Tre unità, tre meccanismi: marcatori pytest (`@pytest.mark.metamorphic`),
cartelle (`tests/metamorphic/`), manifesto dichiarativo. Tutti e tre soddisfano «un controllo
elenca le famiglie presenti e fallisce se ne manca una» (prd:1121). E in tutti e tre **un solo test
banale per famiglia fa passare il controllo**: il controllo è di presenza, non di non-vacuità. È
esattamente il gate-teatro che la lente cerca.

Due difetti aggiuntivi dentro la stessa lista:

- **«mutation testing» non è una famiglia di test: è una tecnica che produce un punteggio.** Un
  controllo di presenza su mutation testing è soddisfatto dall'esistenza della configurazione, con
  zero mutanti uccisi. Il criterio di lettura manca. *(Non propongo una soglia: nessuna esiste in
  §8, e inventarla sarebbe la violazione che §16 Q0 vieta. Segnalo che il criterio manca e che la
  decisione è di chi possiede §8.)*
- **«golden `ProofGraph`» richiede un `ProofGraph` persistito e un formato di serializzazione
  stabile** — che non esistono (T6). E per FR-40 (prd:415-416) il golden deve contenere un caso
  con due branch che si richiudono, che «l'MVP non produce» (AD-29:581-582): quel golden va scritto
  a mano contro uno schema che il seed non contiene.

**Forma minima della correzione.** Emendare AD-15 aggiungendo alla *Rule* il **meccanismo** di
enumerazione (un registro dichiarativo versionato è la forma più verificabile: la famiglia esiste
se il registro la nomina e il registro punta a test eseguiti) e la clausola di **non-vacuità**. E
aggiungere `tests/` e `scripts/` all'albero (793-820), dove l'albero è già stato riscritto una
volta il 15 agosto per la stessa ragione.

---

### T6 🟠 — Il modello di persistenza è quello della v1: le rappresentazioni che le metriche v3 confrontano non hanno tabella

**File:riga.** `ARCHITECTURE-SPINE.md:775-789` (diagramma delle entità), `:231-243` (AD-8 emendata),
`:575-583` (AD-29), `:642` (convenzione identificatori).

AD-8 è stata emendata il 15 agosto proprio per chiudere «sette entità senza proprietario», e la
tabella (231-238) assegna oggi uno scrittore a `LayoutIR`, `TransformOverlay`, `ProofGraph`,
`Claim`, `SourceAsset`, `ProofSession`, `InteractionState`. **Il diagramma delle entità, dieci righe
più giù nello stesso documento, non è stato toccato**: contiene `USER`, `CIRCUIT`, `IR_VERSION`,
`PUBLISHED`, `STEP`, `REFUSAL`, `ARTIFACT`, `EXERCISE_BANK`, `VARIANT`, `SOLUTION_SHEET`,
`CURRICULUM_PROFILE`, `CREDIT_LEDGER`, `TENANT` — cioè il modello della v1.

*(Distinguo dal rilievo R4 di* `review-confini.md`*: quello riguardava l'**albero sorgente**, che è
stato riscritto — vedi la nota `:822-830`. Il **diagramma delle entità** no. E la mia affermazione
è diversa: non «i moduli non esistono», ma «le metriche non hanno su cosa girare».)*

Conseguenze dirette sulla misurabilità:

- **SM-18** confronta `LayoutIR(k)` con `LayoutIR(k+1)`: servono **due** layout leggibili dopo la
  fine della sessione. Nessuna tabella, nessuna dichiarazione di ritenzione.
- **SM-14 (VCER)** ha la stessa esigenza. È l'unica metrica con fonte dichiarata (AD-2:120) e la
  fonte punta a un artefatto che il modello persistito non contiene.
- **SEC** conta i sei campi di un passo: la relazione persistita è `PUBLISHED ||--|{ STEP` (784),
  cioè una **lista dentro il pubblicato** — mentre AD-29:583 dice che la derivazione è un grafo e
  che «la soluzione finale è l'ultimo nodo del grafo, non un campo a parte». Le due affermazioni
  descrivono due schemi diversi, e i golden `ProofGraph` di FR-46 non sanno quale versionare.
- **AD-8 pretende enforcement «a livello di permessi DB, non di convenzione»** (`:219`): su una
  tabella che non esiste, la regola non è applicabile — è la stessa obiezione che l'emendamento del
  15 agosto muove a sé stesso (`:226-228`).
- **La convenzione degli identificatori (`:642`) elenca quattro prefissi** — `ir_`, `sol_`, `var_`,
  `evt_` — per una dozzina di entità. AD-8:241 promette che l'artefatto di layout del braccio 0 ha
  «identità propria e **prefisso proprio**»: nessun registro lo contiene. Ogni metrica che
  congiunge rappresentazioni (VCER, SM-18) ha bisogno di identificatori stabili e distinguibili.

**Forma minima della correzione.** Riscrivere il diagramma delle entità come è già stato fatto per
l'albero, e aggiungere ad AD-8 una colonna «persistito / effimero / ritenzione» — la tabella la
menziona già per due righe (`TransformOverlay`: «non persistito»; `InteractionState`: «non ha
riga»), quindi si tratta di renderla sistematica. Più due righe alla convenzione `:642` per i
prefissi mancanti.

---

### T7 🟠 — Le cinque misure oggettive di Gate A non hanno percorso di cattura

**File:riga.** `ARCHITECTURE-SPINE.md:273-300` (AD-11 emendata), `:238` (AD-8, `InteractionState`),
`:540-550` (AD-26), `:654` (convenzione «Bracci»), `:811-818` (albero); `prd.md:1371-1384` (§7.0.1),
`prd.md:1561-1571` (SM-21).

Cosa la Spine **ha**: `experiment/` come pacchetto (811); il `ParticipantToken` per sessione
sperimentale, non congiungibile, cancellato a fine analisi (290-297); la reportistica aggregata per
braccio (295); i bracci come parametro di rendering (AD-26, e convenzione `:654`).

Cosa la Spine **non ha**: il percorso per cui una misura arriva da un partecipante a
`experiment/`.

Le cinque misure oggettive (prd:1373-1379) sono *tempo per indicare cosa è cambiato*, *errori
nell'indicare cosa è rimasto uguale*, *ricostruzione di `Cₖ`*, *tempo per trovare i nodi terminali*,
*errori nell'identità dei componenti*. Sono eventi di risposta cronometrati — la stessa natura di
`InteractionState`, del quale AD-8:238 dice: «**client**. Non è persistito lato server: non ha
riga, quindi non ha scrittore». E AD-21:455 aggiunge che la `ProofSession` non lo trasporta.

Quindi:

- **nessun port** per registrarli: né in `:61` né in `:812`;
- **nessuna superficie**: l'albero ha `api/http` (PWA e Studio) e `api/assistant` (816-818), niente
  di sperimentale;
- **AD-11:293 vieta** che il token «entri mai in un'API di prodotto» — e `api/http` è l'unico
  ingresso esistente. Un'unità conclude che le misure devono restare nel client (e SM-21 non si
  misura); un'altra conclude che un endpoint dedicato non è «un'API di prodotto» (e il token
  attraversa `api/`, cioè il confine che AD-11 esiste per proteggere). **Entrambe conformi.**
- **AD-8 non ha righe per le entità dell'esperimento**: né `ParticipantToken`, né la sessione con
  braccio e ordine di presentazione che la convenzione `:654` dichiara «registrato», né l'artefatto
  di layout del braccio 0 che AD-8:240-243 nomina senza dargli una riga. L'emendamento che ha chiuso
  «sette entità senza proprietario» ne ha lasciate fuori tre.

**Cosa può divergere.** Nel caso peggiore — che è anche il più probabile, perché è quello che
rispetta la lettera di AD-11 — le cinque misure oggettive si raccolgono **a mano**, con un
cronometro e un foglio, mentre la sesta (la preferenza, che prd:1383 dichiara **secondaria** e che
un braccio da solo non basta a vincere) è l'unica facile da raccogliere. È il modo esatto in cui un
gate a sei misure diventa un gate a una misura, e proprio quella che il PRD ha declassato.

**Forma minima della correzione.** Emendare AD-11 aggiungendo un quinto punto all'elenco
strutturale: `experiment/` ha un **ingresso proprio**, dichiarato non-di-prodotto, e la registrazione
delle sessioni A/B è un artefatto di `experiment/` che **non attraversa il dominio** — chiudendo
insieme la domanda 5 del committente. Più tre righe alla tabella di AD-8.

---

### T8 🟠 — TVR e VDR non sono «non assegnate»: sono strutturalmente non producibili

**File:riga.** `ARCHITECTURE-SPINE.md:797` e `:799` (albero, `validate/` e `transform/check/`),
`:474-501` (AD-22), `:166-168` (AD-5), `:390-412` (AD-19), `:645` (forma degli errori);
`prd.md:1528-1530` (SM-13), `prd.md:1549-1551` (SM-17).

**TVR (SM-13)** chiede due cose: che l'`IR` risultante superi la Validazione elettrica, e che sia
equivalente a quello di partenza sulle grandezze conservate. La Spine:

- colloca `domain/validate` **prima** che una trasformazione esista — il commento nell'albero è
  esplicito: «Validazione elettrica — **PRIMA** che esista una trasformazione» (`:797`), e AD-19:419
  lo ripete come motivazione dell'esistenza di `transform/check`;
- dà a `domain/transform/check` (`:799`) tre compiti soli — massimalità, identità, boundary — che
  sono proprietà di **insiemi di entità** (AD-2:117-118), non elettriche;
- **non nomina alcun modulo che calcoli equivalenza circuitale.**

Quindi nessuno stadio produce il predicato che TVR conta. Nota che il difetto è *simmetrico* a
quello che AD-19 ha appena chiuso: là mancava la causa per un rifiuto obbligatorio, qui manca lo
stadio per una misura obbligatoria.

**VDR (SM-17)** conta le derivazioni **complete, certificate o no** — ed è il denominatore che
rende VVDR interpretabile: «la differenza fra VDR e VVDR isola quanto si perde in certificazione
anziché in completamento» (prd:1550-1551). Ma AD-5:167-168 stabilisce che «Nessun tipo `Solution`
è serializzabile verso l'esterno: solo `Published` lo è», e il `Refusal` ha forma
`{code, message, subject}` (`:645`) più causa tipizzata (AD-19) — **senza riferimento al
`ProofGraph`**. Una derivazione che arriva in fondo e fallisce l'ottavo controllo **non lascia
traccia dell'essere arrivata in fondo**. Il numeratore di VDR non ha artefatto.

**Cosa può divergere.** Su TVR: un'unità la calcola rieseguendo `validate` a valle (e misura una
cosa), un'altra la assimila a `transform/check` (e ne misura un'altra, molto più alta, perché i
controlli di insieme passano quasi sempre). Su VDR: l'unica implementazione possibile senza
emendamento è **VDR = VVDR**, cioè la metrica collassa sul proprio numeratore e la differenza che
serve a leggere Gate A vale zero per costruzione.

**Forma minima della correzione.** Due righe in due AD esistenti. *(a)* AD-19 o AD-13: il `Refusal`
porta il riferimento al `ProofGraph` parziale — è già l'oggetto che AD-5 emendata attraversa nodo
per nodo, quindi esiste al momento del fallimento. *(b)* Albero + AD-22: nominare lo stadio di
rivalidazione post-trasformazione, o dichiarare esplicitamente che TVR è misurata da `eval/`
rieseguendo `domain/validate` su `Cₖ₊₁` — che è lecito, perché `eval/` non è uno stadio.

---

### T9 🟠 — Incidenza geometrica e round-trip condividono una causa: nessuna metrica li separa, e la tolleranza di AD-31 non ha proprietario

**File:riga.** `ARCHITECTURE-SPINE.md:596-611` (AD-31), `:400-412` (tabella cause di AD-19),
`:183-190` (tabella degli otto controlli), `:807`; `prd.md:427-433` (FR-41),
`prd.md:1546-1548` (SM-16), `prd.md:1801-1811` (§16 Q0).

Alla domanda 4 del committente la Spine risponde bene su tre punti su quattro: **artefatto** = SVG
semantico riparsato e canonicalizzato (AD-5:171); **esecutore** = `render/roundtrip` (`:807`, e
AD-19:407 gli attribuisce la causa); **esito del fallimento** = `Refusal`, che AD-13:317-318
distingue da `Failure` e che non consuma Crediti. Tutti e otto i controlli di AD-5:185-189 hanno
una causa in AD-19 — la domanda «esiste un controllo senza Rifiuto associato?» ha risposta
**no**. Questo va detto: è un risultato del lavoro del 15 agosto.

Il difetto è di **granularità**, e si vede solo dalla lente della misura:

- **AD-31:609 assegna all'incidenza geometrica la stessa causa del round-trip**
  (`Refusal.cause = render_roundtrip`), mentre la tabella di AD-19:407 descrive quella causa come
  «l'SVG riparsato non riproduce il `CircuitIR` atteso» — che dell'incidenza non parla. Due
  fallimenti con **soggetti diversi** (un filo che tocca il piedino sbagliato; un grafo che non
  corrisponde) e **una sola etichetta**.
- **RRC (SM-16)** è definita da FR-41:432 come alimentata dal fallimento **del round-trip**;
  l'incidenza non c'era quando la metrica è stata scritta. Un'unità conta solo i mismatch di grafo,
  un'altra conta tutto ciò che esce con `render_roundtrip`. Due numeri, stesso nome.
- Lo stesso appiattimento colpisce i controlli 1-3: KCL, KVL e bilancio di potenza confluiscono in
  `residual` (AD-19:403). **FR-34:1090 pretende «una ripartizione degli errori per tipo»**, e il
  tipo più fine disponibile è più grosso del controllo.
- **AD-31:605-606 introduce una tolleranza nuova** — «entro **tolleranza dichiarata**» — che
  **nessuno dichiara**. Non è nell'elenco owner-locked di §16 Q0 (prd:1801-1805), che nomina le
  soglie di lancio e la tolleranza su `p` di VCER, non questa. È un numero che decide il Badge e
  non ha proprietario. *(Non ne propongo il valore: segnalo che manca il proprietario e che manca la
  riga in §16.)*
- Minore, stessa famiglia: AD-31:610 dice che l'annotazione è derivata dalla geometria «**dove
  possibile**». La clausola di scampo non è misurata da nulla: nessuna metrica dice quanta parte
  delle annotazioni è derivata e quanta scritta a mano.

**Forma minima della correzione.** Una riga nella tabella di AD-19: causa distinta per l'incidenza
geometrica (il *Prevents* di AD-31 la descrive già come un difetto diverso). Più una frase in
AD-31 che dica **chi** dichiara la tolleranza e **dove** è registrata — o il rimando a §16 Q0 se
l'owner la avoca.

---

### T10 🟡 — SM-19 è vera per costruzione: la metrica misura ciò che AD-19 rende impossibile

**File:riga.** `ARCHITECTURE-SPINE.md:390-420` (AD-19, in particolare `:414-420`);
`prd.md:1556-1557`.

SM-19 è la «quota di Rifiuti che portano una causa localizzata e azionabile invece di un rifiuto
generico». AD-19:396-398 impone che ogni causa appartenga a un'enumerazione chiusa e porti
**sempre** `subject`. Dato AD-19, **un rifiuto generico non è costruibile**, quindi SM-19 vale 1 per
costruzione e non è falsificabile.

Il fenomeno che SM-19 vuole vedere esiste, ed è AD-19 stessa a descriverlo (`:417-418`): uno stadio
obbligato a rifiutare senza causa legale «degrada a **eccezione generica** o a **`sanity`** — e in
entrambi i casi l'utente perde la localizzazione». Sono due popolazioni osservabili: i `Refusal` con
causa `sanity` usata come discarica, e i `Failure` emessi dove sarebbe dovuto uscire un `Refusal`.
Nessuna delle due è tipizzata come tale.

**Cosa può divergere.** Un'unità riporta SM-19 = 100% (letteralmente vero, informativo quanto un
tautologia); un'altra la interpreta come tasso di `sanity` e riporta un numero completamente
diverso. Il rapporto di qualità contiene una riga che non significa niente e sembra ottima.

**Forma minima della correzione.** Una riga nella *Rule* di AD-19: `sanity` e la conversione
`Refusal→Failure` **contano come non localizzati** ai fini di SM-19. È un chiarimento di
misurazione, non un cambio di comportamento. Se invece la definizione della metrica va cambiata,
è decisione di §8, non della Spine.

---

### T11 🟠 — SM-C9 nomina un percorso silenzioso che la Spine non rappresenta: nessuno stato, nessun evento, nessun campo sull'artefatto

**File:riga.** `ARCHITECTURE-SPINE.md:718-736` (stadi della pipeline), `:176-190` (AD-5 emendata),
`:624-634` (AD-33); `prd.md:1626-1631` (SM-C9); `epics.md:688-692` (Story 2.10).

SM-C9 è la contro-metrica più specifica del PRD: quando il Piano didattico non trova una catena di
Trasformazioni, il sistema ripiega sull'analisi nodale e consegna «un calcolo corretto invece di una
derivazione disegnata — **con Badge pieno, perché i cinque controlli passano**», e prd:1630 chiede
che «il ripiego vada **misurato e dichiarato all'utente**, non nascosto dietro un Badge identico».

Nella Spine, del ripiego non c'è traccia:

- il diagramma degli stadi (718-736) mostra Percorso A e Percorso B **in parallelo**, entrambi verso
  `ver`. **Non c'è ramo di ripiego**: lo stato non è rappresentato, quindi non c'è transizione da
  contare;
- nessun campo distingue un `Published` con derivazione da un `Published` con solo calcolo. AD-33
  (624-634) governa se il Badge viaggia con la prova, **non di che tipo sia il Badge**;
- **AD-5 emendata non chiude la porta, la lascia aperta in modo più elegante**: il Badge si applica
  «se e solo se **ogni nodo** supera l'intera batteria» (`:181-190`). Un `ProofGraph` con **un solo
  nodo** — il risultato nodale — supera la batteria in modo banale e ottiene il Badge pieno. È
  esattamente il percorso che SM-C9 esiste per vedere, e la formulazione «ogni nodo» lo rende
  conforme;
- il ripiego **esiste già a valle**: `epics.md:688-692` (Story 2.10) dice «il sistema ripiega sul
  piano canonico nodale senza intervento manuale **e l'evento è registrato per l'analisi di
  qualità**». La storia registra un evento che la Spine non prevede e che nessun tipo trasporta
  (T1).

**Cosa può divergere.** Nel modo peggiore possibile: **non diverge affatto**. Due unità conformi
producono lo stesso Badge per due prodotti diversi, e la contro-metrica che dovrebbe accorgersene
non ha campo da contare. VVDR sale, il prodotto si svuota, e nessun numero lo dice.

**Forma minima della correzione.** Una riga in AD-5 o in AD-33: il `Published` porta la **natura
della prova** (derivazione visuale certificata / calcolo certificato senza derivazione), il Badge
riflette la natura, e SM-C9 conta quel campo. Non richiede nuovi moduli: richiede un campo e un
nome.

---

### T12 🟡 — SEC conta sei campi che la Spine non definisce, e i sei che definisce sono altri

**File:riga.** `ARCHITECTURE-SPINE.md:484-486` (AD-22), `:575-583` (AD-29), `:801-802`;
`prd.md:400-401` (FR-39), `prd.md:1543-1545` (SM-15).

FR-39 fissa la grammatica del passo: `BEFORE · ACTION · AFTER · EQUATION · CERTIFICATE ·
PROVENANCE`, «come **schema dati**». SEC è la quota di passi con tutti e sei compilati e non vuoti.

AD-22:484-486 fissa una sestina diversa: `PreserveSet + Delta + Boundary + LayoutPatch + Equation +
Certificate`, «ogni campo è non-vuoto o il prodotto non è costruibile». L'intersezione è di due
elementi. **`PROVENANCE` non ha alcun produttore nella Spine** — la «Marcatura di provenienza» di
AD-10 è un'altra cosa (riguarda gli artefatti esportati, non i passi). E nessun AD dice **quale
tipo** porta la grammatica: nodo del `ProofGraph`? arco? l'entità `STEP` del diagramma (784)?

**Cosa può divergere.** Un'unità che possiede `domain/transform` calcola SEC sui sei campi di AD-22
(e ottiene ~100%, perché AD-22 li rende obbligatori per costruzione). Un'unità che legge FR-39
calcola SEC sui sei di §8 e ottiene un numero più basso, con `PROVENANCE` sistematicamente vuoto.
Due denominatori, due popolazioni, stesso nome. E la clausola «un passo con `CERTIFICATE` assente è
un passo non provato» (prd:1545) perde mordente perché è l'unico campo che entrambe le letture
condividono.

**Forma minima della correzione.** Una riga in AD-29 (che possiede il `ProofGraph`): la grammatica
di FR-39 è portata dall'arco `Transform` del grafo, ed è **la stessa sestina** che SEC conta; se i
sei di AD-22 sono la realizzazione dei sei di FR-39, va scritta la corrispondenza campo per campo,
inclusa l'origine di `PROVENANCE`.

---

### T13 🟡 — FR-35 è assegnato all'harness offline: SM-9 e metà di SER non hanno ingresso

**File:riga.** `ARCHITECTURE-SPINE.md:845` (mappa capacità), `:328-343` (AD-15), `:231-238` (AD-8),
`:816-818` (albero `api/`); `prd.md:1107-1113` (FR-35), `prd.md:1493` (SM-1).

La mappa capacità dice: «Misurazione qualità (**FR-34, FR-35**) | `eval/` | AD-15, AD-1». Ma FR-35 è
la **segnalazione dell'utente dall'artefatto**: un ingresso online, che arriva da una superficie,
allega l'IR e l'identificativo della soluzione, e va scritto da qualche parte. `eval/` è, per
AD-15:333, l'harness che invoca la pipeline fuori linea. Nessuna entità «segnalazione» in AD-8,
nessuna rotta in `api/` (816-818), nessuno scrittore.

Ne discendono due buchi: **SM-9** interamente, e **la seconda metà di SM-1** — SER è misurata «sulla
parte trattenuta … **e sulle segnalazioni**» (prd:1493). La metà gold-set ha fonte; la metà campo
no. Dato che SM-1 è la metrica bloccante e che le segnalazioni sono l'unico canale che vede errori
su circuiti non presenti nel gold set, è la metà più informativa.

**Forma minima della correzione.** Una riga in AD-8 (entità `Report`/`Segnalazione`, scrittore
`api/`), e correggere la riga 845 della mappa separando FR-34 (`eval/`) da FR-35 (`api/` +
persistenza). *(La mappa ha anche il problema, già rilevato da* `review-confini.md` *R4, di non
avere righe per FR-36…FR-53: qui aggiungo solo che una delle righe esistenti è assegnata al modulo
sbagliato.)*

---

### T14 🟡 — Nessun port riporta il consumo: SM-C6 non è calcolabile e AD-12 governa un costo che non si misura

**File:riga.** `ARCHITECTURE-SPINE.md:125-132` (AD-3), `:302-310` (AD-12), `:812`;
`prd.md:1619-1621` (SM-C6).

SM-C6 è «costo di elaborazione diviso derivazioni visuali certificate», e serve a leggere VVDR:
«una VVDR che sale mentre SM-C6 esplode è un prodotto che non regge il proprio prezzo». Il
numeratore richiede il consumo dei modelli. `ModelPort` espone «`extract`, `plan`, `narrate` con
schemi di uscita vincolati» (AD-3:131) e **non riporta né token né costo**; `LedgerPort` misura
Crediti, cioè il lato ricavo. AD-12 disciplina la cascata economico→frontier senza che nulla misuri
l'effetto economico che la cascata esiste per ottenere.

**Forma minima della correzione.** Una riga in AD-3: il risultato di `ModelPort` porta il consumo
dichiarato dall'adapter, che è l'unico a conoscerlo — e resta fuori dal dominio, quindi non tocca il
paradigma.

---

### T15 🟡 — Il registro dei prefissi copre quattro entità su una dozzina

**File:riga.** `ARCHITECTURE-SPINE.md:642` (convenzione identificatori), `:240-243` (AD-8, braccio 0).

`ULID con prefisso per tipo (ir_, sol_, var_, evt_)`. Le entità che AD-8 riconosce oggi sono almeno
dodici, e AD-8:241 promette che l'artefatto di layout del braccio 0 ha «prefisso proprio» — che il
registro non contiene. Ogni misura che congiunge rappresentazioni (VCER fra `LayoutIR` e
`CircuitIR` attraverso `Pₖ`; SM-18 fra due `LayoutIR`; SM-21 fra braccio e sessione) ha bisogno di
identificatori distinguibili a vista in un rapporto. Correzione: estendere la riga `:642`. È
manutenzione, non progetto — la segnalo perché è la differenza fra un rapporto leggibile e un
rapporto in cui due colonne sembrano la stessa.

---

## 4. Cosa NON è un difetto (verificato e scartato)

- **«Il round-trip confronta grafi e non pixel» non è un difetto.** È la scelta giusta per la
  topologia (FR-41:427) e AD-31 ha aggiunto il controllo geometrico che mancava. Il difetto è
  altrove: quel comparatore è anche l'unico disponibile per un test che ha bisogno di vedere il
  colore (T4).
- **AD-15 «nessun ramo `if testing`» è forte e verificabile.** L'harness sul codice di produzione è
  la decisione che rende sensate SER e VSR. *(Il fatto che «sostituendo solo gli adapter» apra una
  porta sul renderer è già rilievo di* `review-confini.md` *R4 e non lo ripeto.)*
- **La lista delle famiglie di test è in un solo posto ed è chiusa** (AD-15:340-341). Il difetto è
  l'enumerazione, non la lista.
- **Ogni controllo di `publish()` ha una causa di Rifiuto** (AD-5:185-189 × AD-19:400-412). La
  domanda 4 del committente — «un controllo senza Rifiuto associato non può fallire in modo
  osservabile» — ha risposta negativa: non ce ne sono. Il problema è la granularità (T9).
- **`SM-C5` è imponibile, non solo misurabile**: il Catalogo chiuso caricato all'avvio (AD-2:106)
  permette di far fallire l'avvio se le Trasformazioni sono più di tre. È l'unica contro-metrica che
  la Spine potrebbe rendere impossibile da violare invece che da osservare.
- **Non ho contato come difetto la mancanza di soglie.** VVDR, RRC, TVR, VCER, SEC, VDR, SER e le
  tolleranze sono owner-locked (prd:1801-1811). Dove ho segnalato una tolleranza mancante (AD-31,
  T9) ho segnalato **l'assenza del proprietario e della riga in §16**, non l'assenza del numero, e
  non ho proposto valori.

---

## 5. Ordine di chiusura consigliato

Per costo crescente e per dipendenza, non per severità nominale.

| # | Rilievo | Forma | Perché prima |
|---|---|---|---|
| 1 | **T2** | cancellare un inciso in AD-15 | costa una riga e sblocca il conteggio corretto di ciò che resta da fare |
| 2 | **T3** | nuovo AD sulla riproducibilità di `render/` | **precondizione di T4**, e senza di esso ogni test di round-trip è instabile e il braccio 0 non è ripetibile |
| 3 | **T4** | tre nomi nella *Rule* di AD-23 | il test di A-0 è il test che decide se il prodotto ha ragione |
| 4 | **T1** | nuovo AD sul canale di osservazione | è la causa comune di 14 dei 20 buchi della tabella |
| 5 | **T7** | quinto punto in AD-11 + tre righe in AD-8 | senza, Gate A si decide sulla misura che il PRD ha dichiarato secondaria |
| 6 | **T6** | riscrivere il diagramma delle entità + colonna ritenzione in AD-8 | sblocca VCER, SM-18, SEC e la famiglia golden `ProofGraph` |
| 7 | **T8**, **T11** | una riga per AD (AD-19/AD-13; AD-5 o AD-33) | rendono osservabili i due modi in cui VVDR sale senza prodotto |
| 8 | **T5** | meccanismo di enumerazione in AD-15 + `tests/`, `scripts/` nell'albero | fino ad allora «tutte le famiglie passano» è una frase, non un esito |
| 9 | **T9, T10, T12, T13, T14, T15** | una o due righe ciascuno negli AD già esistenti | manutenzione di precisione, tutta a costo basso |

**La frase che riassume la lente.** Il documento è molto rigoroso su *chi ha il diritto di
affermare* e quasi muto su *chi ha il dovere di registrare*. Le due discipline hanno la stessa
forma — un solo scrittore, un solo punto di codice, nessun bypass — e la seconda non è stata
ancora scritta.
