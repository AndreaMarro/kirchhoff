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


def _definisci_incognite(ir: IR, prima: DerivationState) -> tuple[AnalyticalStep, DerivationState]:
    """Dichiara le tensioni nodali: incognite piu' noti da generatore verso massa.

    Uno stato terminale senza incognite dichiara comunque i noti: e' una
    derivazione valida a zero equazioni, non un rifiuto. Rifiuta solo quando
    non c'e' nulla da dichiarare oltre il riferimento.
    """
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
            sorgente, valore = fissi[nodo]
            variabili.append(NodalVariable(
                nome_tensione(nodo), nodo, "known_from_source", sorgente, valore,
            ))
        else:
            variabili.append(NodalVariable(nome_tensione(nodo), nodo, "unknown"))
        focused.append(nodo)
    if not focused:
        raise ValueError(
            f"{prima.identifier}: nessun nodo oltre il riferimento, "
            "niente da dichiarare")
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
        evidence="kcl_leaving_currents_dc",
    )
    return passo, dopo


@dataclass(frozen=True, slots=True, order=True)
class SimpleSupernode:
    """Una voltage_source_dc flottante fra due nodi unknown disgiunti."""

    source_id: str
    p: str
    q: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("supernodo senza source_id")
        if not self.p or not self.q:
            raise ValueError("supernodo senza nodi")
        if self.p == self.q:
            raise ValueError(f"supernodo {self.source_id}: nodi coincidenti")
        if REFERENCE_NODE in (self.p, self.q):
            raise ValueError(
                f"supernodo {self.source_id}: tocca il riferimento {REFERENCE_NODE}")


def _sorgenti_tensione_flottanti(ir: IR):
    """Generatori di tensione DC che non toccano il riferimento."""
    return tuple(
        c for c in ir.components
        if c.type == "voltage_source_dc" and REFERENCE_NODE not in c.terminals
    )


def _conteggio_flottanti_per_nodo(ir: IR) -> dict[str, int]:
    conteggio: dict[str, int] = {}
    for c in _sorgenti_tensione_flottanti(ir):
        for nodo in c.terminals:
            conteggio[nodo] = conteggio.get(nodo, 0) + 1
    return conteggio


def _altro_terminale(component, nodo: str) -> str:
    p, q = component.terminals
    return q if p == nodo else p


def _precondizioni_topologiche_supernodo(ir: IR, sn: SimpleSupernode) -> None:
    """Identità del paio flottante: due unknown disgiunti, niente catene."""
    try:
        sorgente = ir.component(sn.source_id)
    except KeyError as exc:
        raise ValueError(
            f"supernodo {sn.source_id}: componente assente dal CircuitIR"
        ) from exc
    if sorgente.type != "voltage_source_dc":
        raise ValueError(
            f"supernodo {sn.source_id}: {sorgente.type} non è voltage_source_dc")
    if sorgente.terminals != (sn.p, sn.q):
        raise ValueError(
            f"supernodo {sn.source_id}: terminali {sorgente.terminals} "
            f"diversi da ({sn.p!r}, {sn.q!r})")
    fissi = _generatori_verso_riferimento(ir)
    noti = tuple(n for n in (sn.p, sn.q) if n in fissi)
    if noti:
        raise ValueError(
            f"supernodo {sn.source_id}: nodi noti da generatore verso "
            f"riferimento ({', '.join(noti)})")
    occorrenze = _conteggio_flottanti_per_nodo(ir)
    if occorrenze.get(sn.p, 0) != 1 or occorrenze.get(sn.q, 0) != 1:
        raise ValueError(
            f"supernodo {sn.source_id}: catena o sovrapposizione di "
            "generatori flottanti")


