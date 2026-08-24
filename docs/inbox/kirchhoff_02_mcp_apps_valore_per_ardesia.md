# MCP Apps come leva strategica per Ardesia

**Data:** 14 agosto 2026  
**Stato:** documento strategico/architetturale  
**Metodo:** BMAD — input per Brief/PRD/Architecture, non sostituto del PRD di Ardesia  
**Tesi:** MCP e MCP Apps possono diventare un cardine di distribuzione e composizione di Ardesia, ma Ardesia non deve trasformarsi in “un prodotto MCP”.

---

# 0. Executive verdict

MCP Apps ha un valore alto per Ardesia per un motivo specifico: **Ardesia sta già diventando un host di capacità modulari**, con ToolHost, plugin, scene, LessonOS, simulatori e superfici embeddable. MCP aggiunge il confine opposto: non solo “plugin dentro Ardesia”, ma anche **capacità Ardesia esportabili dentro altri host AI**.

Il modello strategico è quindi bidirezionale:

```text
                 CAPACITÀ ARDESIA
                      │
          ┌───────────┴───────────┐
          │                       │
   plugin nativi Ardesia       MCP Server
          │                       │
   ToolHost / board          MCP + MCP Apps
          │                       │
          ▼                 ┌─────┼─────────┐
       Ardesia            ChatGPT Claude  altri host
```

Questo può trasformare Ardesia da “applicazione didattica con AI” a **piattaforma di strumenti didattici verificabili consumabili sia dalla lavagna Ardesia sia dagli ecosistemi AI esterni**.

Ma ci sono tre limiti da scrivere subito:

1. **MCP non è il moat didattico.** È distribuzione/interoperabilità.
2. **MCP Apps non sostituisce la web app/Ardesia host.** Gli host terzi hanno sandbox, policy e UX non controllate.
3. **Non tutto il bus interno di Ardesia deve diventare MCP.** Quando due moduli vivono nello stesso sistema, un contratto nativo più stretto può essere migliore e più sicuro.

---

# 1. Perché MCP è particolarmente coerente con Ardesia

## 1.1 Ardesia ha già il pattern mentale corretto

Dal repository esaminato nella conversazione corrente emergono già:

- ToolHost e capability grants;
- plugin lifecycle;
- `renderEmbeddable()`;
- scene strutturate;
- operazioni mutanti che passano da pipeline/validation;
- Simulation Plugin come owner della simulazione;
- LessonOS con event log e materialized graph;
- canale host-mediated `lesson.event.emit`;
- separazione pack/plugin/core.

Queste scelte sono compatibili con MCP perché entrambe richiedono **contratti espliciti tra agent/host e capacità**.

## 1.2 Il vantaggio non è “far chiamare tool a ChatGPT”

Quello è commodity.

Il vantaggio è rendere una capability Ardesia disponibile in quattro forme con un unico kernel:

```text
Capability
├── Ardesia native plugin
├── Web surface
├── REST/domain API
└── Remote MCP + MCP App UI
```

Esempio:

```text
io.ardesia.circuit-reasoning
```

può essere:

- un post-it/tool dentro Ardesia;
- un ProofReplay nella web app;
- un tool chiamato da un agent;
- una MCP App interattiva dentro ChatGPT/Claude.

---

# 2. MCP non appartiene al modello

La distinzione nelle fonti è importante: MCP appartiene all'host/runtime, non al singolo LLM.

Questo significa che Ardesia non deve creare:

```text
ardesia-openai
ardesia-anthropic
ardesia-gemini
ardesia-qwen
```

come prodotti separati per ogni capacità.

Può esporre un contratto MCP e mantenere provider/LLM dietro i propri port.

La portabilità non è perfetta: ogni host può supportare estensioni diverse e offrire funzioni proprietarie. La strategia corretta è **standard first, progressive enhancement second**.

---

# 3. MCP Apps: perché cambia davvero il valore

Un normale tool MCP restituisce soprattutto testo/dati. MCP Apps aggiunge una UI HTML interattiva associata a tool e resa dentro l'host.

Per Ardesia questo è fondamentale perché molti domini STEM non si spiegano bene con una risposta testuale:

- circuiti;
- breadboard;
- Bode/Nyquist;
- grafici;
- diagrammi a blocchi;
- formule interattive;
- lavagna;
- simulazioni;
- quiz/controlli contestuali.

La UI non è decorazione: può diventare una **surface di stato semantico**.

Esempio:

