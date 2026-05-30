"""
Phase 1 — Pattern 2: Tool Dispatch Map
All tool implementations + schemas in one place.
"""
import subprocess
from pathlib import Path


def tool_run_shell(args: dict) -> str:
    cmd = args["command"]
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=30
    )
    output = (result.stdout + result.stderr).strip()
    return output[:4000] if output else "(no output)"


def tool_read_file(args: dict) -> str:
    path = Path(args["path"])
    if not path.exists():
        return f"Error: {path} does not exist"
    lines = path.read_text(errors="replace").splitlines()
    start = args.get("start_line", 1) - 1
    end   = args.get("end_line", len(lines))
    numbered = [f"{i + start + 1}: {l}" for i, l in enumerate(lines[start:end])]
    return "\n".join(numbered)


def tool_write_file(args: dict) -> str:
    path = Path(args["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args["content"])
    return f"Written {len(args['content'])} bytes to {path}"


def tool_list_directory(args: dict) -> str:
    path = Path(args.get("path", "."))
    if not path.is_dir():
        return f"Error: {path} is not a directory"
    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
    return "\n".join(
        f"{'DIR ' if e.is_dir() else 'FILE'} {e.name}" for e in entries
    )


# ── Dispatch map ─────────────────────────────────────────────────────────────
TOOL_HANDLERS = {
    "run_shell":      tool_run_shell,
    "read_file":      tool_read_file,
    "write_file":     tool_write_file,
    "list_directory": tool_list_directory,
}

# ── Schemas (what the model reads to decide which tool to call) ──────────────
TOOL_SCHEMAS = [
    {
        "name": "run_shell",
        "description": (
            "Execute a shell command and return stdout + stderr. "
            "Use for running tests, installing packages, compiling, or any system operation. "
            "Output capped at 4,000 characters."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read a file and return its content with line numbers. "
            "Use start_line/end_line to read large files in sections."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path":       {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line":   {"type": "integer"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates parent directories automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and subdirectories at a given path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
]
