"""8 circuiti curati devono risolvere e verificare in <60s."""
from pathlib import Path
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.resolve import resolve, Solved

EXAMPLES = Path("examples")

def test_examples_curati():
    for name in ("series", "parallel", "ladder", "bridge", "nodal", "series_current", "parallel_current", "floating"):
        netlist = (EXAMPLES / name / "netlist.txt").read_text(encoding="utf-8")
        ir = leggi(netlist)
        esito = resolve(ir)
        assert isinstance(esito, Solved), f"{name} non risolto: {esito}"
        assert "accordo fra percorsi indipendenti" in esito.verifiche
        # SVG solo per maglia singola (series, ladder, series_current, nodal)
        if name in ("series", "ladder", "series_current", "nodal"):
            assert esito.svg is not None and esito.svg.startswith("<svg")
        else:
            pass
