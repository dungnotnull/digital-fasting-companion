"""
Feature extraction pipeline for fatigue detection.

Computes the 7-dimensional feature vector from raw monitoring signals
every 60 seconds for real-time fatigue scoring.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """7-dimension feature vector for fatigue detection."""

    FEATURE_NAMES = [
        "typing_wpm", "error_rate", "backspace_ratio",
        "session_duration_min", "app_switch_rate",
        "hour_of_day", "hrv_score",
    ]

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

    def to_dict(self) -> dict:
        return {
            "typing_wpm": self.typing_wpm,
            "error_rate": self.error_rate,
            "backspace_ratio": self.backspace_ratio,
            "session_duration_min": self.session_duration_min,
            "app_switch_rate": self.app_switch_rate,
            "hour_of_day": self.hour_of_day,
            "hrv_score": self.hrv_score,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FeatureVector":
        return cls(**{k: d.get(k, 0.0) for k in [
            "typing_wpm", "error_rate", "backspace_ratio",
            "session_duration_min", "app_switch_rate",
            "hour_of_day", "hrv_score",
        ]})


class FeaturePipeline:
    """
    Computes 7-feature vectors from raw monitoring signals.

    Maintains a rolling window of the last N samples for smoothing
    and online feature normalization.
    """

    FEATURE_NAMES = [
        "typing_wpm", "error_rate", "backspace_ratio",
        "session_duration_min", "app_switch_rate",
        "hour_of_day", "hrv_score",
    ]

    def __init__(self, window_size: int = 5, compute_interval_seconds: int = 60):
        self.window_size = window_size
        self.compute_interval = compute_interval_seconds

        self._buffer: Deque[dict] = deque(maxlen=window_size)
        self._last_compute_time: float = 0
        self._app_switch_count: int = 0
        self._last_app_name: Optional[str] = None

        self._baseline: dict = {}
        self._feature_min: dict = {}
        self._feature_max: dict = {}

    def add_raw_signals(
        self,
        typing_wpm: float,
        error_rate: float,
        backspace_ratio: float,
        session_duration_min: float,
        current_app_name: Optional[str] = None,
        hour_of_day: Optional[int] = None,
        hrv_score: float = 0.0,
    ) -> None:
        """Feed raw signals into the pipeline."""
        if hour_of_day is None:
            hour_of_day = time.localtime().tm_hour

        # Track app switches
        if current_app_name and current_app_name != self._last_app_name:
            self._app_switch_count += 1
        self._last_app_name = current_app_name

        sample = {
            "typing_wpm": typing_wpm,
            "error_rate": error_rate,
            "backspace_ratio": backspace_ratio,
            "session_duration_min": session_duration_min,
            "app_switch_rate": 0.0,
            "hour_of_day": float(hour_of_day),
            "hrv_score": hrv_score,
        }
        self._buffer.append(sample)

    def compute(self) -> FeatureVector:
        """
        Compute the feature vector from the rolling window.

        Returns:
            FeatureVector with smoothed/aggregated values
        """
        now = time.time()
        interval_hours = max(
            0.001, (now - self._last_compute_time) / 3600
        )
        self._last_compute_time = now

        if not self._buffer:
            return FeatureVector()

        # Average over window for smoothing
        n = len(self._buffer)
        avg = {}
        for key in self.FEATURE_NAMES:
            avg[key] = sum(s.get(key, 0.0) for s in self._buffer) / n

        # App switch rate = switches per hour
        app_switch_rate = self._app_switch_count / interval_hours if interval_hours > 0 else 0
        self._app_switch_count = 0

        fv = FeatureVector(
            typing_wpm=avg["typing_wpm"],
            error_rate=avg["error_rate"],
            backspace_ratio=avg["backspace_ratio"],
            session_duration_min=avg["session_duration_min"],
            app_switch_rate=app_switch_rate,
            hour_of_day=avg["hour_of_day"],
            hrv_score=avg["hrv_score"],
        )

        return fv

    def set_baseline(self, features: list[dict]) -> None:
        """Set user baseline from collected feature samples."""
        if not features:
            return
        n = len(features)
        for key in self.FEATURE_NAMES:
            vals = [s.get(key, 0.0) for s in features]
            self._baseline[key] = sum(vals) / n
            self._feature_min[key] = min(vals)
            self._feature_max[key] = max(vals)

    def normalize(self, fv: FeatureVector) -> FeatureVector:
        """
        Normalize features relative to user baseline.

        Maps each feature to a [0, 1] range based on min/max.
        If no baseline exists, returns the raw vector.
        """
        if not self._baseline:
            return fv

        d = fv.to_dict()
        normalized = {}
        for key in self.FEATURE_NAMES:
            v = d[key]
            b = self._baseline.get(key, v)
            mn = self._feature_min.get(key, v)
            mx = self._feature_max.get(key, v)
            rng = max(0.001, mx - mn)
            normalized[key] = (v - mn) / rng

        return FeatureVector.from_dict(normalized)

    @property
    def has_baseline(self) -> bool:
        return len(self._baseline) >= 7
