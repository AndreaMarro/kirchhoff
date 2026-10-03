"""La wheel contiene l'App effettiva e serve MCP senza un checkout web.

Lo SHA zero è un oracolo congelato esclusivamente della fixture di build: non
identifica una release. Non si scaricano SDK o dipendenze durante questi test.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

import pytest

from kirchhoff.api import app_resource


ROOT = Path(__file__).resolve().parents[1]


def _copy_assets(directory):
    sources = json.loads((ROOT / 'web/dist/mcp/build-manifest.json').read_text())['sources']
    paths = (*sources, 'web/dist/mcp/kirchhoff-mcp-app.iife.js',
             'web/dist/mcp/build-manifest.json')
    for relative in paths:
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def test_built_resource_is_self_contained_and_bound_to_its_actual_sources():
    html, manifest = app_resource.compose_app(ROOT)
    assert '/* KIRCHHOFF_MCP_APP_BUNDLE */' not in html
    assert 'tools/call' in html and 'ui/initialize' in html
    assert '<script src=' not in html
    assert manifest['html_sha256'] == hashlib.sha256(html.encode()).hexdigest()
    assert app_resource.validate_packaged_app(html, manifest) == html


@pytest.mark.parametrize('changed', ['source', 'bundle', 'missing', 'schema', 'sources', 'outside', 'marker'])
def test_build_refuses_stale_missing_or_untrusted_assets(tmp_path, changed):
    _copy_assets(tmp_path)
    manifest_path = tmp_path / 'web/dist/mcp/build-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if changed == 'source':
        (tmp_path / 'web/src/mcp-app.ts').write_text('// sorgente cambiato')
    elif changed == 'bundle':
        (tmp_path / 'web/dist/mcp/kirchhoff-mcp-app.iife.js').write_text('// bundle cambiato')
    elif changed == 'missing':
        manifest_path.unlink()
    else:
        if changed == 'schema':
            manifest['schema'] = 'inventato'
        elif changed == 'sources':
            manifest['sources'] = {}
        elif changed == 'outside':
            manifest['sources']['../outside'] = 'a' * 64
        else:
            template = tmp_path / 'web/mcp-app-template.html'
            template.write_text('<html></html>')
            manifest['sources']['web/mcp-app-template.html'] = hashlib.sha256(template.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        app_resource.compose_app(tmp_path)


def test_installed_app_refuses_modified_html():
    html, manifest = app_resource.compose_app(ROOT)
    with pytest.raises(ValueError, match='installata'):
        app_resource.validate_packaged_app(html + '<script>extra</script>', manifest)


def test_unbuilt_checkout_preserves_headless_mcp_tools(monkeypatch):
    pytest.importorskip('mcp')
    from kirchhoff.api.mcp_server import build_server
    monkeypatch.setattr(app_resource, 'compose_app', lambda _: (_ for _ in ()).throw(ValueError('bundle assente')))
    assert 'Gli strumenti MCP restano disponibili' in app_resource.load_app_html()
    assert build_server() is not None


def test_wheel_and_sdist_install_app_without_checkout_or_runtime_git(tmp_path):
    pytest.importorskip('mcp')
    project, dist, installed = tmp_path / 'source', tmp_path / 'dist', tmp_path / 'installed'
    project.mkdir()
    _copy_assets(project)
    shutil.copytree(ROOT / 'src', project / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('pyproject.toml', 'hatch_build.py'):
        shutil.copyfile(ROOT / name, project / name)
    # Metadato della sola fixture: nessuna attribuzione al checkout sporco.
    env = dict(os.environ, KIRCHHOFF_SOURCE_SHA='0' * 40, UV_OFFLINE='1')
    build = subprocess.run(['uv', 'build', '--offline', '--out-dir', str(dist), str(project)],
                           env=env, text=True, capture_output=True, timeout=90)
    assert build.returncode == 0, build.stdout + build.stderr
    wheel = next(dist.glob('*.whl'))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert 'kirchhoff/api/resources/circuit-lesson.html' in names
        assert 'kirchhoff/api/resources/circuit-lesson.manifest.json' in names
        assert archive.read('kirchhoff/_build_source_sha.txt').strip() == b'0' * 40
    with tarfile.open(next(dist.glob('*.tar.gz'))) as archive:
        assert any(name.endswith('/src/kirchhoff/api/resources/circuit-lesson.html') for name in archive.getnames())
    install = subprocess.run(['uv', 'pip', 'install', '--offline', '--no-deps', '--target', str(installed), str(wheel)],
                             env=env, text=True, capture_output=True, timeout=30)
    assert install.returncode == 0, install.stdout + install.stderr
    code = '''
import asyncio, json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import kirchhoff
from mcp import Client
from kirchhoff.api.mcp_server import APP_URI, build_server
assert pathlib.Path(kirchhoff.__file__).is_relative_to(pathlib.Path(sys.argv[1]))
async def run():
    async with Client(build_server()) as client:
        resource = await client.read_resource(APP_URI)
        html = resource.contents[0].text
        assert 'ui/initialize' in html and 'tools/call' in html
        assert resource.contents[0].mime_type == 'text/html;profile=mcp-app'
        netlist = '@ac 100 rad/s\\nV1 a 0 10 volt 30deg\\nR1 a b 3 ohm\\nL1 b 0 1/25 henry\\n? current R1'
        solved = await client.call_tool('solve_circuit', {'netlist': netlist})
        assert not solved.is_error
        lesson = solved.structured_content
        assert lesson['outcome'] == 'solved'
        assert lesson['source_sha'] == '0' * 40
        assert lesson['verification']['electrical_claim'] == 'PHASOR_PATHS_CROSSCHECKED'
        print(json.dumps({'app_bytes': len(html), 'outcome': lesson['outcome'], 'revision': 'frozen-build-fixture'}))
asyncio.run(run())
'''
    runtime_env = dict(os.environ)
    runtime_env.pop('KIRCHHOFF_SOURCE_SHA', None)
    result = subprocess.run([sys.executable, '-c', code, str(installed)], cwd=tmp_path,
                            env=runtime_env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['app_bytes'] > 100000
