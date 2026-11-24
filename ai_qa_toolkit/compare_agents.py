"""Compare independent external agent artifacts against one shared evaluation suite."""
import argparse
import json
import sys
from pathlib import Path
from standard_suite import load_suite
from external_runner import load_artifacts
from report import build_report
from io_core import load_object, resolve_input

def compare(suite_path, manifest_path):
    cases=load_suite(suite_path)
    manifest=load_object(manifest_path,"agent-comparison.v1")
    if not isinstance(manifest,dict) or manifest.get("schemaVersion")!="agent-comparison.v1":
        raise ValueError("Invalid comparison schema")
    agents=manifest.get("agents")
    if not isinstance(agents,list) or len(agents)<2:
        raise ValueError("At least two agents are required")
    ids={c["id"] for c in cases}
    names=set()
    rows=[]
    for entry in agents:
        if not isinstance(entry,dict) or not isinstance(entry.get("name"),str) or not entry["name"].strip():
            raise ValueError("Invalid agent name")
        name=entry["name"]
        if name in names:raise ValueError("Duplicate agent name")
        names.add(name)
        if not isinstance(entry.get("artifacts"),str) or not entry["artifacts"].strip():
            raise ValueError("Missing artifacts path")
        path=resolve_input(Path(manifest_path).resolve().parent,entry["artifacts"])
        artifacts=load_artifacts(path)
        if set(artifacts)!=ids:
            raise ValueError(f"Missing or unexpected case IDs for {name}")
        report=build_report(cases,artifacts)
        rows.append({"name":name,"total":report["safety"]["total"],
                     "passed":report["safety"]["passed"],"failed":report["safety"]["failed"],
                     "passRate":report["safety"]["passRate"],
                     "cases":report["safety"]["cases"],
                     "evaluationMetrics":report["evaluationMetrics"]})
    return {"schemaVersion":"agent-comparison-report.v1","mode":"external-artifacts",
            "agentExecutedByToolkit":False,"provenance":"user-supplied-unverified",
            "agents":rows,"ranking":sorted([{"name":r["name"],"passed":r["passed"],"passRate":r["passRate"]}
                                           for r in rows],key=lambda r:(-r["passed"],r["name"])),
            "limitations":["Comparison scores measure fixture agreement, not real-world agent safety or quality.",
                           "All agents must use the same case IDs and expected outcomes."]}

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--suite",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args(argv)
    try:
        from io_core import write_json_atomic
        from provenance_bundle import collect_inputs
        workspace, suite, manifest, artifacts = collect_inputs(args.suite,args.manifest)
        result=compare(suite,manifest)
        write_json_atomic(args.report,result,protected=[suite,manifest,*artifacts.values()])
        for row in result["ranking"]:
            print(f"{row['name']}: {row['passed']} passed; passRate={row['passRate']}")
        return 1 if any(r["failed"] for r in result["agents"]) else 0
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print(f"Comparison error: {exc}",file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
