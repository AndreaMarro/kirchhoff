"""Proiezione di presentazione: dalla chiusura alla vista studente.

L'unico contratto tipizzato fra Python e il browser (`StudentSessionView`).
Il browser riceve valori di presentazione immutabili — stringhe esatte,
SVG semantici, riferimenti stabili — e **nessun secondo modello di
dominio**: nessuna legge di Kirchhoff, nessuna equivalenza serie/parallelo,
nessuna equazione nodale, nessun criterio di applicabilita' vive in
TypeScript. I decimali leggibili sono calcolati qui da `Fraction`, mai in
JavaScript da float che hanno perso l'esattezza.

Il proiettore non orchestra, non pianifica, non risolve, non certifica:
consuma la chiusura della radice canonica piu' la run che l'ha prodotta
(`run_proof_session_con_run`, stessa implementazione, zero divergenze) e
le proietta. Senza evidenza certificata non c'e' proiezione.
"""

from __future__ import annotations

import dataclasses
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from kirchhoff.domain.didactic.execute import TransformExecution
from kirchhoff.domain.proof.session import (
    AnalyticalProofStep,
    TransformProofStep,
)
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.state_registry import StateRef
from kirchhoff.render.layout import LayoutStore, PatchStore
from kirchhoff.render.serialize import render
from kirchhoff.render.step import componi

if TYPE_CHECKING:
    from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
    from kirchhoff.domain.ir import IR
    from kirchhoff.domain.proof.session import ProofSession
    from kirchhoff.domain.refusal import Refusal
    from kirchhoff.pipeline.state_registry import CircuitStateRegistry
    from kirchhoff.render.layout import LayoutIR

#: Versione del contratto di presentazione. Chiusa come ogni pin semantico:
#: il frontend valida questo valore al confine e rifiuta il resto.
SCHEMA_VERSION = "student-session.v0.1"

Outcome = Literal["closed", "refusal", "failure"]


def decimale(f, cifre: int = 4) -> str:
    """Il valore leggibile ACCANTO a quello esatto, mai al suo posto."""
    return f"{float(f):.{cifre}g}"


def equazione_analitica(equazione) -> str:
    """L'equazione esatta in una riga di testo, per sola lettura.

    Formattazione di presentazione a valle dell'autorita' matematica
    (`terms` e `rhs` restano nella run): i coefficienti sono `Fraction`
    rese tali e quali, mai float. Il frontend non formatta matematica.
    """
    membri = " + ".join(
        f"{t.coefficient}·{t.variable.kind}({t.variable.node})"
        for t in equazione.terms)
    testo = f"{equazione.kind}({equazione.focus}): {membri} = {equazione.rhs}"
    return testo.replace("+ -", "- ")


@dataclass(frozen=True, slots=True)
class QuestionView:
    request_id: str
    quantity: str
    target: str


@dataclass(frozen=True, slots=True)
class AnswerView:
    target: str
    quantity: str
    exact: str
    decimal: str
    unit: str


@dataclass(frozen=True, slots=True)
class TruthView:
    electrical_claim_status: str | None
    backend_closure_status: str | None
    product_verified: bool = False


@dataclass(frozen=True, slots=True)
class StateView:
    ref: str
    svg: str
    description: str


@dataclass(frozen=True, slots=True)
class EntityView:
    kind: str
    id: str


@dataclass(frozen=True, slots=True)
class StepView:
    index: int
    kind: str
    before_ref: str
    after_ref: str
    action: str | None
    equation: str | None
    equations: tuple[str, ...]
    affected: tuple[EntityView, ...]
    preserved: tuple[EntityView, ...]
    evidence_refs: tuple[str, ...]
    before_svg: str | None
    after_svg: str | None


@dataclass(frozen=True, slots=True)
class VerificationView:
    claim_status: str | None
    claim_verifier: str | None
    claim_version: str | None
    claim_subjects: tuple[str, ...]
    session_status: str | None
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProvenanceView:
    producer: str
    source_sha: str
    detail: str


@dataclass(frozen=True, slots=True)
class RefusalView:
    cause: str
    subject: str
    subject_kind: str
    diagnosis: str


@dataclass(frozen=True, slots=True)
class FailureView:
    dove: str
    messaggio: str


@dataclass(frozen=True, slots=True)
class StudentSessionView:
    schema_version: str
    session_id: str
    outcome: Outcome
    question: QuestionView | None
    answer: AnswerView | None
    truth: TruthView
    states: tuple[StateView, ...]
    steps: tuple[StepView, ...]
    verification: VerificationView | None
    provenance: ProvenanceView | None
    refusal: RefusalView | None
    failure: FailureView | None

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema {self.schema_version!r}: il contratto e' {SCHEMA_VERSION!r}")
        if self.outcome == "closed":
            if self.answer is None or self.verification is None:
                raise ValueError("chiusura senza risposta o senza evidenza")
            if self.refusal is not None or self.failure is not None:
                raise ValueError("chiusura con rifiuto o guasto")
        elif self.outcome == "refusal":
            if self.refusal is None or self.answer is not None:
                raise ValueError("rifiuto senza diagnosi o con risposta")
        elif self.outcome == "failure":
            if self.failure is None or self.answer is not None:
                raise ValueError("guasto senza messaggio o con risposta")
        else:
            raise ValueError(f"esito {self.outcome!r} fuori dal vocabolario")


