#!/usr/bin/env python3
"""Demo: MCP protocol in action.

Run with: python demos/demo_mcp.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.mcp.protocol import create_demo_mcp_server, MCPClient, MCPRequest

def main():
    print("=" * 50)
    print("  MCP Protocol Demo")
    print("=" * 50)

    server = create_demo_mcp_server()
    client = MCPClient()
    client.connect(server)

    print("\n1. Discovered tools:")
    for t in client.list_all_tools():
        print(f"   - {t['name']}: {t['description']}")

    print("\n2. Calling tools:")
    resp = client.call_tool("demo-server", "get_weather", {"city": "Shanghai"})
    print(f"   Weather: {resp.result}")

    resp = client.call_tool("demo-server", "text_stats", {"text": "Hello MCP world!"})
    print(f"   Text stats: {resp.result}")

    print("\n3. JSON-RPC protocol:")
    req = MCPRequest(method="tools/call",
                    params={"name": "get_weather", "arguments": {"city": "Beijing"}})
    print(f"   -> {req.to_json()}")
    resp = server.handle_request(req)
    print(f"   <- {resp.to_json()}")

if __name__ == "__main__":
    main()
