"""Piccolo corpus DC pubblico, separato dall'holdout del prodotto."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.refusal import Refusal
from kirchhoff.eval.generator import generate_case
from kirchhoff.pipeline.netlist import leggi

from .topology import topology_fingerprint


@dataclass(frozen=True, slots=True)
class LabCase:
    """Input ricostruibile e query esplicita per gli oracoli esterni."""

    seed: int
    case_id: str
    family_id: str
    ir: IR
    request: Request


def _case(
    seed: int, case_id: str, family: str, netlist: str, target: str, quantity: str,
) -> LabCase:
    request = Request(f"q_{case_id}", quantity, target)  # type: ignore[arg-type]
    ir = replace(leggi(netlist), requests=(request,))
    return LabCase(seed, case_id, family, ir, request)


def case_for_seed(seed: int) -> LabCase:
    """Genera una delle quattro famiglie DC piccole con Fraction non banali."""
    if seed < 0:
        raise ValueError("seed deve essere non negativo")
    r1 = Fraction(7 + seed % 11, 3)
    r2 = Fraction(11 + seed % 13, 2)
    voltage = Fraction(5 + seed % 7, 1)
    current = Fraction(seed % 5, 3)
    family = seed % 4
    if family == 0:
        return _case(
            seed, f"generated-{seed:03d}", "series", f"""V1 s 0 {voltage} volt
R1 s a {r1} ohm
R2 a 0 {r2} ohm
I1 0 a {current} ampere
""", "R1", "current")
    if family == 1:
        return _case(
            seed, f"generated-{seed:03d}", "parallel", f"""V1 s 0 {voltage} volt
R1 s a {r1} ohm
R2 s a {r2} ohm
R3 a 0 {r1 + r2} ohm
I1 0 a {current} ampere
""", "R1", "voltage")
    if family == 2:
        return _case(
            seed, f"generated-{seed:03d}", "current-source", f"""I1 0 a {voltage / r1} ampere
R1 a 0 {r1} ohm
R2 a 0 {r2} ohm
""", "R1", "current")
    return _case(
        seed, f"generated-{seed:03d}", "floating-source", f"""V1 s 0 {voltage} volt
V2 a b {Fraction(2 + seed % 3)} volt
R1 s a {r1} ohm
R2 b 0 {r2} ohm
R3 a 0 {r1 + r2} ohm
I1 0 b {current} ampere
""", "R1", "voltage")


def generated_cases(number: int = 200) -> tuple[LabCase, ...]:
    if number < 1:
        raise ValueError("number deve essere positivo")
    return tuple(case_for_seed(seed) for seed in range(number))


def _family_from_sequence(sequence: tuple[str, ...], depth: int) -> str:
    reductions = sequence[:sequence.index("legge_di_ohm")]
    kinds = set(reductions)
    if kinds == {"serie"}:
        shape = "pure-series"
    elif kinds == {"parallelo"}:
        shape = "pure-parallel"
    elif kinds == {"serie", "parallelo"}:
        shape = "nested-series-parallel"
    else:
        shape = "single-resistor"
    return f"{shape}-depth-{depth}"


def topology_diverse_cases(number: int = 200) -> tuple[LabCase, ...]:
    """Adatta il generatore SP esistente a casi didattici DC diversificati."""
    if number < 1:
        raise ValueError("number deve essere positivo")
    selected: list[LabCase] = []
    fingerprints: set[str] = set()
    seed = 0
    # Ogni seed/depth e' deterministico. Si privilegia una nuova impronta; il bound
    # evita che una grammatica povera trasformi una richiesta finita in un loop.
    while len(selected) < number and seed < number * 40:
        # Profondita' 1..3: abbastanza varia per la grammatica SP, ma ogni caso
        # resta entro il bound dei controlli certificati del core.
        depth = 1 + seed % 3
        generated, _expected, sequence = generate_case(seed, depth=depth)
        request = Request(f"q_topology_{seed:04d}", "voltage", generated.requests[0].target)
        tail_resistance = Fraction(10 + seed % 19)
        ir = replace(
            generated,
            domain="dc",
            nodes=tuple(sorted((*generated.nodes, "x"))),
            components=(*generated.components,
                        Component.of("R_tail", "resistor", ("A", "x"), tail_resistance, "R_tail"),
                        Component.of("I_tail", "current_source_dc", ("0", "x"), Fraction(1), "I_tail")),
            requests=(request,),
        )
        if isinstance(pianifica(ir, request), Refusal):
            seed += 1
            continue
        fingerprint = topology_fingerprint(ir, request)
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            selected.append(LabCase(
                10_000 + seed,
                f"topology-{seed:04d}-depth-{depth}",
                _family_from_sequence(sequence, depth),
                ir,
                request,
            ))
        seed += 1
    if len(selected) != number:
        raise ValueError(
            f"grammatica SP: {len(selected)} topologie distinte entro il bound richiesto {number}")
    return tuple(selected)
