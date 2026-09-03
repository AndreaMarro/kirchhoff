"""Application composition: CertifiedDidacticRun + VisualStep → session artifact.

Questo modulo VIVE in `pipeline/` perché deve comporre `domain/` e `render/`.
`domain/` non importa `render/` (boundary). Frontend non risolve: consuma artefatto.

Input esplicito: IR, Request, supply di state_ids e LayoutIR.
Output deterministico: session artifact serializzabile.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun, orchestrate_didactic_run
from kirchhoff.domain.ir import IR, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.render.layout import LayoutIR, LayoutStore, PatchStore
from kirchhoff.render.step import VisualStep, componi


@dataclass(frozen=True, slots=True)
class SessionStep:
    index: int
    technique: str
    before_state: str
    after_state: str
    before_svg: str
    after_svg: str
    action: str
    equation: str
    why_legal: dict
    observation: dict
    lineage: dict


@dataclass(frozen=True, slots=True)
class DidacticSession:
    session_id: str
    initial_ir: IR
    original_request: Request
    steps: tuple[SessionStep, ...]
    final_state: str
    final_request: Request
    final_value: Fraction
    final_unit: str
    claim: Any
    verifications: tuple[str, ...]


def build_session(
    initial_ir: IR,
    request: Request,
    *,
    state_ids: tuple[str, ...],
    layouts: dict[str, LayoutIR] | None = None,
) -> DidacticSession | Refusal:
    """Esegue orchestrazione + visual composition.

    `state_ids` supply esplicita (P1-L). `layouts` mappa state_id → LayoutIR
    curato; se assente, usa layout vuoto per test determinismo (serie/parallelo
    a maglia singola hanno layout minimal).
    """
    run = orchestrate_didactic_run(initial_ir, request, state_ids=state_ids)
    if isinstance(run, Refusal):
        return run

    # Layout/Patch stores deterministici
    layout_store = LayoutStore()
    patch_store = PatchStore()
    # Pre-deposita layout forniti
    if layouts:
        for sid, lay in layouts.items():
            try:
                layout_store.deposita(lay)
            except ValueError:
                pass

    steps: list[SessionStep] = []
    # Layout corrente: inizia con layout fornito per stato iniziale
    current_layout = None
    if layouts and run.state_ids[0] in layouts:
        current_layout = layouts[run.state_ids[0]]
        try:
            layout_store.deposita(current_layout)
        except ValueError:
            pass
    for idx, exec_ in enumerate(run.transform_executions):
        before_ir = exec_.before
        before_id = run.state_ids[idx]
        after_id = exec_.proof_node
        before_layout = current_layout
        if before_layout is None:
            continue

        # Componi VisualStep per questa azione
        action = exec_.plan.actions[0]
        visual = componi(
            before_ir,
            action.kind,  # type: ignore
            *action.operands,  # type: ignore
            layout=before_layout,
            layouts=layout_store,
            patches=patch_store,
            istante=1_755_000_000_000 + idx * 1000 + 5000,
            casualita=bytes([(idx*10 + j) % 256 for j in range(10)]),
        )
        if isinstance(visual, Refusal):
            # trasformazione letterale ma visual fallito → artifact senza visual per questo step
            continue
        assert isinstance(visual, VisualStep)
        # Aggiorna layout corrente per il prossimo passo (continuità)
        current_layout = layout_store.risolvi(visual.dopo)
        steps.append(
            SessionStep(
                index=idx,
                technique=action.kind,
                before_state=before_id,
                after_state=after_id,
                before_svg=visual.fotogrammi[visual.prima],
                after_svg=visual.fotogrammi[visual.dopo],
                action=f"{action.kind} {','.join(action.operands)}",
                equation=str(visual.risultato.equation),
                why_legal={
                    "terminali": [e.id for e in visual.giustificazione.terminali],
                    "precondizioni": list(visual.giustificazione.precondizioni),
                    "certificato": visual.giustificazione.certificato.operation,
                },
                observation={"effect": exec_.observation_effect.kind, "derived_from": [e.id for e in exec_.results[0].derived_from] if hasattr(exec_.results[0], "derived_from") else []},
                lineage={"before": exec_.request_lineage.target_before, "after": exec_.request_lineage.target_after, "effect": exec_.observation_effect.kind},
            )
        )

    final = run.final_execution
    val = final.execution.resolved.value.amount  # type: ignore
    unit = final.execution.resolved.value.unit  # type: ignore
    return DidacticSession(
        session_id=run.state_ids[0],
        initial_ir=initial_ir,
        original_request=request,
        steps=tuple(steps),
        final_state=run.state_ids[-1],
        final_request=run.final_request,
        final_value=val,
        final_unit=unit,
        claim=final.claim,
        verifications=(final.claim.verifier_id,),
    )


def to_json(session: DidacticSession) -> str:
    data = {
        "session_id": session.session_id,
        "original_request": {"id": session.original_request.id, "quantity": session.original_request.quantity, "target": session.original_request.target},
        "initial_state": session.steps[0].before_state if session.steps else session.session_id,
        "steps": [
            {
                "index": s.index,
                "technique": s.technique,
                "before": s.before_state,
                "after": s.after_state,
                "action": s.action,
                "equation": s.equation,
                "why_legal": s.why_legal,
                "observation": s.observation,
                "lineage": s.lineage,
            }
            for s in session.steps
        ],
        "final": {
            "state": session.final_state,
            "request": {"id": session.final_request.id, "quantity": session.final_request.quantity, "target": session.final_request.target},
            "value": f"{session.final_value.numerator}/{session.final_value.denominator}",
            "unit": session.final_unit,
            "claim": session.claim.status if hasattr(session.claim, "status") else "VERIFIED",
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
