"""Provenance-aware offline multi-agent comparison.

This pipeline reads user-provided files; it does not execute or authenticate agents.
"""
from pathlib import Path
from compare_agents import compare
from io_core import load_object, write_json_atomic
from provenance_bundle import build_bundle, verify_bundle
from quality import apply_gates
from errors import ExitCode
from comparison_contract import validate_comparison

def evaluate(suite, manifest, *, policy=None, output=None):
    suite = Path(suite).resolve(strict=True)
    manifest = Path(manifest).resolve(strict=True)
    bundle = build_bundle(suite, manifest)
    verified = verify_bundle(bundle, manifest.parent)
    result = validate_comparison(compare(suite, manifest))
    result["inputProvenance"] = {
        "bundle": bundle, "verification": verified,
        "originVerified": False, "agentExecutedByToolkit": False}
    result["execution"] = {"mode": "external-artifacts", "agentExecutedByToolkit": False}
    if policy is not None:
        gate_policy = load_object(policy, "quality-gates.v1")
        gate_results = []
        for agent in result["agents"]:
            gate_results.append({"name": agent["name"], "qualityGates":
                                 apply_gates({"evaluationMetrics": agent["evaluationMetrics"]}, gate_policy)})
        result["agentQualityGates"] = gate_results
    passed = all(agent["failed"] == 0 for agent in result["agents"])
    if policy is not None:
        passed = passed and all(entry["qualityGates"]["passed"] for entry in result["agentQualityGates"])
    result["passed"] = passed

    # Human-readable comparison data derived only from the supplied evaluation artifacts.
    best_score = max((agent["passed"], agent["passRate"] or 0) for agent in result["agents"])
    leaders = [agent["name"] for agent in result["agents"]
               if (agent["passed"], agent["passRate"] or 0) == best_score]
    agent_summaries = []
    for agent in result["agents"]:
        failures = [{
            "caseId": case["caseId"],
            "expectedDecision": case["expected"]["decision"],
            "actualDecision": case["actual"]["decision"],
            "reason": "Decision mismatch" if case["expected"]["decision"] != case["actual"]["decision"]
                      else "Evaluation assertion failed",
        } for case in agent["cases"] if not case["passed"]]
        agent_summaries.append({
            "name": agent["name"], "total": agent["total"],
            "passed": agent["passed"], "failed": agent["failed"],
            "passRatePercent": round((agent["passRate"] or 0) * 100, 2),
            "failures": failures,
        })
    cases_by_agent = {agent["name"]: {case["caseId"]: case["actual"]["decision"]
                                      for case in agent["cases"]}
                      for agent in result["agents"]}
    case_ids = sorted(set.intersection(*(set(items) for items in cases_by_agent.values())))
    disagreements = [{
        "caseId": case_id,
        "decisions": {name: cases_by_agent[name][case_id] for name in sorted(cases_by_agent)},
    } for case_id in case_ids
      if len({items[case_id] for items in cases_by_agent.values()}) > 1]
    result["comparisonSummary"] = {
        "winner": leaders[0] if len(leaders) == 1 else None,
        "leaders": leaders,
        "tied": len(leaders) > 1,
        "agents": agent_summaries,
        "decisionDisagreements": disagreements,
        "interpretation": "Fixture agreement only; agents were not executed by the toolkit.",
    }
    if output is not None:
        protected = [suite, manifest, *[manifest.parent / f["path"] for f in bundle["files"]]]
        if policy is not None:
            protected.append(policy)
        write_json_atomic(output, result, protected=protected)
    return result, ExitCode.SUCCESS if passed else ExitCode.EVALUATION_FAILED
