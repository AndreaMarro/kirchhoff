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

Per una resistenza vista da due morsetti, la domanda nomina i nodi, non un
componente artificiale:

    R1 a 0 3 ohm
    R2 a 0 6 ohm
    ? resistance a 0

Regime sinusoidale tipizzato (lezione corrente/tensione per RLC e V/I indipendenti):

    @ac 100 rad/s
    @amplitude rms
    V1 a 0 10 volt 30deg
    R1 a b 3 ohm
    L1 b 0 1/25 henry
    I1 0 a 2 ampere -60deg
    ? current R1

La pulsazione e' esatta e positiva; la fase di ciascuna sorgente e' esplicita
e multipla intera di 30 gradi. La direttiva opzionale @amplitude, dopo @ac
e prima dei componenti, dichiara rms, peak o unspecified per tutti i fasori.
Senza direttiva la convenzione resta unspecified. La dichiarazione appartiene
all'ingresso della lezione e non cambia i numeri dell'IR. La domanda
«? power R1» richiede rms o peak espliciti e restituisce la potenza complessa
assorbita in convenzione passiva, con parti attiva P e reattiva Q.
«? impedance a b» richiede @ac e misura l'impedenza fra due nodi esistenti
con le sorgenti indipendenti spente. Il rapporto tensione/corrente non dipende
dalla dichiarazione RMS/picco e non calcola una potenza.

Sorgenti controllate da tensione:

    E1 p q cp cq 2
    G1 p q cp cq 1/10 siemens

I guadagni E/G sono reali ed esatti anche in AC: il fasore complesso nasce
dalla tensione di controllo, non da una fase indipendente della sorgente.

Operazionale ideale in regione lineare (uscita p,q; ingressi +,-):

    O1 p q plus minus

Impone V(plus)=V(minus) e correnti di ingresso nulle. Il guadagno non e'
approssimato con un numero grande; la lezione op-amp non e' ancora servita.

Il tipo si deduce dalla lettera iniziale — `V` generatore indipendente, `E`
VCVS, `G` VCCS, `R` resistore — e la riga che comincia con `?` e' una domanda.
Righe vuote e `#` sono commenti.
"""
from __future__ import annotations

from fractions import Fraction
import re

from kirchhoff.domain.ir import IR, Component, Magnitude, PortRequest, Request

#: Lettera iniziale -> tipo. Chiuso di proposito: una lettera non prevista e' un
#: errore che nomina il colpevole, non un componente indovinato.
LETTERE = {"V": "voltage_source_dc", "R": "resistor",
           "C": "capacitor", "L": "inductor", "I": "current_source_dc"}
_PHASE = re.compile(r"^([+-]?\d+)deg$")
AMPLITUDE_CONVENTIONS = frozenset({'rms', 'peak', 'unspecified'})


def _nodo(nodi: list[str], n: str) -> None:
    if n not in nodi:
        nodi.append(n)


def leggi(testo: str) -> IR:
    """Proiezione elettrica della netlist, senza conversioni di ampiezza."""
    return leggi_con_convenzioni(testo)[0]


def leggi_con_convenzioni(testo: str) -> tuple[IR, str]:
    """Legge insieme IR e scala dei fasori; ogni errore identifica la riga.

    La convenzione resta fuori dal kernel, che risolve equazioni lineari sulla
    scala fornita. La lezione conserva la dichiarazione senza inferirla.
    """
    if any(line.split('#', 1)[0].split()[:1] == ['@laplace'] for line in testo.splitlines()):
        from kirchhoff.pipeline.laplace_input import parse_laplace
        return parse_laplace(testo).ir, 'unspecified'
    componenti: list[Component] = []
    richieste: list[Request | PortRequest] = []
    nodi: list[str] = []
    ac_omega: Fraction | None = None
    amplitude: str | None = None

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

        if pezzi[0] == '@amplitude':
            if ac_omega is None:
                raise ValueError(f'riga {numero}: @amplitude richiede prima una direttiva @ac.')
            if amplitude is not None:
                raise ValueError(f'riga {numero}: una sola direttiva @amplitude per circuito.')
            if componenti or richieste:
                raise ValueError(f'riga {numero}: @amplitude va prima dei componenti e della domanda.')
            if len(pezzi) != 2 or pezzi[1] not in AMPLITUDE_CONVENTIONS:
                raise ValueError(f'riga {numero}: usa «@amplitude rms», «@amplitude peak» oppure «@amplitude unspecified».')
            amplitude = pezzi[1]
            continue

        if pezzi[0] == "?":
            if len(pezzi) > 1 and pezzi[1] in {"resistance", "impedance"}:
                if len(pezzi) != 4:
                    raise ValueError(f"riga {numero}: la domanda di porta è «? {pezzi[1]} <morsetto> <morsetto>».")
                if pezzi[1] == "impedance" and ac_omega is None:
                    raise ValueError(f"riga {numero}: la domanda di impedenza richiede prima @ac <pulsazione> rad/s.")
                richieste.append(PortRequest(f"q{len(richieste)+1}",
                                             "equivalent_impedance" if pezzi[1] == "impedance" else "equivalent_resistance",
                                             (pezzi[2], pezzi[3])))
                continue
            if len(pezzi) != 3:
                raise ValueError(
                    f"riga {numero}: una domanda e' «? <grandezza> <componente>», "
                    f"ricevuto {len(pezzi)} pezzi: {riga!r}")
            richieste.append(Request(f"q{len(richieste)+1}", pezzi[1], pezzi[2]))
            continue

        ident = pezzi[0]
        iniziale = ident[0].upper()

        if iniziale == "E":
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

        if iniziale == "O":
            if len(pezzi) != 5:
                raise ValueError(f"riga {numero}: un operazionale ideale e' «<id> <uscita+> <uscita-> <ingresso+> <ingresso->».")
            _p, _q, cp, cq = pezzi[1:]
            for n in (_p, _q, cp, cq):
                _nodo(nodi, n)
            componenti.append(Component(
                ident, "ideal_opamp", (_p, _q),
                Magnitude(Fraction(0), "dimensionless"), ident,
                control_nodes=(cp, cq)))
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
                f"fra {', '.join(sorted(list(LETTERE) + ['E', 'G', 'O']))}. Il vocabolario e' chiuso: un "
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
    ir = IR(ir_version="1.0.0", domain="ac_sinusoidal" if ac_omega is not None else "dc", source_kind="netlist",
              nodes=tuple(sorted(nodi)), components=tuple(componenti),
              requests=tuple(richieste), omega=ac_omega or Fraction(0))
    return ir, amplitude or 'unspecified'
