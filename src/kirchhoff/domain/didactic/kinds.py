"""Vocabolario chiuso e versionato delle tecniche didattiche eseguibili ora.

Distinto da `TransformationKind`: l'analisi nodale non è una trasformazione
circuitale e non entra nel catalogo delle Trasformazioni. Chiuso per questa
versione di schema: aggiungere una tecnica richiede una nuova versione e un
percorso eseguibile, non un'etichetta anticipata.
"""

from __future__ import annotations

from typing import Literal, get_args

DidacticTechniqueKind = Literal[
    "certified_transform_path",
    "nodal_analysis",
]

AnalyticalStepKind = Literal[
    "choose_reference",
    "define_nodal_unknowns",
    "write_kcl",
    "write_voltage_constraint",
]

TECHNIQUES: frozenset[str] = frozenset(get_args(DidacticTechniqueKind))
ANALYTICAL_KINDS: frozenset[str] = frozenset(get_args(AnalyticalStepKind))

PLAN_SCHEMA_VERSION = "didactic-plan.v0.2"
PROFILE = "student-dc-v0.1"
