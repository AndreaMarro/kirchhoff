# KIRCHHOFF — documento sorgente (input BMAD)

> Documento di lavoro dell'utente, 13 agosto 2026. Project knowledge immutabile.
> Tutti gli artefatti BMAD a valle derivano da qui. Le revisioni vivono negli artefatti,
> non in questo file.

## Decisioni e vincoli non negoziabili (estratto operativo)

Questo blocco è il contratto che ogni artefatto a valle deve rispettare. Il corpo del
documento sotto ne è la motivazione.

### D1 — Specifica MCP
Revisione target **2026-07-28** (non esiste "MCP 2.0"). Core **stateless**: rimossi handshake
`initialize`/`initialized` (SEP-2575) e header `Mcp-Session-Id` (SEP-2567). Autorizzazione su
OAuth 2.0/OIDC. Framework estensioni con id reverse-DNS.
**Roots, Sampling, Logging deprecati** (SEP-2577, finestra ≥12 mesi). Transport HTTP+SSE legacy
deprecato.
→ **Non progettare nulla su Sampling.** Il server tiene le proprie credenziali di provider LLM
e chiama l'API direttamente. Costo modello proprio, controllabile, prevedibile.
→ Lo stateless core permette load balancer banale, scaling orizzontale, nessuna sticky session.

### D2 — MRTR (SEP-2322)
Sostituto delle chiamate server-initiated. Il server restituisce `InputRequiredResult` con
`inputRequests` + `requestState` opaco; il client raccoglie le risposte e **ri-emette la chiamata
originale** con `inputResponses`. Stato nel payload, non in connessione aperta.
**Scelta Kirchhoff: `requestState` = riferimento opaco (ID), non stato inline**, perché l'IR serve
comunque persistito per cronologia, eval e fatturazione.
**Vincolo di sicurezza:** ID **firmato HMAC** e legato all'utente autenticato. Non firmarlo = IDOR
sui circuiti altrui. TTL 15 min, monouso, idempotente sui crediti. **Max 2 round-trip**, poi
degrada a modalità Esperto.

### D3 — MCP Apps (SEP-1865)
Prima estensione ufficiale, finalizzata 26 gen 2026, graduata con la spec 2026-07-28. Risorse UI
con schema `ui://`, associate ai tool via `_meta: { ui: { resourceUri: "ui://..." } }`. Contenuto
**HTML** in **iframe sandboxato**. Comunicazione **JSON-RPC su postMessage**. Negoziazione sotto
`io.modelcontextprotocol/ui`. SDK `@modelcontextprotocol/ext-apps`.
Client: Claude (web+desktop), ChatGPT, VS Code, Goose, Postman, MCPJam, inspector v2.
**Correzione a fonti SEO errate:** MCP Apps usa HTML arbitrario, **non** componenti predefiniti
(DataGrid/ActionForm). Verificare su `modelcontextprotocol.io` e repo `ext-apps`.
**Vincolo di design:** il testo della tool response va al modello; **l'HTML dell'iframe NON viene
processato dal modello**. Quindi ogni UI deve restituire *anche* un riassunto testuale strutturato.
Sandbox: niente cookie, niente localStorage, niente DOM dell'host. Accessibilità a carico nostro.

### D4 — Niente confidence auto-dichiarate dal VLM
Un LLM che scrive `confidence: 0.51` **non riporta una probabilità: genera un token plausibile**.
Non calibrata, sovra-confidente, sensibile al prompt. Soglia "procedi se > 0.95" = diga su un
numero inventato. Fallimento peggiore: **sistema sicurissimo e sbagliato**.
**Sostituzione obbligatoria** — l'ambiguità si *misura*:
- **(a) auto-consistenza multi-pass** — K estrazioni indipendenti (K=3 prod, K=5 eval), variando
  modello, preprocessing immagine, inquadratura del prompt. Canonicalizza all'IR, confronta.
  **Il disaccordo fra i pass È la misura di ambiguità.**
- **(b) verosimiglianza deterministica** — serie E12/E24, unità coerente col tipo, ordine di
  grandezza plausibile (τ = RC), grado nodo ≥ 2, grafo connesso, generatore presente, maglia presente.
- **(c) ridondanza testuale** — i valori spesso compaiono anche nel testo; secondo canale indipendente.
All'utente arriva solo ciò che sopravvive ad (a)+(b)+(c). Obiettivo **QPS ≤ 0,5**; sopra 1,5 il
prodotto muore.

### D5 — L'LLM non è mai nel percorso critico del calcolo
L'LLM fa **tre** cose: (1) estrae struttura dall'immagine; (2) sceglie la **strategia didattica**;
(3) **verbalizza** passaggi già calcolati. Non calcola, non giudica correttezza, non inventa valori.
**Ogni numero mostrato esce da SymPy o dal solver numerico, mai da un token generato.**

### D6 — Verifica a 5 controlli, gate di pubblicazione
1. Residui **KCL** per nodo (Σi = 0, per sostituzione della soluzione).
2. Residui **KVL** per maglia indipendente (albero ricoprente + corde).
3. **Bilancio di potenza** (Σ P_gen = Σ P_diss) — cattura errori di segno che KCL/KVL lasciano passare.
4. **Accordo fra percorsi** A (MNA simbolica) ≈ B (riduzione umana) ≈ C (ngspice, opzionale).
   Tolleranza relativa **1e-9 simbolico / 1e-6 numerico**.
5. **Sanità fisica** — nessun passivo con P<0; tensioni di nodo nell'inviluppo dei generatori in
   rete passiva; τ > 0; regime permanente coerente col transitorio a t→∞.
Tutti passano → badge **"Verificata"** con residui ispezionabili. Uno fallisce → **NON si pubblica**:
si mostra dove si rompe e si chiede.

### D7 — Anteprima sempre visibile
La preview della ricostruzione si mostra **SEMPRE**, anche senza ambiguità. Compatta, 1 click.
Tre ragioni: unico modo di intercettare l'errore silenzioso; è lo *human oversight* per la
compliance; è il momento in cui l'utente si fida, cioè converte.

### D8 — Scope tecnico chiuso
**Dentro:** reti lineari, transitori RL/RC/RLC, regime sinusoidale, trifase. ≈90% di Elettrotecnica.
**Fuori (12 mesi):** modello di visione proprio; simulatore SPICE da zero; app native iOS/Android;
**circuiti non lineari** (diodi, BJT, MOS attivo); chat libera generalista; community/gamification/badge.

### D9 — Esclusione uso valutativo (gate AI Act)
Kirchhoff **non produce voti, punteggi di merito, ranking di studenti, né output destinati a
decisioni valutative o di accesso.** Esclusione (a) nei ToS, (b) **imposta tecnicamente** — nessun
endpoint restituisce un punteggio per persona identificata — (c) documentata nella system card.
Vendi **generazione** e **verifica**, mai **valutazione**.

### D10 — Trasparenza art. 50 dal giorno uno
Art. 50 si applica dal **2 agosto 2026** (non rinviato dal Digital Omnibus). Un sistema nuovo non
beneficia della grazia al 2 dic 2026 (riservata ai sistemi già sul mercato al 2 ago 2026).
- 50(1): disclosure al primo punto di contatto, badge persistente, anche nella MCP App.
- 50(2): marcatura machine-readable (XMP nei PDF, `data-*` negli SVG, header API) + footer visibile.

### D11 — Modello di ricavo
**Crediti per il B2C** (mai abbonamento mensile: stagionalità estrema → rimborsi e disdette).
**Abbonamento per il B2B.** MoR per l'IVA UE al lancio.

### D12 — SER è la metrica bloccante
`SER` (Silent Error Rate) = % soluzioni pubblicate come verificate ma numericamente sbagliate.
Target v1 **< 0,5%**, v2 **< 0,1%**. **Preferisci sempre alzare QPS per abbassare SER, mai il contrario.**
SER > 2% e non scende → **ferma tutto**.

---

## 0. Come leggere questo documento

Tre avvertenze.

**Primo.** Verificati sul web i presupposti tecnici e normativi. Alcuni corretti, uno è un
fraintendimento serio, uno è tecnicamente sbagliato in modo che avrebbe compromesso il prodotto.

**Secondo.** "Come costruisco la web app migliore possibile basata su MCP 2.0" contiene un errore di
framing. MCP non è una categoria di prodotto: è un protocollo di integrazione. Nessun utente pagherà
per "un'app MCP". Pagherà per un problema risolto. MCP risponde a *"come lo distribuisco e lo
integro"*, non a *"cosa vendo"*.

**Terzo.** Le sezioni 5 e 6.4 sono analisi documentata, non parere legale/fiscale.

---

# 1. Verifica dei presupposti

## 1.1 Specifica MCP — vero, con la data giusta
Vedi **D1**. Release candidate bloccata 21 maggio 2026; spec finale 28 luglio 2026.
Cambiamenti: core stateless, routing su header, risultati di list cacheabili, autorizzazione
irrigidita su OAuth 2.0/OIDC, framework formale di estensioni con versionamento indipendente.

## 1.2 MRTR — vero, e più elegante
Vedi **D2**.

## 1.3 MCP Apps — vero, e la parte più interessante
Vedi **D3**. Costruita sul lavoro di MCP-UI e dell'Apps SDK di OpenAI, collaborazione
Anthropic/OpenAI. **L'ecosistema MCP è pieno di contenuto generato male: verificare sempre alla fonte.**
Limiti reali: sandbox senza cookie/localStorage/DOM host; accessibilità responsabilità nostra;
non condivisibile fuori dalla conversazione.

## 1.4 Lo studio sulle "1.723 MCP Apps" — vero il numero, sbagliata l'inferenza
arXiv 2607.25635, *An Empirical Study of Model Context Protocol Applications*. 1.723 "MCPApps" da
GitHub: 85,2% configura i server via file, uso prevalente di SDK ufficiali; nessuna convergenza sullo
*human oversight* (37,2% senza blocco di approvazione).
**"MCPApps" in quel paper = applicazioni CLIENT che consumano server MCP — NON l'estensione MCP Apps
per le UI.** Due cose diverse con lo stesso nome. La conclusione operativa ("blocca prima di eseguire")
resta giusta, ma per ragioni nostre, non perché quel dato lo dimostri. Ripetere la conflazione in un
pitch davanti a chi ha letto il paper costa credibilità.

