---
kind: configuration_system
name: Environment-Driven Dataclass Configuration for LLM and Agent Runtime
category: configuration_system
scope:
    - '**'
source_files:
    - harness/config.py
    - harness/llm/engine.py
    - run.py
    - harness/cli.py
    - pyproject.toml
---

## What system/approach is used

The repository uses a lightweight, code-first configuration approach built on Python `dataclasses` with environment variable overrides. There are no YAML/JSON/TOML config files at runtime; all runtime behavior is controlled via `HARNESS_*` environment variables read through `os.getenv`. The central module `harness/config.py` defines typed configuration dataclasses (`LLMConfig`, `MemoryConfig`, `AgentConfig`, `HarnessConfig`) that expose defaults and an `from_env()` classmethod to populate fields from the environment.

## Key files and packages

- `harness/config.py` — Defines all configuration dataclasses and the `HarnessConfig.default()` factory that composes them. `LLMConfig.from_env()` reads five environment variables: `HARNESS_LLM_BACKEND`, `HARNESS_MODEL_NAME`, `HARNESS_MAX_TOKENS`, `HARNESS_TEMPERATURE`, `HARNESS_DEVICE`.
- `harness/llm/engine.py` — Consumes configuration via `create_llm(config=None)`, which falls back to `LLMConfig.from_env()` when no explicit config is passed. The `backend` field selects between `MockBackend` and `TransformersBackend`.
- `run.py` — Documents the supported environment variables in its docstring and delegates to `harness.cli.main`.
- `harness/cli.py` — Repeats environment variable documentation in its module docstring and usage help; demos hardcode paths (e.g., `.chat_memory.json`, `.demo_sessions`) rather than reading them from config.
- `pyproject.toml` — Declares `pyyaml>=6.0.1` as a dependency but it is not imported anywhere in the codebase; no `[tool.setuptools]` or `[project.scripts]` beyond the `harness-demo` entry point.
- `demos/demo_*.py` — Each demo script sets `os.environ.setdefault("HARNESS_LLM_BACKEND", "mock")` before importing harness modules, demonstrating per-demo override of the backend.

## Architecture and conventions

1. **Single source of truth**: `harness/config.py` is the only place where configuration keys and defaults are declared. Other modules import `LLMConfig` and call `from_env()` or receive a pre-built `LLMConfig` instance.
2. **Environment-only overrides**: All configurable values come from `os.getenv` with hardcoded defaults. There is no file-based config loader, no `.env` parser, and no CLI argument parsing for configuration.
3. **Dataclass composition**: `HarnessConfig` composes `LLMConfig`, `MemoryConfig`, and `AgentConfig` using `field(default_factory=...)`, providing a single top-level object that can be passed around if needed.
4. **Factory pattern for selection**: `create_llm()` in `harness/llm/engine.py` is the sole entry point for instantiating an LLM backend. It inspects `config.backend` and returns either `MockBackend` or `TransformersBackend`; any other value raises `ValueError`.
5. **Hardcoded runtime paths outside config**: Memory persistence (`memory_store.json`), chat memory (`.chat_memory.json`), session storage (`.demo_sessions`), and skills directory (`demos/skills`) are literal strings passed directly to constructors in the demos and CLI. They are not exposed via `MemoryConfig` or `HarnessConfig`.
6. **No feature flags or secret management**: Secrets (model names, API keys) are expected to be supplied via environment variables; there is no secrets file, vault integration, or validation beyond type coercion (`int`, `float`).
7. **Dependency coupling**: `pyyaml` is listed in `pyproject.toml` dependencies but never imported; the configuration system does not use YAML despite the dependency being present.

## Conventions and constraints

- Environment variables must be prefixed with `HARNESS_` (observed across all five LLM-related variables).
- `HARNESS_LLM_BACKEND` accepts exactly two values: `"mock"` and `"transformers"`; any other string causes `create_llm` to raise `ValueError`.
- `HARNESS_DEVICE` accepts `"cpu"`, `"cuda"`, `"mps"`, or `"auto"`; `"auto"` triggers runtime detection via `torch.cuda.is_available()` / MPS availability.
- Defaults are always defined inline in the dataclass field definitions, so running without any environment set yields a working mock-backed agent.
- Demo scripts enforce the mock backend by calling `os.environ.setdefault("HARNESS_LLM_BACKEND", "mock")` before importing harness modules, ensuring deterministic demo runs even if the user has a real model configured.
- No schema validation is performed beyond Python's native type coercion; invalid values (e.g., non-numeric `HARNESS_MAX_TOKENS`) will raise `ValueError` at load time.