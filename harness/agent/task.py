"""TaskAgent - an agent specialized in completing specific tasks.

TaskAgent extends BaseAgent with:
- Task-specific system prompts
- More aggressive tool usage (higher max_iterations)
- Structured output handling
- Progress tracking

Use TaskAgent when you need the agent to:
- Complete a specific objective (not just chat)
- Use multiple tools in sequence
- Handle complex multi-step workflows
"""
from __future__ import annotations
from typing import Optional
from harness.agent.base import BaseAgent, AgentTrace
from harness.llm.engine import BaseLLM, Message
from harness.tools.registry import ToolRegistry
from harness.memory.base import BaseMemory


TASK_SYSTEM_PROMPT = """You are a task-oriented AI agent. Your goal is to complete
the given task step by step using the available tools.

Rules:
1. Break the task into steps
2. Use tools when needed to gather information
3. Think before acting
4. Provide a clear final answer when the task is complete"""


class TaskAgent(BaseAgent):
    """Agent specialized for completing specific tasks with tools."""

    def __init__(
        self,
        llm: BaseLLM,
        name: str = "TaskAgent",
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 15,
        verbose: bool = True,
    ):
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=TASK_SYSTEM_PROMPT,
            tool_registry=tool_registry or ToolRegistry(),
            memory=memory,
            max_iterations=max_iterations,
            verbose=verbose,
        )

    def execute_task(self, task_description: str) -> dict:
        """Execute a task and return structured result.

        Returns:
            dict with keys: success, result, trace
        """
        print(f"\n[{self.name}] Starting task: {task_description}")
        print("-" * 50)

        result = self.run(task_description)

        print("-" * 50)
        print(f"[{self.name}] Task complete.\n")

        return {
            "success": True,
            "result": result,
            "task": task_description,
        }
