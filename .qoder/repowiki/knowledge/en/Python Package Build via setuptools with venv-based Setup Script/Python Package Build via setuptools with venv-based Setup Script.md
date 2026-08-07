---
kind: build_system
name: Python Package Build via setuptools with venv-based Setup Script
category: build_system
scope:
    - '**'
source_files:
    - pyproject.toml
    - requirements.txt
    - setup.sh
    - .python-version
    - run.py
---

## Build System Overview

This repository uses a minimal Python packaging setup centered on `setuptools` (configured via `pyproject.toml`) and a shell-based environment bootstrap script. There is no Makefile, Dockerfile, CI pipeline, or release automation present.

### Packaging & Distribution
- **Build backend**: `setuptools.backends._legacy:_Backend` with `setuptools>=68.0` and `wheel` declared in `[build-system]` of `pyproject.toml`.
- **Package metadata**: project name `harness-ai-demo`, version `0.1.0`, requires Python `>=3.11`, MIT license, readme sourced from `README.md`.
- **Dependency declaration**: dependencies are listed both in `pyproject.toml` (`torch`, `transformers`, `accelerate`, `rich`, `pyyaml`, `numpy`) and mirrored in `requirements.txt` — the two files are kept in sync by convention rather than enforced by tooling.
- **Package discovery**: `tool.setuptools.packages.find` includes only packages matching `harness*`, so only the `harness/` package is distributed.
- **Console entry point**: a script target `harness-demo = "harness.cli:main"` is registered under `[project.scripts]`, installing a `harness-demo` command when the package is installed.

### Environment Bootstrap
- **Version pinning**: `.python-version` pins `3.11.15`; `setup.sh` enforces Python 3.11 at runtime by scanning for `python3.11`, `python3`, or `python` and rejecting any other version.
- **Virtual environment**: `setup.sh` creates (or reuses) a `.venv/` directory at the repo root using `python -m venv`. It then upgrades pip, installs from `requirements.txt`, and finally installs the project itself in editable mode (`pip install -e .`).
- **Activation instructions**: after setup, users activate via `source .venv/bin/activate` and run demos through `run.py` (which delegates to `harness.cli:main`).

### Runtime Entry Points
- `run.py` is the documented user-facing entry point; it inserts the project root into `sys.path` and calls `harness.cli.main()`, dispatching subcommands like `chat`, `agent`, `multi-agent`, `mcp`, `skills`, `session`.
- The `harness-demo` console script (installed by `pip install -e .`) provides an alternative entry path into the same CLI.

### Conventions Observed
- Dependencies are declared in two places (`pyproject.toml` and `requirements.txt`) and must be kept in sync manually — there is no tool that auto-syncs them.
- The project is always developed in an editable install inside a dedicated `.venv/` virtual environment created by `setup.sh`; direct `pip install` without first running setup is not the documented workflow.
- No build steps beyond `pip install` exist: there are no compilation targets, no pre-commit hooks, no lint/typecheck scripts, no test runner invocation, no Docker image definition, and no CI configuration files anywhere in the repository.
- Versioning is a flat string in `pyproject.toml` with no changelog or tag-based release process defined.

### Constraints Enforced by Scripts
- `setup.sh` exits with error if Python 3.11 is not found on the system PATH (enforced via `set -e` and an explicit version check).
- The virtual environment must live at `.venv/` relative to the repo root; moving the repo breaks the script's path resolution.