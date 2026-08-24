# Loop Kirchhoff v3 — correct-course chain-top, poi Visual Proof Kernel

Il prodotto è cambiato di categoria: da *risolutore verificato* a **Verified Visual Reasoning
Engine**. Il piano è in `docs/inbox/kirchhoff_01_piano_master_v3.md`. La costituzione è in
`docs/02-costituzione-kirchhoff.md` ed è **owner-locked**.

**Una unità di lavoro per iterazione. Contesto fresco ogni volta. Stato solo su disco.**

---

## FASE 1 — Finire la catena BMAD, prima di scrivere codice nuovo

Il piano master §25.1 dà otto passi. Il primo è fatto. **Non si costruisce Gate A finché la catena
non è chiusa**: le epiche attuali descrivono un prodotto che non è più questo.

<!-- BMAD-CHAIN:START -->
<!-- generato da scripts/bmad_chain.py — non modificare a mano: `uv run python scripts/bmad_chain.py rendi` -->

| # | Passo | Skill | Stato | Prova |
|---|---|---|---|---|
| 1 | Costituzione K-0…K-5 | `—` | ✅ 08-14-2026 12:20 · dedotto dalle prove su disco | ✓ 02-costituzione-kirchhoff.md «K-5»; 02-costituzione-kirchhoff.md «owner-locked» |
| 2 | Brief update | `bmad-product-brief (update)` | ✅ 08-14-2026 12:20 · dedotto dalle prove su disco | ✓ brief.md «version: 3»; addendum.md «H. Delta v3» |
| 3 | PRD v3 | `bmad-prd (update)` | ✅ 08-15-2026 03:43 · PRD v3 · MVP = Visual Proof Kernel · reviewer gate pendente | ✓ prd.md «version: 3» |
| 4 | UX Pro update | `bmad-ux + ui-ux-pro-max:design-system` | ✅ 08-15-2026 05:19 · UX v3: KF-0 journey owner, protocollo A/B, estetica scura Linear-like | ✓ DESIGN.md «version: 3»; EXPERIENCE.md «version: 3» |
| 5 | Architecture Spine v2 | `bmad-architecture (update)` | ✅ 08-15-2026 05:56 · Spine v2: AD-21..AD-30, quattro AD emendati in loco, lint 0 rilievi | ✓ ARCHITECTURE-SPINE.md «version: 2»; ARCHITECTURE-SPINE.md «LayoutPatch» |
| 6 | Ribilanciamento epiche → Gate A–G | `bmad-create-epics-and-stories` | ✅ 08-24-2026 19:36 · Epiche ribilanciate su Gate A-G: 10 epiche per esito utente, 53/53 FR mappati, 64 storie, percorso critico 15 | ✓ epics.md «Gate A»; epics.md «Gate G» |
| 7 | Readiness gate | `bmad-sprint-planning (readiness)` | ✅ 08-24-2026 19:39 · Readiness gate eseguito. Verdetto CONCERNS: 4 rimedi nominati (project-context, emendamenti AD-8/21/22, PRD su FR-44, Story 0.1). Pronte adesso: 0.1, 1.2, 1.4, 1.9 - nessuna e' la prima del percorso critico | ✓ implementation-readiness.md «version: 3» |
| 8 | Ship loop | `.claude/loop.md` | ✅ 08-14-2026 12:20 · dedotto dalle prove su disco | ✓ loop.md «BMAD-CHAIN:START»; loop.md «BMAD-CHAIN:END» |

<!-- aggiornata: 08-24-2026 19:39 -->
<!-- BMAD-CHAIN:END -->

**Una iterazione = un passo.**

### Questa tabella non si edita a mano

Il 14 agosto il passo 2 era chiuso alle 07:41 e la tabella diceva ancora `⬜`: una
ripartenza avrebbe rifatto il lavoro da capo. Uno stato che vive in una tabella Markdown
dipende dalla memoria di un contesto fresco, e quella memoria non c'è.

Adesso lo stato sta in `_bmad-output/planning-artifacts/bmad-chain-status.json`, lo scrive
`scripts/bmad_chain.py`, e la tabella qui sopra è **generata**. Ogni passo ha una **prova**:
un artefatto sul disco che porta il suo timbro — la convenzione è `version: 3` nel
frontmatter, quella che `brief.md` usa già. Il tracciatore confronta il dichiarato col
provato e fallisce in **entrambe** le direzioni:

