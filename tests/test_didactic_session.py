"""DidacticSession application composition — 5 circuiti curati + determinismo visuale."""
from fractions import Fraction
from dataclasses import replace
from pathlib import Path

import pytest
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.domain.ir import Request
from kirchhoff.domain.identity import conia
from kirchhoff.pipeline.didactic_session import build_session, to_json, DidacticSession
from kirchhoff.render.layout import LayoutIR, Placement
from kirchhoff.domain.transform import EntityRef
from kirchhoff.domain.refusal import Refusal

def _states(n, seed=0):
    return tuple(conia("ir", 2000000000000 + i*1000 + seed, bytes([(i*11+j)%256 for j in range(10)])) for i in range(n))

def _layout_for(ir, istante=2000000000000):
    from kirchhoff.render.serialize.geometry import FORME
    # layout curato per ladder (V1 d 0, R1 d c, R2 c b, R3 b 0)
    if set(ir.nodes) == {"0", "b", "c", "d"} and len(ir.components) == 4:
        pls = (
            Placement(EntityRef("node","d"), Fraction(0), Fraction(0)),
            Placement(EntityRef("node","c"), Fraction(200), Fraction(0)),
            Placement(EntityRef("node","b"), Fraction(400), Fraction(0)),
            Placement(EntityRef("node","0"), Fraction(200), Fraction(240)),
            Placement(EntityRef("component","V1"), Fraction(0), Fraction(120)),
            Placement(EntityRef("component","R1"), Fraction(100), Fraction(0)),
            Placement(EntityRef("component","R2"), Fraction(300), Fraction(0)),
            Placement(EntityRef("component","R3"), Fraction(400), Fraction(120)),
        )
        return LayoutIR.nuovo(pls, istante=istante, casualita=bytes(range(10)))
    # layout curato per series (V1 b 0, R1 b a, R2 a 0)
    if set(ir.nodes) == {"0","a","b"} and len(ir.components)==3:
        from tests.test_visual_slice import PIAZZAMENTI
        return LayoutIR.nuovo(PIAZZAMENTI, istante=istante, casualita=bytes(range(10)))
    pls = []
    for n in ir.nodes:
        pls.append(Placement(EntityRef("node", n), Fraction(ir.nodes.index(n)*200), Fraction(0)))
    for idx, c in enumerate(ir.components):
        if c.type not in FORME:
            continue
        a,b = c.terminals
        x = (ir.nodes.index(a)*200 + ir.nodes.index(b)*200)//2 if a in ir.nodes and b in ir.nodes else idx*100
        y = Fraction(160 if c.type == "current_source_dc" else 80 + (idx%2)*40)
        pls.append(Placement(EntityRef("component", c.id), Fraction(x), y))
    return LayoutIR.nuovo(tuple(pls), istante=istante, casualita=bytes(range(10)))

EXAMPLES = {
    "series": ("V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n", "voltage", "R2"),
    "parallel": ("V1 a 0 12 volt\nR1 a 0 100 ohm\nR2 a 0 220 ohm\n", "voltage", "R1"),
    "ladder": ("V1 d 0 12 volt\nR1 d c 10 ohm\nR2 c b 20 ohm\nR3 b 0 30 ohm\n", "voltage", "R1"),
    "bridge": ("V1 p 0 12 volt\nR1 p a 10 ohm\nR2 p b 20 ohm\nR3 a 0 30 ohm\nR4 b 0 40 ohm\nRg a b 50 ohm\n", "voltage", "Rg"),
    "nodal": ("I1 0 a 2 ampere\nR1 a 0 5 ohm\n", "voltage", "R1"),
}

@pytest.mark.parametrize("name", ["series", "parallel", "ladder", "bridge", "nodal"])
def test_curated_example_session(name):
    net, qty, tgt = EXAMPLES[name]
    ir0 = leggi(net)
    req = Request("q1", qty, tgt)
    ir = replace(ir0, requests=(req,))
    state_ids = _states(4, seed=hash(name)%1000)
    lay = _layout_for(ir)
    layouts = {state_ids[0]: lay}
    result = build_session(ir, req, state_ids=state_ids, layouts=layouts)
    # Ogni esempio deve risolvere (o rifiutare esplicitamente) — mai crashare
    assert isinstance(result, (DidacticSession, Refusal)), f"{name} inatteso {result}"
    if isinstance(result, DidacticSession):
        assert result.claim.status == "VERIFIED"
        j1 = to_json(result)
        j2 = to_json(result)
        assert j1 == j2
        for s in result.steps:
            assert s.before_svg.startswith("<svg")
            assert s.after_svg.startswith("<svg")
            assert s.before_svg != s.after_svg
            assert s.equation
            assert s.why_legal["certificato"] in ("serie", "parallelo")

def test_visual_determinism_same_inputs_same_bytes():
    # Usa ladder voltage R1 che ha 1 step con layout curato
    net = "V1 d 0 12 volt\nR1 d c 10 ohm\nR2 c b 20 ohm\nR3 b 0 30 ohm\n"
    ir0 = leggi(net)
    req = Request("q1", "voltage", "R1")
    ir = replace(ir0, requests=(req,))
    state_ids = _states(4, seed=123)
    lay = _layout_for(ir, istante=3000000000000)
    layouts = {state_ids[0]: lay}
    s1 = build_session(ir, req, state_ids=state_ids, layouts=layouts)
    s2 = build_session(ir, req, state_ids=state_ids, layouts=layouts)
    assert isinstance(s1, DidacticSession) and isinstance(s2, DidacticSession)
    assert len(s1.steps) == len(s2.steps) == 1
    assert s1.steps[0].before_svg == s2.steps[0].before_svg
    assert s1.steps[0].after_svg == s2.steps[0].after_svg
    assert s1.final_value == s2.final_value

def test_no_hardcoded_numbers():
    # verifica che il valore finale venga dal solver, non hardcodato
    for name in EXAMPLES:
        net, qty, tgt = EXAMPLES[name]
        ir0 = leggi(net)
        req = Request("q1", qty, tgt)
        ir = replace(ir0, requests=(req,))
        state_ids = _states(4, seed=hash(name)%1000+1)
        lay = _layout_for(ir)
        result = build_session(ir, req, state_ids=state_ids, layouts={state_ids[0]: lay})
        if isinstance(result, Refusal):
            continue
        assert isinstance(result, DidacticSession)
        # ricalcola via resolve diretto e confronta
        from kirchhoff.pipeline.resolve import resolve
        solved = resolve(ir)
        from kirchhoff.pipeline.resolve import Solved
        assert isinstance(solved, Solved)
        assert solved.soluzione[tgt][qty] == result.final_value

def test_refusal_first_class():
    # caso che deve rifiutare: C in DC
    ir0 = leggi("V1 a 0 10 volt\nR1 a b 10 ohm\nC1 b 0 0.001 farad\n")
    req = Request("q1", "voltage", "R1")
    ir = replace(ir0, requests=(req,))
    state_ids = _states(2)
    result = build_session(ir, req, state_ids=state_ids, layouts=None)
    assert isinstance(result, Refusal)
    assert result.cause in ("unsolvable", "topology", "units")
