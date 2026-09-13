"""Schemi elettrici ortogonali della lezione; gli stessi byte vanno a web e PDF.

Rami a due morsetti: disposizione stabile a colonne, con giunzioni esplicite.
Altre topologie: collegamenti per etichette di rete (mai incroci inventati).
Nessuna equazione elettrica o autorità di certificazione nel renderer.
"""
from html import escape
from decimal import Decimal, localcontext


def value_text(value):
    """Decimale soltanto se finito; altrimenti la frazione resta visibile."""
    d=value.denominator
    for factor in (2,5):
        while d % factor == 0:d//=factor
    if d!=1:return str(value)
    with localcontext() as ctx:
        ctx.prec=max(30,len(str(abs(value.numerator)))+len(str(value.denominator))+3)
        return format(Decimal(value.numerator)/Decimal(value.denominator),'f')


def schematic(ir, topology=None, *, focus=(), reduced=False, active=None,
              norton=(), omit=(), thevenin=None, collapsed_current=()):
    pieces = []
    def line(x1, y1, x2, y2, color='#24334b'):
        pieces.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" fill="none" stroke-width="2.5"/>')
    def text(x, y, value, anchor='middle', size=17):
        pieces.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="#24334b">{escape(str(value))}</text>')
    def node(x, y, name=''):
        pieces.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#24334b"/>')
        if name:
            text(x-9, y-10, name, 'end', 15)
    def symbol(x, y, kind, label, value, sign=1, highlight=False, off=False):
        color = '#294bd3' if highlight else '#24334b'
        if highlight:
            pieces.append(f'<rect x="{x-37}" y="{y-42}" width="145" height="88" rx="10" fill="#edf1ff"/>')
        if off and kind == 'voltage_source_dc':
            line(x, y-36, x, y+36)
            text(x+40, y+4, f'{label}: corto', 'start', 15)
            return
        if off and kind == 'current_source_dc':
            line(x, y-36, x, y-12); line(x, y+12, x, y+36)
            text(x+40, y+4, f'{label}: aperto', 'start', 15)
            return
        if kind == 'resistor':
            pieces.append(f'<rect x="{x-11}" y="{y-30}" width="22" height="60" fill="white" stroke="{color}" stroke-width="2.5"/>')
            line(x, y-36, x, y-30); line(x, y+30, x, y+36)
        else:
            pieces.append(f'<circle cx="{x}" cy="{y}" r="27" fill="white" stroke="{color}" stroke-width="2.5"/>')
            line(x, y-36, x, y-27); line(x, y+27, x, y+36)
            if kind == 'voltage_source_dc':
                text(x, y-6, '+' if sign == 1 else '−', size=23)
                text(x, y+21, '−' if sign == 1 else '+', size=23)
            elif kind == 'current_source_dc':
                line(x, y-16*sign, x, y+16*sign, color)
                line(x, y+16*sign, x-6, y+7*sign, color)
                line(x, y+16*sign, x+6, y+7*sign, color)
            else:
                text(x, y+6, '?')
        text(x+40, y-5, label, 'start')
        text(x+40, y+18, value, 'start', 16)
        request = ir.requests[0] if ir.requests else None
        if request is not None and label == request.target:
            if request.quantity == 'voltage':
                text(x-23, y-13, '+' if sign == 1 else '−', size=17)
                text(x-23, y+23, '−' if sign == 1 else '+', size=17)
                text(x-33, y+5, 'v', 'end', 17)
            else:
                line(x-36, y-19*sign, x-36, y+19*sign, '#294bd3')
                line(x-36, y+19*sign, x-41, y+10*sign, '#294bd3')
                line(x-36, y+19*sign, x-31, y+10*sign, '#294bd3')
                text(x-43, y+5, 'i', 'end', 17)
    units = {'resistor':'Ω', 'voltage_source_dc':'V', 'current_source_dc':'A'}
    sources=[c for c in ir.components if c.type=='voltage_source_dc']
    bridge=None
    if topology is None and len(ir.nodes)==4 and len(ir.components)==6 and len(sources)==1:
        p,q=sources[0].terminals
        middle=sorted(n for n in ir.nodes if n not in (p,q))
        pairs=[(p,middle[0]),(middle[0],q),(p,middle[1]),(middle[1],q),tuple(middle)]
        resistors=[]
        for pair in pairs:
            candidates=[c for c in ir.components if c.type=='resistor' and set(c.terminals)==set(pair)]
            if len(candidates)!=1:break
            resistors.append(candidates[0])
        if len(resistors)==5:bridge=(p,q,middle,pairs,resistors)
    ladder=None
    if topology is None and len(ir.nodes)==3 and len(sources)==1 and all(c.type in {'voltage_source_dc','resistor'} for c in ir.components):
        p,q=sources[0].terminals
        m=next(n for n in ir.nodes if n not in (p,q))
        groups=[[c for c in ir.components if set(c.terminals)==set(pair)] for pair in [(p,q),(p,m),(m,q)]]
        if all(groups):ladder=(p,q,m,groups)
    if ladder:
        p,q,m,groups=ladder
        full,upper,lower=groups
        width,height=160+180*(len(full)+max(len(upper),len(lower))),460
        xmax=75+180*(len(full)+max(len(upper),len(lower))-1)
        line(75,65,xmax,65);line(75,405,xmax,405)
        text(40,70,p);text(40,410,q)
        xmid=75+180*len(full)
        line(xmid,235,xmax,235);node(xmid,235,m)
        for group,top,bottom,a,b,offset in [(full,65,405,p,q,0),(upper,65,235,p,m,len(full)),(lower,235,405,m,q,len(full))]:
            for j,c in enumerate(group):
                x=75+180*(offset+j);y=(top+bottom)/2
                node(x,top);node(x,bottom)
                line(x,top,x,y-36);line(x,y+36,x,bottom)
                symbol(x,y,c.type,c.id,f'{value_text(c.value.amount)} {units[c.type]}',1 if c.terminals==(a,b) else -1,c.id in focus)
    elif bridge:
        p,q,middle,pairs,resistors=bridge
        width,height=680,460
        line(80,55,470,55);line(80,405,470,405)
        node(80,55,p);node(80,405,q)
        source=sources[0]
        line(80,55,80,194);line(80,266,80,405)
        symbol(80,230,source.type,source.id,f'{value_text(source.value.amount)} V',highlight=source.id in focus)
        for j,(pair,c) in enumerate(zip(pairs[:4],resistors[:4])):
            x=270 if j<2 else 470
            top,bottom=(55,230) if j%2==0 else (230,405)
            y=(top+bottom)/2
            line(x,top,x,y-36);line(x,y+36,x,bottom)
            symbol(x,y,c.type,c.id,f'{value_text(c.value.amount)} Ω',1 if c.terminals==pair else -1,c.id in focus)
        node(270,230,middle[0]);node(470,230,middle[1])
        c=resistors[4]
        line(270,230,345,230);line(395,230,470,230)
        pieces.append('<rect x="345" y="219" width="50" height="22" fill="white" stroke="#24334b" stroke-width="2.5"/>')
        text(370,205,c.id);text(370,264,f'{value_text(c.value.amount)} Ω',size=16)
        request=ir.requests[0] if ir.requests else None
        if request and request.target==c.id:
            sign=1 if c.terminals==tuple(middle) else -1
            if request.quantity=='current':
                line(370-25*sign,287,370+25*sign,287,'#294bd3')
                line(370+25*sign,287,370+15*sign,281,'#294bd3')
                line(370+25*sign,287,370+15*sign,293,'#294bd3')
                text(370,315,'i',size=17)
            else:
                text(326,215,'+' if sign==1 else '−');text(414,215,'−' if sign==1 else '+')
    elif topology is None:
        width, height = 900, 70+230*((len(ir.components)+2)//3)
        text(width/2, 28, 'Etichette uguali indicano lo stesso nodo', size=17)
        for i, c in enumerate(ir.components):
            x, y = 80+300*(i % 3), 145+230*(i//3)
            line(x, y-70, x, y-36); line(x, y+36, x, y+70)
            node(x, y-70, c.terminals[0]); node(x, y+70, c.terminals[1])
            symbol(x, y, c.type, c.id, f'{value_text(c.value.amount)} {units.get(c.type, c.value.unit)}', highlight=c.id in focus)
    else:
        p, q, branches = topology
        maxparts = max(len(b.parts) for b in branches)
        bottom = 110+max(2, maxparts)*110
        width, height = max(550, 110+len(branches)*210), bottom+65
        xs = [75+i*210 for i in range(len(branches))]
        line(xs[0], 65, xs[-1], 65); line(xs[0], bottom, xs[-1], bottom)
        text(xs[0]-32, 70, p); text(xs[0]-32, bottom+5, q)
        for i, b in enumerate(branches):
            x = xs[i]
            node(x, 65); node(x, bottom)
            if thevenin:
                load, emf, resistance = thevenin
                if i == load:
                    pass
                elif i == next(j for j in range(len(branches)) if j != load):
                    line(x, 65, x, 104)
                    symbol(x, 140, 'resistor', 'Rth', f'{resistance} Ω')
                    line(x, 176, x, 214)
                    symbol(x, 250, 'voltage_source_dc', 'Vth', f'{emf} V')
                    line(x, 286, x, bottom)
                    continue
                else:
                    continue
            if any(c.id in omit for c, _ in b.parts):
                text(x, (65+bottom)/2, 'Ramo rimosso', size=15)
                continue
            if i in collapsed_current:
                source, sign = next((c,s) for c,s in b.parts if c.type == 'current_source_dc')
                y = (65+bottom)/2
                line(x,65,x,y-36);line(x,y+36,x,bottom)
                symbol(x,y,source.type,source.id,f'{value_text(source.value.amount)} A',sign)
                continue
            if i in norton:
                xl, xr, y = x-24, x+60, (65+bottom)/2
                line(xl, 65, xr, 65); line(xl, bottom, xr, bottom)
                for xx in [xl, xr]:
                    line(xx, 65, xx, y-36); line(xx, y+36, xx, bottom)
                symbol(xl, y, 'current_source_dc', '', '', -1)
                symbol(xr, y, 'resistor', '', '')
                text(x+15, 32, f'I_N{i+1} = {value_text(b.emf()/b.resistance)} A', size=14)
                text(x+15, bottom+35, f'R_N{i+1} = {value_text(b.resistance)} Ω', size=14)
                continue
            display = [(c.id, c.type, c.value.amount, s, c.terminals) for c, s in b.parts]
            if reduced and sum(c.type == 'resistor' for c, _ in b.parts) > 1:
                # Resta nello stesso ramo; i nomi consumati sono visibili.
                first = next(j for j, (_, kind, _, _, _) in enumerate(display) if kind == 'resistor')
                names = '+'.join(c.id for c, _ in b.parts if c.type == 'resistor')
                display = [(f'R_eq ({names})', 'resistor', b.resistance, 1, ('','')) if j == first else item
                           for j, item in enumerate(display) if item[1] != 'resistor' or j == first]
            spacing = (bottom-65)/len(display)
            prev = 65
            for j, (name, kind, val, sign, terminals) in enumerate(display):
                y = 65+spacing*(j+.5)
                line(x, prev, x, y-36)
                off = active is not None and kind != 'resistor' and name != active
                symbol(x, y, kind, name, f'{value_text(val)} {units.get(kind, "")}', sign, name in focus, off)
                prev = y+36
                if j+1 < len(display) and terminals[0]:
                    joint = 65+spacing*(j+1)
                    node(x, joint, terminals[1] if sign == 1 else terminals[0])
            line(x, prev, x, bottom)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="Schema elettrico" style="font-family:Arial,sans-serif;background:white">'
            + ''.join(pieces) + '</svg>')
