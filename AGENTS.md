<!-- bmad:context -->
<!-- Verificato 2026-08-24 su d2234fa. Gestito da bmad-project-context; le modifiche dentro
     questo blocco vengono sostituite al refresh. Ciò che vuoi conservare va fuori dai marcatori. -->

## Kirchhoff

Motore di ragionamento circuitale verificato. **Kirchhoff è il motore; CircuitCheck è il prodotto
che lo usa** — il nome del repository è il primo, la priorità è il secondo. Python 3.12 con uv,
aritmetica esatta, pytest. La pianificazione vive in `_bmad-output/planning-artifacts/`, la
costituzione del prodotto in `docs/`, il metodo di lavoro in `.claude/loop.md`.

## Policy

- La catena BMAD 8/8 attesta che i passi di planning sono stati eseguiti; **non** attesta
  implementation readiness. Leggi il verdetto corrente in
  `_bmad-output/planning-artifacts/implementation-readiness.md` prima di selezionare lavoro
  implementativo. Oggi: planning 8/8, readiness `CONCERNS`.
- Lo sviluppo di Implementation Phase va orchestrato da Loop Kirchhoff v3 attraverso il suo
  entrypoint CLI: BMAD decide il lavoro eleggibile, il loop esegue build → verify → review → fix →
  verify → commit → continuazione. Non sostituirlo con implementazioni manuali isolate una volta
  che Epic 0 lo ha reso operativo. Il CLI **non è ancora validato**: le Story 0.1–0.3 sono il suo
  bootstrap.
- Per l'orchestrazione CLI, cerca e riusa il pattern provato del loop Ardesia recente. Kirchhoff
  non deve dipendere a runtime da `~/ardesia-loop-control-plane-v2`: quello è implementazione di
  riferimento, non dipendenza.
- Non leggere `reference-set/holdout/` durante lo sviluppo: usarlo invalida ogni misura successiva.
  Il deny è in `.claude/settings.json`.
- Kirchhoff non importa un simulatore, una memoria studente o una shell applicativa. È CircuitCheck
  a comporre capacità superiori, mai il contrario. Autorità: D11.
- `domain/` non importa nulla del progetto fuori da sé; `scripts/check_boundaries.py` lo verifica.
- Non modificare a mano la tabella FASE 1 di `.claude/loop.md` né
  `_bmad-output/planning-artifacts/bmad-chain-status.json`: li scrive `scripts/bmad_chain.py`, e una
  modifica manuale fa fallire la suite.
- Non aggiungere un'operazione al catalogo delle Trasformazioni: è una modifica del catalogo in
  `src/kirchhoff/domain/transform/catalog.py`, e un test confronta i due insiemi che lo dichiarano.

## Where things are

- Requisiti: `_bmad-output/planning-artifacts/prds/prd-Kirchhoff-2026-08-13/prd.md`
- Architettura: `_bmad-output/planning-artifacts/architecture/architecture-Kirchhoff-2026-08-13/ARCHITECTURE-SPINE.md`
  — dieci AD sono emendati in loco: leggi l'emendamento, non solo la Rule sopra di esso
- Esperienza: `_bmad-output/planning-artifacts/ux-designs/ux-Kirchhoff-2026-08-13/EXPERIENCE.md` e
  `_bmad-output/planning-artifacts/ux-designs/ux-Kirchhoff-2026-08-13/DESIGN.md`