| Dichiarato | Prove | Verdetto |
|---|---|---|
| `done` | assenti | ✗ dichiarato senza prova — non si spunta un passo non fatto |
| ≠ `done` | presenti | ✗ **fatto e non tracciato** — il difetto del 14 agosto, ora rilevato |

La seconda riga è ciò che rende il meccanismo a prova di dimenticanza: emerge anche se il
comando di chiusura non viene eseguito affatto, perché `verifica` gira all'inizio di ogni
iterazione. Modificare la tabella a mano fa fallire `rendi --controlla` e la suite.

```bash
uv run python scripts/bmad_chain.py stato                      # dove siamo
uv run python scripts/bmad_chain.py verifica --con-loop        # esce 1 se diverge
uv run python scripts/bmad_chain.py segna --passo 3 --stato done --nota "..."
```

`segna` **rifiuta** `done` senza prove. Se la prova non è applicabile, `--forza --motivo
"..."` la registra e la lascia a vista come `⚠️` nella tabella: visibile, non silenziosa.

### Cosa deve entrare nei documenti

- **`CircuitIR` e `LayoutIR` distinti.** Il primo è la verità elettrica, il secondo la verità visuale
  persistente. Il renderer non re-inferisce il circuito dal layout; non si rifà il layout globale a
  ogni passo.
- **`ProofGraph`**, non lista lineare: sovrapposizione, Thévenin su sottoproblemi e transitori
  creano branch e join.
- **`LayoutPatch`** con `preserve/remove/create/node_mapping/reroute_scope`. Vincolo:
  `p_{k+1}(x) = p_k(x)` per ogni `x` in `preserve`.
- **Grammatica obbligatoria di ogni passo:** `BEFORE + ACTION + AFTER + EQUATION + CERTIFICATE +
  PROVENANCE`. È schema dati, non presentation design.
- **Visual round-trip:** SVG semantico con `data-component-id`/`data-terminal-*` → riparsa →
  `ReconstructedCircuitIR` → canonicalizza → confronto esatto di grafi. Il controllo primario **non**
  è un VLM che dice "sembra giusto".
- **Metriche nuove** accanto a SER e VSR: NED, TVR, VCER, SEC, RRC, VDR. North star **VVDR** =
  derivazioni visuali interamente certificate / problemi accettati.
- **Tre adapter, un kernel:** Web/API · MCP e MCP Apps · Ardesia. Nessun fork "Kirchhoff per Ardesia".

### Cosa si riusa e non si ridiscute

Dal piano §25.2, verificato sul disco: solver deterministico, aritmetica esatta su `Fraction`,
oracolo con verifica indipendente, harness ed eval, ports-and-adapters, i cinque controlli,
semantica del rifiuto, disclosure e provenance. **159 test verdi, copertura 100%.** Non si tocca.

---

## FASE 2 — Gate A, il Visual Proof Kernel

Solo a catena chiusa. Ingresso **strutturato**, non foto.

Trasformazioni iniziali: serie · parallelo · partitore · Millman · Thévenin/Norton semplice.

**Kill criterion:** se la continuità visuale non è chiaramente migliore di un re-layout completo,
**non espandere il catalogo**. Bastano serie, parallelo e partitore per saperlo. Se non regge,
fermati e segnalalo: tutto il resto poggia su questo.

Poi in ordine: **B** tutor e lavagna · **C** perception · **D** distribuzione · **E** ricavo ·
**F** Ardesia · **G** secondo dominio.

---

## Come si lancia — il costo fisso dell'iterazione

Misurato altrove, stessa macchina: **92 plugin abilitati su 300 installati costano 46 943 token di
`cache_creation` e $0,479 per rispondere «ok»** — prima di qualunque lavoro, a ogni iterazione.
Tabella completa e fonti in `docs/04-ricerca-token-e-automiglioramento.md` §2.1.

```bash
cd ~/MATJOURNEY/kirchhoff && ECC_GATEGUARD=off caffeinate -ims claude \
  --dangerously-skip-permissions \
  --setting-sources project,local \
  --plugin-dir <solo quelli che servono davvero> \
  --max-budget-usd <tetto>
```

