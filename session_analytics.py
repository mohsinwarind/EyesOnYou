# session_analytics.py
import time
from dataclasses import dataclass, field
from event_system import EventSystem, FocusEventType


@dataclass
class SessionSummary:
    session_number:      int
    total_focus_seconds: float
    total_distracted_seconds: float
    distraction_count:   int
    focus_regain_count:  int
    longest_focus_streak_seconds: float
    focus_score:         int       # 0–100


class SessionAnalytics:
    def __init__(self, event_system: EventSystem):
        self.es               = event_system
        self._focus_start     = None
        self._distract_start  = None
        self._streaks: list[float] = []
        self._total_distracted = 0.0

    def on_focus_lost(self):
        if self._focus_start:
            streak = time.time() - self._focus_start
            self._streaks.append(streak)
            self._focus_start = None
        self._distract_start = time.time()

    def on_focus_regained(self):
        if self._distract_start:
            self._total_distracted += time.time() - self._distract_start
            self._distract_start = None
        self._focus_start = time.time()

    def on_session_start(self):
        self._focus_start    = time.time()
        self._distract_start = None
        self._streaks        = []
        self._total_distracted = 0.0

    def build_summary(self, session_number: int, work_seconds: int) -> SessionSummary:
        # Close any open streak
        if self._focus_start:
            self._streaks.append(time.time() - self._focus_start)

        distraction_count = self.es.get_distraction_count(session_number)
        regain_count      = self.es.get_focus_regain_count(session_number)
        total_distracted  = self._total_distracted
        total_focus       = max(0, work_seconds - total_distracted)
        longest_streak    = max(self._streaks) if self._streaks else 0

        # Score: weighted combination
        focus_ratio = total_focus / work_seconds if work_seconds > 0 else 1
        distraction_penalty = min(distraction_count * 3, 30)
        score = int(max(0, min(100, focus_ratio * 100 - distraction_penalty)))

        return SessionSummary(
            session_number=session_number,
            total_focus_seconds=round(total_focus),
            total_distracted_seconds=round(total_distracted),
            distraction_count=distraction_count,
            focus_regain_count=regain_count,
            longest_focus_streak_seconds=round(longest_streak),
            focus_score=score,
        )