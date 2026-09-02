"""Adapter Lcapy: confronto simbolico, senza alcuna autorità di prodotto."""

from __future__ import annotations

from fractions import Fraction

from lcapy import Circuit

from kirchhoff.domain.ir import IR, Request


def _number(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _device_names(ir: IR) -> dict[str, str]:
    counters = {"resistor": 0, "voltage_source_dc": 0, "current_source_dc": 0}
    prefixes = {"resistor": "R", "voltage_source_dc": "V", "current_source_dc": "I"}
    names: dict[str, str] = {}
    for component in ir.components:
        if component.type not in prefixes:
            raise ValueError(f"{component.id}: tipo non supportato da Lcapy lab")
        counters[component.type] += 1
        names[component.id] = f"{prefixes[component.type]}{counters[component.type]}"
    return names


def lcapy_value(ir: IR, request: Request) -> Fraction:
    """Restituisce un valore razionale Lcapy o rifiuta esplicitamente il subset."""
    if ir.domain != "dc":
        raise ValueError("Lcapy lab supporta solo IR DC")
    names = _device_names(ir)
    circuit = Circuit()
    for component in ir.components:
        name = names[component.id]
        p, q = component.terminals
        # Lcapy orienta la sorgente di corrente in verso opposto alla convenzione
        # Kirchhoff p→q. Invertiamo soltanto il netlist di quell'adapter.
        if component.type == "current_source_dc":
            p, q = q, p
        circuit.add(f"{name} {p} {q} {_number(component.value.amount)}")
    element = getattr(circuit, names[request.target])
    expression = element.v.expr if request.quantity == "voltage" else element.i.expr
    if not getattr(expression, "is_Rational", False):
        raise ValueError(f"Lcapy ha prodotto espressione non razionale: {expression!s}")
    value = Fraction(int(expression.p), int(expression.q))
    if ir.component(request.target).type == "current_source_dc":
        return -value
    if request.quantity == "voltage" and ir.component(request.target).type == "current_source_dc":
        return -value
    return value