- `--setting-sources project,local` + `--plugin-dir` mirati: **12 218 token, $0,1451** — 3,3× meno.
- `--strict-mcp-config` **non serve**: misurato 46 958 contro 46 943. Risultato negativo, non
  riprovarlo.
- ⚠️ **Un `--plugin-dir` inesistente esce 0 e il comando gira senza quella skill, in silenzio.**
  Fallisce aperto. Prima di lanciare: `ls -d <ogni percorso>` e leggi l'exit.

**La cache può rompersi senza dirlo.** Ogni breakpoint cammina indietro al massimo 20 blocchi di
contenuto; un turno con molte coppie `tool_use`/`tool_result` lo supera e il breakpoint successivo
non trova nulla. Sintomo: `cache_read_input_tokens` a **zero** su turni ripetuti. Nessun errore
visibile, si paga tutto a prezzo pieno.

### Modello ed effort — deciso, non aperto

Abbassare l'effort è «l'unico margine reale non sfruttato» misurato, ma **non si applica in modo
uniforme**. Decisione owner del 15 agosto: *dipende se usiamo agenti; se no, Opus 5 Max*.

**Topologia degli agenti — decisione owner del 24 agosto, seconda revisione.** Sostituisce sia la
tabella a tre righe sia l'albero a diciassette agenti: entrambi allocavano il modello più costoso a
lavoro che non lo richiede.

Il principio non è «il modello più forte dove conta». È **escalation su rischio misurato, con i test
deterministici come giudice finale**.

```
                        BMAD — stato, dipendenze, gate
                                     │
                        classificatore di rischio
                          (deterministico, non LLM)
                                     │
          ┌──────────────────┬───────────────────┬──────────────────┐
          │                  │                   │                  │
         R0                 R1                  R2                 R3
      routine             normale            critica          chain-top
          │                  │                   │                  │
    Sonnet 5 high      Opus 5 xhigh        Opus 5 max        Opus 5 max
                                                                   +
                                                             Fable 5 max
                                                          (analisi parallele)
          └──────────────────┴───────────────────┘                  │
                             ▼                                      │
                       TEST + GATE                                  │
                    l'unica certificazione                          │
                             │                                      │
              ┌──────────────┴───────────────┐                      │
              │                              │                      │
        R0 · R1                          R2                         │
    Opus 5 high, contesto fresco   Fable 5 max, contesto fresco     │
         Blind Hunter                  Blind Hunter                 │
              │                              │                      │
              └──────────────┬───────────────┘                      │
                             ▼                                      ▼
                   i rilievi tornano a Opus                conclusioni a confronto
                   che li corregge — mai al                        │
                   revisore che li ha trovati            owner se il disaccordo resta
                             │
                       TEST + GATE
                             │
                          commit
```

**Il livello di sotto: Sonnet 5 fa il volume, anche dentro una storia di Opus.**

```
                       Opus 5 — proprietario della storia
                      /              |              \
            Sonnet 5 ricerca   Sonnet 5 test    Sonnet 5 evidenza
                      \              |              /
                          Opus 5 integra e decide
```

Ricerca nel repository, lettura di documenti, inventario, esecuzione dei test, triage di log
semplici, tracciabilità, fixture, ricevute di evidenza: **Sonnet 5**. Non si spende Opus per trovare
quaranta riferimenti a `LayoutIR`, e non si spende Fable per niente di tutto questo. **Opus resta
proprietario della storia**, i sottoagenti no.

| Funzione | Modello | Effort |
|---|---|---|
| Instradamento e eleggibilità delle storie | **nessun LLM** | deterministico |
| Search-before-build, inventario, lettura documenti | Sonnet 5 | medium/high |
| Esecuzione test, triage di log, tracciabilità, ricevute | Sonnet 5 | medium/high |
| Implementazione ordinaria | **Opus 5** | **xhigh** |
| Debug difficile, refactor architetturale | Opus 5 | max |
| Review indipendente ordinaria, contesto fresco | Opus 5 | high |
| Review di storia critica — Gate A, IR, `Verified` | **Fable 5** | **max** |
| Arbitraggio di un disaccordo reale | Fable 5 | max |
| Analisi owner-locked | Fable 5 **+ persona** | max |
| **PASS/FAIL** | **nessun LLM** | codice deterministico |

