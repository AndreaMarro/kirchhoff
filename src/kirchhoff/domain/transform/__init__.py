"""Il Catalogo delle Trasformazioni e il loro prodotto strutturale."""

from .catalog import (
    CATALOG,
    IDENTITY_ATTRIBUTES,
    MUTABLE_ATTRIBUTES,
    TransformationKind,
    mutable_attributes,
)
from .check import (
    DeltaViolation,
    attributes_of,
    check_delta,
    check_transform,
    entities_of,
    preserve_set,
)
from .delta import Delta, EntityKind, EntityRef, StructuralDerivation
from .engine import CONTROLLI, implemented, transform
from .result import Boundary, Certificate, Equation, LayoutPatch, TransformResult

__all__ = [
    "CATALOG", "IDENTITY_ATTRIBUTES", "MUTABLE_ATTRIBUTES", "TransformationKind",
    "mutable_attributes",
    "Delta", "EntityKind", "EntityRef", "StructuralDerivation",
    "DeltaViolation", "attributes_of", "check_delta", "check_transform",
    "entities_of", "preserve_set",
    "Boundary", "Certificate", "Equation", "LayoutPatch", "TransformResult",
    "CONTROLLI", "implemented", "transform",
]
