# Spec — Story 1.4: Serializzatore SVG semantico deterministico, su una fixture a soli resistori

**Chiave:** `1-4-serializzatore-svg-semantico-deterministico-su-una-fixture-a` · **Rischio:** R2
**Autorità:** AD-35 · AD-31 · AD-10 · AD-23 · AD-26 · UX-DR25 · FR-15 · FR-46 · **Data:** 26/08/2026

## Che cosa la storia chiude

> «Il circuito che vedo è lo stesso oggetto che il sistema ha verificato.»

Il disegno smette di essere un'illustrazione della prova e ne diventa una parte
(K-0). Concretamente: `render(CircuitIR, LayoutIR) → str` è pura, l'annotazione che
certifica il disegno è **derivata** dalla geometria emessa, e l'alternativa testuale
descrive la **topologia**, non il fatto che esista uno schema.

| Aggancio | Dove vive |
|---|---|
| Geometria annotata e sue guardie | `render/serialize/geometry.py` — `Scena`, coerente per costruzione |
| Byte | `render/serialize/svg.py` — `render`, `alternativa_testuale` |
| Fixture prescritta, `LayoutIR` predefinito | `tests/test_svg_semantico.py` — `CIRCUITO`, `PIAZZAMENTI` |
| Oracolo di formato | `tests/golden/story-1-4-fixture.svg` |

**Due ingressi, non uno.** AD-35 scrive `render(LayoutIR, TransformOverlay,
ArmEncoding) → SVG`. Non è implementabile alla lettera: il `LayoutIR` porta **dove**
ogni cosa sta e nient'altro (AD-21), quindi da solo non sa che `R1` è un resistore, né
quali nodi tocca — e senza quello non esistono né `data-terminal-*` né l'alternativa
testuale, che sono due criteri di accettazione. `TransformOverlay` e `ArmEncoding` non
ci sono: il primo perché questa storia disegna **uno stato visuale fermo**, il secondo
perché AD-26 lo assegna a `experiment/` e avverte che implementarlo dentro
`render/serialize` è la collocazione velenosa. Nel braccio A la mappa è vuota, ed è la
variabile che Gate A manipola: chiuderla qui per inerzia sarebbe una decisione presa
in un modulo.

## Mappa criterio → test

| Criterio (`epics.md`) | Test |
|---|---|
| **Given** lo stesso `LayoutIR` **When** si renderizza due volte **Then** i byte coincidono | `test_svg_semantico.py::test_due_rendering_dello_stesso_layout_danno_gli_stessi_byte` |
| … e non dipendono dall'ordine d'inserimento (AD-35) | `test_l_ordine_di_inserimento_non_cambia_un_byte` · `test_i_fili_escono_nell_ordine_della_chiave_dichiarata` · `test_una_collezione_fuori_dall_ordine_dichiarato_e_rifiutata[simboli|giunzioni|fili]` |
| … né dall'orologio, né da id a runtime, né da casualità | `test_il_disegno_non_dipende_da_quando_e_stato_chiesto` · `test_render_non_ha_orologio_ne_casualita_fra_le_dipendenze` |
| … né dal **formato**, che due rendering uguali fra loro non vedono cambiare | `test_i_byte_emessi_sono_quelli_depositati` (golden, FR-46) |
| **And** ogni componente porta `data-component-id` | `test_ogni_componente_porta_il_proprio_data_component_id` · `test_ogni_componente_porta_anche_il_nome_simbolico_che_il_dominio_gli_da` |
| **And** ogni terminale porta `data-terminal-*` | `test_ogni_morsetto_porta_gli_attributi_data_terminal` · `test_l_ancoraggio_del_morsetto_e_uno_solo_e_sta_nel_gruppo_del_componente` |
| **And** ogni nodo porta `data-node-id` | `test_ogni_nodo_porta_il_proprio_data_node_id` · `test_il_nodo_di_riferimento_e_disegnato_oltre_che_detto` |
| **And** nessun attributo di identità è scritto a mano: è derivato dalla geometria emessa | `test_ogni_filo_tocca_il_morsetto_che_dichiara_di_toccare` (letto sui byte usciti) · le tredici guardie di `Scena` e `Simbolo`, sotto |
| **And** ogni disegno porta l'alternativa testuale della **topologia** (UX-DR25, FR-15) | `test_l_alternativa_descrive_la_topologia_non_il_disegno` · `test_l_alternativa_nomina_anche_i_nodi_poco_frequentati` · `test_la_radice_dichiara_il_titolo_e_la_descrizione_che_possiede` · `test_la_radice_dichiara_la_lingua_del_testo_che_porta` · `test_il_testo_per_lo_studente_e_in_italiano_con_gli_accenti` |
| … e la polarità del generatore, che l'ordine dei terminali **è** | `test_l_alternativa_dice_la_polarita_del_generatore` · `test_a_valore_negativo_la_croce_si_sposta_e_il_numero_resta_quello_del_componente` · `test_un_generatore_spento_non_disegna_una_polarita_che_non_ha` · `test_la_croce_del_generatore_sta_dentro_il_cerchio` |
| **Ambito stretto:** soli resistori più un generatore | `test_un_tipo_senza_simbolo_solleva_invece_di_produrre_un_refusal` · `test_un_tipo_con_ingombro_e_senza_corpo_si_disegnerebbe_come_niente` |
| **Non-goal:** nessun autolayout, `LayoutIR` predefinito | `test_una_posizione_mancante_si_dichiara_invece_di_inventarla` · `test_l_asse_di_un_bipolo_viene_dai_nodi_a_cui_e_attaccato` · `test_un_layout_di_un_altro_circuito_non_si_disegna` |
| Il disegno regge un circuito che il progetto **possiede**, non solo la fixture | `test_un_circuito_dell_insieme_di_riferimento_si_disegna` (`dc-00001` di `reference-set/dev`) |

