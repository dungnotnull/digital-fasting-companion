"""
Screen time monitoring module.

Monitors active application and track usage time per category.
Uses psutil for cross-platform process monitoring.
"""

import os
import platform
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

import psutil

logger = logging.getLogger(__name__)


class AppCategory(Enum):
    """Application category classification."""
    AI_TOOLS = "ai_tools"
    SOCIAL_MEDIA = "social_media"
    PRODUCTIVE = "productive"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"


# Default app category mappings
DEFAULT_CATEGORY_MAP: Dict[str, AppCategory] = {
    # AI Tools
    "chatgpt": AppCategory.AI_TOOLS,
    "claude": AppCategory.AI_TOOLS,
    "copilot": AppCategory.AI_TOOLS,
    "bard": AppCategory.AI_TOOLS,
    "gemini": AppCategory.AI_TOOLS,
    "perplexity": AppCategory.AI_TOOLS,
    "cursor": AppCategory.AI_TOOLS,
    "windsurf": AppCategory.AI_TOOLS,
    "llama": AppCategory.AI_TOOLS,
    "ollama": AppCategory.AI_TOOLS,
    
    # Social Media
    "facebook": AppCategory.SOCIAL_MEDIA,
    "twitter": AppCategory.SOCIAL_MEDIA,
    "x": AppCategory.SOCIAL_MEDIA,
    "instagram": AppCategory.SOCIAL_MEDIA,
    "tiktok": AppCategory.SOCIAL_MEDIA,
    "youtube": AppCategory.SOCIAL_MEDIA,
    "reddit": AppCategory.SOCIAL_MEDIA,
    "linkedin": AppCategory.SOCIAL_MEDIA,
    "discord": AppCategory.SOCIAL_MEDIA,
    "slack": AppCategory.SOCIAL_MEDIA,
    "telegram": AppCategory.SOCIAL_MEDIA,
    "whatsapp": AppCategory.SOCIAL_MEDIA,
    
    # Productive
    "code": AppCategory.PRODUCTIVE,
    "vscode": AppCategory.PRODUCTIVE,
    "sublime": AppCategory.PRODUCTIVE,
    "notion": AppCategory.PRODUCTIVE,
    "obsidian": AppCategory.PRODUCTIVE,
    "evernote": AppCategory.PRODUCTIVE,
    "to-do": AppCategory.PRODUCTIVE,
    "task": AppCategory.PRODUCTIVE,
    "calendar": AppCategory.PRODUCTIVE,
    "mail": AppCategory.PRODUCTIVE,
    "outlook": AppCategory.PRODUCTIVE,
    "gmail": AppCategory.PRODUCTIVE,
    
    # Entertainment
    "spotify": AppCategory.ENTERTAINMENT,
    "netflix": AppCategory.ENTERTAINMENT,
    "twitch": AppCategory.ENTERTAINMENT,
    "steam": AppCategory.ENTERTAINMENT,
    "epic": AppCategory.ENTERTAINMENT,
    "games": AppCategory.ENTERTAINMENT,
}


@dataclass
class UsageSession:
    """Represents a usage session for an application."""
    
    app_name: str
    category: AppCategory
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    
    def end(self) -> None:
        """End the session and calculate duration."""
        self.end_time = datetime.now()
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())


@dataclass
class ScreenTimeStats:
    """Screen time statistics."""
    
    ai_time_minutes: int = 0
    social_time_minutes: int = 0
    productive_time_minutes: int = 0
    entertainment_time_minutes: int = 0
    other_time_minutes: int = 0
    
    total_sessions: int = 0
    current_session: Optional[UsageSession] = None
    
    def get_category_minutes(self, category: AppCategory) -> int:
        """Get time in minutes for a category."""
        if category == AppCategory.AI_TOOLS:
            return self.ai_time_minutes
        elif category == AppCategory.SOCIAL_MEDIA:
            return self.social_time_minutes
        elif category == AppCategory.PRODUCTIVE:
            return self.productive_time_minutes
        elif category == AppCategory.ENTERTAINMENT:
            return self.entertainment_time_minutes
        return self.other_time_minutes
    
    def add_time(self, category: AppCategory, seconds: int) -> None:
        """Add time to a category."""
        minutes = seconds // 60
        if category == AppCategory.AI_TOOLS:
            self.ai_time_minutes += minutes
        elif category == AppCategory.SOCIAL_MEDIA:
            self.social_time_minutes += minutes
        elif category == AppCategory.PRODUCTIVE:
            self.productive_time_minutes += minutes
        elif category == AppCategory.ENTERTAINMENT:
            self.entertainment_time_minutes += minutes
        else:
            self.other_time_minutes += minutes


