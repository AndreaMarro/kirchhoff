# Spec — Story 1.8: Visual Slice 0 — prima, azione, dopo, e ripercorribile

**Chiave:** `1-8-visual-slice-0-prima-azione-dopo-e-ripercorribile` · **Rischio:** R2
**Autorità:** A-0 · AD-10 · AD-35 · UX-DR12 · UX-DR23 — con AD-21, AD-8 e FR-49 come
vincoli di forma · **Data:** 26/08/2026

## Che cosa la storia chiude

> «percorrere avanti e indietro il passaggio, so that possa fissare il cambiamento
> premendo più volte invece di guardarlo una volta sola.»

La Story 1.7 produceva un passo e due stati visuali; nessuno dei due era un
**oggetto**. Qui il passo diventa una cosa che si può tenere in mano, commutare,
interrogare ed esportare — ed è il primo punto in cui A-0 ha **due disegni** da
confrontare invece di uno solo, cioè il primo in cui la continuità visuale è
misurata e non promessa.

| Aggancio | Dove vive |
|---|---|
| I cinque atti di un passo, in fila | `render/step/compose.py` — `componi` |
| La proiezione, gli stati, i quattro campi, la forma statica | `render/step/schema.py` |
| Le precondizioni dichiarate | `domain/transform/catalog.py` — `PRECONDITIONS`, `preconditions_of` |
| La guardia che le rende esigibili | `domain/transform/engine.py` — `_verifica_le_precondizioni_degli_implementati`, all'import |

## Le tre decisioni di forma, e le autorità che le impongono

**1. `VisualStep` è una proiezione *per riferimento*.** AD-21 v2 dice come si scrive
un tipo che nomina più rappresentazioni senza diventare il quinto contenitore che le
fa collassare: *«porta gli identificatori dei quattro e un'istantanea immutabile di
ciò che serve a renderla, mai i tipi mutabili»*. `VisualStep` porta due `lay_`, un
`patch_` e i **due SVG già emessi**. Nessun `LayoutIR`, nessun `CircuitIR`, nessun
`TransformOverlay`: chi vuole le strutture risolve gli identificatori nei registri.

**2. I fotogrammi sono byte, non una funzione da chiamare.** È ciò che rende
«istantanea, ripetibile all'infinito» una proprietà per costruzione invece di una
misura su un numero di giri: commutare **sceglie fra due stringhe**. Ed è l'unico
modo di soddisfare AD-10 v2 alla lettera — *«`export()` non ri-renderizza»* — perché
la forma statica e l'interattiva escono dallo **stesso oggetto `str`**, non da due
chiamate che si spera coincidano.

**3. Le precondizioni stanno nel Catalogo.** Tre dei quattro campi di UX-DR23 sono
membri del `TransformResult`; le precondizioni no, e senza una dichiarazione
sarebbero l'unico dei quattro **composto al momento della domanda** — cioè la prosa
che UX-DR23 vieta. Stanno in `domain/` e non in `render/` per la ragione di AD-26: le
condizioni sotto cui un passo è lecito sono una proprietà dell'operazione, e un
renderer che le deducesse dai due circuiti dedurrebbe ciò che il dominio ha già
deciso. Sono **trascritte dalle guardie che le impongono**, non riformulate, e ogni
riga dichiarata ha un circuito che la viola in `TestLePrecondizioniSonoFalsificabili`.

## Mappa criterio → test

Tutti in `tests/test_visual_slice.py` salvo dove indicato.

| Criterio (`epics.md`) | Test |
|---|---|
| **Then** la commutazione è **istantanea** (UX-DR12) | `TestLaCommutazione::test_commutare_non_renderizza_nemmeno_una_volta` — conta le chiamate a `render`: due in composizione, **zero** in mille commutazioni |
| … **ripetibile all'infinito** | `test_la_commutazione_e_involutiva_su_entrambi_gli_stati` (forma algebrica) · `test_mille_giri_restituiscono_gli_stessi_identici_byte` (`is`, non `==`) |
| … **senza conferma** | `test_commutare_non_chiede_conferma` — letto sulla firma: nessun parametro di conferma, nessun esito «non commutato» |
| … e senza auto-avanzamento (UX-DR22) | `test_si_apre_su_prima_e_non_avanza_da_solo` |
| **And** toccando `Req` si vede **da cosa deriva** | `TestLIspezioneDelPasso::test_toccando_l_equivalente_si_vede_da_cosa_deriva` · `test_le_risposte_sono_quelle_del_prodotto_e_non_una_seconda_lettura` |
| **And** toccando un nodo preservato si vede **che è lo stesso** | `test_toccando_un_nodo_preservato_si_vede_che_e_lo_stesso` (appartenenza a `Pₖ` **e** stessa posizione nei byte) · verso negativo: `test_cio_che_il_passo_consuma_non_e_lo_stesso` |
| … e il nodo **assorbito** non è muto | `test_il_nodo_assorbito_non_deriva_da_nulla_ma_la_lineage_lo_dice` |
| **And** «Perché posso farlo?» risponde con **quattro** campi | `TestPercheePossoFarlo::test_i_campi_sono_quattro_e_sono_quelli_nominati` |
| … **già calcolati** | `test_i_quattro_campi_sono_letti_dal_prodotto_non_composti` (`is`) · `test_i_quattro_campi_esistevano_prima_della_domanda` · `test_chiedere_due_volte_da_gli_stessi_oggetti` |
| … e **non genera prosa** | gli stessi tre: un campo prodotto al momento della domanda non supera un confronto per identità, qualunque sia il suo contenuto |
| … i quattro, uno per uno | `test_i_terminali_sono_i_due_nodi_su_cui_il_passo_confina` · `test_le_precondizioni_sono_quelle_dichiarate_dal_catalogo` · `test_il_certificato_e_quello_dell_operazione_del_passo` |
| … e le precondizioni sono **esigibili**, non decorative | `TestLePrecondizioniSonoFalsificabili` (8 casi, `Refusal` compreso) · `test_transform.py::TestLePrecondizioniDichiarate` (9 casi, guardie della dichiarazione) |
| **And** lo stesso passo è renderizzabile in **forma statica**, dalla **stessa** sorgente semantica (AD-10) | `TestLaFormaStatica::test_l_export_porta_gli_stessi_identici_byte` (`is`) · `test_esportare_non_renderizza` · `test_i_due_stati_e_l_export_vengono_dalla_stessa_sorgente_semantica` · `test_ogni_fotogramma_dichiara_di_quale_stato_visuale_e` · `test_la_forma_statica_porta_il_patch_del_passo` (CV6) |
| **Autorità A-0** — ciò che è in `preserve` non si muove **fra i due stati** | `TestA0FraIDueStati::test_ogni_nodo_preservato_sta_nello_stesso_punto_nei_due_fotogrammi` · `test_ogni_componente_preservato_e_disegnato_identico_nei_due_fotogrammi` (byte del sottoalbero) · controllo di controllo: `test_cio_che_cambia_invece_non_compare_in_entrambi` |
| **Autorità AD-35** — la composizione intera è deterministica | `TestLaComposizione::test_comporre_due_volte_lo_stesso_passo_da_gli_stessi_byte` |
| **Autorità CV6** — la tripla resta congiungibile | `TestLaComposizione::test_i_due_stati_visuali_restano_risolvibili_dopo_il_passo` |
| **Autorità AD-13** — il Rifiuto si restituisce | `TestLaComposizione::test_un_rifiuto_si_restituisce_e_non_lascia_niente_nei_registri` |

