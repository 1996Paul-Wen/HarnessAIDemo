---
kind: dependency_management
name: Python Dependency Management via pyproject.toml, requirements.txt, and venv
category: dependency_management
scope:
    - '**'
source_files:
    - pyproject.toml
    - requirements.txt
    - setup.sh
    - .python-version
    - .gitignore
---

## What system/approach is used

This repository manages Python dependencies using a dual-manifest approach:
- **`pyproject.toml`** declares the package metadata, build backend (`setuptools` with `wheel`), project name (`harness-ai-demo`), minimum Python version (`>=3.11`), runtime dependencies, and an entry point script (`harness-demo = "harness.cli:main"`).
- **`requirements.txt`** mirrors the same runtime dependency list for environments that install via `pip install -r requirements.txt`.
- A local virtual environment (`.venv/`) is created by the provided `setup.sh` bootstrap script, which pins the interpreter to Python 3.11 (also declared in `.python-version`).

There is no lockfile (no `Pipfile.lock`, `poetry.lock`, `uv.lock`, or `requirements.lock`), no vendored third-party packages under `vendor/`, and no private PyPI registry configuration — dependencies are resolved at install time from the default PyPI index.

## Key files and packages

- `pyproject.toml` — canonical source of truth for the package definition and its runtime dependencies (`torch`, `transformers`, `accelerate`, `rich`, `pyyaml`, `numpy`).
- `requirements.txt` — human-readable mirror of the same dependency set, grouped into comments (`Core dependencies`, `CLI & Display`, `Config`, `Utilities`).
- `setup.sh` — bootstraps the environment: finds Python 3.11, creates `.venv`, upgrades `pip`, installs `requirements.txt`, then installs the project in editable mode (`pip install -e .`).
- `.python-version` — pins the exact interpreter version (`3.11.15`) for tools like `pyenv`/`asdf`.
- `.gitignore` — excludes `.venv/` so the virtual environment is never committed.

## Architecture and conventions

- **Single source of dependencies**: both manifests list the identical six runtime dependencies with lower-bound version specifiers (`>=X.Y.Z`). The `pyproject.toml` is the authoritative declaration; `requirements.txt` exists as a convenience for `pip install -r` workflows.
- **Editable install**: after installing requirements, `setup.sh` runs `pip install -e "$PROJECT_DIR"`, enabling development-time imports of the `harness` package without rebuilding.
- **No pinned versions**: all dependencies use open-ended `>=` constraints, meaning reproducible builds rely on the current PyPI state rather than a lockfile.
- **Build system**: uses classic setuptools (`build-backend = "setuptools.backends._legacy:_Backend"`) with `packages.find(include=["harness*"])` to auto-discover the `harness` package tree.
- **Entry points**: the CLI is exposed via `[project.scripts] harness-demo = "harness.cli:main"`, installed when the package is installed.

## Conventions and constraints

- **Python version pinning**: the project requires Python ≥ 3.11 (`requires-python = ">=3.11"` in `pyproject.toml`) and the setup script explicitly searches for `python3.11` / `python3` / `python` and aborts if none matches version `3.11`; `.python-version` further pins `3.11.15`.
- **Virtual environment isolation**: `.venv/` is created per-machine and ignored by Git; users must run `./setup.sh` (or manually create a venv) before running demos.
- **Dependency sources**: no custom `--index-url`, `--extra-index-url`, or `PIP_*` environment variables are configured; all packages resolve from the default PyPI.
- **No lockfiles or vendoring**: there is no mechanism to freeze transitive dependency versions, nor any vendored third-party code — reproducibility is not enforced beyond the minimum version bounds.
- **Runtime-only dependencies**: only runtime libraries are listed; dev/test tooling (linters, formatters, test runners) does not appear in either manifest and would need to be added separately.