def _precondizioni_kcl_supernodo(ir: IR, sn: SimpleSupernode) -> None:
    """Fail-closed: KCL di un supernodo semplice, senza catene né overlap.

    I rami interni al paio (p, q) non escono dal supernodo. Serve almeno
    un resistore sulla frontiera, altrimenti l'equazione non contiene
    variabili di tensione. I generatori di corrente di frontiera sono
    ammessi nel termine noto.
    """
    _precondizioni_topologiche_supernodo(ir, sn)
    ha_resistore = False
    for nodo in (sn.p, sn.q):
        for ramo in _rami_incidenti(ir, nodo):
            if ramo.id == sn.source_id:
                continue
            altro = _altro_terminale(ramo, nodo)
            if altro in (sn.p, sn.q):
                continue
            if ramo.type not in _KCL_ORDINARIA_TIPI:
                raise ValueError(
                    f"supernodo {sn.source_id}: KCL incompleta, componenti non "
                    f"rappresentabili nello slice ({ramo.type}: {ramo.id})")
            if ramo.type == "resistor":
                ha_resistore = True
    if not ha_resistore:
        raise ValueError(
            f"supernodo {sn.source_id}: KCL senza contributo resistivo")


def supernodi_semplici(ir: IR) -> tuple[SimpleSupernode, ...]:
    """Paia flottanti semplici, in ordine canonico. La KCL si valida a parte."""
    accettati: list[SimpleSupernode] = []
    for c in _sorgenti_tensione_flottanti(ir):
        sn = SimpleSupernode(c.id, c.terminals[0], c.terminals[1])
        try:
            _precondizioni_topologiche_supernodo(ir, sn)
        except ValueError:
            continue
        accettati.append(sn)
    return tuple(sorted(accettati))


def nodi_dei_supernodi_semplici(ir: IR) -> tuple[str, ...]:
    """Nodi unknown coperti da un supernodo semplice, in ordine canonico."""
    return tuple(sorted({nodo for sn in supernodi_semplici(ir) for nodo in (sn.p, sn.q)}))


def _supernodo_di(ir: IR, source_id: str) -> SimpleSupernode:
    for sn in supernodi_semplici(ir):
        if sn.source_id == source_id:
            return sn
    raise ValueError(
        f"generatore {source_id!r} non definisce un supernodo semplice in questo slice")


def _kcl_del_supernodo(ir: IR, sn: SimpleSupernode) -> ExactEquation:
    """KCL del supernodo: Σ I_res,out = −Σ I_src,out sulla frontiera."""
    _precondizioni_kcl_supernodo(ir, sn)
    termini: list[LinearTerm] = []
    rhs = Fraction(0)
    coppia = {sn.p, sn.q}
    for nodo in (sn.p, sn.q):
        for c in _rami_incidenti(ir, nodo):
            if c.id == sn.source_id:
                continue
            altro = _altro_terminale(c, nodo)
            if altro in coppia:
                continue
            if c.type == "resistor":
                g = Fraction(1, c.value.amount)
                termini.append(LinearTerm(g, tensione_nodo(nodo)))
                termini.append(LinearTerm(-g, tensione_nodo(altro)))
                continue
            p, q = c.terminals
            if nodo == p:
                rhs -= c.value.amount
            else:
                rhs += c.value.amount
    return ExactEquation("kcl", tuple(termini), rhs, sn.source_id)


def _vincolo_tensione(ir: IR, sn: SimpleSupernode) -> ExactEquation:
    """V(p) − V(q) = amount, convenzione identica alla MNA."""
    _precondizioni_kcl_supernodo(ir, sn)
    sorgente = ir.component(sn.source_id)
    return ExactEquation(
        "voltage_constraint",
        (
            LinearTerm(Fraction(1), tensione_nodo(sn.p)),
            LinearTerm(Fraction(-1), tensione_nodo(sn.q)),
        ),
        sorgente.value.amount,
        sn.source_id,
    )


def _nodi_unknown_del_supernodo(prima: DerivationState, sn: SimpleSupernode) -> None:
    if not any(v.role == "unknown" for v in prima.variables):
        raise ValueError(
            f"{prima.identifier}: supernodo senza incognite nodali definite")
    for nodo in (sn.p, sn.q):
        try:
            variabile = prima.variabile_del_nodo(nodo)
        except KeyError as exc:
            raise ValueError(
                f"il nodo {nodo} del supernodo {sn.source_id} non ha una "
                f"variabile in {prima.identifier}"
            ) from exc
        if variabile.role != "unknown":
            raise ValueError(
                f"{prima.identifier}: il nodo {nodo} ha ruolo {variabile.role}, "
                f"non ammette un supernodo semplice in questo slice")


