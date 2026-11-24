"""Shared, bounded JSON I/O and atomic report writes."""
import json
import os
import tempfile
import sys
from pathlib import Path
from provenance import read_json_limited, sha256

def load_object(path, schema=None):
    data = read_json_limited(path)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    if schema is not None and data.get("schemaVersion") != schema:
        raise ValueError(f"Expected schemaVersion {schema}")
    return data

def resolve_input(base_dir, value, *, allow_external=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Input path required")
    base = Path(base_dir).resolve(strict=True)
    candidate = Path(value)
    if not allow_external and ".." in candidate.parts:
        raise ValueError("Parent traversal is disabled")
    if candidate.is_absolute() and not allow_external:
        raise ValueError("Absolute input paths are disabled")
    resolved = (base / candidate).resolve(strict=True)
    if not allow_external and not resolved.is_relative_to(base):
        raise ValueError("Input path escapes workspace")
    if not resolved.is_file():
        raise ValueError("Input is not a regular file")
    return resolved

def _forbidden_symlink_component(path):
    """Reject symlinks except macOS's fixed /var and /tmp system aliases."""
    for component in (Path(path), *Path(path).parents):
        if not component.is_symlink():
            continue
        if (sys.platform == "darwin" and str(component) in ("/var", "/tmp")
                and component.resolve() == Path("/private") / component.name):
            continue
        return True
    return False

def write_text_atomic(path, text, protected=()):
    """Atomically write UTF-8 text while preserving output path protections."""
    if not isinstance(text, str):
        raise ValueError("Text output must be a string")
    destination = Path(path).absolute()
    if destination.is_symlink() or _forbidden_symlink_component(destination):
        raise ValueError("Symlink output path is forbidden")
    protected_paths = {Path(item).resolve() for item in protected}
    if destination.exists():
        for item in protected:
            try:
                if os.path.samefile(destination, item):
                    raise ValueError("Output aliases protected input")
            except FileNotFoundError:
                pass
    if destination.resolve() in protected_paths:
        raise ValueError("Output path overlaps protected input")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".evaluation-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if _forbidden_symlink_component(destination):
            raise ValueError("Symlink output path component is forbidden")
        if destination.exists() and any(
            os.path.samefile(destination, item) for item in protected if Path(item).exists()
        ):
            raise ValueError("Output aliases protected input")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination


def write_json_atomic(path, data, protected=()):
    destination = Path(path).absolute()
    if destination.is_symlink():
        raise ValueError("Symlink output path is forbidden")
    # Reject symlinked parent directories, including dangling output symlinks.
    if _forbidden_symlink_component(destination):
        raise ValueError("Symlink output path component is forbidden")
    protected_paths = {Path(item).resolve() for item in protected}
    # Compare file identities as well as paths: hardlinks can alias protected inputs.
    if destination.exists():
        for item in protected:
            try:
                if os.path.samefile(destination, item):
                    raise ValueError("Output aliases protected input")
            except FileNotFoundError:
                pass
    if destination.resolve() in protected_paths:
        raise ValueError("Output path overlaps protected input")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".evaluation-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Recheck after serializing to reduce the path-swap window.
        if _forbidden_symlink_component(destination):
            raise ValueError("Output path changed to a symlink")
        if destination.exists() and any(
            os.path.samefile(destination, item) for item in protected if Path(item).exists()
        ):
            raise ValueError("Output aliases protected input")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination
