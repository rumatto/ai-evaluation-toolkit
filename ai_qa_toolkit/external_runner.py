"""Evaluate externally supplied artifacts; never executes an agent."""
import argparse
import json
import sys
from pathlib import Path
from standard_suite import load_suite
from report import build_report, save_report
from io_core import load_object, write_json_atomic

def load_artifacts(path):
    obj=load_object(path,"evaluation-artifacts.v1")
    if not isinstance(obj,dict) or obj.get("schemaVersion")!="evaluation-artifacts.v1":
        raise ValueError("Unsupported artifact schema")
    records=obj.get("artifacts")
    if not isinstance(records,list):
        raise ValueError("artifacts must be a list")
    result={}
    for item in records:
        if not isinstance(item,dict) or not isinstance(item.get("caseId"),str) or not isinstance(item.get("artifact"),dict):
            raise ValueError("Invalid artifact entry")
        if item["caseId"] in result:raise ValueError("Duplicate caseId")
        result[item["caseId"]]=item["artifact"]
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description="Evaluate independently supplied agent artifacts")
    parser.add_argument("--suite",required=True)
    parser.add_argument("--artifacts",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args(argv)
    try:
        suite_path=Path(args.suite).resolve()
        artifact_path=Path(args.artifacts).resolve()
        report_path=Path(args.report).resolve()
        if report_path in (suite_path,artifact_path):raise ValueError("Report cannot overwrite input")
        cases=load_suite(suite_path)
        artifacts=load_artifacts(artifact_path)
        expected_ids={c["id"] for c in cases}
        if set(artifacts)!=expected_ids:
            raise ValueError("Artifact IDs must match suite IDs exactly; missing or unexpected IDs found")
        report=build_report(cases,artifacts)
        report["execution"]={"mode":"external-artifacts","agentExecutedByToolkit":False,
                             "artifactProvenance":"user-supplied-unverified"}
        write_json_atomic(report_path,report,protected=[suite_path,artifact_path])
        print(f"External evaluation: {report['safety']['passed']}/{report['safety']['total']} passed")
        return 1 if report["safety"]["failed"] else 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(f"External evaluation error: {exc}",file=sys.stderr)
        return 2

if __name__=="__main__":sys.exit(main())
