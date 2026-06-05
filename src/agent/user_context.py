"""
UserContext data class for challenge generation.

Provides structured user state information to the challenge
generation engine for personalized, context-aware challenges.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserContext:
    """User state snapshot for challenge generation."""

    time_of_day: int = field(default_factory=lambda: datetime.now().hour)
    fatigue_score: float = 0.0
    last_challenge_category: Optional[str] = None
    session_duration_minutes: int = 0
    ai_minutes_today: int = 0
    social_minutes_today: int = 0
    recent_activity_category: str = "none"
    intervention_tier: int = 0
    timestamp: float = field(default_factory=time.time)

    def get_time_period(self) -> str:
        """Map hour to natural language time period."""
        if 5 <= self.time_of_day < 12:
            return "morning"
        elif 12 <= self.time_of_day < 17:
            return "afternoon"
        elif 17 <= self.time_of_day < 21:
            return "evening"
        else:
            return "night"

    def get_suggested_category(self) -> str:
        """Suggest challenge category based on time and fatigue."""
        morning_rotation = ["physical", "creative", "introspective", "social"]
        evening_rotation = ["introspective", "physical", "creative", "social"]

        if self.time_of_day >= 17:
            rotation = evening_rotation
        else:
            rotation = morning_rotation

        # Avoid repeating last category
        candidates = [c for c in rotation if c != self.last_challenge_category]
        if not candidates:
            candidates = rotation

        # Select based on fatigue level
        if self.fatigue_score > 0.8:
            idx = 0  # prioritize first (physical or introspective)
        elif self.fatigue_score > 0.6:
            idx = 1
        else:
            idx = 2

        return candidates[min(idx, len(candidates) - 1)]

    def to_summary(self) -> str:
        """Generate a concise summary for LLM prompts."""
        return (
            f"Time of day: {self.get_time_period()} ({self.time_of_day}:00). "
            f"Fatigue score: {self.fatigue_score:.2f}/1.0. "
            f"Session: {self.session_duration_minutes}min. "
            f"Today: {self.ai_minutes_today}min AI, {self.social_minutes_today}min social. "
            f"Recent activity: {self.recent_activity_category}."
        )
