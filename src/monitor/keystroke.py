"""
Keystroke dynamics tracking module.

Tracks typing patterns to detect cognitive fatigue signals:
- Words per minute (WPM)
- Error rate
- Backspace ratio
- Inter-key timing

NOTE: Only aggregate metrics are stored - no individual keystrokes
are logged to protect user privacy.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Optional, List, Tuple
import threading

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None

logger = logging.getLogger(__name__)


@dataclass
class KeystrokeMetrics:
    """Aggregate keystroke metrics for a session."""
    
    session_start: datetime
    total_keys: int = 0
    total_backspaces: int = 0
    total_errors: int = 0
    total_words: int = 0
    
    # Timing data (in milliseconds)
    key_times_ms: List[int] = field(default_factory=list)
    
    # Calculated metrics
    wpm: float = 0.0
    error_rate: float = 0.0
    backspace_ratio: float = 0.0
    
    def calculate_metrics(self) -> None:
        """Calculate derived metrics from raw data."""
        if self.total_keys == 0:
            return
        
        # Calculate duration in minutes
        duration_min = max(1, (datetime.now() - self.session_start).total_seconds() / 60)
        
        # Words per minute (assume 5 chars per word average)
        self.wpm = (self.total_keys / 5) / duration_min
        
        # Error rate (approximated by backspaces / total keys)
        self.error_rate = self.total_errors / max(1, self.total_keys)
        
        # Backspace ratio
        self.backspace_ratio = self.total_backspaces / max(1, self.total_keys)
    
    def to_features(self) -> Tuple[float, float, float]:
        """
        Convert to feature vector for ML model.
        
        Returns:
            Tuple of (typing_wpm, error_rate, backspace_ratio)
        """
        self.calculate_metrics()
        return (self.wpm, self.error_rate, self.backspace_ratio)


@dataclass 
class RollingWindowStats:
    """Rolling statistics for adaptive baseline."""
    
    wpm_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    error_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    backspace_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    
    baseline_wpm: float = 0.0
    baseline_error: float = 0.0
    baseline_backspace: float = 0.0
    
    def update(self, wpm: float, error_rate: float, backspace_ratio: float) -> None:
        """Update rolling statistics."""
        self.wpm_history.append(wpm)
        self.error_history.append(error_rate)
        self.backspace_history.append(backspace_ratio)
        
        # Update baselines (simple moving average)
        if self.wpm_history:
            self.baseline_wpm = sum(self.wpm_history) / len(self.wpm_history)
        if self.error_history:
            self.baseline_error = sum(self.error_history) / len(self.error_history)
        if self.backspace_history:
            self.baseline_backspace = sum(self.backspace_history) / len(self.backspace_history)
    
    def get_deviation(self, wpm: float, error_rate: float, backspace_ratio: float) -> float:
        """
        Get deviation from baseline.
        
        Returns:
            Deviation score (higher = more fatigued)
        """
        if self.baseline_wpm == 0:
            return 0.0
        
        # Calculate percentage changes from baseline
        wpm_dev = max(0, (self.baseline_wpm - wpm) / self.baseline_wpm)
        error_dev = max(0, error_rate - self.baseline_error)
        backspace_dev = max(0, backspace_ratio - self.baseline_backspace)
        
        # Weighted average
        return (wpm_dev * 0.5 + error_dev * 0.3 + backspace_dev * 0.2)


class KeystrokeTracker:
    """
    Track keystroke dynamics to detect cognitive fatigue.
    
    Uses pynput to capture keyboard events and calculate
    typing patterns. Only aggregate metrics are stored.
    
    Privacy: No individual keystrokes or typed content is stored.
    """
    
    def __init__(
        self,
        session_window_seconds: int = 300,
        min_keys_per_sample: int = 10
    ):
        """
        Initialize keystroke tracker.
        
        Args:
            session_window_seconds: Window for metrics calculation
            min_keys_per_sample: Minimum keys before calculating metrics
        """
        self.session_window = session_window_seconds
        self.min_keys = min_keys_per_sample
        
        # Current session data
        self.current_session: Optional[KeystrokeMetrics] = None
        
        # Rolling statistics for adaptive baseline
        self.rolling = RollingWindowStats()
        
        # Listener state
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Key tracking
        self._last_key_time: float = 0
        self._current_char_count: int = 0
        self._current_backspaces: int = 0
        self._key_times: List[int] = []
        
        logger.info("KeystrokeTracker initialized")
    
    def _on_key_press(self, key) -> None:
        """Handle key press event."""
        if not self._running:
            return
        
        try:
            current_time = time.time()
            
            # Calculate inter-key time
            if self._last_key_time > 0:
                inter_key_ms = int((current_time - self._last_key_time) * 1000)
                self._key_times.append(inter_key_ms)
            
            self._last_key_time = current_time
            
            with self._lock:
                if self.current_session is None:
                    self.current_session = KeystrokeMetrics(
                        session_start=datetime.now()
                    )
                
                # Get key value
                try:
                    key_char = key.char if hasattr(key, 'char') else None
                    if key_char:
                        self.current_session.total_keys += 1
                        self._current_char_count += 1
                except AttributeError:
                    pass
                
        except Exception as e:
            logger.debug(f"Key press handler error: {e}")
    
    def _on_key_release(self, key) -> None:
        """Handle key release event."""
        if not self._running:
            return
        
        try:
            # Check for backspace
            if key == keyboard.Key.backspace:
                with self._lock:
                    if self.current_session:
                        self.current_session.total_backspaces += 1
                        self._current_backspaces += 1
        except Exception as e:
            logger.debug(f"Key release handler error: {e}")
    
    def start(self) -> None:
        """Start tracking keystrokes."""
        if not PYNPUT_AVAILABLE:
            logger.warning("pynput not available - keystroke tracking disabled")
            return
        
        if self._running:
            return
        
        self._running = True
        self.current_session = KeystrokeMetrics(session_start=datetime.now())
        self._last_key_time = 0
        self._key_times = []
        
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._listener.start()
        
        logger.info("Keystroke tracking started")
    
    def stop(self) -> None:
        """Stop tracking keystrokes."""
        if not self._running:
            return
        
        self._running = False
        
        if self._listener:
            self._listener.stop()
            self._listener = None
        
        # Calculate final metrics
        if self.current_session:
            self.current_session.calculate_metrics()
            
            # Update rolling baseline
            self.rolling.update(
                self.current_session.wpm,
                self.current_session.error_rate,
                self.current_session.backspace_ratio
            )
        
        logger.info("Keystroke tracking stopped")
    
    def get_current_metrics(self) -> Optional[KeystrokeMetrics]:
        """
        Get current session metrics.
        
        Returns:
            Current KeystrokeMetrics or None
        """
        with self._lock:
            if self.current_session:
                self.current_session.calculate_metrics()
            return self.current_session
    
    def get_features(self) -> Tuple[float, float, float]:
        """
        Get current features for ML model.
        
        Returns:
            Tuple of (wpm, error_rate, backspace_ratio)
        """
        metrics = self.get_current_metrics()
        if metrics:
            return metrics.to_features()
        return (0.0, 0.0, 0.0)
    
    def get_fatigue_signal(self) -> float:
        """
        Get fatigue signal based on deviation from baseline.
        
        Returns:
            Fatigue score [0, 1] - higher = more fatigued
        """
        wpm, error_rate, backspace_ratio = self.get_features()
        
        if wpm == 0:
            return 0.0
        
        return self.rolling.get_deviation(wpm, error_rate, backspace_ratio)
    
    def reset_baseline(self) -> None:
        """Reset adaptive baseline."""
        self.rolling = RollingWindowStats()
        logger.info("Keystroke baseline reset")
    
    @property
    def is_running(self) -> bool:
        """Check if tracker is running."""
        return self._running


# Export helper function
def create_tracker(**kwargs) -> KeystrokeTracker:
    """Factory function to create a keystroke tracker."""
    return KeystrokeTracker(**kwargs)


# Example usage (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    tracker = KeystrokeTracker()
    print("Starting keystroke tracking for 30 seconds...")
    print("Type some text to see metrics (Ctrl+C to stop)")
    
    tracker.start()
    
    try:
        import time
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    
    tracker.stop()
    
    metrics = tracker.get_current_metrics()
    if metrics:
        print(f"\nSession Metrics:")
        print(f"  Total keys: {metrics.total_keys}")
        print(f"  Total backspaces: {metrics.total_backspaces}")
        print(f"  WPM: {metrics.wpm:.1f}")
        print(f"  Error rate: {metrics.error_rate:.2%}")
        print(f"  Backspace ratio: {metrics.backspace_ratio:.2%}")
