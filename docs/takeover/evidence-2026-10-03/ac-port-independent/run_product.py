"""Only run after root authorizes a ready product. Never regenerates the oracle."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

from oracle import ROOT, check_frozen, sha


def decode_coefficients(answer):
    representation = answer["complex_impedance"]
    assert representation["basis"] == "1,zeta12,zeta12^2,zeta12^3"
    coefficients = representation["coefficients"]
    assert len(coefficients) == 4
    a,b,c,d = (Fraction(value) for value in coefficients)
    return complex(float(a+c/2)+float(b/2)*math.sqrt(3), float(d+b/2)+float(c/2)*math.sqrt(3))


def source_manifest(repo):
    files = sorted((repo/"src").rglob("*.py")) + [repo/"pyproject.toml"]
    entries = [{"path":str(path.relative_to(repo)), "bytes":path.stat().st_size,
                "sha256":sha(path.read_bytes())} for path in files if path.is_file()]
    canonical = json.dumps(entries,sort_keys=True,separators=(",", ":")).encode()
    return {"sha256":sha(canonical), "files":entries}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lessons-output", type=Path)
    parser.add_argument("--method", default="test_current")
    args = parser.parse_args()
    if args.output.exists(): raise SystemExit("Refusing to overwrite an existing receipt")
    lessons_path = args.lessons_output or args.output.with_suffix(".lessons.jsonl")
    if lessons_path.exists(): raise SystemExit("Refusing to overwrite saved lesson responses")
    cases, expected = check_frozen()
    source_before = source_manifest(args.repo.resolve())
    # The production import occurs only after validating the immutable oracle.
    sys.path.insert(0, str(args.repo.resolve()/"src"))
    from kirchhoff.pipeline.lesson import create_lesson
    from kirchhoff.pipeline.lesson import lesson_build
    rows, failures, limitations = [], 0, 0
    for case in cases:
        row = {"id":case["id"], "expected":expected["answers"][case["id"]], "status":"failed"}
        try:
            lesson = create_lesson(case["netlist"], method=args.method)
            lesson_bytes = (json.dumps({"case_id":case["id"], "lesson":lesson},ensure_ascii=False,
                                       sort_keys=True,allow_nan=False)+"\n").encode()
            with lessons_path.open("ab") as stream: stream.write(lesson_bytes)
            row["lesson_json_bytes"] = len(lesson_bytes)
            row["lesson_json_sha256"] = sha(lesson_bytes)
            row["outcome"], row["cause"] = lesson.get("outcome"), lesson.get("cause")
            row["verification"] = lesson.get("verification")
            oracle = row["expected"]
            if lesson.get("outcome") == "solved":
                assert oracle["status"] in ("finite_unique", "finite_with_internal_freedom"), "Finite answer for open/invalid port"
                answer = lesson["answer"]
                assert answer["quantity"] == "equivalent_impedance" and answer["unit"] == "Ω"
                assert lesson["verification"]["product_verified"] is False, "Unexpected VERIFIED promotion"
                value = decode_coefficients(answer)
                wanted = complex(oracle["real"], oracle["imaginary"])
                error = abs(value-wanted)/max(1,abs(wanted))
                assert error <= 2e-9, f"Port value mismatch: {value!r} versus {wanted!r}"
                row.update(status="passed", scaled_error=error, answer=answer)
            else:
                assert lesson.get("outcome") == "refusal", "Unknown product outcome"
                assert "answer" not in lesson, "Refusal carries a numerical answer"
                assert lesson.get("cause"), "Refusal has no cause"
                if case["require_finite_answer"]:
                    row["status"] = "unsupported_finite_case"
                    failures += 1
                else:
                    row["status"] = "documented_refusal"
                    limitations += 1
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
            failures += 1
        rows.append(row)
        print(f'{case["id"]}: {row["status"]}', flush=True)
    source_after = source_manifest(args.repo.resolve())
    if source_before != source_after: failures += 1
    receipt = {"model":"inherited/unknown", "seed":expected["seed"], "case_count":len(cases),
               "cases_sha256":expected["cases_sha256"], "oracle_sha256":expected["oracle_sha256"],
               "expected_sha256":sha((ROOT/"expected.json").read_bytes()),
               "runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "source_manifest_before":source_before, "source_manifest_after":source_after,
               "source_unchanged":source_before == source_after,
               "lessons_jsonl_sha256":sha(lessons_path.read_bytes()) if lessons_path.exists() else None,
               "lesson_build":lesson_build(), "failures":failures, "documented_refusals":limitations,
               "regression_after_first_product_run":True, "results":rows}
    args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({key:value for key,value in receipt.items() if key not in
                     ("results","source_manifest_before","source_manifest_after")},ensure_ascii=False,indent=2))
    return int(failures > 0)


if __name__ == "__main__": raise SystemExit(main())
