"""Seconda aritmetica polinomiale, senza importare campo, MNA o costruttore.

Le frazioni polinomiali restano non ridotte: l'uguaglianza usa i prodotti
incrociati. Ricostruiamo le leggi dai dati d'ingresso e rigiocchiamo le righe.
"""
from fractions import Fraction as F
from kirchhoff.pipeline.lesson_math import equation_text, expression_text


def trim(p):
    p = list(p)
    while len(p) > 1 and not p[-1]:
        p.pop()
    return tuple(p)


def plus(a, b):
    return trim([(a[i] if i < len(a) else F(0))+(b[i] if i < len(b) else F(0)) for i in range(max(len(a), len(b)))])


def times(a, b):
    result = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return trim(result)


class Q:
    def __init__(self, n=(F(0),), d=(F(1),)):
        self.n, self.d = trim(n), trim(d)
        if not any(self.d):
            raise ValueError('Denominatore polinomiale nullo.')
        if not any(self.n):
            self.d = (F(1),)

    def __add__(self, other):
        if not self: return other
        if not other: return self
        if self.d == other.d: return Q(plus(self.n,other.n),self.d)
        return Q(plus(times(self.n, other.d), times(other.n, self.d)), times(self.d, other.d))

    def __neg__(self):
        return Q(tuple(-x for x in self.n), self.d)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        if not self or not other: return Q()
        return Q(times(self.n, other.n), times(self.d, other.d))

    def __truediv__(self, other):
        return Q(times(self.n, other.d), times(self.d, other.n))

    def __eq__(self, other):
        return isinstance(other, Q) and times(self.n, other.d) == times(other.n, self.d)

    def __bool__(self):
        return any(self.n)


def scalar(value):
    return Q((F(value),))


ZERO, ONE, S = scalar(0), scalar(1), Q((F(0), F(1)))


def decode(value):
    if not isinstance(value, dict) or set(value) != {'numerator', 'denominator'}:
        raise ValueError('La trasformata richiede numeratore e denominatore esatti.')
    for key in value:
        values = value[key]
        if not isinstance(values, list) or not values or any(not isinstance(x, str) or str(F(x)) != x for x in values):
            raise ValueError('Coefficienti razionali non canonici.')
        if len(values) > 1 and F(values[-1]) == 0:
            raise ValueError('Grado polinomiale non normalizzato.')
    result = Q(tuple(map(F, value['numerator'])), tuple(map(F, value['denominator'])))
    if result.d[-1] != 1:
        raise ValueError('Il denominatore deve essere monico.')
    return result


def expression(expr, context):
    kind = expr['kind']
    size = len(next(iter(context.values())))
    zero = lambda: [ZERO]*size
    constant = lambda v: [ZERO]*(size-1)+[v]
    if kind == 'number':
        coeffs = expr['coefficients']
        if len(coeffs) != 4 or any(F(c) for c in coeffs[1:]):
            raise ValueError('Laplace richiede coefficienti razionali reali.')
        return constant(scalar(coeffs[0]))
    if kind == 'symbol':
        return context[expr['name']]
    if kind == 'add':
        result = zero()
        for arg in expr['args']:
            result = [a+b for a,b in zip(result, expression(arg, context))]
        return result
    if kind in {'multiply', 'divide'}:
        args = expr['args'] if kind == 'multiply' else [expr['numerator'], expr['denominator']]
        result = constant(ONE)
        for index, arg in enumerate(args):
            value = expression(arg, context)
            if kind == 'divide' and index == 1:
                if any(value[:-1]):
                    raise ValueError('Divisore con incognite.')
                result = [a/value[-1] for a in result]
            else:
                if any(result[:-1]) and any(value[:-1]):
                    raise ValueError('Equazione non lineare nelle incognite.')
                result = [a*value[-1]+b*result[-1] for a,b in zip(result[:-1], value[:-1])]+[result[-1]*value[-1]]
        return result
    raise ValueError('Nodo matematico non ammesso.')


