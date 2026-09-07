"""`ProofSession` — la proiezione prodotto per riferimento (spec 6.1, AD-21 v2).

Una `CertifiedDidacticRun` e' la verita' didattica; questa sessione e' come la
si pubblica senza poterla alterare. Porta identificatori e certificati
congelati, mai strutture mutabili: nessun `CircuitIR`, nessun `LayoutIR`,
nessun `ProofGraph` per valore. Chi vuole le strutture risolve gli
identificatori nei registri, che e' cio' che AD-21 chiama ricostruire.

Cosa questo modulo NON fa, per costruzione:

- non risolve, non pianifica, non riesegue trasformazioni, non ricertifica;
- non conia identificatori (li verifica soltanto): coniare richiede orologio
  ed entropia, che sotto `domain/` non esistono (AD-17);
- non calcola hash del contenuto: un hash conservato dentro il contenuto
  hashato e' circolare (H3 li calcola fuori dal modello);
- non modella Refusal o Failure: un rifiuto e' un esito del dominio, un
  guasto e' un difetto applicativo, nessuno dei due e' una sessione mezza
  verificata (AD-13). Il compositore li restituisce su canali separati.

Ogni invariante ha una guardia a runtime e un test che l'ha vista sollevare:
lo stack e' Python senza type checker, quindi <<il vincolo e' nel tipo>> qui
non e' vero.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Union

from ..didactic.kinds import ANALYTICAL_KINDS, PLAN_SCHEMA_VERSION, PROFILE
from ..didactic.observation import ObservationEffect, RequestLineageStep
from ..didactic.request import ResolvedQuantity
from ..identity import verifica
from ..ir import Request
from ..transform.catalog import CATALOG
from ..truthfulness import VERIFIER_ID, VERIFIER_VERSION, Claim

#: L'unica versione di schema che questo modello legge e scrive. Aggiungere
#: una versione e' una migrazione con regole e review, non un'etichetta.
#: v0.2 (O0): la chiusura di backend non si chiama piu' VERIFIED.
SCHEMA_VERSION = "proof-session.v0.2"

#: L'unico profilo documento che lo schema/pubblicazione v0.2 riconosce (D-H2.5-3).
#: Chiuso come ogni pin semantico: un profilo arbitrario fallisce, non si
#: dichiara. Un secondo profilo richiede una nuova versione di schema.
DOCUMENT_PROFILE = "student-pdf.v0.1"

#: Il genere dell'occurrence di sessione (D-H1.5-1). Nominato una volta: il
#: vocabolario chiuso sta in `domain/identity`.
_GENERE_SESSIONE = "sess"

PublicationStatus = Literal["CLOSED"]
STATI_DI_PUBBLICAZIONE: frozenset[str] = frozenset({"CLOSED"})

_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class SessionVersions:
    """I pin semantici della sessione: solo autorita', mai numeri inventati.

    D-H1.5-2: nessuna release autorevole esiste a runtime per core,
    implementazione del planner, catalogo, layout o renderer, quindi lo schema
    non li nomina. `planner_schema_version` e `curriculum_profile` si
    confrontano per uguaglianza con l'autorita' (`didactic/kinds`), non per
    forma. D-H2.5-3: `document_profile` e' un token chiuso (`DOCUMENT_PROFILE`,
    autorita' di questo modulo come `SCHEMA_VERSION`): un profilo arbitrario
    fallisce perche' il documento prodotto dipende dal profilo.
    """

    planner_schema_version: str
    curriculum_profile: str
    document_profile: str

    def __post_init__(self) -> None:
        if self.planner_schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError(
                f"planner_schema_version {self.planner_schema_version!r}: "
                f"l'autorita' e' {PLAN_SCHEMA_VERSION!r}")
        if self.curriculum_profile != PROFILE:
            raise ValueError(
                f"curriculum_profile {self.curriculum_profile!r}: "
                f"l'autorita' e' {PROFILE!r}")
        if self.document_profile != DOCUMENT_PROFILE:
            raise ValueError(
                f"document_profile {self.document_profile!r}: "
                f"l'autorita' e' {DOCUMENT_PROFILE!r}")


@dataclass(frozen=True, slots=True)
class SessionProvenance:
    """Provenienza strutturata, leggibile da una macchina (D-H1.5-3, D-H2.5-4).

    `detail` resta per la diagnostica umana ma non e' mai l'unica provenienza:
    chi, da quale sorgente e sotto quale schema/profilo si leggono senza
    interpretare prosa.

    D-H2.5-4: `source_sha` e' la revisione produttrice *dichiarata* dal
    chiamante (forma SHA-40 esadecimale), non una revisione di checkout
    verificata: il dominio puro non tocca Git e una regex non e' un'autorita'.
    Legare questo campo ai metadati reali di build spetta alla radice di
    composizione, non al modello.
    """

    producer: str
    source_sha: str
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.producer, str) or not self.producer.strip():
            raise ValueError("provenienza senza produttore esplicito")
        if not isinstance(self.source_sha, str) or not _SHA.fullmatch(self.source_sha):
            raise ValueError(
                f"source_sha {self.source_sha!r}: serve lo SHA-40 esadecimale "
                "dichiarato dal produttore della sessione")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("provenienza senza dettaglio esplicito")


@dataclass(frozen=True, slots=True)
class TransformProofStep:
    """Un passo topologico certificato, proiettato per riferimento.

    `effect` e `lineage` sono gli oggetti P1-J della run, non copie
    ricostruite: la coerenza fra i due (operazione, effetto, target) e'
    verificata qui, la verita' elettrica resta nel `TransformResult`
    certificato a monte.
    """

    index: int
    before_state_ref: str
    after_state_ref: str
    operation: str
    effect: ObservationEffect
    lineage: RequestLineageStep

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError(
                f"indice {self.index!r}: serve un intero di posizione")
        if self.index < 0:
            raise ValueError(f"indice {self.index}: un passo non ha posizioni negative")
        object.__setattr__(
            self, "before_state_ref", verifica(self.before_state_ref, "ir"))
        object.__setattr__(
            self, "after_state_ref", verifica(self.after_state_ref, "ir"))
        if self.before_state_ref == self.after_state_ref:
            raise ValueError(
                f"{self.before_state_ref}: un passo topologico collega due stati "
                "circuitali distinti, mai uno stato a se stesso")
        if self.operation not in CATALOG:
            raise ValueError(
                f"operazione {self.operation!r} fuori dal catalogo chiuso: "
                f"{', '.join(sorted(CATALOG))}")
        if not isinstance(self.effect, ObservationEffect):
            raise TypeError(
                f"effetto {type(self.effect).__name__} invece di ObservationEffect")
        if self.effect.kind == "blocked":
            raise ValueError(
                "effetto blocked in una trace certificata: una trasformazione "
                "bloccata non viene scelta e non entra nella sessione")
        if not isinstance(self.lineage, RequestLineageStep):
            raise TypeError(
                f"lineage {type(self.lineage).__name__} invece di RequestLineageStep")
        if self.lineage.operation != self.operation:
            raise ValueError(
                f"lineage su {self.lineage.operation!r} dentro un passo "
                f"{self.operation!r}: la lineage documenta questo passo")
        if self.lineage.effect != self.effect.kind:
            raise ValueError(
                f"lineage con effetto {self.lineage.effect!r} contro effetto "
                f"del passo {self.effect.kind!r}")
        if self.effect.target_after != self.lineage.target_after:
            raise ValueError(
                f"target_after {self.effect.target_after!r} contro "
                f"{self.lineage.target_after!r}: effetto e lineage nominano lo "
                "stesso successore")


@dataclass(frozen=True, slots=True)
class AnalyticalProofStep:
    """Un passo di ragionamento a circuito fermo, proiettato per riferimento.

    Il circuito non cambia: `state_ref` e' lo stesso prima e dopo. Avanza lo
    stato matematico `derivation_before -> derivation_after` (D0, D1, ...).
    Le equazioni restano negli `AnalyticalStep` certificati a monte, qui si
    citano gli stati di derivazione che le contengono.
    """

    index: int
    state_ref: str
    kind: str
    derivation_before: str
    derivation_after: str

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError(
                f"indice {self.index!r}: serve un intero di posizione")
        if self.index < 0:
            raise ValueError(f"indice {self.index}: un passo non ha posizioni negative")
        object.__setattr__(self, "state_ref", verifica(self.state_ref, "ir"))
        if self.kind not in ANALYTICAL_KINDS:
            raise ValueError(
                f"passo {self.kind!r} fuori da {', '.join(sorted(ANALYTICAL_KINDS))}")
        if not isinstance(self.derivation_before, str):
            raise TypeError(
                f"derivation_before {type(self.derivation_before).__name__} invece di str")
        if not self.derivation_before:
            raise ValueError("passo analitico senza derivation_before")
        if not isinstance(self.derivation_after, str):
            raise TypeError(
                f"derivation_after {type(self.derivation_after).__name__} invece di str")
        if not self.derivation_after:
            raise ValueError("passo analitico senza derivation_after")
        if self.derivation_before == self.derivation_after:
            raise ValueError(
                f"{self.kind}: derivation_before e derivation_after coincidono. "
                "Un passo analitico deve mutare lo stato matematico.")


PassoDiProva = Union[TransformProofStep, AnalyticalProofStep]


@dataclass(frozen=True, slots=True)
class ProofSession:
    """Una run certificata, pubblicata come proiezione congelata e tipizzata.

    Schema v0.2: prima tutti i passi topologici, poi quelli analitici, e ogni
    passo analitico e' ancorato allo stato operativo finale (l'esecuzione
    nodale corre sempre sullo stato terminale). Un interleaving arbitrario
    richiedera' una nuova versione di schema, non un flag.

    D-H2.5-2: la sessione porta la soluzione finale per valore
    (`final_solution: ResolvedQuantity`, certificato congelato come il Claim),
    cosi' la risposta esatta e' raggiungibile senza la run viva. Il Claim resta
    l'artefatto di verifica (chi/come ha certificato), la soluzione e'
    l'artefatto di risposta (quanto vale): non sono la stessa cosa.

    O0: `publication_status` e' `CLOSED` (chiusura di pubblicazione di
    backend: integrita' referenziale + Claim elettrico autorevole). Non e'
    `VERIFIED`: quel token resta al Claim elettrico (`truthfulness`) e al
    futuro badge prodotto owner-locked, che richiede anche la chiusura
    visuale (K-0/AD-5, H5). Tre concetti, tre nomi, nessuna confusione
    meccanica possibile.
    """

    session_id: str
    schema_version: str
    versions: SessionVersions
    provenance: SessionProvenance
    original_request: Request
    initial_state_ref: str
    state_refs: tuple[str, ...]
    steps: tuple[PassoDiProva, ...]
    final_derivation_id: str
    final_request: Request
    final_state_ref: str
    final_solution: ResolvedQuantity
    final_claim: Claim
    publication_status: PublicationStatus = "CLOSED"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "session_id", verifica(self.session_id, _GENERE_SESSIONE))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema {self.schema_version!r}: questo modello legge e scrive "
                f"solo {SCHEMA_VERSION!r}")
        if not isinstance(self.versions, SessionVersions):
            raise TypeError(
                f"versions {type(self.versions).__name__} invece di SessionVersions")
        if not isinstance(self.provenance, SessionProvenance):
            raise TypeError(
                f"provenance {type(self.provenance).__name__} invece di SessionProvenance")
        if not isinstance(self.original_request, Request):
            raise TypeError(
                f"original_request {type(self.original_request).__name__} invece di Request")
        if not isinstance(self.final_request, Request):
            raise TypeError(
                f"final_request {type(self.final_request).__name__} invece di Request")
        if self.final_request.id != self.original_request.id:
            raise ValueError(
                f"final_request.id {self.final_request.id!r} contro "
                f"{self.original_request.id!r}: la lineage P1-J non cambia id")
        if self.final_request.quantity != self.original_request.quantity:
            raise ValueError(
                f"final_request.quantity {self.final_request.quantity!r} contro "
                f"{self.original_request.quantity!r}: la lineage P1-J non cambia quantity")
        if not isinstance(self.final_derivation_id, str):
            raise TypeError(
                f"final_derivation_id {type(self.final_derivation_id).__name__} invece di str")
        if not self.final_derivation_id:
            raise ValueError("sessione senza identificatore di derivazione finale")
        object.__setattr__(
            self, "initial_state_ref", verifica(self.initial_state_ref, "ir"))
        object.__setattr__(
            self, "final_state_ref", verifica(self.final_state_ref, "ir"))
        object.__setattr__(self, "state_refs", tuple(self.state_refs))
        if not self.state_refs:
            raise ValueError("sessione senza stati circuitali")
        for ref in self.state_refs:
            verifica(ref, "ir")
        if len(set(self.state_refs)) != len(self.state_refs):
            raise ValueError(
                "state_refs con identificatori ripetuti: uno stato operativo, un ref")
        if self.state_refs[0] != self.initial_state_ref:
            raise ValueError(
                "il primo state_ref non e' lo stato iniziale della sessione")
        if self.final_state_ref != self.state_refs[-1]:
            raise ValueError(
                "il final_state_ref non e' l'ultimo stato operativo della sessione")
        object.__setattr__(self, "steps", tuple(self.steps))
        for posizione, passo in enumerate(self.steps):
            if not isinstance(passo, (TransformProofStep, AnalyticalProofStep)):
                raise TypeError(
                    f"steps[{posizione}] {type(passo).__name__}: un passo e' "
                    "topologico oppure analitico")
            if passo.index != posizione:
                raise ValueError(
                    f"steps[{posizione}] con indice {passo.index}: gli indici sono "
                    "posizioni consecutive da zero")
        trasformazioni: list[TransformProofStep] = []
        analitici: list[AnalyticalProofStep] = []
        vista_analitica = False
        for passo in self.steps:
            if isinstance(passo, TransformProofStep):
                if vista_analitica:
                    raise ValueError(
                        f"passo topologico {passo.index} dopo un passo analitico: "
                        "lo schema v0.2 ordina prima le trasformazioni, poi l'analitica")
                trasformazioni.append(passo)
            else:
                vista_analitica = True
                analitici.append(passo)
        if len(trasformazioni) != len(self.state_refs) - 1:
            raise ValueError(
                f"{len(trasformazioni)} passi topologici per {len(self.state_refs)} "
                "stati: ogni trasformazione porta allo stato operativo successivo")
        for numero, passo in enumerate(trasformazioni):
            if (passo.before_state_ref != self.state_refs[numero]
                    or passo.after_state_ref != self.state_refs[numero + 1]):
                raise ValueError(
                    f"passo topologico {numero}: "
                    f"{passo.before_state_ref} -> {passo.after_state_ref} contro "
                    f"{self.state_refs[numero]} -> {self.state_refs[numero + 1]}")
        atteso: str | None = self.original_request.target
        for passo in trasformazioni:
            if passo.lineage.request_id != self.original_request.id:
                raise ValueError(
                    f"passo topologico {passo.index}: lineage su "
                    f"{passo.lineage.request_id!r}, la sessione e' su "
                    f"{self.original_request.id!r}")
            if passo.lineage.quantity != self.original_request.quantity:
                raise ValueError(
                    f"passo topologico {passo.index}: lineage su "
                    f"{passo.lineage.quantity!r}, la sessione e' su "
                    f"{self.original_request.quantity!r}")
            if passo.lineage.target_before != atteso:
                raise ValueError(
                    f"passo topologico {passo.index}: parte da "
                    f"{passo.lineage.target_before!r}, atteso {atteso!r}")
            atteso = passo.lineage.target_after
        if not trasformazioni:
            if self.final_request != self.original_request:
                raise ValueError(
                    "sessione senza trasformazioni con final_request diversa "
                    "dall'originale: senza passi la domanda non puo' cambiare")
        elif self.final_request.target != atteso:
            raise ValueError(
                f"final_request su {self.final_request.target!r}, la lineage "
                f"arriva a {atteso!r}")
        if not analitici:
            raise ValueError(
                "sessione senza passi analitici: la derivazione nodale certificata "
                "produce sempre almeno un passo")
        if analitici[0].derivation_before != "D0":
            raise ValueError(
                f"la derivazione parte da {analitici[0].derivation_before!r}, atteso D0")
        for prima, dopo in zip(analitici, analitici[1:]):
            if prima.derivation_after != dopo.derivation_before:
                raise ValueError(
                    f"catena di derivazione spezzata: {prima.derivation_after!r} "
                    f"contro {dopo.derivation_before!r}")
        for passo in analitici:
            if passo.state_ref not in self.state_refs:
                raise ValueError(
                    f"passo analitico {passo.index} su {passo.state_ref}, che non e' "
                    "uno stato operativo della sessione")
            if passo.state_ref != self.final_state_ref:
                raise ValueError(
                    f"passo analitico {passo.index} su {passo.state_ref}: lo schema "
                    "v0.2 ancora ogni passo analitico allo stato operativo finale")
        if analitici[-1].derivation_after != self.final_derivation_id:
            raise ValueError(
                f"derivazione finale {self.final_derivation_id!r} contro ultimo passo "
                f"{analitici[-1].derivation_after!r}")
        if not isinstance(self.final_claim, Claim):
            raise TypeError(
                f"final_claim {type(self.final_claim).__name__} invece di Claim")
        if self.final_claim.verifier_id != VERIFIER_ID:
            raise ValueError(
                f"Claim con verifier_id {self.final_claim.verifier_id!r}: "
                f"l'autorita' e' {VERIFIER_ID!r}")
        if self.final_claim.verifier_version != VERIFIER_VERSION:
            raise ValueError(
                f"Claim con verifier_version {self.final_claim.verifier_version!r}: "
                f"l'autorita' e' {VERIFIER_VERSION!r}")
        if not isinstance(self.final_solution, ResolvedQuantity):
            raise TypeError(
                f"final_solution {type(self.final_solution).__name__} "
                "invece di ResolvedQuantity")
        if self.final_solution.derivation_id != self.final_derivation_id:
            raise ValueError(
                f"soluzione con derivation_id {self.final_solution.derivation_id!r} "
                f"contro derivazione finale {self.final_derivation_id!r}")
        if (self.final_solution.request_id != self.final_request.id
                or self.final_solution.target != self.final_request.target
                or self.final_solution.quantity != self.final_request.quantity):
            raise ValueError(
                f"soluzione su {(self.final_solution.request_id, self.final_solution.target, self.final_solution.quantity)}, "
                f"la final_request e' {(self.final_request.id, self.final_request.target, self.final_request.quantity)}")
        if self.final_solution.derivation_id not in self.final_claim.evidence_ids:
            raise ValueError(
                f"soluzione con derivation_id {self.final_solution.derivation_id!r} "
                f"fuori dalle evidenze del Claim {self.final_claim.evidence_ids}")
        if self.final_claim.state_id != self.final_state_ref:
            raise ValueError(
                f"Claim ancorato a {self.final_claim.state_id!r}, lo stato finale e' "
                f"{self.final_state_ref!r}")
        if self.final_claim.subject_ids != (self.final_request.id, self.final_request.target):
            raise ValueError(
                f"Claim su {self.final_claim.subject_ids}, la domanda finale e' "
                f"{(self.final_request.id, self.final_request.target)}")
        if tuple(passo.derivation_after for passo in analitici) != self.final_claim.evidence_ids:
            raise ValueError(
                f"Claim con evidenze {self.final_claim.evidence_ids}, la derivazione "
                "produce "
                f"{tuple(passo.derivation_after for passo in analitici)}")
        if self.publication_status not in STATI_DI_PUBBLICAZIONE:
            raise ValueError(
                f"publication_status {self.publication_status!r} fuori da "
                f"{', '.join(sorted(STATI_DI_PUBBLICAZIONE))}")


__all__ = [
    "AnalyticalProofStep",
    "PassoDiProva",
    "ProofSession",
    "PublicationStatus",
    "SCHEMA_VERSION",
    "DOCUMENT_PROFILE",
    "STATI_DI_PUBBLICAZIONE",
    "SessionProvenance",
    "SessionVersions",
    "TransformProofStep",
]