```text
ChatGPT conversation
        │
        ▼
[Ardesia Circuit MCP App]
  circuito interattivo
  ├── cambia R
  ├── mostra nodo
  ├── prova trasformazione
  └── salva in Ardesia
```

La stessa capability potrebbe poi aprirsi come post-it molto più ricco dentro Ardesia.

---

# 4. Il pattern più potente: Acquire outside, deepen inside

MCP Apps può diventare un canale di acquisizione **nel momento esatto del bisogno**.

Esempio:

```text
utente in ChatGPT/Claude
“non capisco questo Nyquist”
        ↓
Ardesia Control capability
        ↓
Bode/Nyquist interattivo
        ↓
utente modifica K
        ↓
chiede spiegazione
        ↓
“salva questa sessione / continua sulla lavagna”
        ↓
Ardesia account / board / LessonOS
```

Il valore è superiore a un funnel classico “Google → landing → registrazione → dashboard vuota”, perché il prodotto appare dentro il contesto in cui il problema è già attivo.

Questo non significa dipendere dalla directory di un host: l'host è una **porta**, non la casa.

---

# 5. Tre livelli di superficie

Ardesia dovrebbe definire un surface model esplicito.

## Tier A — Text/tool fallback

Ogni capability deve essere utile anche senza UI:

- meaningful `content`;
- structured result;
- error/refusal semantics;
- deterministic IDs.

Questo mantiene compatibilità con host text-only e agent runtime.

## Tier B — MCP App compact surface

UI stretta e task-specific:

- grafico;
- inspector;
- proof step;
- ambiguity resolver;
- mini simulator;
- mini whiteboard.

No tentativo di clonare tutta Ardesia nell'iframe.

## Tier C — Native Ardesia surface

Esperienza completa:

- board;
- multi-post-it;
- LessonOS continuity;
- persistent workspace;
- richer pen interactions;
- cross-plugin composition;
- long-lived projects.

Questo rende MCP Apps un acceleratore della piattaforma, non un concorrente interno.

---

# 6. Architettura consigliata

```text
Domain capability core
        │
        ├── Native Ardesia adapter
        │      └── ToolHost capability contract
        │
        ├── Web adapter
        │      └── REST/WebSocket/PWA
        │
        └── MCP adapter
               ├── remote tools
               ├── resources
               └── MCP App UI resources
```

### Regola

L'MCP adapter **non possiede** domain state e non implementa logica scientifica.

### Regola

L'Ardesia adapter **non importa** specifiche ChatGPT/Claude.

### Regola

Host-specific features sono layer opzionali.

---

# 7. MCP e LessonOS

## 7.1 LessonOS deve restare source-of-truth host-mediated

Le note Ardesia già indicano event log + materialized graph + provenance. Questo non va sostituito con un “MCP memory server” come nuova fonte di verità.

MCP può esporre:

```text
graph.search
graph.neighbors
lesson.get_context
lesson.append_supported_event
```

ma le mutazioni devono passare da policy host e schema eventi.

## 7.2 External host → LessonOS

Una MCP App usata in ChatGPT potrebbe produrre un evento validato:

```text
exercise.completed
simulation.step.completed
proof.transform.corrected
material.cited
```

solo dopo autenticazione/account linking e capability enforcement.

Questo crea continuità reale:

```text
Claude → attività Ardesia → LessonOS → iPad/board Ardesia
```

senza consegnare LessonOS direttamente all'host esterno.

---

# 8. Auth e account linking

La superficie host può essere anonima/free per alcune operazioni, ma appena serve:

- salvataggio;
- cronologia;
- quota/entitlement;
- LessonOS;
- B2B tenant;

serve account Ardesia.

Pattern:

```text
host identity
   ↓ OAuth/account link
Ardesia account_id
   ↓
entitlements / tenant / LessonOS
```

Non affidarsi a cookie/localStorage della MCP App come source of truth.

---

# 9. Sicurezza: MCP aumenta la superficie d'attacco

Il valore strategico ha un costo.

Rischi:

- tool over-privileged;
- prompt injection da risorse;
- confused deputy;
- IDOR su request state/circuit IDs;
- cross-tenant leaks;
- replay/double charge;
- host che invia input malformati;
- UI spoofing/ambiguous confirmations;
- supply-chain dell'MCP package/client.

Mitigazioni:

