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


#: Gli attributi che compongono l'identita' sostanziale di un componente. Non e'
#: l'elenco dei campi di `Component`: `provenance` dice da dove il componente e'
#: stato *letto*, non che cosa *e'*, e un ritaglio diverso non lo rende un altro
#: componente.
IDENTITY_ATTRIBUTES: tuple[str, ...] = (
    "type", "terminals", "value", "symbolic", "phase_steps",
)

#: **Il discriminante di AD-22 v2.1.** Per ciascuna operazione, gli attributi che
#: possono cambiare mentre l'identita' dell'entita' sopravvive.
#:
#: L'insieme predefinito e' **vuoto**: chi non dichiara nulla non muta nulla. Cosi'
#: una `R1` da 10 Ω che dopo una riduzione in parallelo vale 6⅔ Ω **non e'**
#: preservata — e' una rimozione piu' una creazione che ne ha riusato il nome, e
#: come tale deve comparire nel `Delta`.
#:
#: Perche' qui e non nel controllore: il discriminante lo dichiara **il Catalogo**,
#: mai la `Transform` misurata. Chi e' misurato non definisce il proprio
#: riferimento (AD-22, istruttoria R2-A del 24/08/2026).
#:
#: `serie` e `parallelo` non dichiarano nulla: fondono, non modificano in luogo.
#: Un'operazione futura che deve poterlo fare — la disattivazione di un generatore,
#: per esempio — dichiara **qui** l'attributo che le serve, e il controllo lo
#: consente per quella operazione soltanto. E' la riga da cambiare, e
#: `test_un_attributo_dichiarato_mutabile_lascia_l_entita_preservata` il posto dove
#: dichiarare il caso nuovo.
MUTABLE_ATTRIBUTES: dict[str, frozenset[str]] = {
    nome: frozenset() for nome in sorted(CATALOG)
}


def mutable_attributes(operation: str) -> frozenset[str]:
    """Gli attributi mutabili dichiarati da `operation`. Vuoto se non dichiara nulla.

    Solleva se l'operazione e' fuori dal catalogo: chiedere il discriminante di
    un'operazione che non esiste e' un errore di programmazione, non un caso di
    dominio, e rispondere «nessuno» lo renderebbe silenzioso.
    """
    if operation not in CATALOG:
        raise ValueError(
            f"operazione {operation!r} fuori dal catalogo chiuso: "
            "non ha attributi mutabili perche' non esiste.")
    return MUTABLE_ATTRIBUTES[operation]


# Il catalogo e la dichiarazione non possono divergere: una voce senza
# dichiarazione avrebbe discriminante indefinito, e la si leggerebbe come «tutto
# mutabile» o «niente mutabile» a seconda di chi la interroga.
if set(MUTABLE_ATTRIBUTES) != CATALOG:  # pragma: no cover - invariante di import
    raise RuntimeError(
        "il catalogo e la dichiarazione degli attributi mutabili sono divergenti")
