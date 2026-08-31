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
    "DerivationState",
    "DerivationSolution",
    "DidacticExecution",
    "DidacticPlan",
    "DidacticTechniqueKind",
    "NodalExecution",
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
    "SimpleSupernode",
    "SolvedVariable",
    "applica_passo",
    "build_linear_system",
    "execute_plan",
    "il_grafo_resta_fermo",
    "nodo_della_prima_kcl",
    "nodi_dei_supernodi_semplici",
    "nodi_kcl_ordinarie",
    "pianifica",
    "resolve_request",
    "scrivi_kcl_al_nodo",
    "scrivi_kcl_del_supernodo",
    "scrivi_vincolo_tensione",
    "solve_derivation",
    "stato_iniziale",
    "supernodi_semplici",
]
