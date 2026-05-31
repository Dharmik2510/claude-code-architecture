"""
Phase 5 — Pattern 21: MCP Tool Registry
Load tool definitions from Model Context Protocol (MCP) servers and
expose them alongside native tools — no hard-coded integration per server.

MCP spec: https://modelcontextprotocol.io
Claude Code MCP docs: https://docs.anthropic.com/en/docs/claude-code/mcp
"""
import json
from pathlib import Path
from typing import Callable

MCP_CONFIG_DIR = Path(".mcp_servers")


def load_mcp_tool_schemas(server_name: str) -> list[dict]:
    """
    Load pre-registered tool schemas for an MCP server.
    In production, these come from the MCP handshake (tools/list).
    This repo stores example exports as JSON for educational use.
    """
    config = MCP_CONFIG_DIR / f"{server_name}.tools.json"
    if not config.exists():
        return []
    return json.loads(config.read_text())


def merge_tool_sets(
    native_schemas: list[dict],
    native_handlers: dict[str, Callable],
    mcp_server: str,
    mcp_handlers: dict[str, Callable],
) -> tuple[list[dict], dict[str, Callable]]:
    """Combine native tools with tools discovered from an MCP server."""
    mcp_schemas = load_mcp_tool_schemas(mcp_server)
    prefixed_handlers = {
        f"mcp_{mcp_server}_{name}": fn
        for name, fn in mcp_handlers.items()
    }
    prefixed_schemas = [
        {**s, "name": f"mcp_{mcp_server}_{s['name']}"}
        for s in mcp_schemas
    ]
    return (
        native_schemas + prefixed_schemas,
        {**native_handlers, **prefixed_handlers},
    )


def register_example_server() -> None:
    """Write an example MCP tool export for local experimentation."""
    MCP_CONFIG_DIR.mkdir(exist_ok=True)
    example = [{
        "name": "fetch_url",
        "description": "Fetch the text content of a URL (example MCP tool).",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    }]
    (MCP_CONFIG_DIR / "example.tools.json").write_text(
        json.dumps(example, indent=2)
    )


if __name__ == "__main__":
    register_example_server()
    schemas = load_mcp_tool_schemas("example")
    print(f"Loaded {len(schemas)} MCP tool schema(s):")
    for s in schemas:
        print(f"  - {s['name']}: {s['description'][:60]}...")
