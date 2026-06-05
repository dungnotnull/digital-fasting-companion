"""Static challenge pool loader."""

import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Challenge:
    id: str
    category: str
    title: str
    description: str
    time_limit_seconds: int
    source: str = "static"


class StaticChallengePool:
    """Loads and serves challenges from the static JSON pool."""

    _pool: Optional[List[Challenge]] = None
    _category_index: dict = {}

    def __init__(self, pool_path: str = "src/intervention/challenge_pool.json"):
        self.pool_path = Path(pool_path)
        self._load()

    def _load(self) -> None:
        if not self.pool_path.exists():
            logger.warning("Challenge pool not found: %s", self.pool_path)
            StaticChallengePool._pool = []
            return

        with open(self.pool_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        StaticChallengePool._pool = [
            Challenge(
                id=entry["id"],
                category=entry["category"],
                title=entry["title"],
                description=entry["description"],
                time_limit_seconds=entry["time_limit_seconds"],
                source="static",
            )
            for entry in data.get("challenges", [])
        ]

        StaticChallengePool._category_index = {}
        for ch in StaticChallengePool._pool:
            StaticChallengePool._category_index.setdefault(ch.category, []).append(ch)

        logger.info("Loaded %d static challenges", len(StaticChallengePool._pool))

    def is_available(self) -> bool:
        return self._pool is not None and len(self._pool) > 0

    def generate(
        self,
        category: str = "physical",
        session_min: int = 0,
        time_of_day: int = 12,
        fatigue_score: float = 0.5,
        **kwargs,
    ) -> Optional[Challenge]:
        """Generate a challenge — delegates to get_random with category exclusion."""
        exclude = kwargs.get("exclude_category")
        return self.get_random(exclude_category=exclude)

    def get_random(self, exclude_category: Optional[str] = None) -> Optional[Challenge]:
        """Get a random challenge, optionally avoiding a category."""
        candidates = [
            ch for ch in self._pool
            if exclude_category is None or ch.category != exclude_category
        ]
        if not candidates:
            candidates = self._pool
        if not candidates:
            return None
        return random.choice(candidates)

    def get_by_category(self, category: str) -> Optional[Challenge]:
        """Get a random challenge from a specific category."""
        entries = self._category_index.get(category, [])
        if not entries:
            return None
        return random.choice(entries)
