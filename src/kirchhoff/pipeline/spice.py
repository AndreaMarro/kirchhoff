"""Sottoinsieme SPICE DC versionato, a valori esatti e con rifiuti espliciti.

Accetta R/C/L, V/I indipendenti, E/G controllate da tensione, .op e .end.
La domanda Kirchhoff vive in un commento riconoscibile; SPICE non dispone di
una rappresentazione generale della nostra Request. Nessuna direttiva viene
scartata in silenzio. AutoCircuits usa un dialetto randomizzato distinto.
"""
from __future__ import annotations

from fractions import Fraction
import re

from kirchhoff.domain.ir import IR, PortRequest
from kirchhoff.pipeline.netlist import leggi

SCHEMA = "kirchhoff-spice-dc.v1"
_NUMBER = re.compile(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]*)$")
_NAME = re.compile(r"^[A-Za-z0-9_]+$")
_SCALE = {"": Fraction(1), "t": Fraction(10**12), "g": Fraction(10**9),
          "meg": Fraction(10**6), "k": Fraction(10**3), "m": Fraction(1, 10**3),
          "u": Fraction(1, 10**6), "n": Fraction(1, 10**9),
          "p": Fraction(1, 10**12), "f": Fraction(1, 10**15)}
_UNITS = {"R": "ohm", "C": "farad", "L": "henry", "V": "volt", "I": "ampere"}
_TYPE = {"resistor": "R", "capacitor": "C", "inductor": "L",
         "voltage_source_dc": "V", "current_source_dc": "I",
         "voltage_controlled_voltage_source": "E", "voltage_controlled_current_source": "G"}


def _value(token: str) -> Fraction:
    match = _NUMBER.fullmatch(token)
    if not match or match.group(2).lower() not in _SCALE:
        raise ValueError(f"Valore SPICE {token!r} non supportato: usa un numero decimale con prefisso SI noto.")
    return Fraction(match.group(1)) * _SCALE[match.group(2).lower()]


def _decimal(value: Fraction) -> str:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2; twos += 1
    while denominator % 5 == 0:
        denominator //= 5; fives += 1
    if denominator != 1:
        raise ValueError(f"{value}: valore razionale non esprimibile esattamente in SPICE decimale.")
    scale = max(twos, fives)
    magnitude = abs(value.numerator) * 2 ** (scale - twos) * 5 ** (scale - fives)
    digits = str(magnitude).zfill(scale + 1)
    result = digits[:-scale] + "." + digits[-scale:] if scale else digits
    result = result.rstrip("0").rstrip(".") if scale else result
    if len(result) > 40:
        raise ValueError("Valore SPICE troppo lungo per un interscambio affidabile.")
    return ("-" if value < 0 else "") + result


def _check_names(ir: IR) -> None:
    seen_nodes: set[str] = set()
    for node in ir.nodes:
        if not _NAME.fullmatch(node):
            raise ValueError(f"Nodo {node!r} non rappresentabile nel sottoinsieme SPICE.")
        folded = node.casefold()
        if folded in seen_nodes:
            raise ValueError("SPICE non distingue nodi che differiscono soltanto per maiuscole/minuscole.")
        seen_nodes.add(folded)
    seen_ids: set[str] = set()
    for component in ir.components:
        if not _NAME.fullmatch(component.id) or component.id[0].upper() != _TYPE.get(component.type):
            raise ValueError(f"Identificatore {component.id!r} non rappresentabile in SPICE.")
        folded = component.id.casefold()
        if folded in seen_ids:
            raise ValueError("SPICE non distingue componenti che differiscono soltanto per maiuscole/minuscole.")
        seen_ids.add(folded)


