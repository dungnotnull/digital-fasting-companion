"""
Garmin Connect HRV/Stress data integration.

Fetches wearable biometric data (HRV, stress score) from Garmin Connect
to supplement fatigue detection with objective autonomic state signals.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BiometricReading:
    """Single biometric reading from wearable."""

    hrv_score: float = 0.0       # Normalized HRV (0-100, higher = better)
    stress_score: float = 0.0     # 0-100, lower = better
    resting_heart_rate: float = 0.0
    sleep_score: float = 0.0      # 0-100
    timestamp: Optional[datetime] = None

    def to_fatigue_feature(self) -> float:
        """
        Convert biometrics to a single fatigue feature value.
        Lower HRV + higher stress = more fatigued.
        Returns normalized score 0-100 where higher = worse.
        """
        if self.hrv_score == 0 and self.stress_score == 0:
            return 50.0  # neutral

        hrv_penalty = max(0, 50 - self.hrv_score) / 100
        stress_penalty = self.stress_score / 100
        return min(100.0, max(0.0, (hrv_penalty * 0.6 + stress_penalty * 0.4) * 100))


class GarminBackend:
    """
    Garmin Connect biometrics integration.

    Stub implementation — requires real garminconnect library
    and user credentials to activate.
    """

    def __init__(self, username: str = "", password: str = ""):
        self.username = username
        self.password = password
        self._client = None
        self._authenticated = False

    def is_available(self) -> bool:
        return bool(self.username and self.password) and self._authenticated

    def authenticate(self) -> bool:
        """Authenticate with Garmin Connect. Stub — returns False."""
        if not self.username or not self.password:
            return False
        try:
            from garminconnect import Garmin
            self._client = Garmin(self.username, self.password)
            self._client.login()
            self._authenticated = True
            logger.info("Garmin Connect authenticated")
            return True
        except ImportError:
            logger.debug("garminconnect library not installed")
        except Exception as e:
            logger.warning("Garmin auth failed: %s", e)
        return False

    def get_stress_data(self, date=None) -> Optional[BiometricReading]:
        """Fetch today's stress/HRV data. Stub."""
        if not self.is_available():
            return None

        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            # Real: self._client.get_stress_data(date)
            return BiometricReading(
                stress_score=50.0,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.debug("Garmin stress fetch failed: %s", e)
        return None

    def get_hrv_data(self, date=None) -> Optional[BiometricReading]:
        """Fetch HRV data. Stub."""
        if not self.is_available():
            return None
        return BiometricReading(hrv_score=50.0, timestamp=datetime.now())

    def get_latest(self) -> Optional[BiometricReading]:
        """Get the latest combined reading."""
        stress = self.get_stress_data()
        hrv = self.get_hrv_data()

        if not stress and not hrv:
            return None

        return BiometricReading(
            hrv_score=hrv.hrv_score if hrv else 50.0,
            stress_score=stress.stress_score if stress else 50.0,
            resting_heart_rate=stress.resting_heart_rate if stress else 70.0,
            timestamp=datetime.now(),
        )
