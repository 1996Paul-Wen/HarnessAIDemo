# Base Agent

<cite>
**Referenced Files in This Document**
- [base.py](file://harness/agent/base.py)
- [task.py](file://harness/agent/task.py)
- [engine.py](file://harness/llm/engine.py)
- [registry.py](file://harness/tools/registry.py)
- [base.py](file://harness/tools/base.py)
- [manager.py](file://harness/context/manager.py)
- [hybrid.py](file://harness/memory/hybrid.py)
- [builtin.py](file://harness/tools/builtin.py)
- [demo_agent.py](file://demos/demo_agent.py)
- [manager.py](file://harness/session/manager.py)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for the new `set_memory()` method for runtime memory swapping
- Updated constructor parameters section to include memory management capabilities
- Enhanced session isolation and multi-session support documentation
- Added practical examples showing how to use `set_memory()` with SessionManager
- Updated troubleshooting guide with memory-related debugging information

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the BaseAgent class and its core Agent Loop that transforms an LLM into an autonomous agent through iterative reasoning. It covers how context is built, how LLM calls are made, how tool calls are executed and fed back, and how final responses are handled. It also documents the BaseAgent constructor parameters, the run() lifecycle, fallback behavior, subclassing patterns for custom agents, the enhanced AgentTrace debugging system, and the new runtime memory swapping capability that enables per-session isolation.

## Project Structure
The BaseAgent lives in the harness.agent package and orchestrates interactions with:
- LLM engine (message generation and tool call parsing)
- Tool registry (tool discovery and execution)
- Context manager (system prompt assembly, memory integration, history management)
- Memory systems (short-term and long-term storage with runtime swapping)
- Session manager (multi-session coordination with isolated memory contexts)

```mermaid
graph TB
subgraph "Agent"
BA["BaseAgent"]
TA["TaskAgent"]
AT["AgentTrace"]
SM["SessionManager"]
end
subgraph "LLM"
LLM["BaseLLM / Backends"]
end
subgraph "Tools"
TR["ToolRegistry"]
BT["Built-in Tools"]
end
subgraph "Context & Memory"
CM["ContextManager"]
HM["HybridMemory"]
SMEM["Session Memory"]
GM["Global Memory"]
end
BA --> LLM
BA --> TR
BA --> CM
BA --> AT
BA --> SM
CM --> HM
SM --> SMEM
SM --> GM
TR --> BT
```

**Diagram sources**
- [base.py:63-105](file://harness/agent/base.py#L63-L105)
- [task.py:32-73](file://harness/agent/task.py#L32-L73)
- [engine.py:127-141](file://harness/llm/engine.py#L127-L141)
- [registry.py:17-74](file://harness/tools/registry.py#L17-L74)
- [manager.py:41-118](file://harness/context/manager.py#L41-L118)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)

**Section sources**
- [base.py:1-177](file://harness/agent/base.py#L1-L177)
- [task.py:1-73](file://harness/agent/task.py#L1-L73)
- [engine.py:1-421](file://harness/llm/engine.py#L1-L421)
- [registry.py:1-74](file://harness/tools/registry.py#L1-L74)
- [manager.py:1-118](file://harness/context/manager.py#L1-L118)
- [hybrid.py:1-84](file://harness/memory/hybrid.py#L1-L84)
- [manager.py:1-306](file://harness/session/manager.py#L1-L306)

## Core Components
- BaseAgent: Implements the core agent loop, manages iteration, context building, LLM calls, tool execution, response handling, fallbacks, and runtime memory swapping.
- **Enhanced AgentTrace**: Records comprehensive step-by-step execution details including LLM calls, tool invocations, tool results, and final answers for debugging and monitoring multi-step reasoning processes.
- TaskAgent: A specialized agent subclass that sets a task-oriented system prompt and provides a structured execute_task interface.
- ContextManager: Assembles messages including system prompt, tool descriptions, memory context, conversation history, and current input.
- ToolRegistry: Central catalog for registering, listing, and executing tools with error handling.
- HybridMemory: Combines short-term and long-term memory to provide recent and relevant context.
- SessionManager: Manages multiple independent conversation sessions with isolated memory contexts and global shared memory.
- LLM Engine: Abstract interface and backends for generating responses and parsing tool calls from model output.

Key responsibilities:
- BaseAgent.run(): Orchestrates the full cycle per user turn with enhanced tracing.
- BaseAgent.set_memory(): Enables runtime memory swapping for session isolation.
- ContextManager.build_messages(): Builds the complete message list for each LLM call.
- ToolRegistry.execute(): Executes tools safely and returns results or errors.
- HybridMemory.get_relevant_context(): Merges recent and relevant past memories into context.

**Section sources**
- [base.py:38-177](file://harness/agent/base.py#L38-L177)
- [task.py:32-73](file://harness/agent/task.py#L32-L73)
- [manager.py:41-118](file://harness/context/manager.py#L41-L118)
- [registry.py:17-74](file://harness/tools/registry.py#L17-L74)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [engine.py:23-57](file://harness/llm/engine.py#L23-L57)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)

## Architecture Overview
The Agent Loop is the heart of the system. Each user turn triggers a controlled cycle with comprehensive tracing:
1. Build context using ContextManager (system prompt + tool descriptions + memory + history + current input).
2. Call LLM.generate() to get a response.
3. If no tool calls are requested, store the assistant response and return it as the final answer.
4. If tool calls are requested, execute each via ToolRegistry, append tool observations to history, and continue looping until a final answer is produced or max_iterations is reached.

```mermaid
sequenceDiagram
participant User as "User"
participant Agent as "BaseAgent"
participant Trace as "AgentTrace"
participant Ctx as "ContextManager"
participant LLM as "BaseLLM"
participant Reg as "ToolRegistry"
User->>Agent : run(user_input)
Agent->>Trace : Initialize trace
Agent->>Ctx : build_messages(history, user_input)
Ctx-->>Agent : messages
Agent->>Trace : add_step("llm_call", iteration)
Agent->>LLM : generate(messages)
LLM-->>Agent : LLMResponse(content, tool_calls)
alt No tool calls
Agent->>Trace : add_step("final_answer", content)
Agent->>Agent : append assistant to history
Agent-->>User : content (final answer)
else Tool calls present
loop For each tool call
Agent->>Trace : add_step("tool_call", name, args)
Agent->>Reg : execute(name, arguments)
Reg-->>Agent : ToolResult(success, output/error)
Agent->>Trace : add_step("tool_result", name, output)
Agent->>Agent : append tool observation to history
end
Agent->>LLM : generate(messages with tool results)
Note over Agent,LLM : Continue until final answer or max iterations
end
```

**Diagram sources**
- [base.py:97-172](file://harness/agent/base.py#L97-L172)
- [manager.py:61-104](file://harness/context/manager.py#L61-L104)
- [engine.py:127-141](file://harness/llm/engine.py#L127-L141)
- [registry.py:43-60](file://harness/tools/registry.py#L43-L60)

## Detailed Component Analysis

### BaseAgent Constructor Parameters
- name: Identifier for the agent instance used in logs and traces.
- llm: An LLM backend implementing BaseLLM; responsible for generating responses and parsing tool calls.
- system_prompt: Base instructions defining agent persona and behavior; extended by ContextManager with tool instructions.
- tool_registry: A ToolRegistry instance providing available tools and their descriptions; defaults to an empty registry.
- memory: A BaseMemory implementation; defaults to HybridMemory to combine short-term and long-term context.
- max_iterations: Upper bound on tool-call loops to prevent infinite cycles.
- verbose: Enables logging/printing of intermediate steps during execution.

These parameters configure the agent's capabilities, safety limits, and observability. The memory parameter can be swapped at runtime using the `set_memory()` method for session isolation.

**Section sources**
- [base.py:73-95](file://harness/agent/base.py#L73-L95)

### Runtime Memory Swapping: set_memory() Method
The `set_memory()` method enables runtime memory swapping between sessions, allowing for per-session isolation while maintaining a single agent instance.

**Functionality:**
- Swaps the memory instance at runtime without recreating the agent
- Updates both the agent's direct memory reference and the ContextManager's memory reference
- Enables seamless switching between different session contexts
- Supports multi-session architectures where each session maintains its own isolated memory

**Implementation Details:**
- Takes a BaseMemory instance as parameter
- Updates `self.memory` to point to the new memory instance
- Updates `self.context_manager.memory` to ensure context building uses the correct memory
- Maintains consistency between agent and context manager memory references

**Usage Pattern:**
```python
# Create agent with default memory
agent = BaseAgent(llm=llm, tool_registry=registry)

# Create separate sessions with isolated memory
session1_memory = HybridMemory(storage_path="session1_memory.json")
session2_memory = HybridMemory(storage_path="session2_memory.json")

# Switch between sessions
agent.set_memory(session1_memory)
# Agent now uses session1's isolated memory

agent.set_memory(session2_memory)
# Agent now uses session2's isolated memory
```

**Integration with SessionManager:**
The `set_memory()` method works seamlessly with the SessionManager to provide complete session isolation:
- SessionManager creates isolated HybridMemory instances for each session
- Agents can switch between sessions by calling `set_memory()` with the appropriate session memory
- Global memory can be shared across all sessions while maintaining session-specific isolation

**Section sources**
- [base.py:97-105](file://harness/agent/base.py#L97-L105)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)

### Agent Loop: run() Implementation
The run() method implements the core lifecycle with enhanced tracing:
- Initializes AgentTrace for each turn to capture comprehensive execution details.
- Iterates up to max_iterations times:
  - Builds messages via ContextManager.build_messages().
  - Calls LLM.generate() with the assembled messages.
  - Records LLM call step in trace with iteration number.
  - If no tool calls: appends assistant response to history, stores in memory, records final_answer trace, and returns content.
  - If tool calls exist:
    - Appends assistant message (if any content) to history.
    - For each tool call:
      - Records tool_call trace with name and arguments.
      - Executes tool via ToolRegistry.execute().
      - Records tool_result trace with output or error.
      - Appends tool observation message to history with role "tool".
    - Continues loop with updated history; subsequent iterations use empty user_input so the LLM sees tool results and decides next steps.
- Fallback: If max_iterations is reached without a final answer, appends a fallback assistant message and returns a polite error string.

```mermaid
flowchart TD
Start(["run(user_input)"]) --> Init["Initialize AgentTrace"]
Init --> Loop{"iteration < max_iterations?"}
Loop --> |No| Fallback["Append fallback assistant message<br/>Return fallback text"]
Loop --> |Yes| Build["ContextManager.build_messages(history, user_input)"]
Build --> RecordLLM["Record llm_call trace"]
RecordLLM --> CallLLM["LLM.generate(messages)"]
CallLLM --> HasTools{"response.has_tool_calls?"}
HasTools --> |No| StoreAnswer["Append assistant to history<br/>Store in memory<br/>Record final_answer trace"]
StoreAnswer --> ReturnAnswer["Return content"]
HasTools --> |Yes| AppendAssistant["Append assistant message if content exists"]
AppendAssistant --> ExecTools["For each tool call:<br/>Record tool_call trace<br/>execute via ToolRegistry<br/>Record tool_result trace"]
ExecTools --> AppendObs["Append tool observation to history"]
AppendObs --> NextIter["Continue loop with updated history"]
NextIter --> Loop
```

**Diagram sources**
- [base.py:97-172](file://harness/agent/base.py#L97-L172)

**Section sources**
- [base.py:97-172](file://harness/agent/base.py#L97-L172)

### Enhanced AgentTrace System
The AgentTrace system provides comprehensive execution tracing for debugging and monitoring multi-step reasoning processes:

**Step Recording Capabilities:**
- **LLM Calls**: Records each LLM invocation with iteration numbers for tracking reasoning progress.
- **Tool Invocations**: Captures tool names and arguments for every tool call attempt.
- **Tool Results**: Logs successful outputs or error messages from tool executions.
- **Final Answers**: Stores the ultimate response when the agent completes its task.

**Implementation Details:**
- `add_step(step_type, data)`: Adds structured entries with metadata like iteration numbers, tool names, arguments, and outputs.
- `summary()`: Generates human-readable logs suitable for debugging and monitoring, showing the complete execution flow.

**Usage Pattern:**
- Instantiated at the start of each run() call.
- Updated throughout the loop to capture LLM calls, tool executions, results, and final answers.
- Provides concise overview of execution flow for troubleshooting complex multi-step reasoning processes.

**Enhanced Features:**
- Comprehensive step type support: llm_call, tool_call, tool_result, final_answer
- Structured data capture with rich metadata
- Human-readable summary generation for easy debugging
- Integration with verbose logging for real-time monitoring

**Section sources**
- [base.py:38-61](file://harness/agent/base.py#L38-L61)
- [base.py:113-136](file://harness/agent/base.py#L113-L136)

### Context Building and Memory Integration
ContextManager.build_messages() constructs the full prompt:
- System message includes base system_prompt plus tool instructions and tool descriptions when tools are registered.
- HybridMemory.get_relevant_context() injects recent conversation and relevant past memories into the prompt.
- Conversation history is appended verbatim.
- Current user input is added as the last message.
- The user input is stored in memory for future retrieval.

This ensures the LLM has sufficient context while respecting token limits and prioritizing recent and relevant information. The memory integration supports runtime swapping through the `set_memory()` method.

**Section sources**
- [manager.py:61-104](file://harness/context/manager.py#L61-L104)
- [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-73)

### Tool Execution and Error Handling
ToolRegistry.execute() centralizes tool invocation:
- Looks up the tool by name; if not found, returns a ToolResult indicating failure with an error listing available tools.
- Invokes tool.execute(**arguments); catches exceptions and returns a failed ToolResult with the error message.
- Returns success/failure status along with output or error text for feedback to the agent.

Built-in tools demonstrate safe implementations:
- CalculatorTool validates expressions and evaluates safely.
- DateTimeTool returns formatted date/time based on query.
- FileOpsTool performs read-only operations with path validation.

**Section sources**
- [registry.py:43-60](file://harness/tools/registry.py#L43-L60)
- [base.py:144-164](file://harness/agent/base.py#L144-L164)
- [builtin.py:13-83](file://harness/tools/builtin.py#L13-L83)

### LLM Interface and Tool Call Parsing
BaseLLM defines the generate() contract returning LLMResponse with content and optional tool_calls.
Backends implement this contract:
- TransformersBackend loads models, applies chat templates, generates tokens, parses tool calls, and strips tool call blocks from content.
- MockBackend simulates tool calling behavior for demos and testing without GPU requirements.

ToolCallParser extracts tool calls from free-form text using multiple patterns, enabling flexible model outputs.

**Section sources**
- [engine.py:127-141](file://harness/llm/engine.py#L127-L141)
- [engine.py:206-241](file://harness/llm/engine.py#L206-L241)
- [engine.py:254-399](file://harness/llm/engine.py#L254-L399)
- [engine.py:61-123](file://harness/llm/engine.py#L61-L123)

### Creating Custom Agents by Subclassing BaseAgent
To create a specialized agent:
- Subclass BaseAgent and optionally override system_prompt to tailor behavior.
- Provide a higher max_iterations for complex tasks if needed.
- Implement a domain-specific method (e.g., execute_task) that wraps run() and returns structured results.
- Use `set_memory()` to enable session isolation for multi-session applications.

Example pattern:
- TaskAgent sets a task-oriented system prompt and exposes execute_task(task_description) which calls run() and returns a dict with success, result, and task fields.

Practical usage:
- Initialize an LLM backend (e.g., create_llm()).
- Create a ToolRegistry and register tools (e.g., register_default_tools).
- Instantiate TaskAgent with llm and registry.
- Use `set_memory()` to switch between sessions for multi-session support.
- Call execute_task for each objective and clear history between tasks if desired.

**Section sources**
- [task.py:32-73](file://harness/agent/task.py#L32-L73)
- [demo_agent.py:15-39](file://demos/demo_agent.py#L15-L39)
- [builtin.py:77-83](file://harness/tools/builtin.py#L77-L83)

### Multi-Session Management with SessionManager
The SessionManager provides comprehensive multi-session support with isolated memory contexts:

**Key Features:**
- Creates independent sessions with isolated memory storage
- Provides global memory shared across all sessions
- Enables seamless switching between sessions
- Persists session data to JSON files for durability

**Integration with BaseAgent:**
- Use `get_memory(session_id)` to retrieve session-specific memory
- Call `set_memory()` on agents to switch between sessions
- Leverage `search_memories()` for combined global and session search
- Maintain session isolation while sharing common knowledge

**Storage Architecture:**
- Each session has dedicated memory.json file for isolation
- Global memory.json provides shared cross-session knowledge
- Messages stored in append-only JSONL format for performance
- Metadata stored in JSON files for session management

**Section sources**
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

## Dependency Analysis
The following diagram shows key dependencies among components involved in the agent loop:

```mermaid
graph LR
BaseAgent["BaseAgent"] --> ContextManager["ContextManager"]
BaseAgent --> ToolRegistry["ToolRegistry"]
BaseAgent --> BaseLLM["BaseLLM"]
BaseAgent --> AgentTrace["AgentTrace"]
BaseAgent --> SessionManager["SessionManager"]
ContextManager --> HybridMemory["HybridMemory"]
ToolRegistry --> BaseTool["BaseTool"]
BaseLLM --> ToolCallParser["ToolCallParser"]
SessionManager --> BaseMemory["BaseMemory"]
```

**Diagram sources**
- [base.py:63-105](file://harness/agent/base.py#L63-L105)
- [manager.py:41-60](file://harness/context/manager.py#L41-L60)
- [registry.py:17-27](file://harness/tools/registry.py#L17-L27)
- [engine.py:127-141](file://harness/llm/engine.py#L127-L141)
- [engine.py:61-123](file://harness/llm/engine.py#L61-L123)
- [hybrid.py:22-31](file://harness/memory/hybrid.py#L22-L31)
- [base.py:30-45](file://harness/tools/base.py#L30-L45)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)

**Section sources**
- [base.py:63-105](file://harness/agent/base.py#L63-L105)
- [manager.py:41-60](file://harness/context/manager.py#L41-L60)
- [registry.py:17-27](file://harness/tools/registry.py#L17-L27)
- [engine.py:127-141](file://harness/llm/engine.py#L127-L141)
- [hybrid.py:22-31](file://harness/memory/hybrid.py#L22-L31)
- [base.py:30-45](file://harness/tools/base.py#L30-L45)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)

## Performance Considerations
- Token budgeting: ContextManager.estimate_tokens() provides a rough estimate (~4 chars per token) to help manage context windows. In production, use actual tokenizer counts for precision.
- Memory pruning: HybridMemory.get_recent(n) limits short-term context size; adjust capacity to balance relevance and cost.
- Max iterations: Tune max_iterations to avoid excessive LLM calls and tool executions for complex tasks.
- Tool efficiency: Prefer tools that return concise outputs; large tool outputs increase context size and cost.
- Backend selection: Use MockBackend for fast iteration and testing; switch to TransformersBackend for real inference when ready.
- **Tracing overhead**: AgentTrace adds minimal overhead but provides valuable debugging insights; consider disabling verbose mode in production for performance.
- **Memory swapping overhead**: The `set_memory()` method provides O(1) complexity for session switching, making it efficient for frequent session changes.
- **Session isolation benefits**: Per-session memory isolation prevents context pollution and improves performance by limiting memory scope.

## Troubleshooting Guide
Common issues and resolutions:
- Infinite loops: Ensure max_iterations is set appropriately; verify tool outputs do not repeatedly trigger additional tool calls.
- Missing tools: Confirm tools are registered in ToolRegistry; check tool names match exactly what the model requests.
- Tool execution errors: Inspect ToolResult.error messages; validate input schemas and handle edge cases in tool.execute().
- Context overflow: Reduce history length or limit memory retrieval; consider truncating tool outputs before appending to history.
- **Enhanced Debugging**: Use AgentTrace.summary() to review the complete sequence of LLM calls, tool executions, results, and final answers for understanding multi-step reasoning flows.
- **Multi-step Reasoning Issues**: Leverage the comprehensive AgentTrace to identify where reasoning breaks down in complex workflows by examining the step-by-step execution log.
- **Memory Isolation Issues**: Verify that `set_memory()` is called correctly when switching sessions; ensure both agent and context manager memory references are updated.
- **Session Persistence Problems**: Check that SessionManager properly persists session data; verify file permissions and storage directory structure.
- **Cross-Session Contamination**: Ensure proper use of `set_memory()` to maintain session isolation; verify that global memory doesn't interfere with session-specific data.

**Section sources**
- [registry.py:43-60](file://harness/tools/registry.py#L43-L60)
- [base.py:144-172](file://harness/agent/base.py#L144-L172)
- [base.py:38-61](file://harness/agent/base.py#L38-L61)
- [base.py:97-105](file://harness/agent/base.py#L97-L105)
- [manager.py:118-152](file://harness/session/manager.py#L118-L152)

## Conclusion
BaseAgent encapsulates the essential Agent Loop that turns an LLM into an autonomous agent by iteratively building context, invoking the model, executing tools, and handling responses. Its constructor parameters allow customization of identity, capabilities, memory, and verbosity. The run() method manages the lifecycle, enforces iteration limits, and provides fallback behavior. The enhanced AgentTrace system provides comprehensive visibility into execution steps for debugging and monitoring multi-step reasoning processes. The new `set_memory()` method enables runtime memory swapping for session isolation, supporting multi-session architectures with per-session context management. Subclassing BaseAgent enables domain-specific agents like TaskAgent, while the tool and memory ecosystems provide extensibility and robustness.

## Appendices

### Practical Example: Running a Task Agent
- Configure environment to use MockBackend for quick demos.
- Create an LLM via create_llm().
- Register default tools using register_default_tools(registry).
- Instantiate TaskAgent with llm and registry.
- Execute tasks via execute_task() and clear history between runs.

### Practical Example: Multi-Session Memory Management
```python
from harness.session.manager import SessionManager
from harness.agent.base import BaseAgent

# Create session manager
session_mgr = SessionManager(storage_dir=".sessions")

# Create two sessions with isolated memory
session1 = session_mgr.create_session("Python Project")
session2 = session_mgr.create_session("Cooking Recipes")

# Get isolated memory for each session
memory1 = session_mgr.get_memory(session1.id)
memory2 = session_mgr.get_memory(session2.id)

# Create agent and switch between sessions
agent = BaseAgent(llm=llm, tool_registry=registry)

# Work on Python project
agent.set_memory(memory1)
result1 = agent.run("How do I implement a binary search?")

# Switch to cooking recipes
agent.set_memory(memory2)
result2 = agent.run("What ingredients do I need for pasta?")

# Both sessions maintain isolated context
```

**Section sources**
- [demo_agent.py:15-39](file://demos/demo_agent.py#L15-L39)
- [builtin.py:77-83](file://harness/tools/builtin.py#L77-L83)
- [manager.py:118-152](file://harness/session/manager.py#L118-L152)
- [base.py:97-105](file://harness/agent/base.py#L97-L105)