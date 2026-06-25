# event_system.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FocusEventType(Enum):
    FOCUS_LOST_LEFT      = "focus_lost_left"
    FOCUS_LOST_RIGHT     = "focus_lost_right"
    FOCUS_LOST_DOWN      = "focus_lost_down"
    FOCUS_LOST_UP        = "focus_lost_up"
    PHONE_DETECTED       = "phone_detected"
    LONG_ABSENCE         = "long_absence"
    FOCUS_REGAINED       = "focus_regained"
    SESSION_START        = "session_start"
    SESSION_END          = "session_end"
    BREAK_START          = "break_start"
    BREAK_END            = "break_end"


class HeadDirection(Enum):
    FORWARD  = "forward"
    LEFT     = "left"
    RIGHT    = "right"
    DOWN     = "down"
    UP       = "up"
    ABSENT   = "absent"


@dataclass
class FocusEvent:
    event_type:      FocusEventType
    timestamp:       datetime = field(default_factory=datetime.now)
    head_direction:  Optional[HeadDirection] = None
    phone_detected:  bool = False
    duration_seconds: Optional[float] = None
    session_number:  int = 1
    distraction_count: int = 0
    time_remaining:  int = 0        # seconds left in current Pomodoro
    escalation_level: int = 1       # 1–4


class EventSystem:
    def __init__(self):
        self.events: list[FocusEvent] = []

    def log(self, event: FocusEvent):
        self.events.append(event)

    def get_events_this_session(self, session_number: int) -> list[FocusEvent]:
        return [e for e in self.events if e.session_number == session_number]

    def get_distraction_count(self, session_number: int) -> int:
        distraction_types = {
            FocusEventType.FOCUS_LOST_LEFT,
            FocusEventType.FOCUS_LOST_RIGHT,
            FocusEventType.FOCUS_LOST_DOWN,
            FocusEventType.FOCUS_LOST_UP,
            FocusEventType.PHONE_DETECTED,
            FocusEventType.LONG_ABSENCE,
        }
        return sum(
            1 for e in self.get_events_this_session(session_number)
            if e.event_type in distraction_types
        )

    def get_focus_regain_count(self, session_number: int) -> int:
        return sum(
            1 for e in self.get_events_this_session(session_number)
            if e.event_type == FocusEventType.FOCUS_REGAINED
        )

    def clear(self):
        self.events.clear()