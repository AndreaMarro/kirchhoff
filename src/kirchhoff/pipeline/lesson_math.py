"""Espressioni matematiche portabili e una sola proiezione testuale esatta.

I renderer ricevono l'albero: non risolvono il circuito e non ricavano numeri
da stringhe destinate al lettore. La base dei numeri è Q(zeta_12).
"""
from fractions import Fraction as F

from kirchhoff.domain.exact import Cyc12


def number(value):
    """Conserva quattro coefficienti razionali, mai decimali di calcolo."""
    value = value if isinstance(value, Cyc12) else Cyc12.of(value)
    return dict(kind='number', coefficients=[str(x) for x in value.c])


def symbol(name):
    return dict(kind='symbol', name=name)


def add(*args):
    return dict(kind='add', args=list(args)) if args else number(0)


def multiply(*args):
    return dict(kind='multiply', args=list(args))


def divide(numerator, denominator):
    return dict(kind='divide', numerator=numerator, denominator=denominator)


def equation(left, right, unit='', label=''):
    return dict(kind='equation', left=left, right=right, unit=unit, label=label)


def _radical(a, b):
    if not b:
        return str(a)
    term = 'sqrt(3)' if abs(b) == 1 else f'{abs(b)} sqrt(3)'
    return (f'{a} {"−" if b < 0 else "+"} {term}' if a
            else ('−' if b < 0 else '') + term)


def readable_number(coefficients):
    """Forma rettangolare senza parti nulle, parentesi o moltiplicazioni spurie."""
    a, b, c, d = map(F, coefficients)
    real, imag = (a+c/2, b/2), (d+b/2, c/2)
    re, im = _radical(*real), _radical(*imag)
    if not any(imag):
        return re
    negative = (imag[0] < 0 and not imag[1]) or (imag[1] < 0 and not imag[0])
    if negative:
        im = _radical(-imag[0], -imag[1])
    part = 'j' if im == '1' else f'j{im}' if '/' not in im and ' ' not in im else f'j({im})'
    if any(real):
        return re + (' − ' if negative else ' + ') + part
    return ('−' if negative else '') + part


def signed_term(expr):
    """Estrae un meno esplicito, senza confrontare approssimazioni radicali."""
    if expr['kind'] == 'number':
        values = list(map(F,expr['coefficients']))
        if (values[0] < 0 and not any(values[1:])) or (values[3] < 0 and not any(values[:3])):
            return True, dict(kind='number',coefficients=[str(-x) for x in values])
    if expr['kind'] == 'multiply' and expr['args']:
        sign, args = False, []
        for arg in expr['args']:
            negative, positive = signed_term(arg)
            sign ^= negative
            args.append(positive)
        return sign, dict(kind='multiply',args=args)
    return False, expr


def expression_text(expr):
    kind = expr['kind']
    if kind == 'number':
        return readable_number(expr['coefficients'])
    if kind == 'symbol':
        return expr['name']
    if kind == 'divide':
        return f'({expression_text(expr["numerator"])}) / ({expression_text(expr["denominator"])})'
    if kind == 'multiply':
        args = expr['args']
        if len(args) == 2 and args[0] == number(1):
            return expression_text(args[1])
        if len(args) == 2 and args[0] == number(-1):
            inner = expression_text(args[1])
            if args[1]['kind'] == 'add' or (args[1]['kind'] == 'number' and (' ' in inner or inner.startswith(('-', '−')))):
                inner = '(' + inner + ')'
            return '−' + inner
        return ' · '.join('('+expression_text(x)+')' if x['kind'] in {'add', 'number'} else expression_text(x) for x in args)
    if kind == 'add':
        result = ''
        for arg in expr['args']:
            negative, positive = signed_term(arg)
            term = expression_text(positive)
            if negative and positive['kind']=='multiply' and len(positive['args'])==2 and positive['args'][0]==number(1):
                child = positive['args'][1]
                if child['kind']=='add' or (child['kind']=='number' and (' ' in term or term.startswith(('-', '−')))):
                    term = '('+term+')'
            result += (' − ' if negative else ' + ') + term if result else ('−' if negative else '') + term
        return result or '0'
    raise ValueError('Espressione matematica sconosciuta.')


def equation_text(expr):
    """Fallback condiviso per testo, vecchi client e PDF senza compositore."""
    if expr['kind'] != 'equation':
        raise ValueError('Serve un’equazione matematica.')
    label = expr.get('label', '')
    return ((label + ': ') if label else '') + expression_text(expr['left']) + ' = ' + expression_text(expr['right']) + ((' ' + expr['unit']) if expr.get('unit') else '')
