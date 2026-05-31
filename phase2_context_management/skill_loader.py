"""
Phase 2 — Pattern 5: On-Demand Skill Loading
Domain knowledge is stored as text files and injected into context
only when the current task requires it. Keeps the system prompt lean.
"""
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"


def load_skill(skill_name: str) -> str:
    """Load a skill file and return its content."""
    path = SKILLS_DIR / f"{skill_name}.txt"
    if not path.exists():
        available = [p.stem for p in SKILLS_DIR.glob("*.txt")]
        return f"Skill '{skill_name}' not found. Available: {', '.join(available)}"
    return path.read_text().strip()


def list_skills() -> str:
    """Return a catalog of available skills."""
    if not SKILLS_DIR.exists():
        return "No skills directory found."
    skills = sorted(p.stem for p in SKILLS_DIR.glob("*.txt"))
    return "Available skills:\n" + "\n".join(f"  - {s}" for s in skills)


def tool_load_skill(args: dict) -> str:
    """Tool the model calls to inject domain expertise on demand."""
    skill_name = args["skill_name"]
    content    = load_skill(skill_name)
    return f"[SKILL LOADED: {skill_name}]\n\n{content}"


SKILL_TOOL_SCHEMA = {
    "name": "load_skill",
    "description": (
        "Load domain-specific knowledge for the current task. "
        "Call this BEFORE performing any specialised work. "
        f"{list_skills()}"
    ),
    "input_schema": {
        "type": "object",
        "properties": {"skill_name": {"type": "string"}},
        "required": ["skill_name"],
    },
}
