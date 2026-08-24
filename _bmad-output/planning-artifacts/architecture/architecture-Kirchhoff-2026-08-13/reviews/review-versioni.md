# Review — lente: versioni e attualità tecnologica

**Documento sotto esame:** `ARCHITECTURE-SPINE.md` (974 righe, 35 AD, v2 del 15 agosto 2026)
**Repo:** `/Users/andreamarro/MATJOURNEY/kirchhoff/` — `pyproject.toml`, `uv.lock`, `.venv/pyvenv.cfg`
**Data della verifica:** 15 agosto 2026. Ogni versione dichiarata corrente in questo documento è stata
letta sul web in questa esecuzione, con URL e data riportati in tabella.

---

## Perché questa lente

La riga 758 dello spine dichiara il debito con parole sue:

> ⚠️ **Versioni non verificate sul web in questa esecuzione.** Provengono dal documento sorgente
> dell'utente. Vanno confermate contro le release correnti prima di essere pinnate.

E il *Deferred* (riga 951) rimanda la verifica «prima del primo commit». Il primo commit c'è già:
`uv.lock` esiste, con nove pacchetti risolti, dal 13 agosto. Questa review salda il debito.

Le sette review già rientrate — avversario, confini, continuità visuale, invarianti, privacy e
percezione, testabilità, veridicità — **non toccano nessuna riga della sezione `## Stack`**. Ho
letto i loro rilievi e non ne ripeto nessuno: la superficie di questa lente è disgiunta dalle altre.

---

## Verdetto in una riga

Lo spine nomina **12 righe di stack**, di cui **8 ancora letteralmente «da confermare»**; le ho
verificate tutte e **una sola scelta è oggi sbagliata** — `PySpice`, ferma al 2021 e capace di
parlare con `ngspice` fino alla versione 34 mentre la corrente è la 47 — mentre il resto è allineato
o allineabile con un numero; il difetto più grande non è una versione arretrata ma il fatto che
**nessuna riga dello Stack ha oggi una controparte nel repo**, dove `dependencies = []` e nessun
modulo importa qualcosa fuori dalla libreria standard.

**Fuori supporto o inadatte: 1 su 28 tecnologie esaminate.**

| | Tecnologia | Verdetto |
|---|---|---|
| 1 | **PySpice** (riga 769, «ngspice via PySpice») | **inadatta allo scopo** — ultima release 15 maggio 2021, supporta ngspice ≤ 34, la corrente è la 47 |

Nessun'altra tecnologia nominata risulta fuori supporto, deprecata o ritirata. Due sono **arretrate
ma supportate** (`uv` nell'ambiente locale; `Vite 7` come dichiarata dal documento sorgente, che lo
spine però non riporta). Una è **non dichiarata pur essendo vincolante**: Node.js.

**Voci «da confermare» rimaste: 8.** Tutte chiuse qui sotto con una raccomandazione motivata;
nessuna resta aperta per impossibilità di verifica.

---

## 1. La tabella completa

Formato: `nome · dichiarata nello spine · corrente al 15 ago 2026 (fonte) · in uso nel repo · verdetto`

### A — Le dodici righe della sezione `## Stack` (righe 762-775)