**Cosa fa scattare R2**, e sono trigger oggettivi, non giudizio: modifica di `CircuitIR` · un AD ·
la definizione di `Verified` · semantica di `Refusal` · `PreserveSet` · `Delta` · semantica del
renderer · `ProofGraph` · holdout ed eval · semantica del primo errore · Gate A · privacy o
sicurezza · rottura di un contratto pubblico.

**R3 esiste ed è raro.** Modificare `Verified`, un kill criterion, la costituzione, l'identità
semantica, o qualcosa che invaliderebbe Gate A. Lì **due analisi indipendenti in parallelo**, Opus e
Fable, e se le conclusioni divergono decide una persona. Non un agente solo.

**Tre regole che la topologia non può violare.**

1. **Il revisore non vede il ragionamento dell'implementatore.** Riceve storia, criteri di
   accettazione, contesto di progetto, diff, test e riferimenti architetturali. **Non** «ho scelto
   così perché». `50-Lezioni-loop/Il revisore che rivede sé stesso.md`: *«Non trova i propri errori
   perché l'errore sta nel modello mentale che ha prodotto entrambi»* — e qui pesa più che altrove,
   perché **Kirchhoff vende la verifica indipendente**. Contesto fresco anche quando il modello è lo
   stesso: elimina l'impegno verso l'approccio già scelto, che è la metà del difetto.
2. **Chi trova un rilievo non lo corregge.** Il finding torna a Opus, che implementa; poi test e
   gate; poi il revisore rivede. Un revisore che ripara il proprio rilievo e poi dichiara corretta
   la propria riparazione ha chiuso il cerchio su sé stesso.
3. **Il modello propone, il sistema certifica.** `pytest`, coverage di dominio, recinti, oracolo di
   mutazione, round-trip semantico, Gate A e VCER, disciplina dell'holdout **restano gli arbitri**.
   Un modello può dire «vedo un possibile difetto»; non può dichiarare una storia `done`. È K-1,
   applicato al loop che costruisce il prodotto che lo vende.

**Il rischio che i refutatori introducono, misurato altrove.**
`50-Lezioni-loop/Il refutatore è un imputato.md`: su 1 302 traiettorie annotate da esperti,
**nessun giudice LLM supera il 70% di precisione**, e la valutazione a regole **sottostima il
successo del 16,7-18,5%**. Prima di riscrivere ciò che una review boccia, **prendere a mano un
campione dei rifiuti e misurare quanti erano validi.** Un gate che boccia tutto non misura niente,
come uno che resta verde sotto mutazione.

**Quattro vincoli che questa topologia eredita da misure già prese**, non da benchmark importati.
Tutte in `docs/04-ricerca-token-e-automiglioramento.md`.

- **§2.4 · D-4 — «la leva del risparmio token, trovata e non applicata».** Registrata alla lettera:
  *«Il loop gira tutto a `--effort max`. Non applicato.»* Era già indicata come **l'unico margine
  reale non sfruttato**. Questa topologia **è** la sua applicazione: `xhigh` come default e `max`
  come escalation, non `max` ovunque. Non è una scelta di costo importata da fuori — è un difetto
  del nostro loop, misurato qui, finalmente chiuso.
- **§2.5 · l'oracolo costa zero token, e il revisore non parte prima.** Architettura obbligatoria
  `Worker → LocalChecks → Verifier`, dove *«LocalChecks esegue l'oracolo a costo zero token»* e il
  revisore **non parte mai** su un diff che non lo passa — stato `BLOCKED_BEFORE_REVIEW`. E il
  tetto misurato: **una review più una riparazione**, poi escalation. Il modello più costoso non
  legge mai un diff che un test da zero token avrebbe già bocciato.
- **§2.4 · il parallelo vale per chi cerca e per chi confuta, mai per chi scrive.** Dieci passi in
  tre tracce parallele portano l'affidabilità end-to-end **dal 60% all'81-86%**, *«ma solo ricerca e
  confutazione, mai i writer»*. Da qui i Sonnet in parallelo sotto Opus e i refutatori in parallelo,
  e **un solo implementatore per storia**.
