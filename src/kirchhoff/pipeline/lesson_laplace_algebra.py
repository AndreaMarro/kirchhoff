"""Algebra osservabile in Q(s): sostituzioni, eliminazione e riferimenti originali."""
from kirchhoff.domain.laplace_rational import RationalFunction as RF, ZERO, ONE, S
from kirchhoff.pipeline.lesson_math import add, multiply, divide, number, symbol, equation


def polynomial_math(coefficients):
    terms = []
    for degree, coefficient in enumerate(coefficients):
        if not coefficient:
            continue
        factors = [symbol('s') for _ in range(degree)]
        if coefficient != 1 or not factors:
            factors.insert(0, number(coefficient))
        terms.append(factors[0] if len(factors) == 1 else multiply(*factors))
    return terms[0] if len(terms) == 1 else add(*terms)


def rational_math(value):
    numerator = polynomial_math(value.numerator)
    return numerator if value.denominator == (1,) else divide(numerator, polynomial_math(value.denominator))


def potential(node):
    return number(0) if node == '0' else symbol(f'V({node})')


def drop(component):
    p, q = component.terminals
    return add(potential(p), multiply(number(-1), potential(q)))


def branch_current(component, inputs):
    cid, value = component.id, component.value.amount
    if component.type == 'resistor':
        return divide(drop(component), number(value))
    if component.type == 'capacitor':
        return add(multiply(symbol('s'), number(value), drop(component)),
                   multiply(number(-value), symbol(f'v0({cid})')))
    if component.type in {'inductor', 'voltage_source_dc'}:
        return symbol(f'I({cid})')
    return rational_math(inputs['source_transforms'][cid])


def row_equation(row, names, unit='', label=''):
    terms = [multiply(rational_math(a), symbol(name)) for a, name in zip(row[:-1], names) if a]
    return equation(add(*terms), rational_math(row[-1]), unit, label)


def build_laplace_algebra(parsed, solved):
    ir, inputs, system = parsed.ir, parsed.solver_inputs, solved.system
    names = [v.name for v in system.variables]
    rows = [list(row)+[rhs] for row, rhs in zip(system.matrix, system.rhs)]
    wire = lambda row: [value.to_json() for value in row]
    initial, declarations, laws = [], [], []
    for source in parsed.sources:
        prefix, unit = ('V', 'V*s') if source.quantity == 'voltage' else ('I', 'A*s')
        declarations.append(equation(symbol(f'{prefix}[{source.component}]'), rational_math(source.transform), unit))
    for values, prefix, unit in ((parsed.capacitor_voltages, 'v0', 'V'), (parsed.inductor_currents, 'i0', 'A')):
        declarations.extend(equation(symbol(f'{prefix}({cid})'), number(value), unit) for cid, value in values)
    for c in ir.components:
        laws.append(equation(symbol(f'V[{c.id}]'), drop(c), 'V*s'))
        laws.append(equation(symbol(f'I[{c.id}]'), branch_current(c, inputs), 'A*s'))
        if c.type == 'inductor':
            laws.append(equation(symbol(f'V[{c.id}]'), add(multiply(symbol('s'), number(c.value.amount), symbol(f'I({c.id})')),
                                multiply(number(-c.value.amount), symbol(f'i0({c.id})'))), 'V*s'))
    for index, label in enumerate(system.row_labels):
        if label.startswith('KCL('):
            node = label[4:-1]
            terms = [multiply(number(sign), branch_current(c, inputs)) for c in ir.components
                     for endpoint, sign in ((c.terminals[0], 1), (c.terminals[1], -1)) if endpoint == node]
            expr = equation(add(*terms), number(0), 'A*s', label)
            focus = [c.id for c in ir.components if node in c.terminals]
        else:
            c = ir.component(label[4:-1])
            right = (rational_math(inputs['source_transforms'][c.id]) if c.type == 'voltage_source_dc' else
                     add(multiply(symbol('s'), number(c.value.amount), symbol(f'I({c.id})')),
                         multiply(number(-c.value.amount), symbol(f'i0({c.id})'))))
            expr = equation(drop(c), right, 'V*s', label)
            focus = [c.id]
        initial.append(dict(row=wire(rows[index]), substituted=expr,
                            collected=row_equation(rows[index], names, expr['unit'], label), focus=focus))
    operations, groups = [], []
    for column in range(len(names)):
        indices = []
        pivot = next((r for r in range(column, len(rows)) if rows[r][column]), None)
        if pivot is None:
            raise ValueError('L’algebra Laplace incontra un sistema singolare.')
        if pivot != column:
            indices.append(len(operations))
            operations.append(dict(kind='swap', row=column, other=pivot, before=wire(rows[column]), donor=wire(rows[pivot])))
            rows[column], rows[pivot] = rows[pivot], rows[column]
        before, factor = rows[column][:], ONE/rows[column][column]
        rows[column] = [factor*a for a in before]
        indices.append(len(operations))
        old = row_equation(before, names)
        operations.append(dict(kind='scale', row=column, factor=factor.to_json(), before=wire(before), after=wire(rows[column]),
                               math=[equation(multiply(rational_math(factor), old['left']), multiply(rational_math(factor), old['right'])),
                                     row_equation(rows[column], names)]))
        for row in range(len(rows)):
            if row == column or not rows[row][column]:
                continue
            before, donor, factor = rows[row][:], rows[column][:], -rows[row][column]
            rows[row] = [a+factor*b for a, b in zip(before, donor)]
            left, right = row_equation(before, names), row_equation(donor, names)
            indices.append(len(operations))
            operations.append(dict(kind='eliminate', row=row, other=column, factor=factor.to_json(), before=wire(before),
                                   donor=wire(donor), after=wire(rows[row]),
                                   math=[equation(add(left['left'], multiply(rational_math(factor), right['left'])),
                                                  add(left['right'], multiply(rational_math(factor), right['right']))),
                                         row_equation(rows[row], names)]))
        groups.append(dict(variable=names[column], operations=indices))
    branches = [dict(component=c.id, reference=list(c.terminals), voltage=drop(c), current=branch_current(c, inputs),
                     voltage_value=solved.branch(c.id).voltage.to_json(), current_value=solved.branch(c.id).current.to_json())
                for c in ir.components]
    return dict(schema='laplace-algebra.v1', canonical_proof=False, variables=[v.to_json() for v in system.variables],
                declarations=declarations, laws=laws, initial=initial, operations=operations, groups=groups,
                solution={name:rows[i][-1].to_json() for i, name in enumerate(names)}, branches=branches)
