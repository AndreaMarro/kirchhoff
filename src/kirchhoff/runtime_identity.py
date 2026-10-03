"""Identità immutabile dei sorgenti del processo, acquisita all'import iniziale.

Il package importa questo modulo prima dei solver. Una revisione legge soltanto
lo snapshot: i byte aggiornati sul disco non possono rinominare codice già in
memoria. La guardia rifiuta modifiche, aggiunte, rimozioni e file illeggibili.
"""
from hashlib import sha256
from pathlib import Path
from threading import RLock
from types import MappingProxyType


MESSAGE = ('Il codice è cambiato dopo l’avvio. Riavvia il server Kirchhoff '
           'prima di calcolare o esportare la lezione.')


class RuntimeIdentityError(ValueError):
    """Il processo deve ripartire prima di pubblicare un'altra lezione."""


class SourceSnapshot:
    """Snapshot esatto e guardia fail-closed; nessuna cache al primo calcolo."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self._lock = RLock()
        self._stale = False
        self._entrypoints = {}
        self._sources = MappingProxyType(self._read_sources())
        if not self._sources:
            raise RuntimeIdentityError('Sorgenti del processo non disponibili: impossibile identificarlo.')
        digest = sha256()
        for name, data in sorted(self._sources.items()):
            digest.update(name.encode()+b'\0'+str(len(data)).encode()+b'\0'+data)
        self.package_revision = digest.hexdigest()

    def _read_sources(self):
        return {path.relative_to(self.root).as_posix():path.read_bytes()
                for path in sorted(self.root.rglob('*.py')) if path.is_file()}

    def assert_current(self):
        with self._lock:
            if self._stale:
                raise RuntimeIdentityError(MESSAGE)
            try:
                current = self._read_sources()
                unchanged = current == self._sources and all(path.read_bytes() == data for path,data in self._entrypoints.items())
            except OSError:
                unchanged = False
            if not unchanged:
                self._stale = True
                raise RuntimeIdentityError(MESSAGE)

    def register_entrypoint(self, path: Path):
        """Sorveglia anche il launcher HTTP, che può vivere fuori dal wheel."""
        with self._lock:
            self.assert_current()
            resolved = path.resolve()
            data = resolved.read_bytes()
            if resolved in self._entrypoints and self._entrypoints[resolved] != data:
                self._stale = True
                raise RuntimeIdentityError(MESSAGE)
            self._entrypoints[resolved] = data

    def revision(self, names):
        """La selezione conserva la firma precedente, sul package congelato."""
        self.assert_current()
        digest = sha256(b'kirchhoff-loaded-sources.v1\0'+self.package_revision.encode())
        for name in names:
            relative = (self.root / name).resolve().relative_to(self.root).as_posix()
            data = self._sources[relative]
            digest.update(name.encode()+b'\0'+str(len(data)).encode()+b'\0'+data)
        return digest.hexdigest()


# Eseguito da kirchhoff.__init__, prima che qualunque solver venga importato.
SNAPSHOT = SourceSnapshot(Path(__file__).resolve().parent)


def assert_runtime_current():
    SNAPSHOT.assert_current()


def register_entrypoint(path):
    SNAPSHOT.register_entrypoint(Path(path))


def loaded_revision(names):
    return SNAPSHOT.revision(names)
