"""Context Manager - assembles everything the LLM needs to see.

The ContextManager is one of the most critical components in a harness.
It decides what goes into the prompt for each LLM call:

1. System prompt: base instructions + persona
2. Tool descriptions: what tools are available and how to use them
3. Memory context: relevant past conversations and knowledge
4. Conversation history: recent messages
5. Current user input

Key insight: The LLM has a finite context window. The context
manager must be smart about what to include and what to omit.
This is where token counting and prioritization matter.
"""
from __future__ import annotations
import logging
from typing import Optional
from harness.llm.engine import Message
from harness.memory.base import BaseMemory
from harness.memory.hybrid import HybridMemory
from harness.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# Tool calling instructions injected into system prompt
TOOL_INSTRUCTIONS = """
You can use tools to help answer questions. To call a tool, output:

```tool_call
{"name": "tool_name", "arguments": {"arg1": "value1"}}
```

After calling a tool, wait for the Observation (result). Then provide your final answer.
If you do not need a tool, just respond directly.

Available tools:
"""


class ContextManager:
    """Assembles the full context for each LLM call.

    The context is a list of Message objects that form the complete
    prompt: system message, conversation history, tool descriptions,
    and any relevant memories.
    """

    def __init__(
        self,
        system_prompt: str = "You are a helpful AI assistant.",
        memory: Optional[BaseMemory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_context_tokens: int = 4096,
    ):
        self.base_system_prompt = system_prompt
        self.memory = memory or HybridMemory()
        self.tool_registry = tool_registry
        self.max_context_tokens = max_context_tokens

    def build_messages(
        self,
        history: list[Message],
        current_input: str,
    ) -> list[Message]:
        """Build the complete message list for the LLM.

        This is the core assembly method. It constructs:
        1. System message (prompt + tools + instructions)
        2. Historical messages from memory
        3. Current user message

        The method also stores the user input in memory for future use.
        """
        messages = []

        # 1. Build system prompt with tool info
        system_content = self.base_system_prompt
        if self.tool_registry and len(self.tool_registry) > 0:
            system_content += TOOL_INSTRUCTIONS
            system_content += self.tool_registry.get_tools_description()

        messages.append(Message(role="system", content=system_content))

        # 2. Add relevant memory context (long-term retrieval)
        if isinstance(self.memory, HybridMemory):
            mem_context = self.memory.get_relevant_context(current_input)
            if mem_context:
                messages.append(Message(
                    role="system",
                    content=f"[Relevant past context]\n{mem_context}",
                ))

        # 3. Add conversation history (short-term)
        for msg in history:
            messages.append(msg)

        # 4. Add current user message
        messages.append(Message(role="user", content=current_input))

        # 5. Store in memory
        self.memory.add("user", current_input)

        return messages

    def store_assistant_response(self, content: str) -> None:
        """Store the assistant response in memory for future context."""
        self.memory.add("assistant", content)

    def estimate_tokens(self, messages: list[Message]) -> int:
        """Rough token estimation (~4 chars per token for English).

        In production, use the actual tokenizer for precise counting.
        This approximation is sufficient for context window management.
        """
        total_chars = sum(len(m.content) for m in messages)
        return total_chars // 4
