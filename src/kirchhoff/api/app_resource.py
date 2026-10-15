"""Risorsa MCP App portabile: asset reali, provenienza e caricamento senza Git."""
from __future__ import annotations

import hashlib
from importlib import resources
import json
from pathlib import Path
import re

HTML_NAME = 'circuit-lesson.html'
MANIFEST_NAME = 'circuit-lesson.manifest.json'
BUILD_SCHEMA = 'kirchhoff-mcp-app-build.v1'
REQUIRED_SOURCES = frozenset({
    'web/mcp-app-template.html', 'web/src/mcp-app.ts', 'web/src/student/safeSvg.ts',
    'web/package.json', 'web/package-lock.json', 'web/vite.mcp.config.ts',
})


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compose_app(root: Path) -> tuple[str, dict]:
    """Compone solo un bundle compilato dagli stessi sorgenti del checkout."""
    directory = root / 'web/dist/mcp'
    try:
        bundle = (directory / 'kirchhoff-mcp-app.iife.js').read_bytes()
        manifest = json.loads((directory / 'build-manifest.json').read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError('MCP App non compilata: esegui npm run build in web/.') from exc
    if not isinstance(manifest, dict) or manifest.get('schema') != BUILD_SCHEMA:
        raise ValueError('Manifest della MCP App non riconosciuto.')
    sources = manifest.get('sources')
    if not isinstance(sources, dict) or not REQUIRED_SOURCES <= sources.keys():
        raise ValueError('Manifest della MCP App senza i sorgenti necessari.')
    for relative, digest in sources.items():
        source = (root / relative).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file():
            raise ValueError('Manifest della MCP App con sorgente assente o fuori progetto.')
        if _hash(source.read_bytes()) != digest:
            raise ValueError(f'MCP App non aggiornata rispetto a {relative}: ricompila web/.')
    if not bundle or manifest.get('bundle_sha256') != _hash(bundle):
        raise ValueError('Il bundle della MCP App non coincide con il manifest di build.')
    template = (root / 'web/mcp-app-template.html').read_text(encoding='utf-8')
    marker = '/* KIRCHHOFF_MCP_APP_BUNDLE */'
    if template.count(marker) != 1:
        raise ValueError('Il template della MCP App deve contenere un solo punto di inserimento.')
    script = re.sub(r'</script', r'<\\/script', bundle.decode('utf-8'), flags=re.IGNORECASE)
    html = template.replace(marker, script)
    return html, dict(manifest, html_sha256=_hash(html.encode('utf-8')))


def validate_packaged_app(html: str, manifest: dict) -> str:
    """Rifiuta una risorsa installata alterata invece di pubblicarla all'host."""
    if (not isinstance(manifest, dict) or manifest.get('schema') != BUILD_SCHEMA
            or manifest.get('html_sha256') != _hash(html.encode('utf-8'))):
        raise ValueError('La risorsa MCP App installata non coincide con il manifest.')
    return html


def load_app_html() -> str:
    """Wheel/sdist usa package data; il checkout usa la medesima composizione."""
    directory = resources.files('kirchhoff.api').joinpath('resources')
    packaged = directory.joinpath(HTML_NAME)
    if packaged.is_file():
        html = packaged.read_text(encoding='utf-8')
        manifest = json.loads(directory.joinpath(MANIFEST_NAME).read_text(encoding='utf-8'))
        return validate_packaged_app(html, manifest)
    root = Path(__file__).resolve().parents[3]
    try:
        return compose_app(root)[0]
    except ValueError:
        # Nel checkout gli strumenti core restano disponibili anche prima
        # della compilazione web. La build distribuibile resta invece strict.
        template = (root / 'web/mcp-app-template.html').read_text(encoding='utf-8')
        script = ("document.getElementById('status').textContent="
                  "'MCP App non compilata o non aggiornata: esegui npm run build in web/. Gli strumenti MCP restano disponibili.';"
                  "document.getElementById('solve').disabled=true;")
        return template.replace('/* KIRCHHOFF_MCP_APP_BUNDLE */', script)
