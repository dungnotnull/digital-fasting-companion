"""
Ollama backend for local SLM challenge generation.

Uses TinyLlama-1.1B-Chat via Ollama's REST API with structured
prompts for context-aware, category-rotated challenge generation.
"""

import json
import logging
import time
from typing import Optional

import httpx

from src.agent.static_pool import Challenge
from src.agent.user_context import UserContext

logger = logging.getLogger(__name__)

CHALLENGE_SYSTEM_PROMPT = """You are a digital wellbeing coach helping a user recover from digital fatigue.

Generate ONE real-world offline challenge that is:
1. Category: {category} (specific to this category)
2. Takes 10-15 minutes to complete
3. Requires NO digital tools whatsoever (no phone, no computer, no screen)
4. Is specific and immediately actionable — not vague advice
5. Are creative and engaging — make the user WANT to do this

The user context: {user_context}

Return ONLY valid JSON:
{{"title": "short challenge title", "description": "detailed actionable instructions", "category": "{category}", "time_minutes": 12}}
"""


class OllamaBackend:
    """
    Local TinyLlama challenge generator via Ollama REST API.

    Falls back to static pool if Ollama is unavailable or times out.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "tinyllama",
        timeout: int = 30,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._available = False
        self._last_health_check: float = 0
        self._health_check_interval: float = 60

    def is_available(self) -> bool:
        """Check if Ollama is running. Caches result for 60 seconds."""
        now = time.time()
        if now - self._last_health_check < self._health_check_interval:
            return self._available
        self._available = self.check_health()
        self._last_health_check = now
        return self._available

    def check_health(self) -> bool:
        """Ping Ollama to verify it's running."""
        try:
            with httpx.Client(timeout=3) as client:
                resp = client.get(f"{self.host}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    has_model = any(self.model in m.get("name", "") for m in models)
                    if has_model:
                        logger.debug("Ollama available: model=%s", self.model)
                        return True
                    logger.debug("Ollama running but model %s not found", self.model)
                    return False
        except Exception:
            pass
        return False

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
        Generate a challenge via Ollama.

        Args:
            category: Challenge category
            session_min: Minutes in current session
            time_of_day: Hour (0-23)
            fatigue_score: Fatigue score [0, 1]
            user_context: Full UserContext (preferred)

        Returns:
            Challenge or None (falls back to static pool)
        """
        if not self.is_available():
            return None

        ctx = user_context or UserContext(
            time_of_day=time_of_day,
            fatigue_score=fatigue_score,
            session_duration_minutes=session_min,
        )

        prompt = CHALLENGE_SYSTEM_PROMPT.format(
            category=category,
            user_context=ctx.to_summary(),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "top_p": 0.9,
                            "max_tokens": 200,
                        },
                    },
                )

                if resp.status_code != 200:
                    logger.warning("Ollama returned %d", resp.status_code)
                    return None

                result = resp.json()
                response_text = result.get("response", "")

                # Extract JSON from response
                challenge_data = self._parse_response(response_text, category)
                if challenge_data:
                    return Challenge(
                        id=f"ollama-{int(time.time())}",
                        category=challenge_data.get("category", category),
                        title=challenge_data.get("title", "Take a mindful break"),
                        description=challenge_data.get(
                            "description",
                            "Step away from your screen. Breathe deeply for 5 minutes.",
                        ),
                        time_limit_seconds=challenge_data.get("time_minutes", 12) * 60,
                        source="ollama",
                    )

        except httpx.TimeoutException:
            logger.warning("Ollama request timed out after %ds", self.timeout)
        except Exception as e:
            logger.warning("Ollama error: %s", e)

        return None

    def _parse_response(self, text: str, fallback_category: str) -> Optional[dict]:
        """Extract JSON challenge from model output."""
        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON block
        import re
        match = re.search(r'\{[^{}]*"title"[^{}]*"description"[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Broader match
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None
