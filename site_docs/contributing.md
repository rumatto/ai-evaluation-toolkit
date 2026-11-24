# Contributing

Keep the evaluation engine provider-neutral and local-first. Prefer small changes with regression coverage and stable input/output contracts.

Before proposing changes, run:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q ai_qa_toolkit tests
git diff --check
```

When editing documentation, install `docs-requirements.txt` and run:

```sh
python -m mkdocs build --strict
```

Do not include private credentials, client data, or internal infrastructure artifacts in public changes. Separate synthetic test results from verified integration evidence.
