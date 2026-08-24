"""Metriche VSR / SER / QPS / TTV e matrice degli errori (FR-34).

`SolverUnderTest` e' qualunque callabile che, dato un IR, restituisce le
grandezze richieste piu' l'esito della Verifica. L'harness non sa nulla di come
sia fatto: e' lo stesso percorso che attraversano gli utenti, con gli adapter
sostituiti (AD-15).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction

from ..domain.ir import IR

ERROR_KINDS = ("topologia", "valore", "unita", "grandezza_richiesta", "irrisolvibile")

#: Campi del rapporto che misurano la macchina, non il sistema. Sono l'unica cosa
#: che due esecuzioni sugli stessi input possono legittimamente non condividere, e
#: il rapporto li nomina perche' chi confronta due misure sappia cosa saltare.
#: Arrotondare TTV per farlo sembrare stabile sarebbe peggio: un numero fermo che
#: non misura piu' il tempo.
MACHINE_DEPENDENT = ("TTV_p90_s",)


@dataclass(frozen=True, slots=True)
class Outcome:
    """Cio' che il sistema sotto test consegna per un caso."""
    published: bool                     # ha superato il gate di pubblicazione
    values: dict[str, object]           # per request_id: Fraction o Cyc12, sempre esatto
    questions: int = 0                  # Domande mirate poste
    error_kind: str | None = None       # se non pubblicato


SolverUnderTest = Callable[[IR], Outcome]


@dataclass
class Report:
    total: int = 0
    published: int = 0
    correct: int = 0
    silent_errors: int = 0
    questions: int = 0
    seconds: list[float] = field(default_factory=list)
    errors: dict[str, int] = field(default_factory=lambda: dict.fromkeys(ERROR_KINDS, 0))
    coverage_note: str = ""

    @property
    def vsr(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def ser(self) -> float:
        return self.silent_errors / self.published if self.published else 0.0

    @property
    def qps(self) -> float:
        return self.questions / self.published if self.published else 0.0

    @property
    def ttv_p90(self) -> float:
        if not self.seconds:
            return 0.0
        s = sorted(self.seconds)
        return s[min(len(s) - 1, int(round(0.9 * (len(s) - 1))))]

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "published": self.published,
            "VSR": round(self.vsr, 4),
            "SER": round(self.ser, 4),
            "QPS": round(self.qps, 4),
            "TTV_p90_s": round(self.ttv_p90, 4),
            "refusal_rate": round(1 - self.published / self.total, 4) if self.total else 0.0,
            "errors": self.errors,
            "coverage": self.coverage_note,
            "campi_dipendenti_dalla_macchina": list(MACHINE_DEPENDENT),
        }


def run(cases, solver: SolverUnderTest, coverage_note: str) -> Report:
    rep = Report(coverage_note=coverage_note)
    for case in cases:
        rep.total += 1
        t0 = time.perf_counter()
        out = solver(case.ir)
        rep.seconds.append(time.perf_counter() - t0)
        if not out.published:
            kind = out.error_kind or "irrisolvibile"
            if kind not in rep.errors:
                # Cinque tipi, chiusi. Accettarne un sesto cambierebbe la forma del
                # rapporto senza che nessuno se ne accorga.
                raise ValueError(
                    f"tipo d'errore fuori dai cinque previsti: {kind}. "
                    f"Ammessi: {', '.join(ERROR_KINDS)}")
            rep.errors[kind] += 1
            continue
        rep.published += 1
        rep.questions += out.questions
        ok = True
        for r in case.ir.requests:
            want = case.expected[r.target][r.quantity]
            got = out.values.get(r.id)
            if got is None or got != want:
                ok = False
        if ok:
            rep.correct += 1
        else:
            # pubblicato col badge ma numericamente sbagliato: e' esattamente SER
            rep.silent_errors += 1
    return rep


_RIFIUTO_IRRISOLVIBILE = Outcome(published=False, values={}, error_kind="irrisolvibile")
_RIFIUTO_GRANDEZZA = Outcome(published=False, values={}, error_kind="grandezza_richiesta")


def _controlli_passano(ir: IR, sol: dict) -> bool:
    from ..domain.mna import kcl_residuals, power_balance

    return (all(r == 0 for r in kcl_residuals(ir, sol).values())
            and power_balance(ir, sol) == 0)


def _risolvi_stazionario(ir: IR, solve) -> Outcome:
    sol = solve(ir)
    if not _controlli_passano(ir, sol):
        return _RIFIUTO_IRRISOLVIBILE
    return Outcome(published=True, values={r.id: sol[r.target][r.quantity] for r in ir.requests})


def _risolvi_transitorio(ir: IR) -> Outcome:
    from ..domain.transient import CHARACTERISTIC_QUANTITY, initial_state, steady_state

    stati = {"initial_value": initial_state(ir), "final_value": steady_state(ir)}
    if any(r.quantity not in stati for r in ir.requests):
        # la costante di tempo e le radici le sapra' produrre il motore di Epic 2
        return _RIFIUTO_GRANDEZZA
    if not all(_controlli_passano(ir, s) for s in stati.values()):
        return _RIFIUTO_IRRISOLVIBILE
    values = {
        r.id: stati[r.quantity][r.target][CHARACTERISTIC_QUANTITY[ir.component(r.target).type]]
        for r in ir.requests
    }
    return Outcome(published=True, values=values)


def reference_solver(ir: IR) -> Outcome:
    """Sistema sotto test di riferimento: risolve con MNA e applica i controlli.

    Serve a dimostrare che l'harness misura davvero, sulle quattro classi di
    dominio. Non e' il prodotto: rifiuta invece di inventare cio' che non sa
    calcolare, e il Rifiuto e' un esito, non un errore (AD-13).
    """
    from ..domain.mna import solve_dc, solve_phasor

    try:
        if ir.domain == "transient":
            return _risolvi_transitorio(ir)
        if ir.domain in ("ac_sinusoidal", "three_phase"):
            return _risolvi_stazionario(ir, solve_phasor)
        return _risolvi_stazionario(ir, solve_dc)
    except (ValueError, ZeroDivisionError, KeyError):
        return _RIFIUTO_IRRISOLVIBILE
