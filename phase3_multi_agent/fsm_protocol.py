"""
Phase 3 — Pattern 10: FSM Team Communication Protocol
Each task moves through defined states. Agents can only send
messages that are valid transitions from the current state.
"""
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


class TaskState(str, Enum):
    CREATED    = "created"
    ASSIGNED   = "assigned"
    SUBMITTED  = "submitted"   # agent submitted work for review
    IN_REVIEW  = "in_review"
    APPROVED   = "approved"
    REJECTED   = "rejected"    # sent back for rework
    DONE       = "done"
    FAILED     = "failed"


# (current_state, message_type) → next_state
VALID_TRANSITIONS: dict[tuple, TaskState] = {
    (TaskState.CREATED,   "assign"):          TaskState.ASSIGNED,
    (TaskState.ASSIGNED,  "submit"):          TaskState.SUBMITTED,
    (TaskState.SUBMITTED, "start_review"):    TaskState.IN_REVIEW,
    (TaskState.IN_REVIEW, "approve"):         TaskState.APPROVED,
    (TaskState.IN_REVIEW, "request_changes"): TaskState.ASSIGNED,   # back to rework
    (TaskState.IN_REVIEW, "reject"):          TaskState.REJECTED,
    (TaskState.APPROVED,  "complete"):        TaskState.DONE,
    (TaskState.ASSIGNED,  "fail"):            TaskState.FAILED,
    (TaskState.IN_REVIEW, "fail"):            TaskState.FAILED,
}


class AgentFSM:
    """
    Finite state machine for a single task's lifecycle.
    Enforces that agents can only send valid messages for the current state.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.state   = TaskState.CREATED
        self.history: list[dict] = []

    def transition(
        self,
        message_type: str,
        from_agent: str,
        payload: Optional[dict] = None,
    ) -> bool:
        """
        Attempt a state transition.
        Returns True on success, False if the transition is invalid.
        """
        key = (self.state, message_type)
        if key not in VALID_TRANSITIONS:
            print(
                f"[FSM] Invalid: '{message_type}' from state '{self.state}' "
                f"(task {self.task_id})"
            )
            return False

        old_state  = self.state
        self.state = VALID_TRANSITIONS[key]

        event = {
            "from_state":   old_state,
            "to_state":     self.state,
            "message_type": message_type,
            "from_agent":   from_agent,
            "payload":      payload or {},
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }
        self.history.append(event)
        print(f"[FSM] {self.task_id}: {old_state} → {self.state} (via '{message_type}' by {from_agent})")
        return True

    def can(self, message_type: str) -> bool:
        """Check if a message type is valid from the current state."""
        return (self.state, message_type) in VALID_TRANSITIONS

    def valid_next_messages(self) -> list[str]:
        """Return all message types valid from the current state."""
        return [msg for (state, msg) in VALID_TRANSITIONS if state == self.state]

    def summary(self) -> str:
        lines = [f"Task {self.task_id} — current state: {self.state}"]
        for event in self.history:
            lines.append(
                f"  {event['timestamp'][:19]}  {event['from_state']} → "
                f"{event['to_state']}  [{event['message_type']} by {event['from_agent']}]"
            )
        return "\n".join(lines)


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fsm = AgentFSM("task-001")

    fsm.transition("assign",          "coordinator", {"assignee": "code-writer-1"})
    fsm.transition("submit",          "code-writer-1", {"branch": "agent/task-001"})
    fsm.transition("start_review",    "reviewer-1")

    # Try an invalid transition
    fsm.transition("complete", "coordinator")   # → prints invalid, state stays IN_REVIEW

    fsm.transition("request_changes", "reviewer-1", {"comment": "Missing error handling"})
    fsm.transition("submit",          "code-writer-1", {"branch": "agent/task-001"})
    fsm.transition("start_review",    "reviewer-1")
    fsm.transition("approve",         "reviewer-1")
    fsm.transition("complete",        "coordinator")

    print("\n" + fsm.summary())
    print(f"\nValid next messages from '{fsm.state}': {fsm.valid_next_messages()}")