def to_json(vista: StudentSessionView) -> str:
    """La vista in JSON canonico: chiavi ordinate, solo tipi JSON."""
    return json.dumps(
        dataclasses.asdict(vista), sort_keys=True, ensure_ascii=False)


def _descrizione(svg: str, ref: str) -> str:
    try:
        radice = ET.fromstring(svg)
    except ET.ParseError:
        return f"stato {ref}"
    for elemento in radice.iter():
        if elemento.tag.endswith("desc") and (elemento.text or "").strip():
            return elemento.text.strip()
    return f"stato {ref}"


def _entita(ir, nome: str) -> EntityView:
    if nome in ir.nodes:
        return EntityView("node", nome)
    try:
        ir.component(nome)
        return EntityView("component", nome)
    except KeyError:
        raise ValueError(
            f"{nome!r} non e' ne' nodo ne' componente dello stato") from None


def project_refusal(
    rifiuto: Refusal,
    domanda: QuestionView,
    *,
    source_sha: str,
    detail: str,
) -> StudentSessionView:
    """La superficie «Non certificata»: diagnosi onesta, nessuna risposta."""
    return StudentSessionView(
        schema_version=SCHEMA_VERSION,
        session_id="",
        outcome="refusal",
        question=domanda,
        answer=None,
        truth=TruthView(None, None),
        states=(),
        steps=(),
        verification=None,
        provenance=ProvenanceView(
            "kirchhoff.pipeline.presentation", source_sha, detail),
        refusal=RefusalView(
            rifiuto.cause, rifiuto.subject, rifiuto.subject_kind,
            rifiuto.diagnosis),
        failure=None)


def project_failure(
    guasto: Failure,
    domanda: QuestionView | None,
    *,
    source_sha: str,
    detail: str,
) -> StudentSessionView:
    """La superficie del guasto: visivamente e semanticamente distinta."""
    return StudentSessionView(
        schema_version=SCHEMA_VERSION,
        session_id="",
        outcome="failure",
        question=domanda,
        answer=None,
        truth=TruthView(None, None),
        states=(),
        steps=(),
        verification=None,
        provenance=ProvenanceView(
            "kirchhoff.pipeline.presentation", source_sha, detail),
        refusal=None,
        failure=FailureView(guasto.dove, guasto.messaggio))


def project_closed_session(
    chiusura_sessione: ProofSession,
    registro: CircuitStateRegistry,
    run: CertifiedDidacticRun,
    *,
    layout_iniziale: LayoutIR,
    istante: int,
    casualita: bytes,
) -> StudentSessionView | Failure:
    """Dalla chiusura certificata alla vista studente: proiezione soltanto.

    Ogni fatto visibile risale a un artefatto del kernel: gli stati al
    registro, i passi alle esecuzioni certificate, l'equazione al prodotto,
    la risposta esatta alla soluzione risolta. `layout_iniziale` e' fornito
    dal chiamante (maglia calcolata o disposizione a mano riesaminata);
    la continuita' fra stati nasce da `applica` via `componi`, mai da un
    ricalcolo. Il fotogramma d'apertura e' reso senza overlay: l'equazione
    del passo si mostra col passo, non prima (BEFORE, poi ACTION).
    """
    try:
        _verifica_coerenza(chiusura_sessione, run)
    except Exception as e:
        return Failure("projection", f"{type(e).__name__}: {e}")
    try:
        return _proietta(
            chiusura_sessione, registro, run,
            layout_iniziale=layout_iniziale, istante=istante,
            casualita=casualita)
    except Exception as e:
        return Failure("render", f"{type(e).__name__}: {e}")


def _verifica_coerenza(sessione: ProofSession, run: CertifiedDidacticRun) -> None:
    passi_topologici = [p for p in sessione.steps if isinstance(p, TransformProofStep)]
    passi_analitici = [p for p in sessione.steps if isinstance(p, AnalyticalProofStep)]
    if len(passi_topologici) != len(run.transform_executions):
        raise ValueError(
            f"{len(passi_topologici)} passi topologici contro "
            f"{len(run.transform_executions)} esecuzioni certificate")
    nodale = run.final_execution.execution
    if len(passi_analitici) != len(nodale.steps):
        raise ValueError(
            f"{len(passi_analitici)} passi analitici contro "
            f"{len(nodale.steps)} atti nodali certificati")
    for numero, (passo, esecuzione) in enumerate(
            zip(passi_topologici, run.transform_executions)):
        if not isinstance(esecuzione, TransformExecution):
            raise ValueError(f"esecuzione {numero} non trasformativa")
        if passo.operation != esecuzione.plan.actions[0].kind:
            raise ValueError(
                f"il passo {numero} dice {passo.operation!r} mentre la run ha "
                "certificato altro: la sessione non coincide con la run")


