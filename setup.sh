#!/bin/bash
# =============================================================
# HarnessAIDemo - Environment Setup Script
# =============================================================
# This script sets up the Python virtual environment and
# installs all required dependencies.
# =============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_VERSION="3.11"

echo "============================================"
echo "  HarnessAIDemo - Setup"
echo "============================================"
echo ""

# Find Python 3.11
PYTHON_CMD=""
for cmd in python3.11 python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        if [[ "$version" == "$PYTHON_VERSION" ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3.11 is required but not found."
    echo "  Please install Python 3.11 first, then re-run this script."
    exit 1
fi

echo "[1/3] Found Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/3] Creating virtual environment at $VENV_DIR ..."
    $PYTHON_CMD -m venv "$VENV_DIR"
else
    echo "[2/3] Virtual environment already exists at $VENV_DIR"
fi

# Activate and install dependencies
echo "[3/3] Installing dependencies ..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r "$PROJECT_DIR/requirements.txt" -q
pip install -e "$PROJECT_DIR" -q

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the interactive chat demo:"
echo "  python run.py chat"
echo ""
echo "To run a specific demo:"
echo "  python run.py agent          # Single agent with tools"
echo "  python run.py multi-agent    # Multi-agent orchestration"
echo "  python run.py mcp            # MCP protocol demo"
echo "  python run.py skills         # Skill system demo"
echo "  python run.py session        # Multi-session demo"
echo ""
echo "To use mock LLM (no model download needed):"
echo "  export HARNESS_LLM_BACKEND=mock"
echo "  python run.py chat"
echo ""
