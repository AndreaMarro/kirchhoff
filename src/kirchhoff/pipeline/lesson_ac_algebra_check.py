"""Verifica indipendente della derivazione: coppie rettangolari in Q(sqrt(3)).

Non importa l'assemblatore didattico, Cyc12 o un risolutore. Le operazioni sui
quattro razionali e le sorgenti a multipli di 30° sono ricostruite qui.
"""
from fractions import Fraction as F


ZERO = (F(0), F(0), F(0), F(0))
ONE = (F(1), F(0), F(0), F(0))


def _add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def _neg(a):
    return tuple(-x for x in a)


def _pair(a, b):
    return (a[0]*b[0]+3*a[1]*b[1], a[0]*b[1]+a[1]*b[0])


def _mul(a, b):
    rr, ii, ri, ir = _pair(a[:2], b[:2]), _pair(a[2:], b[2:]), _pair(a[:2], b[2:]), _pair(a[2:], b[:2])
    return (rr[0]-ii[0], rr[1]-ii[1], ri[0]+ir[0], ri[1]+ir[1])


def _inverse(a):
    rr, ii = _pair(a[:2], a[:2]), _pair(a[2:], a[2:])
    x, y = rr[0]+ii[0], rr[1]+ii[1]
    norm = x*x-3*y*y
    if not norm:
        raise ValueError('Divisione per zero nella derivazione.')
    den = (x/norm, -y/norm)
    return (*_pair(a[:2], den), *_pair((-a[2], -a[3]), den))


def _of(x):
    return (F(x), F(0), F(0), F(0))


def _decode(coefficients):
    if not isinstance(coefficients, list) or len(coefficients) != 4 or any(not isinstance(x, str) for x in coefficients):
        raise ValueError('Coefficienti esatti incompleti.')
    a, b, c, d = map(F, coefficients)
    return (a+c/2, b/2, d+b/2, c/2)


def _source(component):
    # Coseno/seno indipendenti dalla moltiplicazione di zeta usata nel builder.
    h = F(1, 2)
    phases = [(1,0,0,0),(0,h,h,0),(h,0,0,h),(0,0,1,0),
              (-h,0,0,h),(0,-h,h,0),(-1,0,0,0),(0,-h,-h,0),
              (-h,0,0,-h),(0,0,-1,0),(h,0,0,-h),(0,h,-h,0)]
    return tuple(F(x)*component.value.amount for x in phases[component.phase_steps % 12])


def _impedance(ir, component):
    if component.type == 'resistor':
        return _of(component.value.amount)
    x = ir.omega * component.value.amount
    return (F(0), F(0), x if component.type == 'inductor' else -1/x, F(0))


def _expression(expr, variables):
    """Vettore affine: coefficienti delle incognite e termine costante."""
    size = len(variables)
    kind = expr['kind']
    if kind == 'number':
        return [ZERO]*size + [_decode(expr['coefficients'])]
    if kind == 'symbol':
        row = [ZERO]*(size+1)
        row[variables.index(expr['name'])] = ONE
        return row
    if kind == 'add':
        result = [ZERO]*(size+1)
        for arg in expr['args']:
            result = [_add(a,b) for a,b in zip(result, _expression(arg, variables))]
        return result
    if kind == 'multiply':
        result = [ZERO]*size + [ONE]
        for arg in expr['args']:
            other = _expression(arg, variables)
            if any(x != ZERO for x in result[:-1]) and any(x != ZERO for x in other[:-1]):
                raise ValueError('Un passaggio lineare contiene un prodotto di incognite.')
            result = [_add(_mul(a, other[-1]), _mul(b, result[-1]))
                      for a,b in zip(result[:-1], other[:-1])] + [_mul(result[-1], other[-1])]
        return result
    if kind == 'divide':
        numerator, denominator = _expression(expr['numerator'], variables), _expression(expr['denominator'], variables)
        if any(x != ZERO for x in denominator[:-1]):
            raise ValueError('Il divisore dipende da un’incognita.')
        factor = _inverse(denominator[-1])
        return [_mul(x, factor) for x in numerator]
    raise ValueError('Operazione matematica sconosciuta.')


