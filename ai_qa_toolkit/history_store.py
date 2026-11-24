"""Append-only offline history store; no remote calls."""
import datetime
import json
import uuid
from pathlib import Path
from io_core import write_json_atomic, _forbidden_symlink_component
from provenance import sha256

class HistoryStore:
    def __init__(self, directory):
        candidate=Path(directory).absolute()
        if _forbidden_symlink_component(candidate):
            raise ValueError("Symlinked history directory forbidden")
        self.directory=candidate
    def append(self, report, *, label=None):
        if not isinstance(report,dict) or not isinstance(report.get("schemaVersion"),str):
            raise ValueError("Versioned report object required")
        self.directory.mkdir(parents=True,exist_ok=True)
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        record_id=uuid.uuid4().hex
        destination=self.directory/(record_id+".json")
        write_json_atomic(destination,{"schemaVersion":"evaluation-history-entry.v1",
            "id":record_id,"createdAt":timestamp,"label":label,
            "report":report})
        return {"id":record_id,"path":str(destination),"sha256":sha256(destination)}
    def list_entries(self):
        if not self.directory.exists():
            return []
        return sorted(p.name for p in self.directory.glob("*.json") if p.is_file() and not p.is_symlink())