def residual(eq, context):
    if eq['kind'] != 'equation' or not isinstance(eq['unit'], str) or not isinstance(eq['label'], str):
        raise ValueError('Equazione priva di unità o etichetta.')
    return [a-b for a,b in zip(expression(eq['left'], context), expression(eq['right'], context))]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_laplace_algebra(parsed, proof, solved):
    """Controlla dato fisico, identità affine, operazioni e ogni ramo esposto."""
    ir, metadata = parsed.ir, parsed.to_json()
    _require(proof['schema'] == 'laplace-algebra.v1' and proof['canonical_proof'] is False, 'Stato di prova Laplace scorretto.')
    nodes = [n for n in ir.nodes if n != '0']
    currents = [c for c in ir.components if c.type in {'inductor', 'voltage_source_dc'}]
    variables = ([dict(name=f'V({n})', kind='node_voltage', target=n, unit='V*s') for n in nodes]+
                 [dict(name=f'I({c.id})', kind='branch_current', target=c.id, unit='A*s') for c in currents])
    _require(proof['variables'] == variables, 'Incognite o unità alterate.')
    names, size = [v['name'] for v in variables], len(variables)
    context = {name:[ONE if i == j else ZERO for j in range(size)]+[ZERO] for i,name in enumerate(names)}
    const = lambda q: [ZERO]*size+[q]
    context['s'] = const(S)
    caps, inds, sources = {}, {}, {}
    _require(metadata['schema'] == 'laplace-inputs.v1' and metadata['initial_time'] == '0-', 'Istante iniziale non esplicito.')
    for key, kinds, unit, prefix, dest in (('capacitor_voltages', {'capacitor'}, 'V', 'v0', caps),
                                          ('inductor_currents', {'inductor'}, 'A', 'i0', inds)):
        for entry in metadata[key]:
            _require(entry['unit'] == unit and entry['component'] not in dest, 'Condizione iniziale ripetuta o unità errata.')
            dest[entry['component']] = scalar(entry['exact'])
            context[f'{prefix}({entry["component"]})'] = const(dest[entry['component']])
        _require(set(dest) == {c.id for c in ir.components if c.type in kinds}, 'Condizioni iniziali incomplete.')
    for source in metadata['sources']:
        cid, wave = source['component'], source['waveform']
        c = ir.component(cid)
        quantity = 'voltage' if c.type == 'voltage_source_dc' else 'current'
        unit = ('V' if quantity == 'voltage' else 'A')+('*s' if wave == 'impulse' else '')
        _require(c.type in {'voltage_source_dc', 'current_source_dc'} and source['quantity'] == quantity and wave in {'step', 'impulse'} and
                 source['amplitude']['unit'] == unit and cid not in sources, 'Forma d’onda o unità della sorgente alterata.')
        value = scalar(source['amplitude']['exact'])
        sources[cid] = value/S if wave == 'step' else value
        _require(decode(source['transform']) == sources[cid], 'Trasformata della sorgente incoerente con la forma d’onda.')
    _require(set(sources) == {c.id for c in ir.components if c.type in {'voltage_source_dc','current_source_dc'}}, 'Sorgenti incomplete.')
    def voltage(c):
        p, q = c.terminals
        return [a-b for a,b in zip(context.get(f'V({p})', const(ZERO)), context.get(f'V({q})', const(ZERO)))]
    def current(c):
        v, value = voltage(c), scalar(c.value.amount)
        if c.type == 'resistor':
            return [a/value for a in v]
        if c.type == 'capacitor':
            result = [S*value*a for a in v]
            result[-1] = result[-1]-value*caps[c.id]
            return result
        return context[f'I({c.id})'] if c.type in {'inductor','voltage_source_dc'} else const(sources[c.id])
    expected = []
    for node in nodes:
        row = const(ZERO)
        for c in ir.components:
            sign = int(c.terminals[0] == node)-int(c.terminals[1] == node)
            row = [a+scalar(sign)*b for a,b in zip(row,current(c))]
        expected.append(row[:-1]+[-row[-1]])
    for c in currents:
        row = voltage(c)
        if c.type == 'voltage_source_dc':
            row[-1] = row[-1]-sources[c.id]
        else:
            row = [a-S*scalar(c.value.amount)*b for a,b in zip(row, current(c))]
            row[-1] = row[-1]+scalar(c.value.amount)*inds[c.id]
        expected.append(row[:-1]+[-row[-1]])
    _require(len(proof['initial']) == size, 'Equazioni iniziali incomplete.')
    for index, entry in enumerate(proof['initial']):
        row = list(map(decode,entry['row']))
        _require(row == expected[index], 'Coefficiente o termine noto discordante dal circuito.')
        for key in ('substituted','collected'):
            eq = entry[key]
            _require(eq['unit'] == ('A*s' if index < len(nodes) else 'V*s'), 'Unità dell’equazione iniziale alterata.')
            actual = residual(eq, context)
            _require(actual[:-1]+[-actual[-1]] == row, 'Sostituzione o raccolta matematica errata.')
    rows = [row[:] for row in expected]
    grouped = [i for group in proof['groups'] for i in group['operations']]
    _require(grouped == list(range(len(proof['operations']))) and [g['variable'] for g in proof['groups']] == names,
             'Ordine o copertura delle operazioni errati.')
    for op in proof['operations']:
        r = op['row']
        _require(type(r) is int and 0 <= r < size and list(map(decode,op['before'])) == rows[r], 'Riga precedente alterata.')
        if op['kind'] in {'swap','eliminate'}:
            other = op['other']
            _require(type(other) is int and 0 <= other < size and other != r and list(map(decode,op['donor'])) == rows[other], 'Riga donatrice alterata.')
        if op['kind'] == 'swap':
            rows[r], rows[other] = rows[other], rows[r]
            continue
        factor = decode(op['factor'])
        before = rows[r][:]
        if op['kind'] == 'scale':
            _require(bool(factor), 'Una riga non può essere moltiplicata per zero.')
            rows[r] = [factor*a for a in rows[r]]
        elif op['kind'] == 'eliminate':
            rows[r] = [a+factor*b for a,b in zip(rows[r],rows[other])]
        else:
            raise ValueError('Operazione algebrica sconosciuta.')
        after = list(map(decode,op['after']))
        _require(after == rows[r], 'Operazione non conserva l’identità polinomiale.')
        rows[r] = after  # La normalizzazione dichiarata è già stata confrontata per prodotti incrociati.
        _require(len(op['math']) == 2, 'Operazione senza equazioni matematiche.')
        for eq in op['math']:
            actual = residual(eq, context)
            _require(actual[:-1]+[-actual[-1]] == rows[r] and eq['unit'] == '', 'Equazione mostrata diversa dall’operazione.')
    _require(set(proof['solution']) == set(names), 'Soluzione incompleta.')
    values = [decode(proof['solution'][name]) for name in names]
    for i,row in enumerate(rows):
        _require(row[:-1] == [ONE if i == j else ZERO for j in range(size)] and row[-1] == values[i], 'Incognite non isolate correttamente.')
    _require([decode(v.to_json()) for v in solved.values] == values, 'Soluzione MNA e algebra discordanti.')
    solved_context = {key:const(sum_q([a*v for a,v in zip(row[:-1],values)])+row[-1]) for key,row in context.items()}
    _require(len(proof['branches']) == len(ir.components), 'Rami incompleti.')
    for c, branch in zip(ir.components, proof['branches']):
        _require(branch['component'] == c.id and branch['reference'] == list(c.terminals), 'Riferimenti del ramo alterati.')
        for quantity, affine, unit, prefix in (('voltage',voltage(c),'V*s','V'), ('current',current(c),'A*s','I')):
            value = sum_q([a*v for a,v in zip(affine[:-1],values)])+affine[-1]
            _require(expression(branch[quantity],context) == affine and decode(branch[quantity+'_value']) == value and
                     decode(getattr(solved.branch(c.id),quantity).to_json()) == value, 'Recupero di ramo discordante.')
            solved_context[f'{prefix}[{c.id}]'] = const(value)
    declarations = []
    for source in metadata['sources']:
        prefix, unit = ('V','V*s') if source['quantity'] == 'voltage' else ('I','A*s')
        declarations.append((f'{prefix}[{source["component"]}]', sources[source['component']], unit))
    declarations += [(f'v0({cid})', value, 'V') for cid,value in caps.items()]
    declarations += [(f'i0({cid})', value, 'A') for cid,value in inds.items()]
    _require(len(proof['declarations']) == len(declarations), 'Dichiarazioni incomplete.')
    for eq, (name,value,unit) in zip(proof['declarations'],declarations):
        _require(eq['left'] == dict(kind='symbol',name=name) and eq['unit'] == unit and
                 expression(eq['right'],context) == const(value), 'Dichiarazione di sorgente o stato iniziale alterata.')
    laws = []
    branch_context = dict(context)
    for c in ir.components:
        branch_context[f'V[{c.id}]'] = voltage(c)
        branch_context[f'I[{c.id}]'] = current(c)
        laws.extend([(f'V[{c.id}]', 'V*s', const(ZERO)), (f'I[{c.id}]', 'A*s', const(ZERO))])
        if c.type == 'inductor':
            row = expected[len(nodes)+currents.index(c)]
            laws.append((f'V[{c.id}]', 'V*s', row[:-1]+[-row[-1]]))
    _require(len(proof['laws']) == len(laws), 'Leggi dei rami incomplete.')
    for eq, (name,unit,row) in zip(proof['laws'],laws):
        _require(eq['left'] == dict(kind='symbol',name=name) and eq['unit'] == unit and
                 residual(eq,branch_context) == row, 'Legge di ramo alterata.')
    return solved_context


