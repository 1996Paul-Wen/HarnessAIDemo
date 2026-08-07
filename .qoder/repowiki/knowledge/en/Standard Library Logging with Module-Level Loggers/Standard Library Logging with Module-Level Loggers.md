---
kind: logging_system
name: Standard Library Logging with Module-Level Loggers
category: logging_system
scope:
    - '**'
source_files:
    - harness/cli.py
    - harness/agent/base.py
    - harness/config.py
---

## What system/approach is used

The repository uses Python's built-in `logging` module exclusively — no third-party logging framework (e.g. `loguru`, `structlog`, `sentry-sdk`) is imported anywhere. Each module that needs to emit logs creates a module-level logger via `logging.getLogger(__name__)`, and the application root configures a single console handler through `logging.basicConfig()` in the CLI entry point.

## Key files and packages

- **`harness/cli.py`** — The only place where logging is configured globally: `logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")`. It also defines the root logger name `harness.cli`.
- **`harness/agent/base.py`** — Defines `logger = logging.getLogger(__name__)` and emits an `INFO` log for each LLM raw output during the agent loop (`[AgentName] LLM raw output: ...`).
- Other modules that import `logging` and create a module logger but do not appear to emit calls in the sampled lines: `harness/agent/orchestrator.py`, `harness/context/manager.py`, `harness/llm/engine.py`, `harness/mcp/protocol.py`, `harness/memory/long_term.py`, `harness/session/manager.py`, `harness/skill/loader.py`, `harness/tools/registry.py`.

## Architecture and conventions

1. **Single global configuration**: All log output is routed through one `basicConfig` call at process start in `harness/cli.py`. There is no per-module or per-component handler setup; every module inherits this single console handler.
2. **Module-scoped loggers**: Every component obtains its logger via `logging.getLogger(__name__)`, producing hierarchical names such as `harness.agent.base`, `harness.context.manager`, etc. This lets consumers filter by package later if needed.
3. **Log level strategy**: The default level is `INFO`. No code sets different levels on individual loggers, so all modules share the same threshold. Verbose runtime diagnostics are emitted via `print(...)` statements (e.g. tool call messages in `base.py`), not via separate `DEBUG` log records.
4. **Message format**: A fixed template is used everywhere: `%(asctime)s [%(name)s] %(message)s` with `%H:%M:%S` timestamps. Messages are plain strings — there is no structured field serialization (no JSON payloads, no custom formatters).
5. **No centralized logging utility**: There is no shared helper function wrapping `logger.info/debug/warn/error`; each module writes directly to its own logger instance.
6. **No file sink**: `basicConfig` is invoked without a `filename` argument, so all logs go to stderr/stdout. There is no rotation, no file-based persistence, and no external sink.
7. **No exception logging convention**: The sampled code does not show `logger.exception(...)` usage; errors in tools are surfaced via return objects (e.g. `result.error`) rather than logged centrally.

## Conventions and constraints observed

- **Convention**: Create a module-level `logger = logging.getLogger(__name__)` at the top of any module that needs to log. This pattern is consistent across `agent/base.py`, `agent/orchestrator.py`, `context/manager.py`, `llm/engine.py`, `mcp/protocol.py`, `memory/long_term.py`, `session/manager.py`, `skill/loader.py`, and `tools/registry.py`.
- **Constraint**: Do not call `logging.basicConfig` outside `harness/cli.py` — doing so would reconfigure the root handler and could reset the level/format set by the CLI.
- **Constraint**: There is no programmatic way to change log verbosity at runtime; the only knob is the `level=` argument passed to `basicConfig` in the CLI. Per-component debug toggles use the `verbose` boolean attribute on agents (e.g. `BaseAgent.__init__(verbose=True)`) and guard `print` statements, not log levels.
- **Constraint**: Log output is unstructured text; consumers should not rely on parseable fields beyond the timestamp and logger name already present in the format string.