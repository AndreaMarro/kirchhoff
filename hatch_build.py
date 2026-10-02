"""Incorpora nella distribuzione la revisione reale del produttore.

La wheel deve poter comporre una prova senza la directory Git. Una sorgente
senza revisione dichiarata fallisce: non si attribuisce una build a uno SHA
inventato. Il file temporaneo non modifica il checkout.
"""
from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess
import tempfile

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        if version == "editable":
            return
        root = Path(self.root)
        inherited = root / "src/kirchhoff/_build_source_sha.txt"
        if inherited.is_file():
            sha = inherited.read_text(encoding="ascii").strip()
        else:
            sha = os.environ.get("KIRCHHOFF_SOURCE_SHA", "")
            if not sha:
                sha = subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "HEAD"],
                    check=True, capture_output=True, text=True, timeout=10,
                ).stdout.strip()
                dirty = subprocess.run(
                    ["git", "-C", str(root), "status", "--porcelain", "--",
                     "src/kirchhoff", "pyproject.toml", "hatch_build.py"],
                    check=True, capture_output=True, text=True, timeout=10,
                ).stdout
                if dirty:
                    raise ValueError("Build Kirchhoff con codice non committato: revisione non attribuibile.")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Build Kirchhoff senza SHA-40 produttore valido.")
        self._temporary = tempfile.TemporaryDirectory(prefix="kirchhoff-build-")
        source = Path(self._temporary.name) / "_build_source_sha.txt"
        source.write_text(sha + "\n", encoding="ascii")
        destination = ("src/kirchhoff/_build_source_sha.txt" if self.target_name == "sdist"
                       else "kirchhoff/_build_source_sha.txt")
        build_data["force_include"][str(source)] = destination

    def finalize(self, version: str, build_data: dict, artifact_path: str) -> None:
        temporary = getattr(self, "_temporary", None)
        if temporary is not None:
            temporary.cleanup()
