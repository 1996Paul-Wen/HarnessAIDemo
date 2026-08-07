"""ChatAgent - a conversational agent optimized for multi-turn dialogue.

ChatAgent extends BaseAgent with:
- Richer conversation management (history pruning)
- Persona customization
- Streaming-like output (prints as it generates)
- Memory-aware responses (references past conversations)

This is the agent you would use for interactive chat sessions.
"""
from __future__ import annotations
from typing import Optional
from harness.agent.base import BaseAgent
from harness.llm.engine import BaseLLM
from harness.tools.registry import ToolRegistry
from harness.memory.base import BaseMemory


DEFAULT_CHAT_PROMPT = """You are a friendly and knowledgeable AI assistant.
You engage in natural, helpful conversations.
You can reference previous parts of the conversation when relevant.
Be concise but thorough in your responses."""


class ChatAgent(BaseAgent):
    """Conversational agent for multi-turn dialogue."""

    def __init__(
        self,
        llm: BaseLLM,
        system_prompt: str = DEFAULT_CHAT_PROMPT,
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[BaseMemory] = None,
        name: str = "ChatBot",
    ):
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            tool_registry=tool_registry or ToolRegistry(),
            memory=memory,
            max_iterations=5,
            verbose=False,
        )

    def chat(self, user_input: str) -> str:
        """Convenience method for interactive chat."""
        return self.run(user_input)

    def reset_conversation(self) -> None:
        """Clear conversation history but keep long-term memory."""
        self.history.clear()

    def get_conversation_history(self) -> list[dict]:
        """Get conversation history as a list of dicts."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.history
        ]
