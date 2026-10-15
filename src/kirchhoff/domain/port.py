"""Equivalente DC di una porta: sorgente di prova esatta e due risolutori indipendenti.

La porta e' una coppia ordinata di nodi del circuito originale. Per misurare
V_th si inserisce una sorgente ideale di corrente nulla, cioe' un'apertura;
per R_th si spengono soltanto
le sorgenti indipendenti e si inietta 1 A dal secondo nodo al primo. La
soluzione del problema trasformato non diventa una lezione certificata sulla
domanda originale: questo modulo fornisce soltanto il fatto elettrico.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from .exact import Cyc12, SingularSystemError
from .independent_dc import DC_TABLEAU_TYPES, TableauSingularError, solve_dc_tableau
from .independent_phasor import (
    PHASOR_TABLEAU_TYPES, PhasorTableauSingularError, solve_phasor_tableau,
)
from .ir import DC_DOMAINS, Component, IR, Magnitude
from .mna import solve_dc, solve_phasor
from .refusal import Refusal
from .validate import validate
from .verify import verify


@dataclass(frozen=True, slots=True)
class DCPortEquivalent:
    port: tuple[str, str]
    voltage: Magnitude
    resistance: Magnitude
    norton_current: Magnitude | None


@dataclass(frozen=True, slots=True)
class PhasorMagnitude:
    """Fasore esatto con unita'; la convenzione RMS/picco rimane non dichiarata."""

    amount: Cyc12
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Cyc12):
            raise TypeError("un fasore di porta richiede Cyc12 esatto")
        if self.unit not in {"volt", "ohm", "ampere"}:
            raise ValueError(f"unita' fasoriale di porta non supportata: {self.unit}")


@dataclass(frozen=True, slots=True)
class ACPortEquivalent:
    port: tuple[str, str]
    omega: Fraction
    voltage: PhasorMagnitude
    impedance: PhasorMagnitude
    norton_current: PhasorMagnitude | None


def _probe(ir: IR, port: tuple[str, str], amperes: Fraction, *, off: bool) -> tuple[IR, str]:
    existing = {c.id for c in ir.components}
    probe_id = "I_port_probe"
    while probe_id in existing:
        probe_id += "_"
    components = []
    for c in ir.components:
        if off and c.type in {"voltage_source_dc", "current_source_dc"}:
            components.append(replace(c, value=Magnitude(Fraction(0), c.value.unit),
                                      provenance=None))
        else:
            components.append(replace(c, provenance=None))
    components.append(Component.of(probe_id, "current_source_dc", (port[1], port[0]),
                                   amperes, probe_id))
    # Il circuito di prova e' generato analiticamente: non inventiamo un'area
    # fotografica per la sorgente aggiunta a un originale da immagine.
    return replace(ir, source_kind="generated", components=tuple(components), requests=()), probe_id


def _measure(ir: IR, port: tuple[str, str], amperes: Fraction, *, off: bool) -> Fraction | Refusal:
    measured, probe_id = _probe(ir, port, amperes, off=off)
    gate = validate(measured)
    if isinstance(gate, Refusal):
        return gate
    try:
        nodal = solve_dc(measured)
        branch = solve_dc_tableau(measured)
    except (SingularSystemError, TableauSingularError):
        return Refusal("unsolvable", f"{port[0]}→{port[1]}", "operation",
                       "La porta non ha una soluzione DC finita per la sorgente di prova.")
    if nodal != branch:
        return Refusal("path_disagreement", probe_id, "component",
                       "MNA e tableau di ramo non concordano sulla misura di porta.")
    residual = verify(measured, nodal)
    if residual is not None:
        return residual
    return -nodal[probe_id]["voltage"]


