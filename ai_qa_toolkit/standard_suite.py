"""Synthetic contract fixtures; NOT an agent benchmark."""
import json
from pathlib import Path
from engine import evaluate_batch
from report import build_report

def load_suite(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("schemaVersion")!="evaluation-cases.v1":
        raise ValueError("Unsupported suite version")
    cases=data.get("cases")
    if not isinstance(cases,list) or not cases:
        raise ValueError("Suite must contain cases")
    ids=set()
    for case in cases:
        if not isinstance(case,dict) or not isinstance(case.get("id"),str) or not case["id"] or case["id"] in ids:
            raise ValueError("Invalid or duplicate case ID")
        ids.add(case["id"])
        if case.get("category") not in ("agent-safety","remediation","decision-quality"):
            raise ValueError("Unsupported category")
        if not isinstance(case.get("expected"),dict) or case["expected"].get("decision") not in ("allow","deny","review"):
            raise ValueError("Invalid expected decision")
        if not isinstance(case.get("fixture"),dict):
            raise ValueError("Missing fixture")
    return cases

def run_suite(path):
    cases=load_suite(path)
    result=evaluate_batch(cases,{c["id"]:c["fixture"] for c in cases})
    return result

def run_suite_report(path):
    cases=load_suite(path)
    return build_report([{'id':c['id'],'expected':c['expected']} for c in cases],{c['id']:c['fixture'] for c in cases})
