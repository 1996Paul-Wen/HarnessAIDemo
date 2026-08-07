---
kind: error_handling
name: Ad-hoc Python Exceptions, ToolResult-based tool errors, and logging-only I/O failure handling
category: error_handling
scope:
    - '**'
source_files:
    - harness/llm/engine.py
    - harness/tools/builtin.py
    - harness/mcp/protocol.py
    - harness/memory/long_term.py
    - harness/session/manager.py
    - harness/skill/loader.py
    - harness/cli.py
---

This repository does not define a custom exception hierarchy or centralized error-handling framework. Instead, error handling is scattered across modules using three complementary patterns:

1. **Built-in Python exceptions raised at boundaries**
   - `harness/llm/engine.py`: `create_llm` raises `ValueError(f"Unknown LLM backend: {config.backend}")` for an unrecognized backend; `_load_model` raises `ImportError` with a descriptive message when `transformers`/`torch` are missing.
   - `harness/skill/loader.py`: `SkillLoader.load` raises `FileNotFoundError(f"Skill not found: {skill_name}")` when the SKILL.md file is absent.
   - `harness/session/manager.py`: `switch_session` raises `ValueError(f"Session not found: {session_id}")` for an unknown session id.
   These are the only places where domain-level validation failures bubble up as exceptions to callers; there is no shared base class — each module uses the most specific built-in exception it needs.

2. **ToolResult-based return-value error signaling (tools layer)**
   - `harness/tools/builtin.py` implements tools against `BaseTool.execute`, which returns a `ToolResult(success, content)` object rather than raising. Errors are encoded in `success=False` plus an error string (e.g. invalid expression characters, file-not-found, unknown operation). This pattern lets the agent loop treat tool failures as recoverable data instead of control-flow exceptions.
   - The MCP client adapter (`harness/mcp/protocol.py`, `MCPClient.get_tools_for_registry`) wraps MCP responses into the same `ToolResult` contract: if `resp.error` is set, it returns `ToolResult(False, "", resp.error)`, bridging protocol-level errors back into the tool-result convention.

3. **Logging + swallow for I/O and parsing failures**
   - `harness/memory/long_term.py`: `_save` and `_load` wrap filesystem JSON operations in `try/except Exception` and log via `logger.error(...)` without re-raising; load failures leave the in-memory list empty, so memory loss is tolerated.
   - `harness/session/manager.py._load_all`: similarly catches `Exception` on per-file JSON loads and logs them, skipping bad files.
   - `harness/mcp/protocol.py.MCPServer.handle_request`: a single `except Exception as e` around the entire request dispatch returns `MCPResponse(error=str(e))`, turning any handler crash into a JSON-RPC error envelope rather than crashing the server.
   - `harness/llm/engine.py.ToolCallParser._try_parse`: silently swallows `json.JSONDecodeError, TypeError, KeyError` and returns `None`, treating malformed model output as non-tool-call text.
   - `harness/skill/loader.py.load_all`: catches `Exception` per skill and logs it, continuing to load remaining skills.

4. **User-input / process lifecycle handling**
   - `harness/cli.py` (and `demos/demo_chat.py`) wrap `input()` calls in `try/except (EOFError, KeyboardInterrupt)` to allow clean Ctrl-C / EOF exit from interactive demos.
   - `run.py` / `cli.main` use `sys.exit(1)` for usage errors (unknown demo name, missing argument).

5. **No panics/recover, no middleware**
   - There are no `raise ...Error` sentinel classes, no `try/except` blocks around agent loops that convert exceptions into structured results, no global exception handlers, and no HTTP/middleware-style error middleware. Errors either propagate as standard Python exceptions, are returned as `ToolResult`/`MCPResponse` objects, or are logged and swallowed to keep the system running.

**Observed conventions**
- I/O-bound methods (`_save`, `_load`, `_load_all`) catch broad `Exception` and log via the module's `logging.getLogger(__name__)` logger instead of failing loudly.
- Parsing/validation failures inside internal helpers (JSON parsing, tool-call extraction) are treated as non-fatal by returning `None` or default values.
- Public-facing APIs that represent user-visible configuration or lookup failures raise specific built-in exceptions (`ValueError`, `FileNotFoundError`, `ImportError`).
- Tool implementations never raise; they always return a `ToolResult` with `success=False` and a human-readable message, making tool failures part of normal data flow.