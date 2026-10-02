"""Lezioni su circuiti reali e varianti: oracolo esatto, segni e rifiuti."""
from fractions import Fraction as F
from pathlib import Path
import importlib.util
import json
import random
import xml.etree.ElementTree as ET
import pytest
import http.client
from threading import Thread
from kirchhoff.pipeline.lesson import create_lesson, branches, observed, potential
from kirchhoff.pipeline.capabilities import product_capabilities
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.domain.ir import Component
from kirchhoff.pipeline.lesson_bridge import _verifica_tre_morsetti

TWO='V1 1 0 31/5 volt\nR1 1 2 13/10 ohm\nR2 2 0 11/10 ohm\nV2 3 0 18/5 volt\nR3 3 2 16/5 ohm\n? current R2'
DIVIDER='V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2'
BRIDGE='V1 c 0 12 volt\nR1 c a 10 ohm\nR2 c b 20 ohm\nR3 a 0 30 ohm\nR4 b 0 40 ohm\nRg a b 50 ohm\n? current R4'


@pytest.mark.parametrize('netlist,answer,branch_equation',[
    ('V1 a 0 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? current R1', '3', '(10 - (4)) / (2) = 3 A'),
    ('V1 a 0 10 volt\nR1 a b 2 ohm\nV2 0 b 4 volt\n? current R1', '7', '(10 - (-4)) / (2) = 7 A'),
    ('V1 0 a 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? current R1', '-7', '(-10 - (4)) / (2) = -7 A'),
    ('V1 a 0 10 volt\nR1 b a 2 ohm\nV2 b 0 4 volt\n? current R1', '-3', '(10 - (4)) / (2) = 3 A'),
    ('V1 a 0 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? voltage R1', '6', '(10 - (4)) / (2) = 3 A'),
])
def test_f01_ideal_source_with_second_emf_never_prints_a_false_divider(netlist,answer,branch_equation):
    lesson=create_lesson(netlist)
    equations=[equation for step in lesson['steps'] for equation in step['equations']]
    assert lesson['answer']['exact']==answer
    assert lesson['method']=='millman'
    assert any(branch_equation in equation for equation in equations)
    assert all('I ramo 2 = (10) / (2) = 3 A' not in equation for equation in equations)
    pdf=export_pdf(lesson).replace(b'\\(',b'(').replace(b'\\)',b')')
    assert branch_equation.encode() in pdf


@pytest.mark.parametrize('part',['equation','diagram'])
def test_f01_corrupt_intermediate_is_not_published_with_correct_final_answer(monkeypatch,part):
    import kirchhoff.pipeline.lesson as lesson_module
    original=lesson_module._step
    def damaged(title,explanation,svg,equations=None,focus=None):
        step=original(title,explanation,svg,equations,focus)
        if title=='La tensione è già imposta':
            if part=='equation':step['equations'][-1]='I ramo 2 = (10 - (4)) / (2) = 999 A'
            else:step['svg']=step['svg'].replace('>V2<','>V9<')
        return step
    monkeypatch.setattr(lesson_module,'_step',damaged)
    with pytest.raises(ValueError,match='passaggio intermedio'):
        create_lesson('V1 a 0 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? current R1')


def test_thevenin_open_port_error_is_blocked_even_when_final_answer_stays_correct(monkeypatch):
    import kirchhoff.pipeline.lesson as lesson_module
    original = lesson_module.potential
    branch_count = len(branches(leggi(TWO))[2])

    def damaged(bs, active=None):
        voltage, currents = original(bs, active)
        return (voltage + 1, currents) if len(bs) == branch_count - 1 else (voltage, currents)

    monkeypatch.setattr(lesson_module, 'potential', damaged)
    with pytest.raises(ValueError, match='Thévenin|vuoto'):
        create_lesson(TWO, 'thevenin')