class ScreenTimeMonitor:
    """
    Monitor screen time and application usage.
    
    Tracks active foreground application and categorizes usage
    time per app category.
    """
    
    def __init__(
        self,
        category_map: Optional[Dict[str, AppCategory]] = None,
        poll_interval_seconds: int = 30
    ):
        """
        Initialize screen time monitor.
        
        Args:
            category_map: Custom category mapping (app name -> category)
            poll_interval_seconds: How often to check active app
        """
        self.category_map = category_map or DEFAULT_CATEGORY_MAP.copy()
        self.poll_interval = poll_interval_seconds
        
        self.current_session: Optional[UsageSession] = None
        self.sessions: List[UsageSession] = []
        self.stats = ScreenTimeStats()
        
        self._running = False
        self._last_check: Optional[datetime] = None
        
        logger.info("ScreenTimeMonitor initialized")
    
    def _get_active_app_name(self) -> Tuple[str, str]:
        """
        Get the currently active application name.
        
        Returns:
            Tuple of (app_name, app_title)
        """
        system = platform.system()
        
        try:
            if system == "Windows":
                return self._get_active_app_windows()
            elif system == "Darwin":  # macOS
                return self._get_active_app_macos()
            else:
                return ("unknown", "Unknown")
        except Exception as e:
            logger.warning(f"Failed to get active app: {e}")
            return ("unknown", "Unknown")
    
    def _get_active_app_windows(self) -> Tuple[str, str]:
        """Get active app on Windows."""
        try:
            import win32gui
            import win32process
            
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid:
                    try:
                        process = psutil.Process(pid)
                        name = process.name().lower().replace(".exe", "")
                        return (name, title)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            return ("unknown", "Unknown")
        except ImportError:
            # Fallback if win32 not available
            return ("unknown", "Unknown")
    
    def _get_active_app_macos(self) -> Tuple[str, str]:
        """Get active app on macOS."""
        try:
            from AppKit import NSWorkspace, NSRunningApplication
            
            active = NSWorkspace.shared().frontmostApplication()
            if active:
                name = active.localizedName().lower()
                return (name, name)
            return ("unknown", "Unknown")
        except ImportError:
            return ("unknown", "Unknown")
    
    def _categorize_app(self, app_name: str) -> AppCategory:
        """
        Categorize an application by name.
        
        Args:
            app_name: Name of the application
            
        Returns:
            AppCategory classification
        """
        app_lower = app_name.lower()
        
        # Check direct mappings
        for key, category in self.category_map.items():
            if key in app_lower:
                return category
        
        return AppCategory.UNKNOWN
    
    def start_session(self, app_name: str, category: AppCategory) -> None:
        """
        Start a new usage session.
        
        Args:
            app_name: Name of the application
            category: Category of the application
        """
        # End current session if exists
        if self.current_session:
            self.end_session()
        
        self.current_session = UsageSession(
            app_name=app_name,
            category=category,
            start_time=datetime.now()
        )
        logger.debug(f"Started session for {app_name} ({category.value})")
    
    def end_session(self) -> Optional[UsageSession]:
        """
        End the current usage session.
        
        Returns:
            Completed UsageSession or None
        """
        if not self.current_session:
            return None
        
        self.current_session.end()
        
        # Add time to stats
        self.stats.add_time(
            self.current_session.category,
            self.current_session.duration_seconds
        )
        
        # Store session
        self.sessions.append(self.current_session)
        self.stats.total_sessions += 1
        
        session = self.current_session
        self.current_session = None
        
        logger.debug(f"Ended session: {session.app_name} ({session.duration_seconds}s)")
        return session
    
    def check_active_app(self) -> None:
        """Check and update active application."""
        app_name, app_title = self._get_active_app_name()
        
        if not app_name or app_name == "unknown":
            return
        
        # Determine category
        category = self._categorize_app(app_name)
        
        # Check if we need to start/end session
        if self.current_session:
            if self.current_session.app_name != app_name:
                # App changed, end current and start new
                self.end_session()
                self.start_session(app_name, category)
        else:
            # Start new session
            self.start_session(app_name, category)
        
        self._last_check = datetime.now()
    
    def get_current_stats(self) -> ScreenTimeStats:
        """
        Get current screen time statistics.
        
        Returns:
            Current ScreenTimeStats
        """
        # Update current session time if exists
        if self.current_session:
            session_duration = int(
                (datetime.now() - self.current_session.start_time).total_seconds()
            )
            # Clone stats and add current session
            stats = ScreenTimeStats(
                ai_time_minutes=self.stats.ai_time_minutes,
                social_time_minutes=self.stats.social_time_minutes,
                productive_time_minutes=self.stats.productive_time_minutes,
                entertainment_time_minutes=self.stats.entertainment_time_minutes,
                other_time_minutes=self.stats.other_time_minutes,
                total_sessions=self.stats.total_sessions,
                current_session=self.current_session
            )
            # Add current session time
            stats.add_time(self.current_session.category, session_duration)
            return stats
        
        return self.stats
    
    def get_category_time(self, category: AppCategory) -> int:
        """
        Get total time for a category in minutes.
        
        Args:
            category: AppCategory to query
            
        Returns:
            Time in minutes
        """
        stats = self.get_current_stats()
        return stats.get_category_minutes(category)
    
    def is_threshold_exceeded(self, category: AppCategory, threshold_minutes: int) -> bool:
        """
        Check if a category has exceeded its threshold.
        
        Args:
            category: Category to check
            threshold_minutes: Threshold in minutes
            
        Returns:
            True if threshold exceeded
        """
        minutes = self.get_category_time(category)
        return minutes >= threshold_minutes
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = ScreenTimeStats()
        self.sessions = []
        self.current_session = None
        logger.info("Screen time stats reset")
    
    def export_sessions(self) -> List[Dict]:
        """
        Export all sessions as dictionaries.
        
        Returns:
            List of session dictionaries
        """
        return [
            {
                "app_name": s.app_name,
                "category": s.category.value,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration_seconds": s.duration_seconds
            }
            for s in self.sessions
        ]
    
    def start(self) -> None:
        """Start the monitoring loop."""
        self._running = True
        logger.info("Screen time monitoring started")
    
    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
        if self.current_session:
            self.end_session()
        logger.info("Screen time monitoring stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running


# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
    except ImportError:
        logger.warning("win32gui not available - some features may not work")
elif platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace
    except ImportError:
        logger.warning("AppKit not available - some features may not work")
