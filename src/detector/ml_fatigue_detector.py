"""
ML-based fatigue detection engine using scikit-learn RandomForest.

Replaces rule-based heuristics with a personalized model trained
on the user's own behavioral data.

Architecture:
1. Cold start: rule-based mode for Week 1
2. After 7 days: switch to trained RandomForest model
3. Online learning: weekly retraining on accumulated labeled data
4. Adaptive thresholds: per-user calibration from baseline distribution
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.detector.feature_pipeline import FeatureVector, FeaturePipeline

logger = logging.getLogger(__name__)


class MLFatigueDetector:
    """
    Personalized ML fatigue detector.

    Uses scikit-learn RandomForestClassifier trained on user data.
    Falls back to rule-based scoring when no model is available.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 8,
        min_samples_split: int = 2,
        model_path: Optional[str] = None,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.model_path = model_path or "data/fatigue_model.joblib"

        self._model = None
        self._pipeline = FeaturePipeline(window_size=5)

        self._training_data: List[Tuple[list, float]] = []  # (features, label)
        self._is_trained = False
        self._samples_since_train: int = 0

        self._trained_thresholds: Dict[str, float] = {}

        self._feature_importances: Optional[Dict[str, float]] = None

        # Try to load existing model
        self._load_model()

    def predict_score(
        self,
        typing_wpm: float = 0,
        error_rate: float = 0,
        backspace_ratio: float = 0,
        session_duration_min: float = 0,
        app_switch_rate: float = 0,
        hour_of_day: Optional[float] = None,
        hrv_score: float = 0,
    ) -> float:
        """
        Predict fatigue score [0, 1].

        Uses ML model if trained, otherwise rule-based fallback.
        """
        if hour_of_day is None:
            hour_of_day = float(time.localtime().tm_hour)

        fv = FeatureVector(
            typing_wpm=typing_wpm,
            error_rate=error_rate,
            backspace_ratio=backspace_ratio,
            session_duration_min=session_duration_min,
            app_switch_rate=app_switch_rate,
            hour_of_day=hour_of_day,
            hrv_score=hrv_score,
        )

        if self._is_trained and self._model is not None:
            return self._predict_ml(fv)
        return self._predict_rules(fv)

    def _predict_ml(self, fv: FeatureVector) -> float:
        """Predict using trained RandomForest model."""
        features = np.array([fv.to_list()])
        proba = self._model.predict_proba(features)
        # Class 1 = fatigued
        if proba.shape[1] > 1:
            score = float(proba[0][1])
        else:
            score = float(proba[0][0])
        return max(0.0, min(1.0, score))

    def _predict_rules(self, fv: FeatureVector) -> float:
        """Rule-based fallback (cold start)."""
        ai_minutes = fv.session_duration_min if fv.app_switch_rate > 0 else 0
        screen_factor = min(ai_minutes / 120, 2.0) / 2.0

        wpm_factor = max(0, 1.0 - fv.typing_wpm / 40) if fv.typing_wpm > 0 else 0
        error_factor = min(fv.error_rate / 0.15, 1.0)
        backspace_factor = min(fv.backspace_ratio / 0.2, 1.0)
        keystroke_factor = wpm_factor * 0.5 + error_factor * 0.3 + backspace_factor * 0.2

        hour = fv.hour_of_day
        time_penalty = 0.1 if 18 <= hour <= 23 else (0.15 if 0 <= hour <= 5 else 0.0)

        score = screen_factor * 0.65 + keystroke_factor * 0.25 + time_penalty

        if fv.hrv_score > 60:
            score *= 0.85

        return max(0.0, min(1.0, score))

    def add_training_sample(
        self, fv: FeatureVector, label: float
    ) -> None:
        """
        Add a labeled sample to the training buffer.

        Args:
            fv: Feature vector at time of fatigue event
            label: 0.0 (not fatigued) or 1.0 (fatigued)
        """
        self._training_data.append((fv.to_list(), label))
        self._samples_since_train += 1

    def train(self) -> dict:
        """
        Train/retrain the RandomForest model on all accumulated data.

        Returns:
            Training metrics dict
        """
        if len(self._training_data) < 10:
            logger.warning(
                "Not enough training samples (%d < 10)", len(self._training_data)
            )
            return {"status": "skipped", "reason": "insufficient_data", "samples": len(self._training_data)}

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import cross_val_score
        except ImportError:
            logger.warning("scikit-learn not available — using rule-based fallback")
            return {"status": "skipped", "reason": "no_sklearn"}

        X = np.array([s[0] for s in self._training_data])
        y = np.array([s[1] for s in self._training_data])

        # Ensure binary labels
        y_binary = (np.array(y) >= 0.5).astype(int)

        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X, y_binary)

        # Cross-validation
        n_folds = min(5, len(self._training_data) // 3)
        metrics = {}
        if n_folds >= 2:
            try:
                cv_scores = cross_val_score(
                    self._model, X, y_binary, cv=n_folds, scoring="precision"
                )
                metrics["cv_precision_mean"] = float(cv_scores.mean())
                metrics["cv_precision_std"] = float(cv_scores.std())
            except Exception:
                pass

        # Feature importances
        self._feature_importances = {
            name: float(imp)
            for name, imp in zip(FeaturePipeline.FEATURE_NAMES, self._model.feature_importances_)
        }

        self._is_trained = True
        self._samples_since_train = 0

        # Compute adaptive thresholds from prediction distribution
        self._calibrate_thresholds(X)

        # Save model
        self._save_model()

        logger.info(
            "Model trained: %d samples, precision=%.3f",
            len(self._training_data),
            metrics.get("cv_precision_mean", 0.0),
        )

        metrics.update({
            "status": "trained",
            "samples": len(self._training_data),
            "feature_importances": self._feature_importances,
        })
        return metrics

    def _calibrate_thresholds(self, X: np.ndarray) -> None:
        """Compute adaptive tier thresholds from prediction distribution."""
        if not self._is_trained or self._model is None:
            return

        probas = self._model.predict_proba(X)
        scores = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]

        if len(scores) < 5:
            return

        self._trained_thresholds = {
            "tier1_min": float(np.percentile(scores, 40)),
            "tier2_min": float(np.percentile(scores, 60)),
            "tier3_min": float(np.percentile(scores, 80)),
        }

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        return self._feature_importances

    def get_trained_thresholds(self) -> Dict[str, float]:
        return self._trained_thresholds

    def _save_model(self) -> None:
        if self._model is None:
            return
        try:
            import joblib
            os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
            model_data = {
                "model": self._model,
                "feature_importances": self._feature_importances,
                "trained_thresholds": self._trained_thresholds,
                "n_samples": len(self._training_data),
            }
            joblib.dump(model_data, self.model_path)
            logger.info("Model saved to %s", self.model_path)
        except Exception as e:
            logger.warning("Failed to save model: %s", e)

    def _load_model(self) -> None:
        if not os.path.exists(self.model_path):
            return
        try:
            import joblib
            data = joblib.load(self.model_path)
            self._model = data.get("model")
            self._feature_importances = data.get("feature_importances")
            self._trained_thresholds = data.get("trained_thresholds", {})
            self._is_trained = self._model is not None
            if self._is_trained:
                logger.info(
                    "Model loaded: %d samples trained",
                    data.get("n_samples", 0),
                )
        except Exception as e:
            logger.warning("Failed to load model: %s", e)
            self._is_trained = False

    def needs_retraining(self, min_samples: int = 20) -> bool:
        return self._samples_since_train >= min_samples

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def sample_count(self) -> int:
        return len(self._training_data)
