# Session Management

<cite>
**Referenced Files in This Document**
- [manager.py](file://harness/session/manager.py)
- [demo_session.py](file://demos/demo_session.py)
- [demo_memory.py](file://demos/demo_memory.py)
- [manager.py](file://harness/context/manager.py)
- [base.py](file://harness/memory/base.py)
- [hybrid.py](file://harness/memory/hybrid.py)
- [short_term.py](file://harness/memory/short_term.py)
- [long_term.py](file://harness/memory/long_term.py)
- [base.py](file://harness/agent/base.py)
- [chat.py](file://harness/agent/chat.py)
- [config.py](file://harness/config.py)
- [README.md](file://README.md)
</cite>

## Update Summary
**Changes Made**
- Updated session architecture to support per-session memory isolation with dedicated HybridMemory instances
- Added global shared memory system for cross-session context sharing
- Enhanced SessionManager with search_memories() method for combined global + session memory queries
- Implemented lazy initialization of session-specific memory with isolated storage files
- Updated examples to demonstrate multi-conversation workflows with independent state isolation
- Enhanced persistence system with append-only JSONL format for optimal performance
- Added backward compatibility for legacy single-file session formats

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
This document explains the enhanced session management system designed for multi-conversation support with independent state isolation and global shared memory. The system now supports sophisticated per-session memory isolation where each conversation maintains its own dedicated HybridMemory instance with separate storage files, while also providing a global shared memory layer for cross-session context. It covers the complete lifecycle of sessions, advanced state persistence mechanisms using append-only JSONL format, concurrent conversation handling across multiple independent contexts, and seamless integration between session-specific and global memory systems. The SessionManager class provides comprehensive CRUD operations for creating, managing, and persisting sessions, including configuration options and robust storage backends. Practical examples demonstrate starting new conversations, maintaining context across turns, implementing session recovery after application restarts, and leveraging both isolated and shared memory resources. Security considerations, memory optimization strategies, and scaling approaches for high-concurrency scenarios are thoroughly addressed.

## Project Structure
The session management system has been completely redesigned around a directory-based architecture with enhanced memory isolation capabilities. Each session is stored as an isolated unit with dedicated metadata, message history, and memory storage files, while a global memory file provides shared context across all sessions. The new structure supports concurrent multi-conversation workflows while maintaining complete state isolation between different sessions and enabling cross-session knowledge sharing through the global memory layer.

```mermaid
graph TB
subgraph "Session Storage Layer"
SM["SessionManager"]
GM["Global Memory<br/>global_memory.json"]
SD["Session Directory<br/>.<br/>├── meta.json<br/>├── messages.jsonl<br/>└── memory.json"]
end
subgraph "Context & Memory"
CM["ContextManager"]
HM["HybridMemory"]
STM["ShortTermMemory"]
LTM["LongTermMemory"]
end
subgraph "Agent Integration"
BA["BaseAgent"]
CA["ChatAgent"]
end
SM --> GM
SM --> SD
BA --> CM
CM --> HM
HM --> STM
HM --> LTM
CA --> BA
```

**Diagram sources**
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:41-108](file://harness/context/manager.py#L41-L108)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [short_term.py:16-50](file://harness/memory/short_term.py#L16-L50)
- [long_term.py:24-109](file://harness/memory/long_term.py#L24-L109)
- [base.py:63-96](file://harness/agent/base.py#L63-L96)
- [chat.py:25-59](file://harness/agent/chat.py#L25-L59)

**Section sources**
- [README.md:73-131](file://README.md#L73-L131)

## Core Components
- **Session**: Represents an isolated conversation with its own history, metadata, timestamps, persistent storage, and dedicated HybridMemory instance for long-term knowledge retention. Supports append-only message logging and efficient history retrieval.
- **SessionManager**: Manages multiple independent sessions with directory-based storage, providing comprehensive CRUD operations (create, switch, list, delete, rename), automatic session recovery, and unified memory search across both global and session-specific memory layers.
- **ContextManager**: Assembles prompts from system instructions, tool descriptions, relevant long-term memory, short-term history, and current input with intelligent context filtering and token-aware truncation.
- **Memory System**: HybridMemory composes ShortTermMemory (bounded buffer) and LongTermMemory (persistent TF-IDF retrieval) with duplicate filtering and relevance scoring, supporting both per-session isolation and global sharing.
- **Agent Integration**: BaseAgent and ChatAgent use ContextManager and Memory to run multi-turn conversations with full session isolation at the application level, supporting dynamic memory switching between sessions.

Key responsibilities:
- **Isolation**: Each session maintains completely independent message history, metadata, and memory storage in separate directories with dedicated HybridMemory instances.
- **Persistence**: Sessions use append-only JSONL format for O(1) writes with metadata stored in compact JSON files; memory data persists separately in session-specific JSON files.
- **Global Sharing**: Global memory provides cross-session context sharing while maintaining session isolation for topic-specific knowledge.
- **Concurrency**: In-memory session registry with active session pointer; safe for single-process usage with thread-safe file operations.
- **Recovery**: Automatic loading of all existing sessions from directory structure on startup with backward compatibility for legacy formats.

**Section sources**
- [manager.py:37-77](file://harness/session/manager.py#L37-L77)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:41-108](file://harness/context/manager.py#L41-L108)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [short_term.py:16-50](file://harness/memory/short_term.py#L16-L50)
- [long_term.py:24-109](file://harness/memory/long_term.py#L24-L109)
- [base.py:63-96](file://harness/agent/base.py#L63-L96)
- [chat.py:25-59](file://harness/agent/chat.py#L25-L59)

## Architecture Overview
The enhanced architecture separates concerns with improved scalability and memory isolation:
- **Session layer**: Provides complete isolation for multiple conversations with directory-based persistence, append-only message logging, and dedicated per-session memory storage.
- **Memory layer**: Offers hybrid short-term and long-term storage with sophisticated retrieval strategies, duplicate content filtering, and dual-layer access (global + session-specific).
- **Context layer**: Builds intelligent prompts combining system instructions, tools, memory retrieval from both global and session memory, and conversation history with token-aware filtering.
- **Agent layer**: Orchestrates interactions using the layered architecture with full session isolation, dynamic memory switching, and context management.

```mermaid
sequenceDiagram
participant App as "Application"
participant SM as "SessionManager"
participant S as "Session"
participant BA as "BaseAgent"
participant CM as "ContextManager"
participant GM as "Global Memory"
participant SMem as "Session Memory"
participant LLM as "LLM Engine"
App->>SM : create_session("Title")
SM-->>App : Session(id, title)
App->>S : add_message("user", "Input")
S->>S : Append to messages.jsonl
App->>BA : run(user_input)
BA->>CM : build_messages(history, user_input)
CM->>GM : get_relevant_context(query)
GM-->>CM : global context
CM->>SMem : get_relevant_context(query)
SMem-->>CM : session context
CM-->>BA : full message list
BA->>LLM : generate(messages)
LLM-->>BA : response
BA->>CM : store_assistant_response(content)
BA-->>App : final answer
```

**Diagram sources**
- [manager.py:107-116](file://harness/session/manager.py#L107-L116)
- [manager.py:47-56](file://harness/session/manager.py#L47-L56)
- [base.py:97-160](file://harness/agent/base.py#L97-L160)
- [manager.py:61-108](file://harness/context/manager.py#L61-L108)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)
- [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-L73)

## Detailed Component Analysis

### Session and SessionManager with Enhanced Memory Isolation
- **Session**:
  - Holds id, title, created_at timestamp, messages list, metadata, and dedicated HybridMemory instance with append-only JSONL persistence.
  - Adds messages with role, content, timestamp, and automatically persists to JSONL file via callback mechanism.
  - Provides recent history retrieval with configurable window size and serialization helpers for metadata only.
- **SessionManager**:
  - Initializes storage directory structure with global memory file and loads existing sessions from both new directory format and legacy single-file format.
  - Creates sessions with unique IDs, sets active session, and immediately persists metadata to disk.
  - Switches active session safely with validation; raises descriptive errors if session not found.
  - Lists sessions sorted by creation time; deletes sessions and their entire directory structure including memory files.
  - Renames sessions and updates metadata files atomically.
  - Implements robust session recovery with error handling and logging for corrupted or incomplete data.
  - Provides unified memory search across both global and session-specific memory with deduplication.

```mermaid
classDiagram
class Session {
+string id
+string title
+float created_at
+dict[] messages
+dict metadata
+BaseMemory memory
+add_message(role, content) void
+get_history(n) dict[]
+to_dict() dict
+from_dict(data) Session
}
class SessionManager {
+string storage_dir
-dict~string, Session~ _sessions
-string? _active_session_id
-HybridMemory _global_memory
+create_session(title) Session
+switch_session(session_id) Session
+get_active() Session?
+list_sessions() Session[]
+delete_session(session_id) void
+rename_session(session_id, new_title) void
+get_memory(session_id) BaseMemory
+global_memory HybridMemory
+search_memories(query, session_id, top_k) list[dict]
-_save_meta(session) void
-_load_all() void
-_append_message(session, msg) void
}
SessionManager --> Session : "manages with JSONL persistence"
SessionManager --> HybridMemory : "global memory"
Session --> HybridMemory : "per-session memory"
```

**Diagram sources**
- [manager.py:37-77](file://harness/session/manager.py#L37-L77)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

**Section sources**
- [manager.py:37-77](file://harness/session/manager.py#L37-L77)
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

### Context Assembly and Dual-Layer Memory Retrieval with Multi-Session Support
- **ContextManager.build_messages**:
  - Prepends system prompt and optional tool instructions with dynamic tool discovery.
  - Retrieves relevant context via HybridMemory with intelligent filtering from both global and session memory.
  - Appends short-term history and current user input with token-aware truncation.
  - Stores assistant responses back into memory for future retrieval with role-based categorization.
- **HybridMemory.get_relevant_context**:
  - Combines recent short-term messages with top-K relevant long-term memories.
  - Filters duplicates between recent and relevant sets to avoid redundancy.
  - Formats context with clear section headers for better LLM comprehension.
- **SessionManager.search_memories**:
  - Searches across both global and session-specific memory with unified results.
  - Deduplicates results by content to prevent redundancy.
  - Returns combined results with source attribution ('global' or 'session').

```mermaid
flowchart TD
Start(["Build Messages"]) --> Sys["Assemble System Prompt<br/>+ Tool Instructions"]
Sys --> GlobalMem["Search Global Memory"]
GlobalMem --> SessionMem["Search Session Memory"]
SessionMem --> History["Append Short-Term History"]
History --> Input["Append Current User Input"]
Input --> Store["Store Assistant Response in Memory"]
Store --> End(["Return Message List"])
```

**Diagram sources**
- [manager.py:61-108](file://harness/context/manager.py#L61-L108)
- [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-L73)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

**Section sources**
- [manager.py:41-108](file://harness/context/manager.py#L41-L108)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

### Agent Loop and Multi-Turn Conversations with Dynamic Memory Switching
- **BaseAgent.run**:
  - Builds context via ContextManager with full session isolation and dynamic memory switching.
  - Calls LLM and handles tool calls iteratively until a final answer is reached.
  - Maintains conversation history within session boundaries and stores assistant responses in appropriate memory layer.
  - Provides detailed execution tracing for debugging and monitoring.
- **ChatAgent.chat**:
  - Convenience wrapper around run for interactive chat with session-aware context management.
- **Dynamic Memory Switching**:
  - Agents can switch memory instances at runtime using set_memory() method when sessions change.
  - Enables seamless transition between different conversation contexts while maintaining isolation.

```mermaid
sequenceDiagram
participant U as "User"
participant A as "ChatAgent"
participant B as "BaseAgent"
participant C as "ContextManager"
participant GM as "Global Memory"
participant SMem as "Session Memory"
participant L as "LLM"
U->>A : chat(input)
A->>B : run(input)
B->>C : build_messages(history, input)
C->>GM : get_relevant_context(input)
GM-->>C : global context
C->>SMem : get_relevant_context(input)
SMem-->>C : session context
C-->>B : messages
B->>L : generate(messages)
L-->>B : response
B->>C : store_assistant_response(response.content)
B-->>A : answer
A-->>U : answer
```

**Diagram sources**
- [chat.py:46-59](file://harness/agent/chat.py#L46-L59)
- [base.py:97-160](file://harness/agent/base.py#L97-L160)
- [manager.py:61-108](file://harness/context/manager.py#L61-L108)
- [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-L73)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

**Section sources**
- [chat.py:25-59](file://harness/agent/chat.py#L25-L59)
- [base.py:63-160](file://harness/agent/base.py#L63-L160)

### Enhanced Session Lifecycle with Per-Session Memory Isolation
- **Creation**:
  - New session gets a unique ID, initial empty history, immediate metadata persistence to disk, and lazy-initialized per-session memory.
  - Directory structure is created automatically with proper permissions for messages, metadata, and memory files.
- **Activation**:
  - Active session pointer ensures which session receives messages when accessed via manager methods.
  - Session switching is validated and atomic to prevent race conditions.
- **Message Persistence**:
  - Messages are appended to JSONL files with O(1) write operations for optimal performance.
  - Each message includes timestamp, role, and content with UTF-8 encoding support.
- **Memory Isolation**:
  - Each session gets its own HybridMemory instance with dedicated storage file in session directory.
  - Global memory provides shared context across all sessions while maintaining session isolation.
- **Switching**:
  - Validate existence before switching; update active pointer with error handling.
  - Agents can dynamically switch memory instances using set_memory() method.
- **Deletion**:
  - Remove from in-memory map and delete entire session directory including meta.json, messages.jsonl, and memory.json.
  - Reset active pointer if deleted session was active.
- **Recovery**:
  - On startup, load all directory-based sessions and legacy single-file sessions with comprehensive error handling.
  - Replay JSONL message logs to reconstruct complete session state in memory.

```mermaid
flowchart TD
Init["Initialize SessionManager"] --> Load["Load Existing Sessions<br/>(Directory + Legacy Format)"]
Load --> Create["Create New Session"]
Create --> PersistMeta["Persist meta.json"]
PersistMeta --> Active["Set Active Session"]
Active --> Use["Add Messages / Get History"]
Use --> PersistMsg["Append to messages.jsonl"]
Use --> MemAccess["Access Session Memory<br/>(lazy-initialized)"]
MemAccess --> GlobalMem["Access Global Memory<br/>(shared)"]
GlobalMem --> Search["Combined Memory Search"]
Search --> Switch["Switch Sessions"]
Switch --> Use
Use --> Delete["Delete Session"]
Delete --> Cleanup["Remove Directory & Files<br/>(meta, messages, memory)"]
Cleanup --> Shutdown["Shutdown / Restart"]
Shutdown --> Reload["Reload Sessions on Next Start"]
```

**Diagram sources**
- [manager.py:97-103](file://harness/session/manager.py#L97-L103)
- [manager.py:107-116](file://harness/session/manager.py#L107-L116)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)
- [manager.py:203-218](file://harness/session/manager.py#L203-L218)
- [manager.py:263-303](file://harness/session/manager.py#L263-L303)

**Section sources**
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:118-137](file://harness/session/manager.py#L118-L137)
- [manager.py:139-152](file://harness/session/manager.py#L139-L152)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)
- [manager.py:203-218](file://harness/session/manager.py#L203-L218)
- [manager.py:263-303](file://harness/session/manager.py#L263-L303)

### Practical Examples with Multi-Session Memory Isolation
- **Starting a new conversation**:
  - Create sessions via SessionManager with descriptive titles and add messages to maintain context.
  - Each session operates independently with complete state isolation and dedicated memory storage.
- **Maintaining context across turns**:
  - Use the agent's run method within the active session; ContextManager and HybridMemory ensure relevant past context is included from both global and session memory.
  - Session switching preserves conversation state while allowing topic separation.
- **Recovering after restart**:
  - SessionManager automatically loads existing sessions from directory structure on initialization.
  - Both new directory format and legacy single-file formats are supported for seamless migration.
- **Cross-session knowledge sharing**:
  - Global memory provides shared context across all sessions (user preferences, facts, etc.).
  - Combined search functionality merges results from both global and session-specific memory.

Reference paths:
- Creating sessions and adding messages: [demo_session.py:16-39](file://demos/demo_session.py#L16-L39)
- Building context and storing responses: [manager.py:61-108](file://harness/context/manager.py#L61-L108), [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-L73)
- Loading sessions on startup: [manager.py:263-303](file://harness/session/manager.py#L263-L303)
- Demonstrating memory isolation and global sharing: [demo_memory.py:175-247](file://demos/demo_memory.py#L175-L247)

**Section sources**
- [demo_session.py:11-42](file://demos/demo_session.py#L11-L42)
- [manager.py:61-108](file://harness/context/manager.py#L61-L108)
- [hybrid.py:46-73](file://harness/memory/hybrid.py#L46-L73)
- [manager.py:263-303](file://harness/session/manager.py#L263-L303)
- [demo_memory.py:175-247](file://demos/demo_memory.py#L175-L247)

## Dependency Analysis
- **SessionManager depends on**:
  - Python standard library for filesystem operations, JSON I/O, UUID generation, and logging.
  - Session dataclass for structured data representation and serialization.
  - HybridMemory for both global and per-session memory management.
- **ContextManager depends on**:
  - BaseMemory implementations (HybridMemory, ShortTermMemory, LongTermMemory).
  - ToolRegistry for dynamic tool instruction injection and execution.
- **Agents depend on**:
  - ContextManager and Memory to assemble prompts and manage conversation history.
  - LLM engine for text generation with tool call support.
  - Dynamic memory switching capability for session isolation.

```mermaid
graph LR
SM["SessionManager"] --> S["Session"]
SM --> GM["Global Memory"]
S --> SMem["Session Memory"]
BA["BaseAgent"] --> CM["ContextManager"]
CM --> HM["HybridMemory"]
HM --> STM["ShortTermMemory"]
HM --> LTM["LongTermMemory"]
BA --> LLM["LLM Engine"]
```

**Diagram sources**
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:37-77](file://harness/session/manager.py#L37-L77)
- [manager.py:41-108](file://harness/context/manager.py#L41-L108)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [short_term.py:16-50](file://harness/memory/short_term.py#L16-L50)
- [long_term.py:24-109](file://harness/memory/long_term.py#L24-L109)
- [base.py:63-96](file://harness/agent/base.py#L63-L96)

**Section sources**
- [manager.py:84-152](file://harness/session/manager.py#L84-L152)
- [manager.py:41-108](file://harness/context/manager.py#L41-L108)
- [hybrid.py:22-84](file://harness/memory/hybrid.py#L22-L84)
- [short_term.py:16-50](file://harness/memory/short_term.py#L16-L50)
- [long_term.py:24-109](file://harness/memory/long_term.py#L24-L109)
- [base.py:63-96](file://harness/agent/base.py#L63-L96)

## Performance Considerations
- **Memory Optimization**:
  - ShortTermMemory uses a bounded deque to enforce FIFO eviction, preventing unbounded growth.
  - HybridMemory filters duplicate content between recent and relevant contexts to reduce prompt size.
  - ContextManager estimates token counts to help manage context window constraints efficiently.
  - Per-session memory isolation prevents memory leakage between conversations.
  - Lazy initialization of session memory reduces startup overhead.
- **Storage Efficiency**:
  - SessionManager uses append-only JSONL format for O(1) write operations with minimal overhead.
  - Metadata is stored in compact JSON files with indentation for readability.
  - LongTermMemory persists only user and assistant messages to avoid noise and optimize storage.
  - Separate storage files for global and session memory improve organization and access patterns.
- **Concurrency**:
  - The current design is single-process; in-memory dict and active session pointer are not thread-safe. For high concurrency, consider:
    - Adding locks around session access and persistence operations.
    - Using a database-backed session store for robustness under concurrent writes.
    - Implementing background flushers to batch writes and reduce I/O overhead.
    - Using async I/O for file operations to prevent blocking during high-throughput scenarios.
    - Implementing connection pooling for memory storage backends.

## Troubleshooting Guide
- **Session not found when switching**:
  - Ensure the session ID exists; otherwise, a descriptive ValueError is raised with the missing session ID.
- **Failed to load session on startup**:
  - Errors during loading are logged with specific details; check logs for malformed JSON or permission issues.
  - Legacy format conversion failures are handled gracefully without affecting other sessions.
- **Memory not persisting**:
  - Verify storage paths exist and are writable; JSONL append operations log errors on failure.
  - Check disk space and file permissions for the session directories and memory files.
  - Ensure global memory file has proper write permissions.
- **Context too large**:
  - Adjust max_context_tokens in ContextManager or tune HybridMemory parameters (n_recent, n_relevant).
  - Consider increasing short-term capacity or adjusting similarity thresholds for better relevance.
  - Reduce the number of results returned from combined memory searches.
- **Directory corruption**:
  - Missing meta.json files cause sessions to be skipped during loading.
  - Corrupted JSONL files result in partial session reconstruction with error logging.
  - Corrupted memory files may need manual cleanup or restoration from backups.
- **Memory isolation issues**:
  - Verify that each session has its own memory.json file in its directory.
  - Check that global memory is properly separated from session-specific memory.
  - Ensure agents are using the correct memory instance when switching sessions.

**Section sources**
- [manager.py:186-191](file://harness/session/manager.py#L186-L191)
- [manager.py:263-303](file://harness/session/manager.py#L263-L303)
- [long_term.py:77-105](file://harness/memory/long_term.py#L77-L105)
- [manager.py:49-59](file://harness/context/manager.py#L49-L59)
- [manager.py:154-184](file://harness/session/manager.py#L154-L184)

## Conclusion
The enhanced session management system provides robust isolation for multiple conversations with sophisticated per-session memory isolation and global shared memory capabilities. The directory-based architecture with JSONL message logging and dedicated memory storage offers optimal performance for high-throughput scenarios while maintaining complete state isolation between sessions. The addition of global memory enables cross-session knowledge sharing while preserving session-specific context isolation. Combined with intelligent context assembly and hybrid memory systems, it supports complex multi-turn dialogues that retain relevant knowledge across sessions and topics. For production deployments, the system is ready for scaling with additional concurrency safeguards, database-backed storage backends, and advanced retrieval mechanisms to handle enterprise-level high-concurrency scenarios efficiently.

## Appendices

### Configuration Options
- **LLMConfig**: Backend selection, model name, token limits, temperature control, device specification.
- **MemoryConfig**: Short-term capacity, long-term persistence toggle, storage file path, similarity threshold tuning.
- **HarnessConfig**: Aggregates LLM, memory, and agent configurations with sensible defaults and environment variable support.
- **SessionManager Configuration**: Storage directory path, global memory settings, session-specific memory capacity.

**Section sources**
- [config.py:8-34](file://harness/config.py#L8-L34)
- [config.py:37-44](file://harness/config.py#L37-L44)
- [config.py:55-70](file://harness/config.py#L55-L70)

### Security Considerations
- **Input Validation**:
  - Validate session IDs and titles to prevent injection attacks or path traversal attempts.
  - Sanitize user inputs before storage to prevent malicious content persistence.
- **Filesystem Permissions**:
  - Restrict write access to session storage directories with appropriate OS-level permissions.
  - Implement proper file ownership and access controls for multi-user environments.
  - Secure global memory file to prevent unauthorized cross-session data access.
- **Tool Safety**:
  - Ensure tool execution is sandboxed and audited; validate arguments before execution.
  - Implement rate limiting and resource quotas for tool usage per session.
- **Logging Sensitivity**:
  - Avoid logging sensitive content in session messages or memory items.
  - Implement log rotation and retention policies for compliance requirements.
- **Memory Isolation Security**:
  - Ensure strict separation between global and session-specific memory access.
  - Validate memory search queries to prevent injection attacks.
  - Implement access controls for global memory modifications.

### Scaling Considerations
- **Storage Backend Migration**:
  - Replace JSON file storage with databases (SQLite, PostgreSQL, MongoDB) for concurrent writes and complex queries.
  - Implement sharding strategies for large-scale session management across multiple nodes.
  - Use distributed memory stores for global memory to support multi-instance deployments.
- **Caching Layers**:
  - Introduce Redis or in-memory caching for frequently accessed sessions and memory items.
  - Implement read replicas for session metadata to reduce database load.
  - Cache global memory results to improve cross-session query performance.
- **Asynchronous Operations**:
  - Use async I/O for persistence operations to reduce blocking during high-throughput scenarios.
  - Implement background workers for session cleanup and maintenance tasks.
  - Use asynchronous memory search operations to prevent blocking.
- **Partitioning Strategies**:
  - Partition sessions by user, tenant, or application namespace to limit scope and improve performance.
  - Implement session lifecycle policies with automatic cleanup of inactive sessions.
  - Shard global memory across multiple instances for horizontal scaling.
- **Monitoring and Metrics**:
  - Track session creation rates, message throughput, and storage utilization metrics.
  - Monitor memory usage per session and global memory growth.
  - Implement health checks and alerting for storage capacity and performance degradation.
  - Track combined memory search performance and latency.