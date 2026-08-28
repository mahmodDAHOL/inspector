"""Unit tests for the complaint status state machine (no database needed —
this only exercises the VALID_STATUS_TRANSITIONS table itself)."""
from app.api.v1.complaints import VALID_STATUS_TRANSITIONS


def can_transition(frm: str, to: str) -> bool:
    return to in VALID_STATUS_TRANSITIONS.get(frm, [])


def test_received_can_move_to_investigation_or_closed():
    assert can_transition("received", "under_investigation")
    assert can_transition("received", "closed")


def test_received_cannot_jump_to_escalated_directly():
    # Escalation is a dedicated action (/escalate), not a plain status transition.
    assert not can_transition("received", "escalated")


def test_closed_is_terminal():
    assert VALID_STATUS_TRANSITIONS["closed"] == []
    assert not can_transition("closed", "under_investigation")
    assert not can_transition("closed", "received")


def test_under_investigation_can_return_to_received():
    assert can_transition("under_investigation", "received")


def test_escalated_cannot_go_back_to_received():
    assert not can_transition("escalated", "received")


def test_every_non_terminal_state_can_reach_closed():
    for state, transitions in VALID_STATUS_TRANSITIONS.items():
        if state != "closed":
            assert "closed" in transitions, f"{state} has no path to closed"
