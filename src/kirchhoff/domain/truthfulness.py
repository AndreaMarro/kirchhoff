"""Gate proprietario: nessuna evidenza, nessuna affermazione verificata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterable, Literal, get_args

from . import mna
from .didactic.execute import DidacticExecution, NodalExecution, TransformExecution, execute_plan
from .didactic.plan import DidacticPlan
from .exact import SingularSystemError
from .identity import verifica
from .independent_dc import TableauSingularError, solve_dc_tableau
from .ir import IR, Magnitude, Request
from .refusal import Refusal
from .verify import compare_exact_solution_paths, verify

ClaimType = Literal["resolved_quantity"]
ClaimStatus = Literal["VERIFIED"]
CLAIM_TYPES: frozenset[str] = frozenset(get_args(ClaimType))
CLAIM_STATUSES: frozenset[str] = frozenset(get_args(ClaimStatus))
VERIFIER_ID = "kirchhoff.truthfulness.nodal_dc"
VERIFIER_VERSION = "1.0.0"
SUPPORTED_NODAL_QUANTITIES = frozenset({"voltage", "current"})
_EXPECTED_UNITS = {"voltage": "volt", "current": "ampere"}
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _normalizza_ids(nome: str, ids: Iterable[str]) -> tuple[str, ...]:
    if isinstance(ids, str):
        raise TypeError(f"{nome} deve essere una sequenza di identificatori, non una stringa")
    normalizzati = tuple(ids)
    if not normalizzati:
        raise ValueError(f"{nome} non puo' essere vuoto")
    for identifier in normalizzati:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{nome} contiene un identificatore vuoto o non testuale")
    if len(set(normalizzati)) != len(normalizzati):
        raise ValueError(f"{nome} contiene identificatori duplicati")
    return normalizzati


@dataclass(frozen=True, slots=True)
class Claim:
    """Affermazione verificata con stato, soggetti ed evidenze ispezionabili."""

    claim_type: ClaimType
    state_id: str
    subject_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verifier_id: str
    verifier_version: str
    status: ClaimStatus = field(init=False, default="VERIFIED")

    def __post_init__(self) -> None:
        if self.claim_type not in CLAIM_TYPES:
            raise ValueError(f"claim_type {self.claim_type!r} fuori dal vocabolario chiuso")
        object.__setattr__(self, "state_id", verifica(self.state_id, "ir"))
        object.__setattr__(self, "subject_ids", _normalizza_ids("subject_ids", self.subject_ids))
        object.__setattr__(self, "evidence_ids", _normalizza_ids("evidence_ids", self.evidence_ids))
        if not isinstance(self.verifier_id, str) or not self.verifier_id:
            raise ValueError("Claim senza verifier_id")
        if not isinstance(self.verifier_version, str) or not _SEMVER.fullmatch(self.verifier_version):
            raise ValueError("Claim con verifier_version non semantica")


@dataclass(frozen=True, slots=True)
class CertifiedNodalExecution:
    """Esecuzione nodale e Claim finale verificato."""

    execution: NodalExecution
    claim: Claim

    def __post_init__(self) -> None:
        if not isinstance(self.execution, NodalExecution):
            raise TypeError("CertifiedNodalExecution richiede NodalExecution")
        if not isinstance(self.claim, Claim):
            raise TypeError("CertifiedNodalExecution richiede Claim")
        expected_subjects = (self.execution.resolved.request_id, self.execution.resolved.target)
        expected_evidence = tuple(step.derivation_after for step in self.execution.steps)
        if self.claim.claim_type != "resolved_quantity":
            raise ValueError("Claim incompatibile con una quantita' risolta")
        if self.claim.state_id != self.execution.proof_node:
            raise ValueError("Claim ancorato a uno stato diverso dall'esecuzione")
        if self.claim.subject_ids != expected_subjects:
            raise ValueError("Claim con subject_ids incoerenti con l'esecuzione")
        if self.claim.evidence_ids != expected_evidence:
            raise ValueError("Claim con evidence_ids incoerenti con l'esecuzione")
        if self.claim.verifier_id != VERIFIER_ID:
            raise ValueError("Claim con verifier_id non autorevole")
        if self.claim.verifier_version != VERIFIER_VERSION:
            raise ValueError("Claim con verifier_version non autorevole")
        if self.claim.status != "VERIFIED":
            raise ValueError("Claim finale senza status VERIFIED")


def _binding(request: Request, diagnosis: str) -> Refusal:
    return Refusal("identity_violation", request.id, "request", diagnosis)


def _context(ir: IR, request: Request, execution: NodalExecution) -> Refusal | None:
    if ir.domain != "dc":
        return Refusal("claim_unsupported", request.id, "request", f"domain={ir.domain!r} non supportato")
    if request.quantity not in SUPPORTED_NODAL_QUANTITIES:
        return Refusal("claim_unsupported", request.id, "request", f"quantity={request.quantity!r} non supportata")
    matches = tuple(r for r in ir.requests if r.id == request.id)
    if len(matches) != 1:
        return _binding(request, f"request {request.id!r} deve appartenere una sola volta all'IR")
    if matches[0] != request:
        return _binding(request, "Request argomento diversa dalla Request nell'IR")
    if execution.plan.request_id != request.id:
        return _binding(request, "request.id non coincide con execution.plan.request_id")
    resolved = execution.resolved
    if resolved.request_id != request.id:
        return _binding(request, "execution.resolved.request_id non coincide con Request")
    if resolved.target != request.target:
        return _binding(request, "execution.resolved.target non coincide con Request.target")
    if resolved.quantity != request.quantity:
        return _binding(request, "execution.resolved.quantity non coincide con Request.quantity")
    try:
        verifica(execution.proof_node, "ir")
    except (TypeError, ValueError) as exc:
        return _binding(request, f"invarianti di NodalExecution non verificabili: {exc}")
    return None


def _oracle_value(solution: dict, request: Request) -> Fraction | Refusal:
    try:
        value = solution[request.target][request.quantity]
    except (KeyError, TypeError):
        return Refusal("path_disagreement", request.target, "component", f"oracolo senza {request.quantity} per {request.target}")
    if not isinstance(value, Fraction):
        return Refusal("path_disagreement", request.target, "component", f"oracolo non esatto per {request.target}")
    return value


def truthfulness_gate(ir: IR, request: Request, execution: DidacticExecution) -> Claim | Refusal:
    """Certifica solo il risultato finale NodalExecution DC."""
    if not isinstance(ir, IR):
        raise TypeError(f"ir {type(ir).__name__} invece di IR")
    if not isinstance(request, Request):
        raise TypeError(f"request {type(request).__name__} invece di Request")
    if isinstance(execution, TransformExecution):
        return Refusal("claim_unsupported", request.id, "request", "TransformExecution e' intermedio, senza ResolvedQuantity finale")
    if not isinstance(execution, NodalExecution):
        raise TypeError(f"execution {type(execution).__name__} invece di DidacticExecution")
    refused = _context(ir, request, execution)
    if refused is not None:
        return refused
    try:
        mna_solution = mna.solve_dc(ir)
    except SingularSystemError as exc:
        return Refusal("path_disagreement", request.target, "component", f"derivazione risolta, MNA singolare: {exc}")
    try:
        tableau_solution = solve_dc_tableau(ir)
    except TableauSingularError as exc:
        return Refusal("path_disagreement", request.target, "component", f"derivazione risolta, tableau singolare: {exc}")
    refused = compare_exact_solution_paths(mna_solution, tableau_solution)
    if refused is not None:
        return refused
    refused = verify(ir, mna_solution)
    if refused is not None:
        return refused
    oracle_value = _oracle_value(mna_solution, request)
    if isinstance(oracle_value, Refusal):
        return oracle_value
    expected_unit = _EXPECTED_UNITS[request.quantity]
    resolved = execution.resolved
    if not isinstance(resolved.value, Magnitude) or resolved.value.unit != expected_unit:
        return Refusal("path_disagreement", request.target, "component", f"unita' didattica {getattr(resolved.value, 'unit', None)!r}, attesa {expected_unit!r}")
    if resolved.value.amount != oracle_value:
        return Refusal("path_disagreement", request.target, "component", f"grandezza didattica {request.quantity} = {resolved.value.amount}; oracolo deterministico {request.quantity} = {oracle_value}")
    return Claim("resolved_quantity", execution.proof_node, (request.id, request.target), tuple(step.derivation_after for step in execution.steps), VERIFIER_ID, VERIFIER_VERSION)


def certify_execution(ir: IR, request: Request, execution: DidacticExecution) -> CertifiedNodalExecution | Refusal:
    claim = truthfulness_gate(ir, request, execution)
    if isinstance(claim, Refusal):
        return claim
    return CertifiedNodalExecution(execution, claim)


def execute_certified_plan(ir: IR, request: Request, plan: DidacticPlan, *, proof_node: str) -> CertifiedNodalExecution | Refusal:
    """Replay di un piano ricevuto e gate: non pianifica."""
    execution = execute_plan(ir, request, plan, proof_node=proof_node)
    return certify_execution(ir, request, execution)


__all__ = ["CLAIM_STATUSES", "CLAIM_TYPES", "Claim", "ClaimStatus", "ClaimType", "CertifiedNodalExecution", "SUPPORTED_NODAL_QUANTITIES", "VERIFIER_ID", "VERIFIER_VERSION", "certify_execution", "execute_certified_plan", "truthfulness_gate"]
