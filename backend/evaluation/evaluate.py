"""Offline, repeatable evaluation of deterministic rules and recorded LLM results.

Run: python evaluation/evaluate.py
Optionally pass a JSON map of case id to LLM findings with --llm-results results.json.
The runner never calls Gemini.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.github import PRFile
from app.services.diff_parser import parse_pr_files
from app.services.rule_analyzer import rule_analyzer


def matched(findings, expected):
    return any(f.category.value == expected["category"] and f.severity.value == expected["severity"] for f in findings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-results", help="Recorded JSON: {case_id: [{category, severity}, ...]}")
    args = parser.parse_args()
    cases = json.loads((Path(__file__).parent / "dataset.json").read_text())
    llm_results = json.loads(Path(args.llm_results).read_text()) if args.llm_results else {}
    rows, static_fp, static_fn, llm_fp, llm_fn = [], 0, 0, 0, 0
    for case in cases:
        file = PRFile(filename=case["filename"], status="modified", additions=1, deletions=0, changes=1, patch=case["patch"])
        static = rule_analyzer.analyze(parse_pr_files([file]))
        llm = llm_results.get(case["id"], [])
        expected = case["expected"]
        static_unexpected = bool(not expected and static)
        llm_evaluated = case["id"] in llm_results
        llm_unexpected = bool(not expected and llm) if llm_evaluated else None
        hit = None
        if expected and expected["source"] == "static":
            hit = matched(static, expected)
            static_fn += not hit
        elif expected and llm_evaluated:
            hit = matched(llm, expected)
            llm_fn += not hit
        static_fp += static_unexpected
        llm_fp += bool(llm_unexpected)
        rows.append({"id": case["id"], "expected": expected, "static": [f.model_dump(mode="json") for f in static], "llm": llm, "hit": hit, "static_false_positive": static_unexpected, "llm_false_positive": llm_unexpected})
    report = {"case_count": len(cases), "static": {"false_negatives": static_fn, "false_positives": static_fp}, "llm": {"evaluated": bool(args.llm_results), "false_negatives": llm_fn, "false_positives": llm_fp}, "results": rows,
              "note": "This small curated set checks regression signals; it does not prove correctness or model quality."}
    output = Path(__file__).parent / "report.json"
    output.write_text(json.dumps(report, indent=2))
    print(f"Wrote {output}; static false negatives={static_fn}, static false positives={static_fp}")


if __name__ == "__main__":
    main()
