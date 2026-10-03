"""MNA unilaterale in Q(s), RLC e sorgenti indipendenti, stati a t=0−.

Nessuna stringa simbolica viene valutata.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction as F

from kirchhoff.domain.exact import SingularSystemError, solve_linear
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from .laplace_rational import RationalFunction as RF, ZERO, ONE, S


TYPES = frozenset({'resistor', 'capacitor', 'inductor', 'voltage_source_dc', 'current_source_dc'})


@dataclass(frozen=True, slots=True)
class Variable:
    name: str
    kind: str
    target: str
    unit: str

    def to_json(self):
        return dict(name=self.name, kind=self.kind, target=self.target, unit=self.unit)


@dataclass(frozen=True, slots=True)
class LaplaceSystem:
    variables: tuple[Variable, ...]
    row_labels: tuple[str, ...]
    matrix: tuple[tuple[RF, ...], ...]
    rhs: tuple[RF, ...]
    source_transforms: tuple[tuple[str, str, RF], ...]
    capacitor_voltages: tuple[tuple[str, F], ...]
    inductor_currents: tuple[tuple[str, F], ...]

    def to_json(self):
        return dict(schema='laplace-mna.v1', domain='laplace',
                    variable=dict(symbol='s', unit='1/s'), initial_time='0-',
                    conventions=dict(voltage='V(first)-V(second)', current='first → second',
                                     capacitor='I(s)=s*C*V(s)-C*v(0-)',
                                     inductor='V(s)=s*L*I(s)-L*i(0-)'),
                    variables=[v.to_json() for v in self.variables], row_labels=list(self.row_labels),
                    matrix=[[v.to_json() for v in row] for row in self.matrix], rhs=[v.to_json() for v in self.rhs],
                    source_transforms=[dict(component=cid, unit=unit, value=value.to_json())
                                       for cid, unit, value in self.source_transforms],
                    capacitor_voltages=[dict(component=cid, exact=str(value), unit='V') for cid, value in self.capacitor_voltages],
                    inductor_currents=[dict(component=cid, exact=str(value), unit='A') for cid, value in self.inductor_currents])


@dataclass(frozen=True, slots=True)
class BranchTransform:
    component: str
    reference: tuple[str, str]
    voltage: RF
    current: RF

    def to_json(self):
        return dict(component=self.component, reference=list(self.reference),
                    voltage=dict(unit='V*s', value=self.voltage.to_json()),
                    current=dict(unit='A*s', value=self.current.to_json()))


@dataclass(frozen=True, slots=True)
class LaplaceSolution:
    system: LaplaceSystem
    values: tuple[RF, ...]
    branches: tuple[BranchTransform, ...]

    @property
    def solution(self):
        return {v.name:value for v, value in zip(self.system.variables, self.values)}

    def branch(self, component):
        for branch in self.branches:
            if branch.component == component:
                return branch
        raise KeyError(component)

    def to_json(self):
        return dict(schema='laplace-solution.v1', outcome='solved', system=self.system.to_json(),
                    solution=[dict(variable=v.name, unit=v.unit, value=value.to_json())
                              for v, value in zip(self.system.variables, self.values)],
                    branches=[b.to_json() for b in self.branches],
                    checks=['residui della matrice MNA', 'legge dei nodi su tutti i rami', 'leggi costitutive con stato iniziale'],
                    canonical_proof=False)


def _inputs(ir, source_transforms, capacitor_voltages, inductor_currents):
    if not isinstance(ir, IR):
        raise TypeError('Il circuito Laplace deve essere un IR tipizzato.')
    if ir.domain != 'laplace' or ir.omega != 0 or any(c.type not in TYPES for c in ir.components):
        return Refusal('claim_unsupported', 'laplace', 'operation',
                       'Il percorso Laplace ammette solo R, L, C e sorgenti indipendenti, senza pulsazione AC.')
    if not ir.components or len(set(ir.nodes)) != len(ir.nodes):
        return Refusal('topology', 'laplace', 'operation', 'La rete Laplace è vuota oppure contiene nodi duplicati.')
    for values, kinds, label, expected_type in (
        (source_transforms, {'voltage_source_dc', 'current_source_dc'}, 'trasformate delle sorgenti', RF),
        (capacitor_voltages, {'capacitor'}, 'tensioni iniziali dei condensatori', F),
        (inductor_currents, {'inductor'}, 'correnti iniziali degli induttori', F),
    ):
        if not isinstance(values, Mapping):
            raise TypeError(f'Le {label} devono essere una mappa per identificatore.')
        expected = {c.id for c in ir.components if c.type in kinds}
        if set(values) != expected:
            raise ValueError(f'Dichiara tutte e sole le {label}, anche quando valgono zero: {sorted(expected)}.')
        if any(not isinstance(value, expected_type) for value in values.values()):
            raise TypeError(f'Le {label} richiedono valori esatti del tipo previsto.')
    for cid, transform in source_transforms.items():
        if not transform.proper:
            return Refusal('claim_unsupported', cid, 'component',
                           'Le sorgenti ammesse hanno trasformata propria o costante; le derivate di impulso non sono ingressi supportati.')
    return None


def assemble_laplace(ir: IR, *, source_transforms: Mapping[str, RF],
                     capacitor_voltages: Mapping[str, F],
                     inductor_currents: Mapping[str, F]) -> LaplaceSystem | Refusal:
    """Costruisce A(s)x(s)=b(s). Nessuno stato iniziale viene inferito come zero.

    I tipi V/I dell'IR identificano soltanto i rami; source_transforms è
    l'ingresso esplicito, e non si ricava una forma d'onda da value.amount.
    """
    refused = _inputs(ir, source_transforms, capacitor_voltages, inductor_currents)
    if refused:
        return refused
    nodes = [node for node in ir.nodes if node != '0']
    currents = [c for c in ir.components if c.type in {'voltage_source_dc', 'inductor'}]
    node_index = {node:i for i, node in enumerate(nodes)}
    current_index = {c.id:len(nodes)+i for i, c in enumerate(currents)}
    variables = tuple([Variable(f'V({n})', 'node_voltage', n, 'V*s') for n in nodes]
                      + [Variable(f'I({c.id})', 'branch_current', c.id, 'A*s') for c in currents])
    size = len(variables)
    matrix, rhs = [[ZERO]*size for _ in range(size)], [ZERO]*size
    for c in ir.components:
        p, q = c.terminals
        incidence = [(node_index[n], sign) for n, sign in ((p, 1), (q, -1)) if n != '0']
        if c.type in {'resistor', 'capacitor'}:
            admittance = RF.of(1/c.value.amount) if c.type == 'resistor' else S*c.value.amount
            offset = ZERO if c.type == 'resistor' else RF.of(-c.value.amount*capacitor_voltages[c.id])
            for row, row_sign in incidence:
                rhs[row] -= row_sign*offset
                for column, column_sign in incidence:
                    matrix[row][column] += row_sign*column_sign*admittance
        elif c.type == 'current_source_dc':
            for row, sign in incidence:
                rhs[row] -= sign*source_transforms[c.id]
        else:
            column = current_index[c.id]
            for row, sign in incidence:
                matrix[row][column] += sign
                matrix[column][row] += sign
            if c.type == 'inductor':
                matrix[column][column] = -S*c.value.amount
                rhs[column] = RF.of(-c.value.amount*inductor_currents[c.id])
            else:
                rhs[column] = source_transforms[c.id]
    return LaplaceSystem(variables, tuple([f'KCL({n})' for n in nodes]+[f'KVL({c.id})' for c in currents]),
                         tuple(tuple(row) for row in matrix), tuple(rhs),
                         tuple((c.id, 'V*s' if c.type == 'voltage_source_dc' else 'A*s', source_transforms[c.id])
                               for c in ir.components if c.id in source_transforms),
                         tuple((c.id, capacitor_voltages[c.id]) for c in ir.components if c.type == 'capacitor'),
                         tuple((c.id, inductor_currents[c.id]) for c in ir.components if c.type == 'inductor'))


def _check_residuals(ir, system, values, branches, source_transforms, capacitor_voltages, inductor_currents):
    if any(sum((a*x for a, x in zip(row, values)), ZERO) != rhs for row, rhs in zip(system.matrix, system.rhs)):
        return Refusal('residual', 'laplace', 'operation', 'La soluzione non soddisfa la matrice MNA simbolica.')
    by_id = {branch.component:branch for branch in branches}
    for node in ir.nodes:
        total = sum((sign*by_id[c.id].current for c in ir.components
                     for endpoint, sign in ((c.terminals[0], 1), (c.terminals[1], -1)) if endpoint == node), ZERO)
        if total:
            return Refusal('residual', node, 'node', 'Le correnti trasformate non rispettano la legge dei nodi.')
    for c in ir.components:
        v, i = by_id[c.id].voltage, by_id[c.id].current
        valid = (v == c.value.amount*i if c.type == 'resistor' else
                 i == S*c.value.amount*v-c.value.amount*capacitor_voltages[c.id] if c.type == 'capacitor' else
                 v == S*c.value.amount*i-c.value.amount*inductor_currents[c.id] if c.type == 'inductor' else
                 v == source_transforms[c.id] if c.type == 'voltage_source_dc' else
                 i == source_transforms[c.id])
        if not valid:
            return Refusal('residual', c.id, 'component', 'La legge costitutiva non conserva la condizione iniziale dichiarata.')
    return None


def solve_laplace(ir: IR, *, source_transforms: Mapping[str, RF],
                  capacitor_voltages: Mapping[str, F],
                  inductor_currents: Mapping[str, F]) -> LaplaceSolution | Refusal:
    system = assemble_laplace(ir, source_transforms=source_transforms,
                              capacitor_voltages=capacitor_voltages, inductor_currents=inductor_currents)
    if isinstance(system, Refusal):
        return system
    try:
        values = tuple(solve_linear(system.matrix, system.rhs))
    except SingularSystemError:
        return Refusal('unsolvable', 'laplace', 'operation',
                       'La matrice è singolare nel campo Q(s): le tensioni e correnti non sono univoche.')
    named = {v.name:value for v, value in zip(system.variables, values)}
    def voltage(node):
        return ZERO if node == '0' else named[f'V({node})']
    branches = []
    for c in ir.components:
        v = voltage(c.terminals[0])-voltage(c.terminals[1])
        i = (v/c.value.amount if c.type == 'resistor' else
             S*c.value.amount*v-c.value.amount*capacitor_voltages[c.id] if c.type == 'capacitor' else
             source_transforms[c.id] if c.type == 'current_source_dc' else named[f'I({c.id})'])
        branches.append(BranchTransform(c.id, c.terminals, v, i))
    refused = _check_residuals(ir, system, values, branches, source_transforms, capacitor_voltages, inductor_currents)
    return refused if refused else LaplaceSolution(system, values, tuple(branches))
