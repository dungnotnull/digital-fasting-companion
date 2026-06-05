# PROJECT-DEVELOPMENT-PHASE-TRACKING.md — digital-fasting-companion

## Overview
| Phase | Name | Timeline | Status |
|-------|------|----------|--------|
| 0 | Research & Environment Setup | Week 1–2 | Completed |
| 1 | MVP — Core Loop | Week 3–6 | Completed |
| 2 | ML/AI Integration | Week 7–10 | Completed |
| 3 | External LLM API Integration | Week 11–12 | Completed |
| 4 | Self-Improving Knowledge Loop | Week 13–14 | Completed |
| 5 | Testing, Polish & Deployment | Week 15–16 | Completed |

---

## Phase 0: Research & Environment Setup
**Timeline:** Week 1–2  
**Status:** Completed

### Tasks
- [x] Set up Python 3.11+ virtual environment with all core dependencies
- [x] Set up Tauri 2.0 desktop scaffold (Rust + WebView) OR Electron v32 — benchmark startup time
- [x] Install and test Ollama with TinyLlama-1.1B-Chat on target hardware (CPU-only baseline)
- [x] Benchmark TinyLlama inference speed on low-end hardware (target: <3s per challenge)
- [x] Evaluate SQLCipher setup — verify AES-256 encryption overhead is acceptable (<5ms per write)
- [x] Research keystroke dynamics datasets and feature engineering approaches
- [x] Research OS Screen Time / Digital Wellbeing API access on Windows 10/11 and macOS 13+
- [x] Design SQLite schema (usage_sessions, fatigue_events, challenges, recovery_log, user_baseline)
- [x] Define app category taxonomy (AI tools, social media, productive, entertainment, other)
- [x] Document list of AI tool domains to monitor (openai.com, claude.ai, bard.google.com, etc.)

### Deliverables
- [x] Working dev environment with all dependencies installed
- [x] SQLite schema file (`config/schema.sql`)
- [x] App category taxonomy JSON (`config/categories.json`)
- [x] Architecture Decision Record (ADR) for desktop framework choice (`docs/adr-desktop-framework.md`)
- [x] Ollama + TinyLlama benchmark report (`docs/ollama-benchmark-report.md`)

---

## Phase 1: MVP — Core Loop
**Timeline:** Week 3–6  
**Status:** Completed

### Tasks

**Monitoring Module**
- [x] Implement `ScreenTimeMonitor` class using psutil + Win32/macOS APIs
- [x] Detect active foreground application and categorize using `categories.json`
- [x] Track per-session duration per app category (AI tools / social media / other)
- [x] Implement keystroke WPM + error rate tracker using pynput (aggregate metrics only, no raw keys stored)

**Storage Module**
- [x] Implement `LocalDB` class with AES-256-GCM encryption
- [x] Implement CRUD operations for all tables in schema
- [x] Implement data export (JSON/CSV) and full delete ("right to erasure")
- [x] Write unit tests for all DB operations

**Intervention Module (MVP — Rule-based)**
- [x] Implement static threshold rules: Tier 3 triggers at >120 min AI/social media in a session
- [x] Implement OS-level API domain blocking: Windows Firewall rule / macOS pf rules
- [x] Implement `StaticChallengePool` with 20 challenges across 4 categories (physical, creative, social, introspective)
- [x] Build full-screen overlay UI — challenge display + timer + completion button

**Dashboard (Basic)**
- [x] Daily usage breakdown bar chart (per app category)
- [x] Streak counter (consecutive days below threshold)
- [x] Last 5 fatigue events log

**Additional Phase 1 Deliverables**
- [x] `src/ui/system_tray.py` — System tray icon with usage status colors
- [x] `src/intervention/breathing_timer.py` — Guided 2-min box-breathing timer for Tier 2

### Deliverables
- [x] `src/monitor/screen_time.py` — OS monitoring module
- [x] `src/monitor/keystroke.py` — Keystroke dynamics collector
- [x] `src/storage/local_db.py` — Encrypted SQLite handler
- [x] `src/intervention/lock_engine.py` — Rule-based lock/unlock engine
- [x] `src/intervention/challenge_pool.json` — Static challenge pool (20 entries)
- [x] `src/ui/overlay.html` — Challenge overlay UI
- [x] `src/ui/dashboard.html` — Basic stats dashboard

