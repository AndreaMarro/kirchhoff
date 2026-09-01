"""Pianificazione didattica e derivazione analitica, distinte dalle Trasformazioni.

Il `ProofGraph` resta ciò che è: stati circuitali e trasformazioni certificate.
Questo pacchetto aggiunge il piano didattico e gli avanzamenti matematici che
non cambiano il circuito. Puro: nessuna I/O, nessun orologio, nessuna casualità.
"""

from .analytical import (
    AnalyticalStep,
    SimpleSupernode,
    applica_passo,
    il_grafo_resta_fermo,
    nodo_della_prima_kcl,
    nodi_dei_supernodi_semplici,
    nodi_kcl_ordinarie,
    scrivi_kcl_al_nodo,
    scrivi_kcl_del_supernodo,
    scrivi_vincolo_tensione,
    stato_iniziale,
    supernodi_semplici,
)
from .derivation import (
    DerivationState,
    ExactEquation,
    LinearTerm,
    NodalVariable,
    VariableRef,
)
from .kinds import (
    AnalyticalStepKind,
    DidacticTechniqueKind,
    PLAN_SCHEMA_VERSION,
    PROFILE,
)
from .execute import (
    DidacticExecution,
    NodalExecution,
    TransformExecution,
    execute_plan,
)
from .observation import (
    ObservationContract,
    ObservationEffect,
    RequestLineageStep,
    apply_observation_effect,
    observation_effect,
    validate_observation_lineage,
)
from .plan import DidacticPlan, PlanReason, PlannedAction
from .planner import pianifica
from .request import ResolvedQuantity, resolve_request
from .solve import (
    DerivationSolution,
    ExactLinearSystem,
    SolvedVariable,
    build_linear_system,
    solve_derivation,
)

__all__ = [
    "AnalyticalStep",
    "AnalyticalStepKind",
    "CertifiedDidacticRun",
    "DerivationState",
    "DerivationSolution",
    "DidacticExecution",
    "DidacticPlan",
    "DidacticTechniqueKind",
    "NodalExecution",
    "ObservationContract",
    "ObservationEffect",
    "TransformExecution",
    "ExactEquation",
    "ExactLinearSystem",
    "LinearTerm",
    "NodalVariable",
    "VariableRef",
    "PLAN_SCHEMA_VERSION",
    "PROFILE",
    "PlanReason",
    "PlannedAction",
    "ResolvedQuantity",
    "RequestLineageStep",
    "SimpleSupernode",
    "SolvedVariable",
    "applica_passo",
    "apply_observation_effect",
    "build_linear_system",
    "execute_plan",
    "il_grafo_resta_fermo",
    "nodo_della_prima_kcl",
    "nodi_dei_supernodi_semplici",
    "nodi_kcl_ordinarie",
    "observation_effect",
    "orchestrate_didactic_run",
    "pianifica",
    "resolve_request",
    "scrivi_kcl_al_nodo",
    "scrivi_kcl_del_supernodo",
    "scrivi_vincolo_tensione",
    "solve_derivation",
    "stato_iniziale",
    "supernodi_semplici",
    "validate_observation_lineage",
]


def __getattr__(name: str):
    """Espone P1-L senza creare il ciclo didactic -> truthfulness -> didactic."""
    if name in {"CertifiedDidacticRun", "orchestrate_didactic_run"}:
        from .orchestrate import CertifiedDidacticRun, orchestrate_didactic_run

        return {
            "CertifiedDidacticRun": CertifiedDidacticRun,
            "orchestrate_didactic_run": orchestrate_didactic_run,
        }[name]
    raise AttributeError(f"module {__name__!r} non esporta {name!r}")
