"""
Background task scheduler for digital-fasting-companion.

Manages recurring tasks:
- Every Sunday 02:00: Knowledge crawler run
- Every 60s: Fatigue score prediction
- Weekly: ML model retraining
- Weekly: Baseline collection check
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

APSCHEDULER_AVAILABLE = False
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    logger.warning("APScheduler not available — scheduling disabled")


class TaskScheduler:
    """
    Manages recurring background tasks.

    Uses APScheduler for production, falls back to simple
    threading.Timer for environments without APScheduler.
    """

    def __init__(self):
        self._scheduler: Optional["BackgroundScheduler"] = None
        self._running = False
        self._callbacks: dict = {}
        self._simple_timers: List["threading.Timer"] = []

    def add_weekly(
        self,
        task_id: str,
        callback: Callable,
        day_of_week: str = "sun",
        hour: int = 2,
        minute: int = 0,
    ) -> None:
        """
        Schedule a task to run weekly.

        Args:
            task_id: Unique identifier
            callback: Function to call
            day_of_week: 'mon' through 'sun'
            hour: 0-23
            minute: 0-59
        """
        if APSCHEDULER_AVAILABLE:
            self._ensure_scheduler()
            self._scheduler.add_job(
                callback,
                CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                id=task_id,
                replace_existing=True,
                name=task_id,
            )
            logger.info(
                "Scheduled %s: %s at %02d:%02d", task_id, day_of_week, hour, minute
            )
        else:
            self._callbacks[task_id] = {
                "callback": callback,
                "day": day_of_week,
                "hour": hour,
                "minute": minute,
            }
            logger.info("Registered simple timer for %s (weekly)", task_id)

    def add_interval(
        self,
        task_id: str,
        callback: Callable,
        seconds: int = 60,
    ) -> None:
        """
        Schedule a task to run at a fixed interval.

        Args:
            task_id: Unique identifier
            callback: Function to call
            seconds: Interval in seconds
        """
        if APSCHEDULER_AVAILABLE:
            self._ensure_scheduler()
            self._scheduler.add_job(
                callback,
                IntervalTrigger(seconds=seconds),
                id=task_id,
                replace_existing=True,
                name=task_id,
            )
            logger.info("Scheduled %s: every %ds", task_id, seconds)
        else:
            self._callbacks[task_id] = {
                "callback": callback,
                "seconds": seconds,
                "type": "interval",
            }
            logger.info("Registered simple timer for %s (interval %ds)", task_id, seconds)

    def _ensure_scheduler(self) -> None:
        if self._scheduler is None and APSCHEDULER_AVAILABLE:
            self._scheduler = BackgroundScheduler(
                daemon=True,
                job_defaults={"misfire_grace_time": 3600},
            )

    def start(self) -> None:
        """Start all scheduled tasks."""
        self._running = True
        if APSCHEDULER_AVAILABLE and self._scheduler:
            self._scheduler.start()
            logger.info("Scheduler started (APScheduler)")
        else:
            logger.info("Scheduler started (simple timers)")
            self._run_simple_timers()

    def _run_simple_timers(self) -> None:
        """Run tasks via simple threading.Timer when APScheduler unavailable."""
        import threading

        def interval_loop(task_id, config):
            while self._running:
                try:
                    config["callback"]()
                except Exception as e:
                    logger.error("Task %s failed: %s", task_id, e)
                time.sleep(config.get("seconds", 60))

        def weekly_loop(task_id, config):
            while self._running:
                now = datetime.now()
                target_day = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
                              "fri": 4, "sat": 5, "sun": 6}.get(config["day"], 6)
                days_ahead = target_day - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_run = (now + timedelta(days=days_ahead)).replace(
                    hour=config["hour"], minute=config["minute"], second=0, microsecond=0
                )
                if next_run < now:
                    next_run += timedelta(days=7)
                wait = (next_run - now).total_seconds()
                time.sleep(wait)
                if self._running:
                    try:
                        config["callback"]()
                    except Exception as e:
                        logger.error("Task %s failed: %s", task_id, e)

        for task_id, config in self._callbacks.items():
            if config.get("type") == "interval":
                t = threading.Thread(
                    target=interval_loop, args=(task_id, config), daemon=True
                )
            else:
                t = threading.Thread(
                    target=weekly_loop, args=(task_id, config), daemon=True
                )
            self._simple_timers.append(t)
            t.start()

    def stop(self) -> None:
        """Stop all scheduled tasks."""
        self._running = False
        if APSCHEDULER_AVAILABLE and self._scheduler:
            self._scheduler.shutdown(wait=False)
        for timer in self._simple_timers:
            timer.join(timeout=1)
        logger.info("Scheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._running
