"""`domain/proof` — il `ProofGraph` e i suoi nodi (AD-29, AD-8).

Scrittore unico del `ProofGraph`. Il nodo e' il proprietario del riferimento al
`LayoutIR` (AD-8 v2.1): porta l'identificatore del proprio stato visuale, mai la
struttura, che vive in `render/layout`.

La `ProofSession` — proiezione per riferimento, AD-21 v2 — e' la Story 6.1 e non
abita ancora qui.
"""

from .graph import ProofEdge, ProofGraph, ProofNode

__all__ = ["ProofEdge", "ProofGraph", "ProofNode"]
