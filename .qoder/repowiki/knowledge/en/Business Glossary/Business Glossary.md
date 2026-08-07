---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### Harness
- Definition：The project's own framework layer that wraps an LLM with agent loop, tools, memory, skills, sessions, MCP, and multi-agent orchestration — i.e. the set of "缰绳" (reins) that turn a raw token-in/token-out model into an autonomous task-completing agent.
- Aliases：AI Agent Harness、Harness工程

### Agent Loop
- Definition：The core execution cycle: build context (system prompt + memory + tools + history), call the LLM, detect tool calls, execute them, feed observations back, and repeat until the model produces a final answer rather than another tool request.
- Aliases：agent loop

### Skill
- Definition：A reusable agent capability defined as a Markdown file (`SKILL.md`) with YAML frontmatter (name, description, tags) plus instruction text; loaded at runtime and injected into the prompt so the agent knows how to perform a specific task such as summarization or translation.
- Aliases：SKILL.md、技能

### MCP
- Definition：Model Context Protocol — a JSON-RPC 2.0-based standard for exposing tools, resources, and prompts over a client/server boundary; this project implements both an MCP server and client so agents can discover and call external tool servers.
- Aliases：Model Context Protocol、MCP 协议

### Session
- Definition：An isolated conversation unit that maintains its own message history, metadata (title, creation time), and JSON-backed persistence; multiple sessions can coexist and be switched between via SessionManager.
- Aliases：会话

### Orchestrator
- Definition：A supervisor-style multi-agent coordinator that receives a user request, asks an LLM which specialized agent (e.g. MathAgent, TimeAgent, ChatAgent) is best suited, delegates execution, and returns the result.
- Aliases：多 Agent 编排、Multi-Agent Orchestration

### Hybrid Memory
- Definition：The recommended production memory strategy combining short-term buffer (FIFO window of recent messages) with long-term TF-IDF retrieval (cross-session persistent knowledge); the hybrid layer queries both and merges results into the prompt.
- Aliases：混合记忆