def scrivi_kcl_del_supernodo(
    ir: IR, prima: DerivationState, source_id: str,
) -> tuple[AnalyticalStep, DerivationState]:
    """Formula e persiste la KCL del supernodo semplice identificato dalla sorgente."""
    sn = _supernodo_di(ir, source_id)
    _nodi_unknown_del_supernodo(prima, sn)
    equazione = _kcl_del_supernodo(ir, sn)
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
        focused_entities=(sn.source_id, sn.p, sn.q),
        equations=(equazione,),
        evidence="kcl_supernode_leaving_currents_dc",
    )
    return passo, dopo


def scrivi_vincolo_tensione(
    ir: IR, prima: DerivationState, source_id: str,
) -> tuple[AnalyticalStep, DerivationState]:
    """Persiste V(p) − V(q) = amount del generatore flottante."""
    sn = _supernodo_di(ir, source_id)
    _nodi_unknown_del_supernodo(prima, sn)
    equazione = _vincolo_tensione(ir, sn)
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
        kind="write_voltage_constraint",
        proof_node=prima.proof_node,
        derivation_before=prima.identifier,
        derivation_after=dopo.identifier,
        focused_entities=(sn.source_id,),
        equations=(equazione,),
        evidence="voltage_source_terminal_convention",
    )
    return passo, dopo


def _nessun_operando(kind: str, operands: tuple[str, ...]) -> None:
    """I passi senza operando rifiutano qualsiasi tupla non vuota."""
    if operands:
        raise ValueError(
            f"kind {kind!r} non ammette operands, "
            f"operands ricevuti {operands}")


def _dispatch_write_kcl(
    ir: IR, prima: DerivationState, operands: tuple[str, ...],
) -> tuple[AnalyticalStep, DerivationState]:
    """KCL ordinaria (1 operando-nodo) o KCL di supernodo (sorgente, p, q).

    Non riseleziona il primo candidato: gli operands del piano sono
    l'identità dell'equazione. Una arità diversa da 1 o 3 è illegale.
    """
    if len(operands) == 1:
        return scrivi_kcl_al_nodo(ir, prima, operands[0])
    if len(operands) != 3:
        raise ValueError(
            f"kind 'write_kcl' richiede 1 o 3 operands, "
            f"operands ricevuti {operands}")
    source_id, p, q = operands
    sn = _supernodo_di(ir, source_id)
    attesi = (sn.source_id, sn.p, sn.q)
    if (source_id, p, q) != attesi:
        raise ValueError(
            f"operands {operands} non coincidono con {attesi}")
    return scrivi_kcl_del_supernodo(ir, prima, source_id)


def _dispatch_write_voltage_constraint(
    ir: IR, prima: DerivationState, operands: tuple[str, ...],
) -> tuple[AnalyticalStep, DerivationState]:
    """Vincolo di tensione: un solo operando, il source_id del generatore."""
    if len(operands) != 1:
        raise ValueError(
            f"kind 'write_voltage_constraint' richiede 1 operand, "
            f"operands ricevuti {operands}")
    return scrivi_vincolo_tensione(ir, prima, operands[0])


def applica_passo(
    kind: str,
    ir: IR,
    prima: DerivationState,
    *,
    operands: tuple[str, ...],
) -> tuple[AnalyticalStep, DerivationState]:
    """Esegue un passo analitico onorando gli operands della PlannedAction.

    `operands` è keyword-only e obbligatorio. Il dispatch non sceglie
    il primo nodo o il primo supernodo: formula esattamente ciò che
    il piano ha nominato. Il `CircuitIR` non entra nel prodotto.
    """
    if kind == "choose_reference":
        _nessun_operando(kind, operands)
        return _scegli_riferimento(ir, prima)
    if kind == "define_nodal_unknowns":
        _nessun_operando(kind, operands)
        return _definisci_incognite(ir, prima)
    if kind == "write_kcl":
        return _dispatch_write_kcl(ir, prima, operands)
    if kind == "write_voltage_constraint":
        return _dispatch_write_voltage_constraint(ir, prima, operands)
    raise ValueError(
        f"passo {kind!r} fuori da {', '.join(sorted(ANALYTICAL_KINDS))}")


def il_grafo_resta_fermo(prima: ProofGraph, dopo: ProofGraph) -> bool:
    """Vero quando nessun arco è stato inventato per coprire un passo analitico."""
    return prima.nodes == dopo.nodes and prima.edges == dopo.edges
