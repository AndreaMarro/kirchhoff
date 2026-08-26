"""`render/serialize` — l'SVG semantico, sorgente unica di ogni altro formato.

AD-31 nomina questo pacchetto accanto a `render/roundtrip`, che nascera' con la
Story 1.6: qui si **emette** l'annotazione derivandola dalla geometria, li' la si
riparsera' per confrontare i grafi. I due lati della stessa promessa.
"""

from .geometry import FORME, Filo, Forma, Giunzione, Punto, Scena, Simbolo, Terminale, scena
from .svg import alternativa_testuale, render

__all__ = [
    "FORME",
    "Filo",
    "Forma",
    "Giunzione",
    "Punto",
    "Scena",
    "Simbolo",
    "Terminale",
    "alternativa_testuale",
    "render",
    "scena",
]
