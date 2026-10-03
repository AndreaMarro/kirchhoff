"""Frozen AC port oracle. Standard library only; no Kirchhoff imports.

Source suppression + a 1 A current entering p and leaving q. RREF is built
directly in Python complex arithmetic. Exact hand oracles use Fraction pairs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random

SEED = 2026100311
ROOT = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def parse(text: str):
    components, omega, port = [], None, None
    for line in text.splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == "@ac":
            assert len(words) == 3 and words[2] == "rad/s"
            omega = F(words[1])
        elif words[0] == "@amplitude":
            assert words[1] in ("rms", "peak")
        elif words[0] == "?":
            assert words[1] == "impedance" and len(words) == 4
            port = tuple(words[2:])
        else:
            cid, p, q, value, unit, *phase = words
            kind = cid[0]
            assert kind in "RLCVI"
            assert unit == {"R": "ohm", "L": "henry", "C": "farad", "V": "volt", "I": "ampere"}[kind]
            assert (len(phase) == 1 and phase[0].endswith("deg")) if kind in "VI" else not phase
            components.append((cid, kind, p, q, F(value)))
    assert omega is not None and port is not None
    return omega, components, port


def solve(text: str) -> dict:
    omega, components, (p, q) = parse(text)
    nodes = {n for _, _, a, b, _ in components for n in (a, b)}
    if p == q or p not in nodes or q not in nodes:
        return {"status": "invalid_port"}
    if omega <= 0 or any(value <= 0 for _, kind, _, _, value in components if kind in "RLC"):
        return {"status": "invalid_value"}

    # A graph check distinguishes disconnected open circuits from cancellation
    # at a resonance. Independent current sources contribute no connection.
    adjacent = defaultdict(set)
    for _, kind, a, b, _ in components:
        if kind != "I":
            adjacent[a].add(b)
            adjacent[b].add(a)
    reached, pending = {q}, [q]
    while pending:
        for other in adjacent[pending.pop()]:
            if other not in reached:
                reached.add(other)
                pending.append(other)
    if p not in reached:
        return {"status": "open_disconnected"}

    # q is the numerical reference; node named 0 remains an ordinary node when
    # the requested port has two non-ground terminals.
    order = sorted(nodes - {q})
    index = {node: i for i, node in enumerate(order)}
    voltage_sources = [c for c in components if c[1] == "V"]
    size = len(order) + len(voltage_sources)
    matrix = [[0j] * size for _ in range(size)]
    rhs = [0j] * size
    rhs[index[p]] = 1  # test source q -> p, hence Z = (Vp - Vq) / 1 A

    for _, kind, a, b, value in components:
        if kind in "VI":
            continue
        z = complex(float(value), 0) if kind == "R" else (
            complex(0, float(omega * value)) if kind == "L"
            else complex(0, -float(1 / (omega * value))))
        y = 1 / z
        if a != q:
            matrix[index[a]][index[a]] += y
        if b != q:
            matrix[index[b]][index[b]] += y
        if a != q and b != q:
            matrix[index[a]][index[b]] -= y
            matrix[index[b]][index[a]] -= y
    for offset, (_, _, a, b, _) in enumerate(voltage_sources):
        col = len(order) + offset
        # The original voltage/phase never enters this system: the source is
        # deactivated, but its 0 V constraint is retained even when floating.
        for node, sign in ((a, 1), (b, -1)):
            if node != q:
                matrix[index[node]][col] += sign
                matrix[col][index[node]] += sign

    augmented = [row[:] + [b] for row, b in zip(matrix, rhs)]
    scale = max(1., *(abs(x) for row in matrix for x in row))
    tolerance = 2e-12 * scale
    pivots, row = [], 0
    for col in range(size):
        pivot = max(range(row, size), key=lambda r: abs(augmented[r][col]), default=None)
        if pivot is None or abs(augmented[pivot][col]) <= tolerance:
            continue
        augmented[row], augmented[pivot] = augmented[pivot], augmented[row]
        divisor = augmented[row][col]
        augmented[row] = [v / divisor for v in augmented[row]]
        for r in range(size):
            if r != row:
                factor = augmented[r][col]
                augmented[r] = [v - factor * u for v, u in zip(augmented[r], augmented[row])]
        pivots.append(col)
        row += 1
    if any(max((abs(v) for v in values[:-1]), default=0) <= tolerance and abs(values[-1]) > tolerance
           for values in augmented):
        return {"status": "open_resonance", "rank": len(pivots), "unknowns": size}
    free = set(range(size)) - set(pivots)
    port_col = index[p]
    if port_col in free:
        return {"status": "undetermined_port", "rank": len(pivots), "unknowns": size}
    port_row = augmented[pivots.index(port_col)]
    if any(abs(port_row[f]) > tolerance for f in free):
        return {"status": "undetermined_port", "rank": len(pivots), "unknowns": size}

    # Choose zero only for internal free variables; the preceding check proves
    # that this choice does not affect the measured port voltage.
    solution = [0j] * size
    for r, col in enumerate(pivots):
        solution[col] = augmented[r][-1]
    residual = max((abs(sum(a*x for a, x in zip(values, solution)) - b)
                    for values, b in zip(matrix, rhs)), default=0.)
    assert residual <= 1e-9 * max(1., *(abs(v) for v in solution)), residual
    z = solution[port_col]
    return {"status": "finite_unique" if not free else "finite_with_internal_freedom",
            "real": z.real, "imaginary": z.imag, "rank": len(pivots), "unknowns": size,
            "max_equation_residual": residual, "reference": f"{p} -> {q}"}


# Exact, manually reduced reference calculations. They neither stamp nor solve
# a matrix and share no equation construction with solve().
def pair(a=0, b=0): return F(a), F(b)
def add(x, y): return x[0] + y[0], x[1] + y[1]
def sub(x, y): return x[0] - y[0], x[1] - y[1]
def mul(x, y): return x[0]*y[0] - x[1]*y[1], x[0]*y[1] + x[1]*y[0]
def div(x, y):
    n = y[0]*y[0] + y[1]*y[1]
    return (x[0]*y[0] + x[1]*y[1])/n, (x[1]*y[0] - x[0]*y[1])/n
def parallel(x, y): return div(mul(x, y), add(x, y))


def hand_oracles():
    # Bridge at imposed Vp=1: two Cramer expressions, then invert input current.
    ga, gl, gb, gr, gx = pair("1/2"), pair(0, "-1/3"), pair(0, "1/2"), pair("1/4"), pair("1/5")
    a, d = add(add(ga, gl), gx), add(add(gb, gr), gx)
    determinant = sub(mul(a, d), mul(gx, gx))
    va = div(add(mul(ga, d), mul(gx, gb)), determinant)
    vb = div(add(mul(gb, a), mul(gx, ga)), determinant)
    bridge = div(pair(1), add(mul(ga, sub(pair(1), va)), mul(gb, sub(pair(1), vb))))
    # A deactivated floating V(a,b) identifies a=b; the resulting two parallel
    # blocks are in series, with a separate 7 ohm input shunt.
    floating = parallel(add(parallel(pair(3), pair(0, 4)), parallel(pair(5), pair(0, -6))), pair(7))
    return {"manual_bridge": bridge, "manual_floating_source": floating}


def make_netlist(omega, lines, p="p", q="0", amplitude="rms"):
    return f"@ac {omega} rad/s\n@amplitude {amplitude}\n" + "\n".join(lines) + f"\n? impedance {p} {q}"


def fixtures():
    rng = random.Random(SEED)
    bases = [
        ("manual_bridge", 1, ["R1 p a 2 ohm", "L1 a 0 3 henry", "C1 p b 1/2 farad",
             "R2 b 0 4 ohm", "R3 a b 5 ohm", "I1 a 0 7 ampere 30deg"], "p", "0"),
        ("manual_floating_source", 2, ["R1 p a 3 ohm", "L1 p b 2 henry", "R2 a 0 5 ohm",
             "C1 b 0 1/12 farad", "R3 p 0 7 ohm", "V1 a b 11 volt 60deg", "I1 0 a 2 ampere -30deg"], "p", "0"),
    ]
    nodes = ["p", "a", "b", "c", "d", "0"]
    for case in range(8):
        omega = rng.choice([F("1/2"), F(2), F(3), F("5/2")])
        edges = list(zip(nodes, nodes[1:])) + [("0", "p")]
        extras = [(a,b) for i,a in enumerate(nodes) for b in nodes[i+1:]
                  if (a,b) not in edges and (b,a) not in edges]
        edges += rng.sample(extras, 3)
        lines, counts = [], defaultdict(int)
        for i, (a,b) in enumerate(edges):
            kind = "R" if i in (0,4) else rng.choice("RLC")
            counts[kind] += 1
            x = F(rng.randrange(1, 10))
            value = x if kind == "R" else x/omega if kind == "L" else 1/(omega*x)
            unit = {"R":"ohm", "L":"henry", "C":"farad"}[kind]
            lines.append(f"{kind}{counts[kind]} {a} {b} {value} {unit}")
        lines += ["V1 a d 5 volt 30deg", "I1 b 0 3 ampere 120deg"]
        bases.append((f"seeded_mesh_{case+1:02}", omega, lines, "p", "0" if case % 2 == 0 else "c"))
    cases = []
    for name, omega, lines, p, q in bases:
        variants = [("base", lines, p, q, "rms"), ("port_reversed", lines, q, p, "rms"),
                    ("components_reordered", list(reversed(lines)), p, q, "rms"),
                    ("amplitude_peak", lines, p, q, "peak")]
        values, directions = [], []
        for line in lines:
            words = line.split()
            if words[0][0] in "VI":
                changed = words[:]; changed[3] = "19/3"; changed[5] = "-150deg"
                values.append(" ".join(changed))
                words[1], words[2] = words[2], words[1]
            else:
                values.append(line)
            directions.append(" ".join(words))
        variants += [("source_values_and_phases", values, p, q, "rms"),
                     ("source_polarities", directions, p, q, "rms")]
        for variant, data, port_p, port_q, amplitude in variants:
            cases.append({"id": f"{name}/{variant}", "group": name, "variant": variant,
                          "require_finite_answer": True, "netlist": make_netlist(omega,data,port_p,port_q,amplitude)})
    degenerates = [
        ("parallel_lc_resonance", 2, ["L1 p 0 1 henry", "C1 p 0 1/4 farad"], "p", "0", "open_resonance"),
        ("series_lc_resonance", 2, ["L1 p a 1 henry", "C1 a 0 1/4 farad"], "p", "0", "finite_unique"),
        ("ideal_voltage_shorts_port", 1, ["V1 p 0 9 volt 30deg", "R1 p 0 4 ohm"], "p", "0", "finite_unique"),
        ("disconnected_port", 1, ["R1 p a 3 ohm", "R2 b 0 7 ohm"], "p", "0", "open_disconnected"),
        ("only_current_source", 1, ["I1 p 0 2 ampere 60deg"], "p", "0", "open_disconnected"),
        ("redundant_voltage_constraints", 1, ["V1 p 0 3 volt 0deg", "V2 p 0 3 volt 0deg", "R1 p 0 2 ohm"], "p", "0", "finite_with_internal_freedom"),
        ("inconsistent_original_sources", 1, ["V1 p 0 3 volt 0deg", "V2 p 0 4 volt 0deg", "R1 p 0 2 ohm"], "p", "0", "finite_with_internal_freedom"),
        ("irrelevant_floating_island", 1, ["R1 p 0 3 ohm", "R2 a b 7 ohm"], "p", "0", "finite_with_internal_freedom"),
        ("missing_port_terminal", 1, ["R1 p 0 3 ohm"], "unknown", "0", "invalid_port"),
        ("same_port_terminal", 1, ["R1 p 0 3 ohm"], "p", "p", "invalid_port"),
        ("zero_resistance_not_wire", 1, ["R1 p 0 0 ohm"], "p", "0", "invalid_value"),
    ]
    for name, omega, lines, p, q, expected in degenerates:
        cases.append({"id": name, "group": "degenerate", "variant": name, "require_finite_answer": False,
                      "expected_class": expected, "netlist": make_netlist(omega,lines,p,q)})
    return cases


def freeze():
    if (ROOT / "cases.json").exists() or (ROOT / "expected.json").exists():
        raise SystemExit("Frozen cases already exist. Refusing to overwrite them.")
    cases, exact = fixtures(), hand_oracles()
    answers, bases = {}, {}
    for case in cases:
        result = solve(case["netlist"])
        if case["group"] == "degenerate":
            assert result["status"] == case["expected_class"], (case["id"], result)
        else:
            assert result["status"] == "finite_unique", (case["id"], result)
            z = complex(result["real"], result["imaginary"])
            if case["variant"] == "base": bases[case["group"]] = z
            assert abs(z-bases[case["group"]]) <= 2e-11 * max(1,abs(z))
            if case["group"] in exact:
                re, im = exact[case["group"]]
                assert abs(z-complex(float(re),float(im))) <= 2e-11
                result["manual_exact_real"], result["manual_exact_imaginary"] = str(re), str(im)
        answers[case["id"]] = result
    case_bytes = encoded({"seed": SEED, "cases": cases})
    expected = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(), "model": "inherited/unknown",
                "seed": SEED, "case_count": len(cases), "finite_required": 60,
                "cases_sha256": sha(case_bytes), "oracle_sha256": sha(Path(__file__).read_bytes()),
                "product_called_before_freeze": False, "answers": answers}
    (ROOT / "cases.json").write_bytes(case_bytes)
    (ROOT / "expected.json").write_bytes(encoded(expected))
    print(json.dumps({key:value for key,value in expected.items() if key != "answers"}, indent=2))
    print("Manual exact:", {key:tuple(map(str,value)) for key,value in exact.items()})


def check_frozen():
    expected = json.loads((ROOT / "expected.json").read_text())
    assert sha((ROOT / "cases.json").read_bytes()) == expected["cases_sha256"], "Case mutation"
    assert sha(Path(__file__).read_bytes()) == expected["oracle_sha256"], "Oracle mutation after freeze"
    cases = json.loads((ROOT / "cases.json").read_text())["cases"]
    assert cases == fixtures(), "Seed regeneration differs"
    for case in cases:
        actual = solve(case["netlist"])
        saved = expected["answers"][case["id"]]
        assert all(saved[key] == value for key,value in actual.items()), case["id"]
    return cases, expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze", "check"])
    args = parser.parse_args()
    if args.action == "freeze": freeze()
    else:
        cases, expected = check_frozen()
        print(json.dumps({"frozen_integrity": True, "cases": len(cases), "expected_sha256": sha((ROOT/"expected.json").read_bytes())}))