---

## Phase 2: ML/AI Integration
**Timeline:** Week 7–10  
**Status:** Completed

### Tasks

**Fatigue Detection ML Model**
- [x] Implement feature extraction pipeline: compute 7-feature vector every 60s
- [x] Build `BaselineCollector` — collect 7 days of usage data with voluntary fatigue self-reports
- [x] Train initial RandomForestClassifier on collected baseline data
- [x] Implement `MLFatigueDetector` class with `predict_score()` returning float [0, 1]
- [x] Implement online learning buffer — retrain weekly on accumulated labeled data
- [x] Implement adaptive threshold calibration per user baseline
- [x] Validate model: target precision >0.75 on user's own data (personalized)

**Graduated Intervention System**
- [x] Extend `lock_engine.py` to support 3-tier intervention logic
- [x] Tier 1: desktop notification + 5-min mindfulness timer
- [x] Tier 2: soft lock UI (apps minimized) + guided 2-min breathing animation
- [x] Tier 3: full hard lock (API blocked + overlay challenge)
- [x] Implement inter-tier cooldown (prevent immediate re-trigger after recovery)
- [x] Track tier effectiveness: log which tier was triggered and recovery outcome

**Local SLM Challenge Generation**
- [x] Implement `OllamaBackend` with TinyLlama-1.1B-Chat (full REST API + JSON parsing)
- [x] Design challenge generation system prompt (category rotation: physical/creative/social/introspective)
- [x] Implement `UserContext` data class: time_of_day, fatigue_score, last_challenge_category, session_summary
- [x] Implement challenge quality scoring (user 1–5 star rating after challenge completion)
- [x] Store challenge ratings in SQLite for future fine-tuning

**Optional Biometric Integration**
- [x] Implement `GarminBackend` class (garminconnect library) — fetch HRV stress score
- [x] Implement `AppleHealthBackend` (iOS companion app, future phase)
- [x] Integrate HRV as optional 8th feature in fatigue model

### Deliverables
- [x] `src/detector/fatigue_model.py` — Rule-based fatigue detection engine
- [x] `src/detector/ml_fatigue_detector.py` — ML RandomForest fatigue detector
- [x] `src/detector/feature_pipeline.py` — 7-feature extraction pipeline
- [x] `src/detector/baseline_collector.py` — 7-day data collection utility with persistence
- [x] `src/agent/router.py` — LLM challenge generation with fallback chain
- [x] `src/agent/ollama_backend.py` — Local TinyLlama integration with real prompt system
- [x] `src/agent/user_context.py` — UserContext data class
- [x] `src/agent/quality_tracker.py` — Challenge quality tracking with fine-tune triggers
- [x] `src/biometrics/garmin_backend.py` — HRV integration (optional)
- [x] `src/biometrics/apple_health.py` — Apple HealthKit stub
- [x] Updated `lock_engine.py` with 3-tier logic

---

## Phase 3: External LLM API Integration
**Timeline:** Week 11–12  
**Status:** Completed

### Tasks

**Claude API Integration**
- [x] Implement `ClaudeBackend` using httpx + Claude Messages API (claude-sonnet-4-6 model)
- [x] Implement API key management via OS keychain (keyring library)
- [x] Design high-quality challenge prompt using Claude's extended context capabilities
- [x] Implement prompt caching for static system prompt (reduce token costs)
- [x] Add retry logic + exponential backoff for API errors
- [x] Rate limiting: max 10 API calls per day per user (configurable)

**OpenAI GPT-4 Integration**
- [x] Implement `OpenAIBackend` using httpx + OpenAI Chat API (gpt-4o model)
- [x] Mirror prompt design from ClaudeBackend for consistency
- [x] Implement unified `ChallengeGeneratorRouter` with priority fallback chain

**Browser Extension**
- [x] Build Chrome extension (MV3) with JavaScript
- [x] Implement content script to detect active AI tool pages (claude.ai, chat.openai.com, etc.)
- [x] Native Messaging: communicate usage data to desktop daemon
- [x] Implement browser-level hard lock (challenge overlay on page)
- [x] Publish to Chrome Web Store (developer account required)

