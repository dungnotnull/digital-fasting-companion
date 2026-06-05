"""
Apple HealthKit backend stub.

Integrates iOS HealthKit data (HRV, sleep, activity) as supplementary
fatigue signals. Requires iOS companion app for data sync.
"""

import logging
from typing import Optional

from src.biometrics.garmin_backend import BiometricReading

logger = logging.getLogger(__name__)


class AppleHealthBackend:
    """
    Apple HealthKit integration.

    Stub — requires iOS companion app via React Native HealthKit bridge.
    """

    def __init__(self):
        self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_latest_hrv(self) -> Optional[BiometricReading]:
        return None

    def get_sleep_data(self) -> Optional[dict]:
        return None
