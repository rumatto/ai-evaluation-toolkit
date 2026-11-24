# User Guide

## Workflow

1. Define expected decisions in an `evaluation-cases.v1` suite.
2. Supply external artifact files referenced by an `evaluation-artifacts.v1` contract.
3. Use an `agent-comparison.v1` manifest with relative paths for at least two agents.
4. Optionally supply a `quality-gates.v1` policy.
5. Run `compare` and inspect the JSON and HTML reports.

The supported decision values are `allow`, `deny`, and `review`. Convert any external provider output to the supported artifact contract **before** evaluation.

## Interpreting results

A reported pass means agreement with supplied expected outcomes for the supplied cases. A failure identifies a disagreement or failed threshold; it does not by itself establish a real-world safety defect.

Input hashes help identify byte changes. They do not authenticate artifact origin, author, or execution environment.

See [Architecture](architecture.md) for the trust boundary.
