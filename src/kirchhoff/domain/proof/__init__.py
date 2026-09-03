"""`domain/proof` — il `ProofGraph` e i suoi nodi (AD-29, AD-8).

Scrittore unico del `ProofGraph`. Il nodo e' il proprietario del riferimento al
`LayoutIR` (AD-8 v2.1): porta l'identificatore del proprio stato visuale, mai la
struttura, che vive in `render/layout`.

La `ProofSession` — proiezione per riferimento, AD-21 v2 — abita in
`session.py` e si importa da li' (`kirchhoff.domain.proof.session`), non da
questo pacchetto: `session.py` dipende da `truthfulness`, che dipende da
`didactic`, che dipende da questo pacchetto. Riesportarla qui creerebbe un
import circolare (`analytical -> proof -> session -> truthfulness ->
execute -> analytical`).
"""

from .graph import ProofEdge, ProofGraph, ProofNode

__all__ = ["ProofEdge", "ProofGraph", "ProofNode"]
