"""Esegue pytest contro un mutante senza poter riutilizzare bytecode precedente."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--import-name", required=True)
    parser.add_argument("tests", nargs="+")
    arguments = parser.parse_args()
    if not arguments.module.is_file():
        raise SystemExit(f"modulo mutato assente: {arguments.module}")
    # Quando il wrapper e' eseguito come ``python lab/mutation/...``, Python
    # inserisce ``lab/mutation`` (non la root) in ``sys.path``. Il subject smoke
    # vive nel package locale ``lab`` e dev'essere importabile *prima* che pytest
    # applichi la propria configurazione di collection.
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    # Cosmic Ray riscrive il modulo durante la stessa frazione di secondo. La
    # cache standard puo' quindi avere ancora mtime e dimensione compatibili.
    # Rimuoviamo esclusivamente il bytecode generato del modulo esplicitamente
    # mutato, mai sorgenti o cache di altri moduli.
    cache_dir = arguments.module.parent / "__pycache__"
    for cached in cache_dir.glob(f"{arguments.module.stem}.*.pyc"):
        cached.unlink()
    # Cosmic Ray esegue `test-command` senza shell. Un prefisso nuovo per processo
    # evita cache con mtime e dimensione uguali al file mutato. Il target viene
    # importato prima della collection nello stesso interprete: i test ricevono
    # quindi esattamente le sue classi e funzioni mutate, non quelle di un figlio
    # avviato prima della mutazione. `--assert=plain` esclude la cache separata
    # di pytest assertion-rewrite senza modificare la semantica degli assert.
    cache_prefix = tempfile.mkdtemp(
        prefix="kirchhoff-cosmic-pyc-", dir="/tmp")
    # `PYTHONPYCACHEPREFIX` is read during interpreter bootstrap; this wrapper
    # sets it after startup, therefore it must set the runtime value as well.
    os.environ["PYTHONPYCACHEPREFIX"] = cache_prefix
    sys.pycache_prefix = cache_prefix
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    importlib.invalidate_caches()
    # Alcuni ambienti di test precaricano il package padre. Rimuoviamo solo il
    # target esplicito e il suo attributo sul padre, così l'import successivo non
    # può restituire un oggetto modulo pre-mutazione da `sys.modules`.
    sys.modules.pop(arguments.import_name, None)
    parent_name, _, attribute = arguments.import_name.rpartition(".")
    parent = sys.modules.get(parent_name)
    if parent is not None and hasattr(parent, attribute):
        delattr(parent, attribute)
    importlib.import_module(arguments.import_name)
    import pytest

    return pytest.main(["--assert=plain", "-o", "addopts=", "-x", *arguments.tests])


if __name__ == "__main__":
    raise SystemExit(main())