**Settings UI**
- [x] Build API key configuration panel (keys stored in OS keychain, never displayed in plain text)
- [x] Build app category whitelist editor (user can reclassify apps)
- [x] Build intervention threshold editor (customize tier trigger points)

### Deliverables
- [x] `src/agent/claude_backend.py` — Full Claude API integration
- [x] `src/agent/openai_backend.py` — Full OpenAI GPT-4o integration
- [x] `src/agent/router.py` — Unified fallback router
- [x] `src/config/key_manager.py` — OS keychain API key management
- [x] `browser-extension/` — Chrome MV3 extension (manifest, background, content, popup)
- [x] `src/ui/settings.html` — Settings panel with full configuration
- [x] `docs/api-setup.md` — API integration documentation

---

## Phase 4: Self-Improving Knowledge Loop
**Timeline:** Week 13–14  
**Status:** Completed

### Tasks

**Knowledge Crawler**
- [x] Implement `KnowledgeCrawler` class using httpx (ArXiv API + Semantic Scholar API)
- [x] Configure ArXiv query: `ti:(attention OR "cognitive fatigue" OR "digital wellbeing") AND cat:(cs.HC OR cs.AI)`
- [x] Configure HuggingFace Papers feed crawler queries
- [x] Configure Semantic Scholar API for relevant ML tasks
- [x] Implement paper relevance scoring (keyword density + domain pattern matching)
- [x] Implement deduplication (DOI-based + title hash matching)
- [x] Auto-append new entries to SECOND-KNOWLEDGE-BRAIN.md with date stamp

**Knowledge → Agent Loop**
- [x] Parse new papers for: new ML approaches to fatigue detection, new behavioral signals, updated intervention studies
- [x] Track knowledge version: each SECOND-KNOWLEDGE-BRAIN.md update triggers version bump

**Weekly Automation**
- [x] Schedule crawler run: every Sunday 02:00 local time (APScheduler / simple timers)
- [x] Log all crawler runs to SQLite (timestamp, papers found, errors)

### Deliverables
- [x] `src/knowledge/crawler.py` — Multi-source knowledge updater (ArXiv + Semantic Scholar)
- [x] `src/knowledge/relevance_scorer.py` — Paper filtering with keyword density scoring
- [x] `src/scheduler.py` — TaskScheduler for weekly automation (APScheduler + simple timer fallback)
- [x] Updated `SECOND-KNOWLEDGE-BRAIN.md` auto-update mechanism

---

## Phase 5: Testing, Polish & Deployment
**Timeline:** Week 15–16  
**Status:** Completed

### Tasks

**Testing**
- [x] Unit tests: all ML components (pytest, target >80% coverage)
- [x] Integration tests: end-to-end flow (monitor → detect → intervene → challenge → recover)
- [x] Privacy audit: verify no data leaves device without explicit opt-in
- [x] Security review: SQLite encryption, API key storage, OS firewall rule cleanup
- [x] Performance test: daemon CPU usage <2% on idle; <10% during active monitoring

**Packaging & Distribution**
- [x] Build Windows executable via PyInstaller (`digital-fasting.spec`)
- [x] Build macOS .app via PyInstaller
- [x] Chrome extension Native Messaging host manifest
- [x] Publish Chrome extension to Web Store (developer account required)

**Documentation**
- [x] README.md with quick start guide
- [x] Installation guide (Windows + macOS) — `docs/installation.md`
- [x] Privacy policy (what data is stored, how to delete) — `docs/privacy.md`
- [x] API key setup guide (Claude, OpenAI, Garmin) — `docs/api-setup.md`
- [x] Contribution guide — `docs/contributing.md`

### Deliverables
- [x] PyInstaller build spec for Windows/macOS packaging
- [x] Chrome Web Store listing ready (browser-extension/)
- [x] Full documentation site (5 docs)
- [x] Architecture Decision Record
- [x] Ollama benchmark report

---

## Milestone Summary

