# pomodoro.py
import time
from enum import Enum
from dataclasses import dataclass, field


class PomodoroState(Enum):
    IDLE       = "idle"
    WORK       = "work"
    BREAK      = "break"
    LONG_BREAK = "long_break"
    COMPLETE   = "complete"


@dataclass
class PomodoroConfig:
    work_minutes:       int = 25
    break_minutes:      int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4


class PomodoroTimer:
    def __init__(self, config: PomodoroConfig = None):
        self.config        = config or PomodoroConfig()
        self.state         = PomodoroState.IDLE
        self.session_count = 0
        self.start_time    = None
        self.pause_time    = None
        self.elapsed_pause = 0.0
        self._duration     = 0

    # ── controls ──────────────────────────────────────────────
    def start(self):
        self.state         = PomodoroState.WORK
        self.session_count = 1
        self._duration     = self.config.work_minutes * 60
        self.start_time    = time.time()
        self.elapsed_pause = 0.0

    def next_phase(self):
        """Call when the current phase timer hits zero."""
        if self.state == PomodoroState.WORK:
            self.session_count += 1
            if (self.session_count - 1) % self.config.sessions_before_long_break == 0:
                self.state     = PomodoroState.LONG_BREAK
                self._duration = self.config.long_break_minutes * 60
            else:
                self.state     = PomodoroState.BREAK
                self._duration = self.config.break_minutes * 60

        elif self.state in (PomodoroState.BREAK, PomodoroState.LONG_BREAK):
            self.state     = PomodoroState.WORK
            self._duration = self.config.work_minutes * 60

        self.start_time    = time.time()
        self.elapsed_pause = 0.0

    def pause(self):
        if self.start_time and self.pause_time is None:
            self.pause_time = time.time()

    def resume(self):
        if self.pause_time:
            self.elapsed_pause += time.time() - self.pause_time
            self.pause_time = None

    def reset(self):
        self.__init__(self.config)

    # ── queries ───────────────────────────────────────────────
    @property
    def is_running(self) -> bool:
        return self.state in (PomodoroState.WORK, PomodoroState.BREAK, PomodoroState.LONG_BREAK) and self.pause_time is None

    @property
    def remaining_seconds(self) -> int:
        if self.start_time is None:
            return self._duration
        elapsed = (self.pause_time or time.time()) - self.start_time - self.elapsed_pause
        return max(0, int(self._duration - elapsed))

    @property
    def progress(self) -> float:
        """0.0 → 1.0"""
        if self._duration == 0:
            return 0.0
        return 1.0 - (self.remaining_seconds / self._duration)

    def formatted_time(self) -> str:
        s = self.remaining_seconds
        return f"{s // 60:02d}:{s % 60:02d}"

    def phase_label(self) -> str:
        labels = {
            PomodoroState.IDLE:       "Ready",
            PomodoroState.WORK:       "Focus",
            PomodoroState.BREAK:      "Break",
            PomodoroState.LONG_BREAK: "Long Break",
            PomodoroState.COMPLETE:   "Done",
        }
        return labels[self.state]