## 1.5 Le confidence del vision model — tecnicamente sbagliato
Vedi **D4**. Esempio del fallimento: legge 20 Ω invece di 30 Ω con confidence 0.97, non chiede niente,
produce una soluzione formalmente impeccabile del circuito sbagliato. Lo studente la copia, la consegna,
prende un voto basso, non torna mai più, e lo racconta su Reddit.
Costo di K=3: triplica la spesa di visione, restano centesimi. Investimento col ritorno più alto del sistema.

## 1.6 Verdetto sui presupposti

| Affermazione | Stato |
|---|---|
| Non esiste "MCP 2.0", c'è 2026-07-28 | ✅ Vero |
| Core stateless, niente handshake/session id | ✅ Vero |
| MRTR sostituisce elicitation/sampling | ✅ Vero (SEP-2322) |
| MCP Apps è estensione ufficiale, HTML in iframe | ✅ Vero (SEP-1865) |
| Claude e ChatGPT renderizzano MCP Apps | ✅ Vero |
| Sampling deprecato → server con proprie credenziali | ⚠️ Non nel doc di partenza, ma è così |
| Studio 1.723 MCP Apps → ecosistema UI ha poco oversight | ❌ Conflazione: studia client, non UI |
| Confidence numerica dal vision model come soglia | ❌ Tecnicamente insostenibile |
| MCP non migliora l'accuratezza del riconoscimento | ✅ Vero |

---

# 2. Tesi strategica

## 2.1 Perché "foto → soluzione" non è difendibile
**Vita utile stimata del prodotto preso alla lettera: 12–24 mesi.**
1. I modelli frontier stanno divorando il caso d'uso; la curva è contro di noi.
2. Il concorrente più pericoloso costa zero: il piano gratuito di ChatGPT/Gemini sul telefono dello studente.
3. Categoria satura e commoditizzata: Photomath, Symbolab, Gauth, Question.AI, Chegg.
4. Il segmento paga male: ARPU basso, churn brutale, stagionalità estrema (picchi gen-feb e giu-lug;
   deserto ad agosto e novembre).

## 2.2 Cosa è difendibile
**(1) Garanzia di correttezza verificabile.** Un chatbot non può dire *"questa soluzione ha superato
cinque controlli indipendenti"* perché non ha un solver deterministico sotto. Nessun generalista può
copiarla senza costruire lo stesso backend. È l'unica promessa che giustifica un pagamento: lo studente
non compra "una risposta", compra **il diritto di fidarsi della risposta** la notte prima dell'esame.
**(2) Corpus verificato e specificità curricolare.** Non "circuiti in generale": *l'esame di
Elettrotecnica del corso X dell'ateneo Y, con le convenzioni di segno di quel professore, le notazioni
di quelle dispense, i metodi che quel corso pretende* (Millman qui, Thévenin lì, sovrapposizione mai).
Il corpus LaTeX esistente non è replicabile scrapando il web.
**(3) La sequenza didattica, non il numero.** Un solver produce `V₈ = 1,5 V`. Lo studente ha bisogno di
`R₃∥R₄ → serie con R₂ → ramo equivalente → R₆∥ramo destro → Millman → V_AB → LKT → I₁ → partitore → V₈`,
col disegno del circuito ridotto a ogni passo. **Il numero è commodity. La sequenza con i disegni è il prodotto.**

## 2.3 Un motore, due prodotti

```
                    KIRCHHOFF ENGINE
        (IR circuitale + solver + verifica + renderer)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     KIRCHHOFF SOLVE                KIRCHHOFF STUDIO
        (B2C)                          (B2B)
     studente, foto,               tutor / docente / centro
     soluzione verificata          genera N varianti d'esame
     a crediti                     con soluzioni garantite
              │                           │
     ARPU 5–25 €/anno              ARPU 400–3.000 €/anno
     churn alto, stagionale        churn basso, annuale
     acquisizione: SEO+passaparola acquisizione: outbound diretto
              │                           │
              └──────────┬────────────────┘
                         ▼
              Le varianti generate da STUDIO
              diventano il corpus SEO che
              alimenta l'acquisizione di SOLVE
```

**Il cliente B2B sei tu.** Produci a mano esercizi ed esami in LaTeX con verifica SymPy — reti DC,
Thévenin/Millman, trifase, sinusoidale, e altri domini (automatica, elettronica digitale, analisi
numerica, algebra lineare). È esattamente il lavoro che Studio automatizza. Se non è utile a te per
primo, non è utile a nessuno; se lo è, hai un cliente pilota con feedback loop di un'ora.

**Le economie B2B sono un altro sport.** Un centro a 79 €/mese vale ~30 studenti B2C paganti, con un
decimo del churn e un centesimo del costo di supporto.

## 2.4 Chi paga davvero

| Segmento | Disponibilità a pagare | Volume IT | Churn | Verdetto |
|---|---|---|---|---|
| Studente in panico, 48h dall'esame | Alta ma **puntuale** | Alto, stagionale | Estremo | **Crediti, mai abbonamento** |
| Studente diligente, tutto il semestre | Media | Basso | Medio | Pass sessione |
| Tutor privato | **Alta e ricorrente** | poche migliaia IT | Basso | **Target primario B2B** |
| Centro di ripetizioni / doposcuola | Alta | Centinaia | Molto basso | **Target primario B2B** |
| Docente universitario | Media, budget lento | Migliaia | Bassissimo | Ciclo lungo, alto valore |
| Dipartimento / ateneo | Alta, ma appalto | Decine | Nullo | ⚠️ Fa scattare Annex III (§5.3) |

## 2.5 Il test da fare *prima* di scrivere una riga di prodotto

**Settimana 1–2. Costruisci un benchmark, non un prodotto.**
1. **200 foto reali** da studenti — non scansioni pulite: foto storte, ombre, manoscritte, con la mano
   nell'inquadratura.
2. Per ognuna, **IR gold** a mano: netlist, valori, topologia, grandezze richieste, risultato corretto.
3. **Baseline frontier**: tre modelli SOTA, prompt semplice, % risposte numericamente corrette.

**Poi leggi il numero.**
- **> 80%**: il prodotto non può essere "risolvo meglio". Deve essere "risolvo *e certifico*, nel
  formalismo del tuo corso". **Ridimensiona drasticamente l'investimento in visione.**
- **50–80%**: spazio reale. Multi-pass + validazione elettrica → 90%+; quel delta è vendibile.
- **< 50%**: problema più duro del previsto, alto rischio "sicurissimo e sbagliato". Parti con
  **input strutturato assistito** e la foto come acceleratore, non come contratto.

Costo del test: due settimane e qualche decina di euro di API. Costo di non farlo: sei mesi su
un'architettura già commoditizzata.

---

# 3. Il prodotto

## 3.1 La promessa

> **Kirchhoff non ti dà una risposta. Ti dà una risposta che ha superato cinque verifiche indipendenti
> — e quando non le supera, te lo dice.**

Sottotitolo: *Il circuito dalla foto, il procedimento come lo scriveresti tu, la certezza che il numero
è giusto.* L'onestà come feature è una posizione competitiva vera, non una postura morale.

## 3.2 Loop principale (B2C)

```
FOTO
 ↓
[≈3 s]  Estrazione multi-pass  →  K ricostruzioni IR
 ↓
[<1 s]  Consenso + validazione elettrica deterministica
 ↓
        ┌─── nessuna ambiguità residua ──────────────┐
        │                                             │
        ▼                                             ▼
  ANTEPRIMA CONFERMA                        DOMANDA MIRATA (MRTR)
  overlay sulla foto, 1 click              "R8: 20 Ω o 30 Ω?"  [foto zoomata]
  "Confermo" / "Correggi"                   0–2 domande, mai di più
        │                                             │
        └──────────────────┬──────────────────────────┘
                           ▼
[<1 s]  Risoluzione a doppio percorso (simbolica + numerica)
 ↓
[<1 s]  VERIFICA INDIPENDENTE — 5 controlli
 ↓
        ┌──── passa ────┐          ┌──── non passa ────┐
        ▼                          ▼
  Pianificatore didattico    "Non riesco a certificare
  → passaggi + disegni        questa soluzione. Ecco dove
  → LaTeX / PDF / SVG         si rompe: nodo C."
```

Vedi **D7**. **Budget di latenza totale: < 45 s** dal caricamento alla prima soluzione verificata,
incluse le domande. Sopra i 60 s lo studente in panico apre ChatGPT.

## 3.3 Le tre modalità

| Modalità | Chi | Comportamento |
|---|---|---|
| **Rapida** | Default B2C | Anteprima compatta + 1 click. Domande solo su ambiguità sopravvissute. |
| **Studio** | Default educativo | Rivelazione progressiva dei passaggi, con domanda di verifica prima di scoprire lo step successivo. **Rende il prodotto difendibile davanti a un docente.** |
| **Esperto** | Tutor, docenti | Editor completo del grafo, override di ogni valore, strategia risolutiva forzata ("voglio Thévenin, non Millman"), export IR/netlist/LaTeX. |

*Studio* non è una concessione morale: è lo scudo contro il divieto istituzionale (§5.11) e l'argomento
di vendita B2B.

## 3.4 Kirchhoff Studio (B2B)

- **Generatore di varianti.** Dato un esercizio (foto, LaTeX, editor), produce N varianti parametriche
  con valori diversi, tutte con soluzione completa verificata e disegni. Automatizza il workflow
  SymPy → LaTeX → pdflatex ×2 → ispezione visiva, con verifica integrata invece che a posteriori.
- **Export nativi:** LaTeX (CircuiTikZ), PDF, DOCX, Moodle XML / GIFT, QTI.
- **Banco esercizi privato** del tenant, tag per corso/ateneo/argomento/difficoltà.
- **Fogli soluzione separati** con checksum di verifica per ogni variante.
- **Vincoli d'ambiente noti:** niente `lmodern`, niente babel italiano, label CircuiTikZ con `=`
  racchiusi in graffe. Se il generatore non produce LaTeX che compila al primo colpo, non è pronto.

