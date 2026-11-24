"""Run a fixture suite with quality gates, category summaries, and optional exports."""
import argparse
import json
import sys
from pathlib import Path
from quality import apply_gates, per_category, markdown_summary, csv_summary, fingerprint
from standard_suite import load_suite, run_suite_report
from report import save_report
from io_core import write_text_atomic

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--csv")
    args=ap.parse_args(argv)
    try:
        suite=Path(args.suite).resolve()
        policy_path=Path(args.policy).resolve()
        report_path=Path(args.report).absolute()
        outputs=[report_path]+[Path(x).absolute() for x in (args.markdown,args.csv) if x]
        if len(set(outputs)) != len(outputs) or set(outputs)&{suite,policy_path}:
            raise ValueError("Output paths must be distinct and must not overwrite inputs")
        cases=load_suite(suite)
        policy=json.loads(policy_path.read_text(encoding="utf-8"))
        report=run_suite_report(suite)
        gates=apply_gates(report,policy)
        report["qualityGates"]=gates
        report["categories"]=per_category(report,cases)
        report["execution"]={"mode":"synthetic-fixtures","realAgentExecuted":False,
                             "suiteSha256":fingerprint(suite),"policySha256":fingerprint(policy_path)}
        for path in outputs:
            path.parent.mkdir(parents=True,exist_ok=True)
        protected=[suite, policy_path]
        save_report(report, report_path, protected=protected)
        if args.markdown:
            write_text_atomic(args.markdown, markdown_summary(report,gates), protected=protected)
        if args.csv:
            write_text_atomic(args.csv, csv_summary(report), protected=protected)
        print(f"Evaluation {report['safety']['passed']}/{report['safety']['total']}; gates {'PASS' if gates['passed'] else 'FAIL'}")
        return 0 if gates["passed"] and report["safety"]["failed"]==0 else 1
    except (ValueError,OSError,KeyError,TypeError,IndexError) as exc:
        print(f"Quality runner error: {exc}",file=sys.stderr)
        return 2

if __name__=="__main__":sys.exit(main())
