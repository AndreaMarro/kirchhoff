---
title: "Storia 1.1 — L'identità preservata dev'essere giustificata, non dichiarata"
type: 'feature'
created: '2026-08-25'
baseline_commit: 'e810907'
review_loop_iteration: 1
context: ['AD-22 em.', 'AD-19', 'CV1', 'CV3', 'CV5', 'E-62', 'E-65', 'K-3']
risk_class: 'R2'
status: 'in-review'
---

## Intent

**Problem:** AD-22 chiudeva una direzione sola — *«un controllore strutturale confronta `Cₖ` e
`Cₖ₊₁` per identità e rifiuta se un'entità presente in entrambi compare in `create`»* — mentre
l'altra restava aperta. Con il discriminante v2.1, una trasformazione che battezza `R1` la nuova
resistenza equivalente non ottiene più `R1 ∈ Pₖ`, ma il passo resta **rappresentabile** come
«rimozione più creazione» con lineage nel `Delta`: chi legge `R1` in `Cₖ₊₁` legge il nome di una
cosa che non c'è più, e nessuna riga glielo dice. `Pₖ` è l'ingresso di VCER, della codifica di
braccio e di A-0, quindi un `Pₖ` falsificabile rende il verdetto di Gate A **leggibile e falso** —
CV1, *«un bug che si legge come dato»*.

**Approach:** due lati dello stesso contratto, e la storia ne consegna entrambi.

1. **Il rifiuto.** `check_transform` emette un `Refusal` quando un identificatore compare in `Cₖ` e
   in `Cₖ₊₁` senza nominare la stessa entità. Non dipende da nulla che il produttore dichiari: si
   legge nei due circuiti e nell'operazione, cioè in ciò che il misurato non controlla.
2. **La giustificazione.** CV3 stabilisce che una preservata **può** cambiare proprietà entro la
   semantica della trasformazione. Quella licenza la concede il **Catalogo**, per operazione, e una
   licenza esercitata in silenzio non è distinguibile da un'identità riusata: `IdentityAttestation`
   la rende leggibile, e `check_certificate` la verifica contro i due circuiti.

Il secondo lato è ciò che la prima consegna aveva lasciato aperto: le attestazioni erano **prodotte
e mai verificate**. Un `TransformResult` assemblato da fuori accettava `attestations=()` con una
licenza esercitata, un'attestazione sull'attributo sbagliato e una su attributi mai cambiati — tutte
e tre misurate. È E-65 nel campo che esiste per chiudere E-65.

## Boundaries & Constraints

**Always:**

- Il discriminante lo dichiara il **Catalogo** (`_MUTABILI`), mai la `Transform` misurata. Chi è
  misurato non definisce il proprio riferimento.
- Un solo predicato d'identità nel pacchetto: `check._divergenze`. `Pₖ`, le attestazioni e la
  diagnosi sono tre **letture** dello stesso confronto (E-62). Predicato, non corsa: gira sei volte
  per una `transform()`, ed è la stessa funzione, non lo stesso risultato riusato.
- Ogni invariante ha una guardia a runtime **e** un test che l'ha vista sollevare (CV5).
- La diagnosi nomina l'entità e la trasformazione (AD-19) e si rilegge come Domanda mirata (K-3).

**Never:**

- `preserved == immutable`. È il non-goal esplicito della storia: CV3 tiene preservato e boundary
  coesistenti.
- Aggiungere una causa a `Cause`: l'enumerazione di AD-19 è chiusa e vive nello spine. Ciò che non
  ha una causa legale resta una violazione interna (`CertificateViolation`) o un guasto
  (`CertificatoIncoerente`), mai un `Refusal` travestito.
- Far comparire «coerenza del Certificate» in `CONTROLLI`: un certificato che attestasse di aver
  verificato le proprie attestazioni certificherebbe se stesso asserendolo.

## I/O & Edge-Case Matrix