def _equation(expr, variables):
    if expr['kind'] != 'equation':
        raise ValueError('Equazione mancante.')
    left, right = _expression(expr['left'], variables), _expression(expr['right'], variables)
    result = [_add(a, _neg(b)) for a,b in zip(left, right)]
    return result[:-1] + [_neg(result[-1])]


def _physical_rows(ir, variables):
    """Ricostruisce le correnti uscenti e i vincoli ideali dall'incidenza."""
    rows = []
    for node in (n for n in ir.nodes if n != '0'):
        row = [ZERO]*(len(variables)+1)
        for c in ir.components:
            incidence = int(c.terminals[0] == node) - int(c.terminals[1] == node)
            if not incidence:
                continue
            if c.type == 'current_source_ac':
                row[-1] = _add(row[-1], _mul(_of(-incidence), _source(c)))
            elif c.type == 'voltage_source_ac':
                k = variables.index(f'I({c.id})')
                row[k] = _add(row[k], _of(incidence))
            else:
                conductance = _inverse(_impedance(ir, c))
                for node_index, candidate in enumerate(variables):
                    sign = int(candidate == f'V({c.terminals[0]})') - int(candidate == f'V({c.terminals[1]})')
                    row[node_index] = _add(row[node_index], _mul(_of(incidence*sign), conductance))
        rows.append(row)
    for c in ir.components:
        if c.type == 'voltage_source_ac':
            rows.append([_of(int(name == f'V({c.terminals[0]})') - int(name == f'V({c.terminals[1]})')) for name in variables] + [_source(c)])
    return rows


def verify_algebra(ir, proof, independent):
    """Fallisce su coefficiente, segno, riga, operazione o recupero alterati."""
    try:
        _verify(ir, proof, independent)
    except (KeyError, IndexError, TypeError, ZeroDivisionError, ValueError) as exc:
        raise ValueError(f'Derivazione algebrica non verificata: {exc}') from exc


