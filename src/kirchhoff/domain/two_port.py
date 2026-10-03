"""Matrice Y fasoriale di due porte su una rete lineare a sorgenti spente.

Ogni colonna impone 1 V su una porta e 0 V sull'altra; la corrente entrante
nella rete e' l'opposto della corrente del generatore ideale di prova. Le
controllate restano attive. MNA e tableau indipendente devono concordare.
Questo fatto elettrico non e' una lezione di due porte servita dal prodotto.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from .exact import Cyc12, SingularSystemError
from .independent_phasor import (
    PHASOR_TABLEAU_TYPES, PhasorTableauSingularError, solve_phasor_tableau,
)
from .ir import Component, IR, Magnitude
from .mna import solve_phasor
from .refusal import Refusal
from .validate import validate
from .verify import verify


def _check_matrix(ports, omega, entries) -> None:
    if (len(ports) != 2 or any(len(port) != 2 or not all(isinstance(n, str) and n for n in port)
                               or port[0] == port[1] for port in ports)
            or set(ports[0]) == set(ports[1])):
        raise ValueError("una matrice a due porte richiede due coppie orientate distinte")
    if not isinstance(omega, Fraction) or omega <= 0:
        raise ValueError("una matrice AC richiede pulsazione positiva esatta")
    if len(entries) != 2 or any(len(row) != 2 for row in entries):
        raise ValueError("la matrice di porta deve essere 2×2")
    if any(not isinstance(value, Cyc12) for row in entries for value in row):
        raise TypeError("la matrice di porta richiede fasori Cyc12 esatti")


@dataclass(frozen=True, slots=True)
class ACAdmittanceMatrix:
    ports: tuple[tuple[str, str], tuple[str, str]]
    omega: Fraction
    entries: tuple[tuple[Cyc12, Cyc12], tuple[Cyc12, Cyc12]]
    unit: str = "siemens"

    def __post_init__(self) -> None:
        if self.unit != "siemens":
            raise ValueError("la matrice Y si esprime in siemens")
        _check_matrix(self.ports, self.omega, self.entries)


@dataclass(frozen=True, slots=True)
class ACImpedanceMatrix:
    ports: tuple[tuple[str, str], tuple[str, str]]
    omega: Fraction
    entries: tuple[tuple[Cyc12, Cyc12], tuple[Cyc12, Cyc12]]
    unit: str = "ohm"

    def __post_init__(self) -> None:
        if self.unit != "ohm":
            raise ValueError("la matrice Z si esprime in ohm")
        _check_matrix(self.ports, self.omega, self.entries)


def admittance_to_impedance(admittance: ACAdmittanceMatrix) -> ACImpedanceMatrix | Refusal:
    """Converte Y in Z solo quando det(Y) e' non nullo, senza invalidare Y.

    L'identita' YZ=I verifica la conversione algebrica. Una Y fornita
    dall'utente non diventa per questo un fatto elettrico certificato.
    """
    if not isinstance(admittance, ACAdmittanceMatrix):
        raise TypeError("serve una matrice Y AC tipizzata")
    (a, b), (c, d) = admittance.entries
    determinant = a * d - b * c
    if not determinant:
        return Refusal("claim_unsupported", "parametri Z", "operation",
                       "La matrice Y e' valida ma singolare: la rappresentazione Z non esiste.")
    entries = ((d / determinant, -b / determinant),
               (-c / determinant, a / determinant))
    for i in range(2):
        for j in range(2):
            residual = sum((admittance.entries[i][k] * entries[k][j]
                            for k in range(2)), Cyc12.of(0))
            if residual != int(i == j):
                return Refusal("residual", "parametri Z", "operation",
                               "La conversione di Y non soddisfa l'identita' YZ=I.")
    return ACImpedanceMatrix(admittance.ports, admittance.omega, entries)


def _column(ir: IR, ports: tuple[tuple[str, str], tuple[str, str]], driven: int):
    existing = {c.id for c in ir.components}
    sources = []
    for index, port in enumerate(ports):
        probe_id = f"V_port_probe_{index + 1}"
        while probe_id in existing:
            probe_id += "_"
        existing.add(probe_id)
        sources.append(Component.of(probe_id, "voltage_source_ac", port,
                                    Fraction(1 if index == driven else 0),
                                    probe_id, phase_steps=0))
    components = []
    for c in ir.components:
        if c.type in {"voltage_source_ac", "current_source_ac"}:
            components.append(replace(c, value=Magnitude(Fraction(0), c.value.unit),
                                      phase_steps=0, provenance=None))
        else:
            components.append(replace(c, provenance=None))
    measured = replace(ir, source_kind="generated", components=tuple(components + sources),
                       requests=())
    gate = validate(measured)
    if isinstance(gate, Refusal):
        return gate
    try:
        nodal = solve_phasor(measured)
        branch = solve_phasor_tableau(measured)
    except (SingularSystemError, PhasorTableauSingularError):
        return Refusal("unsolvable", "due porte AC", "operation",
                       "Le sorgenti di prova non producono una matrice Y finita.")
    if nodal != branch:
        return Refusal("path_disagreement", "due porte AC", "operation",
                       "MNA e tableau fasoriale non concordano sulle correnti di porta.")
    residual = verify(measured, nodal)
    if residual is not None:
        return residual
    return (-nodal[sources[0].id]["current"], -nodal[sources[1].id]["current"])


def analyze_ac_y_matrix(
    ir: IR, ports: tuple[tuple[str, str], tuple[str, str]],
) -> ACAdmittanceMatrix | Refusal:
    """Y_ij = corrente entrante in i quando V_j=1 V e l'altra porta e' a 0 V."""
    label = "due porte AC"
    if len(ports) != 2 or any(len(port) != 2 or port[0] == port[1]
                              or any(node not in ir.nodes for node in port) for port in ports):
        return Refusal("claim_unsupported", label, "operation",
                       "Servono due porte orientate, ciascuna con nodi distinti presenti.")
    if set(ports[0]) == set(ports[1]):
        return Refusal("claim_unsupported", label, "operation",
                       "Le due porte non possono essere gli stessi morsetti.")
    if ir.domain != "ac_sinusoidal" or not ir.components or any(
        c.type not in PHASOR_TABLEAU_TYPES for c in ir.components
    ):
        return Refusal("claim_unsupported", label, "operation",
                       "La matrice Y richiede il sottoinsieme AC sinusoidale modellato.")
    first = _column(ir, ports, 0)
    if isinstance(first, Refusal):
        return first
    second = _column(ir, ports, 1)
    if isinstance(second, Refusal):
        return second
    return ACAdmittanceMatrix(ports, ir.omega,
                              ((first[0], second[0]), (first[1], second[1])))
