"""Nomi di riferimento delle Trasformazioni citate dai casi dell'insieme.

Insieme **chiuso**: un generatore che emette un nome non elencato qui e' un errore,
non un'estensione. Il controllo e' un test, non una convenzione.

Questi sono i nomi con cui la sequenza di riferimento di un caso descrive il
percorso risolutivo atteso (Story 1.1, primo criterio): qui non c'e' comportamento,
solo il nome del passo.

Il Catalogo autoritativo vive in `domain/transform/catalog.py` — registro chiuso
caricato all'avvio, con le funzioni pure `transform(IR, params) -> (IR,
TransformResult) | Refusal` di AD-2 **emendato**: il secondo membro non e' piu' un
`Drawing`, ritirato il 15 agosto (AD-18 em.). `domain/` non puo' importare `eval/`
(AD-1), quindi la fonte sta li' e questa lista ne e' il riflesso; la riconciliazione
non e' una promessa ma un test, e `tests/test_delta.py` confronta i due insiemi.

Un caso di riferimento cita anche nomi che il Catalogo **non rende applicabili**:
descrivere un percorso risolutivo non e' eseguirlo, e FR-43 tiene a tre le
Trasformazioni applicabili senza per questo restringere il vocabolario.
"""

from __future__ import annotations

from collections.abc import Iterable

REFERENCE_TRANSFORMATIONS: frozenset[str] = frozenset({
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
})


def validate(names: Iterable[str]) -> tuple[str, ...]:
    """Restituisce la sequenza se ogni nome e' nel catalogo, altrimenti fallisce."""
    seq = tuple(names)
    fuori = [n for n in seq if n not in REFERENCE_TRANSFORMATIONS]
    if fuori:
        raise ValueError(f"Trasformazioni fuori catalogo: {', '.join(sorted(set(fuori)))}")
    return seq