- **§2.6 · il segnale di stop deve venire da fuori dall'agente.** Misurato: sulle traiettorie fallite
  i modelli prevedevano **oltre il 70% di fattibilità dopo aver bruciato il 60% del budget**, e
  l'arresto precoce ha risparmiato **il 28-64% dei token** al costo di 1,6-4,2 punti di successo.
  *«Non è un principio: è la conseguenza operativa di un bias ottimistico misurato su ogni modello
  di frontiera testato.»* Per questo l'escalation la decide il router deterministico, non
  l'implementatore che dichiara di potercela fare.

**Cosa invece non è misurato qui, e va detto.** La distanza di capacità e di prezzo fra Opus 5 e
Fable 5, e il posizionamento di Sonnet 5 come strato di esecuzione, vengono da fonti esterne
dell'owner: **in questo repository non sono stati misurati**, e non vanno citati come se lo fossero.
Valgono da inizializzazione del router, non da verdetto.

**La scadenza.** Dopo 20-30 storie reali il loop calcola per modello: tasso di successo al primo
passaggio, resa delle review, costo per storia, latenza, regressioni trovate, rilievi falsi. **Il
router si ritara su quei numeri.** I benchmark esterni scelgono da dove partire; il nostro eval
sceglie dove restare — ed è la stessa disciplina che §2.1 ha già applicato al costo fisso
dell'iterazione, portandolo da $0,479 a $0,1451 per rispondere «ok».

**Instradamento delle storie oggi in backlog**, come inizializzazione:

| Storia | Implementazione | Review |
|---|---|---|
| 0.1 preflight del runtime BMAD | Opus 5 xhigh | Opus 5 high |
| 0.2 doctor · status · dry-run | Opus 5 xhigh | Opus 5 high |
| 0.3 run · resume | Opus 5 max | Fable 5 max |
| **1.1 identità semantica** | Opus 5 max | **Fable 5 max** — tocca `Verified` |
| 1.2 vocabolario strutturale | Opus 5 xhigh | Opus 5 high |
| **1.3 ritenzione del `LayoutIR`** | Opus 5 max | **Fable 5 max** — tocca Gate A |
| 1.4 serializzatore SVG | Opus 5 xhigh | Opus 5 high |
| 1.5 recinto `render→adapters` | Sonnet 5 high | Opus 5 high |
| **1.6 round-trip semantico** | Opus 5 max | **Fable 5 max** |
| 1.7 trasformazione `serie` | Opus 5 xhigh | Opus 5 high |
| 1.8 Visual Slice 0 | Opus 5 max | Fable 5 max |
| **2.1 `StudentTrace`** | Opus 5 max | Fable 5 max |
| **2.3 primo passo non valido** | Opus 5 max | **Fable 5 max** — semantica del primo errore |

**La regola in una riga: l'effort si abbassa solo su chi non giudica** — e su chi giudica si alza.
Vedi `docs/04-ricerca-token-e-automiglioramento.md` §2.4 per la misura del costo, e §4 qui sotto per
chi sono i sottoagenti che giudicano.

---

## Il ciclo di ogni iterazione

### 1. Orientati

**Primo comando dell'iterazione, prima di leggere qualunque documento:**

```bash
uv run python scripts/bmad_chain.py verifica --con-loop; echo $?
```

Il contesto viene compattato: ciò che non è su disco è perso — e ciò che è su disco ma non
è tracciato viene rifatto. `verifica` chiude tutt'e due i buchi e dice qual è il prossimo
passo. **Se esce 1, la prima unità di lavoro è la divergenza che ha nominato**, non il
passo che avevi in mente: `fatto-non-tracciato` si chiude con `segna`, mai rifacendo il
lavoro.

Poi leggi `_bmad-output/implementation-artifacts/sprint-status.yaml` per le storie.

### 2. 🔑 Scegli per rischio, non per posizione

**Non prendere la prima riga della lista.** Questo difetto è già stato pagato: nella fabbrica
ARDESIA, `promote_pin.py` pesca la prima riga `[AUTO-OK]` in FIFO-greedy senza funzione di valore,
mentre `replenish.sh` inserisce task low-value **in testa** — risultato, le task critiche curate
vengono sepolte entro un ciclo e mai promosse. Vedi `~/.claude/skills/ardesia-curate-factory/`.

Scegli il **collo di bottiglia a rischio più alto** fra ciò che è sbloccato:

