"""Generated public graphs and destructive mutations of the delivered SVG.

The checker has no access to the layout or routing objects, only IR + SVG bytes.
The private textbook regression is kept outside this repository.
"""
from fractions import Fraction as F
import random
import xml.etree.ElementTree as ET

import pytest

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.lesson_svg import schematic
from kirchhoff.pipeline.lesson_pdf import _drawing
from kirchhoff.render.serialize.connectivity import verify_connectivity

PUBLIC = {
    'divider': 'V1 p 0 12 volt\nR1 p m 4 ohm\nR2 m 0 8 ohm\n? voltage R2',
    'bridge': 'V1 p 0 9 volt\nR1 p a 2 ohm\nR2 a 0 3 ohm\nR3 p b 5 ohm\nR4 b 0 7 ohm\nR5 a b 11 ohm\n? current R5',
    'parallel': 'V1 a 0 6 volt\nR1 a 0 2 ohm\nR2 a 0 3 ohm\nI1 0 a 1 ampere\n? current R1',
    'rlc_mesh': '@ac 20 rad/s\nV1 0 a 9 volt 30deg\nR1 a b 2 ohm\nL1 b 0 1/5 henry\nC1 a c 1/100 farad\nR2 c 0 4 ohm\nI1 b c 2 ampere -60deg\n? voltage R2',
    'floating_source': '@ac 10 rad/s\nV1 a b 8 volt 0deg\nR1 a 0 2 ohm\nR2 b c 3 ohm\nL1 c 0 1/10 henry\nC1 a c 1/20 farad\n? current R1',
}


def mutate(svg, fn):
    root = ET.fromstring(svg)
    fn(root)
    return ET.tostring(root, encoding='unicode')


def select(root, key, value=None):
    return next(e for e in root if e.get(key) and (value is None or e.get(key) == value))


@pytest.mark.parametrize('name', PUBLIC)
def test_general_topologies_have_actual_wires_and_stable_focus(name):
    ir = leggi(PUBLIC[name]); svg = schematic(ir)
    certificate = verify_connectivity(svg, ir)
    assert len(certificate.terminal_partition) == len(ir.nodes)
    assert certificate.wire_count >= 2 * len(ir.components)
    assert 'Etichette uguali' not in svg and svg == schematic(ir)
    focused = schematic(ir, focus=(ir.components[-1].id,))
    def positions(text):
        return [(e.get('data-wire'), e.get('d'), e.get('data-pin'), e.get('cx'), e.get('cy'))
                for e in ET.fromstring(text) if e.get('data-wire') or e.get('data-pin')]
    assert positions(svg) == positions(focused)
    verify_connectivity(focused, ir)
    # The same actual paths must survive the PDF projection, including bridges.
    drawing, _ = _drawing(svg)
    assert drawing.count('\nS\n') == sum(e.tag.endswith('path') for e in ET.fromstring(svg))


@pytest.mark.parametrize('seed', range(24))
def test_generated_graphs_independent_of_component_input_order(seed):
    rng = random.Random(seed); count = rng.randrange(3, 10)
    nodes = ('0',) + tuple(f'n{i}' for i in range(1, count))
    pairs = {(nodes[i], nodes[i-1]) for i in range(1, count)}
    for _ in range(count * 2):
        a, b = rng.sample(nodes, 2)
        pairs.add(tuple(sorted((a, b))))
    components = [Component.of(f'R{i}', 'resistor', pair, F(i+1), f'R{i}')
                  for i, pair in enumerate(sorted(pairs))]
    components.append(Component.of('V1', 'voltage_source_dc', ('n1', '0'), F(12), 'V1'))
    ir = IR('1.0.0', 'dc', 'generated', nodes, tuple(components), (Request('q', 'voltage', 'R0'),))
    svg = schematic(ir); verify_connectivity(svg, ir)
    rng.shuffle(components)
    reordered = IR('1.0.0', 'dc', 'generated', tuple(reversed(nodes)), tuple(components), ir.requests)
    assert schematic(reordered) == svg


@pytest.fixture
def bridge():
    ir = leggi(PUBLIC['bridge'])
    return ir, schematic(ir)


def test_net_metadata_is_not_an_oracle(bridge):
    ir, svg = bridge
    def change(root):
        for e in root:
            e.set('data-net', 'deliberately-wrong')
            if e.tag.endswith('text') and e.text in ir.nodes:
                e.text = 'x'
    assert verify_connectivity(mutate(svg, change), ir).terminal_partition == verify_connectivity(svg, ir).terminal_partition


def test_removing_conductor_breaks_partition(bridge):
    ir, svg = bridge
    with pytest.raises(ValueError, match='morsetto|partizione|giunzione'):
        verify_connectivity(mutate(svg, lambda root: root.remove(select(root, 'data-wire', 'R1-0'))), ir)


def test_moving_conductor_breaks_even_with_unchanged_net_metadata(bridge):
    ir, svg = bridge
    def move(root):
        wire = select(root, 'data-wire', 'R1-0')
        tokens = wire.attrib['d'].split()
        x = tokens[0][1:]
        wire.set('d', wire.attrib['d'].replace(f'M{x} ', f'M{int(x)+8} ').replace(f'L{x} ', f'L{int(x)+8} '))
    with pytest.raises(ValueError, match='morsetto|partizione|giunzione'):
        verify_connectivity(mutate(svg, move), ir)


