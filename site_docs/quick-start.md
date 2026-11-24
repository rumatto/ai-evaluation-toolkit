# Quick Start

Run from the repository root:

```sh
cd ai_qa_toolkit
python3 toolkit_cli.py compare \
  --suite demo_cases.json \
  --manifest demo_manifest.json \
  --policy demo_policy.json \
  --report demo-report.json \
  --html demo-report.html
```

This is a **synthetic** comparison. The baseline matches all three supplied cases. The candidate disagrees on the privacy-related decision for `SUP-003`.

The command intentionally exits with **1** when the candidate fails the quality gate. Exit **2** indicates invalid input. Inspect the generated JSON and HTML reports to understand the case-level findings.

The demo is not a live AI evaluation.