- capability minima;
- read vs calculate vs mutate vs external side effect;
- explicit confirmation per delete/purchase/send/deploy;
- signed opaque state;
- idempotency keys;
- tenant binding;
- server-side authorization per ogni tool;
- no trust nell'host per hidden fields;
- schema validation;
- audit events;
- CSP/sandbox corretti;
- security review dedicata in BMAD readiness.

---

# 10. Monetizzazione: cosa MCP Apps può e non può fare

MCP Apps deve essere visto prima di tutto come **distribution + interaction layer**.

Non costruire l'economia assumendo che ogni host offra un rail di pagamento nativo stabile o che la directory garantisca discovery.

Pattern robusto:

```text
Ardesia backend
├── account
├── subscription/credits
├── entitlements
└── billing provider
       ↑
 Web/PWA   MCP hosts   native Ardesia
```

Il cliente compra Ardesia/capability, non “un MCP”.

---

# 11. Cosa pubblicare

Non pubblicare 25 server/app indipendenti all'inizio.

Possibili fasi:

## Fase 1

Un solo remote endpoint Ardesia con namespace/capabilities chiare.

## Fase 2

MCP Apps specializzate ma dentro lo stesso prodotto:

- Circuit Reasoning;
- Controls/Bode/Nyquist;
- Simulation;
- eventually other high-value STEM surfaces.

## Fase 3

Solo se l'ecosistema lo giustifica, separare prodotti/listing per discovery.

Il valore proprietario resta server-side: domain solvers, verification, LessonOS, routing, corpus, analytics, entitlements.

---

# 12. MCP Registry / host directories / GitHub

Usare i canali di discovery come portafoglio, non come unico funnel:

```text
official MCP registry / metadata
host-specific directories
GitHub examples/SDK
npm/PyPI client if useful
ardesia web
B2B direct distribution
```

Ogni canale può cambiare policy. Il dominio Ardesia e il protocollo pubblico versionato sono l'asset durevole.

---

# 13. MCP come API pubblica di Ardesia

Questa è forse la conseguenza più interessante a lungo termine.

Se le capabilities Ardesia sono ben progettate, un altro agente potrebbe usare Ardesia come infrastruttura:

```text
solve_verified_circuit
render_verified_proof
run_simulation
create_scene
inspect_graph
save_learning_event
```

Questo può aprire:

- developer plan;
- institutional integration;
- agent-to-agent workflows;
- embedding in LMS/IDE;
- B2B API.

Ma solo dopo aver dimostrato il prodotto core; non fare “platform before product”.

---

# 14. Cosa NON portare su MCP

- internal database primitive;
- raw LessonOS write access;
- unrestricted filesystem/network;
- private eval/holdout;
- secrets/provider keys;
- low-level simulator internals se non necessari;
- admin/billing destructive operations senza confirmation/policy;
- inter-module calls che sono più sicure come direct typed interfaces.

MCP è un confine pubblico. Un tool pubblicato diventa contratto da versionare e deprecare.

---

# 15. Impatto su Ardesia product architecture

MCP spinge positivamente Ardesia verso capability ownership più chiara.

Ogni plugin dovrebbe poter rispondere a:

1. qual è il suo domain kernel?
2. quali operation sono pubbliche?
3. quali sono read-only?
4. quali mutano stato?
5. quali richiedono user confirmation?
6. qual è la structured result?
7. qual è la compact MCP surface?
8. qual è la full native surface?
9. quali eventi LessonOS produce?
10. quali invarianti verificano la truthfulness?

Questo migliora Ardesia anche se MCP non diventasse mai il canale dominante.

---

# 16. Il legame con Simulation Plugin

Il canon Ardesia separa correttamente:

- Host;
- Simulation Plugin `io.ardesia.simulation`;
- ELABTutor come pack/consumer didattico.

MCP Apps suggerisce di mantenere la stessa separazione esternamente.

Un tool come:

```text
simulation.solve(scene_id)
```

non dovrebbe appartenere a ELABTutor. Appartiene alla capability Simulation.

Una MCP App può renderizzare una versione compatta del simulatore; Ardesia può renderizzare la full board surface usando lo stesso scene graph.

---

# 17. UI/UX: il vantaggio di MCP Apps non è “avere HTML”

Il vero vantaggio è poter mantenere **un oggetto interattivo nella conversazione**.

Per STEM questo abilita:

- manipolazione parametri senza roundtrip in prosa per ogni piccolo gesto;
- selezione di elementi;
- provenance;
- visual diff;
- mini whiteboard;
- graphs con cursori;
- inspectable certificates;
- explicit confirmations contestuali.

