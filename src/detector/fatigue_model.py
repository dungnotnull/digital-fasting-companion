"""
Fatigue detection engine.

Phase 0/1: Rule-based detection using screen time and keystroke signals.
Phase 2: ML-based detection using scikit-learn RandomForest.

The detector outputs a fatigue_score in [0, 1] that feeds the
graduated intervention engine.
"""

import dataclasses
import logging
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FeatureVector:
    """7-dimension feature vector for fatigue detection."""
    typing_wpm: float = 0.0
    error_rate: float = 0.0
    backspace_ratio: float = 0.0
    session_duration_min: float = 0.0
    app_switch_rate: float = 0.0
    hour_of_day: float = 0.0
    hrv_score: float = 0.0

    def to_list(self) -> list:
        return [
            self.typing_wpm, self.error_rate, self.backspace_ratio,
            self.session_duration_min, self.app_switch_rate,
            self.hour_of_day, self.hrv_score,
        ]


class FatigueDetector:
    """
    Fatigue detection using rule-based heuristics (Phase 0/1).

    Computes a composite fatigue_score from:
    - Screen time thresholds (AI tools, social media)
    - Keystroke dynamics (WPM decline, error rate increase)
    - Time of day (higher sensitivity in evenings)
    - HRV score (optional, from wearable)

    In Phase 2, this class is extended with a scikit-learn
    RandomForest model trained on user's own baseline data.
    """

    def __init__(
        self,
        ai_threshold_minutes: int = 120,
        social_threshold_minutes: int = 180,
        feature_window_seconds: int = 300,
    ):
        self.ai_threshold = ai_threshold_minutes
        self.social_threshold = social_threshold_minutes
        self.feature_window = feature_window_seconds

        self.last_prediction_time: float = 0
        self.last_score: float = 0.0
        self._feature_cache: Optional[FeatureVector] = None

    def predict_score(
        self,
        ai_minutes: int = 0,
        social_minutes: int = 0,
        session_duration_min: float = 0,
        typing_wpm: float = 0,
        error_rate: float = 0,
        backspace_ratio: float = 0,
        hour_of_day: Optional[int] = None,
        hrv_score: float = 0,
    ) -> float:
        """
        Compute fatigue score [0, 1] from multi-signal input.

        Returns:
            float in [0, 1] — higher = more fatigued
        """
        if hour_of_day is None:
            hour_of_day = time.localtime().tm_hour

        # ── Screen time factor (0-0.6) ──
        ai_factor = min(ai_minutes / max(1, self.ai_threshold), 2.0)
        social_factor = min(social_minutes / max(1, self.social_threshold), 1.5)
        screen_factor = min((ai_factor * 0.7 + social_factor * 0.3) / 2.0, 1.0)

        # ── Keystroke fatigue factor (0-0.3) ──
        # WPM decline and error rate increase indicate fatigue
        wpm_factor = 0.0
        error_factor = 0.0
        backspace_factor = 0.0

        if typing_wpm > 0:
            # Normal WPM is ~40; decline below baseline = fatigue signal
            wpm_factor = max(0, 1.0 - typing_wpm / 40)
        if error_rate > 0:
            error_factor = min(error_rate / 0.15, 1.0)
        if backspace_ratio > 0:
            backspace_factor = min(backspace_ratio / 0.2, 1.0)

        keystroke_factor = (wpm_factor * 0.5 + error_factor * 0.3 + backspace_factor * 0.2)

        # ── Time of day factor (0-0.1) ──
        # Higher sensitivity 6PM-midnight (willpower depletion)
        time_penalty = 0.0
        if 18 <= hour_of_day <= 23:
            time_penalty = 0.1
        elif 0 <= hour_of_day <= 5:
            time_penalty = 0.15

        # ── Composite score ──
        score = (screen_factor * 0.65 + keystroke_factor * 0.25 + time_penalty)

        # Optional HRV dampening (not yet integrated)
        if hrv_score > 60:
            score *= 0.85

        score = max(0.0, min(1.0, score))

        self.last_score = score
        self.last_prediction_time = time.time()
        self._feature_cache = FeatureVector(
            typing_wpm=typing_wpm,
            error_rate=error_rate,
            backspace_ratio=backspace_ratio,
            session_duration_min=session_duration_min,
            app_switch_rate=ai_minutes / 60 if ai_minutes > 0 else 0,
            hour_of_day=hour_of_day,
            hrv_score=hrv_score,
        )

        logger.debug(
            "Fatigue score: %.3f (screen=%.3f, keystroke=%.3f, time_penalty=%.2f)",
            score, screen_factor, keystroke_factor, time_penalty,
        )

        return score

    def get_last_features(self) -> Optional[FeatureVector]:
        return self._feature_cache

    def get_score_from_features(
        self,
        typing_wpm: float,
        error_rate: float,
        backspace_ratio: float,
        session_min: float,
        app_switch_rate: float,
        hour_of_day: float,
        hrv_score: float,
    ) -> float:
        """
        Phase 2 ML mode — score from pre-computed feature vector.

        Currently rule-based. In Phase 2, delegates to RandomForest model.
        """
        return self.predict_score(
            ai_minutes=int(session_min) if app_switch_rate > 0 else 0,
            session_duration_min=session_min,
            typing_wpm=typing_wpm,
            error_rate=error_rate,
            backspace_ratio=backspace_ratio,
            hour_of_day=int(hour_of_day),
            hrv_score=hrv_score,
        )
