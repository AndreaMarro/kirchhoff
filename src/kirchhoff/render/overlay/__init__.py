"""`render/overlay` — `TransformOverlay`, i layer 5 e 6 di AD-23.

L'albero sorgente dello spine lo nomina cosi': *«`overlay/` — v2 · TransformOverlay,
layer 5-6 (AD-23)»*. Qui vivono i **ruoli**; lo stile e' dell'`ArmEncoding`, che
AD-26 assegna a `experiment/` e che nel braccio A e' vuoto.

Il pacchetto non importa `render/serialize` e non conosce coordinate: e' `serialize`
a leggere un overlay, mai il contrario. Le due direzioni non sono simmetriche —
un overlay che sapesse dove sta cio' che annota sarebbe il `LayoutIR` riscritto da
chi lo annota, e AD-21 tiene le quattro rappresentazioni disgiunte.
"""

from .schema import TransformOverlay, annota

__all__ = ["TransformOverlay", "annota"]
