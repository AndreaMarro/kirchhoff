# Esempi curati — Kirchhoff DC

8 circuiti DC verificati, eseguibili in 60s. Ogni `netlist.txt` è una riga per bipolo, unità SI obbligatoria.

| Esempio | Topologia | Richiesta | SVG | Note |
|---|---|---|---|---|
| `series` | V1 b-0, R1 b-a, R2 a-0 | `? voltage R2` = 33/4 V | sì (maglia singola) | 0 step, nodal diretto |
| `parallel` | V1 a-0, R1 a-0, R2 a-0 | `? voltage R1` = 12 V | no (grado 3) | solve ok, layout manuale |
| `ladder` | V1 d-0, R1 d-c, R2 c-b, R3 b-0 | `? voltage R1` = 2 V | sì | 1 step serie R2,R3 |
| `bridge` | ponte 6 bipoli | `? voltage Rg` = 12/17 V | no | non riducibile, nodal |
| `nodal` | I1 0-a, R1 a-0 | `? voltage R1` = 10 V | sì (2 nodi) | 0 step |
| `series_current` | V1 d-0, R1 d-c, R2 c-b, R3 b-0 | `? voltage R3` = 6 V | sì | 1 step serie R1,R2 |
| `parallel_current` | V1 b-a, R1/R2 b-a, R3 a-0 + I1 | `? current R1` = -53/90 A | no | mix V+I, nodal |
| `floating` | V1 a-b, V2 c-0, R1 a-b, R2 b-0, R3 c-b | `? voltage R2` = 5 V | no | floating, supernodo |

```bash
kirchhoff examples/series/netlist.txt --svg /tmp/series.svg
kirchhoff examples/ladder/netlist.txt --svg /tmp/ladder.svg
```

`parallel`/`bridge`/`nodal` risolvono ma rifiutano `layout_a_maglia` con `NotASingleMeshError` — è il limite dichiarato (K-0). Per visual serve `LayoutIR` manuale.