def test_false_junction_on_bridge_merges_two_nets(bridge):
    ir, svg = bridge
    def join(root):
        wire = next(e for e in root if e.get('data-wire') and ' C' in e.get('d', ''))
        curve = wire.attrib['d'].split(' C')[1].split(' L')[0].split()
        x, y0, _, y1, _, _ = map(F, curve)
        # At t=1/2 the visible bridge is 9 units right of its straight lead.
        ET.SubElement(root, 'circle', {'data-junction': 'true', 'cx': str(x-3),
                                     'cy': str((y0+y1)/2), 'r': '3.5', 'fill': '#24334b'})
    with pytest.raises(ValueError, match='partizione|giunzione'):
        verify_connectivity(mutate(svg, join), ir)


def test_pin_moved_to_a_different_existing_wire_is_rejected(bridge):
    ir, svg = bridge
    def move(root):
        pin = select(root, 'data-pin', 'R1:0')
        pin.set('cy', str(F(pin.attrib['cy'])-39))
    with pytest.raises(ValueError, match='morsetto separato'):
        verify_connectivity(mutate(svg, move), ir)


def test_polarity_flip_is_rejected_with_identical_topological_partition(bridge):
    ir, svg = bridge
    def flip(root):
        for e in root:
            if e.get('data-polarity') == 'V1':
                e.text = '−' if e.text == '+' else '+'
    with pytest.raises(ValueError, match='polarità'):
        verify_connectivity(mutate(svg, flip), ir)


def test_current_arrow_flip_is_rejected():
    ir = leggi(PUBLIC['parallel']); svg = schematic(ir)
    def flip(root):
        arrow = select(root, 'data-direction', 'I1')
        m, l = arrow.attrib['d'].split(' L')
        arrow.set('d', f'M{l} L{m[1:]}')
    with pytest.raises(ValueError, match='verso'):
        verify_connectivity(mutate(svg, flip), ir)


def test_wire_hidden_under_existing_symbol_is_rejected(bridge):
    ir, svg = bridge
    def cover(root):
        pin = select(root, 'data-pin', 'R1:0'); x, y = F(pin.attrib['cx']), F(pin.attrib['cy'])
        wire = select(root, 'data-wire', 'R1-0')
        # Same endpoints as before, but a detour through the resistor body.
        wire.set('d', f'M{x} {y} L{x} {y+60} L{x+4} {y+60} L{x+4} {y} L{x} {y}' + wire.attrib['d'][len(f'M{x} {y}'):])
    with pytest.raises(ValueError, match='coperto'):
        verify_connectivity(mutate(svg, cover), ir)


def test_body_lead_removal_is_rejected(bridge):
    ir, svg = bridge
    with pytest.raises(ValueError, match='reoforo'):
        verify_connectivity(mutate(svg, lambda r: r.remove(select(r, 'data-terminal-lead', 'R1:0'))), ir)


def test_controlled_component_has_explicit_renderer_limit():
    ir = leggi('V1 a 0 4 volt\nE1 b 0 a 0 2\nR1 b 0 3 ohm\n? voltage R1')
    with pytest.raises(ValueError, match='non ancora supportato'):
        schematic(ir)


def test_bridge_requires_visible_underpass_gap(bridge):
    ir, svg = bridge
    def close_gap(root):
        bus = next(e for e in root if e.get('data-wire', '').startswith('bus-') and ' M' in e.get('d', ''))
        bus.set('d', bus.attrib['d'].replace(' M', ' L'))
    with pytest.raises(ValueError, match='sottopasso'):
        verify_connectivity(mutate(svg, close_gap), ir)


@pytest.mark.parametrize('kind,source,domain', [
    ('voltage_source_ac', 'V1', 'ac_sinusoidal'), ('current_source_ac', 'I1', 'ac_sinusoidal'),
    ('voltage_source_dc', 'V1', 'dc'), ('current_source_dc', 'I1', 'dc'),
])
@pytest.mark.parametrize('reverse', [False, True])
def test_requested_voltage_markers_stay_outside_source_symbol(kind, source, domain, reverse):
    terminals = ('0', 'a') if reverse else ('a', '0')
    ir = IR('1.0.0', domain, 'generated', ('0', 'a'), (
        Component.of(source, kind, terminals, F(4), source),
        Component.of('R1', 'resistor', ('a', '0'), F(2), 'R1'),
    ), (Request('q', 'voltage', source),), omega=F(2) if domain == 'ac_sinusoidal' else F(1))
    root = ET.fromstring(schematic(ir)); body = select(root, 'data-body', source)
    markers = [e for e in root if e.get('data-request-polarity') == source]
    assert len(markers) == 2
    assert all(F(e.attrib['x'])+9 < F(body.attrib['cx'])-F(body.attrib['r']) for e in markers)
    plus = next(e for e in markers if e.text == '+')
    minus = next(e for e in markers if e.text == '−')
    assert (F(plus.attrib['y']) > F(minus.attrib['y'])) == reverse
