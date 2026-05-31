"""
Phase 4 — Pattern 15: YAML-Governed Permissions
Tool calls are checked against a YAML policy before execution.
No Python changes needed when policies change — just edit the YAML.
"""
import re
import yaml
from pathlib import Path

PERMISSION_FILE = Path(__file__).parent / "permissions.yaml"


def load_permissions() -> dict:
    if not PERMISSION_FILE.exists():
        return {"default": "allow", "rules": []}
    return yaml.safe_load(PERMISSION_FILE.read_text())


def check_permission(tool_name: str, tool_args: dict) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).
    Rules evaluated top-to-bottom; first match wins.
    """
    config = load_permissions()
    for rule in config.get("rules", []):
        if rule.get("tool") not in (tool_name, "*"):
            continue
        path = tool_args.get("path") or tool_args.get("command", "")
        if "path_pattern" in rule and not re.search(rule["path_pattern"], path):
            continue
        if "command_pattern" in rule and not re.search(rule["command_pattern"],
                                                        tool_args.get("command", "")):
            continue
        action = rule.get("action", "allow")
        return action == "allow", rule.get("reason", str(rule))

    default = config.get("default", "allow")
    return default == "allow", "Default policy"


def governed_tool_call(
    tool_name: str,
    tool_args: dict,
    tool_handlers: dict,
) -> str:
    """Run a tool call through the permission layer first."""
    allowed, reason = check_permission(tool_name, tool_args)
    if not allowed:
        return f"[PERMISSION DENIED] {reason}"
    handler = tool_handlers.get(tool_name)
    if handler is None:
        return f"Unknown tool: {tool_name}"
    return handler(tool_args)