Un tutor che risparmia 4 h/settimana paga 39–79 €/mese senza discutere.

## 3.5 Cosa NON costruire
Vedi **D8**. Motivazioni:
- Modello di visione proprio → mesi, dataset annotati, superato da un aggiornamento di API non controllato.
- SPICE da zero → esiste ngspice, esiste lcapy.
- App native → PWA con fotocamera; store = 30% commissione, review cycle, zero acquisizione aggiuntiva.
- Non lineari → i solver simbolici li gestiscono male; fuori dal 90% di Elettrotecnica.
- Chat libera → diventi un chatbot peggiore dei gratuiti e perdi la promessa di verificabilità.
- Community/gamification → zero evidenza di impatto sulla conversione in questo segmento.

---

# 4. Architettura tecnica

## 4.1 Vista d'insieme

```
                       ┌──────────────────────────────┐
                       │      SUPERFICI CLIENT        │
                       ├──────────────────────────────┤
                       │  web app  │ Claude │ ChatGPT │
                       │  (PWA)    │MCP App │ MCP App │
                       └─────┬──────────┬───────┬─────┘
                             │          │       │
                        HTTP │          │  MCP 2026-07-28
                             │          │  (stateless, MRTR)
                             ▼          ▼       ▼
                    ┌────────────────────────────────┐
                    │        API GATEWAY             │
                    │  auth · quota · rate · audit   │
                    └───────────────┬────────────────┘
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │              ORCHESTRATORE (deterministico)        │
        │  macchina a stati, NON un agente LLM libero        │
        └───┬──────┬──────┬──────┬──────┬──────┬──────┬─────┘
            ▼      ▼      ▼      ▼      ▼      ▼      ▼
        ┌──────┐┌─────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
        │VISION││ IR  ││VALID ││SOLVER││VERIFY││PLAN  ││RENDER│
        │multi ││norm ││elettr││simb+ ││5 con-││didat-││TikZ/ │
        │-pass ││alizz││ico   ││numer ││trolli││tico  ││SVG   │
        └──┬───┘└──┬──┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘
           │       │      │       │       │       │       │
           └───────┴──────┴───────┴───────┴───────┴───────┘
                                │
                  ┌─────────────┴──────────────┐
                  ▼                            ▼
          Postgres (IR, audit,          Object storage EU
          eval, fatturazione)           (immagini, TTL breve)
```

