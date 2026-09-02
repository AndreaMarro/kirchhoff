"""Adapter ngspice a subprocess; le tolleranze vivono soltanto nel laboratorio."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from kirchhoff.domain.ir import IR, Request


def _decimal(value: Fraction) -> str:
    return format(float(value), ".17g")


def _deck(ir: IR, output: Path, target: str) -> tuple[str, float]:
    lines = ["* Kirchhoff P1-M0 generated deck"]
    for index, component in enumerate(ir.components, 1):
        p, q = component.terminals
        value = _decimal(component.value.amount)
        if component.type == "resistor":
            lines.append(f"R{index} {p} {q} {value}")
        elif component.type == "voltage_source_dc":
            lines.append(f"V{index} {p} {q} DC {value}")
        elif component.type == "current_source_dc":
            lines.append(f"I{index} {p} {q} DC {value}")
        else:
            raise ValueError(f"{component.id}: tipo non supportato da ngspice lab")
    component = ir.component(target)
    p, q = component.terminals
    if q == "0":
        measurement, polarity = f"v({p})", 1.0
    elif p == "0":
        measurement, polarity = f"v({q})", -1.0
    else:
        measurement, polarity = f"v({p},{q})", 1.0
    lines.extend((
        ".control",
        "set filetype=ascii",
        "op",
        f"wrdata {output} {measurement}",
        "quit",
        ".endc",
        ".end",
    ))
    return "\n".join(lines) + "\n", polarity


def _last_number(path: Path) -> float:
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    values = [float(item) for item in rows[-1]]
    if len(values) < 2:
        raise ValueError(f"wrdata ngspice inatteso: {rows[-1]!r}")
    return values[-1]


def ngspice_value(ir: IR, request: Request) -> float:
    """Esegue un operating point e restituisce solo la misura richiesta in float lab."""
    if ir.domain != "dc":
        raise ValueError("ngspice lab supporta solo IR DC")
    component = ir.component(request.target)
    with TemporaryDirectory(prefix="kirchhoff-ngspice-") as directory:
        root = Path(directory)
        output = root / "op.dat"
        deck = root / "case.cir"
        deck_text, polarity = _deck(ir, output, request.target)
        deck.write_text(deck_text, encoding="utf-8")
        completed = subprocess.run(
            ["ngspice", "-b", "-o", str(root / "ngspice.log"), str(deck)],
            check=False, text=True, capture_output=True, timeout=20,
        )
        if completed.returncode != 0 or not output.exists():
            log = root / "ngspice.log"
            detail = log.read_text(encoding="utf-8") if log.exists() else ""
            raise RuntimeError(f"ngspice failed: {detail or completed.stderr or completed.stdout}")
        voltage = polarity * _last_number(output)
    if request.quantity == "voltage":
        return voltage
    if component.type == "resistor":
        return voltage / float(component.value.amount)
    if component.type == "current_source_dc":
        return float(component.value.amount)
    raise ValueError("ngspice current comparison iniziale supporta resistori e current source")
