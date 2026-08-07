"""Base Agent with the core Agent Loop implementation.

The Agent Loop is the HEART of the harness. This is the execution
cycle that makes an LLM into an agent:

    while not done:
        1. Build context (system prompt + memory + tools + history)
        2. Call LLM with the context
        3. If LLM wants to call tools:
           a. Execute each tool
           b. Feed results back to LLM
           c. Go to step 2 (loop continues)
        4. If LLM gives a final answer:
           a. Store in memory
           b. Return to user
           c. Exit loop

This loop is what enables the agent to:
- Think step by step
- Use tools to gather information
- Make multi-step decisions
- Self-correct when tools fail

The max_iterations parameter prevents infinite loops.
"""
from __future__ import annotations
import logging
from typing import Optional
from harness.llm.engine import BaseLLM, Message, LLMResponse
from harness.tools.registry import ToolRegistry
from harness.memory.base import BaseMemory
from harness.memory.hybrid import HybridMemory
from harness.context.manager import ContextManager

logger = logging.getLogger(__name__)


class AgentTrace:
    """Records the execution trace of an agent loop for debugging."""

    def __init__(self):
        self.steps: list[dict] = []

    def add_step(self, step_type: str, data: dict) -> None:
        self.steps.append({"type": step_type, **data})

    def summary(self) -> str:
        lines = []
        for s in self.steps:
            t = s["type"]
            if t == "llm_call":
                lines.append(f"  [LLM Call] iteration {s.get('iteration', '?')}")
            elif t == "tool_call":
                lines.append(f"  [Tool Call] {s['name']}({s.get('args', {})})")
            elif t == "tool_result":
                out = s.get("output", "")[:80]
                lines.append(f"  [Tool Result] {out}")
            elif t == "final_answer":
                lines.append(f"  [Answer] {s.get('content', '')[:80]}")
        return "\n".join(lines)


class BaseAgent:
    """Base agent with the core agent loop.

    Subclass this to create specialized agents (ChatAgent, TaskAgent, etc).
    The key customization points are:
    - system_prompt: what instructions the agent receives
    - tool_registry: what tools the agent can use
    - max_iterations: how many tool-call loops are allowed
    """

    def __init__(
        self,
        name: str = "Agent",
        llm: Optional[BaseLLM] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory = memory or HybridMemory()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.history: list[Message] = []
        self.context_manager = ContextManager(
            system_prompt=system_prompt,
            memory=self.memory,
            tool_registry=self.tool_registry,
        )

    def run(self, user_input: str) -> str:
        """Execute the agent loop for one user turn.

        This is the main entry point. It runs the full cycle:
        build context -> call LLM -> (maybe) execute tools -> repeat -> answer.
        """
        trace = AgentTrace()

        for iteration in range(self.max_iterations):
            # Step 1: Build context with all info the LLM needs
            messages = self.context_manager.build_messages(
                history=self.history,
                current_input=user_input,
            )
            trace.add_step("llm_call", {"iteration": iteration + 1})

            # Step 2: Call the LLM
            response = self.llm.generate(messages)

            if self.verbose:
                logger.info(f"[{self.name}] LLM raw output: {response.raw_output[:200]}")

            # Step 3: Check if model wants to call tools
            if not response.has_tool_calls:
                # No tool calls - this is the final answer
                self.history.append(Message(role="assistant", content=response.content))
                self.context_manager.store_assistant_response(response.content)
                trace.add_step("final_answer", {"content": response.content})
                return response.content

            # Step 4: Execute tool calls and feed results back
            # Store assistant message with tool call intent
            if response.content:
                self.history.append(Message(role="assistant", content=response.content))

            for tc in response.tool_calls:
                trace.add_step("tool_call", {"name": tc.name, "args": tc.arguments})

                if self.verbose:
                    print(f"  [{self.name}] Calling tool: {tc.name}({tc.arguments})")

                result = self.tool_registry.execute(tc.name, tc.arguments)
                output = result.output if result.success else f"Error: {result.error}"

                trace.add_step("tool_result", {"name": tc.name, "output": output})

                if self.verbose:
                    print(f"  [{self.name}] Tool result: {output[:100]}")

                # Feed tool result back as a message
                self.history.append(Message(
                    role="tool",
                    content=f"Observation ({tc.name}): {output}",
                    name=tc.name,
                    tool_call_id=tc.id,
                ))

            # Continue the loop - LLM will see tool results and decide next step
            user_input = ""  # Subsequent iterations use empty input

        # Max iterations reached
        fallback = "I apologize, but I was unable to complete the task within the allowed steps."
        self.history.append(Message(role="assistant", content=fallback))
        return fallback

    def get_trace_summary(self) -> str:
        """Get a human-readable summary of the last execution trace."""
        return "Agent trace available via the trace attribute."
