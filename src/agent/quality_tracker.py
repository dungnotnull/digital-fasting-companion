"""
Challenge quality scoring and ratings tracking.

Tracks user ratings for generated challenges and computes
quality metrics to guide model selection and prompt refinement.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChallengeQualityTracker:
    """
    Tracks and analyzes challenge quality ratings.

    Used to:
    - Determine which backend produces the best challenges
    - Track rating trends over time
    - Trigger fine-tuning when quality drops below threshold
    """

    FINE_TUNE_THRESHOLD = 3.5
    FINE_TUNE_WINDOW = 100  # challenges

    def __init__(self, db=None, storage_path: str = "data/ratings.json"):
        self.db = db
        self.storage_path = storage_path
        self._ratings: List[Dict] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            self._ratings = data.get("ratings", [])
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump({"ratings": self._ratings, "updated_at": datetime.now().isoformat()}, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save ratings: %s", e)

    def record_rating(
        self,
        challenge_id: str,
        rating: int,
        source: str = "static",
        category: str = "unknown",
    ) -> None:
        """Record a challenge rating (1-5 stars)."""
        self._ratings.append({
            "challenge_id": challenge_id,
            "rating": rating,
            "source": source,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

        if self.db:
            try:
                self.db.complete_challenge(challenge_id, rating)
            except Exception:
                pass

    def average_rating(self, source: Optional[str] = None, last_n: int = 50) -> float:
        """Get average rating, optionally filtered by source."""
        ratings = self._ratings
        if source:
            ratings = [r for r in ratings if r["source"] == source]
        ratings = ratings[-last_n:]
        if not ratings:
            return 0.0
        return sum(r["rating"] for r in ratings) / len(ratings)

    def comparison_delta(
        self, source_a: str = "claude", source_b: str = "ollama"
    ) -> Optional[float]:
        """Compare two backends: positive delta means source_a is better."""
        avg_a = self.average_rating(source=source_a, last_n=50)
        avg_b = self.average_rating(source=source_b, last_n=50)
        if avg_a == 0 and avg_b == 0:
            return None
        return avg_a - avg_b

    def needs_fine_tuning(self, source: str = "ollama") -> bool:
        """Check if quality has dropped below fine-tuning threshold."""
        recent = self._ratings[-self.FINE_TUNE_WINDOW:]
        recent = [r for r in recent if r["source"] == source]
        if len(recent) < self.FINE_TUNE_WINDOW:
            return False
        avg = sum(r["rating"] for r in recent) / len(recent)
        return avg < self.FINE_TUNE_THRESHOLD

    def get_rating_distribution(self) -> Dict[int, int]:
        dist = defaultdict(int)
        for r in self._ratings:
            dist[r["rating"]] += 1
        return dict(dist)

    def get_recent(self, n: int = 20) -> List[Dict]:
        return self._ratings[-n:]

    @property
    def total_ratings(self) -> int:
        return len(self._ratings)
