# Risparmio token e automiglioramento — ricerca recuperata, non rifatta

**Data:** 14 agosto 2026 · **Stato:** recupero, non ricerca nuova
**Mandato:** `docs/03-ripartenza-2026-08-14.md`, compito B — «Ricerca già svolta abbondantemente
in altre conversazioni: recuperala, non rifarla. […] Ciò che non trovi lo dichiari non trovato —
non lo ricostruisci a memoria.»

Ogni affermazione qui sotto porta la sua fonte. Dove la fonte è un frammento e non il documento
intero, è detto. Dove non ho trovato niente, è scritto nella §5 e non è stato colmato a memoria.

---

## 1. Dove ho cercato, e cosa ha reso

| Fonte | Metodo | Resa |
|---|---|---|
| `~/.claude/skills/` | lettura diretta | 2 skill lette per intero; `learned/` **vuota** |
| `search_session_transcripts` | 16 query a sottostringa esatta | frammenti da 9 sessioni; **il testo integrale non è raggiungibile** (§5) |
| `~/ARDESIA-KNOWLEDGE` (vault Obsidian aperto) | `find` + lettura mirata | **il giacimento**: due documenti di ricerca, 131 KB |
| `~/.claude/projects` | `grep -rl` su 678 `.jsonl`, 747 MB | **zero** — le sessioni CCD non stanno lì |

Il vincolo registrato nella ripartenza è confermato e va aggiunto un pezzo:
`search_session_transcripts` è sottostringa esatta **e restituisce un solo frammento per
sessione**. Query diverse sullo stesso testo aprono finestre diverse: è così che ho ricostruito i
pezzi qui sotto. Il transcript integrale non è su disco in forma leggibile — `grep` su
`~/.claude/projects` e su `~/Library/Application Support/Claude` non trova né gli id di sessione
né il contenuto.

### Le fonti primarie recuperate

- **F1** — `~/ARDESIA-KNOWLEDGE/50-Research/2026-07-30-LOOP-ENGINEERING-RICERCA-E-DECISIONI.md`
  (17 KB, letto per intero). Ricerca sintetizzata + decisioni prese, con il corpus di link.
- **F2** — `~/ARDESIA-KNOWLEDGE/50-Research/RICERCA-LOOP-AUTOMIGLIORANTE-GREZZA.md`
  (114 KB, 2 173 righe, aggiornato **oggi alle 05:02**). Ricerca grezza sullo stato dell'arte
  2025-2026 dei loop automiglioranti, con etichette di provenienza per voce.
  **Letto: §5 intera, §5.17, §5.18, §5.19, §6.0, §6.9. Non letto: §1-§4, §6.1-§6.8, §7.**
- **F3** — `~/.claude/skills/ardesia-curate-factory/SKILL.md` (letto per intero).
- **F4** — frammenti di transcript, citati per titolo e id di sessione.

---

## 2. Risparmio token — ciò che è **misurato**

### 2.1 Il costo fisso per iterazione, e la leva che lo taglia 3,3×

Misura riportata in tre sessioni indipendenti (`Loop treadmill e refutazioni fantasma`
`local_89de01ab`, `Valutazione Ardesia: stato pre-alpha` `local_112f2f60`, `Convergenza loop
ARDESIA` `local_a136bde3`), come tabella di configurazioni:

| configurazione | `cache_creation` | costo |
|---|---:|---:|
| baseline, **92 plugin abilitati su 300 installati** | 46 943 | $0,479 |
| `--strict-mcp-config` | 46 958 | $0,479 |
| `--setting-sources project,local` | 6 316 | $0,0736 |
| **`--setting-sources project,local` + cinque `--plugin-dir` mirati** | **12 218** | **$0,1451** |

Il costo è **per rispondere «ok»** — prima di qualunque lavoro, a **ogni** iterazione.

