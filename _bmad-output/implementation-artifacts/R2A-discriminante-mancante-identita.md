---
title: 'R2-A — il discriminante che manca ad AD-22'
type: 'finding'
created: '2026-08-24'
baseline_commit: '7095030'
stato: 'richiede decisione owner / chain-top'
---

# Cosa è stato verificato prima di scrivere

**Search-before-build eseguito.** Il concetto non va inventato: esiste già come caso
`preserve ⊋ Pₖ` in `reviews/review-invarianti.md` R3, che lo nomina e dichiara che *«non è
nominato»* da nessun documento. Nessun `IdentityWitness` è stato introdotto.

**Semantica di `preserve_nonmaximal`, verificata alla fonte.** `ARCHITECTURE-SPINE.md:495-496`:

> *«Un `LayoutPatch` con `preserve` **diverso da** `Pₖ` è **non conforme** e viene rifiutato da
> `domain/transform/check` (`preserve_nonmaximal`), non ottimizzato.»*

«Diverso da», non «più piccolo di». **La causa copre già entrambi i versi** e non va sovraccaricata.
Resta un disallineamento fra nome e regola — `nonmaximal` suggerisce una direzione, la Rule enuncia
un'uguaglianza — che è materia di chiarimento, non di semantica nuova.

**Quindi il problema non è la causa. È `Pₖ`.**

# Il difetto, dimostrato con codice eseguito

`Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` è un'intersezione **per identificatore**: `canonical.py` ordina
per `(type, id, terminals)` e l'identità di un componente è il suo `id`.

Caso costruito ed eseguito il 24/08/2026 — riduzione in parallelo con riuso deliberato dell'id:

```
prima:  R1 (a,b) 10Ω · R2 (a,b) 20Ω · RL (b,0) 5Ω
dopo:   R1 (a,b) 6⅔Ω · RL (b,0) 5Ω          ← la nuova equivalente battezzata "R1"

preserve_set(prima, dopo) → {component:R1, component:RL, node:0, node:a, node:b}
   R1 ∈ Pₖ  →  True
```

E il confronto attributo per attributo delle due `R1`:

| | prima | dopo | coincide |
|---|---|---|---|
| `type` | resistor | resistor | **sì** |
| `terminals` | `(a, b)` | `(a, b)` | **sì** |
| `value` | 10 Ω | 6⅔ Ω | no |

**Tipo e terminali coincidono. L'unica differenza è il valore — ed è esattamente ciò che
«preservato ≠ immutabile» potrebbe legittimamente consentire.**

Nel caso della riduzione in **serie** un discriminante strutturale ci sarebbe: `R1 (a,b)` e
`R2 (b,0)` fondono in `(a,0)`, e i terminali cambiano. Nel **parallelo** no. Un discriminante che
funziona su un caso e non sull'altro non è un discriminante.

# Il discriminante che manca, nominato con precisione

Nessun attributo oggi presente nel `CircuitIR` separa

> «entità legittimamente preservata il cui valore è cambiato»

da

> «entità nuova che indossa l'identificatore di una consumata».

Manca **una dichiarazione, per ciascuna operazione del catalogo, di quali attributi di un'entità
possono cambiare mentre la sua identità sopravvive** — e, per differenza, quali no.

Con quella dichiarazione il controllo diventa meccanico: `serie` non può cambiare il valore di
un'entità preservata, quindi una `R1` con valore diverso non è preservata; una futura operazione che
*deve* poterlo fare lo dichiara, e il controllo lo consente **per quella operazione soltanto**.

Senza, ogni regola scritta oggi sarebbe o troppo stretta — e violerebbe CV3, che stabilisce che
preservato non significa immutato — o troppo larga, e lascerebbe il difetto aperto.

# Perché mi sono fermato invece di scriverla

`KIRCHHOFF-KNOWLEDGE/10-Costituzione/Confini owner-locked.md` elenca fra i confini che richiedono
decisione umana o BMAD chain-top la **definizione di `Verified`**. `Pₖ` alimenta VCER, che alimenta
Gate A, che decide se una derivazione visuale è certificata. Stabilire cosa può cambiare mentre
l'identità sopravvive **è dare forma a cosa significa `Verified`**.

E la Regola di collisione della stessa nota è esplicita:

> *«Un agente che incontra un criterio di accettazione, un rilievo o una proposta di ottimizzazione
> che richiede di violare un confine **si ferma e lo segnala**. Non sceglie, non aggira, non chiede
> scusa e procede.»*

# Conseguenza sul piano

**R2-A non chiude Story 1.1.** La blocca con precisione maggiore: prima il blocco era *«manca una
regola»*, adesso è *«manca la dichiarazione per-operazione di ciò che può cambiare»*, che è una
domanda a cui si può rispondere.

Le due strade, entrambe pulite:

- **A — dichiarazione per operazione nel catalogo.** Ogni voce del catalogo chiuso dichiara gli
  attributi mutabili sotto di sé. `serie` e `parallelo` non ne dichiarano nessuno: una preservata
  non cambia. Costo: una riga per operazione. Chiude il difetto e rispetta CV3.
- **B — nessuna mutazione ammessa in `Pₖ`, e ogni cambiamento è consumo più creazione.** Più
  semplice e più stretta. Rischia di violare CV3 quando arriveranno le operazioni che modificano in
  luogo — la disattivazione di un generatore, per esempio, che cambia un valore conservando
  l'identità del componente.

**B è più veloce e probabilmente sbagliata sui transitori e sul fasoriale.** A costa una riga per
operazione e regge.

Nessuna delle due è stata scritta nello spine.
