"""Bounded, read-only repository evidence collection for an explicitly supplied root.

This library does not authorize a workspace; callers must enforce that boundary.
Digest matching proves byte integrity, not origin or AI authorship.
"""
import hashlib
import os
import re
import stat
from pathlib import Path

MAX_FILES = 32
MAX_FILE_BYTES = 131072
MAX_TOTAL_BYTES = 1048576

def collect_repository_evidence(root, workspace, commit, paths):
    if not isinstance(workspace, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", workspace):
        raise ValueError("Invalid workspace")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid commit")
    if not isinstance(paths, list) or not 0 < len(paths) <= MAX_FILES or any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(paths):
        raise ValueError("Invalid evidence paths")
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != root:
        raise ValueError("Unsafe repository root")
    base = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    evidence = []
    total = 0
    try:
        for rel in paths:
            if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or ":" in rel or any(ord(ch) < 32 or ord(ch) == 127 for ch in rel) or any(p in ("", ".", "..") for p in rel.split("/")):
                raise ValueError("Unsafe evidence path")
            parts = rel.split("/")
            directory = os.dup(base)
            try:
                for component in parts[:-1]:
                    nextfd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                    os.close(directory)
                    directory = nextfd
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                try:
                    before = os.fstat(fd)
                    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
                        raise ValueError("Unsafe evidence file")
                    data = b""
                    while len(data) <= MAX_FILE_BYTES:
                        chunk = os.read(fd, min(65536, MAX_FILE_BYTES + 1 - len(data)))
                        if not chunk:
                            break
                        data += chunk
                    after = os.fstat(fd)
                    if len(data) > MAX_FILE_BYTES or len(data) != before.st_size or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                        raise ValueError("Evidence changed during collection")
                    total += len(data)
                    if total > MAX_TOTAL_BYTES:
                        raise ValueError("Evidence limit exceeded")
                    evidence.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
                finally:
                    os.close(fd)
            finally:
                os.close(directory)
    finally:
        os.close(base)
    return {"repository": {"workspace": workspace, "commit": commit}, "evidence": evidence, "integrity": "collected-untrusted-authorship"}