| Scenario | Esito | Soggetto |
|---|---|---|
| `{R1 10Ω, R2 20Ω} → R1 6⅔Ω` (nome riusato dall'equivalente) | `Refusal(identity_violation)` | `component:R1` |
| stesso caso con `parallelo` che licenzia `value` | passa, `Certificate` porta `R1 (value)` | — |
| stesso caso con patch **irreprensibile** | `Refusal(identity_violation)` comunque | `component:R1` |
| rinomina `b→z` che sposta i terminali di componenti sopravvissuti | `Refusal(identity_violation)` | `component:R1` |
| rinomina di un nodo **non toccato** da nessun componente | passa | — |
| stessa rinomina, con la patch che rivendica `b` fra le preservate | `Refusal(preserve_nonmaximal)` | `serie` |
| due identificatori divergenti (`R1` e `RL`) | `Refusal(identity_violation)`, diagnosi che li nomina **entrambi** | `component:R1` |
| `boundary=None` e identità compromessa insieme | `Refusal(empty_boundary)` — l'ordine è fisso | `serie` |
| motore con `_nuovo_id` difettoso (`serie` e `parallelo`) | `Refusal(identity_violation)` | `component:R1` |
| nodo riusato con incidenza diversa, stesso nome | **passa** — limite dichiarato, vedi *Aperto* | — |
| `Certificate` che tace una licenza esercitata | `CertificateViolation(licenza_taciuta)` | `component:R1` |
| `Certificate` che attesta ciò che non è cambiato | `CertificateViolation(attestazione_infondata)` | `component:RL` |
| `Certificate` che attesta l'attributo sbagliato | `CertificateViolation(attestazione_discorde)` | `component:R1` |
| motore che emette un attestato falso | `CertificatoIncoerente` (guasto, non Rifiuto) | — |
| `IdentityAttestation(node:a, ("value",))` | `ValueError` | — |
| `Certificate("serie", …, R1 (value))` senza licenza | `ValueError` | — |
| `_MUTABILI["serie"] = {"provenance"}` | `RuntimeError` all'invariante | — |

## Code Map

- `src/kirchhoff/domain/transform/catalog.py` — `_MUTABILI`, `mutable_attributes`,
  `_verifica_dichiarazione` (invariante di import, ora su chiavi **e** valori).
- `src/kirchhoff/domain/transform/check.py` — `_divergenze` (predicato unico), `_perche_diversa`,
  `preserve_set`, `identity_attestations`, `check_certificate` **(nuovo)**, il ramo
  `identity_violation` di `check_transform`.
- `src/kirchhoff/domain/transform/result.py` — `IdentityAttestation` (guardia sul nodo),
  `Certificate` (guardia sulla licenza del Catalogo), `TransformResult` (attestata ⊆ preservate).
- `src/kirchhoff/domain/transform/engine.py` — `CertificatoIncoerente` **(nuovo)**, il cablaggio in
  `_prodotto`, la voce `identita' dei sopravvissuti` in `CONTROLLI`.
- `tests/test_transform.py` — 440 test nella suite; le classi della storia sono
  `TestUnIdentificatoreRiusatoERifiutato`, `TestLaPreservazioneNonBanaleEAttestata`,
  `TestUnEquivalenteHaIdentitaNuova`, `TestLeGuardieDellAttestazione`,
  `TestDiscriminanteDiIdentita`.

## Mappa criterio di accettazione → test

**AC1** — *Given una trasformazione che produce un'entità nuova riusando l'identificatore di una
consumata · When il controllo gira · Then viene rifiutata · And il rifiuto nomina l'entità e la
trasformazione*

| Criterio | Test |
|---|---|
| viene rifiutata | `TestUnIdentificatoreRiusatoERifiutato::test_il_caso_fondativo_r2a_non_attraversa_piu_il_controllore` |
| il rifiuto nomina l'**entità** | `::test_il_rifiuto_nomina_l_entita` (`subject`, `subject_kind`, e il nome nella diagnosi) |
| il rifiuto nomina la **trasformazione** | `::test_il_rifiuto_nomina_la_trasformazione` |
| la diagnosi si rilegge come Domanda mirata (K-3) | `::test_il_rifiuto_dice_quale_attributo_rende_l_entita_diversa` |
| il rifiuto **non dipende** da ciò che il produttore dichiara | `::test_la_patch_irreprensibile_non_salva_il_passo` |
| l'identità precede la massimalità (`Pₖ` compromesso non è un metro) | `::test_l_identita_viene_prima_della_massimalita` |
| l'ordine dei tre controlli è fisso | `::test_il_boundary_vuoto_resta_il_difetto_piu_grosso` |
| **nessuna falsa accusa**: il passo onesto passa | `::test_un_passo_onesto_non_e_accusato`, `::test_un_nodo_sopravvissuto_non_e_mai_accusato_di_identita_riusata` |
| la diagnosi non afferma una causa che il controllo non conosce | `::test_la_diagnosi_non_afferma_una_causa_che_il_controllo_non_conosce` |
| la diagnosi nomina **tutti** gli identificatori divergenti | `::test_la_diagnosi_nomina_tutti_gli_identificatori_divergenti` |
| raggiungibile dal **motore**, non solo da `check_transform` a mano | `::test_un_equivalente_che_riusa_il_nome_e_rifiutato_dal_motore` (2 parametri) |
| il limite dichiarato sui nodi, pinnato | `::test_per_i_nodi_il_controllo_e_vuoto_per_costruzione` |
| `rinomina != preservazione`, dove l'identità non scatta prima | `test_una_rinomina_dichiarata_preservata_e_non_massimale`, `test_un_preserve_che_rivendica_il_nome_vecchio_e_rifiutato` |

**AC2** — *Given un'entità realmente preservata che cambia una proprietà ammessa da quella
trasformazione · When il controllo gira · Then passa · And il `Certificate` porta l'attestazione
dell'identità per il caso non banale*

| Criterio | Test |
|---|---|
| con la licenza la stessa coppia **passa** | `TestLaPreservazioneNonBanaleEAttestata::test_con_la_licenza_la_stessa_coppia_passa` |
| l'attestazione nomina l'entità e ciò che è cambiato | `::test_l_attestazione_nomina_l_entita_e_cio_che_e_cambiato` |
| il caso **banale** non produce attestazioni | `::test_il_caso_banale_non_produce_attestazioni` |
| senza licenza non esiste un grado intermedio | `::test_senza_licenza_non_si_attesta_nulla` |
| la licenza vale per l'operazione che la dichiara | `::test_l_operazione_sceglie_la_licenza` |
| il `Certificate` **porta** l'attestazione | `::test_il_certificato_porta_l_attestazione` |
| il motore interroga il predicato coi due circuiti e l'operazione | `::test_il_motore_interroga_il_predicato_coi_due_circuiti_e_l_operazione` |
| sul percorso interno le attestazioni sono vuote, e vuote sono un'affermazione | `::test_sul_percorso_interno_le_attestazioni_sono_vuote` |
| **una licenza taciuta è contestata** | `::test_un_certificato_che_tace_una_licenza_esercitata_e_contestato` |
| **un'attestazione infondata è contestata** | `::test_un_certificato_che_attesta_cio_che_non_e_cambiato_e_contestato` |
| **un'attestazione discorde è contestata** | `::test_un_certificato_che_attesta_l_attributo_sbagliato_e_contestato` |
| nessuna falsa accusa sul certificato giusto | `::test_il_certificato_giusto_non_e_contestato`, `::test_un_certificato_senza_licenze_da_esercitare_non_e_contestato` |
| un attestato falso emesso dal motore è un **guasto**, non un Rifiuto | `::test_un_certificato_che_mente_sull_identita_e_un_guasto_non_un_rifiuto` |

**AC3** — *Given una derivazione `{R1, R2} → {Req}` · When il controllo gira · Then `Req` ha
identità nuova e lineage nel `Delta`, e **non** compare in `Pₖ`*

| Criterio | Test |
|---|---|
| `Req` ha identità **nuova** | `TestUnEquivalenteHaIdentitaNuova::test_l_equivalente_non_riusa_l_identificatore_di_una_consumata` (2 parametri) |
| `Req` **non** compare in `Pₖ` | `::test_l_equivalente_non_compare_in_pk` (2 parametri) |
| `Req` porta la propria **lineage**, interrogabile nelle due direzioni | `::test_l_equivalente_porta_la_propria_lineage` |

**CV5** — *ogni invariante ha una guardia a runtime e un test che l'ha vista sollevare*

| Guardia | Test |
|---|---|
| attestato senza attributi cambiati | `TestLeGuardieDellAttestazione::test_un_attestato_senza_attributi_cambiati_non_esiste` |
| attributo attestato due volte | `::test_un_attestato_non_nomina_un_attributo_ripetuto` |
| attributo che non compone l'identità | `::test_un_attestato_non_nomina_cio_che_non_compone_l_identita` |
| attestato su una stringa invece che su un `EntityRef` | `::test_un_attestato_nomina_un_entita_non_una_stringa` |
| **attestato su un nodo** | `::test_un_attestato_non_nomina_un_nodo` |
| **licenza che il Catalogo non concede** | `::test_un_certificato_non_attesta_una_licenza_che_il_catalogo_non_concede` |
| stessa entità attestata due volte | `::test_la_stessa_entita_non_si_attesta_due_volte` |
| attestata che il prodotto non conserva | `::test_non_si_attesta_l_identita_di_cio_che_il_prodotto_non_conserva` |
| ordine canonico (attributi, attestazioni) | `::test_gli_attributi_sono_in_ordine_canonico`, `::test_le_attestazioni_di_un_certificato_sono_in_ordine_canonico` |
| **dichiarazione senza una voce del Catalogo** | `TestDiscriminanteDiIdentita::test_una_dichiarazione_senza_una_voce_del_catalogo_e_rifiutata` |
| **attributo mutabile che non compone l'identità** | `::test_non_si_dichiara_mutabile_cio_che_non_compone_l_identita` |
| la dichiarazione reale supera il proprio invariante | `::test_la_dichiarazione_reale_supera_il_proprio_invariante` |
| `type` licenziabile e non licenziato | `::test_il_tipo_resta_licenziabile_e_non_e_licenziato_da_nessuno` |

## Verification

```
ops/loop/verifica.sh
  → exit 0
  → {"copertura": 100.0, "dominio": true, "recinti": true,
     "test_falliti": 0, "test_passati": 440, "verde": true}
```

**Oracolo della storia** — il test negativo va visto rosso rimuovendo la guardia, e il rosso dev'essere
un fallimento di asserzione. Evidenza in `## Oracolo` del rapporto di iterazione: mutazione
`if riusati:` → `if False:` in `check.py`, ripristino verificato per checksum.

## Aperto, dichiarato

Tutte e quattro le voci sono in `deferred-work.md`, che è il canale durevole.

- **La semantica emessa di `identity_violation` non è quella di AD-19**, e la forma che AD-22 v2.1
  dichiara rappresentabile è ora rifiutata. Due clausole owner-locked contraddette dal codice:
  è una **decisione da portare al proprietario**, non una da prendere qui.
- **Per i nodi il controllo d'identità è vuoto per costruzione.** Un nodo è il proprio nome; la sua
  incidenza non è un suo campo. Il limite è dichiarato nel docstring di `_divergenze` e pinnato da
  un test che diventerebbe rosso se il contratto cambiasse.
- **`type` resta licenziabile**, deliberatamente: AD-22 v2.1 porta come esempio illustrativo un caso
  che potrebbe averne bisogno. Esprimibile e non esercitata.
- **`reroute_scope`** resta differito alla Story 1.4, invariato da questa storia.