Tre letture, tutte e tre azionabili:
1. `--strict-mcp-config` **non taglia niente** (46 958 vs 46 943). È un risultato negativo
   misurato: non riprovarlo.
2. La terza riga è a costo minimo ma **senza gli strumenti** — non è utilizzabile da sola.
3. La quarta è quella scelta: **3,3× di risparmio** sul costo fisso, strumenti inclusi.

⚠️ **Modo di fallire, registrato** (`local_a136bde3`): «`--plugin-dir` inesistente → exit 0, il
comando gira senza quella skill, **in silenzio**. Fallisce aperto.» Un percorso sbagliato non
produce errore: produce un loop che gira senza gli strumenti che credi di avergli dato.

### 2.2 Dove va il budget, e perché cresce

Da F1, §«Token — dove va davvero il budget»:

- **Le operazioni di lettura sono il 76,1% del consumo.**
- Il costo cresce **col quadrato del numero di turni**, perché ogni turno rispedisce il prefisso.
- Il prompt caching lo rende ~10× più economico (lettura ≈ 0,1× input) **ma resta quadratico**.
- Solo due cose cambiano l'esponente invece della costante: **limitare la finestra rispedita** e
  **tenere i risultati grossi fuori dal contesto**.

**Numero ritirato, e va detto**: la stessa nota afferma «il contesto ri-inviato è il 62% del
conto» e poi lo **ritira** con una correzione datata `2026-07-30T08:05`: `input_tokens` è soltanto
il resto non cachato, il prompt totale è `input_tokens + cache_creation_input_tokens +
cache_read_input_tokens`. Stato dichiarato: `RITIRATO_IN_ATTESA_DI_RIMISURA`, **non**
`FALSIFICATO`. Il 76,1% e la crescita quadratica sopravvivono e non dipendono da quel numero.

### 2.3 Il breakpoint di cache che smette di funzionare in silenzio

Da F1, corollario operativo scoperto insieme alla correzione:

> ogni breakpoint di cache cammina indietro **al massimo 20 blocchi di contenuto**. Un turno
> agentico con molte coppie `tool_use`/`tool_result` supera quel limite, e il breakpoint
> successivo **non trova nulla — in silenzio**.

**Verifica:** `cache_read_input_tokens` diverso da zero su turni ripetuti. Se è zero, si paga
tutto a prezzo pieno **senza alcun errore visibile**.

### 2.4 Le leve, in ordine di resa dichiarata

Da F1 e dal prompt di loop citato in `Ardesia loop prompt` (`local_e94ee2d4`):

- **prefisso stabile, dati volatili alla fine.** In concreto: «inietta `project.json` come
  messaggio `role:"system"` **dentro** `messages[]`, non nel `system` top-level, o invalidi la
  cache a ogni ciclo».
- **sessione fresca a task chiuso** · **routing di tier** · **potatura del contesto**.
- **esecuzione parallela**: 10 passi in 3 tracce parallele portano l'affidabilità end-to-end da
  60% a 81-86%. Ma solo **ricerca e confutazione**, mai i writer.
- **abbassare l'effort sulle unità piccole** — registrato come «l'unico margine reale non
  sfruttato» e, nella sessione `Loop v2 ripartenza` (`local_4cb62a2c`), come difetto **D-4 · La
  leva del risparmio token, trovata e non applicata**: «Il loop gira tutto a `--effort max`. Non
  applicato.»
- **context editing** — `clear_tool_uses_20250919`, beta `context-management-2025-06-27`: pulisce
  i vecchi tool result (opzionalmente anche i tool *input*) lato server prima della chiamata.
  Frammento recuperato da `local_e94ee2d4`; **la tabella completa non è stata recuperata** (§5).

### 2.5 Il gate deterministico come risparmio, non come qualità

Dal prompt di loop in `local_e94ee2d4`, architettura obbligatoria:

> `Worker -> LocalChecks -> Verifier`, dove **LocalChecks esegue l'oracolo a costo zero token** e
> il revisore **non parte mai** su un diff che non lo passa (stato `BLOCKED_BEFORE_REVIEW`).
> Tetto **1 review + 1 repair**, poi escalation.

E i divieti, con il motivo:

- **mai disabilitare thinking** — la chiamata finisce nel testo, il turno risulta verde, il tool
  non viene mai eseguito;
- **mai comprimere la run che decide un merge** — «0 test raccolti» è indistinguibile da «2040
  verdi»;
- **mai installare MCP di compressione.**

### 2.6 Il numero più pulito per un kill switch

Da F2 §6.9.b, *BAGEN: Are LLM Agents Budget-Aware?* (arXiv 2606.00198):

- Sulle traiettorie fallite i modelli prevedevano **oltre il 70% di fattibilità dopo aver bruciato
  il 60% del budget**; gli allarmi scattano solo nell'ultimo 20%.
- **L'arresto precoce ha risparmiato il 28-64% dei token sui tentativi falliti, al costo di 1,6-4,2
  punti percentuali di successo.**
- Correlazione fra bravura nel task e accuratezza nella stima del budget: **r ≈ 0,35**.

> **Il segnale di stop deve venire da fuori dall'agente.** Non è un principio: è la conseguenza
> operativa di un bias ottimistico misurato su ogni modello di frontiera testato.

---

## 3. Automiglioramento — ciò che è misurato, e che contraddice il senso comune

F2 è verificata su fonti primarie e dichiara **otto correzioni** rispetto alla propria prima
stesura scritta a memoria. La sintesi operativa (§5.17), riportata testualmente:

| meccanismo | ancorato a segnale esterno? | esito **misurato** |
|---|---|---|
| giornale **append-only** sotto drift | no (non revoca) | **0,210 vs 0,309 senza memoria** |
| **«aggiungi tutto»** | no | **−3,7…−12,1 pp su 4 agenti su 4** |
| agente che **riscrive le proprie lezioni** | no | **18 282 → 122 token, −9,6 pp** |
| auto-correzione intrinseca | no | **peggiora** |
| auto-memoria vs RAG verbatim | no | **42,0% vs 47,2%** |
| scrittura distillata vs grezza | — | **il recupero pesa 20 pt, la scrittura 3-8** |
| **cancello di qualità in scrittura** | **sì** | **+25,45 pp** su aggiungi-tutto |
| stato aggiornato **solo da fatti verificati dall'ambiente** | **sì** | **51,8% → 80,7%** |
| **skill programmatiche eseguibili** | sì | **+11,3 pt sopra le skill in prosa** |

Le quattro voci che toccano direttamente il loop Kirchhoff:

**3.1 Il giornale che solo aggiunge è peggio di nessuna memoria.** *TEPA* (arXiv 2608.07429,
2026-08-10, non revisionato): append-only **0,210**, nessuna memoria **0,309**, TEPA revocabile
**0,950**. «La memoria append-only ha ottenuto il **32,1% in meno** di NON avere memoria affatto.»
La proprietà mancante non è la capacità: è la **revoca**.

**3.2 Il cancello in scrittura conta più della memoria.** *How Memory Management Impacts LLM
Agents* (ACL 2026 Long, **peer-reviewed**, arXiv 2505.16067): da 20 a 40 volte più memoria,
prestazioni **uniformemente peggiori su tutti e quattro** gli agenti testati. Il rimedio misurato è
un valutatore severo in scrittura: **+25,45 pp** su EHRAgent. La potatura ha ridotto un archivio da
1 012 a **248 record mantenendo l'accuratezza**.

**3.3 Far riscrivere all'agente il proprio file di lezioni lo distrugge.** *ACE* (ICLR 2026,
**peer-reviewed**, arXiv 2510.04618) nomina i due meccanismi: **brevity bias** («scarta gli
approfondimenti di dominio in favore di riassunti concisi») e **context collapse** («la riscrittura
iterativa erode i dettagli nel tempo»). Il caso di studio: **18 282 token collassati a 122 in UN
SOLO passo, accuratezza dal 66,7% al 57,1%** — sotto il baseline di 63,7%. Rimedio misurato:
**delta strutturati incrementali** invece di riscritture monolitiche (+17,0% offline / +17,1%
online, −83,6% di costo in token).

