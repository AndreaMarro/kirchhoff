"""Tentativi originali e controlli ricalcolati nel PDF, senza badge importati."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import importlib.util
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
from pypdf import PdfReader

from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_pdf import export_pdf

FIXTURE = json.loads((Path(__file__).parents[1] / 'web/tests/fixtures/student-history.json').read_text())


def text_of(pdf):
    return '\n'.join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)


def test_pdf_conserva_riferimento_calcolo_correzione_e_illeggibile():
    lesson = create_lesson(FIXTURE['netlist'], source_sha='b' * 40)
    text = text_of(export_pdf(lesson, trace_history=FIXTURE['attempts']))
    for attempt in FIXTURE['attempts']:
        assert attempt['steps'][0]['transcription'] in text
    for number in range(1, 5):
        assert f'Tentativo {number}' in text
    assert 'Rivedi il riferimento' in text
    assert 'Rivedi il calcolo' in text
    assert 'Non riesco a leggere' in text
    assert 'Passaggi controllati validi' in text
    assert 'a' * 40 in text and 'b' * 40 in text
    assert 'ricalcolati' in text


@pytest.mark.parametrize('damage', ['foreign_diagnosis', 'bad_revision', 'empty_steps', 'over_budget'])
def test_pdf_rifiuta_storia_invalida_senza_pubblicare_materiale(damage):
    attempts = deepcopy(FIXTURE['attempts'])
    if damage == 'foreign_diagnosis': attempts[0]['diagnosis'] = {'outcome': 'valid_so_far'}
    elif damage == 'bad_revision': attempts[0]['engineRevision'] = 'unknown'
    elif damage == 'empty_steps': attempts[0]['steps'] = []
    else: attempts *= 9
    with pytest.raises(ValueError, match='cronologia'):
        export_pdf(create_lesson(FIXTURE['netlist']), trace_history=attempts)


def test_pdf_storia_lunga_mantiene_ultimo_operando_senza_tagli():
    attempts = deepcopy(FIXTURE['attempts'][:1])
    attempts[0]['steps'] = [deepcopy(attempts[0]['steps'][0]) for _ in range(32)]
    for step in attempts[0]['steps']: step['transcription'] = 'premessa ' * 50
    attempts[0]['steps'][-1]['transcription'] += 'ULTIMO_RIFERIMENTO'
    text = text_of(export_pdf(create_lesson(FIXTURE['netlist']), trace_history=attempts))
    assert 'ULTIMO_RIFERIMENTO' in text
    assert 'R1' in text and 'R2' in text


def test_pdf_dichiara_omissione_di_glifi_senza_indovinare_il_testo():
    attempts = deepcopy(FIXTURE['attempts'][:1])
    attempts[0]['steps'][0]['transcription'] = '記号を確認'
    text = text_of(export_pdf(create_lesson(FIXTURE['netlist']), trace_history=attempts))
    assert 'Testo non visualizzabile' in text and 'originale completo nel quaderno' in text
    assert attempts[0]['steps'][0]['transcription'] == '記号を確認'


@pytest.mark.parametrize('damage', ['foreign_circuit', 'extra_step_field', 'not_a_list', 'too_many_steps', 'large_utf8'])
def test_pdf_confini_del_contratto_condiviso(damage):
    attempts = deepcopy(FIXTURE['attempts'][:1])
    if damage == 'foreign_circuit': attempts[0]['circuitFingerprint'] = '0' * 64
    elif damage == 'extra_step_field': attempts[0]['steps'][0]['diagnosis'] = 'valid'
    elif damage == 'not_a_list': attempts = None
    elif damage == 'too_many_steps': attempts[0]['steps'] *= 33
    else:
        step = {**attempts[0]['steps'][0], 'transcription': '字' * 500, 'first': '字' * 500, 'second': '字' * 500}
        attempts = [{**attempts[0], 'steps': [step] * 32}] * 32
    if attempts is None:
        from kirchhoff.pipeline.student_history import recheck_history
        with pytest.raises(ValueError, match='cronologia'): recheck_history(FIXTURE['netlist'], attempts)
    else:
        with pytest.raises(ValueError, match='cronologia'):
            export_pdf(create_lesson(FIXTURE['netlist']), trace_history=attempts)


@pytest.fixture
def server():
    spec = importlib.util.spec_from_file_location('history_http', Path(__file__).parents[1] / 'scripts/serve_student.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    http = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try: yield f'http://127.0.0.1:{http.server_port}'
    finally:
        http.shutdown(); http.server_close(); thread.join(2)


def post(server, path, payload):
    request = Request(server + path, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    return urlopen(request)


def test_api_reale_restituisce_revisione_e_pdf_con_tentativi(server):
    attempt = FIXTURE['attempts'][0]
    with post(server, '/api/diagnose', {'netlist': FIXTURE['netlist'], 'trace': {
            'schema': 'student-trace.v1', 'circuit_fingerprint': attempt['circuitFingerprint'], 'steps': attempt['steps']}}) as response:
        diagnosis = json.load(response)
    assert diagnosis['category'] == 'reference'
    assert len(diagnosis['engine_revision']) == 40
    with post(server, '/api/pdf', {'netlist': FIXTURE['netlist'], 'trace_history': FIXTURE['attempts'],
                                  'expected_engine_revision': diagnosis['engine_revision']}) as response:
        assert response.headers['Content-Type'] == 'application/pdf'
        text = text_of(response.read())
    assert 'Tentativo 4' in text
    assert diagnosis['engine_revision'] in text


@pytest.mark.parametrize('damage', ['stale_engine', 'foreign_circuit', 'fake_diagnosis', 'null_history'])
def test_api_pdf_rifiuta_revisioni_incoerenti(server, damage):
    payload = {'netlist': FIXTURE['netlist'], 'trace_history': deepcopy(FIXTURE['attempts'])}
    if damage == 'stale_engine': payload['expected_engine_revision'] = 'unknown'
    elif damage == 'foreign_circuit': payload['trace_history'][0]['circuitFingerprint'] = '0' * 64
    elif damage == 'fake_diagnosis': payload['trace_history'][0]['diagnosis'] = {'outcome': 'valid_so_far'}
    else: payload['trace_history'] = None
    with pytest.raises(HTTPError) as error:
        post(server, '/api/pdf', payload)
    assert error.value.code == 422
    assert error.value.headers['Content-Type'] == 'application/json'
