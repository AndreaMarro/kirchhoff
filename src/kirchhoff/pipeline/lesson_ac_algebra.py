"""Dalle sostituzioni di Kirchhoff a un'eliminazione esatta leggibile.

La traccia non è un ProofGraph canonico. Un verificatore separato ricostruisce
le equazioni fisiche e controlla ogni operazione prima dell'esposizione.
"""
from copy import deepcopy

from kirchhoff.domain.exact import Cyc12, J, ONE, ZERO, SingularSystemError, zeta_pow
from kirchhoff.pipeline.lesson_math import add, divide, equation, multiply, number, symbol


def impedance(ir, component):
    if component.type == 'resistor':
        return Cyc12.of(component.value.amount)
    if component.type == 'inductor':
        return J * ir.omega * component.value.amount
    return ONE / (J * ir.omega * component.value.amount)


def _potential(node):
    return number(0) if node == '0' else symbol(f'V({node})')


def _drop(component):
    first, second = component.terminals
    return add(_potential(first), multiply(number(-1), _potential(second)))


def _packed(row):
    return [[str(x) for x in value.c] for value in row]


def row_equation(row, variables, unit, label):
    return equation(add(*(multiply(number(coefficient), symbol(variable['name']))
                          for coefficient, variable in zip(row[:-1], variables) if coefficient)),
                    number(row[-1]), unit, label)


def build_algebra(ir):
    """Costruisce sostituzioni, righe raccolte e Gauss-Jordan con fattori esatti."""
    nodes = [node for node in ir.nodes if node != '0']
    sources = [c for c in ir.components if c.type == 'voltage_source_ac']
    variables = ([dict(name=f'V({node})', unit='V') for node in nodes]
                 + [dict(name=f'I({c.id})', unit='A') for c in sources])
    position = {variable['name']: i for i, variable in enumerate(variables)}
    size = len(variables)
    rows, initial, units = [], [], []
    for node in nodes:
        row, terms = [ZERO] * (size + 1), []
        for c in ir.components:
            first, second = c.terminals
            if node not in c.terminals:
                continue
            sign = 1 if first == node else -1
            if c.type in {'resistor', 'inductor', 'capacitor'}:
                z = impedance(ir, c)
                terms.append(multiply(number(sign), divide(_drop(c), number(z))))
                for terminal, orientation in ((first, 1), (second, -1)):
                    if terminal != '0':
                        row[position[f'V({terminal})']] += sign * orientation / z
            elif c.type == 'voltage_source_ac':
                terms.append(multiply(number(sign), symbol(f'I({c.id})')))
                row[position[f'I({c.id})']] += sign
            else:
                value = c.value.amount * zeta_pow(c.phase_steps)
                terms.append(multiply(number(sign), number(value)))
                row[-1] -= sign * value
        label = f'E{len(rows)+1}'
        initial.append(dict(label=label, origin='kcl', node=node,
                            focus=[c.id for c in ir.components if node in c.terminals],
                            substituted=equation(add(*terms), number(0), 'A', label),
                            collected=row_equation(row, variables, 'A', label), row=_packed(row)))
        rows.append(row)
        units.append('A')
    for c in sources:
        row = [ZERO] * (size + 1)
        for terminal, sign in zip(c.terminals, (1, -1)):
            if terminal != '0':
                row[position[f'V({terminal})']] += sign
        row[-1] = c.value.amount * zeta_pow(c.phase_steps)
        label = f'E{len(rows)+1}'
        initial.append(dict(label=label, origin='source', component=c.id, focus=[c.id],
                            substituted=equation(_drop(c), number(row[-1]), 'V', label),
                            collected=row_equation(row, variables, 'V', label), row=_packed(row)))
        rows.append(row)
        units.append('V')

    # Ogni gruppo mantiene le righe identificate: niente matrice muta fra due
    # schermate. La preferenza per la riga più corta evita lavoro superfluo.
    operations, groups = [], []
    for col in range(size):
        candidates = [i for i in range(col, size) if rows[i][col]]
        if not candidates:
            raise SingularSystemError('Sistema didattico singolare.')
        pivot = min(candidates, key=lambda i: sum(bool(x) for x in rows[i][:-1]))
        group = dict(variable=variables[col]['name'], operations=[])
        if pivot != col:
            op = dict(kind='swap', row=col, other=pivot)
            rows[col], rows[pivot] = rows[pivot], rows[col]
            units[col], units[pivot] = units[pivot], units[col]
            operations.append(op)
            group['operations'].append(len(operations)-1)
        factor = ONE / rows[col][col]
        before = rows[col][:]
        rows[col] = [x * factor for x in rows[col]]
        units[col] = variables[col]['unit']
        op = dict(kind='scale', row=col, factor=number(factor), before=_packed(before), after=_packed(rows[col]),
                  equation=row_equation(rows[col], variables, units[col], f'E{col+1}'))
        divisor = before[col]
        conjugate, norm = divisor.conjugate(), divisor * divisor.conjugate()
        op['normalization'] = [
            equation(divide(number(1), number(divisor)), divide(number(conjugate), number(norm))),
            equation(divide(number(conjugate), number(norm)), number(factor)),
        ]
        operations.append(op)
        group['operations'].append(len(operations)-1)
        for r in range(size):
            if r == col or not rows[r][col]:
                continue
            factor, before = -rows[r][col], rows[r][:]
            rows[r] = [a + factor*b for a, b in zip(rows[r], rows[col])]
            op = dict(kind='eliminate', row=r, other=col, factor=number(factor),
                      before=_packed(before), after=_packed(rows[r]),
                      equation=row_equation(rows[r], variables, units[r], f'E{r+1}'))
            operations.append(op)
            group['operations'].append(len(operations)-1)
        groups.append(group)
    solution = {v['name']: number(rows[i][-1]) for i, v in enumerate(variables)}
    branches = []
    for c in ir.components:
        first, second = c.terminals
        voltage = add(solution.get(f'V({first})', number(0)),
                      multiply(number(-1), solution.get(f'V({second})', number(0))))
        if c.type in {'resistor', 'inductor', 'capacitor'}:
            current = divide(voltage, number(impedance(ir, c)))
        elif c.type == 'voltage_source_ac':
            current = deepcopy(solution[f'I({c.id})'])
        else:
            current = number(c.value.amount * zeta_pow(c.phase_steps))
        branches.append(dict(component=c.id, reference=[first, second], voltage=voltage, current=current))
    return dict(schema='ac-algebra.v1', canonical_proof=False, variables=variables,
                initial=initial, operations=operations, groups=groups, solution=solution, branches=branches)