Vedi **D5**. Il principio separa ciò che può sbagliare in modo *rilevabile* (l'estrazione) da ciò che
sbaglierebbe in modo *invisibile* (l'aritmetica di un LLM).

## 4.2 Circuit IR — lo schema

```json
{
  "ir_version": "1.0",
  "source": {
    "kind": "image",
    "asset_id": "img_01J…",
    "extraction": {
      "passes": 3,
      "agreement": 0.94,
      "models": ["vlm-a", "vlm-b", "vlm-a-preprocessed"]
    }
  },
  "domain": "dc_resistive | ac_phasor | transient | three_phase",
  "units": "SI",
  "nodes": [
    { "id": "0",  "label": "GND", "is_reference": true },
    { "id": "A",  "label": "A" },
    { "id": "B",  "label": "B" },
    { "id": "C",  "label": "C" }
  ],
  "components": [
    {
      "id": "R1", "type": "resistor",
      "terminals": ["A", "B"],
      "value": { "magnitude": 10, "unit": "ohm", "symbolic": "R_1" },
      "provenance": { "bbox": [212, 88, 268, 130], "agreement": 1.0 }
    },
    {
      "id": "R8", "type": "resistor",
      "terminals": ["C", "0"],
      "value": { "magnitude": 30, "unit": "ohm", "symbolic": "R_8" },
      "provenance": { "bbox": [640, 402, 700, 448], "agreement": 0.67 },
      "alternatives": [{ "magnitude": 20, "unit": "ohm", "support": 1 }],
      "resolution": { "by": "user", "at": "2026-08-13T12:04:11Z" }
    },
    {
      "id": "E1", "type": "voltage_source_dc",
      "terminals": ["A", "0"],
      "polarity": { "plus": "A", "minus": "0" },
      "value": { "magnitude": 15, "unit": "volt", "symbolic": "E_1" }
    },
    {
      "id": "S1", "type": "switch",
      "terminals": ["B", "C"],
      "schedule": [
        { "t": 0,      "state": "closed" },
        { "t": 5e-6,   "state": "open"   }
      ]
    }
  ],
  "requests": [
    { "id": "q1", "quantity": "voltage", "across": "R8", "at": "steady_state" },
    { "id": "q2", "quantity": "current", "through": "R1", "at": "0+" }
  ],
  "conventions": {
    "current_direction": "passive_sign",
    "curriculum_profile": "unibo_elettrotecnica_2026"
  },
  "open_questions": []
}
```

**Note di progetto:**
- **`symbolic` accanto a `magnitude` non è un vezzo.** Permette (a) di verificare la struttura
  indipendentemente dai valori, (b) di generare varianti parametriche per Studio riusando *la stessa*
  soluzione simbolica, (c) di mostrare formule letterali nei passaggi, come si fa a mano.
- **`provenance.bbox` obbligatorio** su ogni componente. Senza bbox niente overlay; senza overlay né
  UX né oversight.
- **`schedule` sugli interruttori** gestisce nativamente 0⁻/0⁺/∞ con seconda commutazione a 5 μs —
  la classe di esercizi dove le foto ambigue fanno più danno.
- **`curriculum_profile`** è il gancio della difendibilità: convenzioni di segno, metodi ammessi,
  notazione, formato d'uscita, per corso e ateneo.

## 4.3 Stadio 1 — Ingestione
Deterministico, veloce, zero AI: correzione prospettica (quadrilatero + warp); deskew; CLAHE;
upscale ×2 delle regioni ad alta densità di testo (etichette dei valori); rilevamento pagine/esercizi
multipli → **chiedi quale**, non indovinare.
Produci **tre versioni** (originale, migliorata, crop testuale) e usale nei tre pass: il preprocessing
diversificato è la fonte di indipendenza più economica disponibile.

## 4.4 Stadio 2 — Estrazione multi-pass
Come da **D4**. In più:
- **Due fasi separate:** prima *inventario dei componenti* (tipo, valore, bbox), poi *topologia*
  (quali terminali su quale nodo) con l'inventario già fissato. Chiederle insieme aumenta gli errori
  su entrambe.
- **Vietare al modello di inventare:** valore non leggibile → `null` + `alternatives[]`, mai un valore
  plausibile. Testato esplicitamente nell'eval con immagini a valore cancellato.
- **Output vincolato a schema JSON** con validazione rigida e retry su fallimento di parsing.

## 4.5 Stadio 3 — Validazione elettrica deterministica
Gate obbligatorio prima del solver, puro codice:

| Controllo | Fallimento tipico |
|---|---|
| Grafo connesso | ramo staccato per un incrocio letto male |
| Esiste nodo di riferimento | manca la massa |
| Ogni nodo ha grado ≥ 2 | terminale penzolante |
| Nessun loop di soli generatori di tensione | polarità o giunzione letta male |
| Nessun taglio di soli generatori di corrente | idem |
| Valori > 0 per elementi passivi | segno perso |
| Unità coerenti col tipo | confusione μ/m |
| Valori in serie E12/E24 | cifra letta male |
| Le grandezze richieste esistono nel grafo | target su componente non trovato |

**Un fallimento qui non è un errore del sistema: è un'informazione.** Un loop di generatori di tensione
dice *esattamente* quale giunzione è stata letta male, e permette la domanda giusta. Differenza fra
"non ho capito il circuito" e "il nodo C ha un problema: questi due fili si toccano davvero?".

## 4.6 Stadio 4 — Risoluzione a doppio percorso
**Percorso A — MNA simbolica.** Matrice MNA da IR, SymPy, sostituzione valori. Robusta, generale, non didattica.
**Percorso B — Riduzione umana.** Sequenza di trasformazioni scelta dal pianificatore; ogni trasformazione
è una funzione pura su IR che produce un nuovo IR **più un artefatto di disegno**. La grandezza richiesta
si ottiene percorrendo la catena.
**Requisito:** A ≈ B entro 1e-9 (simbolico) / 1e-6 (numerico). Se non concordano il bug è nel Percorso B —
la libreria di trasformazioni — e il sistema **non pubblica**: ripiega su A e segnala internamente.
**Ogni utilizzo in produzione diventa un test di regressione sulla parte più fragile del codice.**
**Percorso C (opzionale): ngspice.** Esporta a netlist SPICE, `.op`/`.tran`/`.ac`, confronta. Un terzo
motore scritto da altri che concorda è l'argomento di vendita più forte verso un docente.

## 4.7 Stadio 5 — Verifica indipendente
Vedi **D6**. Valore commerciale: permette una frase che nessun concorrente può dire —
**"Se Kirchhoff mostra una soluzione, quella soluzione soddisfa le leggi di Kirchhoff. Verificato dal
sistema, non promesso dal modello."** Ed è, non per caso, la documentazione di *human oversight* e
*accuratezza* che servirebbe se un giorno si finisse nell'ambito ad alto rischio (§5.3).

## 4.8 Stadio 6 — Pianificatore didattico
Unico punto dove l'LLM fa qualcosa di veramente cognitivo, comunque sotto vincolo.
Input: IR validato + `curriculum_profile` + grandezze richieste.
Output: **sequenza ordinata di trasformazioni ammesse**, da catalogo chiuso.

```
Catalogo trasformazioni (v1)
├── serie_resistori          ├── thevenin_bipolo
├── parallelo_resistori      ├── norton_bipolo
├── partitore_tensione       ├── millman_nodo
├── partitore_corrente       ├── sovrapposizione_effetti
├── stella_triangolo         ├── kcl_nodale
├── triangolo_stella         ├── kvl_maglie
├── impedenza_fasoriale      ├── condizioni_iniziali_0-/0+
└── regime_permanente_∞      └── costante_tempo_τ
```

L'LLM propone; **il sistema esegue deterministicamente e verifica che porti al risultato**. Se la
sequenza non converge o non è applicabile, ripiega su piano canonico (nodale) invece di lasciare
improvvisare l'LLM.
Il `curriculum_profile` restringe il catalogo: se il corso non ha ancora fatto Thévenin, quella
trasformazione non è disponibile. **Feature che vale soldi presso i tutor**, impossibile per un
chatbot generalista.

## 4.9 Stadio 7 — Rendering
Per ogni passo: un circuito ridotto disegnato, non solo una formula.
- **SVG** per il web (generazione diretta da IR con layout ortogonale; `schemdraw` come base o
  generatore proprio).
- **CircuiTikZ → LaTeX → PDF** per export e Studio: `.tex` → `pdflatex` ×2 `nonstopmode` → `pdftoppm`
  per ispezione visiva automatica → iterazione. L'ispezione automatizzata (overflow, sovrapposizioni,
  box vuoti) va in CI, non fatta a occhio.
- **Watermark di provenienza** su ogni export (**D10**): visibile + machine-readable.

## 4.10 Stack concreto

| Livello | Scelta | Perché |
|---|---|---|
| Solver simbolico | **SymPy + lcapy** | lcapy fa MNA simbolica, Laplace, transitori, fasori su reti lineari. Non copre non lineare → coerente con D8. |
| Solver numerico | **ngspice** via PySpice | Terzo motore indipendente. |
| Grafo | **NetworkX** | Connettività, alberi ricoprenti, maglie indipendenti. |
| Backend | **FastAPI + Pydantic** | Validazione IR nativa. |
| Server MCP | **SDK Python ufficiale, target 2026-07-28** | MRTR + estensione Apps. |
| DB | **Postgres (Supabase, region EU)** | auth, RLS, storage. Verificare region EU esplicita. |
| Storage immagini | **Object storage EU, TTL 24–72h** | Minimizzazione (§5.7). |
| Frontend | **React 19 + Vite 7 + Tailwind 4, PWA** | Stack già padroneggiato. |
| Pagamenti | **Merchant of Record** (§6.4) | Risolve l'IVA UE. |
| Coda / job | **Redis + RQ**, o n8n per orchestrazioni non critiche | Istanza n8n già presente. |
| Osservabilità | **OpenTelemetry + backend qualsiasi** | Serve per l'audit trail. |
| Hosting | **VPS EU** + object storage EU | Semplice, economico, sovranità dati chiara. |

## 4.11 Il server MCP

**Tool esposti** (superficie minima, non massima — ogni tool in più è superficie di attacco e
confusione per il modello):

```
kirchhoff.analyze_circuit(image_ref | latex | netlist)
    → { circuit_id, ir_summary, open_questions[], preview_svg }
    → oppure InputRequiredResult se ci sono ambiguità

kirchhoff.confirm_circuit(circuit_id, corrections[])
    → { circuit_id, status: "validated" }

kirchhoff.solve(circuit_id, requests[], profile?)
    → { solution, verification: {kcl, kvl, power, agreement, sanity}, steps[] }

kirchhoff.explain(circuit_id, step_index, depth)
    → { narrative, formula_latex, figure_svg }

kirchhoff.export(circuit_id, format: "pdf"|"tex"|"svg"|"gift")
    → { url, expires_at, provenance_mark }

kirchhoff.generate_variants(circuit_id, n, constraints)   # Studio
    → { variants[], solutions[], verification[] }
```

**Flusso MRTR concreto:**

```
1. Client → analyze_circuit(image_ref)
2. Server → InputRequiredResult {
       inputRequests: [
         { id: "r8_value", prompt: "Valore di R8?",
           schema: { enum: ["20 Ω", "30 Ω", "altro"] },
           _meta: { ui: { resourceUri: "ui://kirchhoff/verify" } } }
       ],
       requestState: "<id firmato HMAC, TTL 15 min>"
   }
3. Host mostra la MCP App: foto + overlay + zoom su R8 + radio button
4. Utente sceglie
5. Client → analyze_circuit(image_ref, inputResponses: [...], requestState)
6. Server riprende, valida, restituisce IR + preview
```

Regole MRTR: vedi **D2**.

**La MCP App (UI):** HTML statico in sandbox iframe come risorsa `ui://kirchhoff/verify`; JSON-RPC su
postMessage; **deve restituire anche un riassunto testuale strutturato nella tool response** (**D3**);
niente cookie né localStorage — lo stato vive in `requestState`; accessibilità a carico nostro (ARIA,
tastiera, contrasto), non opzionale per clienti istituzionali.

**Avvertimento strategico sul canale MCP.** Distribuire dentro Claude e ChatGPT è un canale di
acquisizione reale e nuovo. Ma: non possiedi la relazione col cliente; la monetizzazione dentro gli
host non è un problema risolto; la scoperta nelle directory non è garantita; le policy possono cambiare
unilateralmente. **La web app resta il sistema di record.** MCP è un canale, non la casa. Progetta
l'autenticazione perché l'utente che arriva da Claude possa collegare un account Kirchhoff — altrimenti
il canale porta uso e non porta clienti.

## 4.12 Costi e latenza per soluzione

| Voce | Costo | Latenza |
|---|---|---|
| Preprocessing immagine | ~0 | 0,3 s |
| Estrazione ×3 (frontier) | 0,02–0,08 € | 4–9 s (parallelo: 3–4 s) |
| Consenso + validazione | ~0 | 0,05 s |
| Solver simbolico + numerico | ~0 (CPU) | 0,2–2 s |
| Verifica 5 controlli | ~0 | 0,05 s |
| Pianificatore (LLM, chiamata piccola) | 0,003–0,01 € | 1–2 s |
| Narrazione passi (LLM) | 0,005–0,02 € | 2–4 s |
| Rendering SVG | ~0 | 0,3 s |
| **Totale** | **0,03–0,11 €** | **8–15 s** |

**Ottimizzazione a scaglioni:** primo pass con modello economico; escalation a frontier solo se consenso
basso o validazione fallita. Costo medio → **0,01–0,04 €** con impatto trascurabile sui casi facili,
che sono la maggioranza.
Con prezzo effettivo **0,30–0,50 €/soluzione**, margine lordo **> 88%**. **Il problema non sarà mai il
COGS. Sarà il CAC.** Non ottimizzare i costi del modello prima di aver risolto l'acquisizione.

## 4.13 Benchmark ed eval harness

**Gold set:** 200 immagini reali stratificate — pulite stampate 40%, manoscritte leggibili 35%,
manoscritte difficili 15%, degradate/storte 10%. Per ognuna: IR gold, risultato numerico gold, sequenza
didattica di riferimento. Split **120 dev / 80 held-out**. **L'held-out non si guarda mai** durante lo sviluppo.

| Metrica | Definizione | Target v1 | Target v2 |
|---|---|---|---|
| **VSR** — Verified Solve Rate | % soluzioni verificate e corrette senza correzione umana | 65% | 88% |
| **SER** — Silent Error Rate | % soluzioni pubblicate come verificate ma numericamente sbagliate | **< 0,5%** | **< 0,1%** |
| **QPS** — Questions Per Solve | domande medie all'utente | ≤ 1,5 | ≤ 0,5 |
| **TTV** — Time To Verified | secondi al primo risultato verificato | < 45 s | < 25 s |

Vedi **D12**. Eval **su ogni commit** che tocchi estrazione, validazione, trasformazioni o pianificatore.

---

# 5. Compliance by design

## 5.1 Il quadro applicabile (al 13 agosto 2026)
1. **AI Act — Reg. (UE) 2024/1689**, modificato dal **Digital Omnibus on AI — Reg. (UE) 2026/1744**
   (GU 24 lug 2026, in vigore 27 lug 2026).
2. **GDPR — Reg. (UE) 2016/679** + Codice Privacy italiano (d.lgs. 196/2003 mod. d.lgs. 101/2018).
3. **Legge 132/2025** — legge italiana sull'IA, in vigore dal 10 ottobre 2025.
4. Diritto d'autore (§5.10).

Il Digital Omnibus ha **rinviato** gli obblighi Allegato III **dal 2 ago 2026 al 2 dic 2027** (Allegato I
al 2 ago 2028). **Non ha toccato l'art. 50 (trasparenza), applicabile dal 2 agosto 2026**, né l'**art. 4
(alfabetizzazione IA)**, in vigore da febbraio 2025. Linee guida Commissione su art. 50 adottate il
20 luglio 2026; Code of Practice sulla trasparenza dei contenuti IA confermato adeguato. Sanzioni art. 50
fino a 15 M€ o 3% del fatturato mondiale (PMI/startup: l'importo inferiore).

## 5.2 Classificazione
**Sei un *provider* (fornitore).** Immetti sul mercato un sistema di IA a tuo nome. Anche *deployer* dei
modelli GPAI a monte, ma conta il primo.
**Rischio: limitato, non alto** — a condizione che il prodotto resti quello descritto qui.
L'Allegato III punto 3 elenca quattro funzioni ad alto rischio in ambito educativo: (a) determinare
accesso/ammissione o assegnare persone a istituti; (b) **valutare i risultati dell'apprendimento**,
incluso quando usati per orientare il processo, **all'interno di istituti**; (c) valutare il livello di
istruzione appropriato; (d) monitorare comportamenti vietati durante i test.
Kirchhoff Solve **non fa nessuna delle quattro**. La linea è sottile e va difesa attivamente: i sistemi
di tutoring con suggerimenti non vincolanti sono *al margine dell'ambito*; la classificazione dipende da
se l'output alimenti una decisione che incide sull'accesso.

## 5.3 La trappola dell'Allegato III
Vedi **D9**. Feature che fanno scattare la trappola — tutte apparentemente innocue, tutte richieste dai
clienti B2B:
- ❌ "Correggi automaticamente i compiti dei miei studenti e dammi il voto"
- ❌ "Dammi una dashboard che mostra chi è indietro e su cosa"
- ❌ "Genera l'esame E correggilo"
- ❌ "Segnala gli studenti a rischio bocciatura"
- ❌ Qualunque profilazione di persone fisiche per valutarne il rendimento — **sempre ad alto rischio**,
  senza eccezione art. 6(3)

Cosa comporta finirci dentro: sistema di gestione dei rischi, governance dei dati, documentazione tecnica,
log automatici, trasparenza verso il deployer, sorveglianza umana progettata, accuratezza/robustezza/
cybersicurezza, valutazione di conformità, registrazione nella banca dati UE, sistema qualità,
monitoraggio post-mercato. **Per un solo-founder: progetto a sé, mesi, costi legali a cinque cifre.**
Il rinvio al 2 dic 2027 dà tempo *se un giorno si decide di entrare*. Non è un motivo per entrarci per
distrazione.

## 5.4 Articolo 50 — implementazione
Vedi **D10**.
- **50(1)** — disclosure al primo punto di contatto, non nei ToS; avviso persistente sufficiente;
  linguaggio chiaro. Badge fisso: `Kirchhoff usa intelligenza artificiale per leggere il circuito.
  I calcoli sono verificati automaticamente.` Presente anche nella MCP App e nel primo messaggio di sessione.
- **50(2)** — machine-readable: XMP nei PDF (`ai_generated=true`, versione sistema, timestamp, hash IR);
  `data-*` negli SVG; header nelle risposte API. Percepibile: footer su ogni export —
  `Soluzione generata con assistenza IA e verificata automaticamente — kirchhoff.app — <hash>`.
- **Aderire al Code of Practice** sulla trasparenza dei contenuti IA: non obbligatorio, ma il modo più
  economico di dimostrare conformità.
- **Non ci riguardano:** 50(3) riconoscimento emozioni/categorizzazione biometrica; 50(4) deepfake e
  testo su temi di interesse pubblico.

## 5.5 Articolo 4 — alfabetizzazione IA
In vigore, non rinviato. Adempimento proporzionato e leggero **ma documentato**: una pagina interna —
cosa fa il sistema, dove sbaglia, cosa non promettere mai agli utenti, chi contattare per un incidente.
Collaboratori e tutor che usano Studio la leggono e firmano. Costo: un'ora. Valore in due diligence B2B: alto.

## 5.6 Legge 132/2025 e minori
Art. 4 L.132/2025 va oltre il GDPR:
> **L'accesso alle tecnologie di IA da parte dei minori di quattordici anni** — non solo il trattamento
> dei dati, **l'accesso** — **richiede il consenso di chi esercita la responsabilità genitoriale.**
> Il minore che ha compiuto quattordici anni può esprimere il proprio consenso per il trattamento dei
> dati connessi all'uso di sistemi di IA, **purché le informazioni siano facilmente accessibili e
> comprensibili**.

Coerente con art. 2-quinquies Codice Privacy: **14 anni** (non 16) l'età del consenso digitale in Italia.

| Se il target è… | Cosa devi fare |
|---|---|
| Solo universitari (18+) | Età minima 18 nei ToS, gate all'iscrizione. **Opzione più semplice.** |
| Anche superiori 14–17 | Consenso del minore ammesso, ma **informativa in linguaggio semplificato obbligatoria**. Niente profilazione a fini di marketing. |
| Anche sotto i 14 | Consenso genitoriale verificabile per l'accesso stesso. **Sconsigliato.** |

**Raccomandazione: 14+, con informativa semplificata.** Elettrotecnica è materia universitaria e degli
ultimi anni di ITIS; sotto i 14 non c'è mercato, solo rischio.
L'autodichiarazione dell'età è l'unico strumento realistico ed è il punto debole riconosciuto della norma.
Va accompagnata da dichiarazione esplicita al signup, ToS che vietano l'uso sotto soglia, e procedura di
rimozione rapida documentata.

## 5.7 GDPR — mappa dei trattamenti

| # | Trattamento | Dati | Base giuridica | Conservazione |
|---|---|---|---|---|
| T1 | Account | email, password hash, età dichiarata | contratto (art. 6.1.b) | durata account + 30 gg |
| T2 | Upload immagini | **immagine dell'esercizio: può contenere nome, matricola, grafia, nome del docente** | contratto | **24–72 h, poi cancellazione** |
| T3 | IR + soluzioni | dati tecnici, non personali una volta derivati | contratto | durata account |
| T4 | Pagamenti | dati fatturazione | obbligo legale (art. 6.1.c) | 10 anni |
| T5 | Telemetria di prodotto | eventi pseudonimizzati | legittimo interesse (art. 6.1.f) + LIA | 14 mesi |
| T6 | Miglioramento modello | immagini + IR | **consenso esplicito, opt-in** (art. 6.1.a) | fino a revoca |
| T7 | Marketing | email | consenso | fino a revoca |
| T8 | Sicurezza / audit | log, IP | legittimo interesse | 6–12 mesi |

**T2 è il trattamento sensibile.** Mitigazioni: estrai l'IR poi **cancella l'immagine** entro 24–72 h;
**blur automatico** delle regioni testuali non circuitali prima dell'invio al provider; avviso all'upload
(*"Non caricare fogli con il tuo nome o la tua matricola. Se ci sono, offuscali."*) — minimizzazione, UX
e gratis.
**T6 è la linea che ci distingue dai grandi.** Nessun training su upload per default. Opt-in esplicito,
detto in chiaro, usato come argomento di vendita: *"I tuoi circuiti non addestrano nessun modello, a meno
che tu non ce lo chieda."* Posizione che i concorrenti americani non possono assumere altrettanto
credibilmente.

## 5.8 Sub-responsabili e trasferimenti
I provider di modelli sono **sub-responsabili** che ricevono le immagini degli utenti.
1. **DPA** con ogni provider di modello.
2. **Zero data retention** dove disponibile — essenziale, non opzionale.
3. **Residenza dati UE** dove esiste.
4. Verifica lo **strumento di trasferimento** vigente (adeguatezza / DPF / SCC) **alla data del lancio**:
   lo scenario cambia, non fidarsi di una nota scritta oggi.
5. **Elenco pubblico dei sub-responsabili** + notifica preventiva delle modifiche. Richiesto
   contrattualmente dai clienti B2B e segnale di serietà.
6. **Registro dei trattamenti** (art. 30) — obbligatorio in pratica.

## 5.9 DPIA
**Falla comunque, versione proporzionata (8–12 pagine).** Tre ragioni: (1) aprendo ai 14–17enni gli
indici del Garante la rendono difficilmente evitabile; (2) ogni cliente B2B istituzionale la chiederà;
(3) produce l'analisi dei rischi che serve comunque per la system card AI Act.

## 5.10 Diritto d'autore sui testi d'esame — il rischio sottovalutato
Un tema d'esame universitario è un'opera dell'ingegno; il titolare è il docente o l'ateneo. Costruire una
libreria pubblica e indicizzabile di temi d'esame altrui risolti — la mossa SEO più ovvia e tentante — è
riprodurre e diffondere opere protette a fini commerciali. Non è una zona grigia particolarmente ampia.

| Fai | Non fare |
|---|---|
| Pubblica **varianti generate da te** (Studio) come corpus SEO | ❌ Pubblicare testi d'esame originali altrui |
| Conserva l'**IR derivato** dell'upload, non l'immagine | ❌ Archivio pubblico di compiti caricati |
| Risolvi in privato qualunque cosa carichi l'utente | ❌ Rendere pubblici gli upload senza licenza |
| Se vuoi materiale reale pubblico, **chiedi licenza** al docente | ❌ Assumere che "è per studiare" copra tutto |

**Il vincolo rafforza il piano:** il corpus SEO deve essere *tuo*, e Kirchhoff Studio esiste per generarlo.
Rischio legale e strategia di prodotto puntano nella stessa direzione.

## 5.11 Integrità accademica: da rischio a posizionamento
**Stai costruendo uno strumento che si può usare per copiare.** Fingere il contrario espone al primo
docente che scrive un post arrabbiato, e i docenti hanno più megafono degli studenti.
1. **Modalità Studio come default educativo.**
2. **Politica di uso accademico pubblica**, scritta, linkata dall'header: cosa il prodotto fa, cosa non fa,
   cosa consideriamo uso improprio, cosa offriamo ai docenti.
3. **Marcatura di provenienza su ogni export** (già dovuta ex art. 50(2)): un PDF Kirchhoff è riconoscibile
   a colpo d'occhio. **Rendi facile essere onesti e visibile essere disonesti.**
4. **Programma docenti gratuito** con email istituzionale verificata. Costo marginale ~zero; converte il
   critico più pericoloso nel canale di distribuzione più efficace.
5. **Nessuna "modalità solo risposta" per i tenant istituzionali.**

Messaggio ai docenti: *"Ai vostri studenti servono esercizi svolti. Li stanno già prendendo da un chatbot
che sbaglia e non lo sa. Kirchhoff mostra il procedimento, verifica il risultato e firma l'output. E a voi
genera le varianti d'esame."*

## 5.12 Pacchetto documentale minimo (prima del primo euro incassato)

| Documento | Priorità | Note |
|---|---|---|
| Informativa privacy (IT + EN) | 🔴 | Versione semplificata separata se apri ai 14–17 |
| Termini di servizio | 🔴 | Include esclusione uso valutativo (D9) e età minima |
| Cookie policy + banner conforme | 🔴 | Solo tecnici se possibile: evita il consenso |
| Disclosure IA art. 50(1) | 🔴 | In-prodotto, non solo nei ToS |
| Marcatura provenienza art. 50(2) | 🔴 | XMP + footer visibile |
| Registro trattamenti (art. 30) | 🔴 | |
| Elenco sub-responsabili | 🔴 | Pubblico |
| DPA con provider di modelli | 🔴 | + ZDR attivo |
| Policy uso accademico | 🟠 | Anche marketing |
| Scheda di sistema / system card | 🟠 | Scopo, limiti noti, VSR/SER misurati, oversight |
| DPIA proporzionata | 🟠 | Necessaria per B2B |
| DPA che *tu* offri ai clienti B2B | 🟠 | Sarai responsabile per i loro dati |
| Nota art. 4 alfabetizzazione | 🟢 | Una pagina |
| Registro incidenti | 🟢 | Vuoto va bene; assente no |

Costo realistico legale + DPO frazionale: **1.500–4.000 €**. Costo di lancio, non opzionale. È anche
asset di vendita B2B: nessun centro di ripetizioni serio compra da chi non ha un'informativa.

---

# 6. Modello di business

## 6.1 Perché non abbonamento puro sul B2C
Stagionalità brutale: due picchi (gen–feb, giu–lug), semi-picco a settembre, mesi morti. Un abbonamento
mensile in questo regime produce rimborsi, disdette e recensioni a una stella. Vedi **D11**.

## 6.2 Listino

**KIRCHHOFF SOLVE (B2C)**

| Piano | Prezzo | Contenuto | Ruolo |
|---|---|---|---|
| **Prova** | 0 € | 3 soluzioni verificate/mese, filigrana | Acquisizione. 3 basta a dimostrare il valore, non a superare una settimana d'esame. |
| **Pacchetto 10** | 4,90 € | 10 soluzioni, no scadenza | Ingresso a basso attrito |
| **Pacchetto 40** | 14,90 € | 40 soluzioni, export PDF/LaTeX | Volume tipico |
| **Pass Sessione** | 19,90 € | 30 giorni illimitati (fair use 150) | **SKU principale nei picchi** |
| **Anno Accademico** | 59 € | 12 mesi illimitati + modalità Studio | Studente diligente |

**KIRCHHOFF STUDIO (B2B)**

| Piano | Prezzo | Contenuto |
|---|---|---|
| **Tutor** | 39 €/mese o 390 €/anno | 1 utente, generazione varianti illimitata, export LaTeX/PDF/Moodle, banco privato |
| **Centro** | 149 €/mese | 5 utenti, banco condiviso, branding |
| **Dipartimento** | da 2.400 €/anno | Utenti multipli, SSO, DPA, profili curricolari su misura, **nessuna funzione valutativa** (D9) |
| **Docenti** | 0 € | Verifica email istituzionale. Investimento in distribuzione, non ricavo. |

Note pricing: euro, IVA inclusa nel display B2C (obbligo consumatori UE). **Nessuno sconto studente sul
B2C**: è già il prezzo studente. Sconto annuale B2B: 2 mesi gratis. Ancoraggio: presenta sempre il Pass
Sessione al centro — è la scelta razionale per chi ha un esame fra tre settimane, ed è la ragione per cui
esiste il Pacchetto 40.

## 6.3 Unit economics

Per soluzione B2C (Pass Sessione, uso medio 25 soluzioni):
```
Ricavo per pass                      19,90 €
MoR fee (~5% + 0,50)                 -1,50 €
Costo modelli (25 × 0,03 €)          -0,75 €
Infrastruttura ammortizzata          -0,30 €
─────────────────────────────────────────────
Margine lordo                        17,35 €  (87%)
```

Per cliente Tutor B2B (annuale):
```
Ricavo annuo                        390,00 €
MoR fee                             -22,00 €
Costo modelli (≈600 gen./anno)      -30,00 €
Supporto (≈1,5 h/anno)              -45,00 €
─────────────────────────────────────────────
Margine lordo                       293,00 €  (75%)
```

**Il numero che decide tutto: il CAC.**
- B2C via SEO organico e passaparola: obiettivo **< 3 €**. Raggiungibile solo se il motore di contenuti funziona.
- B2C via advertising: realisticamente **8–20 €** su LTV 25–40 €. Rapporto marginale. **Niente advertising
  nei primi 6 mesi.**
- B2B via outbound diretto: **50–150 €** su LTV 800–1.500 €. **Canale con l'economia migliore, e senza competizione.**

## 6.4 Fiscalità
⚠️ *Da verificare con il commercialista. Mappa del problema, non parere.*

Vendere servizi digitali B2C a consumatori UE fa scattare le regole IVA del paese del cliente. Soglia
unionale **10.000 € annui** di vendite transfrontaliere B2C: sotto, regime domestico; sopra, IVA del paese
del consumatore, tipicamente via registrazione **OSS**. L'interazione fra forfettario, servizi digitali
transfrontalieri e OSS è uno dei punti più incasinati del sistema italiano, e vendere a studenti spagnoli
o tedeschi ci porta dentro senza preavviso.

| Strada | Come funziona | Pro | Contro |
|---|---|---|---|
| **A. Merchant of Record** (Paddle, Lemon Squeezy) | Il MoR vende all'utente finale; tu vendi al MoR | **Elimina interamente il problema IVA UE.** Un solo rapporto B2B. Time-to-market immediato. | 5%+ del ricavo. Meno controllo su checkout e dati. |
| **B. Stripe + registrazione OSS** | Incassi tu, applichi IVA per paese, dichiari via OSS | Controllo pieno, costi più bassi a volume | Complessità contabile, compatibilità col forfettario, aliquote per 27 paesi |
| **C. Solo Italia** | Blocchi le vendite fuori dall'IT | Semplicissimo | Rinunci al mercato UE. Poco sensato per un prodotto MCP-nativo distribuito globalmente. |

**Raccomandazione: A per il lancio, valutare B sopra i 60–80k € di ricavo annuo.** Il 5% di 20.000 € sono
1.000 € — meno di quanto costa gestire OSS con un commercialista, e infinitamente meno del rischio di sbagliare.
L'infrastruttura di incasso italiana esistente (Stripe/PayPal + ricevute in forfettario) resta utile per la
componente italiana e per il B2B domestico, dove il cliente è un'impresa e le regole sono diverse. Le due
strade coesistono. **Confermare col commercialista prima di implementare.**

## 6.5 Proiezione a 12 mesi
Assunzioni: lancio soft al mese 3, prima sessione d'esame completa al mese 5.

| | Pessimistico | Base | Ottimistico |
|---|---|---|---|
| Utenti registrati M12 | 1.200 | 4.500 | 12.000 |
| Conversione a pagamento | 2,5% | 4,5% | 7% |
| Clienti B2C paganti | 30 | 200 | 840 |
| ARPU B2C annuo | 14 € | 19 € | 24 € |
| **Ricavo B2C** | **420 €** | **3.800 €** | **20.160 €** |
| Clienti B2B (Tutor+) | 3 | 14 | 45 |
| ARPU B2B annuo | 390 € | 480 € | 620 € |
| **Ricavo B2B** | **1.170 €** | **6.720 €** | **27.900 €** |
| **Ricavo totale anno 1** | **1.590 €** | **10.520 €** | **48.060 €** |

**Anche nello scenario ottimistico questo non è un business a tempo pieno al primo anno.** Nel caso base
vale poco più di due mesi di ripetizioni. Tre conclusioni:
1. **Non lasciare le ripetizioni.** Finanziano lo sviluppo, forniscono il canale di distribuzione, generano
   il gold set, e sono il primo cliente B2B. Asset del progetto, non costo opportunità.
2. **Il B2B supera il B2C in ogni scenario.** Nel caso base, 14 clienti B2B > 200 clienti B2C. Se devi
   scegliere dove mettere il tempo, la risposta è quasi sempre B2B.
3. **Il valore reale dell'anno 1 non è il fatturato: è il motore.** Engine di verifica, corpus, profilo
   curricolare e benchmark si compongono. L'anno 2 su questi asset può essere 4–8× l'anno 1; l'anno 1 da
   zero non può.

Se la proiezione sembra troppo bassa per giustificare l'impegno, **fermati adesso e non costruire il
prodotto.** Non c'è nulla di sbagliato nel concluderlo. C'è molto di sbagliato nello scoprirlo al mese 9.

---

# 7. Go-to-market

## 7.1 Posizionamento
> **Per** studenti di ingegneria che devono risolvere circuiti e non possono permettersi una risposta sbagliata,
> **Kirchhoff** è un risolutore di circuiti verificato
> **che** ricostruisce il circuito dalla foto, produce il procedimento passo per passo con i disegni, e
> certifica ogni risultato con cinque controlli indipendenti prima di mostrarlo,
> **a differenza di** ChatGPT e degli app di compiti, che producono risposte plausibili senza sapere se
> sono corrette.

**Claim centrale, da ripetere ovunque: "Non plausibile. Verificata."**

## 7.2 Gerarchia dei messaggi
**Primario:** ogni soluzione supera cinque controlli — KCL, KVL, bilancio di potenza, accordo fra due
metodi indipendenti, sanità fisica — prima di essere mostrata.
**Secondari:** il procedimento come lo scriveresti a mano, col circuito ridisegnato a ogni riduzione; se
il sistema non è sicuro di aver letto la foto, **chiede** invece di inventare; export LaTeX/PDF pulito;
profili per corso (usa i metodi che il tuo professore accetta).
**Da non dire mai:** ❌ "risolve qualsiasi circuito" (falso, si smonta in dieci secondi); ❌ "IA avanzata /
powered by AI" (messaggio di tutti, non differenzia); ❌ "basato su MCP" nel marketing B2C (a nessuno
studente interessa il protocollo — nel materiale tecnico sì).

## 7.3 Canali, ordinati per CAC atteso
1. **La base esistente — CAC ≈ 0. Settimana 1.** Oltre 300 studenti passati e attuali. Non è "un canale":
   è il vantaggio iniziale che quasi nessun fondatore ha in questo mercato. Gold set, beta test, primi
   feedback, primi referral.
2. **Gruppi di corso Telegram/WhatsApp — CAC ≈ 0–2 €.** Il vero sistema di distribuzione degli studenti
   italiani. Non spammare: **entra risolvendo.** Un post nel gruppo giusto, la settimana prima dell'esame,
   che risolve *l'esercizio che stanno tutti chiedendo*, con PDF allegato e link. Il tasso di diffusione di
   uno strumento utile in un gruppo di corso batte qualunque campagna a pagamento.
3. **SEO su coda lunga — CAC decrescente, canale composto. Mesi 2–12.** Se avviato al mese 2, al mese 12
   porta la maggior parte del traffico organico.
4. **Video brevi — CAC 2–8 €.** *"Esercizio d'esame di Elettrotecnica risolto e verificato in 30 secondi"*,
   col momento di verifica in evidenza. YouTube Shorts + TikTok + Instagram, un video ogni due giorni dal
   corpus esistente. Il contenuto esiste già: cambia solo il formato d'uscita.
5. **Directory MCP (Claude / ChatGPT) — CAC basso, volume incerto.** Poca concorrenza nella categoria
   educativa, vale la pena esserci presto. Ma è un'opzione, non un piano di acquisizione.
6. **Outbound B2B — CAC 50–150 €, LTV 800–1.500 €. Mese 4.** Centri di ripetizioni, tutor privati, docenti.
   Lista costruibile a mano in una settimana. Email personalizzata con **una variante d'esame generata dal
   loro programma**, allegata. Non un pitch: una dimostrazione. Tasso di risposta molto sopra la media
   perché il valore è visibile prima della chiamata.
7. **Advertising a pagamento — NON nei primi 6 mesi.** Con LTV B2C 25–40 € non c'è margine per imparare a
   fare advertising. Tornaci quando l'LTV è misurato, non stimato.

## 7.4 Il motore di contenuti

```
   Il corpus LaTeX esistente
   (Elettrotecnica, Automatica, VLSI, analisi numerica…)
                    │
                    ▼
        KIRCHHOFF STUDIO genera N varianti
        con soluzione completa verificata
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
  Pagine pubbliche SEO      Prodotto B2B venduto
  (varianti TUE, non              a tutor
  temi d'esame altrui)             │
        │                          │
        ▼                          ▼
  Traffico organico          Ricavo ricorrente
        │                          │
        ▼                          │
  Iscrizioni B2C ──────────────────┘
        │
        ▼
  Upload reali → miglioramento del benchmark
        │
        ▼
  VSR più alto → prodotto migliore → più referral
```

Ogni pagina pubblica è (a) contenuto SEO, (b) demo del prodotto, (c) artefatto legalmente sicuro perché
generato da noi (§5.10), (d) sottoprodotto gratuito di un asset B2B già venduto. **Un solo lavoro, quattro output.**

**Struttura pagina tipo** (`/esercizi/elettrotecnica/millman-tre-rami-01`): testo dell'esercizio (variante
generata, non copiata); circuito in SVG; soluzione completa con passaggi e disegni intermedi; badge di
verifica con residui numerici; 3 varianti collegate; CTA *"Hai un esercizio diverso? Fai una foto."*

