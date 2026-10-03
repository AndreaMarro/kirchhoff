"""Composizione vettoriale PDF delle espressioni già calcolate nella lezione.

Frazioni, radicali, pedici e numeri complessi provengono dall'AST esatto.
Questo modulo dispone glifi e linee; non risolve equazioni elettriche.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import re

from kirchhoff.pipeline.lesson_math import equation_text, signed_term


@dataclass(frozen=True)
class Box:
    width: float
    above: float
    below: float
    commands: tuple


def _text(text, size=13, font='F2'):
    # Metriche conservative dei font PDF base: nessuna ricerca di font esterni.
    width = sum(.28 if char in 'il.,: ' else .78 if char in 'MW' else .55 for char in text)*size
    return Box(width, size*.82, size*.22, (('text', 0, 0, text, size, font),))


def _shift(box, x=0, y=0):
    result = []
    for command in box.commands:
        if command[0] == 'text':
            result.append(('text', command[1]+x, command[2]+y, *command[3:]))
        else:
            result.append(('line', command[1]+x, command[2]+y, command[3]+x, command[4]+y))
    return tuple(result)


def _join(*boxes, gap=0):
    x, commands = 0, []
    for box in boxes:
        commands.extend(_shift(box, x))
        x += box.width+gap
    return Box(max(0,x-gap), max((b.above for b in boxes),default=0),
               max((b.below for b in boxes),default=0), tuple(commands))


def _fraction(top, bottom, size):
    width = max(top.width, bottom.width)+size*.45
    axis = size*.22
    top_y = axis+size*.25+top.below
    bottom_y = axis-size*.25-bottom.above
    return Box(width, top_y+top.above, -bottom_y+bottom.below,
               _shift(top,(width-top.width)/2,top_y)+_shift(bottom,(width-bottom.width)/2,bottom_y)
               + (('line',0,axis,width,axis),))


def _rational(value, size):
    if value.denominator == 1:
        return _text(str(value.numerator),size)
    return _fraction(_text(str(value.numerator),size*.85), _text(str(value.denominator),size*.85),size)


def _root3(size):
    digit = _text('3',size)
    offset = size*.62
    commands = (('line',0,size*.28,size*.15,size*.34),
                ('line',size*.15,size*.34,size*.29,-size*.05),
                ('line',size*.29,-size*.05,size*.5,size*.92),
                ('line',size*.5,size*.92,offset+digit.width,size*.92)) + _shift(digit,offset)
    return Box(offset+digit.width,size*.95,size*.22,commands)


def _real(a,b,size):
    if not b:
        return _rational(a,size)
    coefficient = _rational(abs(b),size)
    radical = _root3(size) if abs(b) == 1 else _join(coefficient,_root3(size),gap=size*.12)
    if not a:
        return _join(_text('-',size),radical) if b < 0 else radical
    return _join(_rational(a,size),_text(' - ' if b < 0 else ' + ',size),radical)


def _parentheses(box,size):
    # Parentesi alte quanto una frazione, senza appiattirne la struttura.
    height = max(size, (box.above+box.below)*.9)
    return _join(_text('(',height),box,_text(')',height),gap=size*.05)


def _number(coefficients,size):
    a,b,c,d = map(F,coefficients)
    real,imag = (a+c/2,b/2),(d+b/2,c/2)
    if not any(imag):
        return _real(*real,size)
    negative = (imag[0] < 0 and not imag[1]) or (imag[1] < 0 and not imag[0])
    imaginary = tuple(-x for x in imag) if negative else imag
    part = _real(*imaginary,size)
    if imaginary == (F(1),F(0)):
        part = _text('j',size,'F3')
    else:
        if imaginary[0] and imaginary[1]:
            part = _parentheses(part,size)
        part = _join(_text('j',size,'F3'),part,gap=size*.1)
    if any(real):
        return _join(_real(*real,size),_text(' - ' if negative else ' + ',size),part)
    return _join(_text('-',size),part) if negative else part


def _symbol(name,size):
    match = re.fullmatch(r'([A-Z])\(([^()]+)\)',name)
    if not match:
        match = re.fullmatch(r'([E])([0-9]+)',name)
    if match:
        base,sub = _text(match[1],size,'F3'),_text(match[2],size*.7,'F3')
        return Box(base.width+sub.width,max(base.above,sub.above-size*.22),max(base.below,sub.below+size*.22),
                   base.commands+_shift(sub,base.width,-size*.22))
    if name in {'ω','Ω'}:
        return _text('w' if name=='ω' else 'W',size,'F4')
    return _text(name,size,'F3')


def expression_box(expr,size=13):
    kind = expr['kind']
    if kind == 'number':
        return _number(expr['coefficients'],size)
    if kind == 'symbol':
        return _symbol(expr['name'],size)
    if kind == 'divide':
        return _fraction(expression_box(expr['numerator'],size*.92),expression_box(expr['denominator'],size*.92),size)
    if kind in {'add','multiply'}:
        args = expr['args']
        if kind=='multiply' and len(args)==2 and args[0] == dict(kind='number', coefficients=['1','0','0','0']):
            return expression_box(args[1],size)
        if kind=='multiply' and len(args)==2 and args[0] == dict(kind='number', coefficients=['-1','0','0','0']):
            child = expression_box(args[1],size)
            if args[1]['kind'] in {'add','number'}:
                child = _parentheses(child,size)
            return _join(_text('-',size),child)
        parts = []
        for i,arg in enumerate(args):
            negative,positive = signed_term(arg) if kind=='add' else (False,arg)
            if i or negative:
                parts.append(_text((' - ' if negative else ' + ') if kind=='add' else ' · ',size))
            arg = positive
            child = expression_box(arg,size)
            compound_number = False
            if arg['kind']=='number':
                a,b,c,d=map(F,arg['coefficients'])
                compound_number = bool((a+c/2 or b/2) and (d+b/2 or c/2)) or bool((a+c/2) and b)
            if kind=='multiply' and (arg['kind']=='add' or compound_number):
                child = _parentheses(child,size)
            if kind=='add' and negative and arg['kind']=='multiply' and len(arg['args'])==2 and arg['args'][0]==dict(kind='number',coefficients=['1','0','0','0']):
                nested = arg['args'][1]
                if nested['kind'] in {'add','number'}:
                    child = _parentheses(child,size)
            parts.append(child)
        return _join(*parts) if parts else _text('0' if kind=='add' else '1',size)
    raise ValueError('AST matematico non supportato dal PDF.')


def equation_boxes(expr,max_width=510,size=13):
    """Righe composte; le somme lunghe vanno a capo senza troncare termini."""
    if expr['kind'] != 'equation':
        raise ValueError('Il compositore PDF richiede una equazione.')
    label = _text(expr.get('label','')+': ',size) if expr.get('label') else _text('',size)
    left,right = expression_box(expr['left'],size),expression_box(expr['right'],size)
    unit = _join(_text(' ',size),_symbol('Ω',size) if expr.get('unit') == 'Ω' else _text(expr['unit'],size)) if expr.get('unit') else _text('',size)
    full = _join(label,left,_text(' = ',size),right,unit)
    if full.width <= max_width:
        return [full]
    # Diminuire moderatamente è utile; sotto 10pt si divide la riga.
    if size > 10:
        return equation_boxes(expr,max_width,size-1)
    pieces = [label]
    for i,arg in enumerate(expr['left'].get('args',[]) if expr['left']['kind']=='add' else [expr['left']]):
        if i:
            pieces.append(_text(' + ',size))
        pieces.append(expression_box(arg,size))
    pieces.extend([_text(' = ',size),right,unit])
    rows,current = [],[]
    for piece in pieces:
        if current and _join(*current,piece).width > max_width:
            rows.append(_join(*current))
            current=[]
        # Un singolo coefficiente eccezionalmente lungo rimane esatto; il
        # chiamante userà una scala orizzontale locale per stare nella pagina.
        current.append(piece)
    if current:
        rows.append(_join(*current))
    return rows


def draw_box(box,x,y,literal,max_width=510):
    """Comandi PDF; formula selezionabile, linee delle frazioni vettoriali."""
    scale = min(1,max_width/max(box.width,1))
    result = f'q {scale:.8f} 0 0 1 {x:.3f} {y:.3f} cm 0.14 0.20 0.29 rg 0.14 0.20 0.29 RG 0.65 w\n'
    for command in box.commands:
        if command[0]=='text':
            _,tx,ty,text,size,font = command
            result += f'BT /{font} {size:.4f} Tf 1 0 0 1 {tx:.4f} {ty:.4f} Tm ({literal(text)}) Tj ET\n'
        else:
            _,x1,y1,x2,y2 = command
            result += f'{x1:.4f} {y1:.4f} m {x2:.4f} {y2:.4f} l S\n'
    return result+'Q\n'


def actual_text(expr):
    """Testo di accessibilità coerente con la medesima espressione."""
    return 'FEFF'+equation_text(expr).encode('utf-16-be').hex().upper()
