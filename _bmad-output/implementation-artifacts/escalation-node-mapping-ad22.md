---
title: 'Escalation — `node_mapping` non ha un uso legale non banale'
type: 'owner-decision'
created: '2026-08-25'
blocca: 'chiusura della Story 2.6'
classe: 'R3 — decisione di proprieta (emendamento dello spine)'
---

# Che cosa è stato misurato

Il rilievo del Blind Hunter diceva: *«`node_mapping` non ha alcun uso legale: i
due versi del ciclo d'identità coprono l'intero spazio delle mappe con sorgente
reale.»* Verificato per esecuzione, e il risultato è più netto dell'accusa.

| Mappa | Semantica | Esito di `check_transform` |
|---|---|---|
| `b → z` | rinomina vera: `b` sopravvive col nome `z` in `Cₖ₊₁` | **rifiutata** — `identity_violation su b` |
| `b → a` | non iniettiva (`a` si mappa su sé per identità) | **rifiutata** — ora per iniettività |
| `zzz → w` | sorgente assente da `Cₖ` | **era accettata** (`None`) |

Cioè: **ogni mappa con sorgente reale veniva rifiutata, e l'unica che passava era
un riferimento a nulla.** Il buco della spazzatura è stato chiuso (controllo `0a`);
resta la domanda che non decido io.

# Perché accade — la tensione è dentro AD-22 v2

Tre clausole dello stesso emendamento, prese insieme:

1. **«`node_mapping` è totale e iniettiva sui sopravvissuti»** — presuppone che la
   mappa abbia per dominio i sopravvissuti.
2. **`Pₖ` è preso *dopo* `node_mapping`** — quindi un nodo la cui immagine esiste
   in `Cₖ₊₁` entra in `Pₖ`.
3. **`id_{k+1}(x) = id_k(x)` per ogni `x ∈ Pₖ`, senza tolleranza** — quindi un
   sopravvissuto non può essere rinominato.

Da 2 e 3: qualunque nodo che la mappa riesce a mappare finisce in `Pₖ`, e lì
l'identità senza tolleranza gli vieta di avere un nome diverso. Da 1: il dominio
sono i sopravvissuti. **L'unico contenuto legale del campo è la mappa identità**,
cioè nessuna informazione.

Non è un difetto di implementazione: le tre clausole sono implementate fedelmente.
È il loro prodotto logico.

# Le due uscite, e perché non scelgo

## A — emendare AD-22: l'identità vale sull'immagine, non sul nome

`id_{k+1}(map(x)) = map(id_k(x))`. La rinomina diventa esprimibile e resta
verificabile, ma indebolisce «senza tolleranza», che l'emendamento del 15 agosto
ha introdotto **apposta** per chiudere un'autocertificazione. Riaprirla richiede
di mostrare che il nuovo verso non la riapre.

## B — ritirare o differire il campo

`node_mapping` esce da `LayoutPatch` finché non esiste un caso d'uso dimostrato.
Coerente con la dottrina del prodotto: un campo che non può portare informazione
legale è una superficie che mente sulle proprie capacità. Ma AD-22 lo **nomina**,
quindi ritirarlo è comunque un emendamento dello spine.

# Perché è tua

Entrambe le uscite modificano AD-22. Per la topologia che hai congelato, una
decisione che tocca lo spine è **R3 — CHAIN-TOP**, e la tua istruzione era
esplicita:

> «Non aggiungere casi speciali finché non hai chiarito: esiste realmente un
> mapping valido che l'architettura vuole supportare? […] Non decidere dal codice
> isolato.»

Non l'ho deciso. Il codice oggi rifiuta tutto ciò che è verificabilmente
sbagliato — mappe non iniettive, sorgenti inesistenti, arrivi inesistenti,
rinomine di sopravvissuti — e non inventa una semantica che lo spine non ha.

# Che cosa serve per chiudere il criterio della Story

