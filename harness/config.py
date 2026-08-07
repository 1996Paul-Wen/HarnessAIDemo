"""Harness configuration module."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for the LLM backend.
    
    Attributes:
        backend: Which backend to use ('transformers' or 'mock')
        model_name: HuggingFace model identifier
        max_new_tokens: Maximum tokens to generate per response
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        device: Device to run on ('cpu', 'cuda', 'mps', or 'auto')
    """
    backend: str = "transformers"
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
    max_new_tokens: int = 512
    temperature: float = 0.7
    device: str = "auto"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables."""
        return cls(
            backend=os.getenv("HARNESS_LLM_BACKEND", "transformers"),
            model_name=os.getenv("HARNESS_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct"),
            max_new_tokens=int(os.getenv("HARNESS_MAX_TOKENS", "512")),
            temperature=float(os.getenv("HARNESS_TEMPERATURE", "0.7")),
            device=os.getenv("HARNESS_DEVICE", "auto"),
        )


@dataclass
class MemoryConfig:
    """Configuration for the memory system."""
    short_term_capacity: int = 20          # Max messages in short-term buffer
    long_term_enabled: bool = True          # Whether to persist long-term memory
    memory_file: str = "memory_store.json"  # Persistence file path
    similarity_threshold: float = 0.3       # Min similarity for memory retrieval


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str = "Assistant"
    system_prompt: str = "You are a helpful assistant."
    max_iterations: int = 10               # Max tool-call loops per turn
    verbose: bool = True                   # Whether to print thinking/trace info


@dataclass
class HarnessConfig:
    """Top-level configuration for the entire harness."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def default(cls) -> "HarnessConfig":
        """Create a default configuration."""
        return cls(
            llm=LLMConfig.from_env(),
            memory=MemoryConfig(),
            agent=AgentConfig(),
        )
