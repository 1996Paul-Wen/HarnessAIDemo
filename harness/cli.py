"""CLI entry point for the HarnessAIDemo.

Provides both an interactive REPL and command-based access to demos:
- python run.py chat          Interactive multi-turn chat
- python run.py agent         Single agent with tools demo
- python run.py multi-agent   Multi-agent orchestration demo
- python run.py mcp           MCP protocol demonstration
- python run.py skills        Skill system demo
- python run.py memory        Memory system demo
- python run.py session       Multi-session management demo

Environment variables:
- HARNESS_LLM_BACKEND=mock          Use mock LLM (no model download)
- HARNESS_LLM_BACKEND=transformers  Use real model (default)
- HARNESS_MODEL_NAME=<name>         Override model
"""
from __future__ import annotations
import sys, os, logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("harness.cli")


def print_banner():
    print("""
============================================
  HarnessAIDemo - AI Agent Harness Demo
============================================
  Demonstrates: Agent Loop, Context Management,
  Memory, Tools, MCP, Skills, Multi-Agent, Sessions
============================================
""")


def run_chat_demo():
    """Interactive multi-turn chat with the agent."""
    from harness.llm.engine import create_llm
    from harness.agent.chat import ChatAgent
    from harness.tools.registry import ToolRegistry
    from harness.tools.builtin import register_default_tools
    from harness.memory.hybrid import HybridMemory

    print("\n[Chat Demo] Starting interactive chat...")
    print("Type 'quit' or 'exit' to stop.\n")

    llm = create_llm()
    memory = HybridMemory(storage_path=".chat_memory.json")
    registry = ToolRegistry()
    register_default_tools(registry)

    agent = ChatAgent(
        llm=llm,
        tool_registry=registry,
        memory=memory,
    )

    print(f"Model: {llm.get_model_info().get('model', 'unknown')}")
    print(f"Tools: {[t.name for t in registry.list_tools()]}")
    print("-" * 40)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        response = agent.chat(user_input)
        print(f"\nAssistant: {response}")


