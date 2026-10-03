"""Schemi elettrici ortogonali della lezione; gli stessi byte vanno a web e PDF.

Reti generali a due morsetti: layout dalla topologia, fili e ponticelli espliciti.
La connettività del disegno normale viene ricostruita dalle primitive SVG.
Nessuna equazione elettrica o autorità di certificazione nel renderer.
"""
from html import escape
from decimal import Decimal, localcontext
from kirchhoff.domain.ir import Request
from kirchhoff.domain.transform import EntityRef
from kirchhoff.render.layout.connected import connected_layout, lead_path, bus_path
from kirchhoff.render.serialize.connectivity import verify_connectivity
import secrets
import time


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
              norton=(), omit=(), thevenin=None, collapsed_current=(), source_labels=None):
    if ir.domain == 'laplace':
        expected = {c.id for c in ir.components if c.type in {'voltage_source_dc', 'current_source_dc'}}
        source_labels = {} if source_labels is None else source_labels
        if (not isinstance(source_labels, dict) or set(source_labels) != expected or
                any(not isinstance(label, str) or not label or len(label) > 240 for label in source_labels.values())):
            raise ValueError('Lo schema Laplace richiede etichette autorevoli per tutte le sorgenti.')
    elif source_labels is not None:
        raise ValueError('Le etichette delle sorgenti trasformate richiedono il regime Laplace.')
    pieces = []
    def line(x1, y1, x2, y2, color='#24334b', attrs=''):
        pieces.append(f'<path {attrs} d="M{x1} {y1} L{x2} {y2}" stroke="{color}" fill="none" stroke-width="2.5"/>')
    def text(x, y, value, anchor='middle', size=17, attrs=''):
        pieces.append(f'<text {attrs} x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="#24334b">{escape(str(value))}</text>')
    def node(x, y, name=''):
        pieces.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#24334b"/>')
        if name:
            text(x-9, y-10, name, 'end', 15)
    def symbol(x, y, kind, label, value, sign=1, highlight=False, off=False, audited=False):
        body = f' data-body="{escape(label, quote=True)}"' if audited else ''
        polarity = f'data-polarity="{escape(label, quote=True)}"' if audited else ''
        label_attr = 'data-label="true"' if audited else ''
        def terminal_lead(a, b):
            index = 0 if (a < y) == (sign == 1) else 1
            attrs = f'data-terminal-lead="{escape(label, quote=True)}:{index}"' if audited else ''
            line(x, a, x, b, attrs=attrs)
        color = '#294bd3' if highlight else '#24334b'
        if highlight:
            pieces.append(f'<rect x="{x-37}" y="{y-33}" width="145" height="66" rx="10" fill="#edf1ff"/>')
        if off and kind == 'voltage_source_dc':
            line(x, y-36, x, y+36)
            text(x+40, y+4, f'{label}: corto', 'start', 15)
            return
        if off and kind == 'current_source_dc':
            line(x, y-36, x, y-12); line(x, y+12, x, y+36)
            text(x+40, y+4, f'{label}: aperto', 'start', 15)
            return
        if kind == 'resistor':
            pieces.append(f'<rect{body} x="{x-11}" y="{y-30}" width="22" height="60" fill="white" stroke="{color}" stroke-width="2.5"/>')
            terminal_lead(y-36, y-30); terminal_lead(y+30, y+36)
        elif kind == 'capacitor':
            pieces.append(f'<path{body} data-symbol="capacitor" d="M{x-17} {y-10} L{x+17} {y-10} M{x-17} {y+10} L{x+17} {y+10}" stroke="{color}" fill="none" stroke-width="2.5"/>')
            terminal_lead(y-36, y-10); terminal_lead(y+10, y+36)
        elif kind == 'inductor':
            pieces.append(f'<path{body} data-symbol="inductor" d="M{x} {y-24} C{x+17} {y-24} {x+17} {y-12} {x} {y-12} C{x+17} {y-12} {x+17} {y} {x} {y} C{x+17} {y} {x+17} {y+12} {x} {y+12} C{x+17} {y+12} {x+17} {y+24} {x} {y+24}" stroke="{color}" fill="none" stroke-width="2.5"/>')
            terminal_lead(y-36, y-24); terminal_lead(y+24, y+36)
        else:
            marker = f' data-symbol="{kind}"' if kind in {'voltage_source_ac', 'current_source_ac'} else ''
            pieces.append(f'<circle{marker}{body} cx="{x}" cy="{y}" r="27" fill="white" stroke="{color}" stroke-width="2.5"/>')
            terminal_lead(y-36, y-27); terminal_lead(y+27, y+36)
            if kind == 'voltage_source_dc':
                text(x, y-6, '+' if sign == 1 else '−', size=23, attrs=polarity)
                text(x, y+21, '−' if sign == 1 else '+', size=23, attrs=polarity)
            elif kind == 'voltage_source_ac':
                text(x-15, y-8, '+' if sign == 1 else '−', size=17, attrs=polarity)
                text(x-15, y+20, '−' if sign == 1 else '+', size=17, attrs=polarity)
                text(x+6, y+7, '~', size=25)
            elif kind in {'current_source_dc', 'current_source_ac'}:
                line(x, y-16*sign, x, y+16*sign, color, f'data-direction="{escape(label, quote=True)}"' if audited else '')
                line(x, y+16*sign, x-6, y+7*sign, color)
                line(x, y+16*sign, x+6, y+7*sign, color)
            else:
                text(x, y+6, '?')
        text(x+40, y-5, label, 'start', attrs=label_attr)
        text(x+40, y+18, value, 'start', 16, attrs=label_attr)
        request = ir.requests[0] if ir.requests else None
        if isinstance(request, Request) and label == request.target:
            if request.quantity == 'voltage':
                reference_x = x-43 if 'source' in kind else x-23
                marker = f'data-request-polarity="{escape(label, quote=True)}"' if audited else ''
                text(reference_x, y-13, '+' if sign == 1 else '−', size=17, attrs=marker)
                text(reference_x, y+23, '−' if sign == 1 else '+', size=17, attrs=marker)
                text(reference_x-14, y+5, 'v', 'end', 17)
            else:
                line(x-36, y-19*sign, x-36, y+19*sign, '#294bd3', f'data-request-direction="{escape(label, quote=True)}"' if audited else '')
                line(x-36, y+19*sign, x-41, y+10*sign, '#294bd3')
                line(x-36, y+19*sign, x-31, y+10*sign, '#294bd3')
                text(x-43, y+5, 'i', 'end', 17)
    units = {'resistor':'Ω', 'capacitor':'F', 'inductor':'H',
             'voltage_source_dc':'V', 'current_source_dc':'A',
             'voltage_source_ac':'V', 'current_source_ac':'A'}
    def label_value(component):
        if source_labels is not None and component.id in source_labels:
            return source_labels[component.id]
        value = f'{value_text(component.value.amount)} {units.get(component.type, component.value.unit)}'
        if component.type in {'voltage_source_ac', 'current_source_ac'}:
            value += f' ∠ {component.phase_steps * 30}°'
        return value
    if not (reduced or active is not None or norton or omit or thevenin or collapsed_current):
        label_width = max(max(len(c.id) * 12, len(label_value(c)) * 12) for c in ir.components)
        geometry = connected_layout(ir, label_width, istante=time.time_ns() // 1_000_000,
                                    casualita=secrets.token_bytes(10))
        width, height = geometry.width, geometry.height
        for n in sorted(geometry.rows, key=geometry.rows.get):
            y = geometry.rows[n]
            lo, hi = geometry.buses[n]
            if lo != hi:
                crossing_xs = [int(geometry.layout.posizione(EntityRef('component', c.id)).x)
                               for c in ir.components if n not in c.terminals
                               and min(geometry.rows[t] for t in c.terminals) < y
                               < max(geometry.rows[t] for t in c.terminals)
                               and lo < int(geometry.layout.posizione(EntityRef('component', c.id)).x) < hi]
                path = bus_path(lo, hi, y, crossing_xs)
                pieces.append(f'<path data-wire="bus-{escape(n, quote=True)}" d="{path}" '
                              'stroke="#24334b" fill="none" stroke-width="2.5"/>')
            text(lo-15, y+5, n, 'end', 15, attrs='data-label="true"')
        for c in sorted(ir.components, key=lambda c: c.id):
            place = geometry.layout.posizione(EntityRef('component', c.id))
            x, y = int(place.x), int(place.y)
            sign = 1 if geometry.rows[c.terminals[0]] < geometry.rows[c.terminals[1]] else -1
            crossings = [row for n, row in geometry.rows.items() if n not in c.terminals
                         and geometry.buses[n][0] < x < geometry.buses[n][1]]
            for index, n in enumerate(c.terminals):
                pin_y = y + (36 if index == (0 if sign < 0 else 1) else -36)
                path = lead_path(x, pin_y, geometry.rows[n], crossings)
                pieces.append(f'<path data-wire="{escape(c.id, quote=True)}-{index}" d="{path}" '
                              'stroke="#24334b" fill="none" stroke-width="2.5"/>')
                pieces.append(f'<circle data-pin="{escape(c.id, quote=True)}:{index}" '
                              f'cx="{x}" cy="{pin_y}" r="2" fill="#24334b"/>')
            symbol(x, y, c.type, c.id, label_value(c), sign, c.id in focus, audited=True)
        for n, row in geometry.rows.items():
            xs = sorted({int(geometry.layout.posizione(EntityRef('component', c.id)).x)
                         for c in ir.components if n in c.terminals})
            for x in xs:
                if sum(n in c.terminals and int(geometry.layout.posizione(EntityRef('component', c.id)).x) == x
                       for c in ir.components) > 1 or geometry.buses[n][0] != geometry.buses[n][1]:
                    pieces.append(f'<circle data-junction="true" cx="{x}" cy="{row}" r="3.5" fill="#24334b"/>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
               'role="img" aria-label="Schema elettrico con fili connessi" '
               'style="font-family:Arial,sans-serif;background:white">' + ''.join(pieces) + '</svg>')
        verify_connectivity(svg, ir)
        return svg
    if topology is None:
        raise ValueError('Una trasformazione di ramo richiede la topologia esplicita')
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