### Le tre condizioni di AD-31, ciascuna con la sua guardia

AD-31 le enumera; la prima stesura ne applicava due su tre, e la seconda solo entro
lo stesso genere di entità.

| Condizione di AD-31 | Guardia | Test |
|---|---|---|
| «ogni estremo di filo tocchi il terminale che l'annotazione dichiara» | `Scena._verifica_i_fili` | `test_un_filo_che_parte_altrove_dal_morsetto_che_dichiara_e_rifiutato` · `test_un_filo_che_non_arriva_al_nodo_che_dichiara_e_rifiutato` · `test_un_filo_che_nomina_un_nodo_diverso_dal_morsetto_e_il_difetto_di_ad_31` |
| «che due terminali distinti non siano coincidenti» | `_punti_distinti` su **tutti** i punti annotati | `test_due_nodi_coincidenti_rendono_indistinguibile_cio_che_li_tocca` · `test_due_morsetti_coincidenti_rendono_ambigua_la_derivazione` · `test_un_nodo_piazzato_su_un_morsetto_non_e_piu_distinguibile_da_esso` |
| «che nessun filo passi per un terminale che non dichiara di toccare» | `_senza_transiti` | `test_un_filo_che_passa_per_un_morsetto_che_non_dichiara_e_rifiutato` · `test_un_filo_che_passa_per_una_giunzione_che_non_dichiara_e_rifiutato` |

Più le guardie di composizione, che esistono perché `Scena`, `Filo` e `Simbolo` sono
**pubblici**: la Story 1.7 comporrà scene a mano, e ciò che le si impedisce non è di
comporne una, è di comporne una incoerente. `test_due_fili_sullo_stesso_morsetto_…`,
`test_un_simbolo_coi_morsetti_fuori_dal_proprio_asse_…`,
`test_un_simbolo_coi_morsetti_non_simmetrici_…`,
`test_un_simbolo_con_entrambi_i_morsetti_sullo_stesso_nodo_…`,
`test_un_morsetto_senza_filo_sta_in_aria`.

## Nove mutanti verificati

Ognuno applicato in copia-ombra, con `tests/test_svg_semantico.py` eseguito sopra.

