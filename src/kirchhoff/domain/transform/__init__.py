"""Il Catalogo delle Trasformazioni, le riscritture di cui sono fatte, il prodotto.

Due vocabolari chiusi e distinti, e la distinzione e' il contenuto della Story 1.2:
`CATALOG` nomina i **passi pedagogici**, `PRIMITIVES` le **riscritture strutturali**
di cui un passo e' composto. `COMPOSITION` e' la dichiarazione che li lega.
"""

from .catalog import (
    CATALOG,
    COMPOSITION,
    DORMANT,
    IDENTITY_ATTRIBUTES,
    MUTABLE_ATTRIBUTES,
    SUPPORTED,
    CatalogOpening,
    TransformationKind,
    mutable_attributes,
    primitives_of,
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
from .primitives import FORME, PRIMITIVES, Forma, StructuralPrimitive
from .result import (
    Boundary,
    Certificate,
    Equation,
    IdentityAttestation,
    LayoutPatch,
    TransformResult,
)

__all__ = [
    "CATALOG", "COMPOSITION", "DORMANT", "IDENTITY_ATTRIBUTES",
    "MUTABLE_ATTRIBUTES", "SUPPORTED", "CatalogOpening", "TransformationKind",
    "mutable_attributes", "primitives_of", "transformations_supported",
    "FORME", "PRIMITIVES", "Forma", "StructuralPrimitive",
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
