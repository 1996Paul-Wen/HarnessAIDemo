"""Multi-Agent Orchestrator - coordinates multiple agents.

The orchestrator implements the "supervisor" pattern:
1. A supervisor agent receives the user's request
2. It decides which specialist agent(s) to delegate to
3. Specialist agents complete their sub-tasks
4. The supervisor combines results into a final answer

Architecture:
    User --> Orchestrator (Supervisor)
                |
                +--> ResearchAgent  (gathers information)
                +--> AnalysisAgent  (processes data)
                +--> WriterAgent    (generates output)

This pattern enables:
- Separation of concerns (each agent has focused tools/prompt)
- Parallel execution (agents can work independently)
- Better results (specialists outperform generalists)
"""
from __future__ import annotations
import logging
from typing import Optional
from harness.llm.engine import BaseLLM, Message
from harness.agent.base import BaseAgent
from harness.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Coordinates multiple agents to complete complex tasks.

    The orchestrator maintains a pool of specialist agents and
    routes tasks to the appropriate ones. It acts as both:
    - Task router: decides which agent handles what
    - Result aggregator: combines outputs into a coherent response
    """

    def __init__(self, llm: BaseLLM, verbose: bool = True):
        self.llm = llm
        self.verbose = verbose
        self._agents: dict[str, BaseAgent] = {}
        self._supervisor_prompt = """You are a task coordinator. Given a user request,
decide which specialist to delegate to. Respond with ONLY the agent name.

Available agents:
{agents}

User request: {request}

Which agent should handle this? Reply with just the agent name."""

    def register_agent(self, name: str, agent: BaseAgent, description: str = "") -> None:
        """Register a specialist agent with the orchestrator."""
        agent._orchestrator_description = description
        self._agents[name] = agent
        if self.verbose:
            print(f"  [Orchestrator] Registered agent: {name} - {description}")

    def run(self, user_request: str) -> str:
        """Process a user request by delegating to the best agent(s).

        Steps:
        1. Determine which agent is best suited
        2. Delegate the task
        3. Return the result
        """
        if not self._agents:
            return "No agents registered."

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"  Orchestrator received: {user_request}")
            print(f"  Available agents: {list(self._agents.keys())}")
            print(f"{'='*60}")

        # Step 1: Route to the best agent
        chosen = self._select_agent(user_request)
        if self.verbose:
            print(f"\n  [Orchestrator] Delegating to: {chosen}")

        # Step 2: Execute with chosen agent
        agent = self._agents[chosen]
        result = agent.run(user_request)

        if self.verbose:
            print(f"\n  [Orchestrator] Task completed by {chosen}")
            print(f"{'='*60}\n")

        return result

    def run_with_all(self, user_request: str) -> dict[str, str]:
        """Run the request through ALL agents and collect results.

        Useful for tasks that benefit from multiple perspectives.
        """
        results = {}
        for name, agent in self._agents.items():
            if self.verbose:
                print(f"\n  [{name}] Processing...")
            results[name] = agent.run(user_request)
        return results

    def _select_agent(self, request: str) -> str:
        """Use the LLM to select the best agent for the request.

        Falls back to keyword-based matching if LLM routing fails.
        """
        # First try LLM-based routing
        agents_desc = "\n".join(
            f"- {name}: {getattr(a, '_orchestrator_description', 'General agent')}"
            for name, a in self._agents.items()
        )
        prompt = self._supervisor_prompt.format(agents=agents_desc, request=request)
        messages = [Message(role="system", content=prompt)]
        response = self.llm.generate(messages)

        # Try to match the response to an agent name
        for name in self._agents:
            if name.lower() in response.content.lower():
                return name

        # Fallback: keyword-based routing using agent descriptions
        lower_req = request.lower()
        for name, agent in self._agents.items():
            desc = getattr(agent, '_orchestrator_description', '').lower()
            # Check if request keywords match agent description keywords
            desc_words = set(desc.split())
            req_words = set(lower_req.split())
            # Keywords that indicate math/calculator
            if any(w in lower_req for w in ['calculate', 'math', '*', '+', '-', 'compute']) \
               and any(w in desc for w in ['math', 'calcul', 'arithm']):
                return name
            # Keywords that indicate time/date
            if any(w in lower_req for w in ['time', 'date', 'day', 'today', 'clock']) \
               and any(w in desc for w in ['time', 'date']):
                return name
            # Keywords for general chat
            if any(w in lower_req for w in ['tell', 'about', 'explain', 'describe', 'joke']) \
               and any(w in desc for w in ['general', 'conversation', 'chat']):
                return name

        # Default to first agent
        return next(iter(self._agents))

    def list_agents(self) -> list[dict]:
        return [
            {"name": n, "description": getattr(a, "_orchestrator_description", "")}
            for n, a in self._agents.items()
        ]
