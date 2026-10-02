"""Secondo assemblaggio AC: correnti e tensioni di ramo, KCL, KVL, impedenze.

Non importa il solutore MNA né le sue classificazioni o matrice. Condivide
soltanto l'aritmetica esatta Cyc12 e la costruzione dell'albero del tableau DC.
L'inviluppo è intenzionalmente ristretto a R/L/C e generatori sinusoidali di
tensione e corrente con fasi multiple di 30 gradi; non è ancora una lezione servita.
"""

from __future__ import annotations

from .exact import Cyc12, J, ONE, ZERO, zeta_pow
from .independent_dc import _albero_ricoprente, _percorso_albero, _vcontrol_coeffs
from .ir import IR, REFERENCE_NODE

PHASOR_TABLEAU_TYPES = frozenset({"resistor", "inductor", "capacitor", "voltage_source_ac", "current_source_ac", "ideal_opamp"})


def _impedance(ir: IR, component) -> Cyc12:
    if component.type == "resistor":
        return Cyc12.of(component.value.amount)
    if component.type == "inductor":
        return J * Cyc12.of(ir.omega * component.value.amount)
    return ONE / (J * Cyc12.of(ir.omega * component.value.amount))


def _eliminate(matrix: list[list[Cyc12]], known: list[Cyc12]) -> list[Cyc12]:
    """Eliminazione triangolare; distinta da Gauss-Jordan del percorso MNA."""
    size = len(known)
    rows = [line[:] + [known[index]] for index, line in enumerate(matrix)]
    for column in range(size):
        pivot = next((i for i in range(column, size) if rows[i][column]), None)
        if pivot is None:
            raise ValueError(f"tableau fasoriale singolare alla colonna {column}")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for index in range(column + 1, size):
            if rows[index][column]:
                factor = rows[index][column] / rows[column][column]
                rows[index] = [value - factor * top for value, top in zip(rows[index], rows[column])]
    values = [ZERO] * size
    for index in range(size - 1, -1, -1):
        values[index] = (rows[index][-1] - sum(
            (rows[index][j] * values[j] for j in range(index + 1, size)), ZERO
        )) / rows[index][index]
    return values


def solve_phasor_tableau(ir: IR) -> dict[str, dict[str, Cyc12]]:
    """Soluzione indipendente della sottoclasse fasoriale attualmente modellata."""
    if ir.domain not in {"ac_sinusoidal", "three_phase"}:
        raise ValueError("il tableau fasoriale richiede un dominio AC")
    if ir.omega <= 0:
        raise ValueError("il tableau fasoriale richiede pulsazione positiva")
    branches = list(ir.components)
    if not branches:
        raise ValueError("tableau fasoriale senza rami")
    for component in branches:
        if component.type not in PHASOR_TABLEAU_TYPES:
            raise ValueError(f"{component.id}: {component.type} non ammesso nel tableau fasoriale")

    parent, tree = _albero_ricoprente(ir)
    chords = [component for component in branches if component.id not in tree]
    nodes = [node for node in ir.nodes if node != REFERENCE_NODE and node in parent]
    count = len(branches)
    size = 2 * count
    if len(nodes) + len(chords) + count != size:
        raise ValueError("tableau fasoriale non quadrato")
    positions = {component.id: index for index, component in enumerate(branches)}
    matrix = [[ZERO] * size for _ in range(size)]
    known = [ZERO] * size
    row = 0

    for node in nodes:
        for component in branches:
            if component.terminals[0] == node:
                matrix[row][count + positions[component.id]] -= ONE
            elif component.terminals[1] == node:
                matrix[row][count + positions[component.id]] += ONE
        row += 1

    for chord in chords:
        matrix[row][positions[chord.id]] += ONE
        for component_id, sign in _percorso_albero(ir, parent, chord.terminals[1], chord.terminals[0]):
            matrix[row][positions[component_id]] += sign
        row += 1

    for component in branches:
        index = positions[component.id]
        if component.type == "current_source_ac":
            matrix[row][count + index] = ONE
            known[row] = Cyc12.of(component.value.amount) * zeta_pow(component.phase_steps)
        elif component.type == "voltage_source_ac":
            matrix[row][index] = ONE
            known[row] = Cyc12.of(component.value.amount) * zeta_pow(component.phase_steps)
        elif component.type == "ideal_opamp":
            cp, cq = component.control_nodes
            for cid, sign in _vcontrol_coeffs(ir, parent, cp, cq):
                matrix[row][positions[cid]] += Cyc12.of(sign)
        else:
            matrix[row][index] = ONE
            matrix[row][count + index] = -_impedance(ir, component)
        row += 1

    values = _eliminate(matrix, known)
    return {component.id: {"voltage": values[positions[component.id]],
                           "current": values[count + positions[component.id]]}
            for component in branches}