def analyze_dc_port(ir: IR, port: tuple[str, str]) -> DCPortEquivalent | Refusal:
    """Restituisce V_th, R_th e I_N quando finito, nelle unita' SI esatte.

    Accetta circuiti lineari DC che entrambi i percorsi sanno risolvere. Non
    interpreta un operazionale fuori dalla sua regione lineare, ne' serve
    una derivazione didattica o una risposta di esame.
    """
    label = f"{port[0]}→{port[1]}"
    if port[0] == port[1] or any(node not in ir.nodes for node in port):
        return Refusal("claim_unsupported", label, "operation",
                       "La porta deve nominare due nodi distinti del circuito.")
    if ir.domain not in DC_DOMAINS or not ir.components or any(c.type not in DC_TABLEAU_TYPES for c in ir.components):
        return Refusal("claim_unsupported", label, "operation",
                       "Questo calcolo di porta ammette solo i componenti lineari DC supportati.")
    voltage = _measure(ir, port, Fraction(0), off=False)
    if isinstance(voltage, Refusal):
        return voltage
    resistance = _measure(ir, port, Fraction(1), off=True)
    if isinstance(resistance, Refusal):
        return resistance
    norton = None if resistance == 0 else Magnitude(voltage / resistance, "ampere")
    return DCPortEquivalent(port, Magnitude(voltage, "volt"),
                            Magnitude(resistance, "ohm"), norton)


def _ac_probe(ir: IR, port: tuple[str, str], amperes: Fraction, *, off: bool) -> tuple[IR, str]:
    existing = {c.id for c in ir.components}
    probe_id = "I_port_probe"
    while probe_id in existing:
        probe_id += "_"
    components = []
    for c in ir.components:
        if off and c.type in {"voltage_source_ac", "current_source_ac"}:
            components.append(replace(c, value=Magnitude(Fraction(0), c.value.unit),
                                      phase_steps=0, provenance=None))
        else:
            components.append(replace(c, provenance=None))
    components.append(Component.of(probe_id, "current_source_ac", (port[1], port[0]),
                                   amperes, probe_id, phase_steps=0))
    return replace(ir, source_kind="generated", components=tuple(components), requests=()), probe_id


def _measure_ac(ir: IR, port: tuple[str, str], amperes: Fraction, *, off: bool) -> Cyc12 | Refusal:
    measured, probe_id = _ac_probe(ir, port, amperes, off=off)
    gate = validate(measured)
    if isinstance(gate, Refusal):
        return gate
    try:
        nodal = solve_phasor(measured)
        branch = solve_phasor_tableau(measured)
    except (SingularSystemError, PhasorTableauSingularError):
        return Refusal("unsolvable", f"{port[0]}→{port[1]}", "operation",
                       "La porta non ha una soluzione AC finita per la sorgente di prova.")
    if nodal != branch:
        return Refusal("path_disagreement", probe_id, "component",
                       "MNA e tableau fasoriale non concordano sulla misura di porta.")
    residual = verify(measured, nodal)
    if residual is not None:
        return residual
    return -nodal[probe_id]["voltage"]


def analyze_ac_port(ir: IR, port: tuple[str, str]) -> ACPortEquivalent | Refusal:
    """Vth, Zth e Norton finito su fasori a frequenza singola esatta.

    Non fissa RMS/picco, dunque non autorizza una conclusione di potenza.
    Fornisce il fatto elettrico; richiesta/prova didattica AC non servite.
    """
    label = f"{port[0]}→{port[1]}"
    if port[0] == port[1] or any(node not in ir.nodes for node in port):
        return Refusal("claim_unsupported", label, "operation",
                       "La porta deve nominare due nodi distinti del circuito.")
    if ir.domain != "ac_sinusoidal" or not ir.components or any(
        c.type not in PHASOR_TABLEAU_TYPES for c in ir.components
    ):
        return Refusal("claim_unsupported", label, "operation",
                       "Questa porta ammette solo il sottoinsieme AC sinusoidale modellato.")
    voltage = _measure_ac(ir, port, Fraction(0), off=False)
    if isinstance(voltage, Refusal):
        return voltage
    impedance = _measure_ac(ir, port, Fraction(1), off=True)
    if isinstance(impedance, Refusal):
        return impedance
    norton = None if impedance == 0 else PhasorMagnitude(voltage / impedance, "ampere")
    return ACPortEquivalent(port, ir.omega, PhasorMagnitude(voltage, "volt"),
                            PhasorMagnitude(impedance, "ohm"), norton)
