# Architecture

## Scope B: independent evaluation

The public toolkit compares supplied decision artifacts offline. It is independent of private adapters, client-specific integrations, and historical release tooling.

### Inputs

- `evaluation-cases.v1` — cases, categories, expected decisions, fixtures.
- `evaluation-artifacts.v1` — associated external artifact files.
- `agent-comparison.v1` — at least two named artifact sets.
- `quality-gates.v1` — optional thresholds.

### Outputs

- Case-level comparisons and regressions.
- Machine-readable JSON reports.
- Human-readable HTML reports.
- Quality-gate outcomes and command exit codes.

### Trust boundaries

The toolkit does **not** execute AI models, prove artifact authorship, verify the truth of expected decisions, or certify deployment safety. A hash demonstrates byte consistency, not provenance. Evaluation results are scoped to supplied inputs.

The public source baseline excludes private infrastructure and client-specific evidence.
