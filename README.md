# AI QA Evaluation Toolkit

Offline, provider-neutral evaluation of supplied AI decision artifacts. The toolkit compares expected outcomes with artifact files, reports case-level regressions, and applies configurable quality gates. It does **not** execute models, authenticate artifact authorship, or certify real-world model safety.

## Quick start

Requires Python 3.12 (the version used in current local verification). No third-party runtime packages are required for the demonstrated CLI comparison.

From the source repository root:

```sh
cd ai_qa_toolkit
python3 toolkit_cli.py compare \\
  --suite demo_cases.json \\
  --manifest demo_manifest.json \\
  --policy demo_policy.json \\
  --report demo-report.json \\
  --html demo-report.html
```

The sample is synthetic. The baseline passes all three cases; the candidate fails one privacy-related decision (SUP-003). The command intentionally exits with status **1** because the candidate fails the quality gate. The JSON and HTML reports explain the disagreement. Exit status **2** indicates invalid input.

## Data contract

- `evaluation-cases.v1`: case IDs, categories, expected decisions and synthetic fixtures.
- `evaluation-artifacts.v1`: external artifacts associated with those case IDs.
- `agent-comparison.v1`: names and relative artifact-file paths for at least two agents.
- `quality-gates.v1`: optional minimum quality thresholds.

Only the decisions `allow`, `deny` and `review` are supported by the current evaluation contract. External agent outputs must be converted to this contract before comparison; the toolkit does not contact an AI provider.

## Scope and trust boundaries

The source-only distribution excludes private integrations, client-specific evidence, historical release tooling and local development artifacts. Input hashes establish byte consistency, not authenticity. Reports describe agreement with supplied expected outcomes, not actual agent quality outside the supplied cases.

## Testing

Run the local regression suite from the repository root:

    python3 -m unittest discover -s tests -v

Check syntax and Git whitespace:

    python3 -m compileall -q ai_qa_toolkit tests
    git diff --check
    git diff --cached --check

The output-safety regression suite covers protected input files, symbolic and hard links, and synthetic runner report generation. These tests do not establish live model execution, complete filesystem race resistance, or production integration readiness.

## Development and release

This README is a **proposed public-source candidate**, not an approved public repository or proof of distribution rights. A clean repository, complete exact-file inventory, security/privacy review, dependency/license review and owner authorization are required before publication. Current release status: **HOLD**.
