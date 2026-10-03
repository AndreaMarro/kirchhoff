"""Independent check of the conductors actually serialized in a lesson SVG.

No layout/router import, no net attributes and no algebra.  Component/pin ids name
what must be compared; the electrical partition is reconstructed from coordinates
of paths and visible junctions.  Crossings without dots require a curved bridge.
This is a graphical check, not the product's electrical Verified certificate.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
import re
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class GraphicConnectivity:
    terminal_partition: tuple[tuple[str, ...], ...]
    wire_count: int
    geometry_sha256: str


def _point(el):
    return F(el.attrib['cx']), F(el.attrib['cy'])


def _paths(d):
    tokens = re.findall(r'[MLC]|-?(?:\d+(?:\.\d*)?|\.\d+)', d)
    if re.sub(r'[\s,]+', '', ''.join(tokens)) != re.sub(r'[\s,]+', '', d):
        raise ValueError('Geometria: comando SVG non supportato')
    result = []; position = None; i = 0
    while i < len(tokens):
        command = tokens[i]; i += 1
        count = {'M': 2, 'L': 2, 'C': 6}.get(command)
        if count is None or i + count > len(tokens):
            raise ValueError('Geometria: percorso incompleto')
        numbers = [F(x) for x in tokens[i:i+count]]; i += count
        points = tuple(zip(numbers[::2], numbers[1::2]))
        if command == 'M':
            position = points[0]
        else:
            if position is None:
                raise ValueError('Geometria: percorso senza origine')
            if position != points[-1]:
                result.append((command, (position,) + points))
            position = points[-1]
    return result


def _on_line(p, a, b):
    return ((p[0]-a[0])*(b[1]-a[1]) == (p[1]-a[1])*(b[0]-a[0])
            and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def _middle(points):
    a, b, c, d = points
    return tuple((a[i]+3*b[i]+3*c[i]+d[i])/8 for i in range(2))


def _on_segment(p, segment):
    kind, points = segment
    if kind == 'L':
        return _on_line(p, *points)
    return p in (points[0], points[-1], _middle(points))


def _box(el):
    tag = el.tag.rsplit('}', 1)[-1]
    if tag == 'rect':
        x, y, w, h = (F(el.attrib[k]) for k in ('x', 'y', 'width', 'height'))
        return x, y, x+w, y+h
    if tag == 'circle':
        (x, y), r = _point(el), F(el.attrib['r'])
        return x-r, y-r, x+r, y+r
    if tag == 'path':
        points = [p for _, ps in _paths(el.attrib['d']) for p in ps]
        return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
    if tag == 'text':
        x, y = F(el.attrib['x']), F(el.attrib['y'])
        size = F(el.attrib.get('font-size', '17'))
        w = len(el.text or '') * size * F(7, 10)
        anchor = el.attrib.get('text-anchor', 'start')
        x -= w if anchor == 'end' else w/2 if anchor == 'middle' else 0
        return x, y-size, x+w, y+size/5
    raise ValueError('Geometria: corpo non riconosciuto')


def _hits_box(segment, box):
    # Strict interior intersection of each segment's convex hull.  All routed
    # lines are axis aligned; bridges are short and outside component bands.
    _, points = segment
    a, b, c, d = box
    return (max(p[0] for p in points) > a and min(p[0] for p in points) < c
            and max(p[1] for p in points) > b and min(p[1] for p in points) < d)


def verify_connectivity(svg, ir):
    root = ET.fromstring(svg)
    elements = list(root)
    if any(e.tag.rsplit('}', 1)[-1] not in {'text', 'path', 'rect', 'circle'} for e in elements):
        raise ValueError('Geometria: primitiva non supportata')
    if any(e.get('transform') or e.get('display') == 'none' or
           e.get('visibility') == 'hidden' or e.get('opacity', '1') != '1' or
           e.get('stroke-opacity', '1') != '1' or e.get('fill-opacity', '1') != '1' or
           e.get('style') for e in elements):
        raise ValueError('Geometria: primitiva nascosta o trasformata')
    bodies = {}; pins = {}; wires = []; junctions = []
    for el in elements:
        if el.get('data-body'):
            cid = el.attrib['data-body']
            if cid in bodies:
                raise ValueError('Geometria: corpo duplicato')
            bodies[cid] = el
        if el.get('data-pin'):
            key = el.attrib['data-pin']
            if key in pins:
                raise ValueError('Geometria: morsetto duplicato')
            pins[key] = _point(el)
        if el.get('data-wire') or el.get('data-terminal-lead') or el.get('data-body') or el.get('data-direction'):
            if el.get('stroke') in (None, 'none', 'white', '#fff', '#ffffff') or F(el.get('stroke-width', '1')) < 1:
                raise ValueError('Geometria: filo o simbolo invisibile')
        if el.get('data-wire'):
            parts = _paths(el.attrib['d'])
            if not parts:
                raise ValueError('Geometria: filo vuoto')
            # Only the actual supported bridge shape is interpreted as a jump.
            for kind, ps in parts:
                if kind == 'L' and ps[0][0] != ps[-1][0] and ps[0][1] != ps[-1][1]:
                    raise ValueError('Geometria: filo non ortogonale')
                if kind == 'C':
                    a, b, c, d = ps
                    if not (a[0] == d[0] and b[0] == c[0] and a[1] == b[1]
                            and c[1] == d[1] and abs(d[1]-a[1]) == 16 and b[0]-a[0] == 12):
                        raise ValueError('Geometria: ponticello non riconosciuto')
            wires.extend(parts)
        if el.get('data-junction'):
            if el.tag.rsplit('}', 1)[-1] != 'circle' or F(el.get('r', '0')) < 2 or el.get('fill') in (None, 'none', 'white', '#fff', '#ffffff'):
                raise ValueError('Geometria: giunzione invisibile')
            junctions.append(_point(el))
    expected = {f'{c.id}:{i}': n for c in ir.components for i, n in enumerate(c.terminals)}
    if set(pins) != set(expected) or set(bodies) != {c.id for c in ir.components}:
        raise ValueError('Geometria: morsetti o componenti mancanti')
    # Pin coordinates must belong to the visible body they name. This catches a
    # moved pin even when a different wire happens to run through its new place.
    for c in ir.components:
        body = bodies[c.id]; box = _box(body)
        tag = body.tag.rsplit('}', 1)[-1]
        expected_tag = 'rect' if c.type == 'resistor' else 'path' if c.type in {'capacitor', 'inductor'} else 'circle'
        sizes = {'resistor': (22, 60), 'capacitor': (34, 20), 'inductor': (17, 48)}
        if (box[2]-box[0], box[3]-box[1]) != sizes.get(c.type, (54, 54)):
            raise ValueError('Geometria: forma del simbolo alterata')
        if tag != expected_tag:
            raise ValueError('Geometria: simbolo non coerente')
        x = F(body.get('cx')) if tag == 'circle' else (box[0]+box[2])/2 if tag == 'rect' or c.type == 'capacitor' else box[0]
        y = (box[1]+box[3])/2
        p0, p1 = pins[f'{c.id}:0'], pins[f'{c.id}:1']
        if {p0, p1} != {(x, y-36), (x, y+36)}:
            raise ValueError('Geometria: morsetto separato dal simbolo')
        for index, pin in enumerate((p0, p1)):
            leads = [el for el in elements if el.get('data-terminal-lead') == f'{c.id}:{index}']
            edge_y = box[1] if pin[1] < y else box[3]
            if len(leads) != 1 or _paths(leads[0].attrib['d']) not in (
                    [('L', (pin, (x, edge_y)))], [('L', ((x, edge_y), pin))]):
                raise ValueError('Geometria: reoforo interrotto')
        if c.type.startswith('voltage_source'):
            marks = [el for el in elements if el.get('data-polarity') == c.id]
            if any(el.get('fill') in (None, 'none', 'white', '#fff', '#ffffff') for el in marks):
                raise ValueError('Geometria: polarità invisibile')
            plus = [F(el.attrib['y']) for el in marks if el.text == '+']
            minus = [F(el.attrib['y']) for el in marks if el.text in ('−', '-')]
            if len(plus) != 1 or len(minus) != 1 or (plus[0] < minus[0]) != (p0[1] < p1[1]):
                raise ValueError('Geometria: polarità invertita o mancante')
        for role in ('data-direction', 'data-request-direction'):
            arrows = [el for el in elements if el.get(role) == c.id]
            if role == 'data-direction' and c.type.startswith('current_source') and len(arrows) != 1:
                raise ValueError('Geometria: freccia di corrente mancante')
            for arrow in arrows:
                parts = _paths(arrow.attrib['d'])
                if len(parts) != 1 or (parts[0][1][-1][1] > parts[0][1][0][1]) != (p1[1] > p0[1]):
                    raise ValueError('Geometria: verso di corrente invertito')
                tip = parts[0][1][-1]
                heads = [ps for el in elements if el.tag.endswith('path') and el is not arrow
                         and not el.get('data-wire') for kind, ps in _paths(el.attrib['d'])
                         if kind == 'L' and ps[0] == tip and ps[-1][0] != tip[0]
                         and (ps[-1][1] < tip[1]) == (p1[1] > p0[1])]
                if len(heads) != 2:
                    raise ValueError('Geometria: punta di corrente incoerente')
    obstacles = [_box(el) for el in bodies.values()] + [_box(el) for el in elements if el.get('data-label')]
    if any(_hits_box(wire, box) for wire in wires for box in obstacles):
        raise ValueError('Geometria: filo coperto da simbolo o testo')
    parent = list(range(len(wires)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(a, b):
        parent[find(a)] = find(b)
    # A curved overpass and the two collinear ends of its visible underpass
    # gap express a crossing, not a junction. Infer the continuation solely
    # from these actual coordinates. Missing ends or an unbroken underpass fail.
    for kind, ps in wires:
        if kind != 'C':
            continue
        mx, my = _middle(ps)
        ends = ((mx-4, my), (mx+4, my))
        sides = [[i for i, (k, points) in enumerate(wires)
                  if k == 'L' and points[0][1] == points[1][1] == my
                  and end in points] for end in ends]
        if (any(len(side) != 1 for side in sides) or sides[0] == sides[1]
                or any(_on_line((mx, my), *points) for k, points in wires if k == 'L')):
            raise ValueError('Geometria: ponticello senza interruzione visibile del sottopasso')
        union(sides[0][0], sides[1][0])
    for i, a in enumerate(wires):
        for j, b in enumerate(wires[:i]):
            contacts = {p for p in (a[1][0], a[1][-1], b[1][0], b[1][-1])
                        if _on_segment(p, a) and _on_segment(p, b)}
            contacts.update(p for p in junctions if _on_segment(p, a) and _on_segment(p, b))
            if contacts:
                union(i, j)
            elif a[0] == b[0] == 'L':
                pa, qa = a[1]; pb, qb = b[1]
                # A straight interior crossing has no unambiguous drawing convention.
                cross = (pa[0], pb[1]) if pa[0] == qa[0] else (pb[0], pa[1])
                if _on_line(cross, pa, qa) and _on_line(cross, pb, qb):
                    raise ValueError('Geometria: incrocio senza ponticello o giunzione')
    for p in junctions:
        if sum(_on_segment(p, wire) for wire in wires) < 2:
            raise ValueError('Geometria: giunzione non sostenuta dai fili')
    groups = {}
    for key, p in pins.items():
        touching = [i for i, wire in enumerate(wires) if _on_segment(p, wire)]
        if not touching:
            raise ValueError('Geometria: morsetto senza filo')
        roots = {find(i) for i in touching}
        if len(roots) != 1:
            raise ValueError('Geometria: morsetto ambiguo')
        groups.setdefault(next(iter(roots)), []).append(key)
    actual = tuple(sorted(tuple(sorted(v)) for v in groups.values()))
    wanted = tuple(sorted(tuple(sorted(k for k, node in expected.items() if node == n)) for n in set(expected.values())))
    if actual != wanted:
        raise ValueError('Geometria: partizione dei terminali diversa dal circuito')
    return GraphicConnectivity(actual, len(wires), sha256(svg.encode()).hexdigest())
