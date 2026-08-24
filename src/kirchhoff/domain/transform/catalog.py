"""Il catalogo chiuso delle Trasformazioni, nel dominio.

I nomi esistevano gia' in `eval/transformations.py`, che si dichiara «insieme
**chiuso**» e annota: *«Il Catalogo vero ... nasce con la Story 2.6 e dovra'
riconciliarsi con questa lista»*. Non puo' essere quella la fonte: `domain/` non
importa nulla fuori da se' (AD-1, recinto 1), quindi il catalogo autoritativo vive
qui e la lista di `eval/` diventa il riflesso.

La riconciliazione non e' una convenzione: `tests/test_delta.py` confronta i due
insiemi e fallisce se divergono. Un catalogo scritto due volte prima o poi diverge,
e il posto dove diverge e' invisibile (E-62 dell'error ledger).

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from typing import Literal

TransformationKind = Literal[
    # riduzioni di rete
    "serie",
    "parallelo",
    "stella_triangolo",
    # ripartizioni
    "partitore_di_tensione",
    "partitore_di_corrente",
    # leggi costitutive
    "legge_di_ohm",
    "legge_di_ohm_fasoriale",
    "impedenza_complessa",
    # transitori
    "circuito_equivalente_a_t0",
    "circuito_equivalente_a_regime",
    "resistenza_equivalente_di_thevenin",
    "costante_di_tempo",
    "equazione_caratteristica",
    "radici_caratteristiche",
    # trifase
    "circuito_monofase_equivalente",
    "sfasamento_di_fase",
]

CATALOG: frozenset[str] = frozenset({
    "serie",
    "parallelo",
    "stella_triangolo",
    "partitore_di_tensione",
    "partitore_di_corrente",
    "legge_di_ohm",
    "legge_di_ohm_fasoriale",
    "impedenza_complessa",
    "circuito_equivalente_a_t0",
    "circuito_equivalente_a_regime",
    "resistenza_equivalente_di_thevenin",
    "costante_di_tempo",
    "equazione_caratteristica",
    "radici_caratteristiche",
    "circuito_monofase_equivalente",
    "sfasamento_di_fase",
})
