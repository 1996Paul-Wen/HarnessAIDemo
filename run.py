#!/usr/bin/env python3
"""
HarnessAIDemo - Main Entry Point
=================================
Usage:
    python run.py chat            # Interactive chat (multi-turn conversation)
    python run.py agent           # Single agent with tool calling
    python run.py multi-agent     # Multi-agent orchestration
    python run.py mcp             # MCP protocol demonstration
    python run.py skills          # Skill system demonstration
    python run.py session         # Multi-session management demo

Environment:
    HARNESS_LLM_BACKEND=mock      # Use mock LLM (no model download)
    HARNESS_LLM_BACKEND=transformers  # Use real local model (default)
    HARNESS_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct  # Model to use
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harness.cli import main

if __name__ == "__main__":
    main()