def _proietta(sessione, registro, run, *, layout_iniziale, istante, casualita):
    passi_topologici = [p for p in sessione.steps if isinstance(p, TransformProofStep)]
    passi_analitici = [p for p in sessione.steps if isinstance(p, AnalyticalProofStep)]
    nodale = run.final_execution.execution

    layouts, patches = LayoutStore(), PatchStore()
    layouts.deposita(layout_iniziale)

    iniziale = registro.resolve(StateRef(sessione.initial_state_ref))
    apertura = render(iniziale, layout_iniziale)

    # La catena visuale segue la continuita' dei disegni, non i nomi dei ref:
    # con un retarget l'after letterale differisce dallo stato operativo per
    # le Request rilegate, ma i piazzamenti nominano nodi e componenti — mai
    # domande — quindi il disegno dopo resta valido per lo stato prima.
    per_stato: dict[str, LayoutIR] = {sessione.initial_state_ref: layout_iniziale}
    disegno_corrente = layout_iniziale
    fotogrammi: dict[int, tuple[str, str]] = {}

    for numero, (passo, esecuzione) in enumerate(
            zip(passi_topologici, run.transform_executions)):
        esito = componi(
            esecuzione, layout=disegno_corrente, layouts=layouts,
            patches=patches, istante=istante + numero,
            casualita=casualita)
        if isinstance(esito, Failure):
            raise ValueError(f"proiezione del passo {numero}: {esito.messaggio}")
        fotogrammi[numero] = (
            esito.fotogrammi[esito.prima], esito.fotogrammi[esito.dopo])
        disegno_corrente = layouts.risolvi(esito.dopo)
        successivo = passi_topologici[numero + 1].before_state_ref \
            if numero + 1 < len(passi_topologici) else sessione.final_state_ref
        per_stato[successivo] = disegno_corrente

    stati: list[StateView] = []
    for ordine, ref in enumerate(sessione.state_refs):
        ir = registro.resolve(StateRef(ref))
        disegno = per_stato.get(ref)
        if disegno is None:
            raise ValueError(f"stato {ref} senza disposizione visuale")
        svg = apertura if ordine == 0 else render(ir, disegno)
        stati.append(StateView(ref, svg, _descrizione(svg, ref)))

    passi: list[StepView] = []
    for numero, (passo, esecuzione) in enumerate(
            zip(passi_topologici, run.transform_executions)):
        risultato = esecuzione.results[0]
        cambiati = sorted(
            set(risultato.delta.consumed) | set(risultato.delta.produced))
        passi.append(StepView(
            index=passo.index,
            kind="transform",
            before_ref=passo.before_state_ref,
            after_ref=passo.after_state_ref,
            action=passo.operation,
            equation=str(risultato.equation),
            equations=(str(risultato.equation),),
            affected=tuple(EntityView(e.kind, e.id) for e in cambiati),
            preserved=tuple(
                EntityView(e.kind, e.id) for e in sorted(risultato.preserve)),
            evidence_refs=(passo.before_state_ref, passo.after_state_ref),
            before_svg=fotogrammi[numero][0],
            after_svg=fotogrammi[numero][1]))

    for passo, atto in zip(passi_analitici, nodale.steps):
        ir = registro.resolve(StateRef(passo.state_ref))
        equazioni = tuple(equazione_analitica(e) for e in atto.equations)
        passi.append(StepView(
            index=passo.index,
            kind="analytical",
            before_ref=passo.state_ref,
            after_ref=passo.state_ref,
            action=passo.kind,
            equation=equazioni[0] if equazioni else None,
            equations=equazioni,
            affected=tuple(_entita(ir, nome) for nome in atto.focused_entities),
            preserved=(),
            evidence_refs=(passo.state_ref,),
            before_svg=None,
            after_svg=None))

    passi.sort(key=lambda p: p.index)
    soluzione = sessione.final_solution
    domanda = sessione.original_request
    return StudentSessionView(
        schema_version=SCHEMA_VERSION,
        session_id=sessione.session_id,
        outcome="closed",
        question=QuestionView(domanda.id, domanda.quantity, domanda.target),
        answer=AnswerView(
            domanda.target, domanda.quantity,
            str(soluzione.value.amount), decimale(soluzione.value.amount),
            soluzione.value.unit),
        truth=TruthView(
            sessione.final_claim.status, sessione.publication_status),
        states=tuple(stati),
        steps=tuple(passi),
        verification=VerificationView(
            sessione.final_claim.status,
            sessione.final_claim.verifier_id,
            sessione.final_claim.verifier_version,
            tuple(sessione.final_claim.subject_ids),
            sessione.publication_status,
            tuple(sessione.final_claim.evidence_ids)),
        provenance=ProvenanceView(
            sessione.provenance.producer, sessione.provenance.source_sha,
            sessione.provenance.detail),
        refusal=None,
        failure=None)