| Mutante | Esito | Chi lo prende |
|---|---|---|
| `sorted(components)` e `sorted(nodes)` → ordine d'inserimento in un dizionario — **l'oracolo che la storia prescrive** | rosso | `ValueError: simboli fuori dall'ordine dichiarato: ['V1', 'R1', 'R2']`, sollevato costruendo la `Scena`; con esso `test_l_ordine_di_inserimento_non_cambia_un_byte` |
| `_senza_transiti` disattivata | rosso | i due test sui transiti |
| nodi e morsetti confrontati solo fra simili (com'era) | rosso | i due test sulle coincidenze miste |
| filo duplicato ammesso | rosso | `test_due_fili_sullo_stesso_morsetto_…` |
| le scritte non entrano nella `viewBox` (com'era) | rosso | `test_nessuna_scritta_esce_dalla_viewbox` + golden |
| `_verifica_l_ordine` disattivata | rosso | i tre parametri di `test_una_collezione_fuori_dall_ordine_…` |
| croce del generatore a 3/2 del raggio, cioè fuori dal cerchio (com'era) | rosso | `test_la_croce_del_generatore_sta_dentro_il_cerchio` + golden |
| `_verifica_l_asse` disattivata | rosso | i due test sull'asse del simbolo |
| token agganciati con `var()` in un `<style>` (com'era) | rosso | `test_il_disegno_non_dipende_da_un_motore_css_per_esistere` + golden |

**Il difetto che nessun test avrebbe visto, e che ha trovato il secondo renderer.**
I token di `DESIGN.md` erano stati agganciati con un blocco `<style>` e
`stroke:var(--kf-ink-primary,currentColor)` sulle classi, con gli attributi di
presenza come riscatto. Rasterizzata con **`cairosvg`** — un renderer indipendente da
quello di sistema — la fixture usciva **senza un solo tratto**: niente fili, niente
corpi, niente massa, soltanto i pallini e le etichette. Quel renderer applica la regola
di classe e non conosce `var()`, quindi sostituisce l'attributo di presenza con una
tinta non valida invece di scartare la dichiarazione. AD-10 fa di questo SVG la sorgente
di **ogni** altro formato e **D4 — quale stack di rendering, web contro PDF — è
aperta**: presupporre un motore CSS moderno nel percorso di export è scommettere su una
decisione che nessuno ha preso, e un circuito esportato senza fili è il modo peggiore in
cui questo prodotto possa fallire. Il `<style>` è stato ritirato: i valori dei token
viaggiano come attributi di presenza, le classi restano l'aggancio — in CSS qualunque
regola d'autore batte un attributo di presenza, quindi un braccio non perde nulla. Il
difetto è ora un invariante permanente (FR-46):
`test_il_disegno_non_dipende_da_un_motore_css_per_esistere`, più il nono mutante.
Le due rasterizzazioni finali, `qlmanage` e `cairosvg`, disegnano lo stesso circuito.

**Un mutante che era verde, e la riga che lo rendeva tale.** `tuple(sorted(fili,
key=…))` → `tuple(fili)` lasciava verdi tutti e 52 i test della stesura precedente: i
fili nascono già ordinati dentro il ciclo sui componenti ordinati, quindi
quell'ordinamento non poteva cadere. Era codice morto che sembrava una garanzia. È
stato tolto, e il contratto è passato dove **può** cadere — `Scena._verifica_l_ordine`,
che lo impone su tutte e tre le collezioni ed è il primo mutante della tabella.

## Aperto, e non deciso qui

- **`reroute_scope`, la domanda di accettazione differita a questa storia.**
  `deferred-work.md` la pone: *«Qual è l'unità semantica contenuta in `reroute_scope`:
  componenti, nodi, branch/edge renderizzabili, o altro?»*, con l'istruzione di
  fermarsi con `ARCHITECTURE_CONFLICT` **se arrivare a 1.4 la richiedesse**. Non la
  richiede, ed è un fatto misurabile, non un'opinione: questa storia non consuma
  `LayoutPatch` — non c'è `applica`, che è la Story 1.7 — e non reinstrada nulla di
  preesistente. `_percorso` calcola ogni filo da zero a ogni `render`, i fili non sono
  entità (`EntityKind` resta `component | node`), non hanno posizione nel `LayoutIR` e
  non compaiono in nessun `preserve`. La decisione resta quindi **aperta e non chiusa
  di fatto**: va portata alla storia che applica una patch, dove FR-38 la usa come
  vincolo normativo. Nessun `ARCHITECTURE_CONFLICT` è stato aperto, e la ragione è
  questa.
- **Quale nome legge lo studente: `Component.id` o `Component.symbolic`.** In
  `dc-00001` valgono `E1` ed `E_1`, e nessuna autorità dice quale dei due sia quello
  dell'esercizio. Il disegno mostra l'`id`, come faceva; l'altro esce
  in `data-component-symbolic` perché perderlo renderebbe la domanda indecidibile anche
  a chi la risolverà. La scelta di **cosa disegnare** non è presa qui.
- **La tinta dei token non è emessa.** `identity-tag` vuole `{colors.ink-secondary}`,
  che in `DESIGN.md` ha due valori — `#A6ACB8` e `#565C66` — perché la modalità chiara è
  «pari grado, non secondaria». Un file che viaggia da solo non sa quale palette sia
  attiva: `currentColor` lo lascia decidere alla superficie, e la classe resta
  l'aggancio per chi vuole fissarla. Se un giorno l'export debba portare la tinta
  incisa, è una decisione che segue D4.
- **`DESIGN.md` non ha un token per il tratto dello schema.** I quattro che dichiarano
  uno spessore — `provenance-anchor`, `subgraph-highlight`, `boundary-anchor`,
  `unchanged-marker` — sono overlay. `TRATTO = 3/2` è dichiarato nel modulo e non
  inventato altrove, ma il token manca e va aggiunto da chi possiede `DESIGN.md`.
- **La larghezza del testo è un maggiorante, non una misura.** `_LARGHEZZA_DEL_GLIFO`
  vale un quadratone per glifo: nessun glifo latino lo supera, quindi la `viewBox` non
  taglia, ma su etichette lunghe lascia bianco in più. Misurare davvero il font
  richiede metriche che l'export potrebbe non avere, e quale stack renda davvero
  questo SVG è la decisione aperta **D4** (§27.4 del piano master), che tocca Gate A.
- **Il pareggio d'asse.** `_asse` sceglie l'orizzontale quando `|dx| = |dy|`: è una
  regola dichiarata e arbitraria, e un autolayout la sostituirà.
- **`placeholder_unbound`.** AD-19 lo assegna a `render/serialize`, che ora esiste e
  non ha alcun produttore di `Refusal`. Nulla in questa storia lo richiede — non c'è
  `ProofGraph` in gioco — e la voce di `deferred-work.md` che lo cita lo lega alla
  Story 2.5, che è in backlog.
- **L'attraversamento di un corpo.** `_senza_transiti` applica AD-31, che parla di
  terminali. Un filo che attraversa il *rettangolo* di un altro componente senza
  toccarne i morsetti non è vietato da nessuna autorità — AD-23 governa l'occlusione
  fra layer, e i layer che la producono (5 e 6) questa storia non li emette — ed
  evitarlo è materia di autolayout, che è non-goal.
