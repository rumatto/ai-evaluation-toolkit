"""Workspace-relative provenance for multi-directory comparison inputs."""
from pathlib import Path
from io_core import load_object, resolve_input
from provenance import sha256

def collect_inputs(suite_path, manifest_path):
    suite = Path(suite_path).resolve(strict=True)
    manifest_file = Path(manifest_path).resolve(strict=True)
    workspace = manifest_file.parent
    manifest = load_object(manifest_file, "agent-comparison.v1")
    entries = manifest.get("agents")
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValueError("At least two agent entries required")
    if not suite.is_relative_to(workspace):
        raise ValueError("Suite must be inside manifest workspace")
    artifacts = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValueError("Invalid agent entry")
        name = entry["name"]
        if not name.strip() or name in artifacts:
            raise ValueError("Invalid or duplicate agent name")
        artifacts[name] = resolve_input(workspace, entry.get("artifacts"))
    return workspace, suite, manifest_file, artifacts

def build_bundle(suite_path, manifest_path):
    workspace, suite, manifest_file, artifacts = collect_inputs(suite_path, manifest_path)
    paths = {"suite": suite, "comparisonManifest": manifest_file}
    paths.update({f"agent:{name}": path for name, path in artifacts.items()})
    return {"schemaVersion": "evaluation-input-bundle.v1",
            "workspace": ".",
            "files": [{"role": role, "path": str(path.relative_to(workspace)),
                       "sha256": sha256(path)} for role, path in sorted(paths.items())],
            "originVerified": False, "agentExecutedByToolkit": False}

def verify_bundle(bundle, workspace):
    if not isinstance(bundle, dict) or bundle.get("schemaVersion") != "evaluation-input-bundle.v1":
        raise ValueError("Unsupported bundle version")
    files = bundle.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Missing bundle files")
    seen = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("role"), str):
            raise ValueError("Invalid bundle entry")
        role = item["role"]
        if role in seen:
            raise ValueError("Duplicate bundle role")
        seen.add(role)
        path = resolve_input(workspace, item.get("path"))
        if sha256(path) != item.get("sha256"):
            raise ValueError("Bundle checksum mismatch")
    return {"verifiedByteHashes": len(files), "originVerified": False}
