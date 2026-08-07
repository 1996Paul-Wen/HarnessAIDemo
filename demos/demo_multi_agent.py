#!/usr/bin/env python3
"""Demo: Multi-agent orchestration.

Run with: python demos/demo_multi_agent.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HARNESS_LLM_BACKEND", "mock")

from harness.llm.engine import create_llm
from harness.agent.chat import ChatAgent
from harness.agent.task import TaskAgent
from harness.agent.orchestrator import MultiAgentOrchestrator
from harness.tools.registry import ToolRegistry
from harness.tools.builtin import CalculatorTool, DateTimeTool

def main():
    print("=" * 50)
    print("  Multi-Agent Orchestration Demo")
    print("=" * 50)

    llm = create_llm()
    orch = MultiAgentOrchestrator(llm=llm, verbose=True)

    # Math specialist
    calc_reg = ToolRegistry()
    calc_reg.register(CalculatorTool())
    math_agent = TaskAgent(llm=llm, name="MathAgent", tool_registry=calc_reg)
    orch.register_agent("MathAgent", math_agent, "Math calculations")

    # Time specialist
    time_reg = ToolRegistry()
    time_reg.register(DateTimeTool())
    time_agent = TaskAgent(llm=llm, name="TimeAgent", tool_registry=time_reg)
    orch.register_agent("TimeAgent", time_agent, "Date and time queries")

    # General chat
    chat = ChatAgent(llm=llm, name="ChatAgent")
    orch.register_agent("ChatAgent", chat, "General conversation")

    for task in ["What is 99 * 47?", "What day is today?", "Tell me a joke"]:
        print(f"\n>>> {task}")
        print(orch.run(task))

if __name__ == "__main__":
    main()
