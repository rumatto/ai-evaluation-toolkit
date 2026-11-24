from comparison_contract import validate_comparison
"""Read-only comparison between two user-supplied evaluation reports."""
def diff_comparisons(before, after):
    validate_comparison(before)
    validate_comparison(after)
    version="agent-comparison-report.v1"
    if not isinstance(before,dict) or not isinstance(after,dict) or before.get("schemaVersion")!=version or after.get("schemaVersion")!=version:
        raise ValueError("Incompatible comparison report schema")
    def index(report):
        agents=report.get("agents")
        if not isinstance(agents,list):
            raise ValueError("Agents must be a list")
        result={}
        for agent in agents:
            if not isinstance(agent,dict) or not isinstance(agent.get("name"),str) or not agent["name"].strip():
                raise ValueError("Invalid agent")
            name=agent["name"]
            if name in result:
                raise ValueError("Duplicate agent name")
            cases=agent.get("cases")
            if not isinstance(cases,list):
                raise ValueError("Agent cases must be a list")
            indexed={}
            for case in cases:
                if not isinstance(case,dict) or not isinstance(case.get("caseId"),str) or not case["caseId"]:
                    raise ValueError("Invalid case")
                cid=case["caseId"]
                if cid in indexed:
                    raise ValueError("Duplicate case ID")
                if type(case.get("passed")) is not bool or not isinstance(case.get("actual"),dict):
                    raise ValueError("Invalid case result")
                indexed[cid]=case
            result[name]=indexed
        return result
    old=index(before); new=index(after)
    changes=[]
    for name in sorted(set(old)&set(new)):
        for case_id in sorted(set(old[name])&set(new[name])):
            prior=old[name][case_id]; current=new[name][case_id]
            if prior["passed"]!=current["passed"] or prior["actual"]!=current["actual"]:
                changes.append({"agent":name,"caseId":case_id,
                    "wasPassed":prior["passed"],"isPassed":current["passed"],
                    "wasActual":prior["actual"],"isActual":current["actual"]})
    return {"schemaVersion":"evaluation-comparison-diff.v1",
            "addedAgents":sorted(set(new)-set(old)),
            "removedAgents":sorted(set(old)-set(new)),
            "changes":changes,"originVerified":False}
