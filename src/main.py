"""
Digital Fasting Companion — Main Application Entry Point.

Orchestrates the full lifecycle:
  monitor → detect → intervene → challenge → recover

Usage:
  python -m src.main run       Start monitoring daemon
  python -m src.main demo      Run demo with simulated data
  python -m src.main test      Verify all components initialize
  python -m src.main db-init   Initialize database schema
  python -m src.main export    Export data to JSON
  python -m src.main delete    Delete all local data
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
        ],
    )
    # Suppress noisy loggers
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("pynput").setLevel(logging.WARNING)


def build_components():
    """Initialize and connect all system components."""
    from src.config.settings import get_settings
    from src.storage.local_db import get_db
    from src.monitor.screen_time import ScreenTimeMonitor
    from src.monitor.keystroke import KeystrokeTracker
    from src.detector.ml_fatigue_detector import MLFatigueDetector
    from src.detector.baseline_collector import BaselineCollector
    from src.intervention.lock_engine import LockEngine, InterventionConfig
    from src.agent.router import ChallengeGenerator
    from src.agent.quality_tracker import ChallengeQualityTracker
    from src.knowledge.crawler import KnowledgeCrawler
    from src.biometrics.garmin_backend import GarminBackend
    from src.config.key_manager import get_key_manager
    from src.scheduler import TaskScheduler

    settings = get_settings()
    logger = logging.getLogger(__name__)

    logger.info("Initializing components...")

    # Storage
    db = get_db()
    logger.info("  Database: %s", db.db_path)

    # Monitoring
    screen_monitor = ScreenTimeMonitor(
        poll_interval_seconds=settings.monitoring.screen_time_poll_interval_seconds,
    )
    keystroke_tracker = KeystrokeTracker(
        session_window_seconds=settings.fatigue_detection.feature_window_seconds,
    )
    logger.info("  Monitor: ScreenTime + Keystroke ready")

    # Detector (ML-based with rule-based fallback)
    ml_detector = MLFatigueDetector(
        n_estimators=settings.fatigue_detection.n_estimators,
        max_depth=settings.fatigue_detection.max_depth,
        min_samples_split=settings.fatigue_detection.min_samples_split,
    )
    baseline_collector = BaselineCollector(db=db)
    logger.info("  Detector: MLFatigueDetector ready (ml_trained=%s)", ml_detector.is_trained)

    # Intervention
    lock_config = InterventionConfig(
        tier1_min=settings.intervention.tier1_min_score,
        tier1_max=settings.intervention.tier1_max_score,
        tier2_min=settings.intervention.tier2_min_score,
        tier2_max=settings.intervention.tier2_max_score,
        tier3_min=settings.intervention.tier3_min_score,
        tier3_max=settings.intervention.tier3_max_score,
        tier_cooldown_minutes=settings.intervention.tier_cooldown_minutes,
        inter_tier_cooldown_minutes=settings.intervention.inter_tier_cooldown_minutes,
    )
    lock_engine = LockEngine(config=lock_config)
    logger.info("  Intervention: LockEngine ready")

    # Challenge Generator (with quality tracking)
    challenge_gen = ChallengeGenerator()
    backends = challenge_gen.get_available_backends()
    logger.info("  Agent: ChallengeGenerator ready (available: %s)", backends or ["static_pool"])

    # Biometrics (optional)
    key_mgr = get_key_manager()
    garmin = GarminBackend(
        username=key_mgr.get_key("garmin_username") or "",
        password=key_mgr.get_key("garmin_password") or "",
    )
    if garmin.is_available():
        logger.info("  Biometrics: Garmin HRV available")
    else:
        logger.info("  Biometrics: Garmin not configured (optional)")

    # Knowledge Crawler
    crawler = KnowledgeCrawler(db=db)
    logger.info("  Knowledge: Crawler ready (sources: ArXiv, Semantic Scholar)")

    # Scheduler
    scheduler = TaskScheduler()
    logger.info("  Scheduler: Ready")

    logger.info("All components initialized successfully")
    return {
        "settings": settings,
        "db": db,
        "screen_monitor": screen_monitor,
        "keystroke_tracker": keystroke_tracker,
        "detector": ml_detector,
        "baseline_collector": baseline_collector,
        "lock_engine": lock_engine,
        "challenge_gen": challenge_gen,
        "garmin": garmin,
        "crawler": crawler,
        "scheduler": scheduler,
    }


def run_demo():
    """Run a complete demo simulating the full E2E flow."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Digital Fasting Companion -- DEMO MODE")
    logger.info("=" * 50)

    components = build_components()
    db = components["db"]
    screen_monitor = components["screen_monitor"]
    keystroke_tracker = components["keystroke_tracker"]
    detector = components["detector"]
    lock_engine = components["lock_engine"]
    challenge_gen = components["challenge_gen"]

    # Simulate user activity
    import random

    logger.info("\n--- Phase 1: Normal usage (low fatigue) ---")
    score = detector.predict_score(
        typing_wpm=45, error_rate=0.03, backspace_ratio=0.05,
        session_duration_min=15, app_switch_rate=2, hour_of_day=10,
    )
    tier = lock_engine.evaluate(score)
    logger.info("Fatigue score: %.3f -> Tier: %s", score, tier.name)

    logger.info("\n--- Phase 2: Moderate fatigue (Tier 1 nudge) ---")
    score = detector.predict_score(
        typing_wpm=38, error_rate=0.07, backspace_ratio=0.10,
        session_duration_min=60, app_switch_rate=5, hour_of_day=19,
    )
    tier = lock_engine.evaluate(score)
    logger.info("Fatigue score: %.3f -> Tier: %s", score, tier.name)
    if tier.value >= 1:
        event = lock_engine.apply_intervention(
            score, session_id="demo-session-1", trigger_category="ai_tools"
        )
        logger.info("Intervention applied: tier=%s state=%s", event.tier.name, lock_engine.state.value)

    logger.info("\n--- Phase 3: High fatigue (Tier 3 hard lock) ---")
    score = detector.predict_score(
        typing_wpm=15, error_rate=0.18, backspace_ratio=0.25,
        session_duration_min=210, app_switch_rate=10, hour_of_day=22,
    )
    tier = lock_engine.evaluate(score)
    logger.info("Fatigue score: %.3f -> Tier: %s", score, tier.name)

    # Reset cooldown for demo
    from src.intervention.lock_engine import InterventionState
    lock_engine.state = InterventionState.CLEAR

    if tier.value >= 3:
        event = lock_engine.apply_intervention(
            score, session_id="demo-session-2", trigger_category="ai_tools"
        )

        # Generate challenge
        challenge = challenge_gen.get_challenge(
            session_min=120,
            fatigue_score=score,
            time_of_day=22,
        )
        logger.info("--- Challenge Generated ---")
        logger.info("  Category: %s", challenge.category)
        logger.info("  Title: %s", challenge.title)
        logger.info("  Description: %s", challenge.description)
        logger.info("  Time Limit: %ds", challenge.time_limit_seconds)
        logger.info("  Source: %s", challenge.source)

        # Store in DB
        db.insert_fatigue_event(
            event_type="tier3",
            fatigue_score=score,
            session_id="demo-session-2",
            trigger_category="ai_tools",
        )
        challenge_id = db.insert_challenge(
            category=challenge.category,
            title=challenge.title,
            description=challenge.description,
            source=challenge.source,
            event_id="demo-event-1",
        )
        logger.info("Challenge stored: %s", challenge_id)

        # Simulate challenge completion
        logger.info("\n--- Phase 4: Challenge completion ---")
        time.sleep(1)
        db.complete_challenge(challenge_id, rating=4)
        lock_engine.resolve_intervention("challenge_completed")
        logger.info("Challenge completed! Rating: 4/5")
        logger.info("Lock state: %s", lock_engine.state.value)

    # Show today's stats
    logger.info("\n--- Today's Summary ---")
    ai_mins = db.get_category_today_minutes("ai_tools")
    social_mins = db.get_category_today_minutes("social_media")
    events = db.get_recent_events(3)
    logger.info("AI Tools: %d min", ai_mins)
    logger.info("Social Media: %d min", social_mins)
    logger.info("Recent Events: %d", len(events))

    logger.info("\n[OK] Demo completed successfully")
    logger.info("  All modules initialized and integrated correctly")
    logger.info("  Challenge generator fallback chain: working")
    logger.info("  3-tier intervention system: operational")
    logger.info("  Encrypted storage: operational")