Target realistico: **300 pagine entro il mese 6**, generate in gran parte automaticamente e riviste a
campione. Non 3.000: la qualità è fattore di ranking, e la revisione umana a campione è il vincolo.

## 7.5 Sequenza di lancio

| Fase | Quando | Azione | Criterio di uscita |
|---|---|---|---|
| **0. Benchmark** | Sett. 1–2 | Gold set 200 foto + baseline frontier | Numero in mano (§2.5) |
| **1. Engine** | Sett. 3–8 | IR, solver, verifica, renderer. Solo CLI. | VSR > 65% sul dev set |
| **2. Alpha privata** | Sett. 9–10 | 20 studenti, tutto gratis | 15/20 lo riusano spontaneamente |
| **3. Beta pubblica** | Sett. 11–14 | Web app + crediti + pacchetto compliance | 20 utenti paganti |
| **4. Contenuti** | Sett. 12–24 | 300 pagine SEO, video | 1.000 visite organiche/mese |
| **5. MCP** | Sett. 16–20 | Server MCP + MCP App, submission directory | Pubblicato e funzionante |
| **6. Studio B2B** | Sett. 18–26 | Generatore varianti, outbound | 5 clienti B2B paganti |
| **7. Sessione** | Gen 2027 | Push massimo sul picco d'esame | Misura tutto |