def _verify(ir, proof, independent):
    expected_variables = ([dict(name=f'V({n})', unit='V') for n in ir.nodes if n != '0']
                          + [dict(name=f'I({c.id})', unit='A') for c in ir.components if c.type == 'voltage_source_ac'])
    if proof['schema'] != 'ac-algebra.v1' or proof['canonical_proof'] is not False or proof['variables'] != expected_variables:
        raise ValueError('Schema o incognite alterati.')
    variables = [v['name'] for v in expected_variables]
    rows = _physical_rows(ir, variables)
    if len(proof['initial']) != len(rows):
        raise ValueError('Equazioni iniziali mancanti.')
    origins = ([dict(origin='kcl', node=n, focus=[c.id for c in ir.components if n in c.terminals]) for n in ir.nodes if n != '0']
               + [dict(origin='source', component=c.id, focus=[c.id]) for c in ir.components if c.type == 'voltage_source_ac'])
    for index, (entry, row, origin) in enumerate(zip(proof['initial'], rows, origins)):
        unit = 'A' if origin['origin'] == 'kcl' else 'V'
        if (any(entry.get(key) != value for key, value in origin.items())
                or entry['label'] != f'E{index+1}'
                or any(entry[key]['unit'] != unit or entry[key]['label'] != entry['label'] for key in ('substituted', 'collected'))):
            raise ValueError('Origine, etichetta o unità dell’equazione errata.')
        if ([_decode(x) for x in entry['row']] != row
                or _equation(entry['substituted'], variables) != row
                or _equation(entry['collected'], variables) != row):
            raise ValueError('Sostituzione o raccolta dei coefficienti errata.')
    referenced_operations = [i for group in proof['groups'] for i in group['operations']]
    if (referenced_operations != list(range(len(proof['operations'])))
            or [g['variable'] for g in proof['groups']] != variables):
        raise ValueError('Una operazione non appartiene alla sequenza esposta.')
    columns = [col for col, group in enumerate(proof['groups']) for _ in group['operations']]
    units = ['A' if x['origin'] == 'kcl' else 'V' for x in origins]
    for col, op in zip(columns, proof['operations']):
        r = op['row']
        if not isinstance(r, int) or not 0 <= r < len(rows):
            raise ValueError('Riga fuori dal sistema.')
        if op['kind'] == 'swap':
            q = op['other']
            if not isinstance(q, int) or not col < q < len(rows) or r != col:
                raise ValueError('Scambio di righe non valido.')
            rows[r], rows[q] = rows[q], rows[r]
            units[r], units[q] = units[q], units[r]
            continue
        if [_decode(x) for x in op['before']] != rows[r]:
            raise ValueError('La riga di partenza non è quella del passo precedente.')
        if op['factor']['kind'] != 'number':
            raise ValueError('Fattore non numerico.')
        factor = _decode(op['factor']['coefficients'])
        if op['kind'] == 'scale':
            if factor == ZERO:
                raise ValueError('Moltiplicare una riga per zero perde equivalenza.')
            if r != col or factor != _inverse(rows[r][col]):
                raise ValueError('Il fattore non isola l’incognita dichiarata.')
            result = [_mul(factor, x) for x in rows[r]]
            units[r] = expected_variables[r]['unit']
            if len(op['normalization']) != 2:
                raise ValueError('Divisione complessa non esposta.')
            divisor = rows[r][col]
            conjugate = (*divisor[:2], -divisor[2], -divisor[3])
            ratio = op['normalization'][0]['right']
            if (ratio['kind'] != 'divide'
                    or _expression(ratio['numerator'], [])[-1] != conjugate
                    or _expression(ratio['denominator'], [])[-1] != _mul(divisor, conjugate)):
                raise ValueError('Il coniugato o il modulo quadrato del divisore è errato.')
            for identity in op['normalization']:
                if (_expression(identity['left'], [])[-1] != factor
                        or _expression(identity['right'], [])[-1] != factor):
                    raise ValueError('Razionalizzazione errata.')
        elif op['kind'] == 'eliminate':
            q = op['other']
            if not isinstance(q, int) or q != col or q == r:
                raise ValueError('Combinazione di righe non valida.')
            if factor != _neg(rows[r][col]):
                raise ValueError('Il fattore non elimina l’incognita dichiarata.')
            result = [_add(x, _mul(factor,y)) for x,y in zip(rows[r], rows[q])]
        else:
            raise ValueError('Operazione di eliminazione sconosciuta.')
        if [_decode(x) for x in op['after']] != result or _equation(op['equation'], variables) != result:
            raise ValueError('L’operazione non produce l’equazione esposta.')
        if op['equation']['unit'] != units[r] or op['equation']['label'] != f'E{r+1}':
            raise ValueError('Etichetta o unità del passo alterata.')
        rows[r] = result
    if set(proof['solution']) != set(variables):
        raise ValueError('Soluzione incompleta.')
    solved = []
    for i, row in enumerate(rows):
        if row[:-1] != [ONE if i == j else ZERO for j in range(len(variables))]:
            raise ValueError('L’eliminazione non isola tutte le incognite.')
        value = _expression(proof['solution'][variables[i]], [])[-1]
        if value != row[-1]:
            raise ValueError('Soluzione diversa dall’eliminazione.')
        solved.append(value)
    # Anche tutte le equazioni originali devono avere residuo esatto nullo.
    for row in _physical_rows(ir, variables):
        value = ZERO
        for coefficient, unknown in zip(row[:-1], solved):
            value = _add(value, _mul(coefficient, unknown))
        if value != row[-1]:
            raise ValueError('Residuo elettrico nella soluzione didattica.')
    if [b['component'] for b in proof['branches']] != [c.id for c in ir.components]:
        raise ValueError('Recupero dei rami incompleto.')
    for branch, component in zip(proof['branches'], ir.components):
        if branch['reference'] != list(component.terminals):
            raise ValueError('Riferimento di ramo alterato.')
        for quantity in ('voltage', 'current'):
            value = _expression(branch[quantity], [])[-1]
            expected = _decode([str(x) for x in independent[component.id][quantity].c])
            if value != expected:
                raise ValueError('Il recupero del ramo non coincide col tableau indipendente.')