def run_agent_demo():
    """Single agent with tool-calling demonstration."""
    from harness.llm.engine import create_llm
    from harness.agent.task import TaskAgent
    from harness.tools.registry import ToolRegistry
    from harness.tools.builtin import register_default_tools

    print("\n[Agent Demo] Single agent with tools\n")

    llm = create_llm()
    registry = ToolRegistry()
    register_default_tools(registry)

    agent = TaskAgent(llm=llm, tool_registry=registry, name="HelperAgent")

    tasks = [
        "What is the current date and time?",
        "Calculate the result of (15 + 27) * 3",
        "List the files in the current directory",
    ]

    for task in tasks:
        print(f"\n>>> Task: {task}")
        result = agent.execute_task(task)
        print(f"    Result: {result['result']}")
        agent.history.clear()

    # Interactive mode
    print("\n--- Interactive mode (type 'quit' to stop) ---")
    while True:
        try:
            task = input("\nTask: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if task.lower() in ("quit", "exit", "q"):
            break
        if task:
            result = agent.execute_task(task)
            print(f"Result: {result['result']}")
            agent.history.clear()


def run_multi_agent_demo():
    """Multi-agent orchestration demonstration."""
    from harness.llm.engine import create_llm
    from harness.agent.chat import ChatAgent
    from harness.agent.task import TaskAgent
    from harness.agent.orchestrator import MultiAgentOrchestrator
    from harness.tools.registry import ToolRegistry
    from harness.tools.builtin import CalculatorTool, DateTimeTool, FileOpsTool

    print("\n[Multi-Agent Demo] Orchestrator with specialist agents\n")

    llm = create_llm()
    orchestrator = MultiAgentOrchestrator(llm=llm, verbose=True)

    # Create specialist agents
    calc_registry = ToolRegistry()
    calc_registry.register(CalculatorTool())
    math_agent = TaskAgent(
        llm=llm, name="MathAgent",
        tool_registry=calc_registry, max_iterations=5,
    )
    orchestrator.register_agent(
        "MathAgent", math_agent,
        "Handles mathematical calculations and arithmetic"
    )

    time_registry = ToolRegistry()
    time_registry.register(DateTimeTool())
    time_agent = TaskAgent(
        llm=llm, name="TimeAgent",
        tool_registry=time_registry, max_iterations=5,
    )
    orchestrator.register_agent(
        "TimeAgent", time_agent,
        "Handles date and time queries"
    )

    chat_agent = ChatAgent(llm=llm, name="ChatAgent")
    orchestrator.register_agent(
        "ChatAgent", chat_agent,
        "Handles general conversation and questions"
    )

    # Run demo tasks
    demo_tasks = [
        "What is 42 * 13 + 7?",
        "What day is today?",
        "Tell me about artificial intelligence",
    ]

    for task in demo_tasks:
        print(f"\n>>> User request: {task}")
        result = orchestrator.run(task)
        print(f"    Final answer: {result}")


def run_mcp_demo():
    """MCP protocol demonstration."""
    from harness.mcp.protocol import (
        MCPServer, MCPClient, MCPRequest, create_demo_mcp_server,
    )

    print("\n[MCP Demo] Model Context Protocol\n")

    # 1. Create and start MCP server
    print("--- Step 1: Create MCP Server ---")
    server = create_demo_mcp_server()
    print(f"  Server: {server.name}")

    # 2. Create client and connect
    print("\n--- Step 2: Create Client and Connect ---")
    client = MCPClient()
    client.connect(server)

    # 3. Discover tools
    print("\n--- Step 3: Discover Tools ---")
    tools = client.list_all_tools()
    for t in tools:
        print(f"  Tool: {t['name']} (server: {t['server']}) - {t['description']}")

    # 4. Call tools
    print("\n--- Step 4: Call Tools ---")

    resp = client.call_tool("demo-server", "get_weather", {"city": "Tokyo"})
    print(f"  get_weather(Tokyo): {resp.result}")

    resp = client.call_tool("demo-server", "text_stats",
                           {"text": "Hello world, this is a demo text for MCP."})
    print(f"  text_stats: {resp.result}")

    # 5. Read resources
    print("\n--- Step 5: Read Resources ---")
    req = MCPRequest(method="resources/read", params={"uri": "info://server"})
    resp = server.handle_request(req)
    print(f"  Resource info://server: {resp.result}")

    # 6. Get prompts
    print("\n--- Step 6: Get Prompts ---")
    req = MCPRequest(method="prompts/get", params={"name": "analyze"})
    resp = server.handle_request(req)
    print(f"  Prompt 'analyze': {resp.result}")

    # 7. Show JSON-RPC protocol
    print("\n--- Step 7: JSON-RPC Protocol Example ---")
    req = MCPRequest(method="tools/call",
                    params={"name": "get_weather", "arguments": {"city": "Paris"}})
    print(f"  Request:  {req.to_json()}")
    resp = server.handle_request(req)
    print(f"  Response: {resp.to_json()}")

    # 8. Convert MCP tools to harness tools
    print("\n--- Step 8: MCP Tools as Harness Tools ---")
    harness_tools = client.get_tools_for_registry()
    for t in harness_tools:
        print(f"  Harness tool: {t.name} - {t.description}")
        result = t.execute(city="Berlin") if hasattr(t, 'execute') else None

    print("\n  MCP Demo complete!")


def run_skills_demo():
    """Skill system demonstration."""
    from harness.skill.loader import SkillLoader

    print("\n[Skills Demo] Markdown-defined Agent Skills\n")

    loader = SkillLoader(skills_dir="demos/skills")

    # Discover skills
    print("--- Step 1: Discover Skills ---")
    found = loader.discover()
    print(f"  Found {len(found)} skill(s): {found}")

    # Load all skills
    print("\n--- Step 2: Load Skills ---")
    skills = loader.load_all()
    for name, skill in skills.items():
        print(f"  {skill.to_description()}")

    # Show skill details
    print("\n--- Step 3: Skill Details ---")
    for name, skill in skills.items():
        print(f"\n  Skill: {skill.name}")
        print(f"  Description: {skill.description}")
        print(f"  Tags: {skill.metadata.tags}")
        print(f"  Source: {skill.source_path}")
        print(f"  Instructions preview: {skill.instructions[:150]}...")

    # Demonstrate skill application
    print("\n--- Step 4: Apply Skill to Prompt ---")
    for name, skill in skills.items():
        prompt = skill.apply_to_prompt("Please summarize this article about AI.")
        print(f"\n  [{skill.name}] Generated prompt (first 200 chars):")
        print(f"  {prompt[:200]}...")


def run_memory_demo():
    """Memory system demonstration."""
    from demos.demo_memory import main as memory_main
    memory_main()


def run_session_demo():
    """Multi-session management demonstration."""
    from harness.session.manager import SessionManager

    print("\n[Session Demo] Multi-Session Management\n")

    manager = SessionManager(storage_dir=".demo_sessions")

    # Create sessions
    print("--- Step 1: Create Sessions ---")
    s1 = manager.create_session("Coding Project")
    s2 = manager.create_session("Research Notes")
    s3 = manager.create_session("Daily Journal")
    print(f"  Created: {s1.id} - {s1.title}")
    print(f"  Created: {s2.id} - {s2.title}")
    print(f"  Created: {s3.id} - {s3.title}")

    # Add messages to sessions
    print("\n--- Step 2: Add Messages ---")
    s1.add_message("user", "How do I implement a binary search?")
    s1.add_message("assistant", "Binary search works by repeatedly dividing...")
    s2.add_message("user", "Summarize the latest AI papers")
    s2.add_message("assistant", "Here are the key findings...")

    # List all sessions
    print("\n--- Step 3: List Sessions ---")
    for s in manager.list_sessions():
        active = " (active)" if s.id == manager._active_session_id else ""
        msgs = len(s.messages)
        print(f"  [{s.id}] {s.title} - {msgs} messages{active}")

    # Switch sessions
    print("\n--- Step 4: Switch Sessions ---")
    manager.switch_session(s1.id)
    active = manager.get_active()
    print(f"  Active session: {active.title}")
    print(f"  History: {active.get_history()}")

    # Rename session
    print("\n--- Step 5: Rename Session ---")
    manager.rename_session(s3.id, "Personal Diary")
    print(f"  Renamed {s3.id} to 'Personal Diary'")

    # Cleanup
    print("\n--- Step 6: Cleanup ---")
    manager.delete_session(s3.id)
    print(f"  Deleted session {s3.id}")
    print(f"  Remaining sessions: {len(manager)}")

    print("\n  Session Demo complete!")


def main():
    """Main entry point - parse command and run appropriate demo."""
    print_banner()

    if len(sys.argv) < 2:
        print("Usage: python run.py <demo>")
        print("Available demos: chat, agent, multi-agent, mcp, skills, memory, session")
        print("\nTip: Set HARNESS_LLM_BACKEND=mock to skip model download")
        sys.exit(1)

    demo = sys.argv[1].lower()

    demos = {
        "chat": run_chat_demo,
        "agent": run_agent_demo,
        "multi-agent": run_multi_agent_demo,
        "mcp": run_mcp_demo,
        "skills": run_skills_demo,
        "memory": run_memory_demo,
        "session": run_session_demo,
    }

    if demo not in demos:
        print(f"Unknown demo: {demo}")
        print(f"Available: {', '.join(demos.keys())}")
        sys.exit(1)

    demos[demo]()


if __name__ == "__main__":
    main()