def export_spice(circuit: IR | str) -> str:
    ir = leggi(circuit) if isinstance(circuit, str) else circuit
    if ir.domain not in {"dc", "dc_resistive"}:
        raise ValueError("Questo interscambio SPICE copre soltanto il punto di lavoro DC.")
    if any(c.type not in _TYPE for c in ir.components):
        raise ValueError("Componente non supportato dal sottoinsieme SPICE DC.")
    _check_names(ir)
    lines = ["Kirchhoff DC operating point — exact subset", f"* {SCHEMA}"]
    for component in sorted(ir.components, key=lambda c: c.id.casefold()):
        kind = _TYPE[component.type]
        parts = [component.id, *component.terminals]
        if kind in {"E", "G"}:
            parts += list(component.control_nodes or ())
        if kind in {"V", "I"}:
            parts.append("DC")
        parts.append(_decimal(component.value.amount))
        lines.append(" ".join(parts))
    for request in ir.requests:
        if isinstance(request, PortRequest):
            p, q = request.port
            lines.append(f"* KIRCHHOFF_REQUEST resistance {p} {q}")
            continue
        if request.quantity not in {"voltage", "current"}:
            raise ValueError("La domanda non ha un'annotazione nel sottoinsieme SPICE DC.")
        lines.append(f"* KIRCHHOFF_REQUEST {request.quantity} {request.target}")
    return "\n".join([*lines, ".op", ".end", ""])


def import_spice(source: str) -> str:
    if not isinstance(source, str) or not 0 < len(source) <= 16000:
        raise ValueError("File SPICE vuoto o troppo lungo (massimo 16000 caratteri).")
    lines = source.splitlines()
    if not lines or not lines[0].strip():
        raise ValueError("SPICE richiede una riga titolo iniziale.")
    components: list[str] = []
    requests: list[tuple[str, ...]] = []
    ids: dict[str, str] = {}
    ended = False
    for number, raw in enumerate(lines[1:], 2):
        line = raw.strip()
        if not line:
            continue
        if ended:
            raise ValueError(f"Riga {number} dopo .end: contenuto non supportato.")
        if line.startswith("*"):
            words = line[1:].strip().split()
            if words and words[0].upper() == "KIRCHHOFF_REQUEST":
                if len(words) == 4 and words[1].lower() == "resistance":
                    requests.append(("resistance", words[2], words[3]))
                    continue
                if len(words) != 3 or words[1].lower() not in {"voltage", "current"}:
                    raise ValueError(f"Riga {number}: domanda Kirchhoff non valida.")
                requests.append((words[1].lower(), words[2]))
            continue
        if line.startswith("."):
            command = line.lower()
            if command == ".end":
                ended = True
            elif command != ".op":
                raise ValueError(f"Riga {number}: direttiva {line!r} non supportata dal sottoinsieme SPICE DC.")
            continue
        words = line.split()
        ident = words[0]
        kind = ident[0].upper()
        if not _NAME.fullmatch(ident) or kind not in _UNITS | {"E": "", "G": ""}:
            raise ValueError(f"Riga {number}: elemento {ident!r} non supportato.")
        if ident.casefold() in ids:
            raise ValueError(f"Riga {number}: identificatore duplicato in SPICE.")
        ids[ident.casefold()] = ident
        if kind in {"R", "C", "L"} and len(words) == 4:
            nodes = [words[1].lower(), words[2].lower()]
            rest = [str(_value(words[3])), _UNITS[kind]]
        elif kind in {"V", "I"} and len(words) in {4, 5}:
            if len(words) == 5 and words[3].upper() != "DC":
                raise ValueError(f"Riga {number}: solo sorgenti DC indipendenti sono supportate.")
            nodes = [words[1].lower(), words[2].lower()]
            rest = [str(_value(words[-1])), _UNITS[kind]]
        elif kind in {"E", "G"} and len(words) == 6:
            nodes = [x.lower() for x in words[1:5]]
            rest = [str(_value(words[5]))]
        else:
            raise ValueError(f"Riga {number}: arità o modello di {ident} non supportati.")
        if not all(_NAME.fullmatch(node) for node in nodes):
            raise ValueError(f"Riga {number}: nome di nodo non supportato.")
        components.append(" ".join([ident, *nodes, *rest]))
    if not ended:
        raise ValueError("File SPICE senza .end.")
    if not components:
        raise ValueError("File SPICE senza componenti.")
    for request in requests:
        if request[0] == "resistance":
            _, p, q = request
            components.append(f"? resistance {p.lower()} {q.lower()}")
            continue
        quantity, target = request
        if target.casefold() not in ids:
            raise ValueError(f"Domanda su componente inesistente: {target}.")
        components.append(f"? {quantity} {ids[target.casefold()]}")
    netlist = "\n".join(components)
    leggi(netlist)
    return netlist
