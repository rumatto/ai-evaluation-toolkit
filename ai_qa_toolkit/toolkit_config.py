"""Unified offline toolkit configuration (schema v1)."""
from pathlib import Path
from io_core import load_object, resolve_input
DEFAULTS = {"schemaVersion":"toolkit-config.v1","workspace":".","historyDirectory":".evaluation-history","agentAdapters":{}}
def load_config(path):
    config = {**DEFAULTS, **load_object(path,"toolkit-config.v1")}
    base=Path(path).resolve().parent
    workspace=resolve_workspace(base,config["workspace"])
    adapters=config["agentAdapters"]
    if not isinstance(adapters,dict):
        raise ValueError("agentAdapters must be an object")
    for name,entry in adapters.items():
        if not isinstance(name,str) or not name.strip() or not isinstance(entry,dict):
            raise ValueError("Invalid adapter configuration")
        if entry.get("type") not in ("json-file",):
            raise ValueError("Only the offline json-file adapter is supported")
    history=config["historyDirectory"]
    if not isinstance(history,str) or not history or Path(history).is_absolute():
        raise ValueError("historyDirectory must be relative")
    history_path=(workspace/history).resolve()
    if not history_path.is_relative_to(workspace):
        raise ValueError("History path escapes workspace")
    return {"config":config,"workspace":workspace,"historyPath":history_path}
def resolve_workspace(base,value):
    if not isinstance(value,str) or not value:
        raise ValueError("Workspace required")
    workspace=(base/value).resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("Workspace must be a directory")
    return workspace
