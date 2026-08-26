# Spec — Story 1.3: Un `LayoutIR` recuperabile per ogni stato visuale

**Chiave:** `1-3-un-layoutir-recuperabile-per-ogni-stato-visuale` · **Rischio:** R2
**Difetto d'origine:** CV6 · **Data:** 26/08/2026

## Il difetto, e cosa lo chiude

CV6 elenca tre agganci mancanti che rendono VCER incalcolabile: la **ritenzione**
del `LayoutIR` (AD-8 nominava lo scrittore e taceva su quanto vive), gli
**identificatori** (`lay_` e `patch_` non erano nelle convenzioni), e la **relazione**
fra nodo della derivazione e layout. Sotto U2 — *«applicare un `LayoutPatch` aggiorna
il layout in luogo»* — `p_k` non esiste più nel momento in cui servirebbe misurarlo.

| Aggancio | Dove vive ora |
|---|---|
| Identificatori | `domain/identity.py` — sei prefissi derivati da `IdentityKind`, un ULID per tutti |
| Ritenzione `LayoutIR` | `render/layout/store.py` — `LayoutStore`, append-only |
| Ritenzione `LayoutPatch` | `render/layout/store.py` — `PatchStore`, che conia il `patch_` al deposito |
| Relazione nodo ↔ layout | `domain/proof/graph.py` — scritta una volta sola, sul nodo |
| Giunzione della tripla | `render/layout/continuity.py` — `operandi_di_vcer`, cinque condizioni |

**Il proprietario del riferimento è stato cercato, non presupposto.** La risposta era
già scritta in AD-8 em. del 24 agosto: *«Il proprietario del riferimento è **il nodo**,
non la sessione»*. `ProofSession` non è toccata — è la Story 6.1.

## Decisione rivista in review: chi conia il `patch_`

La prima stesura dava alla `LayoutPatch` un identificatore derivato da un'impronta del
contenuto, coniato dentro `transform`. Tre conseguenze l'hanno fatta ritirare:

1. le `Consistency Conventions` dicono «ULID», e un'impronta non lo è — AC2 non era
   soddisfatto alla lettera, e la deviazione era scritta nel materiale, non nell'autorità;
2. un identificatore di contenuto **non identifica un passo**: SM-14 conta i
   `LayoutPatch` che violano la continuità, e un'evidenza «`patch_X` viola VCER» non
   saprebbe a quale arco riferirsi;
3. la patch non aveva ritenzione, quindi `preserve` — cioè il dominio su cui
   `p_{k+1}(x) ≈ p_k(x)` si valuta — non era recuperabile: la tripla di CV6 era
   congiungibile su un lato solo.

**Regola adottata: conia chi ritiene, non chi produce.** `transform` resta pura (AD-2)
e non conia; il `patch_` nasce in `PatchStore.deposita` con l'istante iniettato, come
il `lay_` nasce in `LayoutIR.nuovo`. Le due entità non hanno più due regole diverse.

## Mappa criterio → test

