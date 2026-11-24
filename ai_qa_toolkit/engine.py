"""Provider-neutral evaluation of supplied decision artifacts."""


def normalize_decision(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected decision object")
    decision = payload.get("decision")
    if decision not in ("allow", "deny", "review") or not isinstance(decision, str):
        raise ValueError("Invalid decision")
    reason = payload.get("reasonCode")
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError("Invalid reasonCode")
    return {"decision": decision, **({"reasonCode": reason} if reason is not None else {})}


def evaluate(case, artifact):
    actual = normalize_decision(artifact)
    expected = case["expected"]
    passed = actual["decision"] == expected["decision"]
    if "reasonCode" in expected:
        passed = passed and actual.get("reasonCode") == expected["reasonCode"]
    return {"caseId": case["id"], "expected": expected, "actual": actual, "passed": passed}


def evaluate_batch(cases, artifacts):
    results = [evaluate(case, artifacts[case["id"]]) for case in cases]
    return {"total": len(results), "passed": sum(r["passed"] for r in results), "results": results}
