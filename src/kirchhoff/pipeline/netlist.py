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

Regime sinusoidale tipizzato (la lezione AC non e' ancora servita):

    @ac 100 rad/s
    V1 a 0 10 volt 30deg
    R1 a b 3 ohm
    L1 b 0 1/25 henry
    I1 0 a 2 ampere -60deg
    ? current R1

La pulsazione e' esatta e positiva; la fase di ciascuna sorgente e' esplicita
e multipla intera di 30 gradi. I valori sono moduli di fasore: l'IR non
specifica la convenzione RMS/picco e quindi non autorizza un calcolo di potenza.

Sorgenti controllate da tensione:

    E1 p q cp cq 2
    G1 p q cp cq 1/10 siemens

Il tipo si deduce dalla lettera iniziale — `V` generatore indipendente, `E`
VCVS, `G` VCCS, `R` resistore — e la riga che comincia con `?` e' una domanda.
Righe vuote e `#` sono commenti.
"""
from __future__ import annotations

from fractions import Fraction
import re

from kirchhoff.domain.ir import IR, Component, Magnitude, Request

#: Lettera iniziale -> tipo. Chiuso di proposito: una lettera non prevista e' un
#: errore che nomina il colpevole, non un componente indovinato.
LETTERE = {"V": "voltage_source_dc", "R": "resistor",
           "C": "capacitor", "L": "inductor", "I": "current_source_dc"}
_PHASE = re.compile(r"^([+-]?\d+)deg$")


def _nodo(nodi: list[str], n: str) -> None:
    if n not in nodi:
        nodi.append(n)


def leggi(testo: str) -> IR:
    """Da netlist a `IR`. Ogni errore nomina la riga e cosa c'era di sbagliato."""
    componenti: list[Component] = []
    richieste: list[Request] = []
    nodi: list[str] = []
    ac_omega: Fraction | None = None

    for numero, riga in enumerate(testo.splitlines(), 1):
        riga = riga.split("#", 1)[0].strip()
        if not riga:
            continue
        pezzi = riga.split()

        if pezzi[0] == "@ac":
            if ac_omega is not None:
                raise ValueError(f"riga {numero}: una sola direttiva @ac per circuito.")
            if componenti or richieste:
                raise ValueError(f"riga {numero}: la direttiva @ac va prima dei componenti e della domanda.")
            if len(pezzi) != 3 or pezzi[2] != "rad/s":
                raise ValueError(f"riga {numero}: usa «@ac <pulsazione> rad/s», non Hz o unità implicite.")
            try:
                ac_omega = Fraction(pezzi[1])
            except (ValueError, ZeroDivisionError):
                raise ValueError(f"riga {numero}: pulsazione AC non esatta.") from None
            if ac_omega <= 0:
                raise ValueError(f"riga {numero}: serve una pulsazione AC positiva.")
            continue

        if pezzi[0] == "?":
            if len(pezzi) != 3:
                raise ValueError(
                    f"riga {numero}: una domanda e' «? <grandezza> <componente>», "
                    f"ricevuto {len(pezzi)} pezzi: {riga!r}")
            richieste.append(Request(f"q{len(richieste)+1}", pezzi[1], pezzi[2]))
            continue

        ident = pezzi[0]
        iniziale = ident[0].upper()

        if iniziale == "E":
            if ac_omega is not None:
                raise ValueError(f"riga {numero}: sorgente controllata E non ancora ammessa nel sottoinsieme AC.")
            if len(pezzi) not in (6, 7):
                raise ValueError(
                    f"riga {numero}: una VCVS e' «<id> <p> <q> <cp> <cq> <μ> "
                    f"[dimensionless]», ricevuti {len(pezzi)} pezzi: {riga!r}")
            _p, _q, cp, cq, valore = pezzi[1], pezzi[2], pezzi[3], pezzi[4], pezzi[5]
            unita = pezzi[6] if len(pezzi) == 7 else "dimensionless"
            try:
                quanto = Fraction(valore)
            except ValueError:
                raise ValueError(
                    f"riga {numero}: {valore!r} non e' un numero. Le frazioni si "
                    "scrivono esatte — «1/3», non «0.333»: l'aritmetica di questo "
                    "prodotto e' esatta e un decimale troncato la sporca.") from None
            for n in (_p, _q, cp, cq):
                _nodo(nodi, n)
            componenti.append(Component(
                ident, "voltage_controlled_voltage_source", (_p, _q),
                Magnitude(quanto, unita), ident, control_nodes=(cp, cq)))
            continue

        if iniziale == "G":
            if ac_omega is not None:
                raise ValueError(f"riga {numero}: sorgente controllata G non ancora ammessa nel sottoinsieme AC.")
            if len(pezzi) not in (6, 7):
                raise ValueError(
                    f"riga {numero}: una VCCS e' «<id> <p> <q> <cp> <cq> <g> "
                    f"[siemens]», ricevuti {len(pezzi)} pezzi: {riga!r}")
            _p, _q, cp, cq, valore = pezzi[1], pezzi[2], pezzi[3], pezzi[4], pezzi[5]
            unita = pezzi[6] if len(pezzi) == 7 else "siemens"
            try:
                quanto = Fraction(valore)
            except ValueError:
                raise ValueError(
                    f"riga {numero}: {valore!r} non e' un numero. Le frazioni si "
                    "scrivono esatte — «1/3», non «0.333»: l'aritmetica di questo "
                    "prodotto e' esatta e un decimale troncato la sporca.") from None
            for n in (_p, _q, cp, cq):
                _nodo(nodi, n)
            componenti.append(Component(
                ident, "voltage_controlled_current_source", (_p, _q),
                Magnitude(quanto, unita), ident, control_nodes=(cp, cq)))
            continue

        phase_steps = 0
        if ac_omega is not None and iniziale in {"V", "I"}:
            if len(pezzi) != 6:
                raise ValueError(f"riga {numero}: una sorgente AC richiede una fase esplicita, per esempio 30deg.")
            phase = _PHASE.fullmatch(pezzi[5])
            if phase is None or int(phase.group(1)) % 30:
                raise ValueError(f"riga {numero}: fase AC esatta in gradi multipli di 30, senza arrotondamento.")
            phase_steps = int(phase.group(1)) // 30
            pezzi = pezzi[:5]
        if len(pezzi) != 5:
            raise ValueError(
                f"riga {numero}: un bipolo e' «<id> <nodo> <nodo> <valore> "
                f"<unita>», ricevuti {len(pezzi)} pezzi: {riga!r}")
        ident, na, nb, valore, unita = pezzi
        tipo = LETTERE.get(ident[0].upper())
        if tipo is None:
            raise ValueError(
                f"riga {numero}: {ident!r} comincia per {ident[0]!r}, che non e' "
                f"fra {', '.join(sorted(list(LETTERE) + ['E', 'G']))}. Il vocabolario e' chiuso: un "
                "componente indovinato verrebbe risolto male in silenzio.")
        if ac_omega is not None and iniziale in {"V", "I"}:
            tipo = "voltage_source_ac" if iniziale == "V" else "current_source_ac"
        try:
            quanto = Fraction(valore)
        except ValueError:
            raise ValueError(
                f"riga {numero}: {valore!r} non e' un numero. Le frazioni si "
                "scrivono esatte — «1/3», non «0.333»: l'aritmetica di questo "
                "prodotto e' esatta e un decimale troncato la sporca.") from None
        for n in (na, nb):
            _nodo(nodi, n)
        componenti.append(Component(ident, tipo, (na, nb),
                                    Magnitude(quanto, unita), ident, phase_steps=phase_steps))

    if not componenti:
        raise ValueError("netlist vuota: nessun bipolo da risolvere.")
    return IR(ir_version="1.0.0", domain="ac_sinusoidal" if ac_omega is not None else "dc", source_kind="netlist",
              nodes=tuple(sorted(nodi)), components=tuple(componenti),
              requests=tuple(richieste), omega=ac_omega or Fraction(0))
