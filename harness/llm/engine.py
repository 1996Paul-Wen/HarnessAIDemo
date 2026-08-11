"""LLM Engine - Abstract interface and backends for language model inference.

This module implements the core LLM abstraction layer:
- Message / ToolCall / LLMResponse: data types flowing through the system
- ToolCallParser: extracts structured tool calls from free-form model text
- BaseLLM: abstract interface every backend must implement
- TransformersBackend: loads a real model from HuggingFace
- MockBackend: deterministic mock for demos/testing without GPU
- create_llm(): factory that picks the right backend from config
"""
from __future__ import annotations
import json, re, uuid, logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from harness.config import LLMConfig

logger = logging.getLogger(__name__)


# -- Data Types ---------------------------------------------------------------

@dataclass
class Message:
    """A single message in a conversation (system/user/assistant/tool)."""
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class ToolCall:
    """Model request to call a tool."""
    id: str
    name: str
    arguments: dict
    raw_text: str = ""


@dataclass
class LLMResponse:
    """Complete response from the language model."""
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_output: str = ""

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


# -- Tool Call Parser ---------------------------------------------------------

class ToolCallParser:
    """Parse tool calls from LLM text output (handles multiple formats)."""

    @staticmethod
    def parse(text: str) -> list[ToolCall]:
        calls = []
        seen = set()

        # Pattern 1: triple-backtick tool_call blocks
        for m in re.finditer(r"```tool_call\s*\n?(.*?)\n?\s*```", text, re.DOTALL):
            tc = ToolCallParser._try_parse(m.group(1).strip(), m.group(0))
            if tc:
                key = tc.name + str(tc.arguments)
                if key not in seen:
                    calls.append(tc)
                    seen.add(key)

        # Pattern 2: Action: name / Action Input: json
        action_re = re.compile(
            r"Action:\s*([\w_]+)\s*\nAction Input:\s*(\{.*?\})",
            re.DOTALL,
        )
        for m in action_re.finditer(text):
            tc = ToolCallParser._try_parse(
                json.dumps({"name": m.group(1), "arguments": json.loads(m.group(2))}),
                m.group(0),
            )
            if tc:
                key = tc.name + str(tc.arguments)
                if key not in seen:
                    calls.append(tc)
                    seen.add(key)

        # Pattern 3: bare JSON objects with "name" and "arguments" keys
        for m in re.finditer(r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}', text):
            tc = ToolCallParser._try_parse(m.group(0), m.group(0))
            if tc:
                key = tc.name + str(tc.arguments)
                if key not in seen:
                    calls.append(tc)
                    seen.add(key)

        return calls

    @staticmethod
    def _try_parse(json_str: str, raw: str) -> Optional[ToolCall]:
        try:
            data = json.loads(json_str)
            name = data.get("name") or data.get("tool") or ""
            args = data.get("arguments") or data.get("args") or data.get("parameters") or {}
            if isinstance(args, str):
                args = json.loads(args)
            if name and isinstance(args, dict):
                return ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name=name,
                    arguments=args,
                    raw_text=raw,
                )
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        return None


# -- Abstract Base LLM --------------------------------------------------------

class BaseLLM(ABC):
    """Abstract base class for LLM backends.

    All backends must implement generate() which takes a conversation
    (list of Message) and returns a structured LLMResponse.
    This is the fundamental token-in / token-out interface.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate(self, messages: list[Message]) -> LLMResponse:
        """Generate a response given the full conversation context."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return information about the loaded model."""
        ...


# -- Transformers Backend -----------------------------------------------------

