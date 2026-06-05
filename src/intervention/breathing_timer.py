"""
Breathing exercise timer for Tier 2 soft lock intervention.

Guides the user through a 2-minute box breathing exercise:
Inhale 4s → Hold 4s → Exhale 6s → Hold 2s → Repeat
"""

import time
import threading
from typing import Callable, Optional


class BreathingTimer:
    """
    Guided box-breathing timer.

    Callbacks notify the UI of the current phase and remaining time.
    """

    PHASES = [
        ("breathe_in", "Breathe in", 4),
        ("hold", "Hold", 4),
        ("breathe_out", "Breathe out", 6),
        ("hold", "Hold", 2),
    ]
    TOTAL_CYCLES = 8  # ~2 minutes total
    CYCLE_DURATION = 16  # seconds

    def __init__(self, on_phase_change: Optional[Callable] = None, on_complete: Optional[Callable] = None):
        self.on_phase_change = on_phase_change
        self.on_complete = on_complete
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.current_phase = ""
        self.remaining_seconds = 0
        self.cycle = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self):
        for cycle in range(self.TOTAL_CYCLES):
            if not self._running:
                return
            self.cycle = cycle + 1
            for phase_id, phase_label, duration in self.PHASES:
                if not self._running:
                    return
                self.current_phase = phase_label
                for sec in range(duration, 0, -1):
                    self.remaining_seconds = sec
                    if self.on_phase_change:
                        self.on_phase_change(
                            phase=phase_id,
                            label=phase_label,
                            remaining=sec,
                            cycle=self.cycle,
                            total_cycles=self.TOTAL_CYCLES,
                        )
                    time.sleep(1)
        if self._running and self.on_complete:
            self.on_complete()

    @property
    def progress_pct(self) -> float:
        """Progress as percentage (0-100)."""
        return min(100.0, (self.cycle / self.TOTAL_CYCLES) * 100)
