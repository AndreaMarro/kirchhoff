"""Esporta la revisione canonica come schema CircuitikZ a etichette di rete.

Ogni riga mostra un componente orientato dal primo al secondo terminale.
Etichette identiche significano lo stesso nodo elettrico, anche se le righe
non sono unite graficamente: nessun incrocio puo' cambiare la topologia.
"""
from __future__ import annotations

import re

from kirchhoff.domain.ir import IR
from kirchhoff.pipeline.netlist import leggi

SCHEMA = "kirchhoff-circuitikz-netlabels.v1"
_LABEL = re.compile(r"^[A-Za-z0-9_]{1,64}$")
_KINDS = {
    "resistor": ("R", r"\Omega"),
    "capacitor": ("C", r"\mathrm{F}"),
    "inductor": ("L", r"\mathrm{H}"),
    "voltage_source_dc": ("V", r"\mathrm{V}"),
    "current_source_dc": ("I", r"\mathrm{A}"),
    "voltage_controlled_voltage_source": ("cV", ""),
    "voltage_controlled_current_source": ("cI", r"\mathrm{S}"),
}


def _name(value: str) -> str:
    if not isinstance(value, str) or not _LABEL.fullmatch(value):
        raise ValueError(f"Etichetta {value!r} non rappresentabile con sicurezza in CircuitikZ.")
    return r"\texttt{" + value.replace("_", r"\_") + "}"


def _number(value) -> str:
    if len(str(value.numerator)) > 80 or len(str(value.denominator)) > 80:
        raise ValueError("Valore troppo lungo per uno schema leggibile.")
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    return sign + rf"\frac{{{abs(value.numerator)}}}{{{value.denominator}}}"


def export_circuitikz(circuit: IR | str) -> str:
    ir = leggi(circuit) if isinstance(circuit, str) else circuit
    if ir.domain not in {"dc", "dc_resistive"}:
        raise ValueError("CircuitikZ a etichette di rete supporta solo circuiti DC in questa versione.")
    if not 0 < len(ir.components) <= 64:
        raise ValueError("Lo schema CircuitikZ accetta da 1 a 64 componenti.")
    for node in ir.nodes:
        _name(node)
    for component in ir.components:
        _name(component.id)
        if component.type not in _KINDS:
            raise ValueError(f"{component.id}: simbolo CircuitikZ non supportato.")
        if component.type.startswith("voltage_controlled"):
            if not component.control_nodes or any(node not in ir.nodes for node in component.control_nodes):
                raise ValueError(f"{component.id}: nodi di controllo non rappresentabili.")
    for request in ir.requests:
        _name(request.target)
        if request.target not in {component.id for component in ir.components}:
            raise ValueError(f"Domanda su componente inesistente: {request.target}.")
        if request.quantity not in {"voltage", "current"}:
            raise ValueError("La domanda non ha una notazione CircuitikZ definita.")
    lines = [
        f"% {SCHEMA}",
        r"\documentclass{article}",
        r"\usepackage[american]{circuitikz}",
        r"\begin{document}",
        r"\pagestyle{empty}",
        r"\noindent\textbf{Circuito Kirchhoff}\\",
        r"\par\noindent Etichette uguali identificano lo stesso nodo elettrico. Ogni ramo e' orientato da sinistra a destra.\par",
    ]
    for index, component in enumerate(sorted(ir.components, key=lambda item: item.id.casefold())):
        if index % 8 == 0:
            if index:
                lines.extend([r"\end{circuitikz}", r"\newpage", r"\noindent\textbf{Circuito Kirchhoff, continua}\\"])
            lines.append(r"\begin{circuitikz}[american voltages]")
        symbol, unit = _KINDS[component.type]
        # In questo host CircuitikZ, V e cV senza `invert` pongono + sul
        # primo terminale del path, come il riferimento dichiarato nell'IR.
        p, q = component.terminals
        value = _number(component.value.amount)
        description = rf"{_name(component.id)}={value}"
        if unit:
            description += rf"\, {unit}"
        if component.control_nodes:
            cp, cq = component.control_nodes
            description += rf"\quad(V({_name(cp)})-V({_name(cq)}))"
        y = -2 * (index % 8)
        lines.append(
            rf"\draw (0,{y}) node[left]{{$ {_name(p)} $}} "
            rf"to[{symbol},l_={{$ {description} $}}] (6,{y}) "
            rf"node[right]{{$ {_name(q)} $}};"
        )
    lines.append(r"\end{circuitikz}")
    for request in ir.requests:
        quantity = "tensione" if request.quantity == "voltage" else "corrente"
        lines.append(rf"\par\noindent Domanda: {quantity} di {_name(request.target)}.")
    lines.extend([r"\end{document}", ""])
    return "\n".join(lines)