Finché la decisione è aperta, `node_mapping` resta un campo che **solo** la mappa
vuota può riempire legalmente. Va detto nella Story invece che lasciato implicito:
è la differenza fra un campo differito e un campo morto di cui nessuno sa.

---

# DECISIONE OWNER — 25 agosto 2026: **B, ritiro/differimento**

> «La regola più importante da preservare è: *same semantic entity → same semantic
> identifier*, perché è proprio ciò che impedisce al transformer di autocertificare
> la preservazione riutilizzando o reinterpretando identificatori.»

L'uscita **A** è stata respinta esplicitamente: `id_{k+1}(map(x)) = map(id_k(x))`
introdurrebbe una seconda nozione di identità — «stesso id» accanto a «stessa
entità dopo una rinomina» — e renderebbe molto più difficile stabilire `Pₖ` in
modo indipendente. Nel punto più delicato di Gate A si preferisce una semantica
più piccola e verificabile a una più espressiva e ambigua.

## Che cosa è stato fatto

**Architettura** — AD-22 emendata a **v2.2**. Le clausole della v2 che
riguardavano `node_mapping` restano scritte come **provenienza**: descrivono un
contratto che ha smesso di essere corrente, non un errore da cancellare. Stato:
**DIFFERITA**.

**Codice** — il campo è uscito dal contratto runtime, e con lui tutto ciò che
esisteva solo per sostenerlo:

| Rimosso | Dove |
|---|---|
| campo `node_mapping` | `LayoutPatch` |
| validazione della mappa (vuoto, funzionale, iniettiva) | `LayoutPatch.__post_init__` |
| `image_of` | `LayoutPatch` |
| `_immagine` | `check.py` |
| parametro `node_mapping` | `preserve_set` |
| controllo (0a) dominio della mappa | `check_transform` |
| controllo (0) iniettività | `check_transform` |
| controllo (a) rinomina non confermata | `check_transform` |
| controllo (b) sopravvissuto rinominato | `check_transform` |
| produttore `node_mapping=()` | `engine.py` |

Nessun campo sostitutivo. Nessuna `IdentityMap`, `RenameMap`, `SemanticAlias` o
`SurvivorMap`.

## Che cosa dimostrano i test superstiti

I guard sono stati scritti **prima** della rimozione, per provare che togliere lo
strato non indebolisce il contratto:

- `test_un_nodo_rinominato_non_sopravvive_sotto_nessuno_dei_due_nomi`
- `test_un_preserve_che_rivendica_il_nome_vecchio_e_rifiutato` → `preserve_nonmaximal`
- `test_due_entita_non_possono_collassare_in_una_sola_preservata`
- `test_una_rinomina_non_e_una_preservazione`

Il terzo merita una nota: many-to-one non è più *illegale*, è **inesprimibile**.
`Pₖ` è un insieme, e un identificatore vi compare al più una volta. Un invariante
che nessuno può violare è più forte di un controllo che lo verifica.

## Due conseguenze registrate, non scoperte dopo

**`identity_violation` resta dichiarata in `Cause` e senza produttori.** Senza
mappatura, `id_{k+1}(x) = id_k(x)` su `Pₖ` è vero per costruzione. La causa non è
stata rimossa: la tabella vive in AD-19, che è spine, e toglierne una è un'altra
decisione di proprietà.

**Un componente i cui terminali cambiano non è più preservato.** Sotto la v2 il
confronto passava per la mappa e `R1 (a,b) → R1 (a2,b)` restava preservata; ora i
terminali si confrontano letteralmente. Nel catalogo corrente lo scenario non si
presenta — i componenti che toccano un nodo assorbito sono esattamente quelli
consumati — ed è coperto da un test che lo dichiara invece di lasciarlo implicito.

## Stato

    P0-A  check_delta                   CLOSED
    P0-B  Equation                      CLOSED
    P0-C  Pₖ / iniettività              CLOSED
    P0-D  contraddizione node_mapping   CLOSED BY ARCHITECTURE

Oracolo: 347 test, copertura 100%, recinti verdi, dominio verde.