class TransformersBackend(BaseLLM):
    """Backend that loads a real model from HuggingFace via transformers.

    This backend:
    1. Downloads and loads a model + tokenizer from HuggingFace Hub
    2. Applies the model's chat template to format messages
    3. Generates tokens autoregressively (uses KV cache internally)
    4. Parses the output text for tool calls

    The chat template is critical: different models (Qwen, Llama, etc.)
    have different prompt formats. The tokenizer.apply_chat_template()
    method handles this automatically.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError:
            raise ImportError(
                "transformers and torch are required for TransformersBackend. "
                "Install with: pip install transformers torch accelerate"
            )

        logger.info(f"Loading model: {self.config.model_name}")
        device = self.config.device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        logger.info(f"Target device is {device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name, trust_remote_code=True,
            local_files_only=True,
        )
        # Load model weights to CPU first, then move to target device.
        # Avoid device_map which can hang with accelerate on MPS.
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            dtype=torch.float32 if device == "cpu" else torch.float16,
            trust_remote_code=True,
            local_files_only=True,
        )
        self.model = self.model.to(device)
        self.model.eval()
        self._device = device
        logger.info(f"Model loaded on {device}")

    def generate(self, messages: list[Message]) -> LLMResponse:
        msg_dicts = [m.to_dict() for m in messages]

        # Apply chat template - this handles model-specific formatting
        text = self.tokenizer.apply_chat_template(
            msg_dicts, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        import torch
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                do_sample=self.config.temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the newly generated tokens
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        raw_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        # Parse tool calls from the raw output
        tool_calls = ToolCallParser.parse(raw_text)
        # Remove tool call blocks from the content
        content = raw_text
        for tc in tool_calls:
            content = content.replace(tc.raw_text, "")
        content = content.strip()

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_output=raw_text,
        )

    def get_model_info(self) -> dict:
        return {
            "backend": "transformers",
            "model": self.config.model_name,
            "device": self._device,
            "max_tokens": self.config.max_new_tokens,
        }


# -- Mock Backend -------------------------------------------------------------

class MockBackend(BaseLLM):
    """Mock LLM backend for testing and demos without GPU.

    This backend uses simple pattern matching to simulate tool calling
    and conversation. It is useful for:
    - Understanding the harness flow without waiting for model inference
    - Running demos on machines without GPU
    - Testing the agent loop and tool system in isolation
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._call_count = 0

    def generate(self, messages: list[Message]) -> LLMResponse:
        self._call_count += 1

        # Find the last user message
        last_user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m.content
                break

        # Check if we have a tool observation (result fed back to us)
        last_tool_msg = None
        for m in reversed(messages):
            if m.role == "tool":
                last_tool_msg = m
                break

        lower = last_user_msg.lower()
        tool_calls = []
        content = ""

        # If input is empty but we have a tool result, synthesize an answer
        if not last_user_msg.strip() and last_tool_msg:
            obs = last_tool_msg.content
            content = f"Based on the tool result: {obs}"
            return LLMResponse(content=content, tool_calls=[], raw_output=content)

        # If the last user message is empty but we have tool results
        if not last_user_msg.strip() and not last_tool_msg:
            content = "How can I help you?"
            return LLMResponse(content=content, tool_calls=[], raw_output=content)

        # Detect date/time BEFORE calculator (since "what is" overlaps)
        if any(w in lower for w in ["date", "today", "what day"]):
            tool_calls.append(ToolCall(
                id=f"mock_{self._call_count}",
                name="datetime",
                arguments={"query": "date"},
                raw_text="get_date()",
            ))
            content = "Let me check the date for you."
        elif any(w in lower for w in ["time", "clock", "what time"]):
            tool_calls.append(ToolCall(
                id=f"mock_{self._call_count}",
                name="datetime",
                arguments={"query": "time"},
                raw_text="get_time()",
            ))
            content = "Let me check the current time."
        elif any(w in lower for w in ["date and time", "datetime"]):
            tool_calls.append(ToolCall(
                id=f"mock_{self._call_count}",
                name="datetime",
                arguments={"query": "datetime"},
                raw_text="get_datetime()",
            ))
            content = "Let me check the date and time."
        elif any(w in lower for w in ["calculate", "compute", "what is", "how much"]):
            expr = self._extract_expression(last_user_msg)
            if expr:
                tool_calls.append(ToolCall(
                    id=f"mock_{self._call_count}",
                    name="calculator",
                    arguments={"expression": expr},
                    raw_text=f"calculate({expr})",
                ))
                content = f"Let me calculate {expr} for you."
        elif any(w in lower for w in ["file", "read", "write", "list"]):
            if "read" in lower:
                path = self._extract_path(last_user_msg) or "example.txt"
                tool_calls.append(ToolCall(
                    id=f"mock_{self._call_count}",
                    name="file_ops",
                    arguments={"operation": "read", "path": path},
                    raw_text=f"read_file({path})",
                ))
                content = f"Let me read that file."
            elif "list" in lower:
                path = self._extract_path(last_user_msg) or "."
                tool_calls.append(ToolCall(
                    id=f"mock_{self._call_count}",
                    name="file_ops",
                    arguments={"operation": "list", "path": path},
                    raw_text=f"list_files({path})",
                ))
                content = "Let me list the files."
        else:
            content = (f"I understand your message: '{last_user_msg[:80]}'. "
                      f"I'm a mock LLM for demos. Try asking me to calculate something, "
                      f"check the time/date, or list files!")

        return LLMResponse(content=content, tool_calls=tool_calls, raw_output=content)

    def _extract_expression(self, text: str) -> Optional[str]:
        import re as _re
        # Try multiple patterns to extract math expressions
        patterns = [
            r'(?:calculate|compute)\s+(?:the\s+result\s+of\s+)?(.+?)[\?\.\!]?$',
            r'(?:what is|how much is)\s+(.+?)[\?\.\!]?$',
        ]
        for pat in patterns:
            m = _re.search(pat, text, _re.I)
            if m:
                expr = m.group(1).strip().rstrip('?!. ')
                # Remove "the result of" prefix
                expr = _re.sub(r'^the\s+result\s+of\s+', '', expr, flags=_re.I)
                # Basic sanitization for safety
                if _re.match(r'^[\d\s\+\-\*\/\(\)\.\%\^]+$', expr):
                    return expr
        # Try to find any math expression in the text
        m = _re.search(r'(\d[\d\s\+\-\*\/\(\)\.\%]+\d)', text)
        if m:
            return m.group(1).strip()
        return "2+2"

    def _extract_path(self, text: str) -> Optional[str]:
        import re as _re
        m = _re.search(r'(?:file|path)\s+[:=]?\s*(\S+)', text, _re.I)
        if m:
            return m.group(1)
        m = _re.search(r'(\S+\.\w{1,5})', text)
        if m:
            return m.group(1)
        return None

    def get_model_info(self) -> dict:
        return {
            "backend": "mock",
            "model": "MockLLM (pattern-matching)",
            "device": "N/A",
            "max_tokens": "N/A",
        }


# -- Factory ------------------------------------------------------------------

def create_llm(config: Optional[LLMConfig] = None) -> BaseLLM:
    """Factory function: create the appropriate LLM backend from config.

    This is the main entry point for creating an LLM engine.
    It reads the config.backend field to decide which implementation to use.
    """
    if config is None:
        config = LLMConfig.from_env()

    if config.backend == "mock":
        logger.info("Using MockBackend (no model download needed)")
        return MockBackend(config)
    elif config.backend == "transformers":
        logger.info(f"Using TransformersBackend with model: {config.model_name}")
        return TransformersBackend(config)
    else:
        raise ValueError(f"Unknown LLM backend: {config.backend}")
