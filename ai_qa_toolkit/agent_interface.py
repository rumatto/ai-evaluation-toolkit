"""Data contracts for offline AI-agent evaluation adapters."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from io_core import load_object
from schemas import require_version

@dataclass(frozen=True)
class AgentArtifact:
    agent_id: str
    source_path: Path
    payload: dict
    provenance: str = "user-supplied-unverified"

class AgentAdapter(Protocol):
    def load(self, agent_id: str, path: Path) -> AgentArtifact: ...

class JsonFileAdapter:
    """Loads supplied artifacts; never calls or executes an AI agent."""
    def load(self, agent_id: str, path: Path) -> AgentArtifact:
        if not agent_id or not isinstance(agent_id,str):
            raise ValueError("agent_id required")
        source=Path(path).resolve(strict=True)
        payload=require_version(load_object(source),"artifacts")
        if not isinstance(payload.get("artifacts"),list):
            raise ValueError("artifacts must be a list")
        return AgentArtifact(agent_id,source,payload)

class RepositoryEvidenceAdapter:
    """Normalize externally supplied repository evidence; does not authenticate its source."""
    def load(self, agent_id: str, path: Path) -> AgentArtifact:
        import re
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id required")
        source = Path(path).resolve(strict=True)
        if not source.is_file() or source.stat().st_size > 1_000_000:
            raise ValueError("Artifact must be a bounded regular file")
        payload = load_object(source)
        if not isinstance(payload, dict) or payload.get("schemaVersion") != "repository-evidence.v1":
            raise ValueError("Unsupported repository evidence schema")
        repository = payload.get("repository")
        if not isinstance(repository, dict) or not isinstance(repository.get("workspace"), str) or not repository["workspace"] or not isinstance(repository.get("commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", repository["commit"]):
            raise ValueError("Invalid repository identity")
        evidence = payload.get("evidence")
        if not isinstance(evidence, list) or not 0 < len(evidence) <= 100:
            raise ValueError("Invalid evidence count")
        paths = set()
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError("Invalid evidence entry")
            rel, digest = item.get("path"), item.get("sha256")
            if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or ":" in rel or any(ord(ch) < 32 or ord(ch) == 127 for ch in rel) or any(part in ("", ".", "..") for part in rel.split("/")) or rel in paths or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("Unsafe evidence path or digest")
            paths.add(rel)
        records = payload.get("artifacts")
        if not isinstance(records, list) or not 0 < len(records) <= 100:
            raise ValueError("Invalid artifacts")
        ids = set()
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("caseId"), str) or not isinstance(record.get("artifact"), dict):
                raise ValueError("Invalid artifact entry")
            if record["caseId"] in ids:
                raise ValueError("Duplicate caseId")
            ids.add(record["caseId"])
            references = record["artifact"].get("evidencePaths")
            if not isinstance(references, list) or not references or any(not isinstance(ref, str) or ref not in paths for ref in references):
                raise ValueError("Artifact references missing evidence")
        return AgentArtifact(agent_id, source, {"schemaVersion": "evaluation-artifacts.v1", "artifacts": records}, provenance="repository-evidence-unverified")


ADAPTERS={"json-file":JsonFileAdapter,"repository-evidence":RepositoryEvidenceAdapter}
def get_adapter(adapter_type):
    if adapter_type not in ADAPTERS:
        raise ValueError("Unsupported agent adapter type")
    return ADAPTERS[adapter_type]()
