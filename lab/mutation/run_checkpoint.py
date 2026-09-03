"""Esegue e classifica le sessioni Cosmic Ray P1-M0, lasciando i DB come artefatti."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ("observation", "orchestrate", "truthfulness", "verify")
OUTCOMES = ("killed", "survived", "incompetent", "timeout", "skipped")

# Questi mutanti restano nel report come sopravvissuti, ma sono equivalenti nel
# vocabolario chiuso gia' validato P1-J: `blocked < identity < retarget`, due
# quantita' (`current`, `voltage`) e le sole operazioni certificate (`serie`,
# `parallelo`). La tupla include l'occorrenza Cosmic Ray per non classificare
# genericamente come equivalenti confronti con altra semantica.
_CLOSED_VOCABULARY_EQUIVALENTS = frozenset({
    (
        "core/ReplaceComparisonOperator_Eq_LtE", 1,
        'if self.effect == "blocked" and self.target_after is not None:',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_LtE", 3,
        '(operation == "serie" and contract.quantity == "current")',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_LtE", 4,
        'or (operation == "parallelo" and contract.quantity == "voltage")',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_GtE", 2,
        '(operation == "serie" and contract.quantity == "current")',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_GtE", 5,
        'or (operation == "parallelo" and contract.quantity == "voltage")',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_GtE", 8,
        'elif effect.kind == "retarget":',
    ),
    (
        "core/ReplaceComparisonOperator_NotEq_Gt", 1,
        'if self.effect != "blocked" and not self.target_after:',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_LtE", 6,
        'if expected_effect.kind == "blocked":',
    ),
    (
        "core/ReplaceComparisonOperator_Eq_LtE", 7,
        'if execution.observation_effect.kind == "identity" and successor != current_request:',
    ),
    (
        "core/NumberReplacer", 9,
        'if matches[0] != request:',
    ),
})

# Equivalenze dimostrate sul confine pubblico di P1-K, non declassamenti di
# severita'. Chiavi deliberatamente puntuali: operatore, occorrenza Cosmic Ray
# e sorgente devono coincidere tutti prima che il gate le accetti.
_TRUTHFULNESS_FORMAL_EQUIVALENTS = {
    (
        "core/ReplaceComparisonOperator_NotEq_Lt", 1,
        'if self.claim.claim_type != "resolved_quantity":',
    ): (
        "Claim.__post_init__ rifiuta runtime ogni claim_type fuori dal "
        "vocabolario chiuso {resolved_quantity}; il confronto resta falso "
        "per ogni Claim costruibile legalmente"
    ),
    (
        "core/ReplaceComparisonOperator_NotEq_Lt", 12,
        "if resolved.request_id != request.id:",
    ): (
        "NodalExecution.__post_init__ impone resolved.request_id == "
        "plan.request_id e _context verifica prima plan.request_id == request.id; "
        "il ramo e' irraggiungibile per un NodalExecution costruibile legalmente"
    ),
    (
        "core/ReplaceComparisonOperator_NotEq_Gt", 7,
        'if self.claim.status != "VERIFIED":',
    ): (
        "Claim.status e' init=False con default invariantemente VERIFIED; "
        "costruttore e dataclasses.replace non accettano un override pubblico"
    ),
    (
        "core/ReplaceComparisonOperator_NotEq_Lt", 7,
        'if self.claim.status != "VERIFIED":',
    ): (
        "Claim.status e' init=False con default invariantemente VERIFIED; "
        "costruttore e dataclasses.replace non accettano un override pubblico"
    ),
    (
        "core/ReplaceComparisonOperator_NotEq_IsNot", 7,
        'if self.claim.status != "VERIFIED":',
    ): (
        "Claim.status e' init=False con default literal VERIFIED, identico al "
        "literal del confronto; costruttore e dataclasses.replace non accettano "
        "un override pubblico"
    ),
    (
        "core/NumberReplacer", 3,
        "if matches[0] != request:",
    ): (
        "il ramo e' raggiunto solo dopo len(matches) == 1; per una tupla "
        "unitaria matches[0] e matches[-1] sono lo stesso Request"
    ),
}


def _command(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def _result_type(record: list[object]) -> str:
    result = record[1] if len(record) == 2 else None
    if not isinstance(result, dict):
        return "skipped"
    outcome = result.get("test_outcome")
    if outcome == "killed":
        return "killed"
    if outcome == "survived":
        return "survived"
    if outcome == "incompetent":
        return "incompetent"
    if outcome == "timeout":
        return "timeout"
    return "skipped"


def _source_line(module: str, line_number: int) -> str:
    path = ROOT / module
    try:
        return path.read_text(encoding="utf-8").splitlines()[line_number - 1].strip()
    except (FileNotFoundError, IndexError):
        return ""


def _classification(record: list[object]) -> dict[str, Any]:
    """Classifica ogni esito; HIGH resta conservativo sulle semantiche P1-M0."""
    item = record[0] if record else {}
    mutation = item.get("mutations", [{}])[0] if isinstance(item, dict) else {}
    module = str(mutation.get("module_path", ""))
    start = mutation.get("start_pos", [0, 0])
    line_number = int(start[0]) if isinstance(start, list) and start else 0
    source = _source_line(module, line_number)
    outcome = _result_type(record)
    operator = str(mutation.get("operator_name", ""))
    occurrence = int(mutation.get("occurrence", -1))
    if outcome in {"killed", "skipped"}:
        importance, reason = "not-applicable", f"{outcome}: nessun sopravvissuto da valutare"
    elif (operator, occurrence, source) in _CLOSED_VOCABULARY_EQUIVALENTS:
        importance, reason = (
            "equivalent",
            "equivalente nel vocabolario P1-J chiuso e validato; mutante mantenuto nel report",
        )
    elif formal_reason := _TRUTHFULNESS_FORMAL_EQUIVALENTS.get(
        (operator, occurrence, source),
    ):
        importance, reason = "equivalent", formal_reason
    elif "->" in source or ": " in source and " | " in source:
        importance, reason = "equivalent", "annotazione di tipo senza semantica runtime nel perimetro P1-M0"
    elif source in {"*,", "/,"}:
        importance, reason = "low", "mutazione della firma, non di una decisione di dominio"
    elif any(token in source.lower() for token in (
        "observationeffect", "request", "lineage", "refusal", "claim", "certificate",
        "solution", "residual", "exact", "effect", "operation", "verify", "truth",
    )):
        importance, reason = "HIGH", "puo' cambiare una semantica certificata P1-M0"
    else:
        importance, reason = "medium", "mutazione runtime non inclusa nelle categorie HIGH definite"
    return {
        "module": module,
        "line": line_number,
        "operator": operator,
        "outcome": outcome,
        "semantic_importance": importance,
        "reason": reason,
        "source": source,
    }


def _session_summary(
    session: Path, report: Path, classifications: Path,
) -> dict[str, object]:
    dumped = subprocess.run(
        ("cosmic-ray", "dump", str(session)), cwd=ROOT, check=True,
        text=True, capture_output=True,
    )
    records = [json.loads(line) for line in dumped.stdout.splitlines() if line]
    counts = Counter({outcome: 0 for outcome in OUTCOMES})
    counts.update(_result_type(record) for record in records)
    classified = [_classification(record) for record in records]
    classifications.write_text(
        json.dumps(classified, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_result = subprocess.run(
        ("cr-report", "--all-mutations", str(session)), cwd=ROOT, check=True,
        text=True, capture_output=True,
    )
    report.write_text(report_result.stdout, encoding="utf-8")
    return {
        "session": session.name,
        "generated": len(records),
        "high_semantic_survivors": sum(
            item["outcome"] == "survived" and item["semantic_importance"] == "HIGH"
            for item in classified
        ),
        "unexplained_high_location_incompetent": sum(
            item["outcome"] == "incompetent" and item["semantic_importance"] == "HIGH"
            for item in classified
        ),
        **dict(sorted(counts.items())),
    }


def run(output: Path, configs: tuple[str, ...] = CONFIGS) -> dict[str, object]:
    """Crea, baselina ed esegue sessioni isolate; non conserva DB nel repository."""
    output.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    for name in configs:
        config = ROOT / "lab" / "mutation" / "configs" / f"{name}.toml"
        session = output / f"{name}.sqlite"
        _command("cosmic-ray", "init", str(config), str(session))
        _command("cr-filter-operators", str(session), str(config))
        _command(
            "cosmic-ray", "baseline", "--session-file",
            str(output / f"{name}.baseline.sqlite"), str(config),
        )
        _command("cosmic-ray", "exec", str(config), str(session))
        summaries.append(_session_summary(
            session, output / f"{name}.txt", output / f"{name}-classification.json"))
    total = Counter({outcome: 0 for outcome in (
        "generated", *OUTCOMES, "high_semantic_survivors",
        "unexplained_high_location_incompetent",
    )})
    for summary in summaries:
        total.update({key: value for key, value in summary.items()
                      if key in {
                          "generated", "killed", "survived", "incompetent", "timeout", "skipped",
                          "high_semantic_survivors", "unexplained_high_location_incompetent",
                      }})
    result: dict[str, object] = {"sessions": summaries, "total": dict(sorted(total.items()))}
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", action="append", choices=CONFIGS)
    args = parser.parse_args()
    result = run(args.output, tuple(args.config or CONFIGS))
    total = result["total"]
    if isinstance(total, dict) and (
        total.get("high_semantic_survivors", 0)
        or total.get("unexplained_high_location_incompetent", 0)
    ):
        raise SystemExit(
            "mutation gate: HIGH semantic survivors or unexplained HIGH-location "
            "incompetent mutants are present; inspect the classification artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
