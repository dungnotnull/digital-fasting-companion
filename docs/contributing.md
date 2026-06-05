# Contributing Guide

## Project Philosophy

The Digital Fasting Companion is a privacy-first tool for digital wellbeing. Contributions should respect:
- **Local-first:** No telemetry, no cloud sync by default
- **Privacy:** No raw keystrokes stored, aggregate metrics only
- **Offline-capable:** Core functionality works without internet
- **User-controlled:** All interventions configurable, all data exportable/deletable

## Getting Started

### Development Setup
```bash
git clone <repo-url>
cd digital-fasting-companion
cp .env.example .env
pip install -r requirements.txt
python -m src.main test
```

### Project Structure
```
src/
├── agent/         Challenge generation (Claude, GPT, Ollama, static pool)
│   ├── router.py          Fallback chain orchestrator
│   ├── claude_backend.py  Premium Claude integration
│   ├── openai_backend.py  Premium GPT-4o integration
│   ├── ollama_backend.py  Local TinyLlama integration
│   ├── static_pool.py     20 curated offline challenges
│   ├── user_context.py    Context data class
│   └── quality_tracker.py Challenge rating analytics
├── biometrics/    Wearable data integration
│   ├── garmin_backend.py  Garmin Connect HRV
│   └── apple_health.py    HealthKit stub
├── config/        Settings and key management
│   ├── settings.py        Pydantic-settings from .env
│   └── key_manager.py     OS keychain API key storage
├── detector/      Fatigue detection engine
│   ├── fatigue_model.py       Rule-based detector (Phase 0/1)
│   ├── ml_fatigue_detector.py ML RandomForest detector (Phase 2)
│   ├── feature_pipeline.py    7-feature extraction pipeline
│   └── baseline_collector.py  Cold-start data collection
├── intervention/  Lock engine
│   ├── lock_engine.py     3-tier graduated intervention
│   ├── breathing_timer.py Guided box-breathing timer
│   └── challenge_pool.json 20 static challenges
├── knowledge/     Research paper crawler
│   ├── crawler.py            Multi-source paper fetcher
│   └── relevance_scorer.py   Domain relevance scoring
├── monitor/       Behavioral monitoring
│   ├── screen_time.py        OS-level app tracking
│   └── keystroke.py          Typing dynamics
├── storage/       Encrypted persistence
│   └── local_db.py           AES-256-GCM encrypted SQLite
├── ui/            User interfaces
│   ├── overlay.html          Challenge overlay
│   ├── dashboard.html        Usage stats dashboard
│   ├── settings.html         Configuration panel
│   └── system_tray.py        System tray icon
├── scheduler.py   Background task scheduling
└── main.py        Entry point + CLI
```

## Adding a New Challenge Backend

1. Create a class in `src/agent/` with:
   - `is_available() -> bool`
   - `generate(category, session_min, time_of_day, fatigue_score, **kwargs) -> Optional[Challenge]`

2. Register in `src/agent/router.py` `__init__`:
   ```python
   self.your_backend = YourBackend(...)
   self._backends = [self.claude, self.openai, self.your_backend, self.ollama, self.static]
   ```

## Adding a New Monitoring Signal

1. Create collector in `src/monitor/`
2. Add feature extraction in `src/detector/feature_pipeline.py`
3. Update `FeatureVector` with the new field
4. Update `MLFatigueDetector` feature importances
5. Update `config/schema.sql` if persistence needed

## Code Style

- Python 3.11+ type hints
- Dataclasses for data objects
- No hardcoded paths — use `get_settings()`
- Log with `logging.getLogger(__name__)`
- Thread-safe DB access via `LocalDB._lock`

## Running Tests

```bash
python -m src.main test    # Component initialization
python -m src.main demo    # Full simulated E2E flow
```

## Before Submitting

- Verify `python -m src.main test` passes
- Verify `python -m src.main demo` completes without errors
- No new plaintext API key storage
- No telemetry or external network calls added without opt-in
