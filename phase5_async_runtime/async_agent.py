"""
Phase 5 — Pattern 18: Parallel Tool Execution with asyncio.gather
All tool calls from a single model response run concurrently.
"""
import asyncio
import os
import sys
import aiofiles
from pathlib import Path
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"


# ── Async tool implementations ────────────────────────────────────────────────

async def async_read_file(args: dict) -> str:
    path = Path(args["path"])
    if not path.exists():
        return f"Error: {path} not found"
    async with aiofiles.open(path, errors="replace") as f:
        content = await f.read()
    lines = content.splitlines()
    start = args.get("start_line", 1) - 1
    end   = args.get("end_line", len(lines))
    return "\n".join(f"{i+start+1}: {l}" for i, l in enumerate(lines[start:end]))


async def async_write_file(args: dict) -> str:
    path = Path(args["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w") as f:
        await f.write(args["content"])
    return f"Written {len(args['content'])} bytes to {path}"


async def async_run_shell(args: dict) -> str:
    proc = await asyncio.create_subprocess_shell(
        args["command"],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = (stdout + stderr).decode().strip()
    return output[:4000] if output else "(no output)"


ASYNC_HANDLERS = {
    "read_file":  async_read_file,
    "write_file": async_write_file,
    "run_shell":  async_run_shell,
}

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read a file with line numbers.",
        "input_schema": {"type": "object", "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
        }, "required": ["path"]},
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {"type": "object", "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        }, "required": ["path", "content"]},
    },
    {
        "name": "run_shell",
        "description": "Execute a shell command.",
        "input_schema": {"type": "object", "properties": {
            "command": {"type": "string"},
        }, "required": ["command"]},
    },
]


# ── Parallel tool execution ───────────────────────────────────────────────────

async def execute_tools_in_parallel(tool_blocks: list) -> list[dict]:
    """Run all tool calls from one model response concurrently."""

    async def run_one(block) -> dict:
        handler = ASYNC_HANDLERS.get(block.name)
        if handler is None:
            result = f"Unknown tool: {block.name}"
        else:
            try:
                result = await handler(block.input)
            except Exception as e:
                result = f"Error in {block.name}: {e}"
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(result),
        }

    return list(await asyncio.gather(*[run_one(b) for b in tool_blocks]))


# ── Async agent loop ──────────────────────────────────────────────────────────

async def run_async_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]

    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=8096,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )

        tool_blocks  = [b for b in response.content if b.type == "tool_use"]
        print(f"  [Async] Running {len(tool_blocks)} tool(s) in parallel...")
        tool_results = await execute_tools_in_parallel(tool_blocks)
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else (
        "Read agent.py and tools.py simultaneously, "
        "then write a brief comparison of their purposes to comparison.txt"
    )
    result = asyncio.run(run_async_agent(task))
    print("Result:", result)
