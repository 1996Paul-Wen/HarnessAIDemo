#!/usr/bin/env python3
"""Demo: Single agent with tool-calling.

Run with: python demos/demo_agent.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HARNESS_LLM_BACKEND", "mock")

from harness.llm.engine import create_llm
from harness.agent.task import TaskAgent
from harness.tools.registry import ToolRegistry
from harness.tools.builtin import register_default_tools

def main():
    print("=" * 50)
    print("  Task Agent Demo")
    print("  (Agent with tool-calling loop)")
    print("=" * 50)

    llm = create_llm()
    registry = ToolRegistry()
    register_default_tools(registry)
    agent = TaskAgent(llm=llm, tool_registry=registry)

    tasks = [
        "Calculate (15 + 27) * 3",
        "What is today's date?",
        "What time is it now?",
    ]

    for task in tasks:
        print(f"\n>>> Task: {task}")
        result = agent.execute_task(task)
        print(f"    Answer: {result['result']}")
        agent.history.clear()

if __name__ == "__main__":
    main()
