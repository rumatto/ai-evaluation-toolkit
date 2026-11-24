"""Produce human-review work items from existing offline evaluation reports.

This module does not execute agents or approve remediation.
"""
from datetime import datetime, timezone
from comparison_contract import validate_comparison
from hashlib import sha256
import json

def _stable_id(agent, case_id, reason):
    raw=json.dumps([agent,case_id,reason],ensure_ascii=False,separators=(",",":"))
    return sha256(raw.encode("utf-8")).hexdigest()[:20]

def build_review_queue(comparison):
    validate_comparison(comparison)
    agents=comparison.get("agents")
    if not isinstance(agents,list):
        raise ValueError("agents must be a list")
    tasks=[]
    for agent in agents:
        name=agent["name"]
        for case in agent["cases"]:
            expected=case["expected"]["decision"]
            actual=case["actual"]["decision"]
            if expected=="review" or actual=="review" or not case["passed"]:
                reason=("decision-mismatch" if expected!=actual
                        else "human-review-required" if actual=="review"
                        else "evaluation-failed")
                tasks.append({
                    "id":_stable_id(name,case["caseId"],reason),
                    "agent":name,"caseId":case["caseId"],"reason":reason,
                    "expectedDecision":expected,"actualDecision":actual,
                    "status":"pending-human-review",
                    "provenance":"user-supplied-unverified"
                })
    tasks.sort(key=lambda item:(item["agent"],item["caseId"],item["reason"]))
    return {"schemaVersion":"evaluation-review-queue.v1",
            "generatedAt":datetime.now(timezone.utc).isoformat(),
            "requiresHumanApproval":True,"agentExecutedByToolkit":False,
            "items":tasks}
