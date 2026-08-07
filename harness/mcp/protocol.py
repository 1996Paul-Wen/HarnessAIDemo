"""MCP (Model Context Protocol) - a simplified implementation.

MCP is a protocol that standardizes how AI models interact with
external tools and data sources. It defines:

1. Tools: Functions the model can call (like our tool system)
2. Resources: Data sources the model can read (files, APIs, etc)
3. Prompts: Reusable prompt templates

Architecture:
  Client (Agent) <--JSON-RPC--> Server (Tool Provider)

This demo implements a lightweight in-process MCP that demonstrates
the protocol concepts without requiring network sockets.
In production, MCP servers run as separate processes and communicate
over stdio or HTTP using JSON-RPC 2.0.

Why MCP matters:
- Before MCP: each AI app implements its own tool integration
- With MCP: tools are standardized and reusable across apps
- Analogy: MCP is like USB for AI tools - a universal connector
"""
from __future__ import annotations
import json, logging, uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPToolDef:
    """Definition of a tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    handler: Optional[Callable] = None


@dataclass
class MCPRequest:
    """JSON-RPC style request."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    method: str = ""
    params: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": self.id,
                          "method": self.method, "params": self.params})


@dataclass
class MCPResponse:
    """JSON-RPC style response."""
    id: str = ""
    result: Any = None
    error: Optional[str] = None

    def to_json(self) -> str:
        d = {"jsonrpc": "2.0", "id": self.id}
        if self.error:
            d["error"] = {"message": self.error}
        else:
            d["result"] = self.result
        return json.dumps(d)


class MCPServer:
    """In-process MCP server that exposes tools and resources.

    An MCP server provides:
    - Tools: callable functions with defined schemas
    - Resources: readable data sources
    - Prompts: reusable prompt templates

    This implementation is in-process for demo simplicity.
    A real MCP server would run as a separate process.
    """

    def __init__(self, name: str):
        self.name = name
        self._tools: dict[str, MCPToolDef] = {}
        self._resources: dict[str, Callable] = {}
        self._prompts: dict[str, str] = {}

    def register_tool(self, name: str, description: str,
                      input_schema: dict, handler: Callable) -> None:
        self._tools[name] = MCPToolDef(
            name=name, description=description,
            input_schema=input_schema, handler=handler,
        )
        logger.debug(f"[MCP:{self.name}] Registered tool: {name}")

    def register_resource(self, uri: str, reader: Callable) -> None:
        self._resources[uri] = reader

    def register_prompt(self, name: str, template: str) -> None:
        self._prompts[name] = template

    def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Route a JSON-RPC request to the appropriate handler."""
        method = request.method
        try:
            if method == "tools/list":
                tools = [
                    {"name": t.name, "description": t.description,
                     "inputSchema": t.input_schema}
                    for t in self._tools.values()
                ]
                return MCPResponse(id=request.id, result={"tools": tools})

            elif method == "tools/call":
                tool_name = request.params.get("name", "")
                args = request.params.get("arguments", {})
                tool = self._tools.get(tool_name)
                if not tool:
                    return MCPResponse(id=request.id, error=f"Tool not found: {tool_name}")
                result = tool.handler(**args)
                return MCPResponse(id=request.id, result={"content": str(result)})

            elif method == "resources/read":
                uri = request.params.get("uri", "")
                reader = self._resources.get(uri)
                if not reader:
                    return MCPResponse(id=request.id, error=f"Resource not found: {uri}")
                return MCPResponse(id=request.id, result={"content": reader()})

            elif method == "prompts/get":
                name = request.params.get("name", "")
                template = self._prompts.get(name)
                if not template:
                    return MCPResponse(id=request.id, error=f"Prompt not found: {name}")
                return MCPResponse(id=request.id, result={"template": template})

            else:
                return MCPResponse(id=request.id, error=f"Unknown method: {method}")
        except Exception as e:
            return MCPResponse(id=request.id, error=str(e))


class MCPClient:
    """Client that connects to MCP servers and invokes their tools.

    The agent uses MCPClient to:
    1. Discover available tools across all connected servers
    2. Call tools on specific servers
    3. Read resources

    This demonstrates how the harness manages multiple tool providers.
    """

    def __init__(self):
        self._servers: dict[str, MCPServer] = {}

    def connect(self, server: MCPServer) -> None:
        self._servers[server.name] = server
        logger.info(f"Connected to MCP server: {server.name}")

    def disconnect(self, server_name: str) -> None:
        self._servers.pop(server_name, None)

    def list_all_tools(self) -> list[dict]:
        """Discover all tools across all connected servers."""
        all_tools = []
        for server in self._servers.values():
            req = MCPRequest(method="tools/list")
            resp = server.handle_request(req)
            if resp.result and "tools" in resp.result:
                for t in resp.result["tools"]:
                    t["server"] = server.name
                    all_tools.append(t)
        return all_tools

    def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> MCPResponse:
        """Call a specific tool on a specific server."""
        server = self._servers.get(server_name)
        if not server:
            return MCPResponse(error=f"Server not found: {server_name}")
        req = MCPRequest(
            method="tools/call",
            params={"name": tool_name, "arguments": arguments},
        )
        return server.handle_request(req)

    def get_tools_for_registry(self):
        """Convert MCP tools into harness Tool objects for the ToolRegistry."""
        from harness.tools.base import BaseTool, ToolResult
        tools = []
        for tool_info in self.list_all_tools():
            server_name = tool_info["server"]
            tool_name = tool_info["name"]

            class MCPTool(BaseTool):
                name = tool_name
                description = f"[MCP:{server_name}] {tool_info.get('description', '')}"
                parameters = tool_info.get("inputSchema", {})

                def __init__(self, client, srv_name, t_name):
                    self._client = client
                    self._server_name = srv_name
                    self._tool_name = t_name

                def execute(self, **kwargs):
                    resp = self._client.call_tool(self._server_name, self._tool_name, kwargs)
                    if resp.error:
                        return ToolResult(False, "", resp.error)
                    return ToolResult(True, str(resp.result.get("content", "")))

            tools.append(MCPTool(self, server_name, tool_name))
        return tools


def create_demo_mcp_server() -> MCPServer:
    """Create a demo MCP server with sample tools and resources."""
    import datetime
    server = MCPServer("demo-server")

    # Tool: weather simulation
    server.register_tool(
        name="get_weather",
        description="Get simulated weather for a city",
        input_schema={"city": "string - city name"},
        handler=lambda city="Unknown": f"Weather in {city}: 22C, Partly Cloudy, Humidity 65%",
    )

    # Tool: text stats
    server.register_tool(
        name="text_stats",
        description="Get statistics about a text",
        input_schema={"text": "string - text to analyze"},
        handler=lambda text="": {
            "char_count": len(text),
            "word_count": len(text.split()),
            "line_count": text.count("\n") + 1,
        },
    )

    # Resource: server info
    server.register_resource(
        "info://server",
        lambda: "Demo MCP Server v1.0 - Provides weather and text tools",
    )

    # Prompt: analysis template
    server.register_prompt(
        "analyze",
        "Please analyze the following text and provide insights:\n\n{text}",
    )

    return server
