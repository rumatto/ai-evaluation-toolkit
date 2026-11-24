"""Standalone, deterministic Evaluation Report v1 for synthetic or supplied evaluation data."""
import json
from datetime import datetime, timezone
from pathlib import Path
from engine import evaluate_batch
from metrics import calculate_metrics


def build_report(cases, artifacts, outcomes_summary=None):
    batch = evaluate_batch(cases, artifacts)
    failures = [dict(caseId=r['caseId'], expected=r['expected'], actual=r['actual']) for r in batch['results'] if not r['passed']]
    decisions = {'allow': 0, 'deny': 0, 'review': 0}
    for result in batch['results']:
        decisions[result['actual']['decision']] += 1
    total = batch['total']
    return {
        'schemaVersion': 'evaluation-report.v1',
        'safety': {
            'total': total, 'passed': batch['passed'], 'failed': total - batch['passed'],
            'passRate': round(batch['passed'] / total, 4) if total else None,
            'decisions': decisions, 'failures': failures, 'cases': batch['results'],
        },
        'remediationEffectiveness': outcomes_summary,
        'evaluationMetrics': calculate_metrics(batch['results']),
        'limitations': [
            'A passing assertion is not proof of a safe or correct real-world remediation.',
            'Remediation effectiveness is unavailable unless outcomes data is supplied.',
        ] if outcomes_summary is None else [
            'A passing assertion is not proof of a safe or correct real-world remediation.',
            'Outcome counts are historical observations, not proof of remediation correctness.',
        ],
    }


def render_comparison_html(report):
    """Render a self-contained, escaped HTML view of an offline comparison report."""
    import html

    agents = report.get("comparisonSummary", {}).get("agents", [])
    if not isinstance(agents, list) or len(agents) < 2:
        raise ValueError("Comparison summary requires at least two agents")

    def esc(value):
        return html.escape(str(value), quote=True)

    winner = report.get("comparisonSummary", {}).get("winner")
    cards = []
    for agent in agents:
        failures = agent.get("failures", [])
        failure_rows = "".join(
            "<tr><td>" + esc(item.get("caseId", "")) + "</td><td>"
            + esc(item.get("expectedDecision", "")) + "</td><td>"
            + esc(item.get("actualDecision", "")) + "</td><td>"
            + esc(item.get("reason", "")) + "</td></tr>" for item in failures
        ) or '<tr><td colspan="4">No failed cases</td></tr>'
        name = esc(agent.get("name", "Unnamed agent"))
        rate = float(agent.get("passRatePercent", 0))
        cards.append(
            '<section class="agent"><h2>' + name + '</h2><p class="rate">'
            + esc(f"{rate:.2f}") + '%</p><p>' + esc(agent.get("passed", 0))
            + ' passed · ' + esc(agent.get("failed", 0)) + ' failed</p>'
            + '<div class="bar"><span style="width:' + esc(max(0, min(100, rate)))
            + '%"></span></div><h3>Failed cases</h3><table><thead><tr>'
            + '<th>Case</th><th>Expected</th><th>Actual</th><th>Reason</th>'
            + '</tr></thead><tbody>' + failure_rows + '</tbody></table></section>'
        )

    disagreements = report.get("comparisonSummary", {}).get("decisionDisagreements", [])
    disagreement_rows = "".join(
        '<tr><td>' + esc(item.get("caseId", "")) + '</td><td>'
        + esc(json.dumps(item.get("decisions", {}), sort_keys=True))
        + '</td></tr>' for item in disagreements
    ) or '<tr><td colspan="2">No decision disagreements</td></tr>'
    title = esc(report.get("schemaVersion", "Agent comparison"))
    result = "Tie" if report.get("comparisonSummary", {}).get("tied") else (winner or "No unique winner")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Agent comparison</title><style>'
        'body{font:16px system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#182230}'
        '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}'
        '.agent{border:1px solid #ccd4df;border-radius:12px;padding:1rem;min-width:0}'
        '.rate{font-size:2rem;font-weight:700;margin:.2rem 0}.bar{height:9px;background:#e5eaf0;border-radius:9px;overflow:hidden}'
        '.bar span{display:block;height:100%;background:#23845b}table{border-collapse:collapse;width:100%;font-size:.9rem;overflow-wrap:anywhere}'
        'th,td{text-align:left;padding:.5rem;border-bottom:1px solid #e1e6ed}th{background:#f3f6f9}'
        '.notice{border-left:4px solid #b7791f;padding:.8rem;background:#fff8e8;margin:1rem 0}'
        '</style></head><body><h1>Agent comparison</h1><p>Report: ' + title
        + '</p><h2>Result: ' + esc(result) + '</h2><div class="grid">' + "".join(cards)
        + '</div><h2>Decision disagreements</h2><table><thead><tr><th>Case</th><th>Agent decisions</th>'
        + '</tr></thead><tbody>' + disagreement_rows + '</tbody></table>'
        + '<p class="notice">Fixture agreement only. The toolkit did not execute or authenticate agents; '
        'input hashes do not verify source identity.</p></body></html>')


def save_report(report, path, protected=()):
    from io_core import write_json_atomic
    return write_json_atomic(path, report, protected=protected)
