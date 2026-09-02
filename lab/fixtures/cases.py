"""Piccolo corpus DC pubblico, separato dall'holdout del prodotto."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from kirchhoff.domain.ir import IR, Request
from kirchhoff.pipeline.netlist import leggi


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