- Costituzione del prodotto, owner-locked: `docs/02-costituzione-kirchhoff.md`
- Backlog e storie: `_bmad-output/planning-artifacts/epics.md`
- Stato delle storie: `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Verdetto di readiness corrente: `_bmad-output/planning-artifacts/implementation-readiness.md`
- Regole ricavate da errori misurati: `docs/05-regole-dall-error-ledger.md`

## Running and verifying

- Test: `uv run --with pytest --with pytest-cov python -m pytest tests`. `uv run python -m pytest`
  esce 1 con «No module named pytest» — l'ambiente del progetto non lo contiene.
- `--no-cov` richiede `pytest-cov` fra i `--with`, altrimenti pytest esce **4** per errore d'uso e
  l'uscita somiglia a un test rosso.
- `scripts/check_domain_coverage.py` legge `coverage.json`, che la suite rigenera: eseguirlo senza
  aver appena eseguito i test misura un artefatto vecchio.
- Ogni iterazione comincia con `uv run python scripts/bmad_chain.py verifica --con-loop`.
- Eval senza toccare l'holdout: `uv run kirchhoff-eval report --root reference-set --split dev`.

## Conventions that differ from defaults

- Nessun `float` nel dominio: le grandezze sono `Fraction`, e lo schema respinge il resto.
- Un valore di componente è magnitudine più unità, mai un numero nudo.
- `Refusal` si restituisce, non si solleva: è un esito di dominio, non un'eccezione (AD-13).
- Docstring, identificatori e messaggi d'errore in italiano.
- Ogni invariante ha una guardia a runtime e un test che l'ha vista sollevare: lo stack è Python
  senza type checker, quindi «il vincolo è nel tipo» qui non è vero.

## Known pitfalls

- Cerca prima di costruire. In una sola sessione sei concetti che stavamo per inventare erano già
  progettati altrove, e meglio.
- «Studio» sono due cose: la superficie B2B del docente, da costruire, e `~/whiteboard-studio/studio`,
  un'app React esistente con 88 test, da riusare. Nessuna storia dice «costruisci Studio».
- Il procedimento dello studente è `StudentTrace` (FR-44), confrontabile col `ProofGraph` passo per
  passo e non solo sul risultato finale; non introdurre `StudentSolutionIR` senza search-before-build.
- Un passaggio che non si riesce a leggere non è un passaggio sbagliato: confonderli produce una
  falsa accusa, che è il difetto peggiore di questo prodotto.
- Un conteggio si legge dalla struttura che lo definisce, mai da un riepilogo adiacente: tre
  conteggi sbagliati in una sessione venivano tutti da una vista invece che dalla fonte.
- Un comando fallito lascia un vuoto che somiglia a una misura. `2>/dev/null` su un comando la cui
  uscita diventa un numero nasconde la prova.
- `find` può rispondere a una domanda diversa da quella posta — `domain/ir` è un package e una
  ricerca a profondità limitata non lo vede. Per la struttura usa `ls -R`.

<!-- /bmad:context -->

<!-- Fuori dal blocco gestito da bmad-project-context: qui non viene sostituito al refresh. -->

## Fatti che il blocco gestito non conosce ancora

- **I vocabolari chiusi sono due, non uno.** La riga «Non aggiungere un'operazione al catalogo
  delle Trasformazioni» sopra ne conosce uno solo. Dalla Story 1.2 (26/08/2026) esiste anche
  `src/kirchhoff/domain/transform/primitives.py`: cinque **riscritture strutturali**
  — `fusione_di_componenti`, `fusione_di_nodi`, `eliminazione_di_nodo`,
  `sostituzione_di_componente`, `rimozione_di_componente` — che sono il livello *sotto* i passi
  pedagogici. `StructuralDerivation.operation` punta a queste; `Certificate.operation` al
  catalogo. I due insiemi sono disgiunti, e una guardia all'import lo verifica.
- Le due regole differiscono. Il catalogo è scritto due volte (`TransformationKind` e `CATALOG`)
  e un test confronta i due insiemi. `PRIMITIVES` è invece **derivato** da `StructuralPrimitive`
  con `get_args`, come `refusal.CAUSES` da `Cause`: non c'è un secondo insieme da tenere
  allineato. Aggiungere una riscrittura significa toccare `StructuralPrimitive`, la tabella
  `FORME` (che le impone genere e arità), e `catalog.COMPOSITION` o `catalog.DORMANT` — la
  partizione fra riscritture esercitate e dormienti è imposta esatta all'import.
- **Gli identificatori delle entità esposte hanno un vocabolario chiuso, e sta nel dominio.**
  Dalla Story 1.3 (26/08/2026) `src/kirchhoff/domain/identity.py` deriva i sei prefissi delle
  `Consistency Conventions` — `ir_`, `sol_`, `var_`, `evt_`, `lay_`, `patch_` — da `IdentityKind`
  con `get_args`, come `refusal.CAUSES` da `Cause`. Coniare è **puro**: `conia` prende istante ed
  entropia dalla firma (AD-17, «il tempo si inietta»), non li legge, e **non esiste una seconda
  maniera di coniare** — un test lo verifica. Le convenzioni dicono «ULID», e tutti e sei i generi
  ne ricevono uno vero.
- **Conia chi ritiene, non chi produce.** `transform` è pura per AD-2: non ha orologio, quindi non
  può coniare il `patch_` della `LayoutPatch` che emette. Il nome nasce al deposito, in
  `render/layout.PatchStore`, con l'istante iniettato — la stessa regola di `LayoutIR.nuovo`. Ne
  segue la proprietà che SM-14 richiede: **un `patch_` identifica un passo, non un contenuto**, e
  due passi che emettono patch identiche ricevono due nomi. `ProofGraph` rifiuta due archi sullo
  stesso `patch_`, e `verifica` rifiuta le stringhe di forma giusta e valore oltre i 128 bit.
- **L'entropia dev'essere nuova a ogni conio, e nessun port la fornisce.** `casualita` entra dalla
  firma come l'istante, ma nell'elenco dei port dello spine non c'è un `EntropyPort`: il requisito
  vive nel docstring di `domain/identity`. A entropia costante due conii nello stesso millisecondo
  collidono e il registro solleva «già depositato», accusando chi deposita di un difetto altrui.
- **Il proprietario del riferimento al `LayoutIR` è il nodo del `ProofGraph`, non la sessione.**
  AD-8 em. del 24 agosto lo scrive; `src/kirchhoff/domain/proof/graph.py` lo implementa. Il nodo
  porta due identificatori (`ir_` e `lay_`) e **nessuna struttura**. La relazione è scritta una
  volta sola, sul nodo: `nodo_di` è una scansione, non un secondo registro. Il `LayoutIR` e il suo
  registro append-only vivono in `src/kirchhoff/render/layout/` — AD-8 dà quel ruolo a
  `render/layout` e scrive «**mai** `domain/`», perché dalla v2 il dominio non sa cosa sia una
  posizione. Lì accanto stanno il registro delle `LayoutPatch` e
  `operandi_di_vcer`, che congiunge la tripla di CV6 verificandone le cinque condizioni: senza
  `preserve` risolvibile, `p_k(x)` non è definita e VCER resta un'ipotesi.
- **AD-8 non ha una riga per la `LayoutPatch` persistita.** La tabella dei proprietari non la
  nomina, né come entità con scrittore né come entità dichiarata non persistita. Il `PatchStore`
  sta in `render/layout` perché lì stanno gli altri due operandi della stessa tripla: è
  un'assunzione dichiarata nel modulo, non un fatto dell'autorità. Va ratificata da chi possiede
  lo spine, insieme alla riga dell'ERD che CV6 chiedeva e che non è mai entrata — per la quale
  `implementation-readiness.md` tiene ancora 1.3 a «⛔ non pronta».
