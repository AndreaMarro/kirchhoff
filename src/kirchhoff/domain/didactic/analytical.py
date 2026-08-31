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


def _valore_noto_verso_riferimento(p: str, q: str, amount: Fraction) -> Fraction:
    """Valore esatto di V(nodo) imposto da `V(p) - V(q) = amount` verso massa.

    Contratto identico alla MNA: la tensione del componente è
    `v(terminals[0]) - v(terminals[1])`.
    """
    if p != REFERENCE_NODE and q == REFERENCE_NODE:
        return amount
    if p == REFERENCE_NODE and q != REFERENCE_NODE:
        return -amount
    raise ValueError(
        f"generatore {p!r}→{q!r} non è verso il riferimento {REFERENCE_NODE}")


def _generatori_verso_riferimento(ir: IR) -> dict[str, tuple[str, Fraction]]:
    """Nodo → (source_id, known_value) per ogni generatore di tensione verso massa.

    Fail-closed su un secondo binding dello stesso nodo: niente last-write-wins.
    """
    fissi: dict[str, tuple[str, Fraction]] = {}
    for c in ir.components:
        if c.type != "voltage_source_dc":
            continue
        p, q = c.terminals
        if REFERENCE_NODE not in (p, q):
            continue
        nodo = q if p == REFERENCE_NODE else p
        valore = _valore_noto_verso_riferimento(p, q, c.value.amount)
        if nodo in fissi:
            altro, _ = fissi[nodo]
            raise ValueError(
                f"nodo {nodo}: due generatori verso riferimento "
                f"({altro} e {c.id})")
        fissi[nodo] = (c.id, valore)
    return fissi


def _rami_incidenti(ir: IR, nodo: str):
    """Componenti il cui ramo tocca `nodo`. Ordine = ordine dell'IR."""
    return tuple(c for c in ir.components if nodo in c.terminals)


_KCL_ORDINARIA_TIPI: frozenset[str] = frozenset({
    "resistor",
    "current_source_dc",
})


def _precondizioni_kcl_ordinaria(ir: IR, nodo: str) -> None:
    """Fail-closed: KCL ordinaria con resistori e generatori di corrente.

    Un ramo incidente non rappresentabile rende la KCL incompleta: non
    si omette. Serve almeno un resistore, altrimenti l'equazione non
    contiene variabili di tensione e non determina il nodo.
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
    non_ammessi = tuple(c for c in incidenti if c.type not in _KCL_ORDINARIA_TIPI)
    if non_ammessi:
        tipi = ", ".join(sorted({c.type for c in non_ammessi}))
        ids = ", ".join(c.id for c in non_ammessi)
        raise ValueError(
            f"nodo {nodo}: KCL ordinaria incompleta, componenti non "
            f"rappresentabili nello slice ({tipi}: {ids})")
    if not any(c.type == "resistor" for c in incidenti):
        raise ValueError(
            f"nodo {nodo}: KCL ordinaria senza contributo resistivo")


def nodi_kcl_ordinarie(ir: IR) -> tuple[str, ...]:
    """Nodi, in ordine canonico, su cui una KCL ordinaria è scrivibile senza supernodo."""
    candidati = []
    for nodo in ir.nodes:
        try:
            _precondizioni_kcl_ordinaria(ir, nodo)
        except ValueError:
            continue
        candidati.append(nodo)
    return tuple(sorted(candidati))


def nodo_della_prima_kcl(ir: IR) -> str | None:
    """Il primo nodo, in ordine, su cui una KCL ordinaria è scrivibile senza supernodo."""
    nodi = nodi_kcl_ordinarie(ir)
    return nodi[0] if nodi else None


def _kcl_al_nodo(ir: IR, nodo: str) -> ExactEquation:
    """KCL ordinaria al nodo: Σ I_res,out = −Σ I_src,out.

    I resistori restano a sinistra come (V_nodo − V_altro)/R. I generatori
    di corrente indipendenti vanno nel termine noto, con la convenzione
    uscente positiva e l'orientamento p → q del CircuitIR.

    I contributi di V(0) restano nei termini. Il ruolo `reference` vive
    sulla dichiarazione `NodalVariable`, non sull'algebra.

    Formula ESATTAMENTE `nodo`. Non ne sceglie un altro. Rifiuta se
    un ramo incidente non è rappresentabile in questo slice.
    """
    _precondizioni_kcl_ordinaria(ir, nodo)
    termini: list[LinearTerm] = []
    rhs = Fraction(0)
    for c in _rami_incidenti(ir, nodo):
        if c.type == "resistor":
            altro = c.terminals[1] if c.terminals[0] == nodo else c.terminals[0]
            g = Fraction(1, c.value.amount)
            termini.append(LinearTerm(g, tensione_nodo(nodo)))
            termini.append(LinearTerm(-g, tensione_nodo(altro)))
            continue
        p, q = c.terminals
        if nodo == p:
            rhs -= c.value.amount
        else:
            rhs += c.value.amount
    return ExactEquation("kcl", tuple(termini), rhs, nodo)


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
        variables=(NodalVariable(
            nome_tensione(REFERENCE_NODE), REFERENCE_NODE, "reference",
            known_value=Fraction(0),
        ),),
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
