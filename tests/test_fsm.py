"""Pattern 10 — FSM team communication protocol."""
from fsm_protocol import AgentFSM, TaskState


def test_happy_path_reaches_done():
    fsm = AgentFSM("t1")
    assert fsm.transition("assign", "coord")
    assert fsm.transition("submit", "writer")
    assert fsm.transition("start_review", "reviewer")
    assert fsm.transition("approve", "reviewer")
    assert fsm.transition("complete", "coord")
    assert fsm.state == TaskState.DONE


def test_invalid_transition_is_rejected_and_state_unchanged():
    fsm = AgentFSM("t2")
    fsm.transition("assign", "coord")          # -> ASSIGNED
    assert fsm.transition("complete", "coord") is False
    assert fsm.state == TaskState.ASSIGNED


def test_request_changes_loops_back_to_assigned():
    fsm = AgentFSM("t3")
    fsm.transition("assign", "coord")
    fsm.transition("submit", "writer")
    fsm.transition("start_review", "reviewer")
    assert fsm.transition("request_changes", "reviewer")
    assert fsm.state == TaskState.ASSIGNED


def test_valid_next_messages_reflects_state():
    fsm = AgentFSM("t4")
    assert fsm.valid_next_messages() == ["assign"]
    assert fsm.can("assign") and not fsm.can("complete")
