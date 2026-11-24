# CLI Reference

## Compare

From `ai_qa_toolkit/`:

```sh
python3 toolkit_cli.py compare \
  --suite demo_cases.json \
  --manifest demo_manifest.json \
  --policy demo_policy.json \
  --report demo-report.json \
  --html demo-report.html
```

| Option | Purpose |
| --- | --- |
| `--suite` | Supplied evaluation cases |
| `--manifest` | Supplied comparison manifest |
| `--policy` | Optional quality gate policy |
| `--report` | JSON report output |
| `--html` | HTML report output |

For the documented demo, exit code `1` means the candidate fails its gate; `2` indicates invalid input. Do not treat a successful comparison as proof of model safety or artifact provenance.

## Regression

From repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q ai_qa_toolkit tests
```

These are local source checks, not evidence of live provider integration.
