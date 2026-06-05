"""
OpenAI GPT-4o backend with retry logic and rate limiting.

Mirrors ClaudeBackend design for consistent challenge generation
across premium LLM providers.
"""

import json
import logging
import time
from collections import deque
from datetime import datetime
from typing import Deque, Optional

import httpx

from src.agent.static_pool import Challenge
from src.agent.user_context import UserContext
from src.agent.claude_backend import RateLimiter

logger = logging.getLogger(__name__)

OPENAI_SYSTEM_PROMPT = """You are a digital wellbeing coach helping users recover from cognitive fatigue caused by AI tool and social media overuse.

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


class OpenAIBackend:
    """
    OpenAI GPT-4o challenge generator.

    Features:
    - Exponential backoff retry (2, 4, 8 seconds)
    - Rate limiting: max 10 calls/day
    - API key from environment or OS keychain
    """

    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_calls_per_day: int = 10,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self._rate_limiter = RateLimiter(max_calls=max_calls_per_day)

    def is_available(self) -> bool:
        return bool(self.api_key) and self._rate_limiter.can_call()

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
        Generate a challenge via OpenAI GPT-4o.

        Falls back to None on failure (router handles fallback).
        """
        if not self.is_available():
            return None

        ctx = user_context or UserContext(
            time_of_day=time_of_day,
            fatigue_score=fatigue_score,
            session_duration_minutes=session_min,
        )

        system_prompt = OPENAI_SYSTEM_PROMPT.format(
            category=category,
            user_context=ctx.to_summary(),
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Generate a {category} challenge. Session: {session_min}min, fatigue: {fatigue_score:.2f}.",
                },
            ],
            "max_tokens": 300,
            "temperature": 0.85,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(self.API_URL, headers=headers, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    challenge_data = json.loads(content)
                    self._rate_limiter.record_call()
                    return Challenge(
                        id=f"openai-{int(time.time())}",
                        category=challenge_data.get("category", category),
                        title=challenge_data.get("title", "Mindful break"),
                        description=challenge_data.get(
                            "description",
                            "Take a 10-minute break from all screens.",
                        ),
                        time_limit_seconds=challenge_data.get("time_minutes", 12) * 60,
                        source="openai",
                    )

                elif resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("OpenAI rate limited, retrying in %ds", wait)
                    time.sleep(wait)

                elif resp.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning("OpenAI server error %d, retrying in %ds", resp.status_code, wait)
                    time.sleep(wait)

                else:
                    logger.error("OpenAI API error %d: %s", resp.status_code, resp.text[:200])
                    return None

            except (httpx.TimeoutException, Exception) as e:
                logger.warning("OpenAI error: %s (attempt %d)", e, attempt + 1)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    @property
    def calls_today(self) -> int:
        return self._rate_limiter.calls_today
