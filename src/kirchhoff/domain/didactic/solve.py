"""Riduzione e soluzione esatta di una derivazione già chiusa.

Vista algebrica derivabile da `DerivationState`. Non è una source of truth
e non rilegge il circuito: riceve solo lo stato matematico già costruito.

La rappresentazione (variabili canoniche + matrice esatta + rhs + mapping
della soluzione) è adatta a un futuro confronto con un oracolo esterno;
l'oracolo resta fuori da questo modulo.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..exact import solve_linear
from .derivation import DerivationState, NodalVariable, VariableRef


@dataclass(frozen=True, slots=True)
class ExactLinearSystem:
    """Sistema lineare esatto `A x = b` sulle sole incognite nodali.

    Vista derivabile: variabili in ordine canonico su `VariableRef`,
    righe nell'ordine didattico di `state.equations`.
    """

    variables: tuple[VariableRef, ...]
    matrix: tuple[tuple[Fraction, ...], ...]
    rhs: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if not self.variables:
            raise ValueError("ExactLinearSystem senza variabili")
        if len(self.matrix) != len(self.rhs):
            raise ValueError("ExactLinearSystem: matrix e rhs di lunghezze diverse")
        n = len(self.variables)
        if len(self.matrix) != n:
            raise ValueError("ExactLinearSystem: il sistema non è quadrato")
        viste: list[VariableRef] = []
        for variabile in self.variables:
            if not isinstance(variabile, VariableRef):
                raise TypeError(
                    f"{type(variabile).__name__} fra le variabili invece di VariableRef")
            if variabile in viste:
                raise ValueError(
                    f"ExactLinearSystem: variabile duplicata {variabile}")
            viste.append(variabile)
        if tuple(sorted(self.variables)) != self.variables:
            raise ValueError("ExactLinearSystem: variabili fuori dall'ordine canonico")
        for riga in self.matrix:
            if len(riga) != n:
                raise ValueError("ExactLinearSystem: riga di lunghezza errata")
            for coeff in riga:
                if not isinstance(coeff, Fraction):
                    raise TypeError(
                        f"coefficiente {type(coeff).__name__}, serve una Fraction")
        for valore in self.rhs:
            if not isinstance(valore, Fraction):
                raise TypeError(
                    f"rhs {type(valore).__name__}, serve una Fraction")


@dataclass(frozen=True, slots=True, order=True)
class SolvedVariable:
    """Valore nodale finale. La provenienza resta sullo stato, non qui."""

    variable: VariableRef
    value: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.variable, VariableRef):
            raise TypeError(
                f"variabile {type(self.variable).__name__}, serve un VariableRef")
        if not isinstance(self.value, Fraction):
            raise TypeError(
                f"valore {type(self.value).__name__}, serve una Fraction")


@dataclass(frozen=True, slots=True)
class DerivationSolution:
    """Ambiente nodale finale di una derivazione: noti copiati, incognite risolte."""

    derivation_id: str
    values: tuple[SolvedVariable, ...]

    def __post_init__(self) -> None:
        if not self.derivation_id:
            raise ValueError("DerivationSolution senza identificatore")
        if not self.values:
            raise ValueError(f"{self.derivation_id}: soluzione senza valori")
        for item in self.values:
            if not isinstance(item, SolvedVariable):
                raise TypeError(
                    f"{type(item).__name__} fra i valori invece di SolvedVariable")
        canonici = tuple(sorted(self.values, key=lambda item: item.variable))
        viste: set[VariableRef] = set()
        for item in canonici:
            if item.variable in viste:
                raise ValueError(
                    f"{self.derivation_id}: valore duplicato per {item.variable}")
            viste.add(item.variable)
        object.__setattr__(self, "values", canonici)

    def value_of(self, variable: VariableRef) -> Fraction:
        for item in self.values:
            if item.variable == variable:
                return item.value
        raise KeyError(variable)


def build_linear_system(state: DerivationState) -> ExactLinearSystem:
    """Riduce `state` a un sistema quadrato sulle sole incognite. Pura."""
    dichiarazioni = _chiusura_matematica(state)
    unknown_refs = tuple(sorted(
        v.ref()
        for v in state.variables
        if v.role == "unknown"
    ))
    n_eq = len(state.equations)
    n_unk = len(unknown_refs)
    if n_eq < n_unk:
        raise ValueError(
            f"{state.identifier}: derivazione incompleta, "
            f"insufficient equations ({n_eq} < {n_unk} incognite)")
    if n_eq > n_unk:
        raise ValueError(
            f"{state.identifier}: derivazione non quadrata, "
            f"excess equations ({n_eq} > {n_unk} incognite)")

    righe: list[tuple[Fraction, ...]] = []
    termini_noti: list[Fraction] = []
    for i, equazione in enumerate(state.equations):
        coeff = {ref: Fraction(0) for ref in unknown_refs}
        contributo_noti = Fraction(0)
        for termine in equazione.terms:
            dichiarazione = dichiarazioni[termine.variable]
            if dichiarazione.role == "unknown":
                coeff[termine.variable] = (
                    coeff[termine.variable] + termine.coefficient)
            else:
                contributo_noti += termine.coefficient * dichiarazione.known_value
        riga = tuple(coeff[ref] for ref in unknown_refs)
        rhs = equazione.rhs - contributo_noti
        if all(c == 0 for c in riga):
            if rhs == 0:
                raise ValueError(
                    f"{state.identifier}: riga tautologica dopo la "
                    f"sostituzione (equazione {i}, {equazione.kind}"
                    f"@{equazione.focus})")
            raise ValueError(
                f"{state.identifier}: riga contraddittoria dopo la "
                f"sostituzione (equazione {i}, {equazione.kind}"
                f"@{equazione.focus})")
        righe.append(riga)
        termini_noti.append(rhs)

    for j, ref in enumerate(unknown_refs):
        if all(riga[j] == 0 for riga in righe):
            raise ValueError(
                f"{state.identifier}: unknown node voltage {ref} "
                "is unconstrained")

    return ExactLinearSystem(
        variables=unknown_refs,
        matrix=tuple(righe),
        rhs=tuple(termini_noti),
    )


def solve_derivation(state: DerivationState) -> DerivationSolution:
    """Risolve la derivazione. Non rilegge il circuito."""
    if not any(v.role == "unknown" for v in state.variables):
        return _solve_known_only(state)
    sistema = build_linear_system(state)
    a = [list(riga) for riga in sistema.matrix]
    b = list(sistema.rhs)
    risolte = solve_linear(a, b)
    ambiente: dict[VariableRef, Fraction] = {}
    for variabile in state.variables:
        if variabile.role == "unknown":
            continue
        ambiente[variabile.ref()] = variabile.known_value
    for ref, valore in zip(sistema.variables, risolte):
        ambiente[ref] = valore
    valori = tuple(
        SolvedVariable(ref, ambiente[ref])
        for ref in sorted(ambiente)
    )
    return DerivationSolution(state.identifier, valori)


def _dichiarazioni_chiuse(state: DerivationState) -> dict[VariableRef, NodalVariable]:
    """Riferimento e noti validati, termini dichiarati. Senza vincoli di conteggio."""
    if state.reference_node is None:
        raise ValueError(f"{state.identifier}: riferimento assente")
    try:
        riferimento = state.variabile_del_nodo(state.reference_node)
    except KeyError as exc:
        raise ValueError(
            f"{state.identifier}: riferimento {state.reference_node} "
            "non dichiarato"
        ) from exc
    if riferimento.role != "reference":
        raise ValueError(
            f"{state.identifier}: il riferimento {state.reference_node} "
            f"ha ruolo {riferimento.role}, serve 'reference'")
    if riferimento.known_value != Fraction(0):
        raise ValueError(
            f"{state.identifier}: riferimento con known_value "
            f"{riferimento.known_value}, serve 0")

    dichiarazioni = {variabile.ref(): variabile for variabile in state.variables}
    for variabile in state.variables:
        if variabile.role != "unknown" and variabile.known_value is None:
            raise ValueError(
                f"{state.identifier}: {variabile.ref()} ruolo {variabile.role} "
                "senza known_value")

    for equazione in state.equations:
        for termine in equazione.terms:
            if termine.variable not in dichiarazioni:
                raise ValueError(
                    f"{state.identifier}: l'equazione {equazione.kind}@"
                    f"{equazione.focus} introduce {termine.variable} "
                    "non dichiarato")
    return dichiarazioni


def _solve_known_only(state: DerivationState) -> DerivationSolution:
    """Ambiente dei soli noti per una derivazione terminale senza incognite.

    Non e' un secondo MNA ne' un solver numerico: copia i noti validati e
    verifica che ogni equazione presente sia tautologica sui noti, rifiutando
    quelle contraddittorie. Non costruisce mai un ExactLinearSystem vuoto.
    """
    if any(v.role == "unknown" for v in state.variables):
        raise ValueError(f"{state.identifier}: incognite presenti, serve il sistema")
    dichiarazioni = _dichiarazioni_chiuse(state)
    for i, equazione in enumerate(state.equations):
        residuo = equazione.rhs
        for termine in equazione.terms:
            residuo -= termine.coefficient * dichiarazioni[termine.variable].known_value
        if residuo != 0:
            raise ValueError(
                f"{state.identifier}: riga contraddittoria sui noti "
                f"(equazione {i}, {equazione.kind}@{equazione.focus})")
    valori = tuple(
        SolvedVariable(v.ref(), v.known_value)
        for v in sorted(
            (v for v in state.variables if v.role != "unknown"),
            key=lambda v: v.ref(),
        )
    )
    return DerivationSolution(state.identifier, valori)


def _chiusura_matematica(state: DerivationState) -> dict[VariableRef, NodalVariable]:
    dichiarazioni = _dichiarazioni_chiuse(state)
    n_unknown = sum(1 for variabile in state.variables if variabile.role == "unknown")
    if n_unknown == 0:
        raise ValueError(f"{state.identifier}: nessuna incognita")
    return dichiarazioni
