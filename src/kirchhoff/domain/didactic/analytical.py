"""Passi analitici: il circuito resta fermo, lo stato matematico avanza."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from ..ir import IR, REFERENCE_NODE
from ..proof.graph import ProofGraph
from .derivation import (
    DerivationState,
    ExactEquation,
    NodalTerm,
    NodalVariable,
    nome_tensione,
)
from .kinds import ANALYTICAL_KINDS


@dataclass(frozen=True, slots=True)
class AnalyticalStep:
    """Un atto didattico che non è una Trasformazione circuitale."""

    kind: str
    proof_node: str
    derivation_before: str
    derivation_after: str
    focused_entities: tuple[str, ...]
    equations: tuple[ExactEquation, ...]
    evidence: str

    def __post_init__(self) -> None:
        if self.kind not in ANALYTICAL_KINDS:
            raise ValueError(
                f"passo {self.kind!r} fuori da {', '.join(sorted(ANALYTICAL_KINDS))}")
        if not self.proof_node:
            raise ValueError("AnalyticalStep senza ProofNode")
        if self.derivation_before == self.derivation_after:
            raise ValueError(
                f"{self.kind}: derivation_before e derivation_after coincidono. "
                "Un passo analitico deve mutare lo stato matematico.")
        if not self.evidence:
            raise ValueError(f"{self.kind}: evidence vuota")
        object.__setattr__(self, "focused_entities", tuple(self.focused_entities))
        object.__setattr__(self, "equations", tuple(self.equations))


def stato_iniziale(proof_node: str) -> DerivationState:
    """D0: ancora nessuna convenzione nodale, ancorato al circuito originale."""
    return DerivationState("D0", proof_node)


def _prossimo_id(stato: DerivationState) -> str:
    if not stato.identifier.startswith("D") or not stato.identifier[1:].isdigit():
        raise ValueError(
            f"identificatore di derivazione non sequenziale: {stato.identifier!r}")
    return f"D{int(stato.identifier[1:]) + 1}"


def _generatori_verso_riferimento(ir: IR) -> dict[str, str]:
    """Nodo → id del generatore di tensione che lo fissa rispetto al riferimento."""
    fissi: dict[str, str] = {}
    for c in ir.components:
        if c.type != "voltage_source_dc":
            continue
        p, q = c.terminals
        if p == REFERENCE_NODE and q != REFERENCE_NODE:
            fissi[q] = c.id
        elif q == REFERENCE_NODE and p != REFERENCE_NODE:
            fissi[p] = c.id
    return fissi


def nodo_della_prima_kcl(ir: IR) -> str | None:
    """Il primo nodo, in ordine, su cui una KCL resistiva è scrivibile senza supernodo."""
    toccati_da_v = {
        t
        for c in ir.components
        if c.type == "voltage_source_dc"
        for t in c.terminals
    }
    candidati = []
    for nodo in ir.nodes:
        if nodo == REFERENCE_NODE or nodo in toccati_da_v:
            continue
        if any(c.type == "resistor" and nodo in c.terminals for c in ir.components):
            candidati.append(nodo)
    return min(candidati) if candidati else None


def _kcl_al_nodo(ir: IR, nodo: str) -> ExactEquation:
    termini: list[NodalTerm] = []
    for c in ir.components:
        if c.type != "resistor" or nodo not in c.terminals:
            continue
        altro = c.terminals[1] if c.terminals[0] == nodo else c.terminals[0]
        termini.append(NodalTerm(
            c.id, Fraction(1, c.value.amount), nodo, altro,
        ))
    return ExactEquation("kcl", nodo, tuple(termini))


def _scegli_riferimento(ir: IR, prima: DerivationState) -> tuple[AnalyticalStep, DerivationState]:
    if prima.reference_node is not None:
        raise ValueError(
            f"{prima.identifier}: il riferimento è già {prima.reference_node}")
    dopo = DerivationState(
        identifier=_prossimo_id(prima),
        proof_node=prima.proof_node,
        reference_node=REFERENCE_NODE,
        variables=(NodalVariable(nome_tensione(REFERENCE_NODE), REFERENCE_NODE, "reference"),),
        assumptions=("verso_dai_terminali", "riferimento_convenzione_IR"),
    )
    passo = AnalyticalStep(
        kind="choose_reference",
        proof_node=prima.proof_node,
        derivation_before=prima.identifier,
        derivation_after=dopo.identifier,
        focused_entities=(REFERENCE_NODE,),
        equations=(),
        evidence="reference_node_convention",
    )
    return passo, dopo


def _definisci_incognite(ir: IR, prima: DerivationState) -> tuple[AnalyticalStep, DerivationState]:
    if prima.reference_node is None:
        raise ValueError(
            f"{prima.identifier}: non si definiscono incognite prima del riferimento")
    if any(v.role == "unknown" for v in prima.variables):
        raise ValueError(f"{prima.identifier}: le incognite nodali sono già definite")
    fissi = _generatori_verso_riferimento(ir)
    variabili = list(prima.variables)
    focused: list[str] = []
    for nodo in sorted(n for n in ir.nodes if n != prima.reference_node):
        if nodo in fissi:
            ruolo, sorgente = "known_from_source", fissi[nodo]
        else:
            ruolo, sorgente = "unknown", None
        variabili.append(NodalVariable(nome_tensione(nodo), nodo, ruolo, sorgente))
        focused.append(nodo)
    if not any(v.role == "unknown" for v in variabili):
        raise ValueError(
            "nessuna tensione nodale incognita: tutti i nodi sono riferimento "
            "o fissati da un generatore verso massa")
    dopo = replace(
        prima,
        identifier=_prossimo_id(prima),
        variables=tuple(variabili),
    )
    passo = AnalyticalStep(
        kind="define_nodal_unknowns",
        proof_node=prima.proof_node,
        derivation_before=prima.identifier,
        derivation_after=dopo.identifier,
        focused_entities=tuple(focused),
        equations=(),
        evidence="nodes_minus_reference_and_grounded_sources",
    )
    return passo, dopo


def _scrivi_kcl(ir: IR, prima: DerivationState) -> tuple[AnalyticalStep, DerivationState]:
    if not any(v.role == "unknown" for v in prima.variables):
        raise ValueError(
            f"{prima.identifier}: KCL senza incognite nodali definite")
    nodo = nodo_della_prima_kcl(ir)
    if nodo is None:
        raise ValueError(
            "nessun nodo ammette una KCL resistiva senza supernodo in questo slice")
    try:
        prima.variabile_del_nodo(nodo)
    except KeyError as exc:
        raise ValueError(
            f"il nodo {nodo} della KCL non ha una variabile in {prima.identifier}"
        ) from exc
    equazione = _kcl_al_nodo(ir, nodo)
    dopo = replace(prima, identifier=_prossimo_id(prima))
    passo = AnalyticalStep(
        kind="write_kcl",
        proof_node=prima.proof_node,
        derivation_before=prima.identifier,
        derivation_after=dopo.identifier,
        focused_entities=(nodo,),
        equations=(equazione,),
        evidence="kcl_leaving_currents_ohm",
    )
    return passo, dopo


def applica_passo(
    kind: str, ir: IR, prima: DerivationState,
) -> tuple[AnalyticalStep, DerivationState]:
    """Esegue un passo analitico. Il `CircuitIR` non entra nel prodotto."""
    if kind == "choose_reference":
        return _scegli_riferimento(ir, prima)
    if kind == "define_nodal_unknowns":
        return _definisci_incognite(ir, prima)
    if kind == "write_kcl":
        return _scrivi_kcl(ir, prima)
    raise ValueError(
        f"passo {kind!r} fuori da {', '.join(sorted(ANALYTICAL_KINDS))}")


def il_grafo_resta_fermo(prima: ProofGraph, dopo: ProofGraph) -> bool:
    """Vero quando nessun arco è stato inventato per coprire un passo analitico."""
    return prima.nodes == dopo.nodes and prima.edges == dopo.edges
