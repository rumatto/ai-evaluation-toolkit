# Getting Started

AI QA Evaluation Toolkit is a local-first framework for evaluating **supplied** AI decision artifacts. It does not invoke models.

## Requirements

- Python 3.12 (the version documented for the current local baseline).
- A local checkout of the [public source repository](https://github.com/rumatto/ai-evaluation-toolkit).
- No third-party runtime packages for the demonstrated CLI comparison.

Clone the repository:

```sh
git clone https://github.com/rumatto/ai-evaluation-toolkit.git
cd ai-evaluation-toolkit
```

Proceed to the [Quick Start](quick-start.md) to run the bundled synthetic example.

## Documentation development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r docs-requirements.txt
python -m mkdocs serve
```

The website build is separate from the toolkit runtime.
