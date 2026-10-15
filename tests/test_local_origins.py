"""L'integrazione Ardesia ammette solo l'origine locale configurata esplicitamente."""
import http.client
import importlib.util
import json
from pathlib import Path
from threading import Thread

import pytest


@pytest.fixture
def server_module(monkeypatch):
    monkeypatch.delenv('KIRCHHOFF_ALLOWED_ORIGINS', raising=False)
    path = Path(__file__).resolve().parents[1] / 'scripts/serve_student.py'
    spec = importlib.util.spec_from_file_location('local_origin_server', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('origin', [
    '*', 'null', 'https://untrusted.example:5199', 'http://localhost.evil:5199',
    'http://user@localhost:5199', 'http://localhost:5199/', 'http://localhost:5199/path',
    'http://localhost:5199?x=1', 'http://localhost:5199#x', 'http://localhost',
    'http://127.0.0.1:0', 'http://localhost:65536', 'file://localhost:5199',
    'http://localhost:5199,', 'http://localhost:5199,http://evil.example:5199',
])
def test_configurazione_rifiuta_origini_non_esatte(server_module, monkeypatch, origin):
    monkeypatch.setenv('KIRCHHOFF_ALLOWED_ORIGINS', origin)
    with pytest.raises(ValueError):
        server_module.configured_local_origins()


def test_porta_http_viene_ammessa_solo_dopo_configurazione_esplicita(server_module, monkeypatch):
    server = server_module.ThreadingHTTPServer(('127.0.0.1', 0), server_module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    netlist = 'R1 a 0 3 ohm\nR2 a 0 6 ohm\n? resistance a 0'

    def solve(origin, host=None):
        client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
        headers = {'Content-Type': 'application/json', 'Origin': origin}
        if host:
            headers['Host'] = host
        client.request('POST', '/api/solve', json.dumps({'netlist': netlist}), headers)
        response = client.getresponse()
        data = json.loads(response.read())
        client.close()
        return response.status, data

    try:
        assert solve('http://127.0.0.1:5199')[0] == 403
        assert solve('http://localhost:43920')[0] == 200
        monkeypatch.setenv('KIRCHHOFF_ALLOWED_ORIGINS', 'http://127.0.0.1:5199')
        status, data = solve('http://127.0.0.1:5199')
        assert status == 200 and data['answer']['exact'] == '2'
        assert data['verification']['electrical_claim'] == 'PORT_SUBPROOFS_CROSSCHECKED'
        assert solve('http://localhost:5199')[0] == 403
        assert solve('http://127.0.0.1:5200')[0] == 403
        assert solve('https://untrusted.example')[0] == 403
        assert solve('http://127.0.0.1:5199', 'evil.example')[0] == 403
        monkeypatch.setenv('KIRCHHOFF_ALLOWED_ORIGINS', '*')
        assert solve('http://localhost:43920')[0] == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