def test_thevenin_seen_resistance_is_checked_at_the_port():
    from kirchhoff.pipeline.lesson import _verify_thevenin_port
    ir = leggi('V1 a 0 12 volt\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2')
    with pytest.raises(ValueError, match='resistenza vista di Thévenin'):
        _verify_thevenin_port(ir, 'R2', 'a', '0', F(12), F(1))
    _verify_thevenin_port(ir, 'R2', 'a', '0', F(12), F(0))


@pytest.mark.parametrize('corruption', ['other_branch_current', 'port_voltage'])
def test_human_lesson_rejects_wrong_intermediate_with_correct_requested_answer(monkeypatch, corruption):
    import kirchhoff.pipeline.lesson as lesson_module
    net = DIVIDER.replace('? voltage R2', '? current V1')
    original = lesson_module.potential
    off_target = next(i for i, branch in enumerate(branches(leggi(net))[2])
                      if any(c.id == 'R2' for c, _ in branch.parts))

    def damaged(bs, active=None):
        voltage, currents = original(bs, active)
        if active is not None:
            return voltage, currents
        if corruption == 'port_voltage':
            return voltage + 1, currents
        altered = currents.copy()
        altered[off_target] += 1
        return voltage, altered

    monkeypatch.setattr(lesson_module, 'potential', damaged)
    with pytest.raises(ValueError, match='passaggio intermedio'):
        create_lesson(net)


@pytest.mark.parametrize('net,title', [
    (DIVIDER, 'Usiamo il partitore, senza un sistema di equazioni'),
    ('I1 0 a 2 ampere\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2', 'Il partitore di corrente'),
])
@pytest.mark.parametrize('part', ['equation', 'diagram'])
def test_divider_rejects_corrupt_displayed_step_with_correct_answer(monkeypatch, net, title, part):
    import kirchhoff.pipeline.lesson as lesson_module
    original = lesson_module._step

    def damaged(step_title, explanation, svg, equations=None, focus=None):
        step = original(step_title, explanation, svg, equations, focus)
        if step_title == title:
            if part == 'equation':
                step['equations'][-1] = 'I ramo = 999 A'
            else:
                step['svg'] += '<schema-estraneo/>'
        return step

    monkeypatch.setattr(lesson_module, '_step', damaged)
    with pytest.raises(ValueError, match='passaggio intermedio'):
        create_lesson(net)


def test_divider_prints_reversed_resistor_voltage_in_its_declared_orientation():
    net = 'V1 p 0 12 volt\nR1 p q 4 ohm\nR2 0 q 6 ohm\n? voltage R2'
    lesson = create_lesson(net)
    assert lesson['method'] == 'divider'
    assert lesson['answer']['exact'] == '-36/5'
    step = next(s for s in lesson['steps'] if s['title'] == 'Usiamo il partitore, senza un sistema di equazioni')
    assert any(e.startswith('V(R2) = (-1) × (6/5) × (6) = -36/5 V') for e in step['equations'])
    assert b'V(R2) = (-1) ' in export_pdf(lesson).replace(b'\\(', b'(').replace(b'\\)', b')')


@pytest.mark.parametrize('net,answer,title', [
    ('I1 0 a 2 ampere\nV1 a 0 0 volt\nR1 a 0 6 ohm\n? current R1', '0', 'La tensione è già imposta'),
    ('I1 0 a 2 ampere\nV1 b a 0 volt\nR1 b 0 6 ohm\nR2 a 0 3 ohm\n? voltage R2', '4', 'Tensione comune: il teorema di Millman'),
])
def test_zero_volt_source_is_not_treated_as_a_current_divider(net, answer, title):
    lesson = create_lesson(net)
    assert lesson['method'] == 'millman'
    assert lesson['answer']['exact'] == answer
    assert any(step['title'] == title for step in lesson['steps'])
    assert not any(step['title'] == 'Il partitore di corrente' for step in lesson['steps'])


