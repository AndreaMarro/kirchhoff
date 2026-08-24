"""Insieme di riferimento: costruzione, verifica indipendente, split dev/holdout.

Quattro classi di dominio, quattro generatori, quattro oracoli — e in ogni caso
l'oracolo raggiunge la risposta per una via che il generatore non ha percorso:

    dc_resistive    albero serie/parallelo -> analisi nodale
    ac_sinusoidal   propagazione del fasore -> analisi nodale complessa
    three_phase     simmetria a 120 gradi -> analisi nodale sull'intera rete
    transient       radici scelte, componenti derivati -> singolarita' della
                    matrice MNA nelle radici

La parte trattenuta vive in una directory separata e il flusso di sviluppo non la
puo' leggere: `load()` in modalita' `dev` rifiuta di aprirla (Story 1.2, secondo
criterio). Non e' una convenzione, e' un errore. Lo split e' **stratificato per
classe**: se non lo fosse, con le classi generate in blocco la parte trattenuta
finirebbe per contenere solo le ultime classi, e non misurerebbe piu' nulla delle
prime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from ..domain.exact import Cyc12
from ..domain.ir import IR, Component, Magnitude, Provenance, Request
from ..domain.mna import kcl_residuals, power_balance, solve_dc, solve_phasor
from ..domain.transient import (
    CHARACTERISTIC_QUANTITY,
    initial_state,
    is_natural_frequency,
    steady_state,
)
from . import generator, generator_ac, generator_three_phase, generator_transient

HOLDOUT_ENV = "KIRCHHOFF_ALLOW_HOLDOUT"

#: Le quattro classi di dominio in scope (D8), con il prefisso del loro case_id.
CLASSES: tuple[tuple[str, str], ...] = (
    ("dc_resistive", "dc"),
    ("transient", "tr"),
    ("ac_sinusoidal", "ac"),
    ("three_phase", "3f"),
)


class HoldoutAccessError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Case:
    case_id: str
    ir: IR
    expected: dict[str, dict[str, object]]
    domain_class: str
    transformations: tuple[str, ...]


def _f(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def _pf(s: str) -> Fraction:
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def _enc(x: object) -> dict:
    """Valore atteso in JSON, con il tipo dichiarato. Mai un float, mai un troncamento."""
    if isinstance(x, Cyc12):
        return {"c": [_f(k) for k in x.c]}
    if isinstance(x, Fraction):
        return {"q": _f(x)}
    raise TypeError(f"valore atteso di tipo non serializzabile: {type(x).__name__}")


def _dec(d: dict) -> object:
    if "c" in d:
        k = [_pf(s) for s in d["c"]]
        return Cyc12((k[0], k[1], k[2], k[3]))
    return _pf(d["q"])


# -- verifica indipendente, una per classe -------------------------------------


def _compare(sol: dict, expected: dict, keys: tuple[str, ...]) -> list[str]:
    problems: list[str] = []
    for cid, exp in expected.items():
        got = sol.get(cid)
        if got is None:
            problems.append(f"{cid}: assente nella soluzione nodale")
            continue
        for q in keys:
            if got[q] != exp[q]:
                problems.append(f"{cid}.{q}: costruzione={exp[q]} nodale={got[q]}")
    return problems


def _leggi_di_kirchhoff(ir: IR, sol: dict) -> list[str]:
    problems: list[str] = []
    for node, r in kcl_residuals(ir, sol).items():
        if r != 0:
            problems.append(f"KCL non nullo al nodo {node}: {r}")
    p = power_balance(ir, sol)
    if p != 0:
        problems.append(f"bilancio di potenza non nullo: {p}")
    return problems


def _verify_dc(ir: IR, expected: dict) -> list[str]:
    sol = solve_dc(ir)
    return _compare(sol, expected, ("voltage", "current")) + _leggi_di_kirchhoff(ir, sol)


def _verify_phasor(ir: IR, expected: dict) -> list[str]:
    sol = solve_phasor(ir)
    return _compare(sol, expected, ("voltage", "current")) + _leggi_di_kirchhoff(ir, sol)


def _verify_three_phase(ir: IR, expected: dict) -> list[str]:
    problems = _verify_phasor(ir, expected)
    sol = solve_phasor(ir)
    fasi = [c for c in ir.components if c.type == "voltage_source_ac" and c.value.amount != 0]
    somma = sum((sol[c.id]["current"] for c in fasi), Cyc12.of(0))
    if somma != 0:
        problems.append(f"le tre correnti di fase non sommano a zero: {somma}")
    return problems


def _verify_transient(ir: IR, expected: dict) -> list[str]:
    problems: list[str] = []
    init = initial_state(ir)
    fin = steady_state(ir)
    problems += _leggi_di_kirchhoff(ir, init) + _leggi_di_kirchhoff(ir, fin)

    for cid, exp in expected.items():
        if cid not in init:
            problems.append(f"{cid}: assente nella soluzione nodale")
            continue
        q = CHARACTERISTIC_QUANTITY[ir.component(cid).type]
        if "initial_value" in exp and init[cid][q] != exp["initial_value"]:
            problems.append(
                f"{cid}.initial_value: costruzione={exp['initial_value']} a t=0+={init[cid][q]}")
        if "final_value" in exp and fin[cid][q] != exp["final_value"]:
            problems.append(
                f"{cid}.final_value: costruzione={exp['final_value']} a regime={fin[cid][q]}")
        if "time_constant" in exp:
            tau = exp["time_constant"]
            if tau <= 0:
                problems.append(f"{cid}: costante di tempo non positiva ({tau})")
            elif not is_natural_frequency(ir, -1 / tau):
                problems.append(f"{cid}: -1/tau = {-1 / tau} non e' una frequenza naturale")
        radici = [exp[k] for k in ("root_1", "root_2") if k in exp]
        for s in radici:
            if s >= 0:
                problems.append(f"{cid}: radice non negativa ({s}), il transitorio non si spegne")
            elif not is_natural_frequency(ir, s):
                problems.append(f"{cid}: {s} non annulla la matrice MNA")
        if len(radici) == 2 and radici[0] == radici[1]:
            problems.append(f"{cid}: radici coincidenti, il caso e' degenere")
    return problems


_VERIFIERS = {
    "dc_resistive": _verify_dc,
    "ac_sinusoidal": _verify_phasor,
    "three_phase": _verify_three_phase,
    "transient": _verify_transient,
}


def verify_independently(ir: IR, expected: dict) -> list[str]:
    """Confronta la risposta-per-costruzione con la via indipendente. Zero tolleranza."""
    return _VERIFIERS[ir.domain](ir, expected)


# -- costruzione ---------------------------------------------------------------

_GENERATORS = {
    "dc_resistive": lambda seed, depth: generator.generate_case(seed, depth),
    "transient": lambda seed, depth: generator_transient.generate_case(seed),
    "ac_sinusoidal": lambda seed, depth: generator_ac.generate_case(seed, min(depth, 2)),
    "three_phase": lambda seed, depth: generator_three_phase.generate_case(seed),
}


def _build_class(cls: str, prefix: str, n: int, seed0: int, depth: int):
    accepted: list[Case] = []
    rejected: list[dict] = []
    seed = seed0
    while len(accepted) < n:
        try:
            ir, expected, seq = _GENERATORS[cls](seed, depth)
        except ZeroDivisionError as e:
            # risonanza esatta: impedenza nulla in serie o ammettenza nulla in parallelo
            rejected.append({"seed": seed, "problems": [f"caso degenere: {e}"]})
        else:
            problems = verify_independently(ir, expected)
            if problems:
                rejected.append({"seed": seed, "problems": problems})
            else:
                accepted.append(Case(f"{prefix}-{seed:05d}", ir, expected, cls, seq))
        seed += 1
        if seed - seed0 > 50 * max(n, 1):
            raise RuntimeError(f"generazione non converge per la classe {cls}")
    return accepted, rejected


def build(n: int, seed0: int = 1, depth: int = 3) -> tuple[list[Case], list[dict]]:
    """Costruisce n casi verificati, distribuiti fra le quattro classi di dominio."""
    accepted: list[Case] = []
    rejected: list[dict] = []
    base, resto = divmod(n, len(CLASSES))
    for k, (cls, prefix) in enumerate(CLASSES):
        quota = base + (1 if k < resto else 0)
        a, r = _build_class(cls, prefix, quota, seed0 + 1000 * k, depth)
        accepted.extend(a)
        rejected.extend(r)
    return accepted, rejected


# -- serializzazione -----------------------------------------------------------


def to_json(c: Case) -> dict:
    return {
        "case_id": c.case_id,
        "domain_class": c.domain_class,
        "transformations": list(c.transformations),
        "ir": {
            "ir_version": c.ir.ir_version,
            "domain": c.ir.domain,
            "source_kind": c.ir.source_kind,
            "nodes": list(c.ir.nodes),
            "omega": _f(c.ir.omega),
            "components": [
                {"id": k.id, "type": k.type, "terminals": list(k.terminals),
                 # la grandezza viaggia con la propria unita': un valore letto senza
                 # unita' non e' un valore, e lo schema lo respinge in lettura
                 "value": {"amount": _f(k.value.amount), "unit": k.value.unit},
                 "symbolic": k.symbolic, "phase_steps": k.phase_steps,
                 "provenance": _enc_provenance(k.provenance)}
                for k in c.ir.components
            ],
            "requests": [{"id": r.id, "quantity": r.quantity, "target": r.target}
                         for r in c.ir.requests],
        },
        "expected": {cid: {q: _enc(v) for q, v in d.items()} for cid, d in c.expected.items()},
    }


def _enc_provenance(p: Provenance | None) -> dict | None:
    if p is None:
        return None
    return {"x": _f(p.x), "y": _f(p.y), "width": _f(p.width), "height": _f(p.height)}


def _dec_provenance(d: dict | None) -> Provenance | None:
    if d is None:
        return None
    return Provenance(_pf(d["x"]), _pf(d["y"]), _pf(d["width"]), _pf(d["height"]))


def from_json(d: dict) -> Case:
    ir = IR(
        d["ir"]["ir_version"], d["ir"]["domain"], d["ir"]["source_kind"],
        tuple(d["ir"]["nodes"]),
        tuple(Component(k["id"], k["type"], (k["terminals"][0], k["terminals"][1]),
                        Magnitude(_pf(k["value"]["amount"]), k["value"]["unit"]),
                        k["symbolic"], k["phase_steps"],
                        _dec_provenance(k["provenance"]))
              for k in d["ir"]["components"]),
        tuple(Request(r["id"], r["quantity"], r["target"]) for r in d["ir"]["requests"]),
        _pf(d["ir"]["omega"]),
    )
    exp = {cid: {q: _dec(v) for q, v in x.items()} for cid, x in d["expected"].items()}
    return Case(d["case_id"], ir, exp, d["domain_class"], tuple(d["transformations"]))


def write(cases: list[Case], root: Path, split: float = 0.6) -> dict[str, int]:
    """Scrive dev e holdout, stratificando per classe di dominio."""
    per_classe: dict[str, list[Case]] = {}
    for c in cases:
        per_classe.setdefault(c.domain_class, []).append(c)

    dev: list[Case] = []
    holdout: list[Case] = []
    for cls in sorted(per_classe):
        xs = per_classe[cls]
        cut = int(len(xs) * split + 0.5)
        dev.extend(xs[:cut])
        holdout.extend(xs[cut:])

    for name, subset in (("dev", dev), ("holdout", holdout)):
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        # Si riparte da zero: un caso rimasto da una costruzione precedente
        # misurerebbe una versione del sistema che non esiste piu'.
        for vecchio in d.glob("*.json"):
            vecchio.unlink()
        for c in subset:
            (d / f"{c.case_id}.json").write_text(
                json.dumps(to_json(c), indent=2, ensure_ascii=False), encoding="utf-8")
    return {"dev": len(dev), "holdout": len(holdout)}


def load(root: Path, split_name: str, *, allow_holdout: bool = False) -> list[Case]:
    if split_name == "holdout" and not allow_holdout:
        raise HoldoutAccessError(
            "la parte trattenuta non e' leggibile dal flusso di sviluppo. "
            f"Serve --allow-holdout (o {HOLDOUT_ENV}=1), e usarla durante lo sviluppo "
            "invalida ogni misura successiva."
        )
    d = root / split_name
    return [from_json(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(d.glob("*.json"))]