| Criterio (`epics.md`) | Test |
|---|---|
| **Then** `LayoutIR_k` è ancora recuperabile dopo `k+1` | `test_continuita_visuale.py::test_lo_stato_visuale_del_passo_k_sopravvive_al_passo_successivo` |
| **Then** … **e non è stato sovrascritto** (identità e insieme di entità) | `test_continuita_visuale.py::test_i_tre_stati_visuali_sono_tre_e_nessuno_ha_sovrascritto_gli_altri` · `test_un_secondo_deposito_sullo_stesso_layout_e_rifiutato` |
| **Then** … **e non è stato sovrascritto** (*piazzamenti*) | `test_continuita_visuale.py::test_i_piazzamenti_del_passo_k_sono_quelli_di_prima_non_solo_le_entita` · `test_layout.py::test_i_piazzamenti_di_lay_k_non_cambiano_quando_si_deposita_lay_successivo` · `test_lo_stato_visuale_recuperato_regge_a_una_catena_di_depositi` |
| **And** `LayoutIR` ha un identificatore proprio secondo le convenzioni | `test_continuita_visuale.py::test_ogni_stato_visuale_ha_un_identificatore_lay` · `test_identity.py::test_conia_da_la_risposta_nota_su_ogni_vettore` |
| **And** `LayoutPatch` ha un identificatore proprio secondo le convenzioni | `test_continuita_visuale.py::test_ogni_patch_del_passo_ha_un_identificatore_patch` · `test_layout.py::test_il_patch_e_un_ulid_col_prefisso_delle_convenzioni` |
| **And** … **ULID**, quindi ordinabile nel tempo per entrambi | `test_continuita_visuale.py::test_i_due_identificatori_sono_ulid_e_ordinano_per_istante` |
| **And** un `patch_` nomina un passo, non un contenuto | `test_layout.py::test_un_patch_identifica_un_passo_e_non_un_contenuto` · `test_proof.py::test_due_archi_non_possono_portare_lo_stesso_patch` |
| **And** relazione nodo → layout | `test_proof.py::test_*layout_di*` · `test_continuita_visuale.py::test_da_ogni_nodo_si_arriva_al_suo_layout_e_viceversa` |
| **And** relazione layout → nodo | `test_proof.py::test_*nodo_di*` · `test_continuita_visuale.py::test_dal_layout_intermedio_si_risale_al_passo_che_lo_ha_prodotto` |
| **So that** VCER è calcolabile (tripla congiungibile) | `test_continuita_visuale.py::test_la_tripla_di_cv6_e_congiungibile` · `test_gli_operandi_di_vcer_si_risolvono_tutti_e_tre` |
| **So that** … gli operandi esistono davvero (5 condizioni) | `test_giunzione_vcer.py` — un test per condizione, più `test_una_tripla_coerente_si_congiunge` |
| Il nodo `k` denota `Cₖ` e non un altro | `test_continuita_visuale.py::test_ogni_nodo_denota_il_proprio_circuito_e_non_un_altro` |
| **Non-goal:** non si decide il renderer | `test_giunzione_vcer.py::test_la_giunzione_non_giudica_la_continuita` · contratto di `applica` in `render/layout/__init__.py` |

## Mutante verificato

Un `LayoutStore.deposita` che riscrive le coordinate dei layout già depositati
(stesso `lay_`, stesse entità, `x+1`) — il caso di CV6 in cui `p_k` esiste ma non è
più quello di prima — è stato applicato e la suite è **rossa**. Prima delle tre righe
«piazzamenti» della tabella sopravviveva.

## Aperto, e non deciso qui

- **AD-8 non ha una riga per la `LayoutPatch` persistita.** Il `PatchStore` sta in
  `render/layout` perché lì stanno gli altri due operandi della stessa tripla. È
  un'assunzione dichiarata nel modulo, da ratificare da chi possiede lo spine.
- **L'ERD non conosce `LayoutIR` né `LayoutPatch`** — è la quarta delle quattro righe
  di CV6, e `implementation-readiness.md:137` tiene 1.3 a «⛔ non pronta» finché manca.
- **Nessun `EntropyPort`** nell'elenco dei port: il requisito «dieci byte nuovi a ogni
  conio» vive in un docstring, non in un contratto.
- **La chiave della storia non è registrata in `sprint-status.yaml`, e non può esserlo.**
  `tests/test_chiave_canonica.py::test_la_derivazione_coincide_con_quella_di_bmad`
  confronta le chiavi derivate da `epics.md` con le `new_entries` che BMAD produce
  leggendo quel file: una chiave registrata sparisce da `new_entries` e le due liste
  divergono. Verificato eseguendo — aggiungere la sola chiave di 1.3 rende quel test
  rosso. Il file porta ora un commento che lo dice; la correzione tocca l'armatura di
  Epic 0 e non si fa dal loop.
- **Il produttore degli `ir_` degli stati intermedi** non esiste: `ingest` vede solo
  C₀. La regola adottata qui — conia chi ritiene — vale anche per loro, ma il registro
  dei `CircuitIR` è fuori dall'ambito di questa storia.