@pytest.mark.parametrize('method',['auto','millman','norton','thevenin','superposition','nodal'])
def test_same_real_problem_all_methods(method):
    lesson=create_lesson(TWO,method)
    assert lesson['answer']['exact']=='2452/911'
    assert lesson['verification']['product_verified'] is False
    assert lesson['steps'][0]['svg']==lesson['original']
    assert 'circuito originale' in lesson['steps'][-1]['title']
    for step in lesson['steps']:
        assert len(step['explanation'])>80
        assert ET.fromstring(step['svg']).tag.endswith('svg')
    pdf=export_pdf(lesson)
    assert pdf.startswith(b'%PDF-1.4') and pdf.endswith(b'%%EOF\n')
    assert pdf.count(b'/Type /Page ')>=len(lesson['steps'])
    assert b'2452/911' in pdf
    # Byte identici a input e versione uguali (nessun timestamp nel documento).
    assert export_pdf(create_lesson(TWO,method))==pdf


def test_superposition_sources_are_off_in_other_branch_and_rejoined():
    lesson=create_lesson(TWO,'superposition')
    split=[s for s in lesson['steps'] if s['title'].startswith('Lasciamo')]
    assert len(split)==2
    assert 'V2: corto' in split[0]['svg']
    assert 'V1: corto' in split[1]['svg']
    assert '2452/911' in lesson['steps'][-2]['equations'][0]


def test_superposition_rejects_compensating_wrong_intermediate_contributions(monkeypatch):
    import kirchhoff.pipeline.lesson as lesson_module
    original = lesson_module.observed

    def damaged(bs, target, quantity, active=None):
        value = original(bs, target, quantity, active)
        return value + (F(1) if active == 'V1' else -F(1)) if active else value

    monkeypatch.setattr(lesson_module, 'observed', damaged)
    with pytest.raises(ValueError, match='sovrapposizione|contributo'):
        create_lesson(TWO, 'superposition')


def test_superposition_rejects_wrong_subcircuit_voltage_even_with_right_target(monkeypatch):
    import kirchhoff.pipeline.lesson as lesson_module
    original = lesson_module.potential

    def damaged(bs, active=None):
        voltage, currents = original(bs, active)
        return (voltage + 1, currents) if active == 'V1' else (voltage, currents)

    monkeypatch.setattr(lesson_module, 'potential', damaged)
    with pytest.raises(ValueError, match='sovrapposizione|tensione'):
        create_lesson(TWO, 'superposition')


def test_random_millman_and_load_thevenin_match_independent_formula():
    rng=random.Random(713)
    for _ in range(30):
        r1,r2,r3=[F(rng.randrange(1,20),rng.randrange(1,8)) for _ in range(3)]
        v1,v2=[F(rng.randrange(-15,16)) for _ in range(2)]
        net=f'V1 a 0 {v1} volt\nR1 a b {r1} ohm\nV2 c 0 {v2} volt\nR3 c b {r3} ohm\nR2 b 0 {r2} ohm\n? voltage R2'
        expected=(v1/r1+v2/r3)/(1/r1+1/r2+1/r3)
        for method in ['millman','thevenin','norton','superposition']:
            lesson=create_lesson(net,method)
            assert F(lesson['answer']['exact'])==expected
        reverse=net.replace(f'R2 b 0 {r2}',f'R2 0 b {r2}')
        assert F(create_lesson(reverse)['answer']['exact'])==-expected


@pytest.mark.parametrize('net,expected',[
    (DIVIDER,'33/4'),
    (DIVIDER.replace('? voltage R2','? current V1'),'-3/80'),
    ('I1 0 a 2 ampere\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2','2/3'),
    ('I1 a b 2 ampere\nR1 b 0 3 ohm\nR2 a 0 6 ohm\n? voltage I1','-18'),
    ('V1 a 0 12 volt\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current V1','-6'),
])
def test_source_constraints_and_orientation(net,expected):
    for method in ['auto','norton','superposition','nodal']:
        if method == 'norton' and method not in create_lesson(net)['available']:
            with pytest.raises(ValueError,match='applicabile'):create_lesson(net,method)
            continue
        lesson=create_lesson(net,method)
        assert lesson['answer']['exact']==expected


