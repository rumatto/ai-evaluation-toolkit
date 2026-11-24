"""Offline report catalog: metadata only, no execution."""
from pathlib import Path
from io_core import load_object
from provenance import sha256

SUPPORTED={"evaluation-report.v1","agent-comparison-report.v1"}
def catalog(directory, *, limit=1000):
    root=Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Catalog root must be a directory")
    if type(limit) is not int or limit<1 or limit>10000:
        raise ValueError("limit must be between 1 and 10000")
    entries=[]
    for path in sorted(root.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            report=load_object(path)
        except (ValueError,OSError):
            continue
        if report.get("schemaVersion") not in SUPPORTED:
            continue
        if report["schemaVersion"] == "agent-comparison-report.v1":
            from comparison_contract import validate_comparison
            try:
                validate_comparison(report)
            except (ValueError, KeyError, TypeError):
                continue
        elif not isinstance(report.get("safety"), dict):
            continue
        entries.append({"file":path.name,"schemaVersion":report["schemaVersion"],
                        "sha256":sha256(path),
                        "agentCount":len(report.get("agents",[])) if isinstance(report.get("agents",[]),list) else None})
        if len(entries)>=limit:
            break
    return {"schemaVersion":"evaluation-report-catalog.v1",
            "entries":entries,"limit":limit}