| # | Nome | Dichiarata nello spine | Corrente al 15 ago 2026 (fonte, consultata oggi) | In uso nel repo | Verdetto |
|---|---|---|---|---|---|
| A1 | **Python** | `3.12+` (riga 764) | ramo **3.14** in bugfix (ultimo stabile); **3.13** in bugfix; **3.12 in fase *security*** fino a 2028-10 — [devguide.python.org/versions](https://devguide.python.org/versions/) | `requires-python = ">=3.12"` (`pyproject.toml:5`); **`.venv` gira CPython 3.13.14** (`.venv/pyvenv.cfg`) | **arretrata ma supportata** — il pavimento dichiarato è un ramo che riceve solo fix di sicurezza, e non è l'interprete reale |
| A2 | **FastAPI** | «da confermare» (riga 765) | **0.141.1**, 29 lug 2026, richiede Python ≥3.10 — [pypi.org/project/fastapi](https://pypi.org/project/fastapi/) | **assente** (`dependencies = []`) | **allineata** — scelta corrente e adeguata; manca il numero |
| A3 | **Pydantic** | «da confermare» (riga 765) | **2.13.4**, 6 mag 2026 — [pypi.org/project/pydantic](https://pypi.org/project/pydantic/) | **assente** | **allineata** — manca il numero |
| A4 | **SymPy** | «da confermare» (riga 766) | **1.14.0**, 27 apr 2025; nessuna 1.15 stabile — [pypi.org/project/sympy](https://pypi.org/project/sympy/), [github.com/sympy/sympy/releases](https://github.com/sympy/sympy/releases) | **assente** | **allineata** — 16 mesi senza release *sono* il ritmo di SymPy, non un abbandono |
| A5 | **lcapy** | «da confermare» (riga 767) | **1.26**, 28 set 2025; master a `1.27dev`; **un solo manutentore** — [pypi.org/project/lcapy](https://pypi.org/project/lcapy/), [setup.py su master](https://raw.githubusercontent.com/mph-/lcapy/master/setup.py) | **assente** | **arretrata ma supportata** — con due riserve: bus factor 1 e una superficie di disegno che collide con AD-10/AD-18/AD-31 (rilievo V5) |
| A6 | **NetworkX** | «da confermare» (riga 768) | **3.6.1**, 8 dic 2025; richiede `Python !=3.14.1, >=3.11` — [pypi.org/project/networkx](https://pypi.org/project/networkx/) | **assente** | **allineata** — porta però un vincolo puntuale sull'interprete (§4) |
| A7 | **ngspice** (il simulatore) | «v2, differito» (riga 769) | **47**, 11 ago 2026 — [ngspice.sourceforge.io/news.html](https://ngspice.sourceforge.io/news.html) | **assente** | **allineata** — il simulatore è vivo e recentissimo |
| A8 | **PySpice** (il binding) | nessuna versione; solo «via PySpice» (riga 769) | **1.5**, **15 maggio 2021**; dichiara supporto a «Ngspice **up to version 34**» — [pypi.org/project/PySpice](https://pypi.org/project/PySpice/), [github.com/PySpice-org/PySpice](https://github.com/PySpice-org/PySpice) | **assente** | 🔴 **inadatta allo scopo** — 13 major di distanza dal simulatore che deve pilotare |
| A9 | **SDK MCP Python (`mcp`)** | «revisione protocollo 2026-07-28» (riga 770) | **2.0.0**, 28 lug 2026, implementa la revisione 2026-07-28 — [pypi.org/project/mcp](https://pypi.org/project/mcp/), [github.com/modelcontextprotocol/python-sdk/releases](https://github.com/modelcontextprotocol/python-sdk/releases) | **assente** | **allineata** sulla revisione — ma AD-16 non recepisce ciò che quella revisione ha rotto (rilievo V3) |
| A10 | **PostgreSQL** | «da confermare» (riga 771) | **18.6** (13 ago 2026); 18 è l'ultima major; **14 esce di supporto il 12 nov 2026** — [postgresql.org/support/versioning](https://www.postgresql.org/support/versioning/) | **assente** | **allineata** — da pinnare, ma vedi A11 |
| A11 | **Supabase** | «(Supabase, regione UE)» (riga 771) | default per i nuovi progetti: **Postgres 17**; supporto Supabase a PG 14 finito il **1 lug 2026** — [supabase.com/changelog](https://supabase.com/changelog/45827-deprecation-notice-support-for-postgres-14-ending-on-1st-july-2026) | **assente** | **allineata** — attenzione: pinnare «PostgreSQL 18» contraddirebbe il fornitore nominato nella stessa cella |
| A12 | **Redis** | «da confermare» (riga 772) | client Python `redis` **8.1.0** (30 lug 2026, [pypi](https://pypi.org/project/redis/)); server linea **8.x**, **tri-licenza RSALv2 / SSPLv1 / AGPLv3** dalla 8.0 — [redis.io/legal/licenses](https://redis.io/legal/licenses/) | **assente** | **allineata** — la licenza è una decisione da registrare, non da ereditare (§4) |
| A13 | **RQ** | «da confermare» (riga 772) | **2.10.0**, 20 giu 2026, richiede Python ≥3.10 — [pypi.org/project/rq](https://pypi.org/project/rq/) | **assente** | **allineata** |
| A14 | **React** | «da confermare» (riga 773) | **19.2.8** — [registry.npmjs.org/react/latest](https://registry.npmjs.org/react/latest) | **assente** (nessun `package.json` nel repo) | **allineata** |
| A15 | **Vite** | «da confermare» (riga 773) | **8.2.1**; `engines.node: "^20.19.0 \|\| >=22.12.0"` — [registry.npmjs.org/vite/latest](https://registry.npmjs.org/vite/latest) | **assente** | **allineata** se pinnata a 8; il documento sorgente diceva 7 (rilievo V7) |
| A16 | **Tailwind CSS** | «da confermare» (riga 773) | **4.3.3** — [registry.npmjs.org/tailwindcss/latest](https://registry.npmjs.org/tailwindcss/latest) | **assente** | **allineata** |
| A17 | **CircuiTikZ** | «da confermare» (riga 774) | **1.8.6**, 24 mag 2026 — [ctan.org/pkg/circuitikz](https://ctan.org/pkg/circuitikz) | **assente** | **allineata** — è il pezzo più aggiornato dell'intero stack |
| A18 | **pdflatex / pdfTeX** | «da confermare» (riga 774) | **TeX Live 2026**, rilasciata 1 mar 2026; pdfTeX **1.40.29** (3 mar 2026) — [tug.org/texlive](https://www.tug.org/texlive/) | **assente** | **allineata** — ma i «vincoli non negoziabili» di riga 777 non nominano la distribuzione (rilievo V10) |
| A19 | **OpenTelemetry** | «adapter candidato dell'`ObservationPort`, non il canale stesso» (riga 775) | `opentelemetry-sdk` **1.44.0**, 16 lug 2026, Python ≥3.10 — [pypi.org/project/opentelemetry-sdk](https://pypi.org/project/opentelemetry-sdk/) | **assente** | **allineata** — e la formulazione è quella giusta: l'invariante è il port, non il vettore |

### B — Tecnologie nominate altrove nello spine, o implicate dalle righe dello Stack

| # | Nome | Dichiarata nello spine | Corrente al 15 ago 2026 (fonte) | In uso nel repo | Verdetto |
|---|---|---|---|---|---|
| B1 | **MCP Apps / `ext-apps`** | `specification/2026-01-26/apps.mdx` (AD-16, riga 363) | **2026-01-26** è tuttora l'**unica revisione datata** dell'estensione (accanto a `draft`); identificatore `io.modelcontextprotocol/ui`, negoziato via il campo `extensions` delle capability — [github.com/modelcontextprotocol/ext-apps](https://github.com/modelcontextprotocol/ext-apps/tree/main/specification) | **assente** | **allineata** — e le tre citazioni normative di AD-16 sono verificate *verbatim* (vedi sotto) |
| B2 | **Node.js** | **mai nominato** — pur essendo imposto da A14-A16 | **24** Active LTS (attivo fino 20 ott 2026, sicurezza fino 30 apr 2028); **22** in manutenzione fino 30 apr 2027; **20 fuori supporto dal 30 apr 2026**; **26** Current — [endoflife.date/nodejs](https://endoflife.date/nodejs), [nodejs.org/en/about/previous-releases](https://nodejs.org/en/about/previous-releases) | **assente** | **non dichiarata** — runtime vincolante assente dal contratto (rilievo V6) |
| B3 | **PGF/TikZ** | **mai nominato** — pur essendo la base di CircuiTikZ (riga 774) | **3.1.12** — [ctan.org/pkg/pgf](https://ctan.org/pkg/pgf) | **assente** | **non dichiarata** |
| B4 | **Type checker** | dichiarato **assente** due volte, come premessa (righe 475 e 600) | non applicabile | assente: nessun `mypy`/`pyright`, nessuna sezione di type-checking in `pyproject.toml` | **non dichiarata come scelta** — è la giustificazione di due AD e non compare in nessuna tabella (rilievo V8) |
| B5 | **ULID** | convenzione sugli identificatori (riga 741) | nessuna libreria nominata; nessuna implementazione nel repo | **assente** | **non verificabile** — la convenzione esiste, l'implementazione non è vincolata. Non è un difetto oggi |
| B6 | **JSON-RPC 2.0** | AD-16 (riga 358) | specifica stabile dal 2010, invariata | **assente** | **allineata** |
| B7 | **Mermaid** | usato per i cinque diagrammi del documento | strumento di documentazione, non di runtime | non applicabile | **allineata** — fuori dalla superficie del contratto |

**Verifica testuale delle tre affermazioni normative di AD-16.** Le ho lette sulla fonte che AD-16
cita, e sono **corrette alla lettera**:

- `mimeType` **MUST be** `text/html;profile=mcp-app` — confermato;
- l'associazione al tool passa da **`_meta.ui.resourceUri`** — confermato, e la forma piatta
  `_meta["ui/resourceUri"]` risulta **deprecata**: lo spine usa già quella giusta;
- «*Tools MUST return meaningful content array even when UI is available*» — presente nel testo
  con livello **MUST**, esattamente come citato alla riga 361.

Fonte: `modelcontextprotocol/ext-apps`, `specification/2026-01-26/apps.mdx` e `specification/draft/apps.mdx`,
consultati il 15 agosto 2026. **AD-16 non ha errori di citazione.** Il problema è un altro, ed è V3.

### C — Presenti nel repo, assenti dallo spine

| # | Nome | Dichiarata nello spine | Corrente al 15 ago 2026 (fonte) | In uso nel repo | Verdetto |
|---|---|---|---|---|---|
| C1 | **pytest** | nessuna | **9.1.1**, 19 giu 2026 — [pypi.org/project/pytest](https://pypi.org/project/pytest/) | floor `>=8` (`pyproject.toml:9`); `uv.lock` risolve **9.1.1** | **allineata** — floor largo, lock stretto: la configurazione corretta |
| C2 | **pytest-cov** | nessuna | **7.1.0**, 21 mar 2026 — [pypi.org/project/pytest-cov](https://pypi.org/project/pytest-cov/) | floor `>=5`; lock **7.1.0** | **allineata** |
| C3 | **coverage** | nessuna | **7.15.4**, 6 ago 2026 — [pypi.org/project/coverage](https://pypi.org/project/coverage/) | lock **7.15.4** (transitiva) | **allineata** |
| C4 | **hatchling** (build backend) | nessuna | **1.32.0**, 11 ago 2026 — [pypi.org/project/hatchling](https://pypi.org/project/hatchling/) | `requires = ["hatchling"]` **senza vincolo** (`pyproject.toml:15`) | **allineata ma non vincolata** — build non riproducibile (rilievo V9) |
| C5 | **uv** | nessuna | **0.12.5**, 14 ago 2026 — [pypi.org/project/uv](https://pypi.org/project/uv/) | `.venv` creato da **0.11.8** (`.venv/pyvenv.cfg`) | **arretrata ma supportata** |
| C6 | **packaging** | nessuna | **26.3**, 4 ago 2026 — [pypi.org/project/packaging](https://pypi.org/project/packaging/) | lock **26.3** (transitiva) | **allineata** |
| C7 | colorama 0.4.6 · iniconfig 2.3.0 · pluggy 1.6.0 · pygments 2.20.0 | nessuna | *non verificate in questa esecuzione* | presenti in `uv.lock` come transitive di pytest | **non verificate** — fuori dalla superficie del contratto; le dichiaro come non controllate anziché assegnare un verdetto che non ho guadagnato |

---

## 2. Le otto voci «da confermare», chiuse

La riga 758 dice che i numeri vanno confermati «prima di essere pinnati». Ecco la chiusura, con la
motivazione. **Nessuna resta aperta.**

| Riga | Voce | Raccomandazione | Perché |
|---|---|---|---|
| 765 | FastAPI + Pydantic | `fastapi 0.141.x` · `pydantic 2.13.x` | Correnti entrambe. Nessun blocco: FastAPI ≥0.100 richiede Pydantic v2, e 2.13.4 è la v2 corrente. Lo `0.x` di FastAPI non è immaturità — è il suo schema di versionamento da sempre |
| 766 | SymPy | `sympy 1.14.x` | È la corrente. Anche lcapy vuole `sympy>=1.10.1`: nessun conflitto |
| 767 | lcapy | `lcapy 1.26` **più una clausola sulla superficie ammessa** | Vedi V5. Pinnare il numero senza recintare l'API di disegno lascia aperto un secondo motore di layout |
| 768 | NetworkX | `networkx 3.6.x` | Corrente. Porta con sé `Python !=3.14.1` — vincolo da riportare accanto ad A1 |
| 771 | PostgreSQL (Supabase, UE) | `PostgreSQL 17` | **Non 18.** Supabase serve 17 di default ai nuovi progetti; pinnare 18 significherebbe pinnare qualcosa che il fornitore nominato nella stessa cella non offre di default. AD-14 (row-level security) è nativo in entrambe |
| 772 | Redis + RQ | `redis 8.1.x` (client) · `rq 2.10.x` · **server: decidere fra Redis 8.x tri-licenza e Valkey** | La versione non è il problema; la licenza sì. Su un prodotto commerciale la scelta fra AGPLv3 e il fork BSD va **registrata**, non ereditata |
| 773 | React + Vite + Tailwind | `react 19.2.x` · `vite 8.2.x` · `tailwindcss 4.3.x` · **`node 24 LTS`** | Tre righe, non una. Il collasso in una cella è ciò che ha reso invisibile che il documento sorgente dicesse Vite **7** (V7) e che Node non fosse nominato affatto (V6) |
| 774 | CircuiTikZ + pdflatex | `circuitikz 1.8.6` · `pgf/tikz 3.1.12` · `TeX Live 2026` (pdfTeX 1.40.29) | Correnti. Va aggiunto PGF/TikZ, che CircuiTikZ richiede e lo spine non nomina |

La nona voce, riga 769 (`ngspice via PySpice`), **non si chiude con un numero**: si chiude
separando il simulatore dal binding. Vedi V1.

---

## 3. Rilievi

Severità: 🔴 critico · 🟠 alto · 🟡 medio.

---

### V1 🔴 — `PySpice` è ferma al 2021 e parla con `ngspice` fino alla 34; la corrente è la 47

**Dove:** `ARCHITECTURE-SPINE.md:769` — `| ngspice (via PySpice) | v2, differito |`
Correlati: riga 61 e 911 (`SpicePort` nell'elenco dei port), righe 954-956 (*Deferred*, Percorso C).

**I fatti verificati.**

| | |
|---|---|
| Ultima release di PySpice | **1.5**, **15 maggio 2021** — cinque anni e tre mesi fa |
| Versione di ngspice supportata da PySpice 1.5 | **fino alla 34**, dichiarato dal progetto stesso |
| Versione corrente di ngspice | **47**, **11 agosto 2026** — quattro giorni fa |
| Stato del progetto | non archiviato; il manutentore scrive «*PySpice is developed on my free time actually, so I could be busy with other tasks and less reactive*»; il forum di comunità è stato chiuso per mancanza di attività |
| Sintomo già documentato a monte | issue #307 «WARNING - Unsupported Ngspice version 35»; issue #379, stesso avviso sulla 43 |

**Perché è un rilievo e non «esiste qualcosa di più nuovo».** La novità non è un argomento, e non lo
sto usando. L'argomento è che **la coppia nominata dallo spine è rotta come coppia**: PySpice 1.5
non è vecchia in astratto, è vecchia *rispetto all'unica cosa che deve pilotare*. Tredici versioni
major di ngspice separano il binding dal simulatore, e il difetto si manifesta già dalla 35 con un
avviso di versione non supportata. Il Percorso C esiste per essere un **terzo motore indipendente**
che dia ad AD-5 un confronto fra *n* percorsi: un motore che gira su un binding che avvisa di non
riconoscere il simulatore non è indipendente, è rumoroso.

**Il costo di non chiuderlo ora è asimmetrico.** Oggi il Percorso C è differito e costa una riga
riscriverla. Quando il Percorso C arriva, la riga 769 è un vincolo dello spine e chi costruisce
l'adapter la legge come una decisione presa — e scopre il problema in installazione, che è
esattamente il modo in cui il *Deferred* alla riga 953 dice di **non** volerlo scoprire («il rischio
è di obsolescenza, non di divergenza» — qui è entrambe).

**Forma minima della correzione.** La riga 769 nomina **il simulatore**, non il binding:

```
| ngspice | 47 — Percorso C, v2, differito. Il binding Python è scelta di `adapters/spice`, non dello spine. |
```

Il port esiste già (righe 61 e 911): la scelta è **già confinata** dietro `SpicePort`, quindi non
c'è nulla da decidere oggi. Se si vuole nominare i candidati da valutare al momento del Percorso C —
`spicelib`, `ngspyce`, o l'invocazione a processo di `ngspice -b` con parsing del raw file — vanno
in una nota del *Deferred*, non nella tabella. **Ciò che va tolto dalla tabella è il pin implicito
su un binding fermo da cinque anni.**

---

### V2 🔴 — Lo Stack ha dodici righe, il repo ha zero dipendenze runtime, e nulla lega le due cose

**Dove:** `ARCHITECTURE-SPINE.md:756-775` contro `pyproject.toml:6` (`dependencies = []`) e
`ARCHITECTURE-SPINE.md:951-953` (*Deferred*, «prima del primo commit»).

**I fatti.** Ho letto tutti i `.py` sotto `src/`, `scripts/` e `tests/`. L'insieme completo degli
import non-stdlib è: **vuoto**. Gli unici moduli importati sono `argparse`, `ast`, `collections`,
`dataclasses`, `datetime`, `fractions`, `importlib`, `json`, `os`, `pathlib`, `random`, `re`,
`subprocess`, `sys`, `tempfile`, `time`, `typing` — più `pytest` nei test e i moduli interni di
`kirchhoff`. Il `uv.lock` contiene nove pacchetti, tutti di test o transitivi.

Nessuna delle dodici righe dello Stack — FastAPI, Pydantic, SymPy, lcapy, NetworkX, PySpice, SDK
MCP, PostgreSQL, Redis, RQ, React, CircuiTikZ, OpenTelemetry — ha una controparte nel repo.

**Perché è un rilievo.** Non perché il codice sia incompleto: Epic 1 è il gate di kill, e che
`domain/`, `eval/` e `ports/clock` siano gli unici pacchetti popolati è coerente col piano. Il
rilievo è che **la sezione `## Stack` non è oggi falsificabile da nulla**. Il warning della riga 758
resta vero al 100% e continuerà a esserlo anche dopo che questa review avrà fornito i numeri, perché
non esiste alcun meccanismo che leghi una riga della tabella a una riga di `pyproject.toml`. Lo
spine ha un test di confine per il dominio (`scripts/check_boundaries.py`), un test di copertura
del dominio (`scripts/check_domain_coverage.py`), e **nessun controllo sulle proprie dichiarazioni
di stack**. È la stessa figura che l'intero documento combatte altrove: una promessa senza soggetto.

C'è anche una piccola incoerenza di premessa da correggere: il *Deferred* dice «prima del primo
commit», e il primo commit è del 13 agosto.

**Forma minima della correzione.** Due modifiche, entrambe di testo tranne l'ultima riga:

1. Riga 951: da «prima del primo commit» a **«prima della prima dipendenza runtime»**.
2. Aggiungere allo stesso punto la condizione di verifica: *«una riga di `## Stack` senza versione
   pinnata, o con una versione che non compare in `pyproject.toml`, è un difetto di questo documento»*
   — la stessa forma che AD-15 usa per le metriche di §8 («una metrica di §8 che l'harness non
   calcola è un difetto dell'harness») e che AD-34 usa per le fonti («una metrica senza stadio
   emittente è un difetto di questo documento»). Lo spine ha già il pattern; qui non lo applica a sé.
3. Il controllo corrispondente sta accanto ai due script esistenti. È l'unica delle undici correzioni
   che chiude il debito **in modo permanente** anziché saldarlo una volta.

---

### V3 🟠 — AD-16 pinna la revisione giusta e non recepisce ciò che quella revisione ha rotto

**Dove:** `ARCHITECTURE-SPINE.md:770` (`revisione protocollo 2026-07-28`) e `:351-363` (AD-16).

**Il pin è corretto.** `mcp` **2.0.0**, rilasciato il **28 luglio 2026**, implementa la revisione
2026-07-28 e mantiene compatibilità con le precedenti. Nessun rilievo sul numero.

**Ciò che la revisione 2026-07-28 ha cambiato, e che AD-16 non nomina:**

| # | Cambio | Riferimento |
|---|---|---|
| 1 | **Le sessioni di protocollo e l'header `Mcp-Session-Id` sono rimossi** dal trasporto Streamable HTTP | SEP-2567 |
| 2 | **L'handshake `initialize` / `notifications/initialized` è rimosso**: versione di protocollo e identità del client viaggiano in `_meta` (`io.modelcontextprotocol/protocolVersion`, `/clientInfo`, `/clientCapabilities`) e la negoziazione passa da una nuova RPC **`server/discover`** | SEP-2575 |
| 3 | Il trasporto richiede gli header **`Mcp-Method`** e **`Mcp-Name`** per il routing | SEP-2243 |
| 4 | **MCP Apps diventa un'estensione versionata**, non una funzione del core: si registra sotto `io.modelcontextprotocol/ui` e si negozia attraverso il campo **`extensions`** di `ClientCapabilities` e `ServerCapabilities` | framework estensioni 2026-07-28 |

Fonti: [blog.modelcontextprotocol.io — 2026-07-28 release](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/),
[stacktr.ee — MCP 2026-07-28 spec: every breaking change](https://stacktr.ee/blog/mcp-2026-spec-changes),
consultati il 15 agosto 2026.

**Perché conta.** AD-16 descrive con precisione lo schema `ui://`, il `mimeType`, `_meta.ui.resourceUri`,
i due campi `content` / `structuredContent` e il trasporto JSON-RPC su postMessage — tutto corretto —
ma **non dice che l'estensione va negoziata**. Un'unità che implementa AD-16 alla lettera costruisce
un server che espone la risorsa UI e non dichiara mai `io.modelcontextprotocol/ui` nel campo
`extensions`: l'host non attiva il pannello, e il difetto si manifesta come «la UI non compare»,
senza che nessuna riga dello spine sia stata violata. È la stessa forma di difetto che AD-32 chiude
per il `TruthfulnessGate` — «due gate definiti e uno solo collegato».

**Un fatto positivo, verificato, che vale la pena registrare.** AD-6 (righe 192-200) dice «il server
è stateless per richiesta» e mette lo stato in `resume_ref` firmato HMAC. Con SEP-2567 questa non è
più una scelta prudente: **è ciò che il protocollo ora impone.** È l'unica riga dello spine che la
nuova revisione *rafforza* invece di invecchiare, e merita una riga che lo dica — perché altrimenti
al prossimo giro qualcuno la leggerà come una complicazione da semplificare.

**Un vincolo implicito che nasce dal salto di major.** `mcp` 2.0.0 introduce un **limite di 4 MiB
sul corpo delle richieste HTTP**, oltre a rinomine di API (`FastMCP` → `MCPServer`, campi in
snake_case, `Client(cache=False)` → `Client(cache=None)`, rimozione della configurazione via
variabili `MCP_*`); la linea 1.x riceve solo fix di sicurezza. Il limite di 4 MiB tocca
direttamente FR-1 e AD-9: una foto di circuito caricata **attraverso la superficie assistente** ha
un tetto che la superficie HTTP della PWA non ha. Non è un difetto dello spine — è un vincolo che
si scopre in esecuzione se nessuno lo scrive.

**Forma minima della correzione.** Tre righe in AD-16, dopo la riga 362:

> L'estensione UI è registrata sotto `io.modelcontextprotocol/ui` e **negoziata attraverso il campo
> `extensions`** delle capability di client e server: una risorsa `ui://` esposta senza
> l'estensione dichiarata non viene mai renderizzata. Dalla revisione 2026-07-28 **non esiste
> handshake `initialize`** — versione di protocollo e identità del client viaggiano in `_meta` e la
> negoziazione passa da `server/discover` — e il trasporto richiede gli header `Mcp-Method` e
> `Mcp-Name`. Il corpo di una richiesta HTTP è limitato a 4 MiB: un'immagine sorgente che eccede
> non entra dalla superficie assistente.

Più una riga in AD-6: *«dalla revisione 2026-07-28 le sessioni di protocollo sono rimosse: questo
invariante è ora imposto dal protocollo, non solo scelto».*

---

### V4 🟠 — Due date di revisione, due linee diverse, e lo spine non le distingue

**Dove:** `ARCHITECTURE-SPINE.md:770` («revisione protocollo **2026-07-28**») e `:363` («Fonte:
`modelcontextprotocol/ext-apps`, `specification/**2026-01-26**/apps.mdx`»).

**I fatti verificati.** Non sono in contraddizione: sono **due linee di versionamento distinte**.

- **2026-07-28** è la revisione del **protocollo core**, implementata da `mcp` 2.0.0.
- **2026-01-26** è la revisione dell'**estensione MCP Apps**, e al 15 agosto 2026 la cartella
  `specification/` di `ext-apps` contiene esattamente due voci: `2026-01-26` e `draft`. **2026-01-26
  è tuttora l'unica revisione datata dell'estensione**, quindi la citazione di AD-16 è aggiornata.

**Perché è comunque un rilievo.** Due date diverse nello stesso AD, senza dire che appartengono a
due linee, sono un invito a «correggere» quella che sembra vecchia. Lo spine ha appena speso
un'emendamento intero (AD-24) su un caso identico — due campi omonimi, `provenance` e
`source_asset_ref` — argomentando che *«due nomi distinti, due controlli distinti»*. Qui sono due
date distinte per due contratti distinti, e lo spine le presenta come se fossero la stessa cosa.

**Forma minima della correzione.** La riga 770 diventa:

```
| SDK MCP Python (`mcp`) | 2.0.0 — protocollo core **2026-07-28**; estensione Apps **2026-01-26** (`io.modelcontextprotocol/ui`) |
```

Due date, due linee, nominate. Zero decisioni.

---

### V5 🟠 — `lcapy` ha un manutentore, e disegna schemi CircuiTikZ: fa la cosa che AD-10, AD-18 e AD-31 vietano

**Dove:** `ARCHITECTURE-SPINE.md:767` (`| lcapy | da confermare |`), contro `:261-271` (AD-10
emendato), `:374-394` (AD-18) e `:649-665` (AD-31).

**I fatti verificati.**

- lcapy **1.26**, 28 settembre 2025; master a `1.27dev`; **un solo manutentore** dichiarato su PyPI.
- `install_requires` su master: `matplotlib`, `scipy`, `numpy`, `sympy>=1.10.1`, `networkx`,
  `IPython`, `setuptools`, `wheel`, `packaging`, **`importlib`**, `property_cached`. `python_requires >=3.7`,
  **senza limite superiore** — nessuna garanzia dichiarata su 3.13.
  `importlib` è un modulo della **libreria standard** da Python 3.1: una dipendenza PyPI con quel
  nome risolve a un pacchetto di terze parti, non alla stdlib. Va verificato al momento del pin —
  è il genere di riga che rompe un'installazione pulita e che non si scopre leggendo il changelog.
- **lcapy produce macro CircuiTikZ per disegnare netlist**: «*LaTeX CircuiTikz macros are output
  producing text-book quality schematics […] Netlists require drawing hints to describe the component
  orientation, size, color […] These hints are used to automatically position the components.*»
  Fonte: [github.com/mph-/lcapy](https://github.com/mph-/lcapy), [PeerJ CS-875](https://peerj.com/articles/cs-875/).

**Il difetto architetturale.** Lo spine dice, in tre punti:

- AD-18: *«Il dominio non produce alcuna geometria: `p_k` e `p_{k+1}` vivono nel `LayoutIR`, di cui
  `render/layout` è scrittore unico»* e *«dalla v2 non sa nemmeno cosa sia una posizione»*.
- AD-10 emendato: *«l'SVG semantico verificato è la sorgente unica di ogni altro formato. `export()`
  non ri-renderizza»*; ogni formato non semantico è **derivato**, e porta l'impronta dell'SVG.
- AD-31: l'annotazione è **derivata** dalla geometria, mai il contrario.

lcapy fa esattamente il contrario di tutte e tre: prende una netlist, **posiziona i componenti da
sé** su suggerimenti di disegno, ed **emette CircuiTikZ**. Se `domain/solve` importa lcapy per la
MNA simbolica — che è l'uso per cui è nominato — l'API di schematica arriva nello stesso namespace.
Il giorno in cui qualcuno la chiama, nasce un **secondo motore di layout** che non passa da
`render/layout`, non conosce `LayoutPatch`, non rispetta `Pₖ` (AD-22), non obbedisce all'ordine dei
layer (AD-23) e non attraversa il round-trip (AD-5, controllo 7). E produce CircuiTikZ, cioè
esattamente il formato che AD-10 vuole **derivato** dall'SVG certificato.

Non sto dicendo che accadrà. Sto dicendo che il Design Paradigm (righe 53-56) dichiara di non voler
affidare questa classe di protezione alla disciplina: *«se quella separazione vive solo nella
disciplina di chi scrive, si rompe al primo "aggiungo qui una chiamata […] per fare prima"»*.
Il paradigma difende quel confine contro gli adapter e contro `render/`; **non lo difende contro una
libreria di dominio che porta un renderer dentro**.

**Il bus factor è la riserva minore, ma va detto.** Un manutentore, ultima release undici mesi fa.
Non è abbandono e non lo chiamo tale — lcapy è il pezzo giusto per la MNA simbolica e non ha
concorrenti seri. È una dipendenza da tenere sotto osservazione, non da evitare.

**Forma minima della correzione.** Due cose:

1. La riga 767 dichiara **quale superficie di lcapy è ammessa**:
   `| lcapy | 1.26 — solo analisi simbolica. L'API di schematica (`Circuit.draw`, `lcapy.schematic`) è vietata: il disegno è di `render/` (AD-10, AD-18, AD-31). |`
2. Il divieto diventa il **settimo recinto** di `scripts/check_boundaries.py`, accanto ai cinque di
   AD-21 (righe 466-474) e al sesto di AD-26 (righe 601-602): *un `import` di `lcapy.schematic`
   sotto `domain/` o `render/` è un fallimento di CI*. AD-21 lo dice già meglio di me — *«Non è un
   errore di compilazione […] è il controllo `ast` di `check_boundaries.py` a essere l'unica difesa
   reale»*. Lo stesso vale qui, e il recinto costa una voce nella lista che la prima storia di Epic 1
   sta già estendendo da uno a sei.

---

### V6 🟠 — Node.js non è nominato, e tre righe dello Stack lo vincolano

**Dove:** `ARCHITECTURE-SPINE.md:773` — `| React + Vite + Tailwind (PWA) | da confermare |`.
Node.js non compare in nessuna riga dello Stack, né altrove nelle 974 righe.

**I fatti verificati.**

- Vite **8.2.1** dichiara `engines.node: "^20.19.0 || >=22.12.0"`.
- Node **20** è **fuori supporto dal 30 aprile 2026**.
- Node **22** è in manutenzione **fino al 30 aprile 2027**.
- Node **24** è l'**Active LTS**: supporto attivo fino al **20 ottobre 2026**, sicurezza fino al
  **30 aprile 2028**.
- Node **26** è Current (rilasciato 5 maggio 2026), entrerà in Active LTS il 27 ottobre 2027.

**La finestra reale è dunque Node 22 o 24, e si stringe fra due mesi**: il 20 ottobre 2026 Node 24
passa a sole correzioni di sicurezza, e Node 22 resta l'unico LTS in manutenzione fino ad aprile 2027.

**Perché è un rilievo.** Un runtime non nominato è un runtime che ognuno sceglie da sé, e la
divergenza si manifesta al primo `npm ci` — in installazione, non in review. Lo spine è
scrupolosissimo sul runtime Python (riga 764, più due AD che argomentano sull'assenza di type
checker) e completamente muto sul runtime JavaScript, benché tre delle sue dodici righe di stack
girino lì.

**Forma minima della correzione.** Una riga nella tabella `## Stack`:

```
| Node.js | 24 LTS (finestra imposta da Vite 8: `^20.19 || >=22.12`; Node 20 è fuori supporto dal 30 apr 2026) |
```

---

### V7 🟡 — Il documento sorgente pinnava tre versioni frontend; lo spine le ha collassate in «da confermare», e una era invecchiata

**Dove:** `ARCHITECTURE-SPINE.md:773` contro
`_bmad-output/planning-artifacts/briefs/brief-Kirchhoff-2026-08-13/addendum.md:103`.

**I fatti.** L'addendum del brief — che la riga 758 indica come «documento sorgente dell'utente» —
dice: *«React 19 + Vite 7 + Tailwind 4 PWA»*. Lo spine ha collassato le tre in una cella e le ha
declassate a «da confermare», **perdendo l'informazione che c'era**.

Al 15 agosto 2026:

| Dal documento sorgente | Corrente | Verdetto |
|---|---|---|
| React **19** | **19.2.8** | allineata |
| Vite **7** | **8.2.1** | **una major indietro** |
| Tailwind **4** | **4.3.3** | allineata |

**Perché è un rilievo.** Due delle tre erano giuste e una no, e il collasso in una cella sola le ha
rese indistinguibili: nella forma «da confermare» non c'è modo di accorgersi che una delle tre era
già scaduta. È lo stesso difetto di forma che AD-15 si autoinfligge e poi corregge — *«un inciso che
enumera è una restrizione travestita da chiarimento»* — qui declinato al contrario: **una cella che
aggrega è un'enumerazione travestita da riga**.

**Forma minima della correzione.** La riga 773 diventa tre righe:

```
| React     | 19.2.x  |
| Vite      | 8.2.x   |
| Tailwind  | 4.3.x   |
```

Più la riga Node di V6. Quattro righe al posto di una, ciascuna verificabile da sola.

---

### V8 🟡 — «Lo stack è Python senza type checker» è la premessa di due AD, e non è registrata come scelta

**Dove:** `ARCHITECTURE-SPINE.md:475` (AD-21) e `:600` (AD-26).

**Il testo, due volte.**

- AD-21, riga 475: *«**Non è un errore di compilazione.** Lo stack è Python senza type checker: la
  frase "un adapter importato dal dominio è un errore di compilazione" del paradigma è **falsa**, ed
  è il controllo `ast` di `check_boundaries.py` a essere l'unica difesa reale.»*
- AD-26, riga 600: *«Il vincolo **non è nel tipo**: lo stack è Python senza type checker, e
  affermare il contrario ripeteva qui la stessa figura che AD-21 dichiara esplicitamente falsa. È il
  **sesto recinto** di `check_boundaries.py`.»*

**Il repo conferma il fatto.** Nessun `mypy`, nessun `pyright`, nessuna sezione di type-checking in
`pyproject.toml`; nessun linter (`ruff` assente). Le uniche uscite di qualità sono `pytest` +
`pytest-cov` con `--cov-fail-under=95` (`pyproject.toml:22`) e i due script
`scripts/check_boundaries.py` e `scripts/check_domain_coverage.py`.

**Perché è un rilievo.** L'assenza di type checker non è un dettaglio d'ambiente: è la **premessa
che degrada due invarianti** da «errore di compilazione» a «controllo `ast` in uno script». Questo la
rende una decisione di architettura a tutti gli effetti — e le decisioni di architettura, in questo
documento, stanno negli AD o nelle tabelle, non come inciso dentro l'argomentazione di un'altra
regola. Oggi compare due volte come *constatazione*, mai come *scelta*.

**Non propongo di aggiungere un type checker.** È una scelta del proprietario e non è il mio ruolo
farla. Il rilievo è che la scelta non è scritta dove si scrivono le scelte.

**Forma minima della correzione.** Una riga nella tabella `## Stack`:

```
| Type checker | nessuno — scelta esplicita. I confini architetturali sono retti dal controllo `ast` di `scripts/check_boundaries.py` (AD-21, AD-26), non dal sistema di tipi. |
```

Con quella riga, le righe 475 e 600 citano una decisione invece di constatare un'assenza.

---

### V9 🟡 — Il build backend non è vincolato, e l'ambiente locale è già disallineato

**Dove:** `pyproject.toml:14-16` e `.venv/pyvenv.cfg`.

**I fatti.**

- `[build-system] requires = ["hatchling"]` — **nessun vincolo di versione**. hatchling corrente:
  **1.32.0**, 11 agosto 2026. `uv.lock` blocca le dipendenze, **non blocca il backend di build**:
  la build non è riproducibile.
- `.venv/pyvenv.cfg` riporta `uv = 0.11.8`; uv corrente è **0.12.5** (14 agosto 2026).
- `.venv/lib/python3.13/site-packages/` contiene **soltanto** l'installazione editable di
  `kirchhoff`: `pytest` e `pytest-cov`, presenti in `uv.lock`, non sono installati in
  quell'ambiente. La suite gira altrove (`uv run` con un ambiente effimero) o non gira da lì.

**Perché è un rilievo (medio, non alto).** Niente di questo rompe qualcosa oggi. Ma AD-35 impone al
rendering di essere «deterministico per costruzione, non per disciplina», e la stessa logica vale un
piano sotto: una build il cui backend non è pinnato è una build che può cambiare comportamento senza
che nessun file del progetto cambi. È la forma più economica di non determinismo.

**Forma minima della correzione.** Una riga:

```toml
requires = ["hatchling>=1.32,<2"]
```

Il resto — uv locale, `.venv` parziale — è igiene di postazione, non contratto. Lo segnalo perché
insieme al fatto che `dependencies = []` (V2) descrive un repo in cui **nessuna delle affermazioni
di ambiente dello spine è oggi osservabile**.

---

### V10 🟡 — I «vincoli d'ambiente LaTeX non negoziabili» non nominano l'ambiente

**Dove:** `ARCHITECTURE-SPINE.md:777-778` — *«Vincoli d'ambiente LaTeX noti e non negoziabili:
niente `lmodern`, niente babel italiano, label CircuiTikZ con `=` racchiusi in graffe.»*

**I fatti verificati.**

| | |
|---|---|
| Distribuzione corrente | **TeX Live 2026**, rilasciata **1 marzo 2026** |
| Motore | **pdfTeX 1.40.29** (3 marzo 2026) |
| CircuiTikZ | **1.8.6**, 24 maggio 2026 |
| PGF/TikZ (base di CircuiTikZ) | **3.1.12** — **non nominato dallo spine** |

**Perché è un rilievo.** Un vincolo dichiarato «non negoziabile» senza la versione dell'ambiente in
cui è stato osservato **non è verificabile**: se i tre vincoli nascono da un TeX Live precedente,
uno o più possono essere spariti, cambiati o essersi spostati. Il terzo in particolare — le label
con `=` racchiusi in graffe — è il genere di comportamento che CircuiTikZ ha modificato più volte fra
minor. E PGF/TikZ, che CircuiTikZ richiede, non compare nella riga 774: la catena LaTeX dello spine
ha due anelli su tre.

**Forma minima della correzione.** Riga 774 e riga 777:

```
| CircuiTikZ + PGF/TikZ + pdflatex | circuitikz 1.8.6 · pgf/tikz 3.1.12 · TeX Live 2026 (pdfTeX 1.40.29) |
```

> Vincoli d'ambiente LaTeX **osservati su TeX Live 2026 / CircuiTikZ 1.8.6**: niente `lmodern`,
> niente babel italiano, label CircuiTikZ con `=` racchiusi in graffe. **Da riverificare a ogni
> cambio di distribuzione.**

---

### V11 🟡 — Il pavimento Python è un ramo in sola sicurezza, e non è l'interprete su cui il progetto gira

**Dove:** `ARCHITECTURE-SPINE.md:764` (`| Python | 3.12+ |`) e `pyproject.toml:5`
(`requires-python = ">=3.12"`).

**I fatti verificati.**

| Ramo | Stato al 15 ago 2026 | Fine vita |
|---|---|---|
| 3.12 | **security** — solo fix di sicurezza | ott 2028 |
| 3.13 | bugfix | ott 2029 |
| 3.14 | bugfix — **ultimo stabile** | ott 2030 |
| 3.15 | prerelease | — |

Il `.venv` del repo gira **CPython 3.13.14**.

**Perché è un rilievo, e perché è medio e non alto.** `>=3.12` è un **pavimento**, non un pin, e
3.13 lo soddisfa: nulla è rotto. Ma il pavimento dichiarato è più basso dell'interprete reale, e la
distanza non è registrata da nessuna parte. Nessuna delle altre righe dello Stack impone più di
Python 3.10 (FastAPI, RQ, redis, coverage, hatchling, OpenTelemetry, `mcp`) o 3.11 (NetworkX): il
vincolo stringente del progetto **non è nello Stack, è nella `.venv`**. E c'è un `.python-version`
mancante, quindi la versione reale dipende da cosa `uv` trova sulla macchina.

**Forma minima della correzione.** La riga 764 dichiara due numeri invece di uno:

```
| Python | floor 3.12 (`requires-python`) · runtime di riferimento 3.13.x |
```

Più un `.python-version` allineato. Zero decisioni: registra ciò che è già vero.

---

## 4. Vincoli impliciti — quelli che si scoprono in installazione

Sette, tutti verificati oggi. Nessuno è visibile leggendo la sezione `## Stack`.

| # | Vincolo | Da chi | Conseguenza |
|---|---|---|---|
| 1 | **Node `^20.19 \|\| >=22.12`** | Vite 8.2.1 | Node 20 è fuori supporto: la finestra reale è **22 o 24**, e si restringe il 20 ott 2026. Vedi V6 |
| 2 | **`Python !=3.14.1`** | NetworkX 3.6.1 | Esclusione puntuale di un singolo patch di CPython. Il tipo di riga che fa fallire un'installazione senza che nulla nel progetto sia cambiato |
| 3 | **ngspice ≤ 34** | PySpice 1.5 | Il Percorso C non può girare sul simulatore corrente col binding nominato. Vedi V1 |
| 4 | **corpo HTTP ≤ 4 MiB** | `mcp` 2.0.0 | Un'immagine sorgente oltre 4 MiB **non entra dalla superficie assistente**, mentre entra dalla PWA. Tocca FR-1 e AD-9, e nessuno dei due lo dice |
| 5 | **scipy + numpy + matplotlib + IPython nel processo** | lcapy 1.26 | Non viola AD-2 — le Trasformazioni restano pure — ma porta `matplotlib` in un servizio che per AD-18 «non sa cosa sia un pixel». Superficie di attacco e tempo di avvio, non correttezza |
| 6 | **licenza del server Redis** | Redis 8.x | Tri-licenza RSALv2 / SSPLv1 / **AGPLv3**. Su un prodotto commerciale la scelta va **fatta**, e il fork Valkey (BSD) è il termine di confronto. Lo spine non ha una colonna licenza |
| 7 | **Postgres 17, non 18** | Supabase | Il default per i nuovi progetti Supabase è **17**. Pinnare «PostgreSQL 18» nella stessa cella che nomina Supabase è una contraddizione interna alla riga 771 |

---

## 5. Cosa NON è un rilievo — verificato e scartato

Sei porte che sembravano aperte e sono chiuse. Le elenco perché il valore di questa lente sta anche
in ciò che **non** va toccato.

1. **SymPy 1.14.0 è di aprile 2025 ed è la corrente.** Nessuna 1.15 stabile al 15 agosto 2026.
   Sedici mesi senza release non sono un abbandono: sono la cadenza di SymPy. Verificato su PyPI e
   sulla pagina delle release di GitHub. **Nessuna azione.**
2. **FastAPI è ancora a `0.x` (0.141.1).** Non è un segnale di immaturità: è lo schema di
   versionamento del progetto da sempre, e 0.141.1 è di diciassette giorni fa. **Nessuna azione.**
3. **`pytest>=8` e `pytest-cov>=5` risolvono a 9.1.1 e 7.1.0**, cioè alle correnti. I floor sono
   larghi, il `uv.lock` è al giorno: è esattamente la configurazione giusta — floor generoso, lock
   stretto. **Nessuna azione.**
4. **OpenTelemetry declassato ad «adapter candidato» (riga 775) è la formulazione corretta.**
   L'invariante di AD-34 è l'esistenza dell'`ObservationPort`, non il vettore che lo implementa.
   `opentelemetry-sdk` 1.44.0 è corrente. **Nessuna azione.**
5. **ngspice non è il problema del Percorso C.** La 47 è dell'11 agosto 2026 — quattro giorni fa —
   e il progetto è vivo. Il difetto è nel binding, non nel simulatore, ed è per questo che V1 chiede
   di **separarli** nella riga 769 invece di sostituire la riga.
6. **Le tre citazioni normative di AD-16 sono corrette alla lettera**, incluso il MUST sul `content`
   array che avevo messo in dubbio. Ho letto `apps.mdx` sia nella revisione 2026-01-26 sia nella
   `draft`: `mimeType` MUST `text/html;profile=mcp-app`, associazione via `_meta.ui.resourceUri`
   (la forma piatta è deprecata, e lo spine usa già la nuova), e *«Tools MUST return meaningful
   content array even when UI is available»* con livello MUST. **AD-16 non ha errori di citazione.**

---

## 6. Ordine di chiusura, per costo

| # | Rilievo | Che cosa costa | Quando |
|---|---|---|---|
| 1 | **V4 · V6 · V7 · V11** | Quattro righe della tabella `## Stack`. Testo, zero decisioni | Subito |
| 2 | **V10** | Due nomi e due versioni alle righe 774 e 777 | Subito |
| 3 | **V9** | Un vincolo di versione in `pyproject.toml:15` | Subito |
| 4 | **V8** | Una riga nella tabella. Registra una decisione già presa | Subito |
| 5 | **V1** | Riscrivere la riga 769 separando simulatore e binding | **Ora**, anche se il Percorso C è differito: oggi costa una riga, dopo costa un adapter |
| 6 | **V3** | AD-16 recepisce quattro fatti della revisione 2026-07-28; AD-6 guadagna una riga | **Prima di scrivere una riga di `api/assistant`** |
| 7 | **V5** | Riga 767 più il settimo recinto in `check_boundaries.py` | Con la prima storia di Epic 1, che sta già estendendo i recinti da uno a sei |
| 8 | **V2** | Il controllo che lega `## Stack` a `pyproject.toml` | È l'unico che **chiude** il debito invece di saldarlo una volta |

---

## Nota finale

La riga 758 dello spine è oggi ancora vera, e resterà vera anche dopo che questi numeri saranno
stati incollati nella tabella, perché lo spine non ha alcun modo di accorgersi che sono invecchiati.
Il resto del documento ha risolto questo problema ovunque: *«una metrica di §8 che l'harness non
calcola è un difetto dell'harness»* (AD-15); *«una metrica senza stadio emittente è un difetto di
questo documento»* (AD-34); *«un test fallisce sulla dipendenza inversa»* (AD-21, con i recinti
finalmente nominati uno per uno). La sezione `## Stack` è **l'ultima parte dello spine che vive
ancora sulla disciplina**. V2 è il rilievo che le applica lo standard che il documento applica a
tutto il resto.
