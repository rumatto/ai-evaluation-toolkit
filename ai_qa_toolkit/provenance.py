"""Strict, local-only provenance manifests for untrusted evaluation inputs.

Hashes prove byte equality, not authorship or that an agent really ran.
"""
import hashlib
import json
from pathlib import Path

MAX_INPUT_BYTES = 8 * 1024 * 1024


def read_json_limited(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError('Input must be a regular JSON file <= 8 MiB')
    with path.open('rb') as stream:
        payload = stream.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise ValueError('Input exceeds 8 MiB')
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    return json.loads(payload.decode('utf-8'), object_pairs_hook=unique_keys,
                      parse_constant=reject_constant)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def make_manifest(suite_path, artifact_paths):
    suite_path = Path(suite_path).resolve(strict=True)
    if not isinstance(artifact_paths, dict) or not artifact_paths:
        raise ValueError('At least one named artifact is required')
    entries = []
    for name, path in sorted(artifact_paths.items()):
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Artifact name required')
        resolved = Path(path).resolve(strict=True)
        if resolved == suite_path:
            raise ValueError('Suite cannot also be an artifact')
        entries.append({'name': name, 'file': resolved.name, 'sha256': sha256(resolved)})
    return {'schemaVersion': 'evaluation-provenance.v1',
            'suite': {'file': suite_path.name, 'sha256': sha256(suite_path)},
            'artifacts': entries,
            'originVerified': False,
            'agentExecutedByToolkit': False,
            'note': 'SHA-256 proves byte equality only; origin and execution are unverified.'}


def verify_manifest(manifest, directory):
    if not isinstance(manifest, dict) or manifest.get('schemaVersion') != 'evaluation-provenance.v1':
        raise ValueError('Unsupported provenance manifest')
    base = Path(directory).resolve(strict=True)
    entries = [manifest.get('suite'), *(manifest.get('artifacts') or [])]
    if not entries or not isinstance(manifest.get('artifacts'), list):
        raise ValueError('Missing provenance entries')
    checked = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('file'), str):
            raise ValueError('Malformed provenance entry')
        name = entry['file']
        if name in ('', '.', '..') or Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('Only files directly inside manifest directory are allowed')
        path = (base / name).resolve(strict=True)
        if path.parent != base or not path.is_file():
            raise ValueError('Provenance file escapes manifest directory')
        if sha256(path) != entry.get('sha256'):
            raise ValueError('Provenance digest mismatch: ' + name)
        checked.append(name)
    if len(set(checked)) != len(checked):
        raise ValueError('Duplicate provenance files')
    return {'verifiedByteHashes': len(checked), 'originVerified': False}
