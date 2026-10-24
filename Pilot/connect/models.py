"""Core enums and the allowed state transitions (PRD: mandatory states S01-S14)."""
from enum import Enum

CURRENT_TRL = 3   # engineering scope: what the code is allowed to build (see CLAUDE.md)
REPORTED_TRL = 1  # level shown to management in the README ladder; raise it when signed off


class Outcome(str, Enum):
    """Every conversation ends in exactly one of these (PRD critical conversation rule)."""

    COMPLETED = "Completed"
    FOLLOW_UP_REQUIRED = "Follow-up Required"
    HUMAN_ESCALATION = "Human Escalation"
    UNRESOLVED = "Unresolved"


class State(str, Enum):
    SCHEDULED = "S01_SCHEDULED"
    CALLING = "S02_CALLING"
    CONNECTED = "S03_CONNECTED"
    COMPLETED = "S04_COMPLETED"
    NO_ANSWER = "S05_NO_ANSWER"
    RETRY_SCHEDULED = "S06_RETRY_SCHEDULED"
    NETWORK_INTERRUPTED = "S07_NETWORK_INTERRUPTED"
    PROCESSING_FAILED = "S08_PROCESSING_FAILED"
    FALLBACK_SENT = "S09_FALLBACK_SENT"
    CLARIFICATION_REQUIRED = "S10_CLARIFICATION_REQUIRED"
    HUMAN_ESCALATION = "S11_HUMAN_ESCALATION"
    AWAITING_HUMAN = "S12_AWAITING_HUMAN"
    RESOLVED = "S13_RESOLVED"
    CLOSED = "S14_CLOSED"


S = State
TRANSITIONS: dict[State, set[State]] = {
    S.SCHEDULED: {S.CALLING},
    S.CALLING: {S.CONNECTED, S.NO_ANSWER, S.NETWORK_INTERRUPTED},
    S.CONNECTED: {
        S.COMPLETED,
        S.CLARIFICATION_REQUIRED,
        S.HUMAN_ESCALATION,
        S.NETWORK_INTERRUPTED,
        S.PROCESSING_FAILED,
    },
    S.CLARIFICATION_REQUIRED: {S.CONNECTED, S.HUMAN_ESCALATION},
    S.NO_ANSWER: {S.RETRY_SCHEDULED, S.FALLBACK_SENT},          # TRL 5
    S.RETRY_SCHEDULED: {S.CALLING},                              # TRL 5
    S.NETWORK_INTERRUPTED: {S.RETRY_SCHEDULED, S.FALLBACK_SENT},  # TRL 5
    S.PROCESSING_FAILED: {S.RETRY_SCHEDULED, S.HUMAN_ESCALATION},  # TRL 5
    S.FALLBACK_SENT: {S.CLOSED},                                 # TRL 5
    S.HUMAN_ESCALATION: {S.AWAITING_HUMAN},
    S.AWAITING_HUMAN: {S.RESOLVED},
    S.RESOLVED: {S.CLOSED},
    S.COMPLETED: {S.CLOSED},
    S.CLOSED: set(),
}


class IllegalTransition(Exception):
    pass
