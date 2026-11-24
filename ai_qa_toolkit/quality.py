"""Offline evaluation quality gates and report tooling. No agent execution."""
import csv
import hashlib
import json
import math
from pathlib import Path

METRIC_KEYS = ("decisionAccuracy", "correctDenialRate", "missedDenialRate",
               "humanReviewBypassRate", "reasonCodeMatchRate")
DIRECTIONS = {"decisionAccuracy": "min", "correctDenialRate": "min",
              "missedDenialRate": "max", "humanReviewBypassRate": "max",
              "reasonCodeMatchRate": "min"}

def validate_policy(policy):
    if not isinstance(policy, dict) or policy.get("schemaVersion") != "quality-gates.v1":
        raise ValueError("Unsupported policy schema")
    if set(policy) - {"schemaVersion", "gates", "requireDefined"}:
        raise ValueError("Unknown policy field")
    gates = policy.get("gates")
    if not isinstance(gates, dict) or not gates:
        raise ValueError("Nonempty gates object required")
    if set(gates) - set(METRIC_KEYS):
        raise ValueError("Unknown metric gate")
    for metric, threshold in gates.items():
        if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError(f"Invalid threshold: {metric}")
    if type(policy.get("requireDefined", True)) is not bool:
        raise ValueError("requireDefined must be boolean")
    return policy

def apply_gates(report, policy):
    validate_policy(policy)
    if not isinstance(report, dict):
        raise ValueError("Report must be an object")
    metrics = report.get("evaluationMetrics")
    if not isinstance(metrics, dict):
        raise ValueError("Evaluation metrics must be an object")
    checks = []
    for key, threshold in policy["gates"].items():
        value = metrics.get(key)
        if value is None:
            passed = not policy.get("requireDefined", True)
            status = "undefined"
        elif type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Invalid metric value: {key}")
        else:
            passed = value >= threshold if DIRECTIONS[key] == "min" else value <= threshold
            status = "pass" if passed else "fail"
        checks.append({"metric": key, "direction": DIRECTIONS[key],
                       "threshold": threshold, "actual": value,
                       "status": status, "passed": passed})
    return {"schemaVersion": "quality-gate-result.v1",
            "passed": all(c["passed"] for c in checks), "checks": checks}

def per_category(report, cases):
    categories = {c["id"]: c["category"] for c in cases}
    summary = {}
    for result in report["safety"]["cases"]:
        category = categories[result["caseId"]]
        entry = summary.setdefault(category, {"total": 0, "passed": 0, "failed": 0})
        entry["total"] += 1
        entry["passed" if result["passed"] else "failed"] += 1
    return summary

def failing_cases(report):
    return sorted([r["caseId"] for r in report["safety"]["cases"] if not r["passed"]])

def compare_reports(baseline, candidate):
    if baseline.get("schemaVersion") != "evaluation-report.v1" or candidate.get("schemaVersion") != "evaluation-report.v1":
        raise ValueError("Unsupported report schema")
    old = baseline["safety"]["passRate"]
    new = candidate["safety"]["passRate"]
    if old is None or new is None:
        raise ValueError("Cannot compare empty reports")
    return {"baselinePassRate": old, "candidatePassRate": new,
            "passRateDelta": round(new - old, 4),
            "newFailures": sorted(set(failing_cases(candidate)) - set(failing_cases(baseline))),
            "resolvedFailures": sorted(set(failing_cases(baseline)) - set(failing_cases(candidate)))}

def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def markdown_summary(report, gate_result=None):
    safety = report["safety"]
    lines = ["# AI Evaluation Summary", "",
             f"- Passed: {safety['passed']}/{safety['total']}",
             f"- Failed: {safety['failed']}",
             "- Evidence: evaluation labels only; no live agent execution established."]
    if gate_result is not None:
        lines.append(f"- Quality gates: {'PASS' if gate_result['passed'] else 'FAIL'}")
        for item in gate_result["checks"]:
            lines.append(f"  - {item['metric']}: {item['actual']} ({item['direction']} {item['threshold']}) — {item['status']}")
    return "\n".join(lines) + "\n"

def csv_summary(report):
    import io
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["caseId", "passed", "expectedDecision", "actualDecision"])
    for row in report["safety"]["cases"]:
        writer.writerow([row["caseId"], str(row["passed"]).lower(),
                         row["expected"]["decision"], row["actual"]["decision"]])
    return out.getvalue()