**Timing critico.** Il lancio B2C deve arrivare **prima di una sessione d'esame**, non durante. Lanciare a
metà agosto o a novembre significa non avere domanda. Da oggi: engine ago–set, beta a ottobre, spinta piena
a **dicembre–gennaio**.

## 7.6 Struttura della landing page

```
┌────────────────────────────────────────────────────────┐
│  [logo]                          Prezzi · Docenti · Entra│
├────────────────────────────────────────────────────────┤
│      Il circuito dalla foto.                           │
│      Il procedimento passo per passo.                  │
│      La certezza che il numero è giusto.               │
│                                                        │
│   Kirchhoff verifica ogni soluzione con cinque         │
│   controlli indipendenti prima di mostrartela.         │
│   Se non li supera, te lo dice.                        │
│                                                        │
│         [ Carica una foto — 3 gratis ]                 │
│                                                        │
│   ⚡ Kirchhoff usa IA per leggere il circuito.          │
│      I calcoli sono verificati automaticamente. ← art.50│
├────────────────────────────────────────────────────────┤
│  DEMO INTERATTIVA — foto reale, 25 secondi, senza      │
│  registrazione. Anteprima ricostruzione e badge di     │
│  verifica DEVONO essere visibili.                      │
├────────────────────────────────────────────────────────┤
│  I CINQUE CONTROLLI                                    │
│  ✓ KCL   ✓ KVL   ✓ Bilancio di potenza                │
│  ✓ Due metodi indipendenti concordano                  │
│  ✓ Coerenza fisica                                     │
│  → link: "Come funziona la verifica" (pagina tecnica)  │
├────────────────────────────────────────────────────────┤
│  CONFRONTO ONESTO                                      │
│              Kirchhoff   Chatbot   App compiti         │
│  Verifica       ✓           ✗          ✗              │
│  Passaggi       ✓          a volte     ✗              │
│  Disegni interm.✓           ✗          ✗              │
│  Ammette dubbi  ✓           ✗          ✗              │
│  Circuiti non lineari  ✗   parziale   parziale  ← DILLO│
├────────────────────────────────────────────────────────┤
│  PER I DOCENTI — accesso gratuito a Studio             │
├────────────────────────────────────────────────────────┤
│  Prezzi · Privacy · Uso accademico · Contatti          │
└────────────────────────────────────────────────────────┘
```

