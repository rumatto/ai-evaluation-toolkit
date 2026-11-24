"""Evaluation Runner v1: deterministic, fixture-based CI execution."""
import argparse
import json
import sys
from pathlib import Path
from standard_suite import load_suite, run_suite_report
from report import save_report

def main(argv=None):
    parser = argparse.ArgumentParser(description="Run configured synthetic evaluation cases")
    parser.add_argument("--config", required=True, help="Path to evaluation-runner.v1 JSON")
    args = parser.parse_args(argv)
    try:
        config_path = Path(args.config).resolve()
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or config.get("schemaVersion") != "evaluation-runner.v1":
            raise ValueError("Invalid runner config schemaVersion")
        if not isinstance(config.get("suite"), str) or not config["suite"].strip():
            raise ValueError("Missing suite")
        if not isinstance(config.get("report"), str) or not config["report"].strip():
            raise ValueError("Missing report")
        if type(config.get("failOnFailedCases", True)) is not bool:
            raise ValueError("failOnFailedCases must be boolean")
        suite_path = (config_path.parent / config["suite"]).resolve()
        report_path = (config_path.parent / config["report"]).absolute()
        if suite_path == report_path or report_path == config_path:
            raise ValueError("Report path must not overwrite input")
        load_suite(suite_path)
        report = run_suite_report(suite_path)
        report["execution"] = {"mode": "synthetic-fixtures", "suite": str(suite_path),
                               "realAgentExecuted": False}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        save_report(report, report_path, protected=[suite_path, config_path])
        summary = report["safety"]
        print(f"Evaluation: {summary['passed']}/{summary['total']} passed; report: {report_path}")
        if summary["failed"] and config.get("failOnFailedCases", True):
            return 1
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Evaluation configuration/error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
