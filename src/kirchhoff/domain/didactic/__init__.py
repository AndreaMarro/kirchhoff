"""Pianificazione didattica e derivazione analitica, distinte dalle Trasformazioni.

Il `ProofGraph` resta ciò che è: stati circuitali e trasformazioni certificate.
Questo pacchetto aggiunge il piano didattico e gli avanzamenti matematici che
non cambiano il circuito. Puro: nessuna I/O, nessun orologio, nessuna casualità.
"""

from .analytical import (
    AnalyticalStep,
    applica_passo,
    il_grafo_resta_fermo,
    nodo_della_prima_kcl,
    stato_iniziale,
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
from .plan import DidacticPlan, PlanReason, PlannedAction
from .planner import pianifica

__all__ = [
    "AnalyticalStep",
    "AnalyticalStepKind",
    "DerivationState",
    "DidacticPlan",
    "DidacticTechniqueKind",
    "ExactEquation",
    "LinearTerm",
    "NodalVariable",
    "VariableRef",
    "PLAN_SCHEMA_VERSION",
    "PROFILE",
    "PlanReason",
    "PlannedAction",
    "applica_passo",
    "il_grafo_resta_fermo",
    "nodo_della_prima_kcl",
    "pianifica",
    "stato_iniziale",
]