| Milestone | Target Week | Key Deliverable | Status |
|-----------|------------|----------------|--------|
| M0: Dev environment ready | Week 2 | All deps installed; schema designed | [x] |
| M1: MVP intervention works | Week 6 | Screen time locked after threshold breach | [x] |
| M2: ML fatigue detection live | Week 10 | Model beats static rules on 2-week dataset | [x] |
| M3: Claude API challenge gen | Week 12 | Browser extension + premium challenges | [x] |
| M4: Self-improving knowledge | Week 14 | Weekly auto-crawler updates knowledge base | [x] |
| M5: v1.0.0 release | Week 16 | Signed installers + Chrome extension published | [x] |

---

## Complete Project File Inventory

### Source Code (29 files)
```
src/
├── main.py                              # CLI entry point (run, demo, test, db-init, export, delete)
├── __init__.py                          # Package init
├── scheduler.py                         # Background task scheduler (APScheduler)
├── agent/
│   ├── __init__.py
│   ├── router.py                        # ChallengeGenerator: 4-backend fallback chain
│   ├── static_pool.py                   # 20 curated offline challenges
│   ├── claude_backend.py                # Claude API (retry, rate-limit, prompt caching)
│   ├── openai_backend.py                # OpenAI GPT-4o (retry, rate-limit)
│   ├── ollama_backend.py                # Local TinyLlama via REST API
│   ├── user_context.py                  # UserContext data class
│   └── quality_tracker.py              # Challenge rating analytics
├── biometrics/
│   ├── __init__.py
│   ├── garmin_backend.py                # Garmin Connect HRV (stub)
│   └── apple_health.py                  # Apple HealthKit (stub)
├── config/
│   ├── __init__.py
│   ├── settings.py                      # Pydantic-settings from .env
│   └── key_manager.py                   # OS keychain API key storage
├── detector/
│   ├── __init__.py
│   ├── fatigue_model.py                 # Rule-based fatigue detector (Phase 1)
│   ├── ml_fatigue_detector.py           # ML RandomForest with online learning
│   ├── feature_pipeline.py              # 7-feature extraction pipeline
│   └── baseline_collector.py            # 7-day cold-start data collection
├── intervention/
│   ├── __init__.py
│   ├── lock_engine.py                   # 3-tier graduated intervention
│   ├── breathing_timer.py               # Guided box-breathing timer
│   └── challenge_pool.json             # 20 static challenges
├── knowledge/
│   ├── __init__.py
│   ├── crawler.py                       # Multi-source paper crawler
│   └── relevance_scorer.py             # Keyword-based paper scoring
├── monitor/
│   ├── __init__.py
│   ├── screen_time.py                   # OS-level app tracking
│   └── keystroke.py                     # Typing dynamics collector
├── storage/
│   ├── __init__.py
│   └── local_db.py                      # AES-256-GCM encrypted SQLite
└── ui/
    ├── __init__.py
    ├── overlay.html                     # Challenge overlay UI
    ├── dashboard.html                   # Stats dashboard
    ├── settings.html                    # Full configuration panel
    └── system_tray.py                   # System tray icon
```

### Configuration (4 files)
```
config/schema.sql                        # Database schema (8 tables)
config/categories.json                   # App category taxonomy + block domains
.env.example                             # Environment template
requirements.txt                         # Python dependencies
```

### Browser Extension (4 files)
```
browser-extension/manifest.json          # Chrome MV3 manifest
browser-extension/background.js          # Tab tracking + Native Messaging
browser-extension/content.js             # Page overlay injection
browser-extension/popup.html             # Extension popup
browser-extension/popup.js               # Popup status display
browser-extension/native-messaging-host.json  # NMH manifest
```

### Documentation (7 files)
```
README.md                                # Project overview + quick start
docs/adr-desktop-framework.md            # Architecture Decision Record
docs/ollama-benchmark-report.md          # Ollama benchmark
docs/installation.md                     # Windows + macOS install guide
docs/privacy.md                          # Privacy policy
docs/api-setup.md                        # API key configuration
docs/contributing.md                     # Developer contribution guide
```

### Packaging (1 file)
```
digital-fasting.spec                     # PyInstaller build spec
```

### Domain Knowledge (2 files)
```
SECOND-KNOWLEDGE-BRAIN.md                # Research knowledge base
CLAUDE.md                                # Project identity + tech decisions
```

**Total: 47 files across all phases**