La riga "Circuiti non lineari ✗" non è un errore: **dichiarare esplicitamente un limite aumenta la
credibilità di tutte le altre righe.** Stessa logica che rende credibile il badge di verifica.

## 7.7 Il programma docenti
Il critico più pericoloso è il docente universitario. Rendilo il distributore.
Offerta: **Studio gratis a vita** con email istituzionale verificata, senza obblighi. Il valore ottenuto:
il docente prova il generatore di varianti e ne diventa dipendente; il profilo curricolare del suo corso
finisce nel sistema (asset difendibile); non scrive il post arrabbiato; i suoi studenti vedono lo strumento
nel materiale del corso; a un certo punto il dipartimento chiede un preventivo.
Costo marginale: ~2 €/anno per docente. **ROI più alto del piano.**

---

# 8. Metriche

**Nord (una sola): Soluzioni verificate consegnate per settimana.** Cattura simultaneamente domanda,
qualità tecnica e valore erogato.

**Tecniche:** VSR, SER, QPS, TTV (§4.13). SER è la metrica di sicurezza del prodotto (**D12**).

**Prodotto:**
- Attivazione = prima soluzione verificata entro 10 minuti dalla registrazione. Target **> 60%**.
- D7 = quota che torna entro 7 giorni. Target **> 25%** (stagionale: leggilo per coorte d'esame, non aggregato).
- Ritorno alla seconda soluzione. Target **> 70%** — se qualcuno risolve una sola cosa e sparisce, il
  prodotto non ha convinto.

**Business:** conversione al primo pagamento (per coorte di sessione, non mensile); ricavo per coorte;
CAC per canale; seat B2B netti e churn B2B (target < 5% annuo); margine lordo (target > 80%).

**Fiducia (categoria che quasi nessuno misura e che qui è centrale):**
- **correzioni per soluzione** — quante volte l'utente corregge la ricostruzione. Sopra 1,0 = il sistema legge male.
- **tasso di rifiuto** — soluzioni che non superano la verifica e non vengono pubblicate. **Non è un bug da
  azzerare: è il sistema che funziona.** Ma sopra il 15% il prodotto risulta inaffidabile a prescindere
  dalla correttezza.
- **segnalazioni di errore per 1.000 soluzioni** — segnale precoce che SER sta salendo.

---

# 9. Roadmap e criteri di kill

## Trimestre 1 (mesi 1–3) — Prova o smentisci
**Consegne:** gold set 200; misura baseline; IR v1; solver doppio percorso; 5 controlli; renderer SVG+TikZ;
CLI funzionante; 20 alpha tester.

**🔴 CRITERI DI KILL:**
- **baseline frontier > 85%** su foto reali *e* non superabile di almeno 8 punti col nostro pipeline →
  **il valore non è nella visione.** Abbandona il B2C foto-based, vai diretto su Studio B2B con input strutturato.
- **VSR < 50%** dopo 8 settimane → riduci lo scope a "reti resistive in DC" e riprova, oppure fermati.
- **SER > 2%** e non scende → **ferma tutto.** Un prodotto la cui promessa è la verifica e che sbaglia
  silenziosamente il 2% delle volte è peggio che inutile: è dannoso e brucia la reputazione presso i
  docenti in modo permanente.

## Trimestre 2 (mesi 4–6) — Immetti sul mercato
**Consegne:** web app PWA; crediti + MoR; pacchetto compliance completo; server MCP + MCP App; 300 pagine
SEO; 30 video; primi 5 clienti B2B.

**🔴 CRITERI DI KILL:**
- **< 20 utenti paganti B2C** dopo 8 settimane di beta pubblica con traffico → il problema è posizionamento
  o prezzo, non il prodotto. Fermati e intervista 15 utenti non convertiti prima di scrivere altro codice.
- **0 clienti B2B** dopo 40 contatti outbound qualificati → l'ipotesi B2B è sbagliata. La più grave, perché
  il B2B regge l'economia del piano.

## Trimestre 3 (mesi 7–9) — Componi
**Consegne:** modalità Studio completa; profili curricolari per 5 corsi reali; secondo dominio (Automatica:
Bode/Nyquist — corpus già esistente); espansione B2B; verifica ngspice.

## Trimestre 4 (mesi 10–12) — Sessione e decisione
**Consegne:** spinta massima su gennaio; misura tutto per coorte; decisione strategica sull'anno 2.

**Decisione a M12, sui numeri:**
- Ricavo B2B > 15k € annualizzato → **doppia sul B2B**, il B2C diventa canale di acquisizione.
- Ricavo B2C > 25k € annualizzato → il consumer funziona, valuta advertising e mercati esteri.
- Entrambi sotto → l'ipotesi di mercato è sbagliata. **Il motore resta comunque tuo** e continua a servire
  nelle ripetizioni: non è un fallimento totale, ma smetti di investirci tempo.

---

# 10. Registro rischi

| # | Rischio | P | I | Mitigazione |
|---|---|---|---|---|
| R1 | **Errore silenzioso**: soluzione sbagliata mostrata come verificata | M | **Molto alto** | 5 controlli; SER metrica bloccante; anteprima sempre visibile; escalation invece di indovinare |
| R2 | I modelli frontier commoditizzano il caso d'uso | **Alta** | Alto | Valore su verifica + corpus + curriculum + generazione B2B. Ricontrolla la baseline ogni trimestre |
| R3 | Nessuno paga (studenti) | Alta | Alto | Crediti, non abbonamento; B2B come base economica |
| R4 | Violazione copyright su temi d'esame | M | Alto | Solo varianti generate; niente archivio pubblico di upload; licenze esplicite |
| R5 | Blocco da parte di un ateneo / campagna docenti | M | Alto | Modalità Studio default; policy uso accademico; marcatura provenienza; programma docenti gratuito |
| R6 | Deriva verso feature valutative → Allegato III | M | **Molto alto** | Esclusione esplicita in ToS + blocco tecnico + revisione a ogni release |
| R7 | Sanzione art. 50 per mancata disclosure/marcatura | Bassa | M | Implementata al giorno 1; Code of Practice |
| R8 | Data breach su immagini con dati personali | Bassa | Alto | TTL 24–72h; blur; cifratura; ZDR con i provider |
| R9 | Cambio unilaterale policy directory MCP | M | Basso | La web app resta il sistema di record |
| R10 | Aumento prezzi o degrado dei modelli upstream | M | M | Astrazione multi-provider dal giorno 1; cascata economico→frontier |
| R11 | **Esaurimento del fondatore** | **Alta** | **Molto alto** | Scope brutalmente ristretto (D8); criteri di kill scritti; ripetizioni non abbandonate |
| R12 | Complessità IVA/OSS blocca il lancio | M | M | MoR dal giorno 1 |
| R13 | Il gold set non rappresenta le foto reali → VSR gonfiato | M | Alto | Foto raccolte dagli studenti, non scansioni; held-out mai guardato |

**R11 merita una nota.** Il rischio più concreto non è tecnico né normativo: è che Kirchhoff diventi il
sesto progetto al 60% accanto a ripetizioni, ELAB Builder, StudiaCazzo, Ghost Tutor e broker_v4.
**La decisione più importante non è come costruirlo, ma se c'è lo spazio per costruirlo davvero.** Se no,
la mossa corretta è ridurre lo scope al solo **Kirchhoff Studio** — il generatore di varianti verificate —
più piccolo, utile personalmente ogni settimana, economia migliore, e senza né visione né compliance consumer.

---

# 11. I prossimi 14 giorni

**Giorno 1–2**
1. Scrivi a 30 studenti: *"Mandami 5 foto di esercizi di circuiti dai tuoi appunti, fatte come le faresti
   davvero"*. Obiettivo: 150 foto.
2. Compra il dominio. Verifica il marchio su TMview/UIBM prima di affezionarti al nome.

**Giorno 3–5**
3. Costruisci il gold set: IR + risultato corretto per 100 foto. Noioso, indispensabile, non delegabile.
4. Scrivi lo script di eval (input: cartella immagini + gold; output: VSR, SER, matrice degli errori).

**Giorno 6–7**
5. **Misura la baseline frontier.** Tre modelli, prompt semplice, nessun tuo codice.
6. **Leggi il numero e prendi la decisione di §2.5.** Non proseguire prima di averla presa.

**Giorno 8–12**
7. Prototipo IR + parser + validazione elettrica + MNA con lcapy + i 5 controlli. Solo CLI, nessuna UI.
8. Fai girare l'eval sul pipeline. Confronta con la baseline.

**Giorno 13–14**
9. Delta ≥ 8 punti: continua secondo la roadmap.
10. Delta < 8 punti: **scrivi il pivot verso Studio B2B** e riparti da lì. Non è un fallimento — è il test
    che ha funzionato.
11. In parallelo, a prescindere dall'esito: manda 10 email a centri di ripetizioni con una variante d'esame
    generata a mano, e misura il tasso di risposta. **Il segnale B2B costa due ore e vale più di due mesi
    di sviluppo.**

---

# Appendice A — Riferimenti verificati

**Specifica MCP**
- MCP 2026-07-28, annuncio finale — `blog.modelcontextprotocol.io/posts/2026-07-28/`
- Release candidate (21 mag 2026) — `blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/`
- MRTR = SEP-2322; rimozione handshake = SEP-2575; rimozione session id = SEP-2567; lifecycle/deprecazioni
  = SEP-2596; deprecazione Roots/Sampling/Logging = SEP-2577
- MCP Apps (SEP-1865), finalizzata 26 gen 2026 — `blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/`;
  repo `github.com/modelcontextprotocol/ext-apps`

**AI Act**
- Reg. (UE) 2024/1689; Allegato III punto 3 — `artificialintelligenceact.eu/annex/3/`
- Digital Omnibus on AI = Reg. (UE) 2026/1744, GU 24 lug 2026, in vigore 27 lug 2026
- Nuove scadenze: Annex III → 2 dic 2027; Annex I → 2 ago 2028; art. 50 invariato al 2 ago 2026;
  art. 50(2) per sistemi legacy → 2 dic 2026; nuovi divieti → 2 dic 2026
- Linee guida Commissione su art. 50, adottate 20 lug 2026 —
  `digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act`
- Sanzioni art. 50: fino a 15 M€ o 3% del fatturato mondiale (PMI/startup: l'importo inferiore)

**Diritto italiano**
- Legge 23 settembre 2025 n. 132, art. 4 — accesso IA minori di 14 anni con consenso genitoriale;
  14–17 consenso autonomo con informazioni accessibili e comprensibili
- Art. 2-quinquies Codice Privacy (d.lgs. 196/2003, mod. d.lgs. 101/2018) — consenso digitale a 14 anni
- Garante Privacy, sezione Minori — `garanteprivacy.it/temi/minori`

**Studio citato**
- arXiv 2607.25635, *An Empirical Study of Model Context Protocol Applications* — 1.723 "MCPApps" =
  **applicazioni client** che consumano server MCP, **non** l'estensione UI MCP Apps

---

# Appendice B — Prompt di estrazione (bozza da iterare)

```
Sei un estrattore di circuiti elettrici. Produci SOLO JSON conforme allo schema.

REGOLE ASSOLUTE
1. Non inventare MAI un valore. Se un valore non è leggibile con certezza,
   emetti value: null e popola alternatives[] con ciò che potrebbe essere.
2. Non inferire MAI una connessione da vicinanza visiva. Due fili che si
   incrociano sono collegati SOLO se c'è un punto pieno di giunzione.
3. Riporta il bbox di ogni componente e di ogni etichetta di valore.
4. Se vedi più circuiti/esercizi, elencali tutti separatamente. Non fonderli.
5. Se l'immagine contiene testo con i valori (elenco dati), estrailo in un
   campo separato `text_values` senza fonderlo con le letture dal disegno.

AMBIGUITÀ DA SEGNALARE SEMPRE
- cifre confondibili: 2/3, 0/6, 1/7, 5/6
- prefissi: μ vs m, k vs K
- polarità di generatori poco visibile
- verso delle frecce (corrente o tensione?)
- stato/verso di interruttori
- incroci senza punto di giunzione evidente

SCHEMA DI OUTPUT
<schema IR §4.2>
```

Casi obbligatori nell'eval del prompt:
- immagine con un valore deliberatamente cancellato → deve emettere `null`, non indovinare;
- incrocio senza punto → deve **non** collegare;
- due esercizi nella stessa foto → deve elencarli entrambi.

---

# Appendice C — Checklist compliance operativa pre-lancio

```
AI ACT
[ ] Disclosure art. 50(1) visibile al primo contatto (web + MCP App)
[ ] Marcatura art. 50(2): XMP nei PDF + data-attr negli SVG + footer visibile
[ ] Adesione al Code of Practice sulla trasparenza dei contenuti IA
[ ] Nota art. 4 alfabetizzazione IA (1 pagina, interna)
[ ] System card: scopo, limiti noti, VSR/SER misurati, oversight umano
[ ] ToS: esclusione esplicita di uso valutativo/di accesso
[ ] Blocco tecnico: nessun endpoint restituisce punteggi per persona
[ ] Revisione trimestrale della classificazione (Annex III drift check)

GDPR
[ ] Informativa privacy IT/EN + versione semplificata 14–17
[ ] Registro dei trattamenti (art. 30)
[ ] Basi giuridiche mappate per T1–T8
[ ] LIA scritta per il legittimo interesse (T5, T8)
[ ] TTL 24–72h sulle immagini, cancellazione automatica verificata
[ ] Blur opzionale delle regioni testuali prima dell'invio al provider
[ ] Opt-in esplicito per T6 (miglioramento modello), OFF di default
[ ] DPA firmati con tutti i provider di modelli
[ ] Zero Data Retention attivo e verificato
[ ] Strumento di trasferimento verificato alla data di lancio
[ ] Elenco pubblico sub-responsabili + notifica preventiva modifiche
[ ] Gestione diritti interessati (accesso, cancellazione, portabilità) < 30 gg
[ ] DPIA proporzionata
[ ] Procedura data breach (72h) documentata
[ ] Cookie: solo tecnici se possibile; altrimenti banner conforme

ITALIA
[ ] Età minima 14 con dichiarazione esplicita al signup
[ ] Informativa in linguaggio comprensibile per 14–17 (L.132/2025 art.4)
[ ] Procedura rimozione account non conformi
[ ] Regime IVA definito (MoR o OSS) — CONFERMATO DAL COMMERCIALISTA
[ ] Fatturazione/ricevute conformi al regime applicabile

PRODOTTO
[ ] Policy uso accademico pubblica
[ ] Marcatura di provenienza su ogni export
[ ] Modalità Studio come default educativo
[ ] Nessuna modalità "solo risposta" per tenant istituzionali
[ ] Registro incidenti attivo
```

---

*Fine documento sorgente.*