L'LLM resta il coordinatore conversazionale, la App è il surface preciso, il backend è la verità.

---

# 18. Multimodalità e penna

Ardesia ha un vantaggio nativo che gli host terzi potrebbero non replicare: iPad/pen interaction e board persistence.

Quindi la strategia non deve essere “spostiamo tutto su MCP Apps”.

Deve essere:

```text
MCP App = taste / compact operation
Ardesia = deep workspace / pen / continuity / composition
```

Un utente può iniziare in ChatGPT e continuare sulla lavagna Ardesia con la stessa `proof_id`/`scene_id`.

---

# 19. BMAD: come introdurre MCP senza deragliare Ardesia

## 19.1 Non fare un rewrite

Usare BMAD `correct-course` / architecture update mirato.

### Brief

Aggiungere MCP come strategia di distribution/interoperability, non come nuovo JTBD.

### PRD

Aggiungere requisiti per:

- remote capability surfaces;
- account linking;
- cross-host continuity;
- fallback text/structured results;
- versioning/deprecation;
- explicit external side-effect policy.

### UX

Definire compact surface vs native surface.

### Architecture

Aggiungere MCP adapter, auth, capability mapping, request state/idempotency, UI resource contract.

### Epics

Una vertical slice per capability, non “implementa MCP per tutto Ardesia”.

### Readiness

Security/privacy/host policy gate.

---

# 20. Vertical slice consigliata

Usare Kirchhoff/Circuit Reasoning come primo vero test MCP Apps, perché obbliga a risolvere problemi reali di:

- structured state;
- UI interattiva;
- model context + structured content;
- proof/certificate;
- account linking;
- continuation in Ardesia;
- pen/whiteboard handoff.

Flow:

```text
ChatGPT/Claude
  ↓
solve/inspect circuit
  ↓
ProofReplay MCP App
  ↓
user clicks “prova tu”
  ↓
WhiteboardMini
  ↓
user wants full workspace
  ↓
Open in Ardesia
  ↓
same proof/session imported
  ↓
LessonOS event continuity
```

Se questo funziona, MCP Apps ha dimostrato valore reale per l'architettura Ardesia.

---

# 21. Metriche MCP per Ardesia

Non misurare “tool calls”.

Misurare:

- host → successful capability completion;
- host → account link conversion;
- host → Ardesia continuation rate;
- compact UI completion rate;
- text fallback success;
- MRTR completion/abandonment;
- cross-host resumed session rate;
- cost per acquired activated user;
- error/refusal by host;
- API compatibility regressions;
- security incidents / blocked attempts.

---

# 22. Rischi strategici

## Lock-in host

Mitigazione: standard-first + web/native system of record.

## Directory discovery deludente

Mitigazione: treat as optional acquisition; GitHub/web/B2B remain.

## UX ridotta in iframe

Mitigazione: compact surface, deep-link to Ardesia.

## MCP spec evolution

Mitigazione: adapter isolated + conformance suite + versioned public contract.

## Surface proliferation

Mitigazione: one domain kernel, shared design primitives, no duplicated business logic.

## Security expansion

Mitigazione: least privilege and dedicated harness.

---

# 23. Decisione finale

**Sì: MCP Apps dovrebbe diventare un cardine importante di Ardesia.**

Ma il significato corretto di “cardine” è:

> Ardesia progetta le proprie capacità in modo che possano vivere nativamente sulla sua lavagna e, quando ha senso, essere esportate come strumenti/UI MCP cross-host.

Non:

> Ardesia diventa un wrapper MCP o sposta la propria identità nelle directory ChatGPT/Claude.

La piattaforma durevole è:

```text
ARDESIA
= domain capabilities
+ ToolHost
+ LessonOS
+ board/pen workspace
+ verification/evidence
+ adapters (native, web, MCP)
```

MCP Apps rende quelle capacità **distribuibili nel luogo in cui l'utente sta già parlando con l'AI**. È una leva eccezionalmente coerente con Ardesia; resta comunque una leva, non il prodotto.

---

# 24. Provenienza

Questo documento consolida:

- conversazione allegata sugli MCP Apps e pubblicazione/monetizzazione;
- piano Kirchhoff con ricerca MCP 2026-07-28 e MCP Apps;
- architecture spine e UX Kirchhoff;
- note BMAD;
- stato Ardesia/ToolHost/Simulation Plugin/LessonOS consultato nel repository nella conversazione corrente.

Per il corpus integrale: `kirchhoff_00_corpus_fonti_integrali.md`.
