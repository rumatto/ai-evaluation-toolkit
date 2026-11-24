"""Centralized schema IDs and explicit migration policy."""
SCHEMAS = {
    "suite": "evaluation-cases.v1",
    "artifacts": "evaluation-artifacts.v1",
    "report": "evaluation-report.v1",
    "comparison": "agent-comparison.v1",
    "comparison_report": "agent-comparison-report.v1",
    "provenance": "evaluation-provenance.v1",
    "gates": "quality-gates.v1",
    "toolkit_config": "toolkit-config.v1",
    "history_entry": "evaluation-history-entry.v1",
    "input_bundle": "evaluation-input-bundle.v1",
    "metrics": "evaluation-metrics.v1",
    "gate_result": "quality-gate-result.v1",
    "review_queue": "evaluation-review-queue.v1",
    "comparison_diff": "evaluation-comparison-diff.v1",
    "catalog": "evaluation-report-catalog.v1",
}
def require_version(payload, kind):
    if kind not in SCHEMAS:
        raise ValueError("Unknown schema kind")
    if not isinstance(payload, dict) or payload.get("schemaVersion") != SCHEMAS[kind]:
        raise ValueError(f"Unsupported {kind} schema; migration required")
    return payload

def migrate(payload, kind):
    """No implicit migrations: fail closed until a reviewed migration exists."""
    return require_version(payload, kind)