**3.4 Le skill eseguibili battono le skill in prosa di 11 punti.** *ASI* (arXiv 2504.06821) isola
la variabile: batte il baseline statico del 23,5% e batte **la propria controparte a skill
testuali dell'11,3%**. E la doccia fredda (arXiv 2604.04323): con **34 000 skill reali** da cui
recuperare, «i benefici delle skill sono **fragili** […] con tassi di successo che si avvicinano al
baseline senza skill negli scenari più difficili».

### 3.5 Il refutatore è un imputato, non un testimone

F2 §6.0, *AgentRewardBench* (arXiv 2504.08942, 1 302 traiettorie annotate da esperti, accordo
89,3%):

- **Nessun giudice LLM supera il 70% di precisione** — circa il 30% dei verdetti di successo sono
  falsi positivi.
- L'affidabilità del giudice **non è una proprietà del giudice: è una proprietà del compito**
  (63,5% su WebArena, 94,6% su WorkArena).
- **La valutazione a regole sottostima il successo del 16,7-18,5%, con richiamo 55,9%.**

> Conseguenza scritta nella fonte: «40 commit, 0 tenuti» ha due spiegazioni che i dati non
> distinguono — il generatore produce spazzatura, **oppure il refutatore boccia lavoro valido**.
> Un gate che sotto-accredita del ~17% con richiamo 55,9% è **da solo sufficiente** a produrre un
> tasso di conservazione nullo. Prima di toccare il generatore: **etichettare a mano un campione
> dei rifiuti e misurare il tasso di falso rifiuto.**

### 3.6 Il flywheel che ha funzionato, con il suo numero

Da F1, la decisione presa e validata:

- Classificazione di venti finding confermati da sei round di revisione avversariale:
  **16 meccanicamente controllabili (80%)**, 1 parziale, 3 di giudizio genuino.
- La stessa classe di difetto è **ricomparsa sessanta minuti** dopo essere stata corretta a mano.
- Peggio: durante la sessione erano stati scritti **due checker ad hoc e non installati** — «il
  loop generava i propri gate come scarto della review e li buttava».
- Rimedio: `doc_claims_gate.py`, quattro controlli ognuno da un finding misurato, cablato in un
  job CI **richiesto**. Validato contro verità di terra: sul documento **già fuso** ha riprodotto
  **due dei tre finding del round 6 in meno di un secondo**.
- Metrica: `mechanical_share = finding_meccanici / finding_totali`, **baseline 0,80, DEVE
  scendere**. Dichiarata dagli autori stessi come baseline di **una** sessione su **tre** PR: «non
  è una legge; è il punto di partenza contro cui misurare la prossima».

Fonte esterna che lo sostiene (F1): arXiv 2607.13091, *Self-Improving AI Coding Agents Through
Accumulated Behavioral Rules* — regole derivate dal feedback di review **accettato**, salvate in
file di istruzioni versionati; risultato riportato **zero ricorrenze su 9 classi di errore tracciate
e 74 esposizioni cumulative successive alla regola**.

### 3.7 Due meccanismi anti-treadmill osservati, uno rotto

- **Refutazioni come primo compito obbligatorio** (`local_112f2f60`, `local_a136bde3`): le
  refutazioni vivono in `stato/refutazioni-aperte.txt` e vengono **iniettate nel prompt successivo
  come primo compito obbligatorio**; il loop si ferma solo dopo **tre** refutazioni consecutive.
  Il generatore del prompt lo scrive testualmente:
  `printf '## PRIMO COMPITO OBBLIGATORIO: refutazioni aperte\n\n'`.
