"""
Challenge generator with pluggable backend fallback chain.

Priority order:
1. Claude API  (if API key set, not rate-limited)
2. OpenAI GPT  (if API key set, not rate-limited)
3. Ollama local SLM  (if running)
4. Static challenge pool  (always available)

Manages category rotation, challenge quality tracking,
and session context for personalized generation.
"""

import logging
import random
from typing import List, Optional

from src.agent.static_pool import Challenge, StaticChallengePool
from src.agent.claude_backend import ClaudeBackend
from src.agent.openai_backend import OpenAIBackend
from src.agent.ollama_backend import OllamaBackend
from src.agent.user_context import UserContext
from src.agent.quality_tracker import ChallengeQualityTracker
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

CATEGORIES = ["physical", "creative", "social", "introspective"]


class ChallengeGenerator:
    """
    Unified challenge generation router with automatic fallback.

    Manages:
    - Backend priority chain
    - Category rotation (avoid repeats)
    - Quality tracking
    - User context integration
    """

    def __init__(self):
        settings = get_settings()

        self.claude = ClaudeBackend(
            api_key=settings.claude_api_key,
            max_calls_per_day=10,
        )
        self.openai = OpenAIBackend(
            api_key=settings.openai_api_key,
            max_calls_per_day=10,
        )
        self.ollama = OllamaBackend(
            host=settings.ollama.host,
            model=settings.ollama.model,
            timeout=settings.ollama.timeout_seconds,
        )
        self.static = StaticChallengePool()

        self._backends = [self.claude, self.openai, self.ollama, self.static]
        self.quality_tracker = ChallengeQualityTracker()

        self._last_category: Optional[str] = None
        self._generation_count: int = 0

    def get_challenge(
        self,
        session_min: int = 0,
        fatigue_score: float = 0.5,
        time_of_day: Optional[int] = None,
        exclude_category: Optional[str] = None,
        user_context: Optional[UserContext] = None,
    ) -> Challenge:
        """
        Generate a challenge using the first available backend.

        Args:
            session_min: Minutes in current session
            fatigue_score: Fatigue score [0, 1]
            time_of_day: Hour of day (0-23)
            exclude_category: Category to avoid
            user_context: Full UserContext (preferred)

        Returns:
            A Challenge — always succeeds (static pool is fallback)
        """
        import datetime
        if time_of_day is None:
            time_of_day = datetime.datetime.now().hour

        ctx = user_context or UserContext(
            time_of_day=time_of_day,
            fatigue_score=fatigue_score,
            session_duration_minutes=session_min,
        )

        if not exclude_category:
            exclude_category = self._last_category

        category = exclude_category or ctx.get_suggested_category()
        if not category or category not in CATEGORIES:
            category = random.choice(CATEGORIES)

        for backend in self._backends:
            if backend.is_available():
                result = backend.generate(
                    category=category,
                    session_min=session_min,
                    time_of_day=time_of_day,
                    fatigue_score=fatigue_score,
                    user_context=ctx,
                )
                if result:
                    self._last_category = result.category
                    self._generation_count += 1
                    logger.info(
                        "Challenge generated via %s (category=%s, count=%d)",
                        type(backend).__name__, result.category, self._generation_count,
                    )
                    return result

        # Ultimate fallback
        challenge = self.static.get_random(exclude_category=exclude_category)
        if challenge:
            self._last_category = challenge.category
            self._generation_count += 1
            logger.info(
                "Challenge from static pool (category=%s)", challenge.category
            )
            return challenge

        return Challenge(
            id=f"fallback-{datetime.datetime.now().timestamp():.0f}",
            category="introspective",
            title="Take a break",
            description="Step away from your screen for 10 minutes. Breathe deeply and stretch.",
            time_limit_seconds=600,
            source="fallback",
        )

    def get_available_backends(self) -> List[str]:
        """Return list of currently available backend names."""
        return [
            type(b).__name__
            for b in self._backends
            if b.is_available()
        ]

    def record_rating(self, challenge_id: str, rating: int) -> None:
        """Record a user rating for quality tracking."""
        source = "static"
        if challenge_id.startswith("claude-"):
            source = "claude"
        elif challenge_id.startswith("openai-"):
            source = "openai"
        elif challenge_id.startswith("ollama-"):
            source = "ollama"
        self.quality_tracker.record_rating(
            challenge_id=challenge_id,
            rating=rating,
            source=source,
            category=self._last_category or "unknown",
        )

    @property
    def generation_count(self) -> int:
        return self._generation_count
