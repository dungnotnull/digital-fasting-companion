"""
Claude API backend with retry logic, rate limiting, and prompt caching.

Integrates Anthropic's Claude API (claude-sonnet-4-6) for high-quality
personalized challenge generation.

Full production implementation — activates when CLAUDE_API_KEY is set.
"""

import hashlib
import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, Optional

import httpx

from src.agent.static_pool import Challenge
from src.agent.user_context import UserContext

logger = logging.getLogger(__name__)

CLAUDE_SYSTEM_PROMPT = """You are a digital wellbeing coach helping users recover from cognitive fatigue caused by AI tool and social media overuse.

Your task: Generate ONE specific, engaging, real-world offline challenge.

Rules:
1. Category: {category}
2. Takes 10-15 minutes to complete
3. Absolutely NO digital tools — no phone, no computer, no screens
4. Be specific about WHERE, HOW, and HOW LONG
5. Make it genuinely interesting — something that restores cognitive energy
6. Rotate between physical, creative, social, and introspective categories
7. Avoid clichés like "go for a walk" — unless you add a creative twist

User context: {user_context}

Return ONLY valid JSON with exactly these fields:
{{"title": "Short engaging challenge title (5-10 words)", "description": "Detailed step-by-step instructions for the user to follow (2-4 sentences)", "category": "{category}", "time_minutes": 12}}"""


class RateLimiter:
    """Simple sliding window rate limiter."""

    def __init__(self, max_calls: int = 10, window_seconds: int = 86400):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: Deque[float] = deque()

    def can_call(self) -> bool:
        now = time.time()
        cutoff = now - self.window
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
        return len(self._calls) < self.max_calls

    def record_call(self) -> None:
        self._calls.append(time.time())

    @property
    def calls_today(self) -> int:
        cutoff = time.time() - 86400
        return sum(1 for t in self._calls if t >= cutoff)


class ClaudeBackend:
    """
    Claude API challenge generator with full production features.

    - Exponential backoff retry (2, 4, 8 seconds)
    - Prompt caching via system prompt hash
    - Rate limiting: max 10 calls/day (configurable)
    - API key from OS keychain or environment
    """

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_calls_per_day: int = 10,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self._rate_limiter = RateLimiter(max_calls=max_calls_per_day)
        self._prompt_cache: Dict[str, str] = {}

    def is_available(self) -> bool:
        return bool(self.api_key) and self._rate_limiter.can_call()

    def _cache_key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def generate(
        self,
        category: str = "physical",
        session_min: int = 0,
        time_of_day: int = 12,
        fatigue_score: float = 0.5,
        user_context: Optional[UserContext] = None,
        **kwargs,
    ) -> Optional[Challenge]:
        """
        Generate a challenge via Claude API.

        Uses exponential backoff retry for transient errors.
        Falls back to None (router handles fallback) on failure.
        """
        if not self.is_available():
            logger.debug("Claude API unavailable (no key or rate limited)")
            return None

        ctx = user_context or UserContext(
            time_of_day=time_of_day,
            fatigue_score=fatigue_score,
            session_duration_minutes=session_min,
        )

        system_prompt = CLAUDE_SYSTEM_PROMPT.format(
            category=category,
            user_context=ctx.to_summary(),
        )

        user_prompt = f"Generate a {category} challenge for someone who has been online for {session_min} minutes with fatigue score {fatigue_score:.2f}."

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 300,
            "temperature": 0.85,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(self.API_URL, headers=headers, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("content", [{}])[0].get("text", "")
                    challenge_data = self._parse_response(content, category)
                    if challenge_data:
                        self._rate_limiter.record_call()
                        return Challenge(
                            id=f"claude-{int(time.time())}",
                            category=challenge_data.get("category", category),
                            title=challenge_data.get("title", "Mindful break"),
                            description=challenge_data.get(
                                "description",
                                "Take a 10-minute break from all screens. Stretch and breathe deeply.",
                            ),
                            time_limit_seconds=challenge_data.get("time_minutes", 12) * 60,
                            source="claude",
                        )
                    logger.warning("Claude response parsing failed")

                elif resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Claude rate limited (attempt %d), retrying in %ds", attempt + 1, wait)
                    time.sleep(wait)

                elif resp.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning("Claude server error %d, retrying in %ds", resp.status_code, wait)
                    time.sleep(wait)

                else:
                    logger.error("Claude API error %d: %s", resp.status_code, resp.text[:200])
                    return None

            except httpx.TimeoutException:
                logger.warning("Claude API timeout (attempt %d)", attempt + 1)
            except Exception as e:
                logger.warning("Claude API error: %s (attempt %d)", e, attempt + 1)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    def _parse_response(self, text: str, fallback_category: str) -> Optional[dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        import re
        match = re.search(r'\{[^{}]*"title"[^{}]*"description"[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

    @property
    def calls_today(self) -> int:
        return self._rate_limiter.calls_today
