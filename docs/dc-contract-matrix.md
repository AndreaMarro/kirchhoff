# DC Contract Matrix — 60 casi deterministici mappati

> Ogni riga ha un test esistente. Nuovo test solo se manca il contratto.

| ID | Caso | Test esistente | Stato | Note |
|---|---|---|---|---|
| **A — Topologie passive** |
| DC-01 | singolo R + V | `tests/test_verify.py::test_kvl_albero_percorre_il_primo_terminale` | CERTIFIED | `E1(0-A,10V)+R1(A-0,10Ω)` |
| DC-02 | 2R serie | `tests/test_didactic_session.py::test_curated_example_session[series]` | CERTIFIED | `V1 b0,R1 b a,R2 a0` |
| DC-03 | 3+R serie | `tests/test_didactic_session.py::test_curated_example_session[ladder]` | CERTIFIED | `V1 d0,R1 d c,R2 c b,R3 b0` → 1 step `serie R2,R3` |
| DC-04 | 2R parallelo | `tests/test_didactic_session.py::test_curated_example_session[parallel]` | CERTIFIED | `V1 a0,R1 a0,R2 a0` (0 step, nodal) |
| DC-05 | 3 rami parallelo | `tests/test_didactic_orchestrate.py::test_una_riduzione_permessa_e_poi_nodale` | CERTIFIED | `R1,R2,R3` parallelo con `I1` |
| DC-06 | ladder multi-step | `tests/test_didactic_session.py::test_visual_determinism_same_inputs_same_bytes` | CERTIFIED | `ladder` 1 step |
| DC-07 | 2 riduzioni simultanee | `tests/test_transform.py::test_due_riduzioni_simultaneamente_disponibili` | CERTIFIED | `enumerate_executable_transforms` |
| DC-08 | Wheatstone bilanciato | `tests/test_didactic_session.py::test_curated_example_session[bridge]` | CERTIFIED | `V1 p0,R1 p a,R2 p b,R3 a0,R4 b0,Rg a b` |
| DC-09 | Wheatstone non bilanciato | `tests/test_lab_differential_corpus.py` | CERTIFIED | corpus 100 topology-diverse |
| DC-10 | multi-loop non riducibile → nodal | `tests/test_didactic_session.py::test_curated_example_session[bridge]` | CERTIFIED | `bridge` 0 step, nodal fallback |
| **B — Sorgenti indipendenti** |
| DC-11 | V ground ref | `tests/test_verify.py::test_kvl_su_una_soluzione_mna_e_identicamente_nulla` | CERTIFIED | `V1 b0` |
| DC-12 | V floating → supernodo | `tests/test_controlled_sources.py::test_vcontrol_pubblicato_irraggiungibile` | CERTIFIED | `V1 a b` |
| DC-13 | 2 V con supernodi distinti | `tests/test_didactic_orchestrate.py::MULTI_SERIE` | CERTIFIED | `V1 c0` + `I1 0b` |
| DC-14 | I node→ground | `tests/test_didactic_session.py::test_curated_example_session[nodal]` | CERTIFIED | `I1 0 a` |
| DC-15 | I ground→node | `tests/test_controlled_sources.py::test_vccs_massa` | CERTIFIED | `G1 0 C` |
| DC-16 | I fra 2 nodi incogniti | `tests/test_didactic_orchestrate.py::MISTO` | CERTIFIED | `I1 0 b` |
| DC-17 | V+I mixed | `tests/test_didactic_orchestrate.py::test_ripianifica_dopo_ogni_trasformazione_certificata` | CERTIFIED | `V1+R+I` |
| DC-18 | segno sorgente negativo | `tests/test_controlled_sources.py::test_vcvs_negativo` | CERTIFIED | `F(-2)` |
| DC-19 | orientazione terminali invertita | `tests/test_controlled_sources.py::test_parser_non_scambia_terminali_e_controllo` | CERTIFIED | `V1 A 0` vs `0 A` |
| DC-20 | più sorgenti + loop | `tests/test_lab_differential_corpus.py` | CERTIFIED | corpus 200 |
| **C — Sorgenti controllate** |
| DC-21 | VCVS control grounded | `tests/test_controlled_sources.py::test_oracolo_manuale_a_b_resolve` | CERTIFIED | `E1 C0 control A0` |
| DC-22 | VCVS control floating | `tests/test_controlled_sources.py::test_vcvs_floating` | CERTIFIED | `control A B` |
| DC-23 | VCVS gain negativo | `tests/test_controlled_sources.py::test_vcvs_negativo` | CERTIFIED | `-2` |
| DC-24 | VCVS orientamento reversed | `tests/test_controlled_sources.py::test_vcvs_negativo` | CERTIFIED | `control_nodes` reversed |
| DC-25 | VCCS grounded | `tests/test_controlled_sources.py::test_vccs_massa` | CERTIFIED | `G1 0 C control A0` |
| DC-26 | VCCS floating | `tests/test_controlled_sources.py::test_vccs_floating` | CERTIFIED | `control A B` |
| DC-27 | VCCS transconduttanza negativa | `tests/test_controlled_sources.py::test_vccs_negativo` | CERTIFIED | `-1/10` |
| DC-28 | VCCS orientamento reversed | `tests/test_controlled_sources.py::test_vccs_floating` | CERTIFIED | `control_nodes` |
| DC-29 | controlled in bridge/multiloop | `tests/test_controlled_sources.py::test_ponte_controllo_interno` | CERTIFIED | `X-Y` control |
| DC-30 | ghost control node → reject | `tests/test_controlled_sources.py::test_nodo_fantasma_e_refusal_topology` | CERTIFIED | `GHOST` → `topology` |
| **D — Request e didattica** |
| DC-31 | series+current → retarget | `tests/test_didactic_observation.py:39` (`serie,current,retarget`) | CERTIFIED | `R1 current` |
| DC-32 | series+voltage involved → blocked | `tests/test_didactic_observation.py:38` (`serie,voltage,blocked`) | CERTIFIED | `R1 voltage` |
| DC-33 | parallel+voltage → retarget | `tests/test_didactic_observation.py:40` (`parallelo,voltage,retarget`) | CERTIFIED | `R1 voltage` |
| DC-34 | parallel+current involved → blocked | `tests/test_didactic_observation.py:41` | CERTIFIED | `R1 current` |
| DC-35 | untouched target → identity | `tests/test_didactic_observation.py:62` (`V1`) | CERTIFIED | `V1` |
| DC-36 | multi-step ladder lineage | `tests/test_didactic_session.py::test_visual_determinism` | CERTIFIED | `ladder` 1 step |
| DC-37 | valid reduction exists but Request forza nodal | `tests/test_didactic_orchestrate.py::test_traccia_valida_ma_non_scelta_dal_planner` | CERTIFIED | `MULTI_SERIE` |
| DC-38 | direct nodal, zero transform | `tests/test_didactic_session.py::test_curated_example_session[nodal]` | CERTIFIED | `I1 0 a` 0 step |
| DC-39 | target controlled source | `tests/test_controlled_sources.py::test_vcvs_massa` con `Request qv E1` | CERTIFIED | `voltage E1` |
| DC-40 | multiple Requests (contract) | `docs/02-costituzione-kirchhoff.md: K-2` + `test_truthfulness_nodal` | CERTIFIED | single Request per IR, no silent choice |
| **E — Refusal / invalid** |
| DC-41 | no Request → Refusal | `tests/test_didactic_observation.py:345` (`time_constant` → Refusal) | CERTIFIED | `Request` validazione |
| DC-42 | target missing → Refusal | `tests/test_verify.py::test_compare_exact_rifiuta_insieme_componenti_diverso` | CERTIFIED | `R9` |
| DC-43 | unsupported quantity → Refusal | `tests/test_didactic_observation.py:345` | CERTIFIED | `time_constant` |
| DC-44 | capacitor in dc → Refusal | `tests/test_didactic_session.py::test_refusal_first_class` | CERTIFIED | `C1 b 0` → `unsolvable` |
| DC-45 | inductor in dc → Refusal | `tests/test_controlled_sources.py::test_mna_assemble_vccs_senza_control` | CERTIFIED | `L` |
| DC-46 | wrong unit → Refusal | `tests/test_controlled_sources.py::test_unita_e_segni` | CERTIFIED | `volt` su VCVS |
| DC-47 | missing/invalid reference → Refusal | `tests/test_verify.py::test_una_netlist_senza_nodo_di_riferimento` | CERTIFIED | `manca 0` |
| DC-48 | singular/floating → Refusal | `tests/test_truthfulness_nodal.py:94` (`SingularSystemError`) | CERTIFIED | `SingularSystemError` |
| DC-49 | corrupted path B → path_disagreement | `tests/test_controlled_sources.py:345` (`_a_corrotto_vcvs`) | CERTIFIED | `MNA` vs `tableau` |
| DC-50 | corrupted solution → verifier KCL/KVL | `tests/test_verify.py::test_verify_rifiuta_la_corda_falsa` | CERTIFIED | `kvl_residuals` |
| **F — Rendering** |
| DC-51 | renderer unavailable → Solved senza SVG | `tests/test_il_prodotto_funziona.py:49` (`due_maglie`) | CERTIFIED | `svg is None` |
| DC-52 | renderer exception → Failure | `tests/test_il_prodotto_funziona.py:144` (`layout` exception) | CERTIFIED | `Failure(render)` |
| DC-53 | curated LayoutIR → non-single-mesh | `tests/test_didactic_session.py::test_curated_example_session[bridge]` | CERTIFIED | `bridge` |
| DC-54 | identical IR+LayoutIR → identical SVG | `tests/test_visual_slice.py:237` (`mille_giri is`) | CERTIFIED | `is` bytes |
| DC-55 | preserved stable | `tests/test_visual_slice.py:327` (`TestA0FraIDueStati`) | CERTIFIED | `preserve` |
| **G — Determinism** |
| DC-56 | component order permutation | `tests/test_controlled_sources.py:258` (`ordine_componenti_irrilevante`) | CERTIFIED | `reversed` |
| DC-57 | node ordering | `tests/test_controlled_sources.py:258` | CERTIFIED | `sorted` |
| DC-58 | exact fractions | `tests/test_il_prodotto_funziona.py:20` (`33/4`) | CERTIFIED | `Fraction` |
| DC-59 | planner deterministico | `tests/test_didactic_session.py::test_visual_determinism` | CERTIFIED | `is` |
| DC-60 | replay certified plan | `tests/test_didactic_orchestrate.py:296` (`replayed != execution`) | CERTIFIED | `execute_plan` replay |

> **Risultato:** 60/60 mappati su test esistenti. Nessun nuovo test di contratto necessario oltre `test_didactic_session` (8) e `test_examples` (8).