1. qualunque cosa blocchi il kill criterion di Gate A;
2. un difetto che invalida misure già prese;
3. un vincolo owner-locked non ancora tradotto in gate eseguibile;
4. la prossima unità in sequenza.

Scrivi nel riepilogo **perché** hai scelto quella.

### 3. Costruisci — `bmad-build`

Test per primi, uno per blocco `Given/When/Then`. I criteri **negativi** sono i più importanti.

Prima della review, scrivi nella spec la mappa `criterio → test`. Un criterio senza riga è un
criterio non implementato.

### 4. Rivedi in un contesto che non ha scritto il codice

**Difetto misurato nella v2:** entrambe le storie di Epic 1 furono riviste dallo stesso contesto che
le aveva scritte. Su un prodotto che vende la verifica indipendente, è la contraddizione peggiore.

**Il revisore non parte su un diff che non ha passato i gate deterministici.** I gate del §6 costano
zero token; un revisore costa 20-40 minuti per round, e l'80% dei rilievi che produce è
meccanicamente controllabile. Suite rossa o confini sporchi = `BLOCKED_BEFORE_REVIEW`: si sistema
prima, non si manda un LLM a trovare ciò che `pytest` trova in nove secondi.
Misura in `docs/04-ricerca-token-e-automiglioramento.md` §2.5 e §3.6.

Delega a sottoagenti con contesto pulito, in parallelo — **senza passare loro il tuo ragionamento**:

- `ecc:python-reviewer` — idiomi, tipi, correttezza
- `ecc:silent-failure-hunter` — errori inghiottiti, fallback silenziosi
- `ecc:type-design-analyzer` — quando entrano tipi di dominio nuovi

Poi `bmad-code-review` sul diff. I rilievi non corretti vanno scritti col motivo.

**Tetto: 3 round per unità.** Misurato altrove: i round 1-3 sono sostanziali, i 4-6 aritmetici. Al
quarto round non si continua — si scende di scopo o si ferma l'unità e la si nomina.

**Tetto di concorrenza: 4 sottoagenti insieme, mai di più.**
*Difetto misurato il 15 agosto 2026, ore 06:00.* Undici revisori Opus lanciati **nello stesso
messaggio** sul gate della Spine hanno esaurito il limite di sessione: tutti e undici morti a metà
lavoro, zero file scritti, costo pagato per intero. **Non è il numero che costa, è la
simultaneità** — gli stessi undici a scaglioni di tre sarebbero arrivati in fondo.

*Gate:* scaglioni di **3-4**, e il successivo parte quando il precedente è rientrato. Se il lavoro
è urgente si riduce il numero di lenti, non si aumenta il parallelismo.

*Perché è più grave di quanto sembri:* un gate che non gira **perché ha esaurito la quota** è
peggio di un gate non eseguito. Nel secondo caso lo sai e decidi; nel primo hai pagato, non hai
niente, e la tentazione è dichiarare il passo chiuso lo stesso.

### 5. Interfaccia — `ui-ux-pro-max`

`design-system` sulle fondamenta · `ui-styling` sui componenti · `design` sulle schermate.

`DESIGN.md` ed `EXPERIENCE.md` vincono sempre: il Rifiuto non è rosso, nessuno stato è portato dal
solo colore, cifre tabulari, nessuna animazione celebrativa.

Verifica su ogni storia di interfaccia: leggibile **in scala di grigi**, percorribile da
**tastiera**, ogni disegno con **alternativa testuale topologica**.

### 6. Verifica

```bash
uv run --with pytest --with pytest-cov python -m pytest
uv run --with pytest --with pytest-cov python -m pytest --cov-report=json -q
uv run python scripts/check_domain_coverage.py
uv run python scripts/check_boundaries.py
uv run python scripts/bmad_chain.py verifica --con-loop
uv run kirchhoff-eval build --n 60 --out reference-set
uv run kirchhoff-eval report --root reference-set --split dev
```

Fatto significa, tutto insieme: ogni criterio ha un test che passa · suite verde · **copertura non
scende rispetto all'iterazione precedente** — il pavimento è 100%, non 95% · `domain/` al 100% righe
e rami · confini puliti · **catena BMAD coerente** · SER non sale, mai.

Leggi gli exit code senza pipe: `cmd > file 2>&1; echo $?`.

