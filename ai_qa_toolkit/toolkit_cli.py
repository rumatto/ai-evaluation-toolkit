"""Unified CLI for offline toolkit operations. No agent execution or CI."""
import argparse
import json
import sys
from pathlib import Path
from errors import ExitCode, error_payload
from io_core import load_object, write_json_atomic, write_text_atomic
from report import render_comparison_html
from toolkit_config import load_config
from agent_interface import get_adapter
from history_store import HistoryStore
from comparison_pipeline import evaluate
from provenance_bundle import build_bundle, verify_bundle, collect_inputs
from schemas import require_version
from review_queue import build_review_queue
from report_catalog import catalog
from policy_profiles import get_profile, list_profiles
from review_workflow import review_file
from comparison_diff import diff_comparisons
from provenance import read_json_limited

def main(argv=None):
    parser=argparse.ArgumentParser(prog="ai-qa-toolkit")
    sub=parser.add_subparsers(dest="command",required=True)
    compare=sub.add_parser("compare",help="Compare supplied offline agent artifacts")
    compare.add_argument("--suite",required=True)
    compare.add_argument("--manifest",required=True)
    compare.add_argument("--report",required=True)
    compare.add_argument("--html",help="Optional self-contained HTML comparison report")
    compare.add_argument("--policy")
    compare.add_argument("--history")
    bundle=sub.add_parser("provenance",help="Create local input provenance bundle")
    bundle.add_argument("--suite",required=True)
    bundle.add_argument("--manifest",required=True)
    bundle.add_argument("--output",required=True)
    config=sub.add_parser("config",help="Inspect toolkit configuration")
    config.add_argument("--file",required=True)
    adapter=sub.add_parser("import-agent",help="Inspect supplied agent artifact")
    adapter.add_argument("--agent",required=True)
    adapter.add_argument("--file",required=True)
    adapter.add_argument("--type",default="json-file")
    review=sub.add_parser("review-queue",help="Extract human-review tasks from comparison report")
    review.add_argument("--comparison",required=True)
    review.add_argument("--output",required=True)
    reports=sub.add_parser("catalog",help="List local evaluation report metadata")
    reports.add_argument("--directory",required=True)
    profiles=sub.add_parser("policy-profile",help="Show built-in offline policy profile")
    profiles.add_argument("--name",choices=list_profiles(),required=True)
    profiles.add_argument("--output")
    review_action=sub.add_parser("review-decision",help="Record a human decision in a new queue file")
    review_action.add_argument("--queue",required=True)
    review_action.add_argument("--output",required=True)
    review_action.add_argument("--item-id",required=True)
    review_action.add_argument("--decision",required=True,choices=["approved","rejected","needs-information"])
    review_action.add_argument("--reviewer",required=True)
    review_action.add_argument("--note",required=True)
    comparison_diff=sub.add_parser("comparison-diff",help="Compare two offline comparison reports")
    comparison_diff.add_argument("--before",required=True)
    comparison_diff.add_argument("--after",required=True)
    comparison_diff.add_argument("--output",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="review-decision":
            result=review_file(args.queue,args.output,args.item_id,args.decision,args.reviewer,args.note)
            print(json.dumps({"items":len(result["items"]),"output":args.output}))
            return int(ExitCode.SUCCESS)
        if args.command=="comparison-diff":
            result=diff_comparisons(
                load_object(args.before,"agent-comparison-report.v1"),
                load_object(args.after,"agent-comparison-report.v1"))
            write_json_atomic(args.output,result,protected=[args.before,args.after])
            print(json.dumps({"changes":len(result["changes"]),"output":args.output}))
            return int(ExitCode.SUCCESS)
        if args.command=="review-queue":
            result=build_review_queue(load_object(args.comparison,"agent-comparison-report.v1"))
            write_json_atomic(args.output,result,protected=[args.comparison])
            print(json.dumps({"pendingReview":len(result["items"]),"output":args.output}))
            return int(ExitCode.SUCCESS)
        if args.command=="catalog":
            print(json.dumps(catalog(args.directory),ensure_ascii=False,indent=2))
            return int(ExitCode.SUCCESS)
        if args.command=="policy-profile":
            result=get_profile(args.name)
            if args.output:
                write_json_atomic(args.output,result)
            else:
                print(json.dumps(result,indent=2))
            return int(ExitCode.SUCCESS)
        if args.command=="compare":
            if args.html and Path(args.html).resolve() == Path(args.report).resolve():
                raise ValueError("HTML and JSON report paths must be distinct")
            _, suite_path, manifest_path, artifacts = collect_inputs(args.suite, args.manifest)
            protected = [suite_path, manifest_path, *artifacts.values()]
            if args.policy:
                protected.append(Path(args.policy).resolve(strict=True))
            # Validate both outputs before writing either one. Include hardlink
            # aliases of all supplied inputs, not only suite and manifest.
            outputs = [args.report] + ([args.html] if args.html else [])
            for output in outputs:
                target = Path(output)
                if any(target.resolve() == source or
                       (target.exists() and target.samefile(source))
                       for source in protected):
                    raise ValueError("Output overlaps protected input")
            result,code=evaluate(args.suite,args.manifest,policy=args.policy,output=args.report)
            if args.html:
                html = render_comparison_html(result)
                write_text_atomic(args.html, html, protected=[*protected,args.report])
            if args.history:
                HistoryStore(args.history).append(result,label="offline-comparison")
            print(json.dumps({"passed":result["passed"],"agents":len(result["agents"]),
                              "report":args.report},sort_keys=True))
            return int(code)
        if args.command=="provenance":
            payload=build_bundle(args.suite,args.manifest)
            verified=verify_bundle(payload,Path(args.manifest).resolve().parent)
            protected=[args.suite,args.manifest]
            protected.extend(Path(args.manifest).resolve().parent / x["path"] for x in payload["files"])
            write_json_atomic(args.output,payload,protected=protected)
            print(json.dumps(verified,sort_keys=True))
            return int(ExitCode.SUCCESS)
        if args.command=="config":
            data=load_config(args.file)
            print(json.dumps({"schemaVersion":data["config"]["schemaVersion"],
                "workspace":str(data["workspace"]),"historyPath":str(data["historyPath"]),
                "agentAdapters":sorted(data["config"]["agentAdapters"])},indent=2))
            return int(ExitCode.SUCCESS)
        if args.command=="import-agent":
            artifact=get_adapter(args.type).load(args.agent,Path(args.file))
            print(json.dumps({"agentId":artifact.agent_id,"caseCount":len(artifact.payload["artifacts"]),
                              "provenance":artifact.provenance},sort_keys=True))
            return int(ExitCode.SUCCESS)
    except (ValueError,OSError,TypeError,KeyError,OverflowError) as exc:
        print(json.dumps(error_payload(exc),ensure_ascii=False),file=sys.stderr)
        return int(ExitCode.INVALID_INPUT)

if __name__=="__main__":
    sys.exit(main())
