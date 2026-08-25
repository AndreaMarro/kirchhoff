"""Il Catalogo delle Trasformazioni e il loro prodotto strutturale."""

from .catalog import (
    CATALOG,
    IDENTITY_ATTRIBUTES,
    MUTABLE_ATTRIBUTES,
    SUPPORTED,
    CatalogOpening,
    TransformationKind,
    mutable_attributes,
    transformations_supported,
)
from .check import (
    BoundaryViolation,
    CertificateViolation,
    PatchViolation,
    check_boundary,
    check_certificate,
    check_patch,
    DeltaViolation,
    attributes_of,
    check_delta,
    check_transform,
    entities_of,
    identity_attestations,
    preserve_set,
)
from .delta import Delta, EntityKind, EntityRef, StructuralDerivation
from .engine import CONTROLLI, implemented, transform
from .result import (
    Boundary,
    Certificate,
    Equation,
    IdentityAttestation,
    LayoutPatch,
    TransformResult,
)

__all__ = [
    "CATALOG", "IDENTITY_ATTRIBUTES", "MUTABLE_ATTRIBUTES", "SUPPORTED",
    "CatalogOpening", "TransformationKind",
    "mutable_attributes", "transformations_supported",
    "Delta", "EntityKind", "EntityRef", "StructuralDerivation",
    "DeltaViolation", "attributes_of", "check_delta", "check_transform",
    "entities_of", "identity_attestations", "preserve_set",
    "Boundary", "Certificate", "Equation", "IdentityAttestation",
    "LayoutPatch", "TransformResult",
    "PatchViolation", "check_patch",
    "BoundaryViolation", "check_boundary",
    "CertificateViolation", "check_certificate",
    "CONTROLLI", "implemented", "transform",
]
