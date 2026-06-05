"""
Baseline collector for Phase 2 ML training.

Collects 7 days of usage data with voluntary fatigue self-reports
to bootstrap the personalized RandomForest model.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from src.detector.feature_pipeline import FeatureVector

logger = logging.getLogger(__name__)


class BaselineCollector:
    """
    Collects 7 days of feature samples with user fatigue labels.

    Cold start strategy:
    1. Days 1-7: Collect feature vectors every 60s
    2. Prompt user for fatigue self-report 2-3 times per day
    3. After 7 days + >= 100 labeled samples: train ML model
    4. Switch from rule-based to ML-based detection
    """

    MIN_DAYS = 7
    MIN_SAMPLES = 100
    REPORT_WINDOW_HOURS = 3  # hours between self-report prompts

    def __init__(
        self,
        db=None,
        storage_path: str = "data/baseline.json",
        on_report_needed: Optional[Callable] = None,
    ):
        self.db = db
        self.storage_path = storage_path
        self.on_report_needed = on_report_needed

        self._samples: List[Dict] = []
        self._active = False
        self._start_time: Optional[float] = None
        self._last_report_time: float = 0

        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            import json
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            self._samples = data.get("samples", [])
            self._start_time = data.get("start_time")
            logger.info(
                "Loaded %d baseline samples from disk", len(self._samples)
            )
        except Exception as e:
            logger.warning("Failed to load baseline: %s", e)

    def _save(self) -> None:
        try:
            import json
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(
                    {
                        "samples": self._samples,
                        "start_time": self._start_time,
                        "updated_at": time.time(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning("Failed to save baseline: %s", e)

    def start(self) -> None:
        self._active = True
        if self._start_time is None:
            self._start_time = time.time()
        self._save()
        logger.info("Baseline collection started (day %d)", self._days_elapsed)

    def stop(self) -> None:
        self._active = False
        self._save()
        logger.info(
            "Baseline collection stopped: %d samples, %d days",
            len(self._samples), self._days_elapsed,
        )

    def record_sample(
        self,
        features: FeatureVector,
        fatigue_label: Optional[float] = None,
    ) -> None:
        """Record a feature vector with optional fatigue label."""
        if not self._active:
            return

        sample = {
            "timestamp": time.time(),
            "features": features.to_dict(),
            "label": fatigue_label,
        }
        self._samples.append(sample)

        # Periodic save (every 50 samples)
        if len(self._samples) % 50 == 0:
            self._save()

        # Check if we should prompt for self-report
        if (
            self._last_report_time > 0
            and time.time() - self._last_report_time > self.REPORT_WINDOW_HOURS * 3600
        ):
            if self.on_report_needed:
                self.on_report_needed()

    def record_label(self, fatigue_score: float) -> None:
        """
        Record a fatigue self-report label.

        Applies to the most recent unlabeled samples.
        """
        self._last_report_time = time.time()
        unlabeled = [s for s in self._samples if s["label"] is None]
        count = min(20, len(unlabeled))
        for s in unlabeled[-count:]:
            s["label"] = fatigue_score
        self._save()
        logger.info(
            "Labeled %d recent samples with score %.2f", count, fatigue_score
        )

    def is_ready(self) -> bool:
        """Check if enough data has been collected to train."""
        return (
            self._active
            and self._days_elapsed >= self.MIN_DAYS
            and self.labeled_count >= self.MIN_SAMPLES
        )

    def get_labeled_samples(self, min_label: float = 0.5) -> List[Tuple[List[float], float]]:
        """Get labeled samples for ML training, binarized at threshold."""
        labeled = [s for s in self._samples if s.get("label") is not None]
        return [
            (
                [s["features"].get(k, 0.0) for k in FeatureVector.FEATURE_NAMES]
                if hasattr(FeatureVector, "FEATURE_NAMES")
                else list(s["features"].values()),
                1.0 if (s["label"] or 0.0) >= min_label else 0.0,
            )
            for s in labeled
        ]

    @property
    def _days_elapsed(self) -> int:
        if self._start_time is None:
            return 0
        return int((time.time() - self._start_time) / 86400)

    @property
    def labeled_count(self) -> int:
        return sum(1 for s in self._samples if s.get("label") is not None)

    @property
    def sample_count(self) -> int:
        return len(self._samples)