def test_general_topology_stays_honest_and_reuses_actual_equations():
    lesson=create_lesson(BRIDGE,'nodal')
    assert lesson['method']=='nodal'
    assert 'millman' not in lesson['available']
    assert any(s['equations'] for s in lesson['steps'][1:-1])
    assert 'Etichette uguali' not in lesson['original']
    assert '>Rg<' in lesson['original']
    with pytest.raises(ValueError,match='topologia'):create_lesson(BRIDGE,'millman')


@pytest.mark.parametrize('text,match',[
    ('','vuota'),('R1 a 0 3 ohm','domanda'),(DIVIDER+'\n? current R2','domanda'),
    ('V1 a 0 12 volt\nR1 a 0 0 ohm\n? current R1','positiv'),
    ('x'*16001,'lungo'),
])
def test_invalid_input_never_returns_a_lesson(text,match):
    with pytest.raises(ValueError,match=match):create_lesson(text)


def test_unsupported_reactive_returns_refusal_not_fake_dc_solution():
    r=create_lesson('V1 b 0 12 volt\nR1 b a 100 ohm\nC1 a 0 1/1000 farad\n? voltage R1')
    assert r['outcome']=='refusal'
    assert 'answer' not in r
    with pytest.raises(ValueError):export_pdf(r)


def test_unknown_method_and_mismatched_crosscheck_stop(monkeypatch):
    with pytest.raises(ValueError,match='sconosciuto'):create_lesson(TWO,'fantasy')
    monkeypatch.setattr('kirchhoff.pipeline.lesson.observed',lambda *a:F(999))
    with pytest.raises(ValueError,match='non coincide'):create_lesson(TWO)


def test_renderer_escapes_names_and_marks_open_current_source():
    text='I1 0 a 1 ampere\nI2 0 a 2 ampere\nR<script> a 0 6 ohm\n? voltage R<script>'
    r=create_lesson(text,'superposition')
    assert '<script>' not in r['original'] and '&lt;script&gt;' in r['original']
    assert any('aperto' in s['svg'] for s in r['steps'])


def test_exporter_continues_long_explanations_without_clipping():
    lesson=create_lesson(DIVIDER)
    lesson['steps'][0]['explanation']='Questo è un passaggio da spiegare. '*300
    pdf=export_pdf(lesson)
    assert pdf.count(b'/Type /Page ')>len(lesson['steps'])


def test_canonical_refusal_on_missing_target_and_parallel_ideal_sources():
    with pytest.raises(ValueError,match='inesistente'):
        create_lesson(DIVIDER.replace('? voltage R2','? voltage R9'))
    text='V1 a 0 12 volt\nV2 a 0 6 volt\nR1 a 0 6 ohm\n? current R1'
    assert create_lesson(text)['outcome']=='refusal'


def test_recognition_unconfigured_or_remote_url_cannot_make_a_network_request():
    path=Path(__file__).resolve().parents[1]/'scripts/serve_student.py'
    spec=importlib.util.spec_from_file_location('student_server',path)
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    with pytest.raises(ValueError,match='configurato'):server.recognize('data:image/png;base64,AAAA',None,None)
    with pytest.raises(ValueError,match='PNG'):server.recognize('https://example.org/image','not-a-real-key','model')


def test_catalog_is_generated_from_the_same_entrypoint():
    root=Path(__file__).resolve().parents[1]/'web/public/lessons'
    for example in json.loads((root/'index.json').read_text()):
        for method,name in example['methods'].items():
            saved=json.loads((root/(name+'.json')).read_text())
            assert saved==create_lesson(example['netlist'],method,saved['source_sha'])
            assert (root/(name+'.pdf')).read_bytes()==export_pdf(saved)


