"""Skill loader - discovers and loads skills from the filesystem.

The SkillLoader scans directories for skill definitions (SKILL.md files),
parses their metadata, and makes them available to the agent.

SKILL.md format:
    ---
    name: My Skill
    description: What this skill does
    tags: [tag1, tag2]
    version: 1.0
    ---

    # Skill Instructions

    Here are the detailed instructions for the skill...
"""
from __future__ import annotations
import os, re, logging
from pathlib import Path
from harness.skill.base import Skill, SkillMetadata

logger = logging.getLogger(__name__)


class SkillLoader:
    """Discovers and loads skills from a directory."""

    def __init__(self, skills_dir: str = "demos/skills"):
        self.skills_dir = skills_dir
        self._skills: dict[str, Skill] = {}

    def discover(self) -> list[str]:
        """Scan the skills directory and return names of found skills."""
        found = []
        if not os.path.isdir(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return found
        for entry in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_path):
                found.append(entry)
        return found

    def load(self, skill_name: str) -> Skill:
        """Load a specific skill by name."""
        skill_path = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if not os.path.isfile(skill_path):
            raise FileNotFoundError(f"Skill not found: {skill_name}")

        with open(skill_path, "r") as f:
            content = f.read()

        metadata, instructions = self._parse_skill_md(content)
        skill = Skill(
            metadata=metadata,
            instructions=instructions,
            source_path=skill_path,
        )
        self._skills[skill_name] = skill
        logger.info(f"Loaded skill: {skill_name}")
        return skill

    def load_all(self) -> dict[str, Skill]:
        """Discover and load all skills."""
        for name in self.discover():
            try:
                self.load(name)
            except Exception as e:
                logger.error(f"Failed to load skill {name}: {e}")
        return dict(self._skills)

    def get(self, name: str) -> Skill:
        if name not in self._skills:
            self.load(name)
        return self._skills[name]

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    @staticmethod
    def _parse_skill_md(content: str) -> tuple[SkillMetadata, str]:
        """Parse a SKILL.md file into metadata and instructions.

        Expected format:
            ---
            name: ...
            description: ...
            tags: [a, b]
            ---
            # Instructions
            ...
        """
        metadata = SkillMetadata()
        instructions = content

        # Extract YAML frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(1)
            instructions = fm_match.group(2).strip()

            for line in frontmatter.split("\n"):
                line = line.strip()
                if line.startswith("name:"):
                    metadata.name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    metadata.description = line.split(":", 1)[1].strip()
                elif line.startswith("version:"):
                    metadata.version = line.split(":", 1)[1].strip()
                elif line.startswith("tags:"):
                    tags_str = line.split(":", 1)[1].strip()
                    tags = re.findall(r"[\w_]+", tags_str)
                    metadata.tags = tags

        if not metadata.name:
            # Fallback: use first heading
            h_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            metadata.name = h_match.group(1) if h_match else "Unknown Skill"

        return metadata, instructions