### 7. Chiudi e riparti

**Un solo blocco, sempre tutt'e due i comandi.** L'iterazione non è chiusa finché il
secondo non è uscito 0: è lì che il tracciamento smette di dipendere dal ricordarsene.

```bash
# a) le storie — se l'iterazione ha chiuso una storia
uv run /Users/andreamarro/.claude/plugins/cache/bmad-method/bmad-method-analyze-plan-build/6.11.0/src/bmm-skills/plan/bmad-sprint-planning/scripts/sprint_plan.py generate \
  --epic-file _bmad-output/planning-artifacts/epics.md \
  --status-file _bmad-output/implementation-artifacts/sprint-status.yaml \
  --stories-dir _bmad-output/implementation-artifacts \
  --project "Kirchhoff" --date "<MM-DD-YYYY HH:MM>" --set <chiave>=done

# b) la catena — se l'iterazione ha chiuso un passo di FASE 1
uv run python scripts/bmad_chain.py segna --passo <n> --stato done --nota "<prova in una riga>"

# c) il gate di chiusura: esce 0 o l'iterazione non è chiusa
uv run python scripts/bmad_chain.py verifica --con-loop; echo $?
```

`segna` rigenera la tabella di FASE 1 da sé: non esiste un secondo comando da ricordare.
Se `segna` rifiuta, l'artefatto non porta il timbro del passo — **manca il lavoro, non il
comando**. Chiudere una storia senza chiudere un passo di catena è normale: (b) si salta,
(c) no.

A fine epica: `bmad-retrospective`.

`ScheduleWakeup`: `delaySeconds: 60`, `noop: false`, `reason` che nomina la scelta successiva **e il
motivo del rischio**.

---

## Automiglioramento — il ciclo che rende il loop diverso da una catena di montaggio

Un loop che esegue bene ma non impara ripete gli stessi errori con efficienza crescente. Tre
meccanismi lo evitano, e vanno eseguiti, non ammirati.

### 1. Ogni escaped failure diventa un invariante permanente

Un difetto che è passato attraverso i gate ed è stato trovato dopo **non si chiude con una fix**. Si
chiude con una fix **più** un test di regressione o un invariante che rende impossibile riprodurlo.
Se non sai scrivere quel test, il difetto non è capito.

### 2. Ogni causa radice ricorrente diventa un gate **eseguibile**, non una nota

L'intenzione «scrivi la lezione» è giusta, la forma in prosa no. Tre misure, con le fonti in
`docs/04-ricerca-token-e-automiglioramento.md` §3:

- le skill **eseguibili** battono quelle in prosa di **11,3 punti** a parità di tutto il resto;
- un file di lezioni che l'agente **riscrive** collassa: 18 282 token → 122 in **un solo passo**,
  accuratezza dal 66,7% al 57,1% — **sotto** il baseline;
- e la prova locale: `~/.claude/skills/learned/`, creata l'11 agosto per questo scopo, **è vuota**.

**Ordine di preferenza, dal più durevole al meno:**

1. **un test o un controllo di script** — `tests/`, `scripts/`. È la forma che gira da sola.
2. **una prova nella catena** — una riga in `CATENA` di `scripts/bmad_chain.py`, se la lezione
   riguarda un artefatto di piano.
3. **una skill in `~/.claude/skills/`** — solo se la lezione non è esprimibile come codice, e
   allora col formato minimo: **il meccanismo** (perché accade), **il sintomo** (come lo
   riconosci), **il gate** (cosa lo rende impossibile). `ardesia-curate-factory` è il modello.

**Il gate si installa nella stessa iterazione che l'ha scoperto.** Il difetto opposto è misurato:
una sessione altrove scrisse due checker ad hoc durante la review e **non li installò** — il loop
generava i propri gate come scarto e li buttava. Un checker scritto e non cablato non esiste.

### 3. Ogni retrospettiva produce azioni indirizzate, non osservazioni

Un'azione senza destinatario e senza storia in cui scatta non viene mai eseguita. La retrospettiva
di Epic 1 lo ha fatto bene: sette azioni, ciascuna con un proprietario e la storia in cui si applica.

### Cosa puoi cambiare di te stesso

**Puoi:** codice · prompt · routing dei modelli · euristiche di layout · UX · ranking delle
trasformazioni · politica dei suggerimenti · test non protetti · **e le sezioni di processo di
questo file**.

