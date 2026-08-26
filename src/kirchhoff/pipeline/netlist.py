"""Una netlist testuale: il modo piu' corto per dare un circuito al prodotto.

**Perche' un formato proprio e non SPICE.** SPICE e' lo standard e sara' il
formato d'ingresso vero, ma il suo dialetto porta con se' direttive, modelli e
sottocircuiti che questo prodotto non sa ancora onorare. Un lettore SPICE
parziale accetterebbe file che poi risolve male — e risolvere male in silenzio e'
il difetto che K-1 esiste per impedire. Meglio un formato piccolo che dichiara
cosa sa leggere, finche' il resto non c'e'.

Formato, una riga per bipolo:

    V1 b 0 12 volt
    R1 b a 100 ohm
    R2 a 0 220 ohm
    ? voltage R2

Il tipo si deduce dalla lettera iniziale — `V` generatore, `R` resistore — e la
riga che comincia con `?` e' una domanda. Righe vuote e `#` sono commenti.
"""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.ir import IR, Component, Magnitude, Request

#: Lettera iniziale -> tipo. Chiuso di proposito: una lettera non prevista e' un
#: errore che nomina il colpevole, non un componente indovinato.
LETTERE = {"V": "voltage_source_dc", "R": "resistor",
           "C": "capacitor", "L": "inductor", "I": "current_source_dc"}


def leggi(testo: str) -> IR:
    """Da netlist a `IR`. Ogni errore nomina la riga e cosa c'era di sbagliato."""
    componenti: list[Component] = []
    richieste: list[Request] = []
    nodi: list[str] = []

    for numero, riga in enumerate(testo.splitlines(), 1):
        riga = riga.split("#", 1)[0].strip()
        if not riga:
            continue
        pezzi = riga.split()

        if pezzi[0] == "?":
            if len(pezzi) != 3:
                raise ValueError(
                    f"riga {numero}: una domanda e' «? <grandezza> <componente>», "
                    f"ricevuto {len(pezzi)} pezzi: {riga!r}")
            richieste.append(Request(f"q{len(richieste)+1}", pezzi[1], pezzi[2]))
            continue

        if len(pezzi) != 5:
            raise ValueError(
                f"riga {numero}: un bipolo e' «<id> <nodo> <nodo> <valore> "
                f"<unita>», ricevuti {len(pezzi)} pezzi: {riga!r}")
        ident, na, nb, valore, unita = pezzi
        tipo = LETTERE.get(ident[0].upper())
        if tipo is None:
            raise ValueError(
                f"riga {numero}: {ident!r} comincia per {ident[0]!r}, che non e' "
                f"fra {', '.join(sorted(LETTERE))}. Il vocabolario e' chiuso: un "
                "componente indovinato verrebbe risolto male in silenzio.")
        try:
            quanto = Fraction(valore)
        except ValueError:
            raise ValueError(
                f"riga {numero}: {valore!r} non e' un numero. Le frazioni si "
                "scrivono esatte — «1/3», non «0.333»: l'aritmetica di questo "
                "prodotto e' esatta e un decimale troncato la sporca.") from None
        for n in (na, nb):
            if n not in nodi:
                nodi.append(n)
        componenti.append(Component(ident, tipo, (na, nb),
                                    Magnitude(quanto, unita), ident))

    if not componenti:
        raise ValueError("netlist vuota: nessun bipolo da risolvere.")
    return IR(ir_version="1.0.0", domain="dc", source_kind="netlist",
              nodes=tuple(sorted(nodi)), components=tuple(componenti),
              requests=tuple(richieste))