## I quattro mutanti, e che cosa li ha uccisi

Un oracolo che resta verde sotto mutazione non misura niente. Eseguiti il
26/08/2026, ciascuno introdotto nel sorgente e poi ritirato:

| Mutante | Autorità violata | Ucciso da |
|---|---|---|
| `esporta` ricostruisce le due stringhe | AD-10 v2 | `test_l_export_porta_gli_stessi_identici_byte` |
| `giustificazione` ricostruisce i campi (`tuple(list(...))`) | UX-DR23 | `test_i_quattro_campi_sono_letti_dal_prodotto_non_composti` + `test_i_quattro_campi_esistevano_prima_della_domanda` |
| lo stato *dopo* nasce da un layout traslato di 7 | A-0 | i due test di `TestA0FraIDueStati` + `test_toccando_un_nodo_preservato_si_vede_che_e_lo_stesso` |
| `fotogramma` ricompone la stringa a ogni chiamata | UX-DR12 | `test_mille_giri_restituiscono_gli_stessi_identici_byte` |

Il primo tentativo del secondo mutante — `tuple(x)` su una tupla — **non era una
mutazione**: in CPython restituisce lo stesso oggetto, e il test è giustamente
rimasto verde. Registrato perché un mutante che non muta si legge come un oracolo
debole, ed è il contrario.

## Assunzioni dichiarate, da ratificare

- **`InteractionState` non ha un domicilio nell'albero sorgente.** AD-21 elenca fra i
  propri *binds* `ui/`, che non esiste; la review dei confini registra proprio questo
  come il buco del quarto tipo. Il tipo nasce in `render/step` perché lì c'è il passo
  che si commuta. Stessa forma dell'assunzione dichiarata dalla Story 1.3 per il
  `PatchStore` e dalla 1.7 per il layer dell'equazione.
- **`StaticStep` non è l'`Artifact` di AD-10**, e il modulo lo dice: un `Artifact`
  porta la Marcatura di provenienza, che è FR-18/FR-19 ed Epic 4. Prendere il nome
  senza la marcatura dichiarerebbe conforme ciò che non lo è ancora.

## Fuori ambito, dichiarato

Il Piano didattico che sceglie **quale** trasformazione applicare (Epic 2), `publish()`
e i suoi otto controlli (AD-5), la Marcatura di provenienza (FR-18/FR-19), il toggle
come componente di interfaccia (`{motion.instant}`, pollice-raggiungibile: sono token
e layout, e non esiste una superficie), e il recinto 4 di AD-21 su `render/`, che è
la Story 1.5 e sta in backlog.

Ne segue una precisazione sugli oracoli, dovuta alla seconda revisione:
`scripts/check_boundaries.py` cammina il **solo** recinto `domain`. Il suo exit 0 è
evidenza sulle righe toccate in `catalog.py` ed `engine.py`, e su **niente** di
`render/step/`, che fino alla 1.5 non ha alcun controllo di confine: un verde in
tabella non va letto come copertura del codice nuovo.

## Seconda revisione a contesto fresco, 26/08/2026

Undici rilievi, tutti confermati per esecuzione; otto riparati, tre registrati in
`deferred-work.md` (voci 8–10) con la rettifica della §7. Le riparazioni visibili in
questa spec: la guardia d'attribuzione dei fotogrammi su `VisualStep` e `StaticStep`
(lo scambio dei due disegni superava ogni guardia esistente), le guardie di
`Justification` (l'unico dei quattro tipi esportati senza), il `patch_` che
`esporta()` lasciava cadere e ora attraversa l'export (CV6, SM-14), le precondizioni
di `serie` e `parallelo` passate da 5/4 righe a 7/5 (arità e validazione elettrica
di `Cₖ` erano esigite e non dichiarate), la misura dell'unione esatta di `entita`
estesa alle quattro forme di passo componibili, e l'oracolo sul ramo di `componi`
che solleva senza depositare mezzo passo.
