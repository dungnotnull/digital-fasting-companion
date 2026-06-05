"""
Paper relevance scorer for knowledge crawler.

Uses keyword-based scoring with domain ontology matching.
Phase 4+ can be upgraded to cosine similarity with sentence-transformers
embeddings (all-MiniLM-L6-v2, 22MB, local).
"""

import logging
import re

logger = logging.getLogger(__name__)

DOMAIN_KEYWORDS = [
    "cognitive fatigue", "information overload", "attention span",
    "digital wellbeing", "screen time", "HRV", "keystroke dynamics",
    "behavioral intervention", "mental health smartphone", "deep work",
]

RELEVANCE_THRESHOLD = 0.65


class RelevanceScorer:
    """
    Scores paper relevance to digital-fasting domain.

    Uses keyword density + pattern matching for lightweight scoring.
    Upgrade path: sentence-transformers/all-MiniLM-L6-v2 for semantic
    similarity (22MB, local, GPU not required).
    """

    THRESHOLD = RELEVANCE_THRESHOLD

    def __init__(self, threshold: float = RELEVANCE_THRESHOLD):
        self.THRESHOLD = threshold
        self._pattern = re.compile(
            "|".join(r"\b" + re.escape(kw) + r"\b" for kw in DOMAIN_KEYWORDS),
            re.IGNORECASE,
        )

    def score(self, title: str, abstract: str) -> float:
        """
        Score paper relevance using keyword density.

        Returns:
            float [0, 1] — higher = more relevant
        """
        text = f"{title} {abstract}".lower()

        # Count keyword matches
        matches = self._pattern.findall(text)
        match_count = len(matches)

        # Density bonus
        words = text.split()
        if not words:
            return 0.0
        density = match_count / max(1, len(words) / 100)  # per 100 words

        # Strong signals
        bonus = 0.0
        if "cognitive fatigue" in text or "digital wellbeing" in text:
            bonus += 0.2
        if "screen time" in text or "attention span" in text:
            bonus += 0.15
        if "intervention" in text:
            bonus += 0.10

        score = min(1.0, density * 0.6 + bonus)

        return score

    def is_relevant(self, title: str, abstract: str) -> bool:
        return self.score(title, abstract) >= self.THRESHOLD