- **Memoria anti-treadmill rotta** (`local_4cb62a2c`, difetto D-2): «`ops/loop/compiti.py` **legge**
  `stato/compiti-tentati.json` (righe 289 e 292) e **nessuno lo scrive mai**. Il contatore vale
  sempre zero.» È il modo peggiore di fallire per una memoria: **sembra funzionare**.
- **La fabbrica ARDESIA sotterra le task critiche** (F3, già citata in `loop.md` §2):
  `replenish.sh` inserisce in **testa**, `promote_pin.py` pesca la **prima** riga in FIFO-greedy
  senza funzione di valore → le task critiche curate sono sepolte entro **un** ciclo.

### 3.8 Il meccanismo «scrivi una skill» ha prodotto zero skill

**Verificato ora:** `~/.claude/skills/learned/` esiste, è stata creata l'**11 agosto alle 19:31**, e
**è vuota**. Le undici skill presenti sono tutte anteriori e scritte a mano. In tre giorni il
meccanismo «una causa radice ricorrente diventa una skill» — che `loop.md` prescrive — non ha
prodotto un solo artefatto.

---

## 4. Il corpus di link, recuperato

Da F1. Sono i link che l'utente dice di aver raccolto altrove; li riporto come sono, senza
verificarli uno per uno.

**Token — dove va il budget**
- [mem0 — 2026 token optimization playbook](https://mem0.ai/blog/the-2026-token-optimization-playbook-cut-ai-agent-memory-costs-3%E2%80%934x)
- [Vantage — agentic coding costs](https://www.vantage.sh/blog/agentic-coding-costs)
- [Augment — AI coding cost analysis](https://www.augmentcode.com/guides/ai-coding-cost-analysis-agent-token-spend)
- [Glean — optimize token efficiency in agentic systems](https://www.glean.com/perspectives/how-to-optimize-token-efficiency-in-agentic-systems)
- [LeanOps — agentic AI cost runaway](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
- [arXiv 2601.16746 — SWE-Pruner](https://arxiv.org/pdf/2601.16746) · [arXiv 2604.08290 — Tokalator](https://arxiv.org/pdf/2604.08290)

**Automiglioramento**
- [arXiv 2607.13091 — Self-Improving AI Coding Agents Through Accumulated Behavioral Rules](https://arxiv.org/html/2607.13091v1)
- [Factory.ai — using linters to direct agents](https://factory.ai/news/using-linters-to-direct-agents)
- [Augment — the agent-run loop](https://www.augmentcode.com/guides/agent-run-development-loop)
- [arXiv 2606.10241 — Regimes: auditable, held-out-gated improvement loop](https://arxiv.org/pdf/2606.10241)

**Loop e harness engineering**
- [Loop Engineering with Codex CLI](https://codex.danielvaughan.com/2026/06/11/loop-engineering-codex-cli-autonomous-agent-loops-automations-subagents-goal-mode/)
  — parametri concreti: goal mode come comando con exit code, **verificatore separato**,
  `max_turns = 200`, `timeout_minutes = 480`, memory file letto a inizio ciclo e aggiornato alla
  fine, subagenti `max_threads = 6`, `max_depth = 1`, `sandbox_mode = read-only` per i reviewer.
- [Martin Fowler — harness engineering](https://martinfowler.com/articles/harness-engineering.html) ·
  [Addy Osmani — agent harness engineering](https://addyosmani.com/blog/agent-harness-engineering/)
- [arXiv 2607.00038 — Stop Hand-Holding Your Coding Agent](https://arxiv.org/abs/2607.00038) ·
  [arXiv 2604.17025 — CAAF](https://arxiv.org/pdf/2604.17025) (determinismo come asset)
- [Sonar — loop engineering without verification is just automation](https://www.sonarsource.com/blog/loop-engineering-without-verification-is-just-automation/)

**Multi-agente — perché NON aggiungere writer**
- [arXiv 2503.13657 — MAST](https://arxiv.org/abs/2503.13657) ·
  [arXiv 2510.18893 — CodeCRDT](https://arxiv.org/abs/2510.18893) (fino a **−39,4%** su alcuni
  task, conflitti semantici 5-10%) · [METR](https://metr.org/research/) (**−19%** in RCT su
  sviluppatori esperti) ·
  [Anthropic — alignment auditing agents](https://alignment.anthropic.com/2025/automated-auditing/)
  (13%→42% **solo su indagini replicabili e aggregate**)

**Fonti primarie della §3** (da F2): arXiv [2608.07429](https://arxiv.org/abs/2608.07429) ·
[2505.16067](https://arxiv.org/abs/2505.16067) · [2510.04618](https://arxiv.org/abs/2510.04618) ·
[2303.11366](https://arxiv.org/abs/2303.11366) · [2305.16291](https://arxiv.org/abs/2305.16291) ·
[2603.02473](https://arxiv.org/abs/2603.02473) · [2606.29914](https://arxiv.org/pdf/2606.29914) ·
[2504.06821](https://arxiv.org/abs/2504.06821) · [2604.04323](https://arxiv.org/abs/2604.04323) ·
[2504.08942](https://arxiv.org/abs/2504.08942) · [2606.00198](https://arxiv.org/abs/2606.00198) ·
[2607.06503](https://arxiv.org/abs/2607.06503)

---

## 5. Ciò che NON ho trovato

Dichiarato, non colmato.

1. **Il documento inglese completo delle tecniche di risparmio token.** Esiste in
   `Ardesia loop prompt` (`local_e94ee2d4`, 1 325 messaggi) come sezione «Practical Techniques
   That Work» con una tabella numerata. Ho recuperato **due righe** per frammenti: la voce
   *Prompt Caching* («freeze a stable prefix — system prompt, tools, reference docs — push
   volatile data like timestamps to the end») e la voce 1 della tabella, *context editing*
   `clear_tool_uses_20250919`. **Le righe 2..N non sono state recuperate.** Il transcript non è su
   disco in forma leggibile e paginare 1 325 messaggi a 14 per chiamata era fuori budget.
2. **`~/ARDESIA-KNOWLEDGE/40-Capability-Evolution/AGENT-ERROR-LEDGER.md`** (44 KB, 2 agosto).
   Esiste, il nome promette esattamente «non ripetere errori», **non l'ho letto**. È il primo posto
   dove guardare alla prossima iterazione.
3. **§1-§4, §6.1-§6.8 e §7 di F2** — 1 400 righe su loop auto-modificanti (Darwin Gödel Machine,
   GEPA, PACEvolve), reward hacking, verifica e giudizio. Non lette. La §7 si chiama «COSA NON HO
   TROVATO» ed è il complemento onesto di questa sezione.
4. **Nessuna nota nel vault** con i termini «risparmio token» / «token budget» /
   «automiglioramento» nel titolo: il materiale sta dentro i due file di §1, non in note dedicate.
   `90-Archive/…/13-AUTOMIGLIORAMENTO-BRAINSTORM-2026-06-16.md`, citato in cinque transcript, **non
   è sul disco** in nessuno dei percorsi cercati.
5. **I venti video YouTube** allegati dall'utente: la sessione del 30 luglio dichiara di non averli
   aperti — «non ho un canale per trascriverli e inventarne il contenuto sarebbe fabbricare una
   fonte». Restano non aperti.
6. **Nessun testa-a-testa pubblicato** «giornale append-only vs indice di recupero» (lacuna
   dichiarata da F2 stessa), e nessun benchmark dei plugin Obsidian di retrieval.

---

## 6. Che cosa di tutto questo è azionabile per Kirchhoff

Solo ciò che diventa un comando o un gate. Il resto è contesto, e sta qui.

| # | Meccanismo | Fonte | Dove va |
|---|---|---|---|
| M1 | Lancio con `--setting-sources project,local` + `--plugin-dir` mirati, **e verifica che i percorsi esistano** | §2.1 | `loop.md` — comando di avvio |
| M2 | Controllare `cache_read_input_tokens ≠ 0`; se è zero la cache è rotta in silenzio | §2.3 | `loop.md` — verifica |
| M3 | Nessun revisore su un diff che non ha passato i gate deterministici | §2.5 | `loop.md` §4 |
| M4 | Tetto ai round di revisione | §2.5, F1 | `loop.md` §4 |
| M5 | Il segnale di arresto viene da fuori: tetto di budget esplicito | §2.6 | `loop.md` — arresto duro |
| M6 | Ogni finding meccanico diventa un gate eseguibile, e si installa **nella stessa iterazione** | §3.6 | `loop.md` §7 |
| M7 | Le skill sono **eseguibili**, non prosa | §3.4 | `loop.md` — automiglioramento |
| M8 | Lo stato si aggiorna **solo da fatti verificati dall'ambiente**, ed è revocabile | §3.1, §3.5 | già fatto: `bmad_chain.py` |
| M9 | Prima di incolpare il generatore, misurare il **falso rifiuto** del refutatore | §3.5 | `loop.md` — debugging |
| M10 | Effort basso sulle unità piccole | §2.4 | decisione aperta, vedi sotto |

### Un conflitto da nominare

`loop.md` §«Automiglioramento», punto 2, prescrive: «Se una lezione merita di sopravvivere alla
sessione, scrivila in `~/.claude/skills/`». La ricerca dice che la **forma** conta più
dell'intenzione: le skill in prosa perdono 11,3 punti contro quelle eseguibili (§3.4), un file di
lezioni riscritto dall'agente collassa (§3.3), e il meccanismo così com'è ha prodotto **zero
skill in tre giorni** (§3.8).

Non è un conflitto fra due artefatti di piano — è ricerca contro una sezione di processo, e
`loop.md` dichiara le proprie sezioni di processo modificabili. Quindi l'ho corretta invece di
fermarmi. Il punto 1 dello stesso paragrafo — «ogni escaped failure diventa un invariante
permanente, cioè una fix **più** un test di regressione» — era già la forma giusta: è una skill
eseguibile scritta come test.

### M10, l'effort — deciso il 15 agosto

Registrata come aperta il 14, **chiusa dall'owner il 15**: «dipende se vogliamo usare agenti, se no
Opus 5 Max».

Tradotta in regola eseguibile, perché il loop delega già a sottoagenti nel §4:

| Chi | Modello · effort |
|---|---|
| loop principale — sceglie, costruisce, decide | **Opus 5, effort max** |
| sottoagenti che **giudicano** (`python-reviewer`, `silent-failure-hunter`, `type-design-analyzer`) | effort alto |
| sottoagenti **meccanici** (ricerca, inventario, lettura, conteggio) | effort basso |

**L'effort si abbassa solo su chi non giudica.** Senza delega, non si abbassa niente — che è
esattamente il «se no, Opus 5 Max». Il margine misurato resta prendibile, ma non a spese della
verifica indipendente, che è ciò che il prodotto vende (K-1 nella costituzione).

Applicata in `.claude/loop.md`, sezione «Modello ed effort».

---

## 7. Collegamenti

- `.claude/loop.md` — dove i meccanismi M1-M9 sono entrati
- `docs/03-ripartenza-2026-08-14.md` — il mandato
- `~/ARDESIA-KNOWLEDGE/50-Research/RICERCA-LOOP-AUTOMIGLIORANTE-GREZZA.md` — F2, il giacimento
- `~/ARDESIA-KNOWLEDGE/50-Research/2026-07-30-LOOP-ENGINEERING-RICERCA-E-DECISIONI.md` — F1
- `~/.claude/skills/ardesia-curate-factory/SKILL.md` — F3
