---
title: 'Escalation — le tre cause v2 non possono uscire dal contratto pubblico'
type: 'owner-decision'
created: '2026-08-25'
classe: 'R3 — tocca AD-22 e AD-19'
trovato_da: 'Blind Hunter Fable 5 max, quarta tornata'
---

# Il rilievo, verificato

`transform()` non può emettere **nessuna** delle tre cause che questo ramo ha
aggiunto ad AD-19.

| Causa | Perché non può uscire |
|---|---|
| `identity_violation` | zero produttori: i controlli d'identità sono usciti con `node_mapping` (v2.2) |
| `preserve_nonmaximal` | `engine.py:205` riempie `patch.preserve` con `preserve_set(prima, dopo, op)`, e `check_transform` la riconfronta con `preserve_set(before, after, op)` — funzione **pura** sugli stessi argomenti: `f(x) != f(x)` non è mai vero. Il secondo ramo (`create ∩ Pₖ`) è strutturalmente vuoto: `_nuovo_id` garantisce un id assente da `Cₖ` |
| `empty_boundary` | le riduzioni costruiscono sempre un `Boundary`; `None` non arriva mai dal motore |

Empirico del revisore: griglia di chiamate su tre circuiti più il prodotto non
valido e l'ingresso rotto. **Unica causa mai osservata: `topology`.**

I test vedono i tre `Refusal` solo chiamando `check_transform` a mano con patch
costruite dal test, o monkeypatchando il motore.

# Perché è una decisione e non una correzione

AD-22 promette che la massimalità sia **«verificata indipendentemente dalla
`Transform` che la dichiara»**. Ma nessuna `Transform` dichiara un `preserve`:
`_prodotto` non lo accetta nemmeno come parametro, lo **deriva**. Riferimento e
misurato sono la stessa variabile.

L'argomento con cui questo stesso ramo ha rimosso i controlli d'identità —
*«un controllo che non può più fallire non protegge nulla, e lasciarlo
suggerirebbe una superficie che il contratto non ha più»* — vale parola per parola
qui, e il `Certificate` elenca «massimalità di preserve» fra i controlli
**eseguiti**: attestazione tautologica.

**C'è però una differenza dal caso identità, e conta.** L'identità era
infalsificabile *per costruzione del tipo*: `Pₖ` è un'intersezione per
identificatore, quindi ogni elemento ha lo stesso nome nei due circuiti, punto.
`preserve_nonmaximal` invece **può** fallire — per un produttore esterno.
`check_transform` è esportato ed è la porta dichiarata per chi non è il motore.

Quindi il controllo è: **significativo al confine pubblico, tautologico sul
percorso interno.**

# Le tre uscite

**A — le Trasformazioni dichiarano `preserve`.** `_prodotto` lo accetta come
parametro invece di derivarlo, e `check_transform` lo verifica contro `Pₖ`
calcolato in proprio. È ciò che AD-22 sembra intendere con «indipendentemente
dalla `Transform` che la dichiara», e renderebbe il controllo reale anche
internamente. Costo: ogni voce del catalogo deve dichiarare il proprio `preserve`,
e sbagliarlo diventa un `Refusal` invece di un'impossibilità.

**B — si dichiara che il percorso interno è per costruzione conforme**, e
`CONTROLLI` smette di elencare la massimalità fra i controlli *eseguiti* sul
prodotto del motore, come già fatto per l'identità. Il gate resta per i produttori
esterni. Costo: il `Certificate` diventa più povero e più vero.

**C — nulla, e si registra.** Il controllo resta dov'è, il `Certificate` continua
a elencarlo, e si accetta che sul percorso interno sia tautologico.

# Che cosa è stato fatto e cosa no

**Fatto:** niente su questo rilievo. Non si inventa la semantica di AD-22.

**Registrato:** anche la seconda metà del rilievo su `reroute_scope`. La parte
verificabile è chiusa — fantasmi e insieme vuoto sono contestati da `check_patch` —
ma **che cosa il campo debba contenere resta aperto**: il docstring lo definisce
«l'insieme dei rami la cui instradatura è libera», il motore vi scrive il
componente creato più i **nodi** del boundary. Le due letture non coincidono, e
nemmeno il produttore interno rispetta la semantica dichiarata.
