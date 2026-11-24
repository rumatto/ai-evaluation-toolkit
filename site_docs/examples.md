# Examples

The public source includes a synthetic comparison dataset:

- `ai_qa_toolkit/demo_cases.json` — expected decisions.
- `ai_qa_toolkit/demo_manifest.json` — supplied comparison references.
- `ai_qa_toolkit/demo_policy.json` — gate thresholds.

Run the command on the [Quick Start](quick-start.md) page.

**Expected demonstration:** the baseline matches three cases and the candidate fails a privacy-related decision (`SUP-003`), resulting in a nonzero gate exit.

Do not substitute these synthetic cases for a validated production evaluation dataset.
