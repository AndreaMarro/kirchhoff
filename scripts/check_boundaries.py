#!/usr/bin/env python3
"""Il confine di dipendenza dello spine, verificato sull'albero sintattico.

Regola: nessun modulo sotto `domain/` importa qualcosa del progetto che stia fuori
da `domain/`. Vale per `adapters/` e `ports/` come per tutto il resto — il dominio
non conosce nulla del mondo attorno a sé (AD-1, paradigma ports-and-adapters).

**Perché `ast` e non `grep`.** Un'espressione regolare su `from ..adapters` non vede
`import kirchhoff.adapters as a`, non vede `from kirchhoff import pipeline`, non vede
un import dentro una funzione, e non sa risolvere quanti pacchetti risale un
`from ...` . Lette come nodi, le tre forme collassano nello stesso caso e la
risoluzione dei relativi diventa aritmetica sui segmenti del percorso.

Uso:

    uv run python scripts/check_boundaries.py [radice]

Uscita 0 se il confine regge, 1 altrimenti, nominando file, riga e import. Un file
che non si lascia analizzare solleva: un modulo illeggibile non è un modulo pulito.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

PACCHETTO = "kirchhoff"
RECINTO = "domain"
RADICE_PREDEFINITA = Path(__file__).resolve().parent.parent / "src" / PACCHETTO


@dataclass(frozen=True, slots=True)
class Violazione:
    file: Path
    riga: int
    modulo_importato: str


def _fuori_dal_recinto(nome: str) -> bool:
    """Vero quando `nome` appartiene al progetto ma non a `domain/`."""
    if not (nome == PACCHETTO or nome.startswith(f"{PACCHETTO}.")):
        return False                       # libreria standard o terze parti: non ci riguarda
    interno = f"{PACCHETTO}.{RECINTO}"
    return not (nome == interno or nome.startswith(f"{interno}."))


def _moduli_importati(nodo: ast.AST, pacchetto: list[str]) -> list[str]:
    """I nomi assoluti che un nodo di import porta dentro il modulo."""
    if isinstance(nodo, ast.Import):
        return [alias.name for alias in nodo.names]

    if isinstance(nodo, ast.ImportFrom):
        if nodo.level:
            base = pacchetto[: len(pacchetto) - (nodo.level - 1)]
            parti = [*base, nodo.module] if nodo.module else list(base)
        else:
            parti = [nodo.module] if nodo.module else []
        nome = ".".join(parti)
        if nome == PACCHETTO:
            # `from kirchhoff import pipeline`: cio' che entra e' il sottopacchetto
            return [f"{PACCHETTO}.{alias.name}" for alias in nodo.names]
        return [nome]

    return []


def _parti_pacchetto(file: Path, radice: Path) -> list[str]:
    return list(file.relative_to(radice.parent).parts[:-1])


def violazioni(radice: Path) -> list[Violazione]:
    """Ogni import che esce dal recinto, in ordine deterministico."""
    recinto = radice / RECINTO
    if not recinto.is_dir():
        # Il modo peggiore di fallire per un gate: puntato sulla directory sbagliata,
        # non trova nulla, dichiara tutto pulito. Un refuso nel percorso lo
        # spegnerebbe senza che nessuno se ne accorga.
        raise FileNotFoundError(f"nessuna directory da controllare: {recinto}")

    trovate: list[Violazione] = []
    for file in sorted(recinto.rglob("*.py")):
        albero = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        pacchetto = _parti_pacchetto(file, radice)
        for nodo in ast.walk(albero):
            for nome in _moduli_importati(nodo, pacchetto):
                if _fuori_dal_recinto(nome):
                    trovate.append(Violazione(file, nodo.lineno, nome))
    return trovate


def descrivi(v: Violazione) -> str:
    return (f"{v.file}:{v.riga}: importa {v.modulo_importato} — "
            f"{RECINTO}/ non puo' dipendere da nulla del progetto fuori da se'")


def main(argv: list[str] | None = None) -> int:
    argomenti = sys.argv[1:] if argv is None else argv
    radice = Path(argomenti[0]) if argomenti else RADICE_PREDEFINITA

    trovate = violazioni(radice)
    if not trovate:
        print(f"{RECINTO}/ non importa nulla del progetto fuori da se'")
        return 0

    for v in trovate:
        print(descrivi(v))
    print(f"\n{len(trovate)} violazioni del confine di dipendenza.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