def test_ideal_source_pruning_respects_requested_internal_quantity():
    text='V1 a 0 12 volt\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2'
    lesson=create_lesson(text)
    removed=[s for s in lesson['steps'] if 'irrilevante' in s['title']]
    assert len(removed)==1 and '>R1<' not in removed[0]['svg'] and '>R2<' in removed[0]['svg']
    generator=create_lesson(text.replace('? current R2','? current V1'))
    assert not any('irrilevante' in s['title'] for s in generator['steps'])
    series='I1 a b 2 ampere\nR1 b 0 3 ohm\nR2 a 0 6 ohm\n? voltage R2'
    lesson=create_lesson(series)
    reduced=[s for s in lesson['steps'] if 'dettagli interni' in s['title']]
    assert len(reduced)==1 and '>R1<' not in reduced[0]['svg']
    requested=create_lesson(series.replace('? voltage R2','? voltage I1'))
    assert not any('dettagli interni' in s['title'] for s in requested['steps'])


def test_bridge_star_delta_path_and_internal_observation_guard():
    for target in ['R1','R2','R3','R4','V1']:
        for quantity in ['voltage','current']:
            text=BRIDGE.replace('? current R4',f'? {quantity} {target}')
            transformed=create_lesson(text,'star_delta')
            canonical=create_lesson(text,'nodal')
            assert transformed['answer']==canonical['answer']
            assert len(transformed['steps'])==5
            assert all('Etichette uguali' not in s['svg'] for s in transformed['steps'])
    diagonal=BRIDGE.replace('? current R4','? current Rg')
    assert create_lesson(diagonal)['method']=='nodal'
    with pytest.raises(ValueError,match='topologia'):create_lesson(diagonal,'star_delta')


def test_bridge_numeric_variants_keep_exact_values_and_polarity():
    rng=random.Random(480)
    for _ in range(12):
        rs=[F(rng.randrange(1,40),rng.randrange(1,6)) for _ in range(5)]
        voltage=F(rng.randrange(-15,16))
        text=f'V1 c 0 {voltage} volt\nR1 c a {rs[0]} ohm\nR2 c b {rs[1]} ohm\nR3 a 0 {rs[2]} ohm\nR4 b 0 {rs[3]} ohm\nRg a b {rs[4]} ohm\n? current R4'
        assert create_lesson(text,'star_delta')['answer']==create_lesson(text,'nodal')['answer']


@pytest.mark.parametrize('part',['equation','diagram'])
def test_bridge_corrupt_intermediate_is_not_published_with_correct_final_answer(monkeypatch,part):
    import kirchhoff.pipeline.lesson as lesson_module
    original=lesson_module._step
    def damaged(title,explanation,svg,equations=None,focus=None):
        step=original(title,explanation,svg,equations,focus)
        if title=='Trasformiamo la stella in un triangolo':
            if part=='equation':step['equations'][0]='Rdelta = 999 Ω'
            else:step['svg']=step['svg'].replace('Rdelta01','Rdelta99')
        return step
    monkeypatch.setattr(lesson_module,'_step',damaged)
    with pytest.raises(ValueError,match='passaggio intermedio'):
        create_lesson(BRIDGE,'star_delta')


def test_star_delta_checks_all_three_ports_not_just_the_requested_answer():
    legs={node:Component.of('R'+node,'resistor',('x',node),value,'R'+node)
          for node,value in [('a',F(2)),('b',F(3)),('c',F(5))]}
    delta=[Component.of('Dab','resistor',('a','b'),F(31,5),'Dab'),
           Component.of('Dac','resistor',('a','c'),F(31,3),'Dac'),
           Component.of('Dbc','resistor',('b','c'),F(31,2),'Dbc')]
    _verifica_tre_morsetti(legs,('a','b','c'),delta)
    delta[2]=Component.of('Dbc','resistor',('b','c'),F(16),'Dbc')
    with pytest.raises(ValueError,match='tre morsetti'):
        _verifica_tre_morsetti(legs,('a','b','c'),delta)


