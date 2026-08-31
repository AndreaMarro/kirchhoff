"""Passi analitici: il circuito resta fermo, lo stato matematico avanza."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from ..ir import IR, REFERENCE_NODE
from ..proof.graph import ProofGraph
from .derivation import (
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    nome_tensione,
    tensione_nodo,
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


def _rami_incidenti(ir: IR, nodo: str):
    """Componenti il cui ramo tocca `nodo`. Ordine = ordine dell'IR."""
    return tuple(c for c in ir.components if nodo in c.terminals)


def _precondizioni_kcl_ordinaria(ir: IR, nodo: str) -> None:
    """Fail-closed: questo slice formula solo KCL resistive complete.

    Non filtra i rami sconosciuti: se un incidente non è un resistore,
    la KCL non si scrive. Una somma sui soli resistori sarebbe falsa.
    """
    if nodo not in ir.nodes:
        raise ValueError(f"nodo {nodo!r} assente dal CircuitIR")
    if nodo == REFERENCE_NODE:
        raise ValueError(
            f"KCL al riferimento {nodo}: non è un'equazione indipendente "
            "del sistema nodale scelto in questo slice")
    incidenti = _rami_incidenti(ir, nodo)
    if not incidenti:
        raise ValueError(f"nodo {nodo}: nessun ramo incidente")
    non_resistivi = tuple(c for c in incidenti if c.type != "resistor")
    if non_resistivi:
        tipi = ", ".join(sorted({c.type for c in non_resistivi}))
        ids = ", ".join(c.id for c in non_resistivi)
        raise ValueError(
            f"nodo {nodo}: KCL ordinaria incompleta, componenti non "
            f"rappresentabili nello slice ({tipi}: {ids})")


def nodi_kcl_ordinarie(ir: IR) -> tuple[str, ...]:
    """Nodi, in ordine canonico, su cui una KCL resistiva è scrivibile senza supernodo."""
    candidati = []
    for nodo in ir.nodes:
        try:
            _precondizioni_kcl_ordinaria(ir, nodo)
        except ValueError:
            continue
        candidati.append(nodo)
    return tuple(sorted(candidati))


def nodo_della_prima_kcl(ir: IR) -> str | None:
    """Il primo nodo, in ordine, su cui una KCL resistiva è scrivibile senza supernodo."""
    nodi = nodi_kcl_ordinarie(ir)
    return nodi[0] if nodi else None


def _kcl_al_nodo(ir: IR, nodo: str) -> ExactEquation:
    """KCL resistiva al nodo: Σ (V_nodo − V_altro)/R = 0.

    I contributi di V(0) restano nei termini. Il ruolo `reference` vive
    sulla dichiarazione `NodalVariable`, non sull'algebra.

    Formula ESATTAMENTE `nodo`. Non ne sceglie un altro. Rifiuta se
    un ramo incidente non è rappresentabile nello slice resistivo.
    """
    _precondizioni_kcl_ordinaria(ir, nodo)
    termini: list[LinearTerm] = []
    for c in _rami_incidenti(ir, nodo):
        altro = c.terminals[1] if c.terminals[0] == nodo else c.terminals[0]
        g = Fraction(1, c.value.amount)
        termini.append(LinearTerm(g, tensione_nodo(nodo)))
        termini.append(LinearTerm(-g, tensione_nodo(altro)))
    return ExactEquation("kcl", tuple(termini), Fraction(0), nodo)


def _variabili_dell_equazione_dichiarate(
    stato: DerivationState, equazione: ExactEquation,
) -> None:
    """Ogni VariableRef dell'equazione deve essere già dichiarato nello stato."""
    for termine in equazione.terms:
        try:
            stato.variabile_del_nodo(termine.variable.node)
        except KeyError as exc:
            raise ValueError(
                f"{stato.identifier}: l'equazione {equazione.kind}@"
                f"{equazione.focus} introduce {termine.variable.kind}@"
                f"{termine.variable.node} non dichiarato"
            ) from exc


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


def scrivi_kcl_al_nodo(
    ir: IR, prima: DerivationState, nodo: str,
) -> tuple[AnalyticalStep, DerivationState]:
    """Formula e persiste la KCL ordinaria del nodo richiesto.

    Il planner sceglie il nodo. Questa primitiva esegue quel nodo,
    senza riselezionarne un altro.
    """
    if not any(v.role == "unknown" for v in prima.variables):
        raise ValueError(
            f"{prima.identifier}: KCL senza incognite nodali definite")
    if nodo not in ir.nodes:
        raise ValueError(f"nodo {nodo!r} assente dal CircuitIR")
    if nodo == REFERENCE_NODE:
        raise ValueError(
            f"KCL al riferimento {nodo}: non è un'equazione indipendente "
            "del sistema nodale scelto in questo slice")
    try:
        variabile = prima.variabile_del_nodo(nodo)
    except KeyError as exc:
        raise ValueError(
            f"il nodo {nodo} della KCL non ha una variabile in {prima.identifier}"
        ) from exc
    if variabile.role != "unknown":
        raise ValueError(
            f"{prima.identifier}: il nodo {nodo} ha ruolo {variabile.role}, "
            "non ammette una KCL ordinaria in questo slice")
    equazione = _kcl_al_nodo(ir, nodo)
    _variabili_dell_equazione_dichiarate(prima, equazione)
    if equazione in prima.equations:
        raise ValueError(
            f"{prima.identifier}: equazioni duplicate {equazione.kind}@{equazione.focus}")
    dopo = replace(
        prima,
        identifier=_prossimo_id(prima),
        equations=(*prima.equations, equazione),
    )
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


def _scrivi_kcl(ir: IR, prima: DerivationState) -> tuple[AnalyticalStep, DerivationState]:
    nodo = nodo_della_prima_kcl(ir)
    if nodo is None:
        raise ValueError(
            "nessun nodo ammette una KCL resistiva senza supernodo in questo slice")
    return scrivi_kcl_al_nodo(ir, prima, nodo)


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