def sum_q(values):
    result = ZERO
    for value in values:
        result = result+value
    return result


def verify_laplace_presentation(parsed, proof, solved, steps, answer):
    context = verify_laplace_algebra(parsed, proof, solved)
    expected = [proof['declarations'], proof['laws']]
    expected += [[entry['substituted'],entry['collected']] for entry in proof['initial']]
    expected += [[eq for i in group['operations'] for eq in proof['operations'][i].get('math',[])] for group in proof['groups']]
    _require(len(steps) == len(expected)+3, 'Copertura dei passaggi incompleta.')
    for step, expressions in zip(steps,expected):
        _require(step['math'] == expressions, 'Passaggio mancante, scambiato o alterato.')
    isolated = steps[-3]['math']
    _require(len(isolated) == len(proof['variables']), 'Incognite isolate incomplete.')
    for eq, variable in zip(isolated, proof['variables']):
        _require(eq['left'] == dict(kind='symbol',name=variable['name']) and eq['unit'] == variable['unit'], 'Incognita o unità di soluzione alterata.')
    target = parsed.ir.component(parsed.ir.requests[0].target)
    branch = next(b for b in proof['branches'] if b['component'] == target.id)
    recovered = steps[-2]['math']
    _require(len(recovered) == 2, 'Recupero della grandezza incompleto.')
    for eq, quantity, prefix, unit in zip(recovered, ('voltage','current'), ('V','I'), ('V*s','A*s')):
        _require(eq['left'] == dict(kind='symbol',name=f'{prefix}[{target.id}]') and eq['right'] == branch[quantity] and eq['unit'] == unit,
                 'Passaggio di ritorno ai morsetti alterato.')
    last = steps[-1]['math']
    prefix = 'V' if parsed.ir.requests[0].quantity == 'voltage' else 'I'
    _require(len(last) == 1 and last[0]['left'] == dict(kind='symbol',name=f'{prefix}[{target.id}]') and
             last[0]['right'] == answer['math'] and last[0]['unit'] == answer['unit'], 'Passaggio finale discordante.')
    for step in steps:
        _require(step['equations'] == [equation_text(eq) for eq in step['math']], 'Proiezione testuale discordante.')
        for eq in step['math']:
            _require(not any(residual(eq, context)), 'Un passaggio mostrato non è un’identità.')
    req = parsed.ir.requests[0]
    target = parsed.ir.component(req.target)
    prefix, unit = ('V','V*s') if req.quantity == 'voltage' else ('I','A*s')
    _require(answer['quantity'] == req.quantity and answer['unit'] == unit and answer['reference'] == ' → '.join(target.terminals), 'Risposta o riferimento errato.')
    raw = answer['laplace_transform']
    _require(raw['variable'] == 's' and raw['coefficient_order'] == 'ascending', 'Convenzione polinomiale alterata.')
    value = decode({key:raw[key] for key in ('numerator','denominator')})
    _require(answer.get('exact', expression_text(answer['math'])) == expression_text(answer['math']) and
             answer.get('display_exact', expression_text(answer['math'])) == expression_text(answer['math']), 'Testo della risposta discordante.')
    _require(value == context[f'{prefix}[{target.id}]'][-1] and expression(answer['math'],context)[-1] == value, 'Risposta finale discordante.')
