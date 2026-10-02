"""Primi controlli semantici sul procedimento dello studente.

Il circuito resta l'IR canonico. Si controllano riduzioni R dichiarate e
osservabili DC numerici sul circuito originale; altri metodi non vengono
giudicati errati.
L'esito e' transitorio, senza profilo o punteggio dello studente.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from hashlib import sha256

from kirchhoff.domain import mna
from kirchhoff.domain.ir import IR
from kirchhoff.domain.independent_dc import solve_dc_tableau
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.transform import transform
from kirchhoff.domain.transform.applicability import motivo_non_parallelo, motivo_non_serie
from kirchhoff.domain.verify import compare_exact_solution_paths, verify


READING_STATES = frozenset({"clear", "ambiguous", "unreadable", "unsupported"})


@dataclass(frozen=True, slots=True)
class StudentStep:
    transcription: str
    operation: str
    first: str
    second: str
    claimed_value: str | None = None
    reading: str = "clear"

    def __post_init__(self) -> None:
        if self.reading not in READING_STATES:
            raise ValueError("stato di lettura sconosciuto")
        if not all(isinstance(x, str) for x in (self.transcription, self.operation, self.first, self.second)):
            raise TypeError("un passaggio richiede testo e identificatori semantici")
        if self.claimed_value is not None and not isinstance(self.claimed_value, str):
            raise TypeError("il valore dichiarato deve essere testo esatto")
        if self.claimed_value is not None and len(self.claimed_value) > 100:
            raise ValueError("valore dichiarato troppo lungo")
        if any(len(x) > 500 for x in (self.transcription, self.operation, self.first, self.second)):
            raise ValueError("passaggio troppo lungo")


@dataclass(frozen=True, slots=True)
class StudentTrace:
    circuit_fingerprint: str
    steps: tuple[StudentStep, ...]
    schema: str = "student-trace.v1"

    def __post_init__(self) -> None:
        if self.schema != "student-trace.v1":
            raise ValueError("versione del procedimento non supportata")
        if len(self.circuit_fingerprint) != 64 or any(c not in "0123456789abcdef" for c in self.circuit_fingerprint):
            raise ValueError("impronta del circuito non valida")
        if not 1 <= len(self.steps) <= 32:
            raise ValueError("indica da uno a 32 passaggi")
        if not all(isinstance(step, StudentStep) for step in self.steps):
            raise TypeError("StudentTrace richiede passaggi semantici, non immagini o testo grezzo")


def diagnose(ir: IR, trace: StudentTrace, netlist: str) -> dict:
    """Si ferma al primo errore provato o al primo passo non valutabile.

    Il fingerprint lega la trace al testo confermato. L'IR di lavoro e' una copia
    del circuito senza domanda, per ammettere la riduzione del componente
    richiesto prima della ricostruzione dell'osservabile. Non certifica il
    risultato finale né un metodo non rappresentato qui.
    """
    if trace.circuit_fingerprint != sha256(netlist.encode()).hexdigest():
        raise ValueError("Il circuito è cambiato: ricontrolla i passaggi sulla revisione attuale.")
    current = replace(ir, requests=())
    observed_dc = None
    for index, step in enumerate(trace.steps, 1):
        base = dict(schema="student-diagnosis.v1", step=index,
                    circuit_fingerprint=trace.circuit_fingerprint,
                    focus=[step.first, step.second])
        if step.reading != "clear":
            return {**base, "outcome": "not_assessable", "category": step.reading,
                    "message": "Non riesco a leggere con sicurezza questo passaggio; chiariscilo prima del controllo."}
        if step.operation in {"corrente", "tensione"}:
            base["focus"] = [step.first]
            try:
                component = ir.component(step.first)
            except KeyError:
                return {**base, "outcome": "not_assessable", "category": "identifier",
                        "message": "Questo componente non appartiene al circuito originale confermato."}
            if not step.claimed_value:
                return {**base, "outcome": "not_assessable", "category": "transcription",
                        "message": "Indica il valore numerico esatto che hai scritto per poterlo controllare."}
            try:
                claimed = Fraction(step.claimed_value)
            except (ValueError, ZeroDivisionError):
                return {**base, "outcome": "not_assessable", "category": "transcription",
                        "message": "Il valore scritto non è un numero esatto leggibile; correggi la trascrizione."}
            if observed_dc is None:
                try:
                    tableau = solve_dc_tableau(ir)
                    nodal = mna.solve_dc(ir)
                except (ValueError, TypeError):
                    return {**base, "outcome": "not_assessable", "category": "proof",
                            "message": "Questo osservabile non è certificabile nel circuito confermato; non lo considero errato."}
                if compare_exact_solution_paths(nodal, tableau) is not None or verify(ir, nodal) is not None:
                    return {**base, "outcome": "not_assessable", "category": "proof",
                            "message": "I controlli indipendenti del circuito non concordano; nessun passaggio dello studente viene giudicato errato."}
                observed_dc = nodal
            quantity = "current" if step.operation == "corrente" else "voltage"
            unit = "A" if quantity == "current" else "V"
            expected = observed_dc[component.id][quantity]
            if claimed != expected:
                t0, t1 = component.terminals
                return {**base, "outcome": "first_invalid", "category": "value",
                        "message": f"Per {component.id}, {step.operation} orientata {t0} → {t1}: {expected} {unit}, non {claimed} {unit}. Il metodo scritto non è giudicato da questo controllo."}
            continue
        if step.operation not in {"serie", "parallelo"}:
            return {**base, "outcome": "not_assessable", "category": "method",
                    "message": "Questo metodo non è ancora verificabile qui; non lo considero errato."}
        try:
            a, b = current.component(step.first), current.component(step.second)
        except KeyError:
            return {**base, "outcome": "not_assessable", "category": "identifier",
                    "message": "Un identificatore non corrisponde al circuito di questo passaggio; controlla la trascrizione."}
        if a.id == b.id or a.type != "resistor" or b.type != "resistor":
            return {**base, "outcome": "not_assessable", "category": "model",
                    "message": "Posso verificare questa riduzione soltanto fra due resistori distinti."}
        reason = (motivo_non_serie(current, a, b) if step.operation == "serie"
                  else motivo_non_parallelo(a, b))
        if reason:
            return {**base, "outcome": "first_invalid", "category": "topology",
                    "message": reason}
        expected = (a.value.amount + b.value.amount if step.operation == "serie"
                    else a.value.amount * b.value.amount / (a.value.amount + b.value.amount))
        if step.claimed_value is not None:
            try:
                claimed = Fraction(step.claimed_value)
            except (ValueError, ZeroDivisionError):
                return {**base, "outcome": "not_assessable", "category": "transcription",
                        "message": "Il valore scritto non è un numero esatto leggibile; correggi la trascrizione."}
            if claimed != expected:
                return {**base, "outcome": "first_invalid", "category": "algebra",
                        "message": f"La riduzione è applicabile, ma il valore equivalente è {expected} ohm, non {claimed} ohm."}
        try:
            result = transform(current, step.operation, a.id, b.id)
        except (ValueError, NotImplementedError):
            return {**base, "outcome": "not_assessable", "category": "proof",
                    "message": "La riduzione non è certificabile con queste condizioni; non la considero errata."}
        if isinstance(result, Refusal):
            return {**base, "outcome": "not_assessable", "category": "proof",
                    "message": "La riduzione non è certificabile con queste condizioni; non la considero errata."}
        current = result[0]
    return dict(schema="student-diagnosis.v1", outcome="valid_so_far", step=None,
                category=None, focus=[], circuit_fingerprint=trace.circuit_fingerprint,
                message="I passaggi controllati sono validi fin qui; il procedimento completo resta da verificare.")
