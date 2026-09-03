# Esempi curati — Kirchhoff DC

5 circuiti DC verificati, eseguibili in 60s. Ogni `netlist.txt` è una riga per bipolo, unità SI obbligatoria.

| Esempio | Topologia | Richiesta | SVG | Note |
|---|---|---|---|---|
| `series` | V1 b-0, R1 b-a, R2 a-0 | `? voltage R2` = 33/4 V | sì (maglia singola) | corrente preservata |
| `parallel` | V1 a-0, R1 a-0, R2 a-0 | `? voltage R1` = 12 V | no (grado 3) | solve ok, layout manuale richiesto |
| `ladder` | V1 d-0, R1 d-c, R2 c-b, R3 b-0 | `? voltage R2` = 4 V | sì | multi-step |
| `bridge` | ponte 6 bipoli | `? voltage Rg` = 12/17 V | no | non riducibile, nodal fallback |
| `nodal` | I1 0-a, R1 a-0 | `? voltage R1` = 10 V | no | corrente imposta |

```bash
kirchhoff examples/series/netlist.txt --svg /tmp/series.svg
kirchhoff examples/ladder/netlist.txt --svg /tmp/ladder.svg
```

`parallel`/`bridge`/`nodal` risolvono ma rifiutano `layout_a_maglia` con `NotASingleMeshError` — è il limite dichiarato (K-0). Per visual serve `LayoutIR` manuale.
