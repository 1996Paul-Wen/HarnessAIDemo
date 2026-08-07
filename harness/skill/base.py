"""Skill system - reusable, markdown-defined agent capabilities.

A Skill is a self-contained capability that can be loaded and used
by an agent. Skills are defined as directories containing:

1. SKILL.md: Markdown file with metadata and instructions
   - Name, description, tags
   - The prompt/instructions for the skill
   - Example usage

2. Optional assets: supporting files the skill might need

Key insight: Skills make agent capabilities modular and reusable.
Instead of hardcoding every behavior into the agent, skills can be
added, removed, and shared independently.

Analogy: If the agent is a person, skills are like training
certifications - each one adds a specific capability.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillMetadata:
    """Metadata extracted from a skill definition."""
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    version: str = "1.0"


class Skill:
    """A loaded skill with its metadata and instructions."""

    def __init__(
        self,
        metadata: SkillMetadata,
        instructions: str,
        source_path: str = "",
    ):
        self.metadata = metadata
        self.instructions = instructions
        self.source_path = source_path

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description

    def apply_to_prompt(self, user_input: str) -> str:
        """Generate the full prompt by combining skill instructions with user input.

        The skill instructions act as a specialized system prompt that
        guides the agent behavior for this particular skill.
        """
        return f"""{self.instructions}

---
User request: {user_input}
"""

    def to_description(self) -> str:
        tags_str = ", ".join(self.metadata.tags) if self.metadata.tags else "none"
        return f"[{self.name}] {self.description} (tags: {tags_str})"
