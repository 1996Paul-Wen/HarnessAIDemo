#!/usr/bin/env python3
"""Demo: Interactive chat with tool-calling capabilities.

Run with: python demos/demo_chat.py
(Uses mock backend by default for quick start)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HARNESS_LLM_BACKEND", "mock")

from harness.llm.engine import create_llm
from harness.agent.chat import ChatAgent
from harness.tools.registry import ToolRegistry
from harness.tools.builtin import register_default_tools
from harness.memory.hybrid import HybridMemory

def main():
    print("=" * 50)
    print("  Interactive Chat Demo")
    print("  (with tool-calling support)")
    print("=" * 50)

    llm = create_llm()
    memory = HybridMemory(storage_path=".chat_demo_memory.json")
    registry = ToolRegistry()
    register_default_tools(registry)

    agent = ChatAgent(llm=llm, tool_registry=registry, memory=memory)
    print(f"\nModel: {llm.get_model_info()['model']}")
    print(f"Tools: {[t.name for t in registry.list_tools()]}")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        response = agent.chat(user_input)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()