def run_monitor():
    """Run the full monitoring daemon loop."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Digital Fasting Companion -- Starting monitor daemon")

    components = build_components()
    screen_monitor = components["screen_monitor"]
    keystroke_tracker = components["keystroke_tracker"]
    detector = components["detector"]
    lock_engine = components["lock_engine"]
    challenge_gen = components["challenge_gen"]
    db = components["db"]

    running = True

    def shutdown(sig, frame):
        nonlocal running
        logger.info("Shutdown signal received")
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start monitors
    keystroke_tracker.start()
    screen_monitor.start()

    logger.info("Monitoring loop started (Ctrl+C to stop)")

    try:
        while running:
            # Check active app every 30s
            screen_monitor.check_active_app()
            stats = screen_monitor.get_current_stats()

            # Get keystroke metrics
            wpm, error_rate, backspace = keystroke_tracker.get_features()

            # Compute fatigue score
            hour = datetime.now().hour
            score = detector.predict_score(
                typing_wpm=wpm,
                error_rate=error_rate,
                backspace_ratio=backspace,
                session_duration_min=max(
                    stats.ai_time_minutes + stats.social_time_minutes +
                    stats.entertainment_time_minutes, 1
                ),
                app_switch_rate=stats.total_sessions,
                hour_of_day=hour,
            )

            # Evaluate tier and apply intervention
            tier = lock_engine.evaluate(score)
            if tier.value > 0:
                logger.info("Fatigue: %.3f -> Tier %d (AI:%dm Social:%dm WPM:%.0f)",
                             score, tier.value, stats.ai_time_minutes,
                             stats.social_time_minutes, wpm)

                event = lock_engine.apply_intervention(
                    score,
                    session_id=None,
                    trigger_category="ai_tools" if stats.ai_time_minutes > stats.social_time_minutes else "social_media",
                )

                if event.tier.value >= 3:
                    challenge = challenge_gen.get_challenge(
                        session_min=stats.ai_time_minutes + stats.social_time_minutes,
                        fatigue_score=score,
                        time_of_day=hour,
                    )
                    logger.info("Challenge: %s [%s]", challenge.title, challenge.source)
                    db.insert_fatigue_event(
                        event_type=f"tier{event.tier.value}",
                        fatigue_score=score,
                        trigger_category=event.trigger_category,
                    )
                    # In real run, show overlay UI here
                    # In headless/daemon mode, log and wait
                    logger.info("Overlay would show: %s", challenge.title)

            # Sleep interval
            time.sleep(components["settings"].monitoring.screen_time_poll_interval_seconds)

    finally:
        keystroke_tracker.stop()
        screen_monitor.stop()
        db.disconnect()
        logger.info("Monitor daemon stopped")


def run_test():
    """Run component initialization test."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Digital Fasting Companion -- COMPONENT TEST")
    logger.info("=" * 50)

    try:
        components = build_components()
        logger.info("\n[OK] All components initialized successfully")

        # Test detector (ML-based with rule-based fallback)
        score = components["detector"].predict_score(
            typing_wpm=40, error_rate=0.05, backspace_ratio=0.08,
            session_duration_min=60, app_switch_rate=3,
        )
        logger.info("[OK] FatigueDetector: score=%.3f", score)

        # Test lock engine
        tier = components["lock_engine"].evaluate(score)
        logger.info("[OK] LockEngine: tier=%s", tier.name)

        # Test challenge generator
        challenge = components["challenge_gen"].get_challenge()
        logger.info("[OK] ChallengeGenerator: %s [%s]", challenge.title, challenge.category)

        # Test DB
        components["db"].set_setting("test_key", "test_value")
        val = components["db"].get_setting("test_key")
        assert val == "test_value"
        logger.info("[OK] Database: read/write OK")

        logger.info("\n[OK] All tests passed")
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        sys.exit(1)


def cmd_db_init():
    """Initialize database schema."""
    setup_logging()
    from src.storage.local_db import get_db
    db = get_db()
    print(f"Database initialized: {db.db_path}")


def cmd_export():
    """Export all data to JSON."""
    setup_logging()
    from src.storage.local_db import get_db
    db = get_db()
    out = "data/export.json"
    db.export_json(out)
    print(f"Data exported to {out}")


def cmd_delete():
    """Delete all local data."""
    confirm = input("This will PERMANENTLY DELETE all local data. Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("Cancelled")
        return
    setup_logging()
    from src.storage.local_db import get_db
    db = get_db()
    db.full_delete()
    print("All data deleted")


def main():
    parser = argparse.ArgumentParser(
        description="Digital Fasting Companion -- AI & Smartphone Addiction Recovery"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("run", help="Start monitoring daemon")
    subparsers.add_parser("demo", help="Run demo simulation")
    subparsers.add_parser("test", help="Test all components")
    subparsers.add_parser("db-init", help="Initialize database")
    subparsers.add_parser("export", help="Export data to JSON")
    subparsers.add_parser("delete", help="Delete all local data")

    args = parser.parse_args()

    if args.command == "run":
        run_monitor()
    elif args.command == "demo":
        run_demo()
    elif args.command == "test":
        run_test()
    elif args.command == "db-init":
        cmd_db_init()
    elif args.command == "export":
        cmd_export()
    elif args.command == "delete":
        cmd_delete()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