**Non puoi**, mai, senza decisione umana: la definizione di `Verified` · gli held-out · le soglie di
qualità · gli invarianti di privacy · il confine AI Act · gli invarianti di billing · la retention
massima · le counter-metrics · `docs/02-costituzione-kirchhoff.md`.

> «Un sistema che può modificare autonomamente il proprio standard di verità non è automigliorante:
> è epistemicamente incontrollato.»

---

## Debugging — `superpowers:systematic-debugging`

Al **primo** test che non si sistema con la correzione ovvia. Non la seconda ipotesi a caso.

Vale anche per: test che passa da solo e fallisce nella suite · copertura che scende senza aver
tolto test · **residuo di Verifica non nullo** dove l'aritmetica è esatta, lì è *sempre* un bug ·
SER che sale dopo una modifica innocua · disegno che non supera il round-trip.

**Il refutatore è un imputato, non un testimone.** Se molte unità vengono bocciate e poche
sopravvivono, ci sono due spiegazioni e non si distinguono a occhio: il generatore produce
spazzatura, **oppure il gate boccia lavoro valido**. Misurato: nessun giudice LLM supera il **70% di
precisione**, e la valutazione a regole sottostima il successo del **16,7-18,5%** con richiamo
**55,9%** — da sola basta a produrre un tasso di conservazione nullo. Prima di riscrivere il
generatore: **prendi a mano un campione dei rifiuti e misura il tasso di falso rifiuto.** Fonte in
`docs/04-ricerca-token-e-automiglioramento.md` §3.5.

---

## Arresto duro — `ScheduleWakeup(stop: true)` e spiega

- **Un confine owner-locked verrebbe violato.** Non scegliere: fermati e nominalo.
- **Due artefatti di piano si contraddicono.** È già successo due volte. Non decidere tu chi ha
  ragione.
- **Il kill criterion di Gate A non è soddisfatto** dopo serie, parallelo e partitore.
- **SER sale** o **la copertura scende**, e l'indagine sistematica non ha trovato la causa.
- **Una decisione aperta blocca il lavoro.** Le dodici sono in `kirchhoff_01_piano_master_v3.md`
  §27. **Non inventarle:** salta a un'unità che non ne dipende, oppure fermati.
- **Servono chiave, account o servizio esterno** non configurati.
- **Il backlog si riempie di task-specchio a basso valore.** È il bloat dello strategist osservato
  nella fabbrica ARDESIA: fermati e chiedi curatela.
- **Il tetto di budget è vicino.** Il segnale di arresto **viene da fuori**, non da te: misurato,
  i modelli prevedono oltre il **70% di fattibilità dopo aver bruciato il 60% del budget**, e la
  correlazione fra bravura nel compito e stima del budget residuo è **r ≈ 0,35**. L'arresto precoce
  costa 1,6-4,2 punti di successo e risparmia il **28-64% dei token** sui tentativi falliti. Per
  questo `--max-budget-usd` è nel comando di lancio e non è negoziabile a caldo.
  Fonte in `docs/04-ricerca-token-e-automiglioramento.md` §2.6.

---

## Cosa non fare

- Non costruire Gate A prima che la catena BMAD sia chiusa.
- Non prendere la prima unità della lista senza valutarne il rischio.
- Non rivedere il proprio codice da soli.
- Non toccare `docs/00-fonte-piano-kirchhoff.md`, `docs/inbox/`, `docs/02-costituzione-kirchhoff.md`.
- Non abbassare una soglia per far passare un'unità di lavoro.
- Non importare un simulatore, una memoria studente o una shell dentro Kirchhoff: appartengono ad
  Ardesia e al suo Simulation Plugin.
- Non far entrare concetti MCP-specifici nel dominio.
- Non pubblicare, push, pagare, registrare account.
- Non usare materiale con licenza non commerciale — licenze verificate in `docs/01-fonti-esterne.md`.

---

## Contesto in una riga

**Il circuito è la spiegazione.** Ogni passaggio mostra cosa cambia, perché era lecito e come si sa
che il nuovo circuito è equivalente. Se una scelta di implementazione indebolisce quella promessa, è
la scelta sbagliata anche quando è la più comoda.
