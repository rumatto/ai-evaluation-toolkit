"""Strict shared contract for offline comparison reports."""
from schemas import require_version

def validate_comparison(report):
    require_version(report, "comparison_report")
    agents=report.get("agents")
    if not isinstance(agents,list) or len(agents)<2:
        raise ValueError("Comparison report requires at least two agents")
    names=set()
    for agent in agents:
        if not isinstance(agent,dict) or not isinstance(agent.get("name"),str) or not agent["name"].strip():
            raise ValueError("Invalid comparison agent")
        if agent["name"] in names:
            raise ValueError("Duplicate comparison agent")
        names.add(agent["name"])
        cases=agent.get("cases")
        if not isinstance(cases,list):
            raise ValueError("Missing agent cases")
        case_ids=set()
        for case in cases:
            if not isinstance(case,dict) or not isinstance(case.get("caseId"),str) or not case["caseId"].strip():
                raise ValueError("Invalid comparison case")
            if case["caseId"] in case_ids:
                raise ValueError("Duplicate comparison case")
            case_ids.add(case["caseId"])
            if type(case.get("passed")) is not bool:
                raise ValueError("Invalid case pass flag")
            for field in ("expected","actual"):
                value=case.get(field)
                if not isinstance(value,dict) or value.get("decision") not in ("allow","deny","review"):
                    raise ValueError(f"Invalid {field} decision")
        metrics=agent.get("evaluationMetrics")
        if not isinstance(metrics,dict) or metrics.get("schemaVersion")!="evaluation-metrics.v1":
            raise ValueError("Missing evaluation metrics")
    return report
