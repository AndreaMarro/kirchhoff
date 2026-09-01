"""Semantica della domanda utente attraverso una Trasformazione certificata.

Il motore delle trasformazioni certifica l'equivalenza elettrica del circuito.
Questo modulo certifica separatamente se quella trasformazione conserva proprio
cio' che l'utente aveva chiesto di osservare. Non pianifica e non modifica il
motore: interpreta un solo risultato gia' certificato.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..ir import IR, Request
from ..transform.delta import EntityRef
from ..transform.result import TransformResult

ObservationEffectKind = Literal["identity", "retarget", "blocked"]
OBSERVATION_EFFECTS: frozenset[str] = frozenset({
    "identity", "retarget", "blocked",
})
OBSERVABLE_QUANTITIES: frozenset[str] = frozenset({"voltage", "current"})


@dataclass(frozen=True, slots=True)
class ObservationContract:
    """La parte immutabile della Request che una trasformazione deve conservare."""

    request_id: str
    target: str
    quantity: str

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("contratto di osservazione senza request_id")
        if not self.target:
            raise ValueError("contratto di osservazione senza target")
        if self.quantity not in OBSERVABLE_QUANTITIES:
            raise ValueError(
                f"contratto di osservazione con quantity {self.quantity!r}: "
                f"ammesse {', '.join(sorted(OBSERVABLE_QUANTITIES))}")

    @classmethod
    def from_request(cls, request: Request) -> ObservationContract:
        if not isinstance(request, Request):
            raise TypeError(
                f"request {type(request).__name__} invece di Request")
        return cls(request.id, request.target, request.quantity)


@dataclass(frozen=True, slots=True)
class ObservationEffect:
    """L'effetto certificato di un passo su una sola osservazione utente."""

    kind: ObservationEffectKind
    target_after: str | None
    reason: str

    def __post_init__(self) -> None:
        if self.kind not in OBSERVATION_EFFECTS:
            raise ValueError(
                f"effetto di osservazione {self.kind!r} fuori dal vocabolario")
        if not self.reason:
            raise ValueError("effetto di osservazione senza motivazione")
        if self.kind == "blocked" and self.target_after is not None:
            raise ValueError("un effetto blocked non ha target_after")
        if self.kind != "blocked" and not self.target_after:
            raise ValueError(
                f"un effetto {self.kind} richiede target_after esplicito")


@dataclass(frozen=True, slots=True)
class RequestLineageStep:
    """Passo ispezionabile che collega una Request prima e dopo un trasformazione."""

    request_id: str
    quantity: str
    target_before: str
    target_after: str | None
    operation: str
    effect: ObservationEffectKind

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("lineage della Request senza request_id")
        if self.quantity not in OBSERVABLE_QUANTITIES:
            raise ValueError(
                f"lineage della Request con quantity {self.quantity!r} non osservabile")
        if not self.target_before:
            raise ValueError("lineage della Request senza target_before")
        if not self.operation:
            raise ValueError("lineage della Request senza operation")
        if self.effect not in OBSERVATION_EFFECTS:
            raise ValueError(
                f"lineage della Request con effect {self.effect!r} sconosciuto")
        if self.effect == "blocked" and self.target_after is not None:
            raise ValueError("lineage blocked con target_after")
        if self.effect != "blocked" and not self.target_after:
            raise ValueError("lineage non blocked senza target_after")


def observation_effect(
    before: IR,
    after: IR,
    result: TransformResult,
    operation: str,
    contract: ObservationContract,
) -> ObservationEffect:
    """Applica l'unica tabella di verita' P1-J a un risultato certificato.

    Per un target consumato la sostituzione e' ammessa soltanto quando il risultato
    dichiara e materializza **un solo** nuovo componente. In ogni altra situazione
    non supportata l'esito e' fail-closed.
    """
    if not isinstance(before, IR) or not isinstance(after, IR):
        raise TypeError("observation_effect richiede IR prima e dopo")
    if not isinstance(result, TransformResult):
        raise TypeError("observation_effect richiede TransformResult")
    if not isinstance(contract, ObservationContract):
        raise TypeError("observation_effect richiede ObservationContract")
    if operation != result.certificate.operation:
        raise ValueError(
            f"operazione {operation!r} diversa dal risultato certificato "
            f"{result.certificate.operation!r}")

    before_ids = {component.id for component in before.components}
    after_ids = {component.id for component in after.components}
    if contract.target not in before_ids:
        return ObservationEffect(
            "blocked", None, "il target osservato non appartiene al circuito prima")
    if contract.target in after_ids:
        return ObservationEffect(
            "identity", contract.target, "il target osservato sopravvive invariato")

    consumed = EntityRef("component", contract.target)
    if (consumed not in result.delta.consumed
            or consumed not in result.layout_patch.remove):
        return ObservationEffect(
            "blocked", None, "il risultato non certifica il consumo del target")

    permitted = (
        (operation == "serie" and contract.quantity == "current")
        or (operation == "parallelo" and contract.quantity == "voltage")
    )
    if not permitted:
        return ObservationEffect(
            "blocked", None,
            f"{operation} non conserva {contract.quantity} sul componente consumato")

    created = tuple(
        entity for entity in result.layout_patch.create
        if entity.kind == "component"
    )
    if len(created) != 1:
        return ObservationEffect(
            "blocked", None,
            "il retarget richiede esattamente un componente creato certificato")
    equivalent = created[0]
    if equivalent not in result.delta.produced or equivalent.id not in after_ids:
        return ObservationEffect(
            "blocked", None,
            "il componente creato non e' materializzato nel circuito dopo")
    return ObservationEffect(
        "retarget", equivalent.id,
        f"{operation} conserva {contract.quantity} sul componente equivalente")


def apply_observation_effect(
    request: Request,
    effect: ObservationEffect,
    *,
    operation: str,
) -> tuple[Request | None, RequestLineageStep]:
    """Deriva la sola Request successiva ammessa dall'effetto certificato."""
    if not isinstance(request, Request):
        raise TypeError(f"request {type(request).__name__} invece di Request")
    if not isinstance(effect, ObservationEffect):
        raise TypeError(f"effect {type(effect).__name__} invece di ObservationEffect")
    if not operation:
        raise ValueError("applicazione dell'effetto senza operation")

    if effect.kind == "identity":
        if effect.target_after != request.target:
            raise ValueError("un effetto identity non puo' cambiare il target")
        successor: Request | None = request
    elif effect.kind == "retarget":
        successor = Request(request.id, request.quantity, effect.target_after)  # type: ignore[arg-type]
    else:
        successor = None

    return successor, RequestLineageStep(
        request.id,
        request.quantity,
        request.target,
        None if successor is None else successor.target,
        operation,
        effect.kind,
    )


def validate_request_lineage(
    before: IR,
    after: IR,
    request: Request,
    effect: ObservationEffect,
    successor: Request | None,
    lineage: RequestLineageStep,
    *,
    operation: str,
) -> None:
    """Rifiuta una lineage che non sia il risultato deterministico dell'effetto."""
    expected_successor, expected_lineage = apply_observation_effect(
        request, effect, operation=operation)
    if successor != expected_successor:
        raise ValueError("successore Request incoerente con l'effetto certificato")
    if lineage != expected_lineage:
        raise ValueError("lineage della Request incoerente con l'effetto certificato")
    if successor is not None:
        after_ids = {component.id for component in after.components}
        if successor.target not in after_ids:
            raise ValueError("successore Request su componente assente dal circuito dopo")
    if request.target not in {component.id for component in before.components}:
        raise ValueError("Request di partenza su componente assente dal circuito prima")