def test_http_new_circuit_pdf_and_origin_boundary(monkeypatch):
    path=Path(__file__).resolve().parents[1]/'scripts/serve_student.py'
    spec=importlib.util.spec_from_file_location('http_student_server',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    server=module.ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    def send(method,path,payload=None,origin=None):
        client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        client.request(method,path,json.dumps(payload) if payload is not None else None,headers)
        response=client.getresponse();data=response.read();status=response.status;client.close()
        return status,data
    try:
        status,data=send('GET','/api/capabilities');assert status==200
        capabilities=json.loads(data)
        assert {key:value for key,value in capabilities.items() if key!='examples'} == product_capabilities()
        text=DIVIDER.replace('12 volt','10 volt')
        status,data=send('POST','/api/solve',dict(netlist=text));assert status==200
        assert json.loads(data)['answer']['exact']=='55/8'
        status,data=send('POST','/api/pdf',dict(netlist=text));assert status==200 and data.startswith(b'%PDF')
        f01='V1 a 0 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? current R1'
        status,data=send('POST','/api/solve',dict(netlist=f01));assert status==200
        served=json.loads(data)
        assert served['method']=='millman' and served['answer']['exact']=='3'
        assert any('(10 - (4)) / (2) = 3 A' in equation
                   for step in served['steps'] for equation in step['equations'])
        status,data=send('POST','/api/pdf',dict(netlist=f01));assert status==200
        assert b'(10 - (4)) / (2) = 3 A' in data.replace(b'\\(',b'(').replace(b'\\)',b')')
        ac='@ac 100 rad/s\nV1 a 0 10 volt 30deg\nR1 a 0 3 ohm\n? current R1'
        status,data=send('POST','/api/solve',dict(netlist=ac));assert status==200
        assert json.loads(data)['outcome']=='refusal'
        assert capabilities['ac'] is False
        assert send('POST','/api/solve',dict(netlist=text),'https://untrusted.example')[0]==403
        assert send('POST','/api/solve',dict(netlist='broken'))[0]==422
        assert send('POST','/api/pdf',dict(netlist='broken'))[0]==422
        assert send('POST','/api/recognize',dict(image='data:image/png;base64,AAAA'))[0]==422
        assert send('GET','/%2e%2e/pyproject.toml')[0]==404
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


def test_thevenin_explains_open_voltage_then_deactivates_sources_separately():
    lesson=create_lesson(TWO,'thevenin')
    voltage=next(s for s in lesson['steps'] if 'tensione a vuoto' in s['title'])
    resistance=next(s for s in lesson['steps'] if 'resistenza vista' in s['title'])
    assert lesson['steps'].index(voltage)<lesson['steps'].index(resistance)
    assert 'corto' not in voltage['svg']
    assert resistance['svg'].count(': corto')==2
    assert 'Ramo rimosso' in voltage['svg'] and 'Ramo rimosso' in resistance['svg']
    assert any('1/(13/10)' in e and '1/(16/5)' in e for e in resistance['equations'])
    assert any('= 208/225 Ω' in e for e in resistance['equations'])
    pdf=export_pdf(lesson)
    assert b'IL PERCORSO DEL RAGIONAMENTO' in pdf
    assert b'/BaseFont /Times-Roman' in pdf
    assert pdf.count(b'/Type /Page ')==len(lesson['steps'])+1


def test_thevenin_open_current_source_and_zero_resistance_voltage_source():
    current=create_lesson('I1 0 a 2 ampere\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2','thevenin')
    step=next(s for s in current['steps'] if 'resistenza vista' in s['title'])
    assert 'I1: aperto' in step['svg']
    assert any('= 3 Ω' in e for e in step['equations'])
    voltage=create_lesson('V1 a 0 12 volt\nR1 a 0 3 ohm\nR2 a 0 6 ohm\n? current R2','thevenin')
    step=next(s for s in voltage['steps'] if 'resistenza vista' in s['title'])
    assert step['equations']==['Rth = 0 Ω']
    assert 'V1: corto' in step['svg']
    assert voltage['answer']['exact']=='2